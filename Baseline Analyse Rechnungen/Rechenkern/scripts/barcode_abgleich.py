"""D-052: Barcode-Abgleich Einzeltickets × Zutritts-Scans – Nicht-Scan-Quote je Saison.

Verbindet pro Spieltag die Barcodes der Einzeltickets (Exporte 2021/22–2024/25: Spalte «Barcode_»,
CSVs ab 2025/26: «Barcode» in Hochkommas) mit den Barcodes der erlaubten Drehkreuz-Durchgänge
(alle vier Herren-Lieferungen). Die IDs bleiben ausschliesslich im Arbeitsspeicher; ausgegeben
werden nur Zählungen je Saison bzw. je Spiel. Keine Personenfelder werden gelesen.

Validierung: In 2022/23 liegen sowohl Scans als auch das ZKS-Eintrittsfeld vor → Übereinstimmung
pro Ticket wird ausgegeben.

Zusätzlich: Public-Abo-No-Show-Näherung je Saison (Funktion abo_quote).

Lesart: «nicht gescannt» ist eine Obergrenze für No-Show (Barcode-Neuausstellung, Zweitmarkt,
manueller Einlass möglich) – siehe Teamnotiz 2026-11-12_barcode_abgleich_noshow.md.

    python scripts/barcode_abgleich.py <Ordner Rohdaten> <mart_match.csv> [<Ausgabeordner>]\n\nAusgabe: nur Tabellen je Saison (keine IDs, keine Spielzeilen mit Ticketdaten).
"""
import sys
from pathlib import Path

import pandas as pd

DATEN, MART = Path(sys.argv[1]), Path(sys.argv[2])
OUT = Path(sys.argv[3]) if len(sys.argv) > 3 else None  # Ordner
ZUTRITT = next(p for p in (DATEN / "Zutritte", DATEN / "Zutritt") if p.exists())
TICKETING = DATEN / "Ticketing"
MIN_SCAN_IST = 0.95  # Spiel gilt als vollständig gescannt, wenn eindeutige Scans ≥ 95 % IST
LEER = ["", "nan", "None"]


def _norm(s: pd.Series) -> pd.Series:
    return s.astype(str).str.strip().str.strip("'").str.replace(r"\.0$", "", regex=True)


def lade_scans() -> pd.DataFrame:
    """Alle Herren-Scan-Lieferungen: Spieltag, Barcode, Lieferung."""
    teile = []
    for name, opts, cols in (
        ("zugangsdaten_herren_inhouse.csv", dict(sep=";", header=None, encoding="utf-8-sig"), [0, 3, 6]),
        ("zugangsdaten_herren_alteSaisons.txt", dict(sep="\t"), ["Matchday", "Barcode", "Lesername"]),
        ("Saison_2024-25_Transaktionen.csv", dict(sep=";", header=None, encoding="utf-8-sig"), [0, 3, 6]),
    ):
        if (ZUTRITT / name).exists():
            d = pd.read_csv(ZUTRITT / name, dtype=str, usecols=cols, **opts)
            d.columns = ["datum", "bc", "leser"]
            teile.append(d.assign(lieferung=name))
    xl = ZUTRITT / "ErlaubteZutritteHerren.xlsx"
    if xl.exists():
        d = pd.read_excel(xl, engine="calamine", dtype=str, usecols=["Datum", "UTId", "Lesername"])
        d.columns = ["datum", "bc", "leser"]
        teile.append(d.assign(lieferung=xl.name))
    s = pd.concat(teile, ignore_index=True)
    s["datum"] = pd.to_datetime(s["datum"].str[:10], format="%Y-%m-%d", errors="coerce")
    s["bc"] = _norm(s["bc"])
    leser = s["leser"].fillna("").str.strip()
    s["sektor"] = leser.str.extract(r"^(HH|B4|[ABCD])", expand=False).fillna("?")
    return s


def lade_einzeltickets() -> pd.DataFrame:
    """Einzeltickets (ohne Abos): Spieltag, Barcode, ZKS-Eintritt vorhanden (nur Exporte)."""
    teile = []
    for p in sorted(TICKETING.glob("*/Einzeltickets_*.xlsx")):
        if p.name.startswith("~$"):
            continue
        xl = pd.ExcelFile(p, engine="calamine")
        for blatt in xl.sheet_names:
            d = pd.read_excel(xl, blatt, dtype=str,
                              usecols=lambda c: c in ("Veranstaltungsdatum", "Barcode_", "ZKS-Eintrittsdatum"))
            if "Barcode_" not in d.columns:
                continue
            teile.append(pd.DataFrame({
                "datum": pd.to_datetime(d["Veranstaltungsdatum"], errors="coerce", format="mixed").dt.normalize(),
                "bc": _norm(d["Barcode_"]),
                "zks": d["ZKS-Eintrittsdatum"].fillna("").str.strip().ne("")}))
    for p in sorted(TICKETING.glob("20*/*/*.csv")):
        if "Saisonabo" in p.name or p.parent.name == "MS_Frauen":
            continue
        d = pd.read_csv(p, encoding="utf-8-sig", dtype=str, keep_default_na=False, usecols=lambda c: c == "Barcode")
        teile.append(pd.DataFrame({"datum": pd.to_datetime(p.name[:8], format="%Y%m%d", errors="coerce"),
                                   "bc": _norm(d["Barcode"]), "zks": False}))
    return pd.concat(teile, ignore_index=True)


def abo_quote(g: pd.DataFrame) -> pd.DataFrame:
    """Public-Abo-No-Show-Näherung je Saison (SL, vollständig gescannte Spiele).

    Bestand je Saison = Median(SOLL − Einzeltickets + Zweitmarkt) über Spiele ohne Kapazitäts-SOLL
    (Umkehrung der SOLL-Formel «Einzel + Abo − Zweitmarkt»), minus Hospitality-Anteil 859/13'052
    (Abo-Snapshot 2026/27). Hauptvariante: je Spiel zusätzlich die über den Zweitmarkt weiterverkauften
    Plätze abziehen (deren Besucher kommen mit neuem Ticket und zählen als Einzelticket).
    Besuche = Scans ohne Einzelticket-Treffer, ohne Hospitality-Leser (HH). Gäste (B4) sind Einzeltickets.
    Rest enthält auch Freikarten/Mitarbeitende/Medien → Quote ist eher Untergrenze.
    """
    hosp = 859 / 13052
    x = g[g["vollstaendig"] & (g["wettbewerb"] == "SL")].copy()
    x["bestand_roh"] = x["soll"] - x["einzeltickets"] + x["zweitmarkt"].fillna(0)
    kap = x["soll_definition"].fillna("").str.contains("Kapazität|ausverkauft")
    bestand = x[~kap].groupby("saison")["bestand_roh"].median()
    x["bestand_public"] = x["saison"].map(bestand) * (1 - hosp)
    x["bestand_netto"] = x["bestand_public"] - x["zweitmarkt"].fillna(0)
    x["abo_besuche"] = x["scans_rest"] - x["scans_rest_hospitality"].fillna(0)
    x["abo_quote"] = 1 - x["abo_besuche"] / x["bestand_netto"]
    s = x.groupby("saison")
    z = pd.DataFrame({
        "spiele": s.size(), "spiele_fuer_bestand": (~kap).groupby(x["saison"]).sum(),
        "abo_bestand": bestand.round(0), "public_abo_bestand": (bestand * (1 - hosp)).round(0),
        "zweitmarkt_median": s["zweitmarkt"].median(), "abo_besuche_median": s["abo_besuche"].median(),
        "abo_noshow_quote": (1 - s["abo_besuche"].sum() / s["bestand_netto"].sum()).round(3),
        "quote_min_spiel": s["abo_quote"].min().round(3), "quote_max_spiel": s["abo_quote"].max().round(3),
        "variante_ohne_zweitmarkt_abzug": (1 - s["abo_besuche"].sum() / s["bestand_public"].sum()).round(3),
        "variante_inkl_hospitality": (1 - s["scans_rest"].sum() / (s["bestand_public"].sum() / (1 - hosp))).round(3),
        "gaeste_scans_ohne_einzelticket": s["scans_rest_gaeste_b4"].sum(),
    }).reset_index()
    print(f"\nPublic-Abo-No-Show (Näherung, SL, Bestand minus Zweitmarkt):\n{z.to_string(index=False)}")
    return z


def main() -> None:
    m = pd.read_csv(MART, parse_dates=["datum"])
    m = m[m["spielstatus"] == "gespielt"][["match_id", "datum", "saison", "wettbewerb", "ist", "zks_valide",
                                           "soll", "soll_definition", "zweitmarkt"]]
    tage = set(m["datum"])
    s = lade_scans()
    s = s[s["datum"].isin(tage)].drop_duplicates(["datum", "bc"])
    t = lade_einzeltickets()
    t = t[t["datum"].isin(tage) & ~t["bc"].isin(LEER)].drop_duplicates(["datum", "bc"])
    scan_keys = set(zip(s["datum"], s["bc"]))
    ticket_keys = set(zip(t["datum"], t["bc"]))
    t["gescannt"] = [k in scan_keys for k in zip(t["datum"], t["bc"])]
    s["einzel"] = [k in ticket_keys for k in zip(s["datum"], s["bc"])]

    g = m.set_index("datum")
    g["scans"] = s.groupby("datum").size()
    g["scans_einzelticket"] = s.groupby("datum")["einzel"].sum()
    g["einzeltickets"] = t.groupby("datum").size()
    g["einzeltickets_gescannt"] = t.groupby("datum")["gescannt"].sum()
    rest = s[~s["einzel"]]
    g["scans_rest"] = rest.groupby("datum").size()
    g["scans_rest_gaeste_b4"] = rest[rest["sektor"] == "B4"].groupby("datum").size()
    g["scans_rest_hospitality"] = rest[rest["sektor"] == "HH"].groupby("datum").size()
    g = g.reset_index()
    g["scan_ist_ratio"] = (g["scans"] / g["ist"]).round(3)
    g["nicht_scan_quote"] = (1 - g["einzeltickets_gescannt"] / g["einzeltickets"]).round(3)
    g["vollstaendig"] = (g["scan_ist_ratio"] >= MIN_SCAN_IST) & (g["einzeltickets"] > 1)

    v = t[t["datum"].isin(set(m.loc[m["zks_valide"] == True, "datum"]) & set(s["datum"]))]  # noqa: E712
    print(f"Validierung ZKS × Barcode ({v['datum'].nunique()} Spiele, {len(v):,} Tickets): "
          f"Übereinstimmung {(v['zks'] == v['gescannt']).mean():.4f}")
    print(pd.crosstab(v["zks"], v["gescannt"]).to_string())

    ok = g[g["vollstaendig"]]
    tabellen = []
    for titel, x in (("Alle Wettbewerbe", ok), ("Nur Super League", ok[ok["wettbewerb"] == "SL"])):
        z = x.groupby("saison").agg(spiele=("match_id", "size"), einzeltickets=("einzeltickets", "sum"),
                                    gescannt=("einzeltickets_gescannt", "sum"), scans=("scans", "sum"),
                                    scans_einzel=("scans_einzelticket", "sum"),
                                    median_spiel=("nicht_scan_quote", "median"))
        z["nicht_scan_quote"] = (1 - z["gescannt"] / z["einzeltickets"]).round(3)
        z["anteil_scans_einzel"] = (z["scans_einzel"] / z["scans"]).round(3)
        print(f"\n{titel} (nur vollständig gescannte Spiele):\n{z.round(3).to_string()}")
        tabellen.append(z.round(3).reset_index().assign(wettbewerb=titel))
    print("\nNicht abgleichbar (Scans < 95 % IST oder keine Einzeltickets):",
          g.loc[~g["vollstaendig"]].groupby("saison").size().to_dict())
    validierung = pd.DataFrame([{"spiele": v["datum"].nunique(), "tickets": len(v),
                                 "uebereinstimmung": round((v["zks"] == v["gescannt"]).mean(), 4),
                                 "zks_ja_scan_nein": int((v["zks"] & ~v["gescannt"]).sum()),
                                 "zks_nein_scan_ja": int((~v["zks"] & v["gescannt"]).sum())}])
    abo = abo_quote(g)
    if OUT:
        OUT.mkdir(parents=True, exist_ok=True)
        validierung.to_csv(OUT / "validierung_zks_barcode.csv", index=False)
        pd.concat(tabellen).to_csv(OUT / "nicht_scan_quote_einzeltickets_je_saison.csv", index=False)
        abo.to_csv(OUT / "abo_noshow_naeherung_je_saison.csv", index=False)
        g.groupby(["saison", "wettbewerb"])["vollstaendig"].agg(spiele="size", abgleichbar="sum").reset_index() \
            .to_csv(OUT / "abdeckung_je_saison.csv", index=False)
        print("Tabellen geschrieben nach:", OUT.name)


if __name__ == "__main__":
    main()

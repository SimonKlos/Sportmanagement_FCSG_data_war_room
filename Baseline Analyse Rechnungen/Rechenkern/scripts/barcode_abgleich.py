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

    python scripts/barcode_abgleich.py <Ordner Rohdaten> <mart_match.csv> [<je_spiel.csv ausserhalb Repo>]
"""
import sys
from pathlib import Path

import pandas as pd

DATEN, MART = Path(sys.argv[1]), Path(sys.argv[2])
OUT = Path(sys.argv[3]) if len(sys.argv) > 3 else None
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


def abo_quote(g: pd.DataFrame) -> None:
    """Public-Abo-No-Show-Näherung (SL, vollständig gescannte Spiele).

    Bestand je Saison = Median(SOLL − Einzeltickets + Zweitmarkt) über Spiele ohne Kapazitäts-SOLL,
    davon Hospitality-Anteil 859/13'052 (Abo-Snapshot 2026/27) abgezogen.
    Besuche = Scans ohne Einzelticket-Treffer, ohne Hospitality-Leser (HH). Gäste (B4) sind bereits
    Einzeltickets. Rest enthält auch Freikarten/Mitarbeitende/Medien → Quote ist eher Untergrenze.
    """
    hosp = 859 / 13052
    x = g[g["vollstaendig"] & (g["wettbewerb"] == "SL")].copy()
    x["bestand_roh"] = x["soll"] - x["einzeltickets"] + x["zweitmarkt"].fillna(0)
    kap = x["soll_definition"].fillna("").str.contains("Kapazität|ausverkauft")
    bestand = x[~kap].groupby("saison")["bestand_roh"].median()
    x["bestand_public"] = x["saison"].map(bestand) * (1 - hosp)
    x["abo_besuche"] = x["scans_rest"] - x["scans_rest_hospitality"].fillna(0)
    x["abo_quote"] = 1 - x["abo_besuche"] / x["bestand_public"]
    z = x.groupby("saison").agg(spiele=("match_id", "size"), bestand_spiele=("bestand_roh", lambda v: int((~kap[v.index]).sum())),
                                bestand_public=("bestand_public", "first"), besuche_median=("abo_besuche", "median"),
                                quote_min=("abo_quote", "min"), quote_max=("abo_quote", "max"))
    z["abo_noshow_quote"] = 1 - x.groupby("saison")["abo_besuche"].sum() / x.groupby("saison")["bestand_public"].sum()
    z["inkl_hospitality"] = 1 - x.groupby("saison")["scans_rest"].sum() / (x.groupby("saison")["bestand_public"].sum() / (1 - hosp))
    print("\nGäste-Scans (B4) ohne Einzelticket-Treffer:", int(x["scans_rest_gaeste_b4"].fillna(0).sum()))
    print(f"Public-Abo-No-Show (Näherung, SL):\n{z.round(3).to_string()}")


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
    for titel, x in (("Alle Wettbewerbe", ok), ("Nur Super League", ok[ok["wettbewerb"] == "SL"])):
        z = x.groupby("saison").agg(spiele=("match_id", "size"), einzeltickets=("einzeltickets", "sum"),
                                    gescannt=("einzeltickets_gescannt", "sum"), scans=("scans", "sum"),
                                    scans_einzel=("scans_einzelticket", "sum"),
                                    median_spiel=("nicht_scan_quote", "median"))
        z["nicht_scan_quote"] = (1 - z["gescannt"] / z["einzeltickets"]).round(3)
        z["anteil_scans_einzel"] = (z["scans_einzel"] / z["scans"]).round(3)
        print(f"\n{titel} (nur vollständig gescannte Spiele):\n{z.round(3).to_string()}")
    print("\nNicht abgleichbar (Scans < 95 % IST oder keine Einzeltickets):",
          g.loc[~g["vollstaendig"]].groupby("saison").size().to_dict())
    abo_quote(g)
    if OUT:
        g.to_csv(OUT, index=False)
        print("Je Spiel geschrieben:", OUT.name)


if __name__ == "__main__":
    main()

"""D-052: Barcode-Abgleich Einzeltickets × Zutritts-Scans – Nicht-Scan-Quote je Saison.

Verbindet pro Spieltag die Barcodes der Einzeltickets (Exporte 2021/22–2024/25: Spalte «Barcode_»,
CSVs ab 2025/26: «Barcode» in Hochkommas) mit den Barcodes der erlaubten Drehkreuz-Durchgänge
(alle vier Herren-Lieferungen). Die IDs bleiben ausschliesslich im Arbeitsspeicher; ausgegeben
werden nur Zählungen je Saison bzw. je Spiel. Keine Personenfelder werden gelesen.

Validierung: In 2022/23 liegen sowohl Scans als auch das ZKS-Eintrittsfeld vor → Übereinstimmung
pro Ticket wird ausgegeben.

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
        ("zugangsdaten_herren_inhouse.csv", dict(sep=";", header=None, encoding="utf-8-sig"), [0, 3]),
        ("zugangsdaten_herren_alteSaisons.txt", dict(sep="\t"), ["Matchday", "Barcode"]),
        ("Saison_2024-25_Transaktionen.csv", dict(sep=";", header=None, encoding="utf-8-sig"), [0, 3]),
    ):
        if (ZUTRITT / name).exists():
            d = pd.read_csv(ZUTRITT / name, dtype=str, usecols=cols, **opts)
            d.columns = ["datum", "bc"]
            teile.append(d.assign(lieferung=name))
    xl = ZUTRITT / "ErlaubteZutritteHerren.xlsx"
    if xl.exists():
        d = pd.read_excel(xl, engine="calamine", dtype=str, usecols=["Datum", "UTId"])
        d.columns = ["datum", "bc"]
        teile.append(d.assign(lieferung=xl.name))
    s = pd.concat(teile, ignore_index=True)
    s["datum"] = pd.to_datetime(s["datum"].str[:10], format="%Y-%m-%d", errors="coerce")
    s["bc"] = _norm(s["bc"])
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


def main() -> None:
    m = pd.read_csv(MART, parse_dates=["datum"])
    m = m[m["spielstatus"] == "gespielt"][["match_id", "datum", "saison", "wettbewerb", "ist", "zks_valide"]]
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
    if OUT:
        g.to_csv(OUT, index=False)
        print("Je Spiel geschrieben:", OUT.name)


if __name__ == "__main__":
    main()

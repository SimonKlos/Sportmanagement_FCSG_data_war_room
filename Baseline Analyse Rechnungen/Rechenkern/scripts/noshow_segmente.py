"""D-052b: No-Show der Einzeltickets nach Segment und Saison (Erweiterung von D-049d über den Barcode-Abgleich).

Eintritt je Einzelticket:
* 2021/22: ZKS-Eintrittsfeld der Exporte (nur Spiele mit validem ZKS, wie D-049d)
* ab 2022/23: Barcode des Tickets unter den erlaubten Durchgängen desselben Spieltags (nur Spiele mit
  eindeutigen Scans ≥ 95 % IST). 2024/25 entfällt (Scans und Ticket-Export überschneiden sich nicht).

Segmente: Kanal, Bestellgrösse, Gästesektor B4, gratis/bezahlt (Preis 0) – über alle Ticketsysteme vergleichbar.
Tarifgruppe «Sponsor/Dritte» nur 2021/22–2023/24: ab 2025/26 neues Ticketsystem mit anderen Tarifnamen
(Sponsorentarif kaum noch vorhanden), daher nicht vergleichbar.

Datenschutz: Barcodes, Auftrags-/Rechnungsnummern nur im Arbeitsspeicher (Bestellgrösse, Abgleich), keine
Personenfelder, keine Tarif-Rohbezeichnungen in der Ausgabe. Zellen < 10 Tickets werden unterdrückt.

    python scripts/noshow_segmente.py <Ordner Rohdaten> <mart_match.csv> [<Ausgabeordner>]
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.dont_write_bytecode = True
HIER = Path(__file__).resolve().parent
sys.path.insert(0, str(HIER.parent))
sys.path.insert(0, str(HIER))
import barcode_abgleich as ba  # noqa: E402
from fcsg.sources.tickets import KANAL_GRUPPE, tarifgruppe, tribuene_gruppe  # noqa: E402
from fcsg.utils import parse_chf  # noqa: E402

MIN = 10
MIN_TICKETS_SPIEL = 100   # Spiel nur mit mindestens 100 Einzeltickets
INHOUSE = "Inhouse (Geschäftsstelle/Kasse)"
EXPORT_SPALTEN = ("Veranstaltungsdatum", "Veranstaltung", "Auftrag", "Verkaufsmodul-Bez.", "Verkaufsart-Bez.",
                  "Platzgruppen-Bez.", "Block-Bez.", "Preis", "ZKS-Eintrittsdatum", "Barcode_")
CSV_SPALTEN = ("Tribüne", "Block", "Ermäßigung", "Filiale", "Rechnung", "Summe", "Barcode")


def lade_tickets() -> pd.DataFrame:
    """Einzeltickets mit Segmentmerkmalen; Auftrag/Rechnung nur für die Bestellgrösse, danach verworfen."""
    teile = []
    for p in sorted(ba.TICKETING.glob("*/Einzeltickets_*.xlsx")):
        if p.name.startswith("~$"):
            continue
        xl = pd.ExcelFile(p, engine="calamine")
        d = pd.concat([pd.read_excel(xl, b, dtype=str, usecols=lambda c: c in EXPORT_SPALTEN) for b in xl.sheet_names],
                      ignore_index=True)
        groesse = d.groupby(["Veranstaltung", "Auftrag"])["Preis"].transform("size")
        preis = pd.to_numeric(d["Preis"], errors="coerce")
        teile.append(pd.DataFrame({
            "datum": pd.to_datetime(d["Veranstaltungsdatum"], errors="coerce", format="mixed").dt.normalize(),
            "bc": ba._norm(d["Barcode_"]), "zks": d["ZKS-Eintrittsdatum"].fillna("").str.strip().ne(""),
            "kanal": d["Verkaufsmodul-Bez."].map(KANAL_GRUPPE).fillna("Andere"),
            "tarifgruppe": [tarifgruppe(t, x) for t, x in zip(d["Verkaufsart-Bez."], preis)],
            "tribuene": [tribuene_gruppe(b, pg) for b, pg in zip(d["Block-Bez."], d["Platzgruppen-Bez."])],
            "preis": preis, "bestellung": groesse, "system": "Export bis 2024/25"}))
    for p in sorted(ba.TICKETING.glob("20*/*/*.csv")):
        if "Saisonabo" in p.name or p.parent.name == "MS_Frauen":
            continue
        d = pd.read_csv(p, encoding="utf-8-sig", dtype=str, keep_default_na=False, usecols=lambda c: c in CSV_SPALTEN)
        preis = d["Summe"].map(parse_chf)
        teile.append(pd.DataFrame({
            "datum": pd.to_datetime(p.name[:8], format="%Y%m%d", errors="coerce"),
            "bc": ba._norm(d["Barcode"]), "zks": False,
            "kanal": d["Filiale"].map(KANAL_GRUPPE).fillna("Andere"),
            "tarifgruppe": [tarifgruppe(t, x) for t, x in zip(d["Ermäßigung"], preis)],
            "tribuene": [tribuene_gruppe(b, None, t) for b, t in zip(d["Block"], d["Tribüne"])],
            "preis": preis, "bestellung": d.groupby("Rechnung")["Summe"].transform("size").to_numpy(),
            "system": "CSV ab 2025/26"}))
    t = pd.concat(teile, ignore_index=True)
    return t[~t["bc"].isin(ba.LEER)].drop_duplicates(["datum", "bc"])


def segmente(t: pd.DataFrame) -> pd.DataFrame:
    """No-Show-Quote und Anteil an allen Einzelticket-No-Shows je Segment."""
    alle_ns = t["noshow"].sum()
    gross = t[(t["kanal"] == INHOUSE) & (t["bestellung"] >= 10)]
    ohne_b4 = gross[gross["tribuene"] != "B4 (Gäste)"]
    defs = [
        ("Alle Einzeltickets", t),
        ("Online-Shop, 2–4 Tickets", t[(t["kanal"] == "Online-Shop") & t["bestellung"].between(2, 4)]),
        ("Inhouse ab 10 Tickets", gross),
        ("– davon Gästesektor B4", gross[gross["tribuene"] == "B4 (Gäste)"]),
        ("– davon ohne Gästesektor", ohne_b4),
        ("   – ohne Gästesektor, gratis", ohne_b4[ohne_b4["preis"].fillna(0) == 0]),
        ("   – ohne Gästesektor, bezahlt", ohne_b4[ohne_b4["preis"].fillna(0) > 0]),
        ("   – ohne Gästesektor, Tarif Sponsor/Dritte", ohne_b4[ohne_b4["tarifgruppe"] == "Sponsor/Dritte"]),
        ("Gratis-Tickets insgesamt (Preis 0)", t[t["preis"].fillna(0) == 0]),
        ("Übrige Einzeltickets (ohne Inhouse ab 10)", t.drop(gross.index)),
    ]
    rows = []
    for name, x in defs:
        n, ns = len(x), int(x["noshow"].sum())
        rows.append({"segment": name, "tickets": n, "noshows": ns if n >= MIN else np.nan,
                     "noshow_quote": round(ns / n, 3) if n >= MIN else np.nan,
                     "anteil_an_allen_noshows": round(ns / alle_ns, 3) if n >= MIN and alle_ns else np.nan})
    out = pd.DataFrame(rows)
    if (t["system"] == "CSV ab 2025/26").any():   # Tarifnamen ab 2025/26 nicht vergleichbar
        out.loc[out["segment"].str.contains("Sponsor"), ["tickets", "noshows", "noshow_quote", "anteil_an_allen_noshows"]] = np.nan
    return out


def main(daten, mart, out=None) -> None:
    ba.setze_pfade(daten, mart, out)
    m = pd.read_csv(mart, parse_dates=["datum"])
    m = m[m["spielstatus"] == "gespielt"][["datum", "saison", "wettbewerb", "ist", "zks_valide"]]
    s = ba.lade_scans()
    s = s[s["datum"].isin(set(m["datum"]))].drop_duplicates(["datum", "bc"])
    scans_je_tag = s.groupby("datum").size()
    m["scan_ist"] = m["datum"].map(scans_je_tag) / m["ist"]
    t = lade_tickets().merge(m, on="datum")
    keys = set(zip(s["datum"], s["bc"]))
    t["gescannt"] = [k in keys for k in zip(t["datum"], t["bc"])]

    zks = t[(t["saison"] == "2021/22") & (t["zks_valide"] == True)].assign(noshow=lambda x: ~x["zks"], quelle="ZKS")  # noqa: E712
    bar = t[(t["saison"] >= "2022/23") & (t["scan_ist"] >= ba.MIN_SCAN_IST)].assign(
        noshow=lambda x: ~x["gescannt"], quelle="Barcode")
    basis = pd.concat([zks, bar], ignore_index=True)
    # Spiele ohne nennenswerte Einzelticket-Daten ausschliessen (2024/25: Export endet 09.12.2024)
    je_spiel = basis.groupby("datum").size()
    basis = basis[basis["datum"].map(je_spiel) >= MIN_TICKETS_SPIEL]

    tab = []
    for saison, x in basis.groupby("saison"):
        seg = segmente(x.reset_index(drop=True)).assign(saison=saison, spiele=x["datum"].nunique(),
                                                         eintritt_quelle=x["quelle"].iloc[0])
        tab.append(seg)
    tab = pd.concat(tab, ignore_index=True)[["saison", "spiele", "eintritt_quelle", "segment", "tickets", "noshows",
                                             "noshow_quote", "anteil_an_allen_noshows"]]
    pd.set_option("display.width", 200)
    print(tab.to_string(index=False))
    if ba.OUT:
        ba.OUT.mkdir(parents=True, exist_ok=True)
        tab.to_csv(ba.OUT / "noshow_segmente_je_saison.csv", index=False)
        print("Geschrieben:", (ba.OUT / "noshow_segmente_je_saison.csv").name)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else None)

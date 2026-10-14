"""Einzeltickets (Exporte 21/22–24/25 und CSVs 25/26–26/27) und Saisonabo-Snapshots.

Datenschutz: Personenfelder (Name, Geburtstag, PLZ, Geschlecht, Kunden-/Ticket-/Barcode-Nummern)
werden beim Einlesen gar nicht erst übernommen. Auftrags- bzw. Rechnungsnummern werden nur
verwendet, um die Bestellgrösse (Tickets pro Bestellung) zu zählen, und danach verworfen.
"""
from __future__ import annotations

import re
from pathlib import Path

import numpy as np
import pandas as pd

from .. import config
from ..log import befund, logger
from ..utils import parse_chf, saison_von, text
from . import korrekturen

XLSX_SPALTEN = [
    "Saison-Bez.", "Veranstaltung", "Veranstaltungsdatum", "Veranstaltungszeit", "Veranstaltungs-Bez.",
    "Preiskategorie-Bez.", "Verkaufsmodul-Bez.", "Auftrag", "Stornostatus-Bez.", "Verkaufsstatus-Bez.",
    "Platzgruppen-Bez.", "Verkaufsart-Bez.", "Bestelldatum", "Versandart-Bez.", "Block-Bez.",
    "Anzahl Waren", "Preis", "ZKS-Eintrittsdatum", "ZKS-Übergabedatum",
]
CSV_SPALTEN = ["Tribüne", "Block", "Ermäßigung", "Datum", "Uhrzeit", "Filiale", "Rechnung", "Versandart", "Summe"]
PERSONENFELDER = ["Kunde", "Kundenname", "Privatperson-Bez.", "Anreden-Bez.", "Geburtstag", "Alter",
                  "Geschlecht-Bez.", "Postleitzahl", "Länder-Bez.", "Barcode_", "KundenNr", "Barcode",
                  "Ticketnummer", "Interne Nummer"]

ORDNER_WETTBEWERB = {"MS_Herren": "SL", "Europacup": "UEFA", "Cup": "Cup", "MS_Frauen": "Frauen"}

KANAL_GRUPPE = {
    "Webshop": "Online-Shop", "FCSG: Onlineshop": "Online-Shop",
    "Inhouse": "Inhouse (Geschäftsstelle/Kasse)", "FC St.Gallen 1879": "Inhouse (Geschäftsstelle/Kasse)",
    "Connect Online": "Partner online (Connect/TDL)", "FCSG: TDL Webshop/Callcenter": "Partner online (Connect/TDL)",
    "FCSG: TDL POS": "Partner-Verkaufsstelle (POS)", "Websales Client": "Verkaufs-App (Direktverkauf)",
    "FCSG: Hospitality": "Hospitality-Verkauf",
}

_HOSPITALITY = r"loge|lounge|business|pub|salon|vip|\bbs\b|tisch"


def tarifgruppe(bezeichnung, preis: float) -> str:
    """Harmonisierte Tarifgruppe aus der Tarifbezeichnung (Export: Verkaufsart, CSV: Ermässigung)."""
    t = text(bezeichnung).lower()
    if re.search(_HOSPITALITY, t):
        return "Hospitality"
    if re.search(r"gratis|promo|0\.-|gutschein|freikarte", t):
        return "Gratis/Promo"
    if re.search(r"\bma\b|mitarbeit|ma fcsg|ma event", t):
        return "Mitarbeitende"
    if re.search(r"sponsor|dritte", t):
        return "Sponsor/Dritte"
    if re.search(r"gäste|gast|visiting", t) and not re.search(r"u1[68]|ausbildung|ahv|ermäss", t):
        return "Gäste Vollpreis" if re.search(r"voll|adults", t) else "Gäste übrige"
    if re.search(r"u1[68]|ausbildung|ahv|\biv\b|stucard|student|ermäss|kind|jugend|lehrling|rollstuhl|rabatt", t):
        return "Ermässigt"
    if "voll" in t:
        return "Vollpreis"
    if preis == 0:
        return "Gratis/Promo"
    return "Übrige"


def tribuene_gruppe(block, platzgruppe=None, tribuene=None) -> str:
    """A, B, B4 (Gäste), C, D, Hospitality oder Andere – aus Block/Platzgruppe/Tribüne."""
    b = text(block).strip()
    pg = text(platzgruppe).lower()
    if re.search(_HOSPITALITY, b.lower()) or re.search(r"business|logen", pg):
        return "Hospitality"
    m = re.search(r"(?:Sektor\s*)?([ABCD])(\d)", b)
    if m:
        return "B4 (Gäste)" if m.group(1) == "B" and m.group(2) == "4" else m.group(1)
    if "gast" in pg:
        return "B4 (Gäste)"
    m = re.match(r"([ABCD])\s*\|", text(tribuene))
    if m:
        return m.group(1)
    return "Andere"


def _vorlauf_tage(spiel: pd.Series, verkauf: pd.Series) -> pd.Series:
    return (spiel.dt.normalize() - verkauf.dt.normalize()).dt.days


# --------------------------------------------------------------------------------------------
# Exporte 2021/22–2024/25
# --------------------------------------------------------------------------------------------
def lade_einzeltickets_export() -> pd.DataFrame:
    teile = []
    for pfad in sorted(config.TICKETING_DIR.glob(config.EINZELTICKET_GLOB)):
        xl = pd.ExcelFile(pfad, engine="calamine")
        for blatt in xl.sheet_names:
            d = xl.parse(blatt, usecols=lambda c: c in XLSX_SPALTEN)
            # Datumsspalten je Blatt typisieren (leere ZKS-Spalten sonst float → uneinheitlicher concat)
            for c in ("Veranstaltungsdatum", "Bestelldatum", "ZKS-Eintrittsdatum", "ZKS-Übergabedatum"):
                d[c] = pd.to_datetime(d[c], errors="coerce")
            d["datei"] = pfad.name
            teile.append(d)
        logger.info("Einzelticket-Export gelesen: %s", pfad.name)
    df = pd.concat(teile, ignore_index=True)
    assert not set(PERSONENFELDER) & set(df.columns), "Personenfelder dürfen nicht eingelesen werden"

    # Bestellgrösse je Veranstaltung und Auftrag, danach Auftragsnummer verwerfen
    df["bestellung_groesse"] = df.groupby(["Veranstaltung", "Auftrag"])["Preis"].transform("size")
    df = df.drop(columns=["Auftrag"])

    out = pd.DataFrame({
        "quelle": "Export XLSX", "datei": df["datei"],
        "saison_datei": df["Saison-Bez."].astype(str).str.replace(r"(\d{4})/\d{2}(\d{2})", r"\1/\2", regex=True),
        "event_id": df["Veranstaltung"], "event_label": df["Veranstaltungs-Bez."].astype(str),
        "match_datum": pd.to_datetime(df["Veranstaltungsdatum"], errors="coerce").dt.normalize(),
        "event_zeit": df["Veranstaltungszeit"].astype(str).str[:5],
        "preiskategorie": df["Preiskategorie-Bez."].astype(str),
        "verkauf_ts": pd.to_datetime(df["Bestelldatum"], errors="coerce"),
        "kanal_roh": df["Verkaufsmodul-Bez."].astype(str),
        "tarif_roh": df["Verkaufsart-Bez."].astype(str),
        "platzgruppe": df["Platzgruppen-Bez."].astype(str),
        "block": df["Block-Bez."].astype(str),
        "preis": pd.to_numeric(df["Preis"], errors="coerce"),
        "versand": df["Versandart-Bez."].astype(str),
        "status": df["Stornostatus-Bez."].astype(str) + " / " + df["Verkaufsstatus-Bez."].astype(str),
        "anzahl": pd.to_numeric(df["Anzahl Waren"], errors="coerce").fillna(1),
        "eintritt_ts": pd.to_datetime(df["ZKS-Eintrittsdatum"], errors="coerce"),
        "uebergabe_ts": pd.to_datetime(df["ZKS-Übergabedatum"], errors="coerce"),
        "bestellung_groesse": df["bestellung_groesse"],
    })
    out["ist_fcsg_herren_event"] = out["event_label"].str.contains(r"^FC St\.Gallen 1879 - ", regex=True) & \
        ~out["event_label"].str.contains(r"Frauen|Staad|Mitgliedschaft|KIDS|Europatest|Testeuropa|Q3 \(|Spiel 20",
                                         regex=True)
    return _harmonisieren(out)


# --------------------------------------------------------------------------------------------
# CSVs 2025/26–2026/27
# --------------------------------------------------------------------------------------------
def _datei_info(pfad: Path) -> dict:
    m = re.match(r"^(\d{8})_", pfad.name)
    datum = pd.to_datetime(m.group(1), format="%Y%m%d", errors="coerce") if m else pd.NaT
    return {"datei": pfad.name, "ordner": pfad.parent.name, "saison_ordner": pfad.parent.parent.name,
            "datei_datum": datum, "ist_abo": "Saisonabo" in pfad.name,
            "wettbewerb": ORDNER_WETTBEWERB.get(pfad.parent.name, "Andere")}


def _lese_csv(pfad: Path) -> pd.DataFrame:
    d = pd.read_csv(pfad, encoding="utf-8-sig", dtype=str, keep_default_na=False,
                    usecols=lambda c: c in CSV_SPALTEN)
    assert not set(PERSONENFELDER) & set(d.columns), "Personenfelder dürfen nicht eingelesen werden"
    d["bestellung_groesse"] = d.groupby("Rechnung")["Summe"].transform("size")
    return d.drop(columns=["Rechnung"])


def lade_ticket_csvs() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Liefert (einzeltickets, abos, inventar) aus den CSVs der Saisons 2025/26 und 2026/27."""
    pfade = sorted(config.TICKETING_DIR.glob(config.TICKET_CSV_GLOB))
    dateien = pd.DataFrame([{**_datei_info(p), "pfad": p, "blatt": p.name, "zeile": 0} for p in pfade])
    dateien = korrekturen.anwenden(dateien, "Ticket-CSV", {"Datum": "datei_datum"})
    einzel, abos, inventar = [], [], []
    for _, info in dateien.iterrows():
        pfad = info["pfad"]
        d = _lese_csv(pfad)
        verkauf = pd.to_datetime(d["Datum"] + " " + d["Uhrzeit"], format="%d.%m.%Y %H:%M", errors="coerce")
        t = pd.DataFrame({
            "quelle": "CSV", "datei": info["datei"], "wettbewerb_datei": info["wettbewerb"],
            "match_datum": info["datei_datum"], "verkauf_ts": verkauf,
            "kanal_roh": d["Filiale"], "tarif_roh": d["Ermäßigung"], "tribuene_roh": d["Tribüne"],
            "block": d["Block"], "preis": d["Summe"].map(parse_chf), "versand": d["Versandart"],
            "anzahl": 1.0, "bestellung_groesse": pd.to_numeric(d["bestellung_groesse"]),
        })
        inventar.append({**info.drop(["pfad", "blatt", "zeile"]).to_dict(), "zeilen": len(t),
                         "verkauf_min": verkauf.min(), "verkauf_max": verkauf.max(),
                         "negative_betraege": int((t["preis"] < 0).sum()), "betrag_fehlt": int(t["preis"].isna().sum())})
        (abos if info["ist_abo"] else einzel).append(t)
    for ordner in sorted(p for p in config.TICKETING_DIR.glob("20*/*") if p.is_dir()):
        if not any(ordner.glob("*.csv")):
            befund("Ticketing", "mittel", f"Ordner {ordner.relative_to(config.TICKETING_DIR)}",
                   "Ordner ist leer (keine Ticket-CSV).",
                   "Für das zugehörige Spiel (Cup-Viertelfinal 04.02.2026) fehlen Einzelticket-Daten.",
                   "Spiel ohne Einzelticket-Modul geführt; Datei bei Sandro anfragen.")
    inv = pd.DataFrame(inventar)
    for _, r in inv[inv["ist_abo"]].iterrows():
        if pd.isna(r["datei_datum"]):
            befund("Ticketing", "tief", r["datei"], "Dateiname enthält kein gültiges Datum (Stichtag des Abo-Snapshots unklar).",
                   "Stichtag nur über letztes Verkaufsdatum abschätzbar.", f"Stichtag = letzter Verkauf ({r['verkauf_max']:%d.%m.%Y}).")
    e = _harmonisieren(pd.concat(einzel, ignore_index=True))
    a = pd.concat(abos, ignore_index=True)
    a["tarifgruppe"] = [tarifgruppe(x, p) for x, p in zip(a["tarif_roh"], a["preis"])]
    a["tribuene"] = [tribuene_gruppe(b, None, t) for b, t in zip(a["block"], a["tribuene_roh"])]
    a["kanal"] = a["kanal_roh"].map(KANAL_GRUPPE).fillna("Andere")
    a["team"] = np.where(a["datei"].str.contains("Frauen"), "Frauen", "Herren")
    if (inv["negative_betraege"] > 0).any():
        befund("Ticketing", "info", "Ticket-CSVs", "Negative Beträge gefunden (mögliche Stornos).", "-", "Geprüft.")
    else:
        befund("Ticketing", "info", "Ticket-CSVs 2025/26–2026/27",
               "Keine negativen Beträge und keine Statusspalte: Stornos/Rückgaben sind in den Exporten nicht sichtbar.",
               "Verkaufskurven zeigen den Endbestand nach allfälligen Stornos, nicht den historischen Verlauf inkl. Rückgaben.",
               "Als Einschränkung dokumentiert (Klärungsfrage an Sandro).")
    return e, a, inv


def _harmonisieren(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["saison"] = df["match_datum"].map(saison_von)
    df["kanal"] = df["kanal_roh"].map(KANAL_GRUPPE).fillna("Andere")
    df["tarifgruppe"] = [tarifgruppe(t, p) for t, p in zip(df["tarif_roh"], df["preis"])]
    pg = df["platzgruppe"] if "platzgruppe" in df.columns else pd.Series(None, index=df.index)
    tr = df["tribuene_roh"] if "tribuene_roh" in df.columns else pd.Series(None, index=df.index)
    df["tribuene"] = [tribuene_gruppe(b, p, t) for b, p, t in zip(df["block"], pg, tr)]
    df["vorlauf_tage"] = _vorlauf_tage(df["match_datum"], df["verkauf_ts"])
    df["gratis"] = df["preis"].fillna(0) == 0
    return df

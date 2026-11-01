"""Ticketing-Zuschauerzahlen-Historie: eine Zeile pro Event (SOLL, IST, VIP, Gäste, Zweitmarkt).

Neben den Werten werden die Excel-Formeln ausgewertet, weil sie die SOLL-Definition offenlegen:
teils Summe der Ticketkomponenten (Einzeltickets je Filiale + Abos − Zweitmarkt), teils eine
Kapazitätsformel bei ausverkauften Spielen (z.B. =20036-1930+Gäste).
"""
from __future__ import annotations

import re

import numpy as np
import openpyxl
import pandas as pd

from .. import config
from ..log import befund
from ..utils import text, ist_leer, parse_anpfiff, parse_datum, saison_von, wochentag
from . import korrekturen

BLATT = "Zuschauerzahlen"

WETTBEWERB_MAP = {
    "Meisterschaft": "SL", "Cup": "Cup", "Schweizer Cup": "Cup",
    "UEFA Conference League": "UEFA", "UEFA Europa League": "UEFA",
    "Testspiel": "Test", "Nationalmannschaft": "Nati", "Nationalmannschaft Frauen": "Nati Frauen",
    "Meisterschaft Frauen": "Frauen", "Cup Frauen": "Frauen",
}


def _soll_definition(formel, wert, ausverkauft: bool) -> str:
    if isinstance(formel, str) and formel.startswith("="):
        f = formel.replace(" ", "")
        if re.search(r"(20\d{3}|19\d{3})-1930|19200-900|19999-650", f):
            return "Formel: Kapazität (ausverkauft)"
        if f.count("+") >= 3:
            return "Formel: Summe Ticketkomponenten"
        return "Formel: Korrektur/Ergänzung"
    if ist_leer(wert):
        return "fehlt"
    if ausverkauft:
        return "Fixwert (ausverkauft, vermutlich Kapazität)"
    return "Fixwert"


def _ist_definition(formel) -> str:
    if isinstance(formel, str) and formel.startswith("="):
        return "Formel: Scans + Ergänzung"
    return "Fixwert"


def _bool_zelle(v) -> object:
    if ist_leer(v):
        return pd.NA
    if isinstance(v, str):
        t = v.strip().upper().lstrip("=")
        if t in ("TRUE()", "TRUE", "WAHR"):
            return True
        if t in ("FALSE()", "FALSE", "FALSCH"):
            return False
    try:
        return bool(int(v))
    except (TypeError, ValueError):
        return pd.NA


def lade_historie() -> pd.DataFrame:
    """Alle Zeilen der Historie (alle Saisons), mit Definitionsflags und angewendeten Korrekturen."""
    wb_v = openpyxl.load_workbook(config.HISTORIE_FILE, data_only=True)
    wb_f = openpyxl.load_workbook(config.HISTORIE_FILE, data_only=False)
    ws_v, ws_f = wb_v[BLATT], wb_f[BLATT]

    rows = []
    for r in range(2, ws_v.max_row + 1):
        v = [ws_v.cell(r, c).value for c in range(1, 17)]
        f = [ws_f.cell(r, c).value for c in range(1, 17)]
        if all(ist_leer(x) for x in v):
            continue
        datum = parse_datum(v[2])
        ausv_zelle = _bool_zelle(v[14]) if not ist_leer(v[14]) else _bool_zelle(f[14])
        bem = None if ist_leer(v[15]) else str(v[15]).strip()
        ausv_text = bool(bem and re.search(r"ausverkauft", bem, re.I))
        rows.append({
            "blatt": BLATT, "zeile": r,
            "saison_text": v[0], "wettbewerb_text": v[1], "datum": datum,
            "wochentag_text": None if ist_leer(v[3]) else str(v[3]).strip(),
            "anpfiff": parse_anpfiff(v[4]), "spiel_text": v[5],
            "soll": v[6], "ist": v[7], "ist_vip": v[8], "ist_gaeste": v[9], "zweitmarkt": v[10],
            "noshow_blatt": v[11], "auslastung_exkl_gaeste_blatt": v[13],
            "ausverkauft_zelle": ausv_zelle, "ausverkauft_text": ausv_text, "bemerkung": bem,
            "soll_formel": f[6] if isinstance(f[6], str) and f[6].startswith("=") else None,
            "ist_formel": f[7] if isinstance(f[7], str) and f[7].startswith("=") else None,
        })
    df = pd.DataFrame(rows)
    for c in ["soll", "ist", "ist_vip", "ist_gaeste", "zweitmarkt", "noshow_blatt", "auslastung_exkl_gaeste_blatt"]:
        df[c] = pd.to_numeric(df[c], errors="coerce")

    df = korrekturen.anwenden(df, "Historie", {"Datum": "datum", "Anpfiff": "anpfiff"})

    # Saison aus der Spalte «Saison» (COVID-Saison 2019/20 reichte bis August 2020), sonst aus dem Datum
    saison_txt = df["saison_text"].astype(str).str.strip()
    df["saison"] = saison_txt.where(saison_txt.str.fullmatch(r"\d{4}/\d{2}"), df["datum"].map(saison_von))
    df["wettbewerb"] = df["wettbewerb_text"].map(lambda w: WETTBEWERB_MAP.get(str(w).strip(), "Andere"))
    df["ausverkauft"] = df["ausverkauft_zelle"].map(lambda x: x is True) | df["ausverkauft_text"]
    df["soll_definition"] = [
        _soll_definition(fm, w, a) for fm, w, a in zip(df["soll_formel"], df["soll"], df["ausverkauft"])
    ]
    df["ist_definition"] = df["ist_formel"].map(_ist_definition)
    df["noshow_quote"] = np.where(df["soll"] > 0, 1 - df["ist"] / df["soll"], np.nan)
    df["anwesenheitsquote"] = np.where(df["soll"] > 0, df["ist"] / df["soll"], np.nan)
    _pruefungen(df)
    return df


def _pruefungen(df: pd.DataFrame) -> None:
    """Plausibilitätsprüfungen: Wochentag, Ausverkauft-Flag, Reihenfolge."""
    ab = df[df["saison"] >= config.BASELINE_AB_SAISON]
    for _, r in ab.iterrows():
        ort = f"Historie Zeile {r['zeile']} ({r['datum']:%d.%m.%Y}, {r['spiel_text']})"
        if r["wochentag_text"] and wochentag(r["datum"]) and r["wochentag_text"] != wochentag(r["datum"]) \
                and "Datum" not in text(r["korrektur"]):
            befund("Historie", "mittel" if r["wettbewerb"] in config.KERN_WETTBEWERBE else "tief", ort,
                   f"Wochentag «{r['wochentag_text']}» passt nicht zum Datum ({wochentag(r['datum'])}).",
                   "Datum oder Wochentag falsch; Spielzuordnung über Datum unsicher.",
                   "Nicht korrigiert (ausserhalb Kernstichprobe oder ohne Gegenbeleg); an Sandro melden.")
        if r["ausverkauft_text"] and r["ausverkauft_zelle"] is not True and r["wettbewerb"] in config.KERN_WETTBEWERBE:
            befund("Historie", "tief", ort,
                   "Bemerkung nennt «ausverkauft», Spalte «Ausverkauft» ist aber leer/FALSCH.",
                   "Ausverkauft-Flag unvollständig.", "Für Analysen gilt ausverkauft = Flag ODER Bemerkung.")
    kern = ab[ab["wettbewerb"].isin(config.KERN_WETTBEWERBE)]
    for _, r in kern[kern["soll"].isna() | kern["ist"].isna()].iterrows():
        befund("Historie", "mittel", f"Historie Zeile {r['zeile']} ({r['datum']:%d.%m.%Y})",
               "SOLL oder IST fehlt.", "Anwesenheitsquote für dieses Spiel nicht berechenbar.", "Als fehlend geführt.")

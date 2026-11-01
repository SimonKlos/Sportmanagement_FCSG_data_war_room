"""Spielkontext-Tabelle der Gruppe (Blatt «Übersicht» + Tageskalender «Ferien», «Paralellevent», Feiertage).

Leere Zellen bedeuten «nicht erfasst», nicht «Nein» (Auftrag Abschnitt D) und bleiben daher fehlend.
"""
from __future__ import annotations

import re

import numpy as np
import openpyxl
import pandas as pd

from .. import config
from ..log import befund
from ..utils import (form_punkte, gegner_kanonisch, ist_leer, ja_nein, parse_anpfiff, parse_datum, parse_zahl,
                     saison_von, text)

# Spielkontext-Tabelle Version 5 (14.10.2026, vom Team bestätigt, D-034). Im Repo angepasst (D-028): Version 3 wird
# nicht mehr unterstützt. Rang/Punkte stehen als Zahlen in eigenen Spalten, Wetter bezieht sich auf die
# Anstossstunde (MeteoSchweiz STG), Schulferien = Stadt St.Gallen.
_SPALTEN = {
    "Datum": "datum", "Wochentag": "wochentag_text", "Anstoss (Lokalzeit)": "anpfiff_text",
    "Wettbewerb": "wettbewerb_text", "Spieltag / Runde": "spieltag_runde", "Gegner": "gegner_text",
    "Gegner-Kategorie": "gegner_kategorie", "Resultat (FCSG : Gegner)": "resultat",
    "Platzierung FCSG vor Spiel": "rang_fcsg_kontext", "Punkte FCSG vor Spiel": "punkte_fcsg_kontext",
    "Platzierung Gegner vor Spiel": "rang_gegner_kontext", "Punkte Gegner vor Spiel": "punkte_gegner_kontext",
    "Form FCSG (letzte 5 SL-Spiele)": "form_fcsg_text", "Form Gegner (letzte 5 SL-Spiele)": "form_gegner_text",
    "TV-Übertragung": "tv", "Free-TV (SRF)": "free_tv_text", "Temperatur Anstossstunde (°C)": "temperatur_text",
    "Niederschlag 1 h vor bis 2 h nach Anstoss (mm)": "niederschlag_text", "Wind Anstossstunde (km/h)": "wind_text",
    "Schulferien Stadt SG": "schulferien_text", "Feiertag Kt. SG": "feiertag_text",
    "Parallelevent Stadt SG": "parallelevent_text", "Covid-Massnahmen": "covid_text",
    "Quelle / Bemerkungen": "quelle_bemerkung",
}


def _wettbewerb(wert: str) -> str:
    t = text(wert).lower()
    if "super league" in t or "meisterschaftsrunde" in t or "abstiegsrunde" in t:
        return "SL"
    if "cup" in t and "league" not in t:
        return "Cup"
    if "league" in t:
        return "UEFA"
    return "Andere"


def lade_kontext() -> pd.DataFrame:
    if not config.KONTEXT_FILE.exists():
        befund("Kontext", "hoch", str(config.KONTEXT_FILE), "Spielkontext-Tabelle nicht gefunden.",
               "Keine Kontextvariablen aus der Gruppentabelle.", "Nur abgeleitete Kontextvariablen verwendet.")
        return pd.DataFrame()
    ws = openpyxl.load_workbook(config.KONTEXT_FILE, data_only=True)["Übersicht"]
    kopf = {str(ws.cell(1, c).value).strip(): c for c in range(1, ws.max_column + 1) if ws.cell(1, c).value}
    fehlend = [h for h in _SPALTEN if h not in kopf]
    if fehlend:
        raise ValueError(f"Spielkontext-Tabelle (Blatt «Übersicht»): Spalten der Version 5 fehlen: {fehlend}")
    rows = []
    for r in range(2, ws.max_row + 1):
        werte = {name: ws.cell(r, kopf[h]).value for h, name in _SPALTEN.items()}
        if ist_leer(werte.get("datum")):
            continue
        werte["zeile"] = r
        rows.append(werte)
    df = pd.DataFrame(rows)
    df["datum"] = df["datum"].map(parse_datum)
    df["saison"] = df["datum"].map(saison_von)
    df["anpfiff"] = df["anpfiff_text"].map(parse_anpfiff)
    df["wettbewerb"] = df["wettbewerb_text"].map(_wettbewerb)
    df["gegner"] = df["gegner_text"].map(gegner_kanonisch)
    for wer in ("fcsg", "gegner"):
        df[f"rang_{wer}_kontext"] = df[f"rang_{wer}_kontext"].map(parse_zahl)
        df[f"punkte_{wer}_kontext"] = df[f"punkte_{wer}_kontext"].map(parse_zahl)
        form = df[f"form_{wer}_text"].map(form_punkte)
        df[f"form_{wer}_punkte_kontext"] = [x[0] for x in form]
        df[f"form_{wer}_spiele_kontext"] = [x[1] for x in form]
    df["free_tv_srf"] = df["free_tv_text"].map(lambda t: pd.NA if ist_leer(t) else ja_nein(t))
    # Name aus v1.1.0 beibehalten: enthält in Version 5 die Temperatur der Anstossstunde (siehe Befund unten).
    df["temp_tagesmittel"] = df["temperatur_text"].map(parse_zahl)
    df["niederschlag_tag_mm"] = df["niederschlag_text"].map(parse_zahl)
    df["wind_tag_kmh"] = df["wind_text"].map(parse_zahl)
    df["schulferien"] = df["schulferien_text"].map(lambda t: pd.NA if str(t).strip().lower() == "n/a" else ja_nein(t))
    df["feiertag"] = df["feiertag_text"].map(ja_nein)
    df["parallelevent"] = df["parallelevent_text"].map(ja_nein)
    df["covid"] = df["covid_text"].map(ja_nein)
    df["besondere_anlaesse"] = pd.NA  # Spalte gibt es in Version 5 nicht mehr
    df["resultat_bekannt"] = df["resultat"].map(lambda x: not ist_leer(x))
    befund("Kontext", "info", "Spielkontext-Tabelle Version 5",
           "Temperatur/Wind beziehen sich auf die Anstossstunde, Niederschlag auf 1 h vor bis 2 h nach Anstoss "
           "(MeteoSchweiz STG); Schulferien = Stadt St.Gallen.",
           "Die Spalte temp_tagesmittel enthält die Temperatur der Anstossstunde aus der Gruppentabelle; die "
           "Sensitivität «Tagesmittel statt Anpfiff» vergleicht damit zwei Quellen derselben Grösse.",
           "Hauptmodell nutzt weiterhin die eigenen MeteoSchweiz-Stundenwerte zum Anpfiff.")
    return df


def lade_kalender() -> pd.DataFrame:
    """Tageskalender aus der Kontextdatei: Schulfrei, Parallelevents, Feiertage (für Spiele ohne Kontextzeile)."""
    if not config.KONTEXT_FILE.exists():
        return pd.DataFrame(columns=["datum"])
    wb = openpyxl.load_workbook(config.KONTEXT_FILE, data_only=True)
    teile = []
    if "Ferien" in wb.sheetnames:
        ws = wb["Ferien"]
        kopf = {str(ws.cell(1, c).value).strip(): c for c in range(1, ws.max_column + 1) if ws.cell(1, c).value}
        rows = []
        for r in range(2, ws.max_row + 1):
            d = ws.cell(r, kopf["Datum"]).value
            if ist_leer(d):
                continue
            sf = ws.cell(r, kopf.get("Schulfrei (Ferien oder Einzeltag)", kopf.get("Schulferien Stadt SG"))).value
            rows.append({"datum": parse_datum(d), "schulfrei_kalender": ja_nein(sf) if str(sf).lower() != "n/a" else pd.NA})
        teile.append(pd.DataFrame(rows).set_index("datum"))
    if "Paralellevent" in wb.sheetnames:
        ws = wb["Paralellevent"]
        kopf = {str(ws.cell(1, c).value).strip(): c for c in range(1, ws.max_column + 1) if ws.cell(1, c).value}
        spalte = next((c for h, c in kopf.items() if h.startswith("relevanter Parallelevent")), None)
        namen = kopf.get("Parallelevents")
        rows = []
        for r in range(2, ws.max_row + 1):
            d = ws.cell(r, kopf["Datum"]).value
            if ist_leer(d) or spalte is None:
                continue
            rows.append({"datum": parse_datum(d), "parallelevent_kalender": ja_nein(ws.cell(r, spalte).value),
                         "parallelevent_namen": ws.cell(r, namen).value if namen else None})
        teile.append(pd.DataFrame(rows).set_index("datum"))
    if "Hilfsdaten" in wb.sheetnames:
        ws = wb["Hilfsdaten"]
        rows = [{"datum": parse_datum(ws.cell(r, 1).value), "feiertag_name": ws.cell(r, 2).value}
                for r in range(3, ws.max_row + 1) if not ist_leer(ws.cell(r, 1).value)
                and not pd.isna(parse_datum(ws.cell(r, 1).value))]
        teile.append(pd.DataFrame(rows).drop_duplicates("datum").set_index("datum"))
    if not teile:
        return pd.DataFrame(columns=["datum"])
    kal = pd.concat(teile, axis=1).reset_index().rename(columns={"index": "datum"})
    kal["feiertag_kalender"] = kal["feiertag_name"].notna()
    return kal

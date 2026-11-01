"""Zutrittsdaten (erlaubte Drehkreuz-Durchgänge) der Herren: drei Lieferungen, ein Format.

* zugangsdaten_herren_inhouse.csv   – Saisons 2022/23 und 2023/24 (ohne Kopfzeile, Semikolon)
* zugangsdaten_herren_alteSaisons.txt – 2023/24 (Duplikate) und 2024/25 (ab Januar 2025 vollständig)
* ErlaubteZutritteHerren.xlsx         – 2025/26 und 2026/27 (Retos Sichtung: 27 Spiele)

Die pseudonyme Ticket-ID (Barcode/UTId) wird ausschliesslich technisch verwendet: exakte Duplikate
entfernen und pro Spiel den ersten Durchgang je Ticket bestimmen. Danach wird sie verworfen und
erscheint in keinem Resultat (Auftrag Abschnitt B und 8).
"""
from __future__ import annotations

import re

import numpy as np
import pandas as pd

from .. import config
from ..utils import text
from ..log import befund, logger

_SPALTEN_ALT = ["Matchday", "Spieltag", "TransactionTime", "Barcode", "TicketData", "Coding",
                "Lesername", "Seatinfo", "Errorcode", "DisplayMessage"]
_BENOETIGT = ["Matchday", "Spieltag", "TransactionTime", "Barcode", "Coding", "Lesername", "Seatinfo", "Errorcode"]


def sektor_gruppe(leser: str) -> str:
    """Physischer Eingang aus dem Lesernamen: A, B (Heim), B4 (Gäste), C, D oder HH (Hospitality-Eingänge)."""
    t = text(leser)
    if t.startswith("HH"):
        return "HH (Hospitality)"
    m = re.match(r"([ABCD])(\d)", t)
    if not m:
        return "Unbekannt"
    if m.group(1) == "B" and m.group(2) == "4":
        return "B4 (Gäste)"
    return m.group(1)


def _lese_rohdaten() -> pd.DataFrame:
    teile = []
    if config.ZUTRITT_INHOUSE_FILE.exists():
        d = pd.read_csv(config.ZUTRITT_INHOUSE_FILE, sep=";", header=None, names=_SPALTEN_ALT,
                        encoding="utf-8-sig", dtype=str, usecols=_BENOETIGT)
        d["lieferung"] = config.ZUTRITT_INHOUSE_FILE.name
        teile.append(d)
    if config.ZUTRITT_ALT_FILE.exists():
        d = pd.read_csv(config.ZUTRITT_ALT_FILE, sep="\t", dtype=str, usecols=_BENOETIGT)
        d["lieferung"] = config.ZUTRITT_ALT_FILE.name
        teile.append(d)
    if config.ZUTRITT_ERLAUBT_FILE.exists():
        d = pd.read_excel(config.ZUTRITT_ERLAUBT_FILE, engine="calamine", dtype=str,
                          usecols=["Datum", "Spieltag", "TransactionTime", "UTId", "Coding", "Lesername",
                                   "Seatinfo", "Errorcode"])
        d = d.rename(columns={"Datum": "Matchday", "UTId": "Barcode"})
        d["lieferung"] = config.ZUTRITT_ERLAUBT_FILE.name
        teile.append(d)
    df = pd.concat(teile, ignore_index=True)
    df["datum"] = pd.to_datetime(df["Matchday"].str[:10], format="%Y-%m-%d", errors="coerce")
    df["ts"] = pd.to_datetime(df["TransactionTime"].str[:19], format="%Y-%m-%d %H:%M:%S", errors="coerce")
    return df


def lade_zutritt() -> tuple[pd.DataFrame, pd.DataFrame]:
    """Liefert (ankuenfte, spiel_info).

    ``ankuenfte``: erster erlaubter Durchgang je Ticket und Spiel (ohne Ticket-ID).
    ``spiel_info``: je Spieltag Rohzeilen, Duplikate, Mehrfachscans, Leser und Lieferung.
    """
    df = _lese_rohdaten()
    roh = df.groupby("datum").size().rename("scans_roh")
    nicht_null = (df["Errorcode"].fillna("0") != "0").sum()
    if nicht_null:
        befund("Zutritt", "mittel", "Zutrittsdateien", f"{nicht_null} Zeilen mit Errorcode ≠ 0.",
               "Nicht erlaubte Durchgänge in den Daten.", "Ausgeschlossen.")
        df = df[df["Errorcode"].fillna("0") == "0"]

    vor = len(df)
    df = df.drop_duplicates(["datum", "Barcode", "TransactionTime"])
    exakte_dup = vor - len(df)
    if exakte_dup:
        befund("Zutritt", "info", "zugangsdaten_herren_alteSaisons.txt",
               f"{exakte_dup} Zeilen sind exakte Duplikate (gleiches Spiel, Ticket und Zeitstempel) aus einer zweiten Lieferung.",
               "Ohne Bereinigung doppelt gezählte Besucher.", "Exakte Duplikate entfernt.")

    df = df.sort_values(["datum", "Barcode", "ts"])
    df["scan_nr"] = df.groupby(["datum", "Barcode"]).cumcount() + 1
    mehrfach = df[df["scan_nr"] == 2].groupby("datum").size().rename("tickets_mehrfach_gescannt")
    first = df[df["scan_nr"] == 1].copy()

    info = first.groupby("datum").agg(
        spieltag_label=("Spieltag", "first"), lieferung=("lieferung", "first"),
        besucher_scans=("Barcode", "size"), erster_scan=("ts", "min"), letzter_scan=("ts", "max"),
        leser_aktiv=("Lesername", "nunique"),
    ).join(roh).join(mehrfach).fillna({"tickets_mehrfach_gescannt": 0}).reset_index()
    info["anteil_mehrfach"] = info["tickets_mehrfach_gescannt"] / info["besucher_scans"]

    ank = first[["datum", "ts", "Lesername", "Seatinfo", "Coding", "lieferung"]].rename(
        columns={"Lesername": "leser", "Seatinfo": "seatinfo", "Coding": "coding"})
    ank["sektor"] = ank["leser"].map(sektor_gruppe)
    ank["kartentyp"] = np.where(ank["coding"].isin(["16777235", "16777348"]), "Chipkarte", "Barcode")
    logger.info("Zutritt: %s erste Durchgänge in %s Spielen", f"{len(ank):,}", ank["datum"].nunique())
    return ank.reset_index(drop=True), info


def lade_zutritt_frauen() -> pd.DataFrame:
    """Frauen-Zutritte (nur Inventar; nicht Teil der Kernstichprobe)."""
    if not config.ZUTRITT_FRAUEN_FILE.exists():
        return pd.DataFrame()
    d = pd.read_csv(config.ZUTRITT_FRAUEN_FILE, sep="\t", dtype=str,
                    usecols=["Datum", "Spieltag", "TransactionTime", "Barcode"])
    d["datum"] = pd.to_datetime(d["Datum"].str[:10], errors="coerce")
    out = d.groupby(["datum", "Spieltag"]).agg(scans=("Barcode", "size"), besucher=("Barcode", "nunique")).reset_index()
    return out

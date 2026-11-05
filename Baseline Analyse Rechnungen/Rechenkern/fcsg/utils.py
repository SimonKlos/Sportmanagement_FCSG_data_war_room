"""Robuste Parser für die uneinheitlichen Formate in den FCSG-Dateien."""
from __future__ import annotations

import datetime as dt
import math
import re

import numpy as np
import pandas as pd

from . import config

WOCHENTAGE = ["Montag", "Dienstag", "Mittwoch", "Donnerstag", "Freitag", "Samstag", "Sonntag"]
_MONATE = {"januar": 1, "jänner": 1, "februar": 2, "märz": 3, "maerz": 3, "april": 4, "mai": 5, "juni": 6,
           "juli": 7, "august": 8, "september": 9, "oktober": 10, "november": 11, "dezember": 12}


def ist_leer(value) -> bool:
    if value is None:
        return True
    if isinstance(value, float) and math.isnan(value):
        return True
    if value is pd.NaT:
        return True
    if isinstance(value, str) and value.strip() == "":
        return True
    try:
        return bool(pd.isna(value))
    except (TypeError, ValueError):
        return False


def text(value) -> str:
    """Text oder leerer String für fehlende Werte (None, NaN, pd.NA) – identisch unter pandas 2 und 3."""
    return "" if ist_leer(value) else str(value)


def als_bool(s: pd.Series) -> pd.Series:
    """Wahrheitswerte aus gemischten Spalten (True/False/NaN/pd.NA); fehlend = False."""
    return s.map(lambda v: (not ist_leer(v)) and bool(v)).astype(bool)


def saison_von(datum) -> str | None:
    """Saison im Format '2025/26' (Saisonwechsel am 1. Juli)."""
    if ist_leer(datum):
        return None
    ts = pd.Timestamp(datum)
    start = ts.year if ts.month >= 7 else ts.year - 1
    return f"{start}/{str(start + 1)[-2:]}"


def saison_index(saison: str) -> int:
    """'2025/26' -> 2025 (für Sortierung und Trends)."""
    return int(str(saison)[:4])


def parse_datum(value) -> pd.Timestamp:
    """Datum aus Excel-Werten oder Texten wie 'Mittwoch, 27. September 2023' oder '17.05.2026'.

    Mehrtägige Angaben ('15./16. August 2025', '29.05.-02.06.2023') ergeben NaT, weil sie keinem
    einzelnen Spieltag zugeordnet werden können.
    """
    if ist_leer(value):
        return pd.NaT
    if isinstance(value, (dt.datetime, pd.Timestamp)):
        return pd.Timestamp(value).normalize()
    if isinstance(value, dt.date):
        return pd.Timestamp(value)
    text = str(value).strip()
    if re.search(r"\d\s*[./]\s*-|\bbis\b|\bund\b|–|\s-\s|\d\.\s*/\s*\d", text):
        return pd.NaT
    m = re.fullmatch(r"(\d{4})-(\d{2})-(\d{2})(?:[ T].*)?", text)
    if m:
        return pd.Timestamp(int(m.group(1)), int(m.group(2)), int(m.group(3)))
    m = re.fullmatch(r"(\d{1,2})\.(\d{1,2})\.(\d{4})", text)
    if m:
        return pd.Timestamp(int(m.group(3)), int(m.group(2)), int(m.group(1)))
    m = re.search(r"(\d{1,2})[.,]?\s+([A-Za-zäÄ]+)\s+(\d{4})", text)
    if m and m.group(2).lower() in _MONATE:
        return pd.Timestamp(int(m.group(3)), _MONATE[m.group(2).lower()], int(m.group(1)))
    return pd.NaT


def parse_anpfiff(value) -> str | None:
    """Anstosszeit als 'HH:MM'. Excel-Zahlen wie 20.3 bedeuten 20:30, 14.15 bedeutet 14:15.

    Zeitspannen ('13.00 - 17.00 Uhr') oder Texte ohne eindeutige Uhrzeit ergeben None.
    """
    if ist_leer(value):
        return None
    if isinstance(value, (dt.datetime, pd.Timestamp)):
        return f"{value.hour:02d}:{value.minute:02d}"
    if isinstance(value, dt.time):
        return f"{value.hour:02d}:{value.minute:02d}"
    if isinstance(value, (int, np.integer)):
        return f"{int(value):02d}:00" if 0 <= int(value) <= 23 else None
    if isinstance(value, (float, np.floating)):
        h = int(value)
        m = int(round((float(value) - h) * 100))   # 20.3 -> 30, 14.15 -> 15
        return f"{h:02d}:{m:02d}" if 0 <= h <= 23 and 0 <= m < 60 else None
    text = str(value).strip().lower().replace("uhr", "").strip()
    if re.search(r"\d\s*-\s*\d|ab\s|nachmittag|abend|tbd", text):
        return None
    m = re.fullmatch(r"(\d{1,2})[.:](\d{1,2})", text)
    if m:
        h, mi = int(m.group(1)), m.group(2)
        mi = int(mi) * (10 if len(mi) == 1 else 1)
        return f"{h:02d}:{mi:02d}" if 0 <= h <= 23 and 0 <= mi < 60 else None
    m = re.fullmatch(r"(\d{1,2})", text)
    if m and 0 <= int(m.group(1)) <= 23:
        return f"{int(m.group(1)):02d}:00"
    return None


def minuten(hhmm: str | None) -> float:
    if not hhmm:
        return np.nan
    h, m = hhmm.split(":")
    return int(h) * 60 + int(m)


def parse_chf(value) -> float:
    """Beträge wie '25,00 CHF', '1.303,00\xa0CHF', "1'234.50" oder Zahlen."""
    if ist_leer(value):
        return np.nan
    if isinstance(value, (int, float, np.integer, np.floating)):
        return float(value)
    t = str(value).replace("CHF", "").replace("\xa0", "").replace(" ", "").replace("'", "").replace("’", "")
    if t in ("", "-"):
        return np.nan
    if "," in t:
        t = t.replace(".", "").replace(",", ".")
    try:
        return float(t)
    except ValueError:
        return np.nan


def parse_zahl(value) -> float:
    """Erste Zahl aus Texten wie '19.9°C (Tagesmittel; ...)', '2.9 mm' oder '-3.8°C'."""
    if ist_leer(value):
        return np.nan
    if isinstance(value, (int, float, np.integer, np.floating)):
        return float(value)
    m = re.search(r"-?\d+(?:[.,]\d+)?", str(value))
    return float(m.group(0).replace(",", ".")) if m else np.nan


def zahl_oder_nan(value) -> float:
    """Numerische Zellen; Texte wie 'keine Angabe' werden zu NaN (fehlend, nicht null)."""
    if ist_leer(value):
        return np.nan
    if isinstance(value, (int, float, np.integer, np.floating)) and not isinstance(value, bool):
        return float(value)
    return np.nan


def parse_rang(text) -> tuple[float, float]:
    """'7. Platz, 0 Pkt' -> (7, 0). Fehlende/nicht anwendbare Angaben -> (nan, nan)."""
    if ist_leer(text):
        return np.nan, np.nan
    m = re.search(r"(\d+)\.\s*Platz,\s*(\d+)\s*Pkt", str(text))
    if not m:
        return np.nan, np.nan
    return float(m.group(1)), float(m.group(2))


def form_punkte(text) -> tuple[float, float]:
    """Form-String 'S-U-N-S' -> (Punkte, Anzahl Spiele). S=3, U=1, N=0."""
    if ist_leer(text):
        return np.nan, np.nan
    tokens = [t for t in re.split(r"[-\s]+", str(text).strip().upper()) if t in ("S", "U", "N")]
    if not tokens:
        return np.nan, np.nan
    return float(sum({"S": 3, "U": 1, "N": 0}[t] for t in tokens)), float(len(tokens))


def ja_nein(value) -> object:
    """'Ja'/'Nein' -> True/False; Feiertagsnamen ('Ostermontag') -> True; leer -> pd.NA (nicht erfasst)."""
    if ist_leer(value):
        return pd.NA
    t = str(value).strip().lower()
    if t in ("nein", "no", "0", "false", "n/a"):
        return False
    return True


def mwst_satz(datum) -> float:
    return config.MWST_NEU if pd.Timestamp(datum) >= pd.Timestamp(config.MWST_WECHSEL) else config.MWST_ALT


def wochentag(datum) -> str | None:
    if ist_leer(datum):
        return None
    return WOCHENTAGE[pd.Timestamp(datum).weekday()]


def anpfiff_slot(hhmm: str | None) -> str | None:
    """Gruppierung der Anstosszeiten: Mittag/Nachmittag (<17 Uhr), Vorabend (17-19.59), Abend (>=20)."""
    m = minuten(hhmm)
    if np.isnan(m):
        return None
    if m < 17 * 60:
        return "Nachmittag (<17 Uhr)"
    if m < 20 * 60:
        return "Vorabend (17-19 Uhr)"
    return "Abend (ab 20 Uhr)"


def anstoss_slot(wochentag_: str | None, hhmm: str | None) -> str | None:
    """Anstoss-Slot aus Wochentag und Anpfiffzeit (config.SLOTS, Referenz Samstag 17–19.59 Uhr).

    Fehlende Anpfiffzeit bleibt fehlend. Mo–Fr und (bisher nicht beobachtet) Sonntag ab 17 Uhr = Werktagabend.
    """
    m = minuten(hhmm) if isinstance(hhmm, str) else np.nan
    if np.isnan(m):
        return None
    if m < 17 * 60:
        return config.SLOTS["slot_nachmittag"]
    if wochentag_ == "Samstag":
        return config.REFERENZ_SLOT if m < 20 * 60 else config.SLOTS["slot_sa_abend"]
    return config.SLOTS["slot_werktag_abend"]


_TEAM_MUSTER = [
    (r"lausanne[- ]?ouchy|stade[- ]lausanne|\bslo\b", "Lausanne Ouchy"),
    (r"lausanne|\bls\b", "Lausanne"),
    (r"young boys|\byb\b|bsc yb|\bbsc\b", "Young Boys"),
    (r"grasshopper|\bgcz?\b|gc zürich", "Grasshoppers"),
    (r"\bfcz\b|zürich|zurich", "Zurich"),
    (r"basel|\bfcb\b", "Basel"),
    (r"luzern|\bfcl\b", "Luzern"),
    (r"lugano|\blug\b", "Lugano"),
    (r"servette|\bsfc\b", "Servette"),
    (r"\bsion\b|\bfcs\b|\bsio\b", "Sion"),
    (r"winterthur|winterhtur|\bfcw\b", "Winterthur"),   # «Winterhtur»: Tippfehler in der Catering-Datei
    (r"thun|\bfct\b", "Thun"),
    (r"vaduz", "Vaduz"),
    (r"yverdon|\bys\b", "Yverdon"),
    (r"aarau|\bfca\b", "Aarau"),
    (r"xamax", "Xamax"),
    (r"münsingen", "Münsingen"),
    (r"tobol", "Tobol"),
    (r"slask|śląsk|wroclaw|wrocław", "Slask Wroclaw"),
    (r"trabzon", "Trabzonspor"),
    (r"fiorentina", "Fiorentina"),
    (r"\btsc\b|topola|fktsc", "TSC Backa Topola"),
    (r"vitoria|vitória|guimar", "Vitoria Guimaraes"),
    (r"benfica", "Benfica"),
    (r"sheriff", "Sheriff Tiraspol"),
    (r"nordsj", "Nordsjaelland"),
]


def gegner_kanonisch(text) -> str | None:
    """Gegner aus Bezeichnungen wie 'FCSG - FC Luzern', 'BSL25/26: FCB' oder 'FC St.Gallen 1879 - GC'.

    Nur für Anzeige und Kontrollen – verknüpft wird ausschliesslich über das Datum (Auftrag 3.1).
    """
    if ist_leer(text):
        return None
    t = str(text).lower().replace("_", " ")
    t = re.sub(r"^.*?:\s*", "", t) if re.match(r"^(bsl|uecl|uel|ch-cup|awsl)", t) else t
    t = re.sub(r"fc\s*st\.?\s*gallen(\s*1879)?|fcsg|st\.?\s*gallen", " ", t)
    for muster, name in _TEAM_MUSTER:
        if re.search(muster, t):
            return name
    return None


def anzeige_gegner(name: str | None) -> str | None:
    if name is None:
        return None
    return config.TEAM_ANZEIGE.get(name, name)

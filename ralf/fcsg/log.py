"""Protokoll der Datenqualitäts-Befunde und des Pipeline-Ablaufs.

Jeder Befund wird mit Ort (Datei/Blatt/Zeile), Auswirkung und Behandlung festgehalten, damit
alle Zahlen bis zur Transformation rückverfolgbar sind (Abnahmekriterium «Quellenpfad»).
"""
from __future__ import annotations

import logging
from dataclasses import asdict, dataclass

import pandas as pd

logger = logging.getLogger("fcsg")


def setup_logging(level: int = logging.INFO) -> None:
    logging.basicConfig(level=level, format="%(asctime)s  %(levelname)-7s %(message)s", datefmt="%H:%M:%S")


@dataclass
class Befund:
    bereich: str        # Quelle bzw. Modul, z.B. «Historie», «Catering», «Zutritt»
    schweregrad: str    # hoch | mittel | tief | info
    ort: str            # Datei, Blatt, Zeile/Zelle oder Spiel
    befund: str
    auswirkung: str
    behandlung: str


_BEFUNDE: list[Befund] = []


def befund(bereich: str, schweregrad: str, ort: str, text: str, auswirkung: str, behandlung: str) -> None:
    """Registriert einen Datenqualitäts-Befund (doppelte Einträge werden ignoriert)."""
    item = Befund(bereich, schweregrad, ort, text, auswirkung, behandlung)
    if item not in _BEFUNDE:
        _BEFUNDE.append(item)


def befunde_tabelle() -> pd.DataFrame:
    order = {"hoch": 0, "mittel": 1, "tief": 2, "info": 3}
    df = pd.DataFrame([asdict(b) for b in _BEFUNDE],
                      columns=["bereich", "schweregrad", "ort", "befund", "auswirkung", "behandlung"])
    if df.empty:
        return df
    df["_o"] = df["schweregrad"].map(order).fillna(9)
    return df.sort_values(["_o", "bereich", "ort"]).drop(columns="_o").reset_index(drop=True)


def reset() -> None:
    _BEFUNDE.clear()

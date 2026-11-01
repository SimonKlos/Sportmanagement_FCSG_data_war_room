"""Belegte manuelle Korrekturen (overrides/korrekturen.csv).

Eine Korrektur wird nur angewendet, wenn der aktuelle Wert noch dem dokumentierten Altwert
entspricht. Ändert Sandro die Quelldatei, greift die Korrektur nicht mehr und erscheint als Befund.
"""
from __future__ import annotations

import pandas as pd

from .. import config
from ..log import befund, logger


def lade_korrekturen() -> pd.DataFrame:
    if not config.OVERRIDES_FILE.exists():
        return pd.DataFrame(columns=["quelle", "blatt", "zeile", "feld", "alt", "neu", "begruendung"])
    df = pd.read_csv(config.OVERRIDES_FILE, sep=";", dtype=str, encoding="utf-8")
    df["zeile"] = df["zeile"].astype(int)
    return df


def anwenden(df: pd.DataFrame, quelle: str, spalten: dict[str, str]) -> pd.DataFrame:
    """Wendet Korrekturen auf ``df`` an.

    ``df`` braucht die Spalten ``blatt`` und ``zeile`` (Excel-Zeilennummer). ``spalten`` ordnet die
    Feldnamen der Korrekturdatei (z.B. 'Datum') den Spalten in ``df`` zu (z.B. 'datum').
    """
    korr = lade_korrekturen()
    korr = korr[korr["quelle"] == quelle]
    out = df.copy()
    if "korrektur" not in out.columns:
        out["korrektur"] = ""
    for _, k in korr.iterrows():
        spalte = spalten.get(k["feld"])
        mask = (out["blatt"] == k["blatt"]) & (out["zeile"] == k["zeile"])
        if spalte is None or not mask.any():
            befund(quelle, "mittel", f"{k['blatt']} Zeile {k['zeile']}",
                   f"Korrektur «{k['feld']}: {k['alt']} -> {k['neu']}» findet keine passende Zeile.",
                   "Korrektur wirkungslos.", "Korrekturdatei prüfen (Quelldatei geändert?).")
            continue
        aktuell = out.loc[mask, spalte].iloc[0]
        aktuell_txt = aktuell.strftime("%Y-%m-%d") if isinstance(aktuell, pd.Timestamp) else str(aktuell)
        if aktuell_txt != k["alt"]:
            befund(quelle, "mittel", f"{k['blatt']} Zeile {k['zeile']}",
                   f"Korrektur nicht angewendet: aktueller Wert «{aktuell_txt}» statt dokumentiert «{k['alt']}».",
                   "Quelle wurde vermutlich bereits korrigiert oder verschoben.", "Korrekturdatei prüfen.")
            continue
        neu = pd.Timestamp(k["neu"]) if isinstance(aktuell, pd.Timestamp) else k["neu"]
        out.loc[mask, spalte] = neu
        out.loc[mask, "korrektur"] = (out.loc[mask, "korrektur"] + f"{k['feld']}: {k['alt']} -> {k['neu']}; ").str.strip()
        befund(quelle, "hoch", f"{k['blatt']} Zeile {k['zeile']}",
               f"{k['feld']} «{k['alt']}» ist widersprüchlich: {k['begruendung']}",
               "Ohne Korrektur falsche Spielzuordnung bzw. falsche Ankunftszeiten.",
               f"Belegt korrigiert auf «{k['neu']}» (overrides/korrekturen.csv); an Sandro melden.")
        logger.info("Korrektur %s %s Zeile %s: %s %s -> %s", quelle, k["blatt"], k["zeile"], k["feld"], k["alt"], k["neu"])
    return out

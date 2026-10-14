"""Pfade, Scope-Definitionen und fachliche Konstanten.

Datenordner und Kontexttabelle lassen sich beim Start angeben, damit das Projekt auch auf einem
anderen Rechner (z.B. bei Simon) ohne Codeänderung läuft. Vorrang: Kommandozeile > Umgebungsvariable >
Standardablage im Projektordner.

    run_all.py --daten     bzw. FCSG_DATA_DIR      Ordner «1. Daten FCSG» (Rohdaten von Sandro)
    run_all.py --kontext   bzw. FCSG_KONTEXT_FILE  Spielkontext-Tabelle (Excel)
    run_all.py --ausgabe   bzw. FCSG_OUTPUT_DIR    Zielordner für Ergebnisse (nur Aggregate)
    run_all.py --ideen-ausgabe bzw. FCSG_IDEEN_DIR Zielordner der Ideen-Grundlage (nur Aggregate)
"""
from __future__ import annotations

import os
from pathlib import Path

# --------------------------------------------------------------------------------------------
# Pfade
# --------------------------------------------------------------------------------------------
CODE_DIR = Path(__file__).resolve().parents[1]      # .../2. Modellierung/Python_Auswertung
MODEL_DIR = CODE_DIR.parent                          # .../2. Modellierung
PROJECT_ROOT = MODEL_DIR.parent                      # .../Sportmanagement

OUTPUT_DIR = Path(os.environ.get("FCSG_OUTPUT_DIR", MODEL_DIR / "Ergebnisse_Phase1"))
IDEEN_DIR = Path(os.environ.get("FCSG_IDEEN_DIR", MODEL_DIR / "Ergebnisse_Ideen_Grundlage"))

OVERRIDES_FILE = CODE_DIR / "overrides" / "korrekturen.csv"
ARTIKEL_BASIS_FILE = CODE_DIR / "overrides" / "artikel_basis.csv"
EXTERNAL_DIR = CODE_DIR / "external"
WETTER_FILE = EXTERNAL_DIR / "meteoschweiz_stg_stuendlich.csv"
RESULTATE_FILE = EXTERNAL_DIR / "football_data_super_league.csv"

KIESPLATZ_GLOB = "Abrechnung Kiesplatz_Saison *.xlsx"
EINZELTICKET_GLOB = "*/Einzeltickets_*.xlsx"
TICKET_CSV_GLOB = "20*/*/*.csv"

# Rohdatenpfade: gesetzt durch setze_datenpfade() (beim Import und erneut durch run_all.py --daten/--kontext)
DATA_DIR: Path
KONTEXT_FILE: Path
TICKETING_DIR: Path
CATERING_DIR: Path
ZUTRITT_DIR: Path
HISTORIE_FILE: Path
CATERING_FILE: Path
ARTIKEL_FILE: Path
ZUTRITT_ERLAUBT_FILE: Path
ZUTRITT_INHOUSE_FILE: Path
ZUTRITT_ALT_FILE: Path
ZUTRITT_FRAUEN_FILE: Path


def setze_datenpfade(daten: str | Path | None = None, kontext: str | Path | None = None) -> None:
    """Rohdatenordner und Kontexttabelle festlegen und alle davon abgeleiteten Pfade neu bilden."""
    global DATA_DIR, KONTEXT_FILE, TICKETING_DIR, CATERING_DIR, ZUTRITT_DIR, HISTORIE_FILE, CATERING_FILE
    global ARTIKEL_FILE, ZUTRITT_ERLAUBT_FILE, ZUTRITT_INHOUSE_FILE, ZUTRITT_ALT_FILE, ZUTRITT_FRAUEN_FILE
    DATA_DIR = Path(daten or os.environ.get("FCSG_DATA_DIR") or PROJECT_ROOT / "1. Daten FCSG")
    KONTEXT_FILE = Path(kontext or os.environ.get("FCSG_KONTEXT_FILE") or MODEL_DIR / "Spielkontext_Tabelle_FCSG_5.xlsx")  # Version 5, D-034

    TICKETING_DIR = DATA_DIR / "Ticketing"
    CATERING_DIR = DATA_DIR / "Catering"
    ZUTRITT_DIR = DATA_DIR / "Zutritt"

    HISTORIE_FILE = TICKETING_DIR / "Ticketing-Zuschauerzahlen-Historie.xlsx"
    CATERING_FILE = CATERING_DIR / "Umsatz Public Catering ab Saison 18-19_Neu.xlsx"
    ARTIKEL_FILE = CATERING_DIR / "Artikelauswertung Meisterschaft.xlsx"
    ZUTRITT_ERLAUBT_FILE = ZUTRITT_DIR / "ErlaubteZutritteHerren.xlsx"
    ZUTRITT_INHOUSE_FILE = ZUTRITT_DIR / "zugangsdaten_herren_inhouse.csv"
    ZUTRITT_ALT_FILE = ZUTRITT_DIR / "zugangsdaten_herren_alteSaisons.txt"
    ZUTRITT_FRAUEN_FILE = ZUTRITT_DIR / "zugangsdaten_frauenequipe_alleSpiele.txt"


def fehlende_pflichteingaben() -> list[str]:
    """Eingaben, ohne die der Lauf abbricht oder die Kontextmodelle nicht schätzbar sind."""
    pflicht = {
        "Rohdatenordner «1. Daten FCSG» (--daten)": DATA_DIR,
        "Zuschauer-Historie": HISTORIE_FILE,
        "Public-Catering-Umsätze": CATERING_FILE,
        "Zutritte 2025/26–2026/27": ZUTRITT_ERLAUBT_FILE,
        "Spielkontext-Tabelle (--kontext)": KONTEXT_FILE,
        "Wetter-Cache im Codeordner": WETTER_FILE,
        "Resultate-Cache im Codeordner": RESULTATE_FILE,
    }
    return [f"{name}: {pfad}" for name, pfad in pflicht.items() if not pfad.exists()]


setze_datenpfade()

# --------------------------------------------------------------------------------------------
# Scope
# --------------------------------------------------------------------------------------------
# Kernstichprobe = Pflichtspiele der Herren im kybunpark (Super League, Schweizer Cup, UEFA).
KERN_WETTBEWERBE = ("SL", "Cup", "UEFA")
BASELINE_AB_SAISON = "2021/22"     # Spielebene: alle Kernquellen ab hier vorhanden
MODELL_AB_SAISON = "2022/23"       # Kontextmodelle: Spielkontext-Tabelle ab hier (Auftrag Abschnitt D)
TREND_AB_SAISON = "2018/19"        # Langfristiger Catering-Trend (Saisonebene)

# Datenschutz: Segmentzellen mit weniger Tickets/Scans werden unterdrückt (Auftrag Abschnitt 8)
MIN_ZELLE = 10

# --------------------------------------------------------------------------------------------
# Fachliche Konstanten (Herkunft jeweils dokumentiert)
# --------------------------------------------------------------------------------------------
# Kapazität gemäss Formel «Auslastung, exkl. Gäste» in der Zuschauer-Historie: (SOLL-Gäste)/(20136-1930)
KAPAZITAET_TOTAL = 20136
KAPAZITAET_GAESTESEKTOR = 1930
KAPAZITAET_HEIM = KAPAZITAET_TOTAL - KAPAZITAET_GAESTESEKTOR   # 18'206

# Mehrwertsteuer Schweiz: Normalsatz 7.7 % bis 31.12.2023, 8.1 % ab 01.01.2024; reduzierter Satz (Take-away-Speisen
# und alkoholfreie Getränke) 2.5 % bzw. 2.6 %
MWST_WECHSEL = "2024-01-01"
MWST_ALT = 0.077
MWST_NEU = 0.081
MWST_REDUZIERT_ALT = 0.025
MWST_REDUZIERT_NEU = 0.026

# Gegner mit traditionell grosser Anhängerschaft (vor Spielbeginn bekannt, nicht aus Zielgrössen abgeleitet)
TOP_GEGNER = frozenset({"Basel", "Young Boys", "Zurich"})

# Ideen-Grundlage: Szenarien für φ (Konsum eines zusätzlichen Anwesenden relativ zum Schnitt; Simon §12, Reto A5)
IDEEN_PHI = (0.6, 0.8, 1.0)

# Ankunftsschwellen (Minuten vor Anpfiff) gemäss Retos Sichtung und Auftrag Paket D
ANKUNFT_FRUEH_MIN = 45
ANKUNFT_SPAET_MIN = 15

# Kanonische Teamnamen (football-data.co.uk) -> deutsche Anzeige
TEAM_ANZEIGE = {
    "Basel": "FC Basel", "Young Boys": "BSC Young Boys", "Zurich": "FC Zürich",
    "Grasshoppers": "Grasshopper Club Zürich", "Luzern": "FC Luzern", "Lugano": "FC Lugano",
    "Servette": "Servette FC", "Sion": "FC Sion", "Lausanne": "FC Lausanne-Sport",
    "Lausanne Ouchy": "Stade Lausanne-Ouchy", "Winterthur": "FC Winterthur", "Thun": "FC Thun",
    "Vaduz": "FC Vaduz", "Yverdon": "Yverdon Sport", "Aarau": "FC Aarau", "Xamax": "Neuchâtel Xamax",
}

ZEITZONE = "Europe/Zurich"

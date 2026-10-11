"""Erzeugung der künstlichen Mini-Fixture ``synthetic_mini``.

Alle Werte sind frei erfunden und bewusst unrealistisch klein (Zuschauer ~100 statt ~15 000),
Spieldaten liegen in 2099/2100, Saisons heissen «FX1»/«FX2», Gegner «Testgegner A–D».
Jede Zeile trägt ``data_origin = FIXTURE_MARKER``. Die Fixture enthält absichtlich Sonderfälle,
die die Pipeline erkennen muss:

- fehlendes IST bei einem Spiel (Missing, nicht 0),
- ein Spiel ohne Catering-Zeile,
- ein Public-Viewing-Event am selben Datum wie ein Spiel (Mehrfach-Event, muss ausgeschlossen werden),
- eine Catering-Zeile ohne passendes Heimspiel (Unmatched-Report),
- Zutrittsscans nur für Saison FX2 (unterschiedliche Abdeckung je Modul).

Die Netto-Umsätze sind Brutto × 0.9 – ein willkürlicher Faktor, **kein** MwSt-Satz.
"""

from __future__ import annotations

import random
from pathlib import Path

import pandas as pd

from fcsg import FIXTURE_MARKER

ATTENDANCE_ROWS = [
    # match_date, season, competition, opponent_label, kickoff_local, soll, ist, ist_vip, ist_guests
    ("2099-08-01", "FX1", "Liga-Test", "Testgegner A", "18:00", 100, 82, 5, 3),
    ("2099-08-15", "FX1", "Liga-Test", "Testgegner B", "20:30", 120, 90, 6, 4),
    ("2099-08-29", "FX1", "Cup-Test", "Testgegner C", "14:00", 80, 70, 4, 2),
    ("2100-08-07", "FX2", "Liga-Test", "Testgegner A", "18:00", 110, 95, 5, 3),
    ("2100-08-21", "FX2", "Liga-Test", "Testgegner D", "20:30", 130, None, 6, None),
    ("2100-09-04", "FX2", "Liga-Test", "Testgegner B", "16:00", 100, 88, 5, 2),
]

CATERING_ROWS = [
    # match_date, event_type, event_label, public_attendance, receipts, revenue_gross_chf
    ("2099-08-01", "match", "Testgegner A", 77, 70, 1100.00),
    ("2099-08-15", "match", "Testgegner B", 84, 81, 1300.00),
    # 2099-08-29: absichtlich keine Catering-Zeile
    ("2100-08-07", "match", "Testgegner A", 90, 88, 1500.00),
    ("2100-08-07", "public_viewing", "Test-Public-Viewing", None, 20, 300.00),
    ("2100-08-21", "match", "Testgegner D", 100, 95, 1600.00),
    ("2100-09-04", "match", "Testgegner B", 83, 79, 1250.00),
    ("2100-09-18", "match", "Testgegner X", 60, 55, 800.00),  # kein Heimspiel in attendance
]

# Anzahl Scans je Spiel (nur FX2); bewusst leicht unter bzw. nahe IST.
ACCESS_SCANS_PER_MATCH = {"2100-08-07": 94, "2100-08-21": 97, "2100-09-04": 88}
ACCESS_SECTORS = ["A", "B", "C", "D"]
ACCESS_SEED = 20991231


def build_synthetic_mini() -> dict[str, pd.DataFrame]:
    """Baut die drei Fixture-Tabellen deterministisch auf.

    Returns:
        Dict ``{source_name: DataFrame}`` mit den Quellen ``attendance_match``,
        ``catering_match`` und ``access_scans``.
    """
    attendance = pd.DataFrame(
        ATTENDANCE_ROWS,
        columns=["match_date", "season", "competition", "opponent_label", "kickoff_local",
                 "soll", "ist", "ist_vip", "ist_guests"],
    )
    for col in ("soll", "ist", "ist_vip", "ist_guests"):
        attendance[col] = attendance[col].astype("Int64")

    catering = pd.DataFrame(
        CATERING_ROWS,
        columns=["match_date", "event_type", "event_label", "public_attendance", "receipts",
                 "revenue_gross_chf"],
    )
    catering["public_attendance"] = catering["public_attendance"].astype("Int64")
    catering["revenue_net_chf"] = (catering["revenue_gross_chf"] * 0.9).round(2)

    rng = random.Random(ACCESS_SEED)
    scans = []
    for match_date, n in ACCESS_SCANS_PER_MATCH.items():
        for _ in range(n):
            # Gemischte Verteilung: ~45 % früh (45–90 Min.), Rest 0–44 Min., wenige nach Anpfiff.
            r = rng.random()
            if r < 0.45:
                minutes = rng.randint(45, 90)
            elif r < 0.95:
                minutes = rng.randint(0, 44)
            else:
                minutes = rng.randint(-10, -1)
            scans.append((match_date, minutes, rng.choice(ACCESS_SECTORS)))
    access = pd.DataFrame(scans, columns=["match_date", "minutes_before_kickoff", "reader_sector"])

    tables = {"attendance_match": attendance, "catering_match": catering, "access_scans": access}
    for df in tables.values():
        df.insert(0, "data_origin", FIXTURE_MARKER)
    return tables


def write_synthetic_mini(target_dir: str | Path) -> list[Path]:
    """Schreibt die Fixture als CSV (UTF-8) nach ``target_dir`` und gibt die Pfade zurück."""
    target = Path(target_dir)
    target.mkdir(parents=True, exist_ok=True)
    paths = []
    for name, df in build_synthetic_mini().items():
        path = target / f"{name}.csv"
        df.to_csv(path, index=False, encoding="utf-8", lineterminator="\n")
        paths.append(path)
    return paths

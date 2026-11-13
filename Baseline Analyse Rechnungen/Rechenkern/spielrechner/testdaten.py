"""TESTDATEN für den Spielrechner – vollständig künstlich (Zufallszahlen, erfundene Gegner), keine Clubzahlen.

Gleiches Schema wie die Run-4-Tabellen `koeffizienten.csv` und `erwartung_je_spiel.csv`, `mart_match.csv` und die
Blätter «Ferien» und «Paralellevent» der Spielkontext-Tabelle (erfundene Daten im Jahr 2099).

Demo-Modus (`demo=True`, für die öffentliche Vorschau): gleiche künstliche Zahlen, aber realistische Saisonbezeichnungen
2023/24–2025/26 und Daten mit passendem Wochentag je Anstoss-Slot, damit der Rückblick lesbar ist. Gegner bleiben
«Testgegner», Werte bleiben Zufallszahlen.
"""
from __future__ import annotations

import datetime as dt
from pathlib import Path

import numpy as np
import pandas as pd

SAISONS = ["T1/T2", "T2/T3", "T3/T4"]          # bewusst keine echten Saisonbezeichnungen
DEMO_SAISONS = ["2023/24", "2024/25", "2025/26"]
DEMO_MONATE = [8, 8, 9, 9, 10, 10, 11, 2, 3, 3, 4, 5]
SLOT_TAG = [5, 5, 6, 2]                          # Samstag, Samstag, Sonntag, Mittwoch (Python: Mo = 0)


def _demo_datum(saison: str, i: int) -> str:
    """Erstes Datum im Monat DEMO_MONATE[i] (ab Tag 1 + 7·(i mod 2)) mit dem Wochentag des Slots i mod 4."""
    jahr = int(saison[:4]) + (1 if DEMO_MONATE[i] < 7 else 0)
    d = dt.date(jahr, DEMO_MONATE[i], 1 + 7 * (i % 2))
    while d.weekday() != SLOT_TAG[i % 4]:
        d += dt.timedelta(days=1)
    return d.isoformat()
SLOT_LABELS = ["Samstag 17–19.59 Uhr", "Samstag ab 20 Uhr", "Nachmittag vor 17 Uhr (Sonntag/Feiertag)", "Werktagabend ab 17 Uhr"]
MODELLE = {  # ziel_code: (label, transformation, intercept, rmse)
    "anwesenheitsquote": ("Anwesenheitsquote (IST/SOLL)", "logit", 1.5, 0.25),
    "kf_exkl": ("Kundenfranken exkl. MwSt", "log", 2.6, 0.05),
    "bons_pro_anwesende": ("Bons je Public-Anwesendem", "log", -0.2, 0.06),
    "bon_exkl": ("Ø Bon exkl. MwSt", "log", 2.8, 0.04),
}


def erzeuge(ordner: Path, demo: bool = False) -> tuple[Path, Path, Path]:
    rng = np.random.default_rng(42)
    saisons = DEMO_SAISONS if demo else SAISONS
    ordner.mkdir(parents=True, exist_ok=True)
    koeff, erw = [], []
    for code, (label, art, icpt, rmse) in MODELLE.items():
        terme = {"Intercept": icpt, f"C(saison)[T.{saisons[1]}]": 0.05, f"C(saison)[T.{saisons[2]}]": 0.08,
                 "slot_sa_abend": -0.03, "slot_nachmittag": -0.15, "slot_werktag_abend": -0.10,
                 "top_gegner": 0.10, "temp_anpfiff_c": 0.005, "regen_anreise": -0.02, "schulferien": -0.03}
        koeff += [{"zielgroesse": label, "ziel_code": code, "transformation": art, "term": t, "koeffizient": v,
                   "standardfehler": 0.02, "rmse_lomo_transformiert": rmse, "mittel_rueck": np.nan} for t, v in terme.items()]
        r = (lambda z: np.exp(z)) if art == "log" else (lambda z: 1 / (1 + np.exp(-z)))
        for s in saisons:
            for i in range(12):
                z = icpt + rng.normal(0, 0.1)
                datum = _demo_datum(s, i) if demo else f"2099-{1 + i % 12:02d}-{1 + SAISONS.index(s) * 9:02d}"
                erw.append({"match_id": f"TEST_{s}_{i:02d}", "datum": datum,
                            "saison": s, "anstoss_slot": SLOT_LABELS[i % 4], "zielgroesse": label, "ziel_code": code,
                            "beobachtet": r(z + rng.normal(0, rmse * 1.2)), "erwartet": r(z),
                            "band80_unten": r(z - 1.2816 * rmse), "band80_oben": r(z + 1.2816 * rmse)})
    tab = ordner / "Tabellen"
    tab.mkdir(exist_ok=True)
    pd.DataFrame(koeff).to_csv(tab / "koeffizienten.csv", index=False)
    pd.DataFrame(erw).to_csv(tab / "erwartung_je_spiel.csv", index=False)
    ids = sorted({e["match_id"] for e in erw})
    mart = pd.DataFrame({"match_id": ids, "saison": [i.split("_")[1] for i in ids], "wettbewerb": "SL",
                         "spielstatus": "gespielt", "gegner_anzeige": [f"Testgegner {chr(65 + n % 10)}" for n in range(len(ids))],
                         "soll": rng.integers(14000, 18000, len(ids)), "ist_vip": rng.integers(500, 900, len(ids)),
                         "wochentag": [("Samstag", "Samstag", "Sonntag", "Mittwoch")[int(i[-2:]) % 4] for i in ids]})
    mart.to_csv(ordner / "mart_match.csv", index=False)
    return tab, ordner / "mart_match.csv", kontext(ordner / "Kontext_TEST.xlsx")


def kontext(pfad: Path) -> Path:
    """TESTDATEN: Ferien 01.–14.07.2099 und 10.–20.10.2099, ein erfundener Parallelanlass am 18.10.2099."""
    import datetime as dt

    import openpyxl
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Ferien"
    ws.append(["Datum", "Wochentag", "Schulferien Stadt SG", "Ferienart"])
    tag = dt.date(2099, 7, 1)
    while tag <= dt.date(2099, 12, 31):
        ferien = dt.date(2099, 7, 1) <= tag <= dt.date(2099, 7, 14) or dt.date(2099, 10, 10) <= tag <= dt.date(2099, 10, 20)
        ws.append([tag, "", "Ja" if ferien else "Nein", "Testferien" if ferien else None])
        tag += dt.timedelta(days=1)
    pe = wb.create_sheet("Paralellevent")
    pe.append(["Datum", "Wochentag", "relevanter Parallelevent (Ja/Nein)", "Anzahl Events", "Parallelevents", "Grossevent (≥ 100'000 Besucher)"])
    pe.append([dt.date(2099, 10, 18), "", "Ja", 1, "Testanlass", "Nein"])
    pe.append([dt.date(2099, 10, 19), "", "Nein", 0, None, "Nein"])
    wb.save(pfad)
    return pfad

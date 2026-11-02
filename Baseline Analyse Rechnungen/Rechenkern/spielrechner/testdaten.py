"""TESTDATEN für den Spielrechner – vollständig künstlich (Zufallszahlen, erfundene Gegner), keine Clubzahlen.

Gleiches Schema wie die Run-4-Tabellen `koeffizienten.csv` und `erwartung_je_spiel.csv` sowie `mart_match.csv`.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

SAISONS = ["T1/T2", "T2/T3", "T3/T4"]          # bewusst keine echten Saisonbezeichnungen
SLOT_LABELS = ["Samstag 17–19.59 Uhr", "Samstag ab 20 Uhr", "Nachmittag vor 17 Uhr (Sonntag/Feiertag)", "Werktagabend ab 17 Uhr"]
MODELLE = {  # ziel_code: (label, transformation, intercept, rmse)
    "anwesenheitsquote": ("Anwesenheitsquote (IST/SOLL)", "logit", 1.5, 0.25),
    "kf_exkl": ("Kundenfranken exkl. MwSt", "log", 2.6, 0.05),
    "bons_pro_anwesende": ("Bons je Public-Anwesendem", "log", -0.2, 0.06),
    "bon_exkl": ("Ø Bon exkl. MwSt", "log", 2.8, 0.04),
}


def erzeuge(ordner: Path) -> tuple[Path, Path]:
    rng = np.random.default_rng(42)
    ordner.mkdir(parents=True, exist_ok=True)
    koeff, erw = [], []
    for code, (label, art, icpt, rmse) in MODELLE.items():
        terme = {"Intercept": icpt, f"C(saison)[T.{SAISONS[1]}]": 0.05, f"C(saison)[T.{SAISONS[2]}]": 0.08,
                 "slot_sa_abend": -0.03, "slot_nachmittag": -0.15, "slot_werktag_abend": -0.10,
                 "top_gegner": 0.10, "temp_anpfiff_c": 0.005, "regen_anreise": -0.02, "schulferien": -0.03}
        koeff += [{"zielgroesse": label, "ziel_code": code, "transformation": art, "term": t, "koeffizient": v,
                   "standardfehler": 0.02, "rmse_lomo_transformiert": rmse, "mittel_rueck": np.nan} for t, v in terme.items()]
        r = (lambda z: np.exp(z)) if art == "log" else (lambda z: 1 / (1 + np.exp(-z)))
        for s in SAISONS:
            for i in range(12):
                z = icpt + rng.normal(0, 0.1)
                erw.append({"match_id": f"TEST_{s}_{i:02d}", "datum": f"2099-{1 + i % 12:02d}-{1 + SAISONS.index(s) * 9:02d}",
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
                         "soll": rng.integers(14000, 18000, len(ids)), "ist_vip": rng.integers(500, 900, len(ids))})
    mart.to_csv(ordner / "mart_match.csv", index=False)
    return tab, ordner / "mart_match.csv"

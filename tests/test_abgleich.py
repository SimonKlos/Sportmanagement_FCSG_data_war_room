"""Abgleich der Spieltabellen Simon vs. Ralf (fcsg.abgleich) mit künstlichen Daten (Jahr 2099)."""

import pandas as pd

from fcsg.abgleich import compare_marts


def test_compare_marts_status_und_datumskorrektur():
    simon = pd.DataFrame({
        "match_date": ["2099-08-01", "2099-08-08", "2024-08-24"], "season": ["2099/00"] * 2 + ["2024/25"],
        "soll": [100.0, 100.0, 50.0], "ist": [80.0, 90.0, 40.0], "public_attendance": [70.0, None, 35.0],
        "revenue_gross_chf": [1000.0, None, 500.0],
    })
    ralf = pd.DataFrame({
        "datum": ["2099-08-01", "2099-08-08", "2024-09-24", "2099-09-01"], "saison": ["2099/00"] * 2 + ["2024/25", "2099/00"],
        "spielstatus": ["gespielt", "gespielt", "gespielt", "geplant"],
        "soll": [100, 100, 50, 100], "ist": [80, 91, 40, None], "public_netto": [70, 85, 35, None],
        "umsatz_inkl": [1000.0, 1200.0, 500.0, None],
    })
    per_game, summary = compare_marts(simon, ralf)
    st = per_game.set_index(["datum", "kennzahl"])["status"]
    assert st[("2099-08-01", "IST")] == "gleich" and st[("2099-08-08", "IST")] == "abweichend"
    assert st[("2099-08-08", "Public Netto")] == "nur Ralf"
    assert st[("2024-09-24", "SOLL")] == "gleich"  # Historie-Datum 24.08. wird auf 24.09. abgebildet (D-030)
    assert "2099-09-01" not in set(per_game["datum"])  # geplante Spiele nicht im Abgleich
    assert summary.set_index("kennzahl").loc["IST", "gleich"] == 2

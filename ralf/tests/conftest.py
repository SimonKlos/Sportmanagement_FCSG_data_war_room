import sys
from pathlib import Path

import pytest

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


@pytest.fixture(scope="session")
def phase1():
    """Phase-1-Objekte (r, m, res) wie in run_all.py, einmal je Testlauf; übersprungen, wenn der Datenordner fehlt."""
    from fcsg import config
    if not config.DATA_DIR.exists():
        pytest.skip("Datenordner nicht vorhanden")
    from fcsg.analysis import arrival, attendance, baseline, catering, models
    from fcsg.datamodel import baue_modell
    from fcsg.mart import baue_mart
    from fcsg.pipeline import lade_rohdaten

    r = lade_rohdaten()
    m = baue_modell(r)
    res = {}
    res.update(baseline.baseline(r, m))
    k = res["spiel_kpi"]
    res.update(attendance.anwesenheit(r, m, k))
    res.update(catering.catering(r, m, k))
    res.update(arrival.ankunft(r, m, k, res["scan_ist"]))
    d = models.modell_daten(k, m.dim_match_context, res["ankunft_je_spiel"])
    res["modell_daten"] = d
    res.update(models.kontextmodelle(d))
    res.update(models.diagnosekarte(res["diagnosekarte_lang"], d, m.fact_attendance_match, m.fact_catering_match))
    res.update(arrival.toroeffnung_experiment(res["ankunft_je_sektor"], k, res["diagnosekarte_lang"]))
    res["mart_match"] = baue_mart(m, res)
    return r, m, res

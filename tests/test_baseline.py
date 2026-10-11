"""Baseline auf bereinigten Tabellen (fcsg.baseline) mit künstlichen Daten: Join, Summenerhalt, Regeln, KPIs."""

import numpy as np
import pandas as pd
import pytest

from conftest import N_GAMES
from fcsg.baseline import (add_real_kpis, build_mart_match_real, guest_sector_note, hhmm_to_min, kpi_checks_real,
                           lead_bucket, season_summary_real, source_total_check, weighted_median)
from fcsg.joins import JoinError


@pytest.fixture
def mart(clean_tables):
    return build_mart_match_real(clean_tables, today="2099-12-31")


def test_cardinality_and_sums(mart):
    m = mart.mart
    assert len(m) == 2 * N_GAMES  # nur Pflichtspiele, Testspiel ausgeschlossen
    assert m["match_date"].is_unique
    assert all(c["status"] == "OK" for c in mart.checks), [c for c in mart.checks if c["status"] != "OK"]


def test_access_duplicate_file_rule(mart, clean_tables):
    m = mart.mart.set_index("match_date")
    first = clean_tables["access_match_summary"].iloc[0]
    assert m.loc[first["match_date"], "scan_count"] == first["scans"]  # Zweitdatei (40) nicht addiert
    assert m.loc[first["match_date"], "access_source_file"] == "zutritt_a.txt"
    a01 = next(c for c in mart.checks if c["check_id"] == "A01")
    assert a01["detail"].startswith("1 Daten doppelt; 40 Scans")


def test_unmatched_report(mart):
    reasons = mart.unmatched.groupby("source")["reason"].apply(list).to_dict()
    assert any("abgesagt" in r for r in reasons["catering_match"])
    assert any("Freundschaftsspiel" in r for r in reasons["catering_match"])
    assert reasons["context_match"] == ["noch nicht gespielt"]


def test_kpis_missing_stays_missing(mart):
    m = add_real_kpis(mart.mart)
    s1 = m[m["season"] == "2098/99"]
    assert s1["receipts_per_public"].isna().all() and s1["avg_receipt_gross_chf"].isna().all()  # keine Bons → leer
    assert np.allclose(m["kf_gross_chf"], 15 * m["ist"] / m["public_attendance"])
    assert (m["access_complete"] == 1).all()
    assert np.allclose(m["share_arrived_45min_before"], 0.30 + 0.03 * (np.arange(len(m)) % N_GAMES), atol=1e-3)
    assert s1["single_entry_rate"].notna().all() and m.loc[m["season"] == "2099/00", "single_entry_rate"].isna().all()
    assert all(c["status"] == "OK" for c in kpi_checks_real(m))


def test_season_summary_weighted(mart):
    m = add_real_kpis(mart.mart)
    s = season_summary_real(m).set_index("season")
    g = m[m["season"] == "2099/00"]
    assert s.loc["2099/00", "kf_gross_weighted_chf"] == pytest.approx(g["revenue_gross_chf"].sum() / g["public_attendance"].sum())
    assert np.isnan(s.loc["2098/99", "receipts_per_public_weighted"])


def test_source_total_check(clean_tables):
    out = source_total_check(clean_tables)
    assert (out["status"] == "OK").all()  # abgesagte Zeile nicht mitgezählt


def test_duplicate_catering_date_aborts(clean_tables):
    cat = clean_tables["catering_match"]
    clean_tables["catering_match"] = pd.concat([cat, cat.iloc[[0]]], ignore_index=True)
    with pytest.raises(JoinError):
        build_mart_match_real(clean_tables, today="2099-12-31")


def test_helpers():
    assert hhmm_to_min(pd.Series(["18:30", "x"])).tolist()[0] == 1110 and np.isnan(hhmm_to_min(pd.Series(["x"]))[0])
    notes = guest_sector_note(pd.Series(["ausverkauft (exkl. Gästesektor)", "ausverkauft (Zusatz Gästesektor im B3)", None]))
    assert notes.tolist()[:2] == ["geschlossen/exkl.", "zusatz"] and pd.isna(notes.iat[2])
    assert lead_bucket(pd.Series([0, 5, 30, 31, -2])).tolist() == ["0–1 Tage", "2–7 Tage", "8–30 Tage", "> 30 Tage",
                                                                   "ungültig (< 0)"]
    assert weighted_median(pd.Series([10.0, 40.0, 50.0]), pd.Series([1, 1, 5])) == 50.0

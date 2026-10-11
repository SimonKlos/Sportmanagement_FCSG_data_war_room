"""KPI-Formeln gegen handgerechnete Werte der Fixture."""

import datetime as dt

import numpy as np
import pandas as pd
import pytest

from fcsg.joins import build_mart_match
from fcsg.metrics import add_match_kpis, kpi_checks, safe_ratio, season_summary


@pytest.fixture
def mart(sources):
    m, _, _ = build_mart_match(sources["attendance_match"], sources["catering_match"], sources["access_scans"])
    return add_match_kpis(m)


def _row(mart, y, m, d):
    return mart.loc[mart["match_date"] == dt.date(y, m, d)].iloc[0]


def test_match_kpis_hand_calculated(mart):
    r = _row(mart, 2099, 8, 1)  # SOLL 100, IST 82, Public 77, Bons 70, Brutto 1100, Netto 990
    assert r["attendance_rate"] == pytest.approx(0.82)
    assert r["no_show_rate"] == pytest.approx(0.18)
    assert r["no_show_abs"] == 18
    assert r["kf_gross_chf"] == pytest.approx(1100 / 77)
    assert r["kf_net_chf"] == pytest.approx(990 / 77)
    assert r["receipts_per_public"] == pytest.approx(70 / 77)
    assert r["avg_receipt_gross_chf"] == pytest.approx(1100 / 70)


def test_missing_ist_gives_missing_kpis(mart):
    r = _row(mart, 2100, 8, 21)
    assert np.isnan(r["attendance_rate"]) and np.isnan(r["no_show_abs"]) and np.isnan(r["scan_vs_ist_rate"])
    assert r["kf_gross_chf"] == pytest.approx(16.0)  # Catering unabhängig von IST vorhanden


def test_safe_ratio_zero_and_missing_denominator():
    out = safe_ratio(pd.Series([1.0, 1.0, np.nan]), pd.Series([0.0, np.nan, 2.0]))
    assert out.isna().all()


def test_season_kf_is_weighted_not_mean(mart):
    s = season_summary(mart).set_index("season")
    assert s.loc["FX1", "kf_gross_weighted_chf"] == pytest.approx(2400 / 161)
    assert s.loc["FX1", "kf_gross_unweighted_mean_chf"] == pytest.approx((1100 / 77 + 1300 / 84) / 2)
    assert s.loc["FX1", "kf_gross_weighted_chf"] != pytest.approx(s.loc["FX1", "kf_gross_unweighted_mean_chf"])
    assert s.loc["FX2", "kf_gross_weighted_chf"] == pytest.approx(4350 / 273)
    # Anwesenheit FX2 nur aus Spielen mit SOLL und IST: (95 + 88) / (110 + 100)
    assert s.loc["FX2", "attendance_rate_weighted"] == pytest.approx(183 / 210)
    assert s.loc["FX2", "n_attendance"] == 2 and s.loc["FX2", "n_matches"] == 3


def test_kpi_checks_pass(mart):
    assert all(c["status"] == "OK" for c in kpi_checks(mart))

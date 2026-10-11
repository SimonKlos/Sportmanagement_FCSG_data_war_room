"""Join-Kardinalität, Unmatched-Report und Summenerhalt."""

import datetime as dt

import pandas as pd
import pytest

from fcsg.joins import JoinError, aggregate_access, build_dim_match, build_mart_match


def test_mart_has_one_row_per_home_match(sources):
    mart, _, checks = build_mart_match(sources["attendance_match"], sources["catering_match"], sources["access_scans"])
    assert len(mart) == 6
    assert mart["match_id"].is_unique
    assert not [c for c in checks if c["status"] == "FAIL"]


def test_public_viewing_and_unknown_date_are_reported_not_joined(sources):
    mart, unmatched, _ = build_mart_match(sources["attendance_match"], sources["catering_match"], sources["access_scans"])
    assert set(unmatched["match_date"]) == {dt.date(2100, 8, 7), dt.date(2100, 9, 18)}
    # Am 07.08.2100 darf nur die Spiel-Zeile im Mart stecken, nicht zusätzlich das Public Viewing.
    row = mart.loc[mart["match_date"] == dt.date(2100, 8, 7)].iloc[0]
    assert row["revenue_gross_chf"] == 1500.0 and row["receipts"] == 88


def test_match_without_catering_is_missing_not_zero(sources):
    mart, _, _ = build_mart_match(sources["attendance_match"], sources["catering_match"], sources["access_scans"])
    row = mart.loc[mart["match_date"] == dt.date(2099, 8, 29)].iloc[0]
    assert pd.isna(row["revenue_gross_chf"]) and not row["has_catering"]


def test_sum_preservation(sources):
    mart, _, _ = build_mart_match(sources["attendance_match"], sources["catering_match"], sources["access_scans"])
    # Von Hand: zuordenbare Spiel-Zeilen 1100 + 1300 + 1500 + 1600 + 1250
    assert mart["revenue_gross_chf"].sum() == pytest.approx(6750.0)
    assert mart["scan_count"].sum() == len(sources["access_scans"]) == 94 + 97 + 88


def test_duplicate_match_date_aborts(sources):
    att = pd.concat([sources["attendance_match"], sources["attendance_match"].iloc[[0]]])
    with pytest.raises(JoinError, match="nicht eindeutig"):
        build_dim_match(att)


def test_duplicate_catering_match_rows_abort(sources):
    cat = pd.concat([sources["catering_match"], sources["catering_match"].iloc[[0]]])
    with pytest.raises(JoinError):
        build_mart_match(sources["attendance_match"], cat, sources["access_scans"])


def test_access_aggregation_shares():
    scans = pd.DataFrame({
        "match_date": [dt.date(2099, 1, 1)] * 4,
        "minutes_before_kickoff": [60.0, 45.0, 10.0, -3.0],
        "reader_sector": ["A"] * 4,
    })
    agg = aggregate_access(scans).iloc[0]
    assert agg["scan_count"] == 4
    assert agg["share_arrived_45min_before"] == pytest.approx(0.5)
    assert agg["share_last_15min"] == pytest.approx(0.25)  # -3 (nach Anpfiff) zählt nicht
    assert agg["arrival_median_min_before"] == pytest.approx(27.5)

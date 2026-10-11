"""Fixture-Kennzeichnung, Inputschema und Datenmodus-Schutz."""

import pandas as pd
import pytest

from conftest import FIXTURE_DIR
from fcsg import FIXTURE_MARKER
from fcsg.config import ConfigError, load_config
from fcsg.fixtures import build_synthetic_mini
from fcsg.io import SOURCE_SCHEMAS, SchemaError, inventory, load_source


def test_committed_fixture_matches_generator():
    """Die eingecheckten CSVs entsprechen exakt dem Generator (kein unbemerkter Drift)."""
    for name, df in build_synthetic_mini().items():
        on_disk = pd.read_csv(FIXTURE_DIR / f"{name}.csv", dtype=str, keep_default_na=False)
        generated = pd.read_csv(pd.io.common.StringIO(df.to_csv(index=False)), dtype=str, keep_default_na=False)
        pd.testing.assert_frame_equal(on_disk, generated)


def test_every_fixture_row_is_marked_and_clearly_artificial():
    for name, df in build_synthetic_mini().items():
        assert (df["data_origin"] == FIXTURE_MARKER).all(), name
        years = pd.to_datetime(df["match_date"]).dt.year
        assert (years >= 2099).all(), "Fixture-Daten müssen in 2099+ liegen"


def test_missing_column_raises_without_cell_values(tmp_path):
    df = pd.read_csv(FIXTURE_DIR / "attendance_match.csv").drop(columns=["soll"])
    df.to_csv(tmp_path / "attendance_match.csv", index=False)
    with pytest.raises(SchemaError) as exc:
        load_source(tmp_path, SOURCE_SCHEMAS["attendance_match"])
    msg = str(exc.value)
    assert "soll" in msg and "Testgegner" not in msg


def test_unmarked_rows_are_refused(tmp_path):
    df = pd.read_csv(FIXTURE_DIR / "attendance_match.csv")
    df.loc[0, "data_origin"] = "REAL"
    df.to_csv(tmp_path / "attendance_match.csv", index=False)
    with pytest.raises(SchemaError, match="ohne Fixture-Marker"):
        load_source(tmp_path, SOURCE_SCHEMAS["attendance_match"])


def test_non_numeric_value_reports_count_only(tmp_path):
    df = pd.read_csv(FIXTURE_DIR / "catering_match.csv")
    df["receipts"] = df["receipts"].astype(object)
    df.loc[0, "receipts"] = "geheim123"
    df.to_csv(tmp_path / "catering_match.csv", index=False)
    with pytest.raises(SchemaError) as exc:
        load_source(tmp_path, SOURCE_SCHEMAS["catering_match"])
    assert "1 nicht-numerische" in str(exc.value) and "geheim123" not in str(exc.value)


def test_missing_values_stay_missing(sources):
    att = sources["attendance_match"]
    assert att["ist"].isna().sum() == 1  # nicht zu 0 umgewandelt
    assert (att["ist"].fillna(-1) != 0).all()


def test_config_rejects_unreleased_data_mode(tmp_path):
    cfg = tmp_path / "x.yaml"
    cfg.write_text("data_mode: real\ninput_dir: a\noutput_dir: b\n", encoding="utf-8")
    with pytest.raises(ConfigError, match="nicht freigegeben"):
        load_config(cfg)


def test_inventory_shows_structure_only():
    inv = inventory(FIXTURE_DIR)
    assert set(inv["source"]) == set(SOURCE_SCHEMAS)
    assert (inv["missing_required"] == "-").all()
    assert not inv.astype(str).apply(lambda s: s.str.contains("Testgegner")).any().any()

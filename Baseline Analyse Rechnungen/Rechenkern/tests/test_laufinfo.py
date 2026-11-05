"""Laufprotokoll: Eingabedateien werden auch über Ordner-Verknüpfungen erfasst (künstliche Dateien, keine Clubdaten)."""
import pandas as pd

import run_all
from fcsg import config


def test_laufinfo_folgt_verknuepften_ordnern(tmp_path, monkeypatch):
    lieferung = tmp_path / "lieferung" / "Zutritte"
    lieferung.mkdir(parents=True)
    (lieferung / "TESTDATEN_scans.csv").write_text("a,b\n1,2\n", encoding="utf-8")
    daten = tmp_path / "daten"
    daten.mkdir()
    (daten / "Zutritt").symlink_to(lieferung, target_is_directory=True)
    (daten / ".versteckt").write_text("x", encoding="utf-8")
    monkeypatch.setattr(config, "DATA_DIR", daten)
    for name in ("KONTEXT_FILE", "WETTER_FILE", "RESULTATE_FILE", "OVERRIDES_FILE"):
        monkeypatch.setattr(config, name, tmp_path / f"fehlt_{name}")
    info = run_all._laufinfo(pd.Timestamp("2026-09-12"), 0)
    assert [e["datei"] for e in info["eingabedateien"]] == ["TESTDATEN_scans.csv"]
    assert info["eingabedateien"][0]["bytes"] == 8

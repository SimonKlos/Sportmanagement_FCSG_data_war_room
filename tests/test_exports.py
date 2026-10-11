"""End-to-end: Lauf → Excel → Readback, inklusive Negativtests."""

import json

from openpyxl import load_workbook

from fcsg import FIXTURE_BANNER
from fcsg.cli import main
from fcsg.config import load_config
from fcsg.export import HEADER_ROW, export_excel, readback_excel
from fcsg.pipeline import run_pipeline


def test_run_export_readback_roundtrip(tmp_config):
    result = run_pipeline(load_config(tmp_config))
    assert result.n_fail == 0
    manifest = json.loads((result.run_dir / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["data_mode"] == "synthetic_fixture" and manifest["coverage"]["home_matches"] == 6
    assert ":" not in manifest["input_dir_name"]  # keine absoluten lokalen Pfade im Manifest

    xlsx = export_excel(result.run_dir)
    report = readback_excel(result.run_dir, xlsx)
    assert report["passed"], report

    wb = load_workbook(xlsx)
    assert wb.sheetnames[0] == "Start" and "Spiel-Baseline" in wb.sheetnames
    assert all(ws["A1"].value == FIXTURE_BANNER for ws in wb.worksheets)


def test_readback_detects_tampered_value(tmp_config):
    result = run_pipeline(load_config(tmp_config))
    xlsx = export_excel(result.run_dir)
    wb = load_workbook(xlsx)
    ws = wb["Spiel-Baseline"]
    header = [c.value for c in ws[HEADER_ROW]]
    col = header.index("revenue_gross_chf") + 1
    ws.cell(row=HEADER_ROW + 1, column=col).value = 9999.0
    wb.save(xlsx)
    report = readback_excel(result.run_dir, xlsx)
    assert not report["passed"]
    failed = {c["check_id"] for c in report["checks"] if c["status"] == "FAIL"}
    assert "T-Spiel-Baseline" in failed and "R03" in failed


def test_readback_detects_formula_and_missing_banner(tmp_config):
    result = run_pipeline(load_config(tmp_config))
    xlsx = export_excel(result.run_dir)
    wb = load_workbook(xlsx)
    wb["Annahmen"]["A1"] = "=1+1"
    wb.save(xlsx)
    failed = {c["check_id"] for c in readback_excel(result.run_dir, xlsx)["checks"] if c["status"] == "FAIL"}
    assert {"R01", "R02"} <= failed


def test_cli_run_end_to_end(tmp_config, capsys):
    assert main(["run", "--config", str(tmp_config)]) == 0
    out = capsys.readouterr().out
    assert "KÜNSTLICHE TESTDATEN" in out and "Readback BESTANDEN" in out


def test_analyze_real_mode_end_to_end(clean_config, tmp_path, capsys):
    """Echtdaten-Weg (release_aggregates) mit künstlichem bereinigtem Lauf: Lauf → Bericht → Excel → Readback."""
    report_dir = tmp_path / "report"
    assert main(["analyze", "--config", str(clean_config), "--report-dir", str(report_dir)]) == 0
    out = capsys.readouterr().out
    assert "Readback BESTANDEN" in out and "FAIL" not in out
    md = (report_dir / "01_baseline_erste_erkenntnisse.md").read_text(encoding="utf-8")
    assert "VORLÄUFIG" in md and "### H3" in md
    assert len(list((report_dir / "figures").glob("*.png"))) == 5
    run_dir = next((tmp_path / "outputs").iterdir())
    wb = load_workbook(next(run_dir.glob("FCSG_BASELINE_*.xlsx")))
    assert {"Hypothesen", "Kontext", "Reto-Abgleich"} <= set(wb.sheetnames)
    assert all(ws["A1"].value.startswith("VORLÄUFIG") for ws in wb.worksheets)


def test_analyze_rejects_fixture_mode(tmp_config, capsys):
    assert main(["analyze", "--config", str(tmp_config)]) == 2
    assert "nicht freigegeben" in capsys.readouterr().err


def test_cli_rejects_unreleased_mode(tmp_path, capsys):
    cfg = tmp_path / "bad.yaml"
    cfg.write_text("data_mode: real_data\ninput_dir: x\noutput_dir: y\n", encoding="utf-8")
    assert main(["run", "--config", str(cfg)]) == 2
    assert "nicht freigegeben" in capsys.readouterr().err

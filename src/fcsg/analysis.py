"""Analyse-Lauf auf echten (bereinigten) Daten: Baseline + Hypothesen → Laufordner mit Manifest.

Liest ``data/clean/LATEST`` (Datenmodus ``release_aggregates``, D-001 c) und schreibt nach
``<output_dir>/<run_id>/`` (bei echten Daten ausserhalb des Repos, D-015). Excel und Bericht werden
anschliessend ausschliesslich aus diesen Artefakten erzeugt.
"""

from __future__ import annotations

import json
import platform
from datetime import datetime
from importlib.metadata import version
from pathlib import Path
from zoneinfo import ZoneInfo

import pandas as pd

from fcsg import __version__
from fcsg.baseline import (add_real_kpis, build_mart_match_real, coverage_real, kpi_checks_real, load_clean,
                           reto_comparison, season_summary_real, source_total_check)
from fcsg.config import ProjectConfig
from fcsg.hypotheses import run_all
from fcsg.joins import _check
from fcsg.pipeline import RunResult, make_run_id

ANALYSIS_TABLES = {
    "mart_match.csv": "1 Herren-Pflichtspiel pro Zeile mit Spiel-KPIs (vorläufig)",
    "season_summary.csv": "gewichtete Saisonwerte (Σ/Σ) mit Stichprobe",
    "coverage.csv": "Abdeckung je Saison und Stichproben der Hypothesen",
    "quality_checks.csv": "Prüfprotokoll (Join, Summenerhalt, KPI, Quellabgleich)",
    "unmatched_report.csv": "nicht zuordenbare oder ausgeschlossene Zeilen",
    "sources.csv": "Eingangsdateien des bereinigten Laufs (Name, Hash)",
    "reto_comparison.csv": "Abgleich mit Retos Sichtungswerten (DQ S. 3–4)",
    "source_total_check.csv": "Spielzeilen vs. Quell-Tab «Entwicklung»",
    "hypotheses.csv": "Ergebnis je Hypothese (H1–H3, K1)",
    "h1_sold_out.csv": "H1: KF nach Ausverkauft",
    "h2_correlations.csv": "H2: Korrelationen Ankunft × Catering",
    "h3_leadtime.csv": "H3: Eintrittsquote nach Kaufvorlauf",
    "context_associations.csv": "K1: alle Kontext-Zusammenhänge",
}


def run_analysis(config: ProjectConfig, today: str | None = None) -> RunResult:
    """Führt Baseline und Hypothesentests aus und schreibt alle Artefakte.

    Returns:
        ``RunResult`` (Lauf-ID, Laufordner, Anzahl FAIL-Prüfungen).
    """
    if config.clean_dir is None:
        raise ValueError("clean_dir fehlt in der Konfiguration.")
    clean_id, t, clean_manifest = load_clean(config.clean_dir)
    run_id = make_run_id(config.timezone, kind="baseline")
    run_dir = config.output_dir / run_id
    run_dir.mkdir(parents=True, exist_ok=False)

    res = build_mart_match_real(t, today=today)
    mart = add_real_kpis(res.mart)
    checks = res.checks + kpi_checks_real(mart)
    src = source_total_check(t)
    bad = src[src["status"] != "OK"]
    checks.append(_check("Q01", "Catering-Spielzeilen = Quell-Tab «Entwicklung» (Meisterschaft, ab 21/22)", bad.empty,
                         "; ".join(f"{r.season}: {r.rel_diff:+.1%} ({r.rows_n:.0f} vs. {r.entwicklung_n:.0f} Spiele)"
                                   for r in bad.itertuples()) or "alle Saisons ± 0.5 %", warn_only=True))

    hyps = run_all(t, mart)
    h = {r.hid: r for r in hyps}
    tables = {
        "mart_match.csv": mart,
        "season_summary.csv": season_summary_real(mart),
        "coverage.csv": coverage_real(mart),
        "quality_checks.csv": pd.DataFrame(checks),
        "unmatched_report.csv": res.unmatched,
        "sources.csv": pd.DataFrame(clean_manifest["inputs"]).assign(clean_run_id=clean_id),
        "reto_comparison.csv": reto_comparison(mart, elasticity=h["H1"].estimate),
        "source_total_check.csv": src,
        "hypotheses.csv": pd.DataFrame([r.summary_row() for r in hyps]),
        "h1_sold_out.csv": h["H1"].table,
        "h2_correlations.csv": h["H2"].table,
        "h3_leadtime.csv": h["H3"].table,
        "context_associations.csv": h["K1"].table,
    }
    for name, df in tables.items():
        df.to_csv(run_dir / name, index=False, encoding="utf-8", lineterminator="\n")

    n_fail = sum(c["status"] == "FAIL" for c in checks)
    manifest = {
        "run_id": run_id,
        "created_at": datetime.now(ZoneInfo(config.timezone)).isoformat(timespec="seconds"),
        "data_mode": config.data_mode,
        "clean_run_id": clean_id,
        "config_file": config.config_path.name,
        "code_version": __version__,
        "python": platform.python_version(),
        "packages": {p: version(p) for p in ("pandas", "numpy", "openpyxl", "matplotlib")},
        "checks": {"total": len(checks), "fail": n_fail, "warn": sum(c["status"] == "WARN" for c in checks)},
        "coverage": {"home_matches": len(mart), "with_attendance": int(mart["attendance_rate"].notna().sum()),
                     "with_catering": int(mart["revenue_gross_chf"].notna().sum()),
                     "with_access": int(mart["scan_count"].notna().sum())},
        "outputs": ANALYSIS_TABLES,
    }
    (run_dir / "manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    return RunResult(run_id=run_id, run_dir=run_dir, n_fail=n_fail)

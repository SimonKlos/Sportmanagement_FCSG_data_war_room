"""Orchestrierung eines Laufs: Laden → Datenkern → KPIs → Ablage mit Manifest.

Ein Lauf schreibt nach ``<output_dir>/<run_id>/`` CSV-Zwischenergebnisse und ``manifest.json``.
Der Excel-Export (``fcsg.export``) arbeitet anschliessend nur mit diesen Laufartefakten.
"""

from __future__ import annotations

import json
import platform
import secrets
from dataclasses import dataclass
from datetime import datetime
from importlib.metadata import version
from pathlib import Path
from zoneinfo import ZoneInfo

import pandas as pd

from fcsg import FIXTURE_BANNER, FIXTURE_MARKER, __version__
from fcsg.config import ProjectConfig
from fcsg.io import SOURCE_SCHEMAS, file_sha256, load_all_sources
from fcsg.joins import build_mart_match
from fcsg.metrics import add_match_kpis, kpi_checks, season_summary

# Laufartefakte (Dateiname → Beschreibung); dienen auch als Outputmanifest.
RUN_TABLES = {
    "mart_match.csv": "1 Heimspiel pro Zeile mit Spiel-KPIs",
    "season_summary.csv": "gewichtete Saisonwerte mit Stichprobe",
    "coverage.csv": "Abdeckung je Modul / gemeinsame Stichproben",
    "quality_checks.csv": "Prüfprotokoll (Join, Summenerhalt, KPI)",
    "unmatched_report.csv": "nicht zuordenbare oder ausgeschlossene Zeilen",
    "sources.csv": "verwendete Inputdateien mit Hash",
}


@dataclass(frozen=True)
class RunResult:
    run_id: str
    run_dir: Path
    n_fail: int


def make_run_id(tz: str, kind: str = "fixture") -> str:
    """Lauf-ID: lokaler Zeitstempel + Art + Zufallssuffix, z. B. ``20261010T153012_fixture_3fa1``."""
    stamp = datetime.now(ZoneInfo(tz)).strftime("%Y%m%dT%H%M%S")
    return f"{stamp}_{kind}_{secrets.token_hex(2)}"


def coverage_table(mart: pd.DataFrame) -> pd.DataFrame:
    """Abdeckung je Modul und gemeinsame Stichproben (AA S. 5: keine fiktive Gesamtstichprobe)."""
    has_ctx = pd.Series(False, index=mart.index)  # Kontextquelle in dieser Fixture nicht enthalten
    modules = {
        "Heimspiele (dim_match)": pd.Series(True, index=mart.index),
        "Anwesenheit (SOLL+IST vorhanden)": mart["has_attendance"],
        "Catering (Spiel-Zeile vorhanden)": mart["has_catering"],
        "Zutritt (Scans vorhanden)": mart["has_access"],
        "Anwesenheit+Catering (gemeinsam)": mart["has_attendance"] & mart["has_catering"],
        "Zutritt+Catering (gemeinsam)": mart["has_access"] & mart["has_catering"],
        "Kontext (nicht in Fixture)": has_ctx,
    }
    rows = []
    for module, mask in modules.items():
        sub = mart[mask]
        rows.append({
            "module": module,
            "n_matches": int(mask.sum()),
            "share_of_home_matches": float(mask.mean()) if len(mart) else float("nan"),
            "seasons": ", ".join(sorted(sub["season"].unique())) or "-",
        })
    return pd.DataFrame(rows)


def run_pipeline(config: ProjectConfig) -> RunResult:
    """Führt einen vollständigen Lauf aus und schreibt die Artefakte.

    Returns:
        ``RunResult`` mit Lauf-ID, Laufordner und Anzahl FAIL-Prüfungen.
    """
    run_id = make_run_id(config.timezone)
    run_dir = config.output_dir / run_id
    run_dir.mkdir(parents=True, exist_ok=False)

    sources = load_all_sources(config.input_dir)
    mart, unmatched, checks = build_mart_match(
        sources["attendance_match"], sources["catering_match"], sources["access_scans"]
    )
    mart = add_match_kpis(mart)
    checks += kpi_checks(mart)
    mart.insert(0, "data_origin", FIXTURE_MARKER)

    source_rows = []
    for name, schema in SOURCE_SCHEMAS.items():
        path = config.input_dir / schema.filename
        source_rows.append({"source": name, "file": schema.filename, "grain": schema.grain,
                            "n_rows": len(sources[name]), "sha256": file_sha256(path),
                            "data_origin": FIXTURE_MARKER})

    tables = {
        "mart_match.csv": mart,
        "season_summary.csv": season_summary(mart),
        "coverage.csv": coverage_table(mart),
        "quality_checks.csv": pd.DataFrame(checks),
        "unmatched_report.csv": unmatched,
        "sources.csv": pd.DataFrame(source_rows),
    }
    for filename, df in tables.items():
        df.to_csv(run_dir / filename, index=False, encoding="utf-8", lineterminator="\n")

    n_fail = sum(c["status"] == "FAIL" for c in checks)
    manifest = {
        "run_id": run_id,
        "created_at": datetime.now(ZoneInfo(config.timezone)).isoformat(timespec="seconds"),
        "data_mode": config.data_mode,
        "banner": FIXTURE_BANNER,
        "config_file": config.config_path.name,
        "input_dir_name": config.input_dir.name,  # bewusst nur Ordnername, kein lokaler Pfad
        "inputs": source_rows,
        "code_version": __version__,
        "python": platform.python_version(),
        "packages": {p: version(p) for p in ("pandas", "numpy", "openpyxl", "PyYAML")},
        "checks": {"total": len(checks), "fail": n_fail,
                   "warn": sum(c["status"] == "WARN" for c in checks)},
        "coverage": {"home_matches": len(mart), "with_attendance": int(mart["has_attendance"].sum()),
                     "with_catering": int(mart["has_catering"].sum()), "with_access": int(mart["has_access"].sum())},
        "outputs": RUN_TABLES,
    }
    (run_dir / "manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    return RunResult(run_id=run_id, run_dir=run_dir, n_fail=n_fail)

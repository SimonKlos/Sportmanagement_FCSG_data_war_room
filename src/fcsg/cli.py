"""Kommandozeilen-Einstieg.

Beispiele (im Projektroot, venv aktiv)::

    python -m fcsg.cli inventory --config config/project.example.yaml
    python -m fcsg.cli run       --config config/project.example.yaml
    python -m fcsg.cli export    --config config/project.example.yaml --run-id <lauf-id>
    python -m fcsg.cli readback  --config config/project.example.yaml --run-id <lauf-id>
    python -m fcsg.cli make-fixture --target tests/fixtures/synthetic_mini
    python -m fcsg.cli inventory-raw --config config/project.local.yaml   # nur Struktur echter Dateien
    python -m fcsg.cli prepare-data  --config config/project.local.yaml   # echte Daten → data/clean
    python -m fcsg.cli analyze       --config config/project.local.yaml   # Baseline + Hypothesen + Bericht + Excel

``run`` führt standardmässig auch Export und Readback aus (``--no-export`` schaltet das ab).
Exit-Code 0 = alles OK, 1 = Prüfung fehlgeschlagen, 2 = Konfigurations-/Schemafehler.
"""

from __future__ import annotations

import argparse
import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import pandas as pd

from fcsg import FIXTURE_BANNER
from fcsg.analysis import run_analysis
from fcsg.config import PREPARE_MODES, STRUCTURE_MODES, ConfigError, load_config
from fcsg.export import export_excel, readback_excel
from fcsg.fixtures import write_synthetic_mini
from fcsg.inventory import build_inventory, write_inventory
from fcsg.io import SchemaError, inventory
from fcsg.joins import JoinError
from fcsg.pipeline import run_pipeline
from fcsg.prepare import PrivacyError, run_prepare
from fcsg.report import write_report

PROJECT_ROOT = Path(__file__).resolve().parents[2]


def _run_dir(config_path: str, run_id: str) -> Path:
    cfg = load_config(config_path)
    run_dir = cfg.output_dir / run_id
    if not (run_dir / "manifest.json").is_file():
        raise ConfigError(f"Lauf '{run_id}' nicht gefunden (kein manifest.json).")
    return run_dir


def _print_readback(report: dict) -> int:
    for c in report["checks"]:
        print(f"  [{c['status']}] {c['check_id']}: {c['description']} – {c['detail']}")
    print(f"Readback {'BESTANDEN' if report['passed'] else 'FEHLGESCHLAGEN'}: {report['xlsx']}")
    return 0 if report["passed"] else 1


def cmd_inventory(args: argparse.Namespace) -> int:
    cfg = load_config(args.config)
    with pd.option_context("display.max_columns", None, "display.width", 200, "display.max_colwidth", 60):
        print(inventory(cfg.input_dir).drop(columns=["columns"]).to_string(index=False))
    return 0


def cmd_run(args: argparse.Namespace) -> int:
    cfg = load_config(args.config)
    print(FIXTURE_BANNER)
    result = run_pipeline(cfg)
    print(f"Lauf-ID: {result.run_id}")
    print(f"Laufordner: outputs/{result.run_dir.name}")
    checks = pd.read_csv(result.run_dir / "quality_checks.csv")
    for _, c in checks.iterrows():
        print(f"  [{c['status']}] {c['check_id']}: {c['description']} – {c['detail']}")
    if result.n_fail:
        print(f"{result.n_fail} Prüfung(en) FAIL – Export übersprungen.")
        return 1
    if args.no_export:
        return 0
    xlsx = export_excel(result.run_dir)
    print(f"Excel: outputs/{result.run_dir.name}/{xlsx.name}")
    return _print_readback(readback_excel(result.run_dir, xlsx))


def cmd_export(args: argparse.Namespace) -> int:
    run_dir = _run_dir(args.config, args.run_id)
    xlsx = export_excel(run_dir)
    print(f"Excel: outputs/{run_dir.name}/{xlsx.name}")
    return _print_readback(readback_excel(run_dir, xlsx))


def cmd_readback(args: argparse.Namespace) -> int:
    return _print_readback(readback_excel(_run_dir(args.config, args.run_id)))


def cmd_inventory_raw(args: argparse.Namespace) -> int:
    """Strukturinventar echter Rohdateien (nur Datenmodus structure_only)."""
    cfg = load_config(args.config, allowed_modes=STRUCTURE_MODES | PREPARE_MODES)
    roots = [("raw", cfg.input_dir)] + [("projekt", p) for p in cfg.extra_input_files]
    missing = [label for label, p in roots if not p.exists()]
    if missing:
        raise ConfigError(f"Inputpfad nicht gefunden: {', '.join(missing)}")
    print("Strukturinventar (structure_only) – es werden keine Zellinhalte ausgegeben.")
    inv = build_inventory(roots, progress=lambda line: print(f"  {line}", flush=True))
    out_dir = cfg.output_dir / f"inventory_{datetime.now(ZoneInfo(cfg.timezone)):%Y%m%dT%H%M%S}"
    paths = write_inventory(inv, out_dir)
    n_personal = int((inv.columns["personal_category"] != "").sum()) if not inv.columns.empty else 0
    print(f"Dateien: {len(inv.files)} | Tabs: {len(inv.sheets)} | Spalten: {len(inv.columns)} | "
          f"Personenbezug-Kandidaten: {n_personal}")
    print(f"Bericht: {paths['md']}")
    print(f"Excel:   {paths['xlsx']}")
    return 0


def cmd_prepare_data(args: argparse.Namespace) -> int:
    """Bereinigung echter Daten → data/clean/<run_id>/ (nur Datenmodus release_aggregates)."""
    cfg = load_config(args.config, allowed_modes=PREPARE_MODES)
    if cfg.clean_dir is None:
        raise ConfigError("clean_dir fehlt in der Konfiguration.")
    context = next((p for p in cfg.extra_input_files if "spielkontext" in p.name.lower()), None)
    if context is None or not context.exists():
        raise ConfigError("Spielkontext-Tabelle (extra_input_files) nicht gefunden.")
    out_dir = run_prepare(cfg.input_dir, context, cfg.clean_dir, cfg.timezone,
                          progress=lambda s: print(f"  {s}", flush=True))
    checks = pd.read_csv(out_dir / "quality_checks.csv")
    for _, c in checks.iterrows():
        print(f"  [{c['status']}] {c['check_id']}: {c['description']} – {c['detail']}")
    print(f"Bereinigte Daten: {out_dir}")
    return 0 if (checks["status"] != "FAIL").all() else 1


def cmd_analyze(args: argparse.Namespace) -> int:
    """Baseline + Hypothesen auf data/clean/LATEST → Laufordner, Bericht (docs/analysis), Excel + Readback."""
    cfg = load_config(args.config, allowed_modes=PREPARE_MODES)
    result = run_analysis(cfg)
    print(f"Lauf-ID: {result.run_id}")
    print(f"Laufordner: {result.run_dir}")
    checks = pd.read_csv(result.run_dir / "quality_checks.csv")
    for _, c in checks.iterrows():
        print(f"  [{c['status']}] {c['check_id']}: {c['description']} – {c['detail']}")
    if result.n_fail:
        print(f"{result.n_fail} Prüfung(en) FAIL – Bericht und Export übersprungen.")
        return 1
    report = write_report(result.run_dir, Path(args.report_dir) if args.report_dir else PROJECT_ROOT / "docs" / "analysis")
    print(f"Bericht: {report}")
    xlsx = export_excel(result.run_dir)
    print(f"Excel: {xlsx}")
    return _print_readback(readback_excel(result.run_dir, xlsx))


def cmd_make_fixture(args: argparse.Namespace) -> int:
    for p in write_synthetic_mini(args.target):
        print(f"geschrieben: {p.name}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="fcsg", description="FCSG Phase 1 – technischer Vertikalschnitt")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("inventory", help="Dateiinventar (nur Struktur, keine Inhalte)")
    p.add_argument("--config", required=True)
    p.set_defaults(func=cmd_inventory)

    p = sub.add_parser("run", help="Pipeline-Lauf inkl. Excel-Export und Readback")
    p.add_argument("--config", required=True)
    p.add_argument("--no-export", action="store_true", help="nur Laufartefakte, kein Excel")
    p.set_defaults(func=cmd_run)

    p = sub.add_parser("export", help="Excel für bestehenden Lauf erzeugen und zurücklesen")
    p.add_argument("--config", required=True)
    p.add_argument("--run-id", required=True)
    p.set_defaults(func=cmd_export)

    p = sub.add_parser("readback", help="Excel eines Laufs gegen Datenkern prüfen")
    p.add_argument("--config", required=True)
    p.add_argument("--run-id", required=True)
    p.set_defaults(func=cmd_readback)

    p = sub.add_parser("inventory-raw", help="Strukturinventar echter Rohdateien (nur structure_only)")
    p.add_argument("--config", required=True)
    p.set_defaults(func=cmd_inventory_raw)

    p = sub.add_parser("prepare-data", help="echte Daten bereinigen/aggregieren nach data/clean (release_aggregates)")
    p.add_argument("--config", required=True)
    p.set_defaults(func=cmd_prepare_data)

    p = sub.add_parser("analyze", help="Baseline + Hypothesen auf bereinigten echten Daten (release_aggregates)")
    p.add_argument("--config", required=True)
    p.add_argument("--report-dir", default=None, help="Zielordner Bericht (Standard: docs/analysis)")
    p.set_defaults(func=cmd_analyze)

    p = sub.add_parser("make-fixture", help="künstliche Mini-Fixture neu schreiben")
    p.add_argument("--target", default="tests/fixtures/synthetic_mini")
    p.set_defaults(func=cmd_make_fixture)
    return parser


def main(argv: list[str] | None = None) -> int:
    # Windows-Konsole: Umlaute/Gedankenstriche sicher ausgeben.
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    args = build_parser().parse_args(argv)
    try:
        return args.func(args)
    except (ConfigError, SchemaError, JoinError, PrivacyError, FileNotFoundError, ValueError) as exc:
        print(f"FEHLER: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())

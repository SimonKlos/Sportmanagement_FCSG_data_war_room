"""Laden und Absichern der Laufkonfiguration.

Die Konfiguration ist eine kleine YAML-Datei (Vorlage: ``config/project.example.yaml``).
Wichtigste Schutzregel: Solange kein Datenmodus fachlich freigegeben ist (docs/decisions.md, D-001),
akzeptiert die Pipeline ausschliesslich ``data_mode: synthetic_fixture``.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml

ALLOWED_DATA_MODES = {"synthetic_fixture"}
# Strukturmodus (D-001 b): nur für das Strukturinventar, nie für Analyse-Läufe.
STRUCTURE_MODES = {"structure_only"}
# Datenmodus für nicht personenbezogene Daten und Aggregate (D-001 c): Bereinigung nach data/clean.
PREPARE_MODES = {"release_aggregates"}


class ConfigError(ValueError):
    """Konfiguration ungültig oder Datenmodus nicht freigegeben."""


@dataclass(frozen=True)
class ProjectConfig:
    """Validierte Laufkonfiguration; alle Pfade absolut aufgelöst."""

    data_mode: str
    input_dir: Path
    output_dir: Path
    timezone: str
    config_path: Path
    extra_input_files: tuple[Path, ...] = ()
    clean_dir: Path | None = None


def load_config(path: str | Path, allowed_modes: set[str] = ALLOWED_DATA_MODES) -> ProjectConfig:
    """Liest die YAML-Konfiguration und prüft den Datenmodus.

    Relative Pfade werden relativ zum Projektroot (Elternordner von ``config/``) bzw.
    zum Ordner der Config-Datei aufgelöst. ``allowed_modes`` legt fest, welche Datenmodi der
    aufrufende Befehl akzeptiert (Analyse-Lauf: nur ``synthetic_fixture``).

    Raises:
        ConfigError: Datei fehlt, Pflichtfeld fehlt oder Datenmodus ist nicht freigegeben.
    """
    config_path = Path(path).resolve()
    if not config_path.is_file():
        raise ConfigError(f"Konfigurationsdatei nicht gefunden: {config_path.name}")
    raw = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}

    missing = [k for k in ("data_mode", "input_dir", "output_dir") if k not in raw]
    if missing:
        raise ConfigError(f"Pflichtfelder fehlen in der Konfiguration: {', '.join(missing)}")

    data_mode = str(raw["data_mode"])
    if data_mode not in allowed_modes:
        raise ConfigError(
            f"Datenmodus '{data_mode}' ist für diesen Befehl nicht freigegeben. Erlaubt: {sorted(allowed_modes)}. "
            "Siehe Entscheid D-001 (docs/decisions.md)."
        )

    base = config_path.parent.parent if config_path.parent.name == "config" else config_path.parent
    return ProjectConfig(
        data_mode=data_mode,
        input_dir=(base / raw["input_dir"]).resolve(),
        output_dir=(base / raw["output_dir"]).resolve(),
        timezone=str(raw.get("timezone", "Europe/Zurich")),
        config_path=config_path,
        extra_input_files=tuple((base / p).resolve() for p in raw.get("extra_input_files", []) or []),
        clean_dir=(base / raw["clean_dir"]).resolve() if raw.get("clean_dir") else None,
    )

"""Laden der Quellen mit Schemaprüfung.

Fehlermeldungen nennen nur Datei-/Spaltennamen und Anzahlen, **nie Zellinhalte**, damit bei
späteren echten Daten keine Rohwerte in Logs oder Toolausgaben gelangen.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from fcsg import FIXTURE_MARKER


class SchemaError(ValueError):
    """Quelldatei entspricht nicht dem erwarteten Inputschema."""


@dataclass(frozen=True)
class SourceSchema:
    """Inputvertrag einer Quelle: Pflichtspalten und Datentypen."""

    name: str
    filename: str
    grain: str  # fachliche Bedeutung einer Zeile
    date_columns: tuple[str, ...]
    numeric_columns: tuple[str, ...]
    text_columns: tuple[str, ...]

    @property
    def required_columns(self) -> tuple[str, ...]:
        return ("data_origin", *self.date_columns, *self.numeric_columns, *self.text_columns)


SOURCE_SCHEMAS: dict[str, SourceSchema] = {
    "attendance_match": SourceSchema(
        name="attendance_match",
        filename="attendance_match.csv",
        grain="1 Zeile = 1 Heimspiel",
        date_columns=("match_date",),
        numeric_columns=("soll", "ist", "ist_vip", "ist_guests"),
        text_columns=("season", "competition", "opponent_label", "kickoff_local"),
    ),
    "catering_match": SourceSchema(
        name="catering_match",
        filename="catering_match.csv",
        grain="1 Zeile = 1 Spiel oder Event (event_type)",
        date_columns=("match_date",),
        numeric_columns=("public_attendance", "receipts", "revenue_gross_chf", "revenue_net_chf"),
        text_columns=("event_type", "event_label"),
    ),
    "access_scans": SourceSchema(
        name="access_scans",
        filename="access_scans.csv",
        grain="1 Zeile = 1 erlaubter Scan",
        date_columns=("match_date",),
        numeric_columns=("minutes_before_kickoff",),
        text_columns=("reader_sector",),
    ),
}


def file_sha256(path: Path) -> str:
    """SHA-256 einer Datei (für Manifest/Rückverfolgbarkeit)."""
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_source(input_dir: Path, schema: SourceSchema, require_fixture_marker: bool = True) -> pd.DataFrame:
    """Lädt eine Quelle als DataFrame und prüft das Inputschema.

    Verarbeitung: CSV lesen; Pflichtspalten prüfen; Datumsspalten als ``YYYY-MM-DD`` parsen;
    numerische Spalten als Float (Missing bleibt NaN, wird **nicht** zu 0). Im Fixture-Modus muss
    jede Zeile ``data_origin == FIXTURE_MARKER`` tragen.

    Raises:
        SchemaError: Datei fehlt, Spalten fehlen, Werte nicht parsebar oder Fixture-Marker fehlt.
    """
    path = input_dir / schema.filename
    if not path.is_file():
        raise SchemaError(f"[{schema.name}] Datei fehlt: {schema.filename}")
    df = pd.read_csv(path, dtype=str, keep_default_na=True, encoding="utf-8")

    missing = [c for c in schema.required_columns if c not in df.columns]
    if missing:
        raise SchemaError(f"[{schema.name}] Pflichtspalten fehlen: {', '.join(missing)}")

    if require_fixture_marker:
        n_bad = int((df["data_origin"] != FIXTURE_MARKER).sum())
        if n_bad:
            raise SchemaError(
                f"[{schema.name}] {n_bad} Zeile(n) ohne Fixture-Marker. Im Modus synthetic_fixture "
                "werden nur markierte künstliche Daten verarbeitet."
            )

    for col in schema.date_columns:
        # Datumsspalten sind Join-Schlüssel und dürfen daher nicht leer sein.
        parsed = pd.to_datetime(df[col], format="%Y-%m-%d", errors="coerce")
        n_bad = int(parsed.isna().sum())
        if n_bad:
            raise SchemaError(f"[{schema.name}] Spalte {col}: {n_bad} Wert(e) leer oder kein Datum YYYY-MM-DD")
        df[col] = parsed.dt.date

    for col in schema.numeric_columns:
        parsed = pd.to_numeric(df[col], errors="coerce")
        n_bad = int(parsed.isna().sum() - df[col].isna().sum())
        if n_bad:
            raise SchemaError(f"[{schema.name}] Spalte {col}: {n_bad} nicht-numerische(r) Wert(e)")
        df[col] = parsed.astype("float64")

    return df[list(schema.required_columns)]


def load_all_sources(input_dir: Path) -> dict[str, pd.DataFrame]:
    """Lädt alle in ``SOURCE_SCHEMAS`` definierten Quellen aus ``input_dir``."""
    return {name: load_source(input_dir, schema) for name, schema in SOURCE_SCHEMAS.items()}


def inventory(input_dir: Path) -> pd.DataFrame:
    """Dateiinventar ohne Inhalte: Name, Zeilen, Spalten, Hash, Schema-Status.

    Gibt bewusst keine Zellwerte aus; nur Strukturinformationen.
    """
    rows = []
    for name, schema in SOURCE_SCHEMAS.items():
        path = input_dir / schema.filename
        row = {"source": name, "file": schema.filename, "grain": schema.grain, "exists": path.is_file()}
        if path.is_file():
            header = pd.read_csv(path, nrows=0, encoding="utf-8").columns.tolist()
            with path.open(encoding="utf-8") as fh:
                n_rows = sum(1 for _ in fh) - 1
            missing = [c for c in schema.required_columns if c not in header]
            row.update(
                n_rows=n_rows,
                n_columns=len(header),
                columns=", ".join(header),
                missing_required=", ".join(missing) or "-",
                sha256=file_sha256(path)[:16],
            )
        rows.append(row)
    return pd.DataFrame(rows)

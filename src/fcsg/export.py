"""Excel-Export eines Laufs und Readback-Prüfung.

Excel ist reine Ergebnisausgabe: Es werden nur Werte geschrieben, keine Formeln (Excel-Leser rechnen
Formeln nicht neu; PROJECT_SETUP §5). Jedes Blatt trägt in Zelle A1 ein Banner je Datenmodus:
Fixture-Läufe (``synthetic_fixture``) bzw. Analyse-Läufe auf echten Daten (``release_aggregates``, «VORLÄUFIG»).
Der Readback liest die Datei wieder ein und vergleicht jede Tabelle mit den Laufartefakten (CSV).
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
from openpyxl import load_workbook
from openpyxl.styles import Font, PatternFill

from fcsg import FIXTURE_BANNER, FIXTURE_MARKER
from fcsg.baseline import KPI_DEFINITIONS_REAL
from fcsg.metrics import KPI_DEFINITIONS

HEADER_ROW = 4  # 1-basiert in Excel; Zeilen 1–2 Banner/Beschreibung, Zeile 3 leer

# Blattname → (Quell-CSV im Laufordner oder None, Beschreibung)
TABLE_SHEETS: dict[str, tuple[str | None, str]] = {
    "Quellen": ("sources.csv", "Verwendete Inputdateien (künstliche Fixture) mit SHA-256"),
    "Definitionen": (None, "KPI-Formeln laut Arbeitsauftrag; fachliche Definitionen noch NICHT freigegeben"),
    "Abdeckung": ("coverage.csv", "Abdeckung je Modul; gemeinsame Stichproben unterscheiden sich"),
    "Qualität": ("quality_checks.csv", "Prüfprotokoll: Join-Kardinalität, Summenerhalt, KPI-Identität"),
    "Unmatched": ("unmatched_report.csv", "Nicht zuordenbare bzw. bewusst ausgeschlossene Zeilen"),
    "Spiel-Baseline": ("mart_match.csv", "1 Heimspiel pro Zeile; leere Zelle = fehlender Wert (nicht 0)"),
    "Saison-Baseline": ("season_summary.csv", "Gewichtete Saisonwerte (Σ/Σ); 'unweighted_mean' nur zum Vergleich"),
    "Annahmen": (None, "Technische Annahmen dieses Vertikalschnitts"),
}

ASSUMPTIONS = [
    ("A01", "Alle Daten sind künstlich (Fixture synthetic_mini). Keine Aussage über den FCSG."),
    ("A02", "Spieldatum ist Join-Schlüssel; mehrere Heimspiele am selben Datum führen zum Abbruch."),
    ("A03", "Catering-Zeilen mit event_type != 'match' werden ausgeschlossen und im Unmatched-Report gezeigt."),
    ("A04", "SOLL, IST, Public-Anwesende und Umsatzbasis sind fachlich nicht definiert; Brutto/Netto getrennt."),
    ("A05", "Scans sind keine eindeutigen Besucher; keine Deduplizierung, keine Aufenthaltsdauer."),
    ("A06", "Ankunftsanteile: ≥ 45 Min. vor Anpfiff bzw. 0 ≤ Min. < 15; Abgrenzung technisch gewählt."),
    ("A07", "Kein Kontextmodell, keine Diagnoselücke: Modellierung erst nach Baseline-Freigabe."),
]


REAL_BANNER = "VORLÄUFIG – echte FCSG-Daten (aggregiert, Herren), vertraulich – Definitionen D-004/D-005 offen"

REAL_SHEETS: dict[str, tuple[str | None, str]] = {
    "Quellen": ("sources.csv", "Eingangsdateien des bereinigten Laufs (Dateiname, Hash) – keine Inhalte"),
    "Definitionen": (None, "KPI-Formeln (Arbeitsdefinitionen D-025); fachlich noch NICHT freigegeben"),
    "Abdeckung": ("coverage.csv", "Abdeckung je Saison und Stichproben der Hypothesen"),
    "Qualität": ("quality_checks.csv", "Prüfprotokoll: Join-Kardinalität, Summenerhalt, KPI-Identität, Quellabgleich"),
    "Unmatched": ("unmatched_report.csv", "Nicht zuordenbare bzw. bewusst ausgeschlossene Zeilen"),
    "Spiel-Baseline": ("mart_match.csv", "1 Herren-Pflichtspiel pro Zeile; leere Zelle = fehlender Wert (nicht 0)"),
    "Saison-Baseline": ("season_summary.csv", "Gewichtete Saisonwerte (Σ/Σ); 'unweighted_mean' nur zum Vergleich"),
    "Reto-Abgleich": ("reto_comparison.csv", "Eigene Werte vs. Retos Sichtung (DQ S. 3–4)"),
    "Quellabgleich": ("source_total_check.csv", "Spielzeilen vs. Quell-Tab «Entwicklung»"),
    "Hypothesen": ("hypotheses.csv", "H1–H3 und K1: Aussage, Methode, Effekt, KI, Status (vorläufig)"),
    "H1-Ausverkauft": ("h1_sold_out.csv", "H1: KF nach Ausverkauft (saison-zentriert)"),
    "H2-Ankunft": ("h2_correlations.csv", "H2: Spearman-Korrelationen Ankunft × Catering (saison-zentriert)"),
    "H3-Vorlauf": ("h3_leadtime.csv", "H3: Eintrittsquote Einzeltickets nach Kaufvorlauf"),
    "Kontext": ("context_associations.csv", "K1: Kontext × Zielgrösse, Spearman mit Bootstrap-KI (explorativ)"),
    "Annahmen": (None, "Arbeitsannahmen dieses Laufs"),
}

REAL_ASSUMPTIONS = [
    ("B01", "Spielkalender = Herren-Pflichtspiele (Liga/Cup/UEFA) der Zuschauer-Historie ab 21/22; Frauen ausgeschlossen (D-016)."),
    ("B02", "Quellen je Datum aggregiert, 1:1-Join über Datum (D-007); abgesagte Spiele und Freundschaftsspiele ausgeschlossen."),
    ("B03", "Zutritt: Datum in zwei Dateien (23/24) → Datei mit den meisten Scans; Ankunft nur bei vollständigem Zutritt (D-018)."),
    ("B04", "KF = Catering-Umsatz / Public Netto der Catering-Datei; Brutto und Netto getrennt (D-005 offen)."),
    ("B05", "Bonsrate und Ø Bon erst ab 23/24 (D-019)."),
    ("B06", "Deckungsbeitrag nicht berechnet – keine Kosten-/Margendaten (D-003)."),
    ("B07", "Hypothesen = Assoziationen auf Spielebene (saison-zentriert, Bootstrap-KI); keine Kausalität, keine Potenziale."),
    ("B08", "Schulferien vor 26/27 recherchiert (D-021); Wetter = Tageswerte."),
]

MODES = {
    "synthetic_fixture": {"banner": FIXTURE_BANNER, "prefix": "FCSG_FIXTURE_", "sheets": TABLE_SHEETS,
                          "defs": KPI_DEFINITIONS, "assumptions": ASSUMPTIONS, "origin": FIXTURE_MARKER,
                          "title": "FCSG Fixture-Lauf"},
    "release_aggregates": {"banner": REAL_BANNER, "prefix": "FCSG_BASELINE_", "sheets": REAL_SHEETS,
                           "defs": KPI_DEFINITIONS_REAL, "assumptions": REAL_ASSUMPTIONS,
                           "origin": "ECHTE_DATEN_AGGREGIERT_VORLAEUFIG", "title": "FCSG Baseline-Lauf (vorläufig)"},
}


def _mode(data_mode: str) -> dict:
    if data_mode not in MODES:
        raise ValueError(f"Export für Datenmodus '{data_mode}' nicht freigegeben.")
    return MODES[data_mode]


def _static_tables(data_mode: str = "synthetic_fixture") -> dict[str, pd.DataFrame]:
    mode = _mode(data_mode)
    defs = pd.DataFrame(mode["defs"])
    defs["status"] = ("technischer Entwurf – fachlich offen" if data_mode == "synthetic_fixture"
                      else "vorläufig – fachlich offen")
    return {
        "Definitionen": defs,
        "Annahmen": pd.DataFrame(mode["assumptions"], columns=["id", "assumption"]),
    }


def _read_run_csv(run_dir: Path, filename: str) -> pd.DataFrame:
    return pd.read_csv(run_dir / filename, encoding="utf-8")


def export_excel(run_dir: Path) -> Path:
    """Schreibt ``FCSG_FIXTURE_<run_id>.xlsx`` bzw. ``FCSG_BASELINE_<run_id>.xlsx`` in den Laufordner."""
    manifest = json.loads((run_dir / "manifest.json").read_text(encoding="utf-8"))
    data_mode = manifest.get("data_mode")
    mode = _mode(data_mode)
    run_id = manifest["run_id"]
    path = run_dir / f"{mode['prefix']}{run_id}.xlsx"
    static = _static_tables(data_mode)

    start = pd.DataFrame(
        [
            ("Lauf-ID", run_id),
            ("Erstellt", manifest["created_at"]),
            ("Datenmodus", manifest["data_mode"]),
            ("Datenherkunft", mode["origin"]),
            ("Bereinigter Datenlauf", manifest.get("clean_run_id", "–")),
            ("Code-Version", manifest["code_version"]),
            ("Python", manifest["python"]),
            ("Prüfungen gesamt / FAIL / WARN",
             f"{manifest['checks']['total']} / {manifest['checks']['fail']} / {manifest['checks']['warn']}"),
            ("Heimspiele / mit Anwesenheit / Catering / Zutritt",
             " / ".join(str(v) for v in manifest["coverage"].values())),
            ("Hinweis", "Werte sind Ergebnisausgabe ohne Formeln. Aktualisierung nur über neuen Pipeline-Lauf."),
        ],
        columns=["item", "value"],
    )

    with pd.ExcelWriter(path, engine="openpyxl") as writer:
        start.to_excel(writer, sheet_name="Start", index=False, startrow=HEADER_ROW - 1)
        for sheet, (csv_name, _) in mode["sheets"].items():
            df = static[sheet] if csv_name is None else _read_run_csv(run_dir, csv_name)
            df.to_excel(writer, sheet_name=sheet, index=False, startrow=HEADER_ROW - 1)

        wb = writer.book
        wb.properties.creator = "fcsg-analysis"
        wb.properties.title = f"{mode['title']} {run_id}"
        descriptions = {"Start": "Laufübersicht"} | {k: v[1] for k, v in mode["sheets"].items()}
        for ws in wb.worksheets:
            ws["A1"] = mode["banner"]
            ws["A1"].font = Font(bold=True, color="FFFFFF", size=12)
            ws["A1"].fill = PatternFill("solid", fgColor="C00000")
            ws["A2"] = descriptions[ws.title]
            ws["A2"].font = Font(italic=True)
            for cell in ws[HEADER_ROW]:
                cell.font = Font(bold=True)
            ws.freeze_panes = ws.cell(row=HEADER_ROW + 1, column=1)
            for col in ws.iter_cols(min_row=HEADER_ROW, max_row=HEADER_ROW):
                width = max(len(str(c.value or "")) for c in col)
                ws.column_dimensions[col[0].column_letter].width = min(max(width + 2, 10), 60)
    return path


def _normalize(series: pd.Series) -> pd.Series:
    return series.map(lambda v: "" if pd.isna(v) else str(v))


def _frames_equal(expected: pd.DataFrame, actual: pd.DataFrame) -> tuple[bool, str]:
    if list(expected.columns) != list(actual.columns):
        return False, "Spalten weichen ab"
    if expected.shape != actual.shape:
        return False, f"Form {actual.shape} statt {expected.shape}"
    for col in expected.columns:
        e, a = expected[col], actual[col]
        if pd.api.types.is_numeric_dtype(e) and pd.api.types.is_numeric_dtype(a):
            if not np.allclose(e.astype(float), a.astype(float), rtol=1e-12, atol=1e-9, equal_nan=True):
                return False, f"Werte in Spalte {col} weichen ab"
        elif not (_normalize(e) == _normalize(a)).all():
            return False, f"Werte in Spalte {col} weichen ab"
    return True, "identisch"


def readback_excel(run_dir: Path, xlsx_path: Path | None = None) -> dict:
    """Liest die Excel-Datei zurück und prüft sie gegen den Datenkern des Laufs.

    Prüfungen: Banner auf jedem Blatt; keine Formeln; jede Tabelle identisch mit Lauf-CSV bzw.
    statischer Tabelle; Saison-KF aus dem Excel-Blatt «Spiel-Baseline» neu berechnet = Blatt
    «Saison-Baseline». Ergebnis wird als ``readback_report.json`` abgelegt.
    """
    data_mode = json.loads((run_dir / "manifest.json").read_text(encoding="utf-8")).get("data_mode")
    mode = _mode(data_mode)
    if xlsx_path is None:
        candidates = sorted(run_dir.glob(f"{mode['prefix']}*.xlsx"))
        if not candidates:
            raise FileNotFoundError("Keine Excel-Datei im Laufordner gefunden; zuerst exportieren.")
        xlsx_path = candidates[-1]

    results = []
    wb = load_workbook(xlsx_path)  # Formeln bleiben als Formeln sichtbar (data_only=False)
    n_formulas = sum(1 for ws in wb.worksheets for row in ws.iter_rows() for c in row if c.data_type == "f")
    results.append(("R01", "Keine Formeln im Export", n_formulas == 0, f"{n_formulas} Formelzellen"))
    missing_banner = [ws.title for ws in wb.worksheets if ws["A1"].value != mode["banner"]]
    results.append(("R02", "Banner auf jedem Blatt", not missing_banner,
                    "alle Blätter" if not missing_banner else f"fehlt: {', '.join(missing_banner)}"))

    static = _static_tables(data_mode)
    sheets = {}
    for sheet, (csv_name, _) in mode["sheets"].items():
        expected = static[sheet] if csv_name is None else _read_run_csv(run_dir, csv_name)
        actual = pd.read_excel(xlsx_path, sheet_name=sheet, header=HEADER_ROW - 1)
        sheets[sheet] = actual
        ok, detail = _frames_equal(expected.reset_index(drop=True), actual.reset_index(drop=True))
        results.append((f"T-{sheet}", f"Blatt '{sheet}' = Datenkern", ok, detail))

    games, seasons = sheets["Spiel-Baseline"], sheets["Saison-Baseline"]
    cat = games[games["public_attendance"].notna() & games["revenue_gross_chf"].notna()]
    recomputed = (cat.groupby("season")["revenue_gross_chf"].sum() / cat.groupby("season")["public_attendance"].sum())
    reported = seasons.set_index("season")["kf_gross_weighted_chf"]
    ok = bool(np.allclose(recomputed.reindex(reported.index).astype(float), reported.astype(float), equal_nan=True))
    results.append(("R03", "Saison-KF brutto aus Spielzeilen neu berechnet = Saison-Blatt", ok,
                    "; ".join(f"{s}: {v:.4f}" for s, v in reported.items())))

    report = {
        "xlsx": xlsx_path.name,
        "passed": all(r[2] for r in results),
        "checks": [{"check_id": c, "description": d, "status": "OK" if ok else "FAIL", "detail": det}
                   for c, d, ok, det in results],
    }
    (run_dir / "readback_report.json").write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    return report

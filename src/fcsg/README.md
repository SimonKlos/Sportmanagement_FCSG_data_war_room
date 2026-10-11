# src/fcsg/ – Python-Paket

Datenfluss eines Laufs:

```
config.load_config ─▶ io.load_all_sources ─▶ joins.build_mart_match ─▶ metrics.add_match_kpis
   (Datenmodus-        (Schema, Fixture-        (dim_match, Aggregation      (Spiel-KPIs, Saison
    Sperre)             Marker, Missing=NaN)     vor Join, Unmatched,         gewichtet, KPI-Checks)
                                                 Summenerhalt)
        ─▶ pipeline.run_pipeline (CSV-Artefakte + manifest.json in outputs/<run_id>/)
        ─▶ export.export_excel ─▶ export.readback_excel (Vergleich Excel ↔ Datenkern)
```

| Modul | Aufgabe |
|---|---|
| `__init__.py` | Version, Fixture-Marker und Banner |
| `config.py` | YAML-Konfiguration, Datenmodus-Sperre |
| `fixtures.py` | deterministische künstliche Mini-Fixture |
| `io.py` | Inputverträge (`SOURCE_SCHEMAS`), Laden, Inventar ohne Inhalte |
| `joins.py` | Spielkalender, Aggregation, 1:1-Join, Prüfprotokoll |
| `metrics.py` | KPI-Definitionen und -Berechnung |
| `pipeline.py` | Lauf-ID, Artefakte, Manifest, Abdeckung |
| `export.py` | Excel ohne Formeln, Banner je Blatt, Readback |
| `inventory.py` | Strukturinventar echter Rohdateien (Modus `structure_only`): Tabs, Kopfzeile, Spalten, Typen, Missing, Datumsbereich, Personenbezug-Kandidaten – **keine Zellinhalte** |
| `cli.py` | `inventory`, `inventory-raw`, `prepare-data`, `analyze`, `run`, `export`, `readback`, `make-fixture` |
| `prepare.py` | Bereinigung/Aggregation echter Daten nach `data/clean/<run_id>/` (D-001 c), Frauen-Ausschluss (D-016), Schulferien-Recherche (D-017 b) |
| `baseline.py` | Echte Daten: Spieltabelle aus `data/clean` (1:1-Join, Summenerhalt, Unmatched), KPIs, Saisonwerte, Abdeckung, Reto-/Quellabgleich |
| `hypotheses.py` | H1–H3, K1: einheitliches Ergebnisformat, saison-zentriert, Bootstrap-KI; Liste weiterer Hypothesen |
| `analysis.py` | Analyse-Lauf (`analyze`): Artefakte + Manifest in `<output_dir>/<run_id>/` |
| `report.py` | Bericht `docs/analysis/01_baseline_erste_erkenntnisse.md` + PNG-Grafiken aus den Laufartefakten |

Echtdaten-Fluss: `prepare.run_prepare` → `data/clean/LATEST` → `analysis.run_analysis` (baseline + hypotheses) →
`report.write_report` + `export.export_excel` → `export.readback_excel`.

Noch nicht vorhanden (bewusst): Kontextmodelle, Diagnosekarte, Deckungsbeitrag (keine Kostendaten). Modelle erst
nach Baseline-Freigabe.

# Changelog

## 0.4.1 – 11.10.2026
- Vorbereitung erster Push ins private Team-Repo: README für die interne Abstimmung neu geschrieben; Ergebnisordner
  `outputs/run1_simon_2026-10-11/` (Analyse-Artefakte, Bericht-Schnappschuss, Prüfprotokolle der Bereinigung, README);
  `config/project.local.example.yaml`; Notebook mit Repo-Modus (läuft ohne Rohdaten auf `mart_match.csv` von Run 1).
- Freigaben: D-011 (Briefing ins private Repo), D-024 ergänzt (geteilte Laufordner).

## 0.4.0 – 11.10.2026
- **Erste Baseline-Analyse auf echten Daten** (`python -m fcsg.cli analyze`, Task «FCSG: Baseline-Analyse»):
  Spieltabelle (108 Herren-Pflichtspiele 21/22–26/27, 1:1-Join, Summenerhalt), KPIs je Spiel/Saison, Abgleich mit
  Retos Sichtung und Quell-Tab «Entwicklung», Excel mit 16 Blättern + Readback (ausserhalb des Repos).
- **Hypothesen** H1 (Ticketing × Catering), H2 (Zutritt × Catering), H3 (Ticketing × Zutritt), K1 (Spielkontext)
  mit Bootstrap-KI; Bericht `docs/analysis/01_baseline_erste_erkenntnisse.md` mit 5 Grafiken; Übergabe-Doku
  `docs/analysis/README.md`; Notebook `notebooks/01_baseline_hypothesen.ipynb`.
- Neue Module `baseline.py`, `hypotheses.py`, `analysis.py`, `report.py`; Export für Datenmodus `release_aggregates`.
- Entscheide D-024 (echte aggregierte Zahlen ins private Repo), D-025 (Arbeitsdefinitionen).
- Abhängigkeiten: matplotlib, ipykernel, nbconvert (nur `.venv`); `requirements.lock.txt` nach Test neu fixiert.
  83 Tests bestanden.

## 0.3.0 – 11.10.2026
- Entscheide der Projektverantwortlichen umgesetzt (`docs/decisions.md`): D-002, D-003 (Steuerungsgrösse **Deckungsbeitrag**),
  D-007–D-009, D-011, D-013, D-016 (Frauen-Daten raus), D-017, D-018, D-019, D-022; neu D-021 (Schulferien), D-023 (Datenraum, offen).
- `fcsg.prepare`: Frauen-Dateien werden nicht gelesen, `drop_women` entfernt Frauen-Events; `apply_school_holidays` ersetzt
  Schulferien vor 26/27 durch recherchierte Werte (`config/reference/school_holidays_stadt_sg.csv`, mit Quellen).
- CLAUDE.md/AGENTS.md/Briefing-Synthese: Steuerungsgrösse DB nachgeführt. 5 neue Tests (66 gesamt).

## 0.2.0 – 10.10.2026
- Strukturinventar echter Rohdaten (`fcsg.cli inventory-raw`, Modus `structure_only`, keine Zellinhalte; Tests mit Sentinel-Werten).
- Bereinigung/Aggregation echter Daten (`fcsg.cli prepare-data`, Modus `release_aggregates`) nach `data/clean/<run_id>/`:
  18 Tabellen, Personenfelder nie gelesen/exportiert, Summenerhalt- und Datenschutzprüfungen.
- Dokumentation: `docs/data_inventory.md` (Abdeckung, Befunde, Klärungsfragen), `docs/data_dictionary_clean.md`, Entscheidungen D-001 (entschieden), D-014–D-020.
- `python-calamine` ergänzt; 61 Tests bestanden.

## 0.1.0 – 10.10.2026
- Projekt lokal aufgesetzt: `.venv` (Python 3.12.10), Paket `fcsg`, VS-Code-Tasks/-Empfehlungen, `.gitignore`.
- Quell-PDFs nach `docs/sources/` verschoben; Briefing-Arbeitsfassungen v1 mit Seitenverweisen in `docs/briefing/`.
- `AGENTS.md` aus `CLAUDE.md`/`PROJECT_SETUP.md` synchronisiert.
- Künstliche Fixture `synthetic_mini` und technischer Vertikalschnitt: Laden mit Schemaprüfung → `mart_match`
  (1:1-Join, Unmatched-Report, Summenerhalt) → Spiel-/Saison-KPIs → Excel-Export → Readback.
- 25 pytest-Tests bestanden; getestete Versionen in `requirements.lock.txt`.
- Keine echten Daten gelesen; Datenmodus-Sperre (`synthetic_fixture`) aktiv.

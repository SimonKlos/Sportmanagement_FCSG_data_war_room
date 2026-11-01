# Changelog

## Stadionname – 02.11.2026
- D-044: «kybunpark» durch «Berit Sitterstadion» ersetzt in Deliverables (HTML-Bericht, Excel-Blatt 20_Chancenfelder, Folienleitfaden), in den Generatoren `delivery/build_report.py` und in den Textbausteinen des Rechenkerns (`config.py` Kommentar, `report/methodennotiz.py`, `ideen/chancen.py`, `ideen/bericht/html.py`), damit künftige Läufe die alte Bezeichnung nicht wieder erzeugen.
- Excel per Text-Ersatz direkt in der Datei (Formate, Formeln und übrige Zellen unverändert); `data_inventory.md`: offene Frage zur Umbenennung als geklärt markiert.
- Historische Run-Artefakte unverändert. Nur Bezeichnung; keine Rechen-, Daten- oder Modelländerung.

## Rechenkern und Notebooks einsortiert – 01.11.2026
- Root `ralf/` nach `Baseline Analyse Rechnungen/Rechenkern/` verschoben: aktiver kanonischer Code, Tests, Referenzdaten und Korrekturen vollständig erhalten. Keine fachliche Logik geändert; Standardpfade trotz zusätzlicher Ordnerebene stabilisiert.
- Root `notebooks/` nach `Baseline Analyse Rechnungen/Notebooks_Archiv/` verschoben; Repository-Erkennung für den tieferen Startordner angepasst. Keine Notebook-Ausgaben erzeugt oder archivierte Ergebnisse verändert.
- Navigation, aktive Pfadverweise, Ignore-Ausnahmen und Startanleitung angepasst. Keine Dateien gelöscht, keine neuen externen Dokumente erzeugt; bestehende Deliverables unverändert. D-043.


## Struktur und externe Aufbereitung – 01.11.2026
- Simon bestätigt drei Hauptbereiche: `Baseline Analyse Rechnungen` (bisher outputs), `Quellen und interne Dokumentation` (bisher docs), separater Root `Deliverables`. Quellen-/Entscheidungsdokumente bleiben intern; Code/Paketstruktur bleibt unverändert.
- Historische Laufartefakte nur verschoben; Inhalt und Rechenlogik bleiben identisch. Aktive Pfade, Markdown-Links, Fixture-Konfiguration, CLI-Berichtsziel und Archiv-Notebook auf die neuen Ordnernamen angepasst.
- Externe Dokumentation: gemeinsamer Bericht, Excel, neutrale Diagramme, Methodik; Präsentationsausgabe ausdrücklich nur ausführliches Folienkonzept als Inspiration für Simons eigenen PPT-Teamaufschlag, keine PPT/PPTX.
- Alle extern ausgerichteten Dateien bleiben Review-Fassungen; keine automatische fachliche Freigabe, kein öffentlicher Upload, kein Baseline-/Sensitivitätsneulauf. D-042.


## Dokumentationsnachtrag – 01.11.2026
- Partnerantworten zum Catering quellengetrennt dokumentiert: Kundenfranken exkl. MwSt., Umsatzbeteiligung/Warenkosten, steuerliche 80/20-Aufteilung und Bons-Erfassungsbruch.
- D-038 bis D-041 und Nachträge D-003/D-004/D-005/D-019/D-029: Phase-2-Massnahmen auf Umsatz (Simon); 20 % Cateringbeteiligung ausschliesslich unbestätigte Szenarioannahme.
- Teamnotiz `Quellen und interne Dokumentation/team/2026-11-01_catering_klaerung_und_baseline_folgen.md`: verbleibende Rückfragen, Codeprüfung und begrenzte Bons-Sensitivität statt pauschalem Neuimport.
- README und beide Agentenregeln synchronisiert. Nur Dokumentation; keine Code-/Datenänderung, keine Neuberechnung, keine Freigabe historischer Modelle.


## 0.5.2 – 14.10.2026
- D-037: `Baseline Analyse Rechnungen/Notebooks_Archiv/01_baseline_hypothesen.ipynb` als **Auslaufmodell** gekennzeichnet (Hinweis im Notebook und in
  `Baseline Analyse Rechnungen/Notebooks_Archiv/README.md`); Idee einer Phase-2-Analyse-Werkbank auf Ralfs Rechenkern festgehalten (Bau nach dem
  Chancenfeld-Workshop).

## 0.5.1 – 14.10.2026
- **D-036 entschieden, D-016 ergänzt (Simon):** Frauen-Spiele **und Länderspiele** (Nationalteams, WEURO 2025,
  Nati-Trainings, Public Viewings) werden überall ignoriert.
  - Ralfs Ideen-Grundlage angepasst (`Baseline Analyse Rechnungen/Rechenkern/fcsg/ideen/`: Randfelder ohne Frauen/Länderspiele, Blatt F2 entfällt,
    Chancenfeld 9 neu «Das Stadion an weiteren Anlässen») und in Run 3 neu gerechnet (`ralf_ideen_grundlage/`, QA 18/18).
  - Simons Bereinigung: neuer Filter `drop_national_team` (Prüfungen `D016N-*`, Herren-Pflichtspiele geschützt) + Test;
    entfernt 22 Historie-, 16 Catering-, 9 Saisonsummen- und 189 Kiesplatz-Zeilen. Analyse-Ergebnisse unverändert.
  - Run 3 aktualisiert (Gegenrechnung mit bereinigtem Lauf `20261014T215420_clean_0cf1`); Phase 1 von Ralf identisch.

## 0.5.0 – 14.10.2026
- **Ralfs Rechenkern übernommen (D-028 entschieden, Simon):** Code v1.1.0 unter `Baseline Analyse Rechnungen/Rechenkern/` (inkl. Tests, Korrekturen,
  öffentliche Zusatzdaten), Einbindung beschrieben in `Baseline Analyse Rechnungen/Rechenkern/README_REPO.md`. Einzige Codeänderung am Kern: Einlesen der
  Spielkontext-Tabelle Version 5 (`Baseline Analyse Rechnungen/Rechenkern/fcsg/sources/kontext.py`, Standarddatei in `config.py`) + 2 Tests.
- **Spielkontext-Tabelle Version 5 (D-034 entschieden):** einzige gültige Version, kein Rückfall auf ältere Versionen.
  Simons `prepare_context` auf v5 umgestellt (neue Spalten: Gegner-Kategorie, Punkteschnitt, Wetter zur Anstossstunde
  `temp_c`/`precip_mm`/`wind_kmh`, Covid, Saison 21/22); Schulferien-Recherche nur noch Gegenprobe (96 Spiele, 0 Abweichungen);
  nicht mehr benötigte Parser für v3 entfernt. Befund: Run 1 und Ralf v1.1.0 nutzten dieselbe Vorgängerversion 3.
- **Run 2** (`Baseline Analyse Rechnungen/run2_ralf_2026-10-13/`): Ralfs Ergebnisse vom 13.10. unverändert (Phase 1 + Ideen-Grundlage).
- **Run 3** (`Baseline Analyse Rechnungen/run3_kontext-v5_2026-10-14/`): Neuberechnung mit v5 – Ralfs Kern (Zahlenbasis; Importtests 19/19,
  Testsuite mit echten Daten 50/50) und Simons Pipeline als Gegenrechnung; Ergebnis: v5 ändert Ralfs Modelle und KPIs nicht,
  beide Pipelines liefern identische Kernzahlen.
- Neues Modul `fcsg.abgleich` (Spieltabellen Simon vs. Ralf je Spiel) + Test.
- **Korrektur:** WARN Q01 «Catering 23/24: ein Spiel fehlt» war ein Datumsparser-Fehler in Simons Pipeline (27.09.2023),
  keine Datenlücke der Quelle.
- Entscheide: D-028, D-034 entschieden; Nachträge D-017, D-021, D-030, D-031, D-035; neu D-036 (Frauen-Daten in Ralfs
  Ideen-Grundlage, offen); W-05 präzisiert.
- `Quellen und interne Dokumentation/team/2026-10-14_vorschlag_naechste_schritte.md`: Vorschläge Phase 1 → Phase 2 (zur Diskussion).
- Abhängigkeiten: statsmodels, scipy, xlsxwriter (für Ralfs Kern) in `.venv`; `requirements.lock.txt` neu fixiert.

## 0.4.3 – 14.10.2026
- Neuer Ordner `Quellen und interne Dokumentation/team/` für die Team-Abstimmung:
  - `2026-10-14_abgleich_ralf_und_entscheide.md`: Abgleich Simon Run 1 vs. Ralf v1.1.0 (Übereinstimmungen,
    Abweichungen mit Grund, von Ralf geklärte Punkte), offene Entscheide E-1 bis E-8 mit Vorschlag,
    Integrationsplan (technisch, Phase 1, Phase 2), Begründbarkeit und Zeitplan bis 25.11.
  - `2026-10-14_fragen_sandro_v2.md`: überarbeitete Fragen an Sandro für den Termin vom 16.10. (Folie 8 + Backup).
- `Quellen und interne Dokumentation/decisions.md`: D-028 bis D-035 als **offene** Entscheide erfasst (Vorschläge, noch nicht entschieden).
- Nur Dokumentation; kein Code, keine Daten, keine Ergebnisse geändert. Ralfs Paket ist nicht im Repo.

## 0.4.2 – 13.10.2026
- Neue Arbeitsregel D-027: Jede fachliche oder methodische Festlegung wird in `Quellen und interne Dokumentation/decisions.md` erfasst (Datum,
  wer entschieden hat, Quelle; Agent-Annahmen offen bis Teambestätigung); grössere Änderungen erhalten einen
  Eintrag in diesem Changelog. Verankert in `CLAUDE.md`, `AGENTS.md` (Stand 13.10.2026) und README §7.
- D-026 nachgetragen: Hypothesen H1–H3 und K1 aus Run 1 als offene Agent-Annahme erfasst, Bestätigung durch das
  Team ausstehend.
- Nur Dokumentation; kein Code, keine Daten, keine Ergebnisse geändert.

## 0.4.1 – 11.10.2026
- Vorbereitung erster Push ins private Team-Repo: README für die interne Abstimmung neu geschrieben; Ergebnisordner
  `Baseline Analyse Rechnungen/run1_simon_2026-10-11/` (Analyse-Artefakte, Bericht-Schnappschuss, Prüfprotokolle der Bereinigung, README);
  `config/project.local.example.yaml`; Notebook mit Repo-Modus (läuft ohne Rohdaten auf `mart_match.csv` von Run 1).
- Freigaben: D-011 (Briefing ins private Repo), D-024 ergänzt (geteilte Laufordner).

## 0.4.0 – 11.10.2026
- **Erste Baseline-Analyse auf echten Daten** (`python -m fcsg.cli analyze`, Task «FCSG: Baseline-Analyse»):
  Spieltabelle (108 Herren-Pflichtspiele 21/22–26/27, 1:1-Join, Summenerhalt), KPIs je Spiel/Saison, Abgleich mit
  Retos Sichtung und Quell-Tab «Entwicklung», Excel mit 16 Blättern + Readback (ausserhalb des Repos).
- **Hypothesen** H1 (Ticketing × Catering), H2 (Zutritt × Catering), H3 (Ticketing × Zutritt), K1 (Spielkontext)
  mit Bootstrap-KI; Bericht `Quellen und interne Dokumentation/analysis/01_baseline_erste_erkenntnisse.md` mit 5 Grafiken; Übergabe-Doku
  `Quellen und interne Dokumentation/analysis/README.md`; Notebook `Baseline Analyse Rechnungen/Notebooks_Archiv/01_baseline_hypothesen.ipynb`.
- Neue Module `baseline.py`, `hypotheses.py`, `analysis.py`, `report.py`; Export für Datenmodus `release_aggregates`.
- Entscheide D-024 (echte aggregierte Zahlen ins private Repo), D-025 (Arbeitsdefinitionen).
- Abhängigkeiten: matplotlib, ipykernel, nbconvert (nur `.venv`); `requirements.lock.txt` nach Test neu fixiert.
  83 Tests bestanden.

## 0.3.0 – 11.10.2026
- Entscheide der Projektverantwortlichen umgesetzt (`Quellen und interne Dokumentation/decisions.md`): D-002, D-003 (Steuerungsgrösse **Deckungsbeitrag**),
  D-007–D-009, D-011, D-013, D-016 (Frauen-Daten raus), D-017, D-018, D-019, D-022; neu D-021 (Schulferien), D-023 (Datenraum, offen).
- `fcsg.prepare`: Frauen-Dateien werden nicht gelesen, `drop_women` entfernt Frauen-Events; `apply_school_holidays` ersetzt
  Schulferien vor 26/27 durch recherchierte Werte (`config/reference/school_holidays_stadt_sg.csv`, mit Quellen).
- CLAUDE.md/AGENTS.md/Briefing-Synthese: Steuerungsgrösse DB nachgeführt. 5 neue Tests (66 gesamt).

## 0.2.0 – 10.10.2026
- Strukturinventar echter Rohdaten (`fcsg.cli inventory-raw`, Modus `structure_only`, keine Zellinhalte; Tests mit Sentinel-Werten).
- Bereinigung/Aggregation echter Daten (`fcsg.cli prepare-data`, Modus `release_aggregates`) nach `data/clean/<run_id>/`:
  18 Tabellen, Personenfelder nie gelesen/exportiert, Summenerhalt- und Datenschutzprüfungen.
- Dokumentation: `Quellen und interne Dokumentation/data_inventory.md` (Abdeckung, Befunde, Klärungsfragen), `Quellen und interne Dokumentation/data_dictionary_clean.md`, Entscheidungen D-001 (entschieden), D-014–D-020.
- `python-calamine` ergänzt; 61 Tests bestanden.

## 0.1.0 – 10.10.2026
- Projekt lokal aufgesetzt: `.venv` (Python 3.12.10), Paket `fcsg`, VS-Code-Tasks/-Empfehlungen, `.gitignore`.
- Quell-PDFs nach `Quellen und interne Dokumentation/sources/` verschoben; Briefing-Arbeitsfassungen v1 mit Seitenverweisen in `Quellen und interne Dokumentation/briefing/`.
- `AGENTS.md` aus `CLAUDE.md`/`PROJECT_SETUP.md` synchronisiert.
- Künstliche Fixture `synthetic_mini` und technischer Vertikalschnitt: Laden mit Schemaprüfung → `mart_match`
  (1:1-Join, Unmatched-Report, Summenerhalt) → Spiel-/Saison-KPIs → Excel-Export → Readback.
- 25 pytest-Tests bestanden; getestete Versionen in `requirements.lock.txt`.
- Keine echten Daten gelesen; Datenmodus-Sperre (`synthetic_fixture`) aktiv.

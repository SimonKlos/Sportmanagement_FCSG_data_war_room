# AGENTS.md – Regeln für Coding-Agenten (Codex, Claude Code u. a.)

Diese Datei synchronisiert die verbindlichen Regeln aus `CLAUDE.md` und `PROJECT_SETUP.md` für alle
Agenten. Bei Widerspruch gilt: ausdrückliche Anweisung der Projektverantwortlichen > `CLAUDE.md` >
diese Datei. Änderungen an Regeln immer in **beiden** Dateien nachführen. Stand: 14.10.2026.

## Auftrag
- Projekt: FC St.Gallen 1879, «Untapped Business», Phase 1 (HSG, Sportmanagement in der Praxis HS26).
- Fachliche Quellen: PDFs in `Quellen und interne Dokumentation/sources/` (nicht committen). Arbeitsfassungen mit Seitenverweisen in
  `Quellen und interne Dokumentation/briefing/`. Vor fachlichen Änderungen lesen: `Quellen und interne Dokumentation/briefing/01_arbeitsauftrag_modellierung.md`
  und `Quellen und interne Dokumentation/briefing/10_synthese_widersprueche.md`. Bei Widerspruch gilt das PDF.
- Massgeblich ist der **Arbeitsauftrag vom 08.10.2026**. Fehlt eine Quelle: Blocker benennen, nichts vermuten.
- Projektverantwortliche schreiben keinen Code. Erklärungen auf **Deutsch**, technische Namen **Englisch**.

## Grenzen (ohne ausdrückliche Zustimmung verboten)
- Datenupload, Git-Push, Remote-Repo, Codespaces/Actions, externe Freigaben, Systeminstallationen, Lizenzentscheid.
- Berechtigungen umgehen.
- **Echte Daten/Rohzeilen lesen oder in Toolausgaben zeigen**, solange kein Datenmodus freigegeben ist
  (`Quellen und interne Dokumentation/decisions.md`, D-001). Lokaler Agent ≠ offline: Gelesenes geht an ein externes Modell.
  Der Projektantrag verlangt Arbeit ausschliesslich im Datenraum (PA S. 2).
- `.gitignore` ist keine Zugriffssperre. Keine Tokens/Geheimnisse in Dateien, Logs oder Notebooks.
- Analyse-Läufe (`fcsg.cli run`) akzeptieren nur `data_mode: synthetic_fixture`; echte Daten nur über `prepare-data` (D-001 c).
- Echte Rohdaten liegen unter `C:\FCSG_Daten\raw` (D-015). Freigegeben (D-001): Strukturinventar und
  **Datenmodus für nicht personenbezogene Daten** (`release_aggregates`). Analysen arbeiten mit `data/clean/<LATEST>/`
  (bereinigt/aggregiert, `Quellen und interne Dokumentation/data_dictionary_clean.md`). Personenbezogene Rohdateien (Einzeltickets, Ticket-CSVs,
  Abos, Zutritte) nie zeilenweise anzeigen; Personen-/ID-Spalten nie laden ausser intern zum Zählen in `fcsg.prepare`.

## Methodik (fachliche Leitplanken)
- Steuerungsgrösse Phase 1 = **Deckungsbeitrag** (D-003, Abweichung vom AA bewusst entschieden). Umsatz brutto/netto
  bleibt Grundlage/Zwischengrösse; DB nur mit belegten Kosten-/Margendaten, keine Margen annehmen.
  Massnahmenquantifizierung (Phase 2) zurückgestellt. Frauen-Daten ausserhalb Scope (D-016).
- Kein Dynamic Pricing, keine Hospitality, keine Kapazitätserweiterung. Keine Personensegmentierung.
- Eine Zeile pro Heimspiel (`mart_match`). Faktentabellen **vor** dem Join aggregieren; Summenerhalt und
  Join-Kardinalität prüfen; Unmatched-/Duplikatreport ist Pflicht.
- SOLL/IST/Public-Netto und Brutto/Netto erst definieren; bis dahin getrennt führen und als Entwurf markieren.
- Missing ≠ 0. Fehlender Scan ≠ automatisch No-Show. Abo-Snapshot und Saisonartikel separat.
- Keine erfundenen Merch-, Sektor-Konsum- oder Zeit-Konsumdaten.
- Keine Kausalität aus Korrelation; Residuen ≠ realisierbares Potenzial.
  Diagnoselücke = erwartet − beobachtet (AA S. 8). Lücken aus KF, Bonsrate, Ø Bon **nie addieren**.
- Saisonquoten gewichtet (Σ/Σ), nicht als Mittel der Spielquoten.
- Modellierung erst nach Baseline-Freigabe.

## Rechenkern-Migration – 01.11.2026 (D-043)
Der kanonische Code liegt jetzt in `Baseline Analyse Rechnungen/Rechenkern` (bisher Root `ralf`), historische Notebooks in `Baseline Analyse Rechnungen/Notebooks_Archiv` (bisher Root `notebooks`). Den kanonischen Kern aus seinem eigenen Ordner starten, um die beiden Pakete namens `fcsg` nicht zu verwechseln. Frühere Angaben zur Beibehaltung dieser Root-Ordner sind überholt. Keine Dateien/Archivresultate löschen; keine fachliche Rechenlogik ändern.

## Ausgabe- und Strukturregel – 01.11.2026 (D-042)
Quellen/Logs intern in `Quellen und interne Dokumentation`, Rechenstände in `Baseline Analyse Rechnungen`, externe Review-Unterlagen im separaten Root `Deliverables`. Historische Artefakte unverändert erhalten. Externe Fassungen ohne interne Personenvergleiche; Zahlen und Logik unverändert. Präsentation ausschliesslich als ausführlicher Folienleitfaden zur eigenen PPT-Erstellung durch Simon, **keine PPT/PPTX**.

## Aktueller Nachtrag – 01.11.2026
Phase-2-Massnahmen primär auf inkrementellen Umsatz prüfen (Simon, D-039), nicht DB. Catering-Systemumsatz exkl. MwSt. und Cluberlös trennen. 20 % Cateringbeteiligung nur unbestätigte Szenarioannahme (D-040), kein Default/Margennachweis; Vertragsbasis offen. Phase-1-Entscheid D-003 bleibt historisch bestehen. Kundenfranken-Definition bestätigt, Nenner-Mapping offen (D-038). Bons 2023/24 wegen System-/Gutscheinwechsel eingeschränkt vergleichbar: D-041 und Teamnotiz vor Verwendung lesen; kein bereits erfolgter Sensitivitätslauf.

## Code und Dokumentation
- **Zahlenbasis = Ralfs Rechenkern unter `Baseline Analyse Rechnungen/Rechenkern/`** (D-028; immer aus `Baseline Analyse Rechnungen/Rechenkern/` starten, siehe `Baseline Analyse Rechnungen/Rechenkern/README_REPO.md`).
  `src/fcsg/` bleibt für Bereinigung, Datenschutzprüfung, Tests und Gegenrechnung (`fcsg.abgleich`).
  Spielkontext-Tabelle nur **Version 5** (D-034).
- Python-Paket `src/fcsg/` (modular, Docstrings für zentrale Funktionen), CLI `python -m fcsg.cli`,
  Tests `tests/` (pytest), VS-Code-Tasks `.vscode/tasks.json`. Kurze erklärende Notebooks folgen bei Bedarf.
- README pro Hauptordner; `Quellen und interne Dokumentation/data_dictionary.md` und `Quellen und interne Dokumentation/decisions.md` nachführen.
- **Jede fachliche oder methodische Festlegung** (Definition, Hypothese, Abgrenzung, Annahme) als D-Eintrag in
  `Quellen und interne Dokumentation/decisions.md`: Datum, wer entschieden hat (Team oder Agent-Annahme), Quelle. Agent-Annahmen bleiben
  «offen» bzw. «Arbeitsannahme», bis das Team sie bestätigt (D-027).
- **Jede grössere Änderung** (neue Analyse, neuer Lauf, geänderte Definition, neue Abhängigkeit, geänderte Regel)
  erhält einen Eintrag in `CHANGELOG.md`.
- Fehlermeldungen/Logs ohne Zellinhalte (nur Spaltennamen und Anzahlen).
- Abhängigkeiten erst nach erfolgreichem Testlauf in `requirements.lock.txt` fixieren.

## Umsetzung und Lieferung
- Kleine End-to-End-Pakete. Künstliche Fixtures klar markiert (`data_origin = SYNTHETIC_FIXTURE_NOT_CLUB_DATA`,
  Daten in 2099+). Testdaten nie als Clubdaten berichten. Stubs/TODO-Gerüste nicht als fertig deklarieren.
- Jeden Schritt ausführen und prüfen. Excel immer exportieren **und zurücklesen** (`fcsg.cli export` macht beides).
- Bericht nennt: geänderte Dateien, Zweck, tatsächlich ausgeführte Befehle/Tests, tatsächliche Outputs,
  offene Einschränkungen, fachliche Prüfhandlungen, Lauf-ID/Versionen, Datenabdeckung.
- Notebook-Ausgaben vor Versionskontrolle leeren; keine Daten oder lokalen Pfade committen.

## Freigaben
Lesen/Schreiben/Tests im Codebereich: delegiert. Datenzugriff, fachliche Scope-Änderung, externe Seiteneffekte:
jeweils separate Freigabe. Umfangreiche Änderungen erst kurz begründen.

## Schnellstart für Agenten
```
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m fcsg.cli run --config config/project.example.yaml
```

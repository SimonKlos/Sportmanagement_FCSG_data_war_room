# FCSG Analyseprojekt – VS Code + Claude Code

## Status und Ziel
Dieser Plan ersetzt den Colab-Ansatz. Phase 1 wird lokal in VS Code mit der offiziellen Claude-Code-Erweiterung entwickelt. Die Projektverantwortlichen schreiben keinen Code: Sie formulieren Aufgaben, bestätigen Zugriffe und verproben Outputs. Der Agent erstellt Dateien, Umgebung, Tests, Skripte und erklärende Notebooks. GitHub-Übergabe folgt als eigener Schritt, nicht als automatischer Upload.

Noch nicht eingerichtet: die lokale Umgebung, echter Datenimport, Repository oder Cloud-Ausführung. Dieses Startpaket enthält Plan, Regeln und Prompts, keine bereits validierte Analysepipeline.

## Verbindliche Quellen
- **Modellierungsauftrag als PDF:** aus dem gemeinsamen SharePoint herunterladen.
- **Datenquellen & Treiberbaum als PDF:** aus dem gemeinsamen SharePoint herunterladen.
- Beide freigegebenen Dokumente lokal unter `Quellen und interne Dokumentation/sources/` ablegen; sie sind diesem Paket nicht beigefügt. Die Originaldateinamen beibehalten und in `Quellen und interne Dokumentation/sources/README.md` dokumentieren. Keine SharePoint-Adresse oder Dateinamen erraten.
- Der Agent liest beide PDFs vor der fachlichen Umsetzung und erstellt daraus versionierte Arbeitsfassungen unter `Quellen und interne Dokumentation/briefing/`, inklusive Quelldatei, Dokumentstand und Seitenverweisen. Die PDFs bleiben fachlich massgeblich; bei neuen Fassungen Arbeitsbriefing und Entscheidungen aktualisieren.
- Retos Angaben zu Dateien und Vollständigkeit erst beim Import bestätigen. Keine KPI- oder Modellbefunde ohne echten Datenlauf.

## 1. Einmalige Einrichtung
1. VS Code installieren/öffnen. Offizielle Erweiterung **Claude Code von Anthropic** installieren und anmelden; passende Claude-Code-Nutzungsberechtigung erforderlich. Kein pauschales Bypass-permissions aktivieren.
2. Einen leeren lokalen Ordner `fcsg-analysis` öffnen. Dieses Startpaket entpacken bzw. die Markdown-Dateien dort ablegen. Die beiden freigegebenen Briefing-PDFs aus SharePoint herunterladen und unter `Quellen und interne Dokumentation/sources/` ablegen. Noch keine Rohdaten hineinlegen.
3. Claude Code mit Prompt 1 starten. Der Agent prüft OS, Python und Git, legt die Projektumgebung an und erklärt fehlende Installationen. Er darf projektspezifische Dateien bearbeiten und Tests ausführen; systemweite Änderungen und externe Aktionen brauchen Zustimmung.
4. Datenzugriff und Weitergabe separat klären. Erst danach mit Prompt 2 ff. fortfahren.

**Nicht erforderlich:** Notebook selbst erstellen, Python tippen oder Ordner manuell ausarbeiten. Gegebenenfalls sind Installation/Login, Berechtigungen und die Wahl eines freigegebenen Datenpfads nötig.

## 2. Rollen und Delegation
- **Projektverantwortliche:** fachlicher Auftrag, Definitionen, Zugriff-/Cloudfreigaben, Quellenstichproben und Freigabe der Ergebnisse.
- **Lokaler Claude-Code-Agent:** Dateien erstellen, Umgebung konfigurieren, Skripte/Notebooks/Tests schreiben, zulässige Ausführung und verständliche Laufreports liefern.

Die Projektverantwortlichen geben die bereitgestellten Prompts an den lokalen Agenten, prüfen dessen Laufberichte und geben die nächsten Arbeitspakete frei. Ein zusätzlicher Orchestrierungsagent ist nicht erforderlich.

## 3. Datenschutz: lokale Ausführung ist nicht Offline-KI
Python rechnet lokal. Claude Code nutzt aber ein externes Modell: gelesene Daten, Toolausgaben und Fehlermeldungen können in den Modellkontext gelangen. NDA-/Datenraumvorgaben gelten weiterhin. Private Git-Repos sind keine Freigabe zum externen Verarbeiten von Clubdaten.

**Zwei Betriebsmodi:**
- Code-only: Agent erhält Briefing, freigegebene Schemas und künstliche Testdaten; echte Daten bleiben geschützt. Eine lokale Pipeline wird ausserhalb des Agentenzugriffs ausgeführt. Der Agent bekommt nur geprüfte, zulässige Berichte. Bei automatischem Zugriff auf echte Daten ist die Trennung nicht mehr garantiert.
- Freigegebener Datenmodus: Agent darf klar definierte bereinigte/aggregierte Daten und Outputs verarbeiten, sofern diese Übermittlung/Verarbeitung ausdrücklich zulässig ist.

`gitignore` verhindert weder Dateilesen noch Modellübermittlung. Datenpfad ausserhalb des Repos ist Organisation, keine Sicherheitsbarriere. Wo strikte Trennung nötig ist, OS-/Containerberechtigungen oder eine freigegebene interne/lokale KI nutzen. Der Wunsch nach vollständiger Autonomie darf diese Grenze nicht aufheben.

Keine Rohzeilen standardmässig loggen. Auch Seat/Scanzeit/IDs und Kombinationen prüfen; Pseudonymisierung ist keine vollständige Anonymisierung. Excel-Metadaten, versteckte Tabs, Kommentare, externe Links mitbedenken. Keine Geheimnisse in Prompts, Git oder Notebooks.

## 4. Zielarchitektur
```text
fcsg-analysis/
  README.md
  CLAUDE.md
  AGENTS.md
  CHANGELOG.md
  pyproject.toml
  requirements.lock.txt
  .gitignore
  .vscode/extensions.json
  .vscode/tasks.json
  config/
    README.md
    project.example.yaml
    sources.example.yaml
    column_mapping.example.yaml
    metric_definitions.yaml
    model_specs.yaml
  Quellen und interne Dokumentation/
    README.md
    sources/README.md
    briefing/README.md
    data_inventory.md
    data_dictionary.md
    data_flow.md
    methods_and_limits.md
    decisions.md
    validation_and_signoff.md
    troubleshooting.md
    fcsg_handover.md
  prompts/README.md
  notebooks/
    README.md
    00_quality_and_inventory.ipynb
    01_baseline.ipynb
    02_attendance_and_sales.ipynb
    03_catering.ipynb
    04_arrival.ipynb
    05_context_models.ipynb
    06_diagnostics.ipynb
  src/fcsg/
    README.md
    __init__.py
    inventory.py
    io.py
    normalize.py
    joins.py
    metrics.py
    analysis.py
    models.py
    diagnostics.py
    export.py
    cli.py
  tests/
    README.md
    fixtures/README.md
    test_imports.py
    test_joins.py
    test_metrics.py
    test_models.py
    test_exports.py
  Baseline Analyse Rechnungen/README.md
```
Kein leeres Vollgerüst als Erfolgsnachweis: zuerst kleiner funktionsfähiger Vertikalschnitt. Weitere Module entstehen nach Bedarf. Rohdatenpfad wird lokal konfiguriert, nicht eingecheckt; Outputs standardmässig ausgeschlossen. `.venv`, Geheimnisse, lokale Config, Excel-Daten und Notebook-Ergebnisausgaben nicht committen.

## 5. Technischer Stack und Bedienung
Python-Version anhand des Systems und kompatibler Pakete wählen und dokumentieren. Virtuelle Umgebung `.venv`, VS-Code-Python-Interpreter und Jupyter-Kernel passend einrichten. pandas, NumPy, openpyxl, PyArrow, XlsxWriter, matplotlib/seaborn, scikit-learn, statsmodels, PyYAML und pytest nach Bedarf. Abhängigkeiten nach getestetem Setup fixieren; keinen ungetesteten Versionsmix behaupten.

Wiederverwendbare Logik in Modulen, Notebooks als verständliche Oberfläche. Ein dokumentierter Kommandozeilen-Einstieg und VS-Code-Tasks erlauben Aufträge wie «Inventar erstellen», «Baseline aktualisieren» und «Excel exportieren». Die folgenden Schnittstellen sind zu implementieren und zu testen, noch keine fertigen Befehle:
```text
python -m fcsg.cli inventory --config <lokale-config>
python -m fcsg.cli run --config <lokale-config>
python -m fcsg.cli export --run-id <freigegebener-lauf>
python -m pytest
```
Keine versteckten Notebook-Zustände. Keine GPU als Startvoraussetzung. Bei Dateiformeln gespeicherte Werte prüfen; Excel-Leser berechnen Formeln nicht automatisch neu.

## 6. Arbeitsplan und fachlicher Scope
1. **Zielbild/Importvertrag:** Briefing lesen; Quellen, Granularität, erwartete Outputs und Datenlücken aufschreiben. Source-Manifest als Datei-/Tab-/Header-/Feldmapping. Tabellen nicht blind konkatenieren.
2. **Inventar/Qualität:** zuerst Namen, Tabs, Schema, Abdeckung und Summenkontrollen. Keine automatischen Annahmen zu unbekannten Pflichtfeldern.
3. **Datenkern:** pro Quelle normalisieren und aggregieren; eindeutiger Match-Key über Datum mit Mehrfach-Event-Prüfung. Erst dann ein Heimspiel pro Zeile verbinden. Summen-/Kardinalitätsprüfungen.
4. **Baseline:** SOLL/IST/Public-Scope, No-Show, KF, Bonsrate und Ø Bon. Brutto/Netto separat. Abo-Snapshot und Artikel-Saisonsummen getrennt, fehlender Scan nicht automatisch No-Show.
5. **Deskriptiv:** Anwesenheit, Einzelticket-Vorlauf, Catering und Ankunft. Kein individueller Konsum, kein Sektor-KF ohne Mapping/Nenner, keine Konsumzeit ohne Bon-Zeitdaten.
6. **Kontextmodelle:** sparsame Modelle gegen einfache Baseline; geeignete zeit-/spielbasierte Validierung, kein Leakage. Trainingstransformationen im Fold lernen. Merchandise nur bei Lieferung. «Nicht belastbar modellierbar» ist zulässig.
7. **Diagnose/Excel:** Erwartung minus Beobachtung, Unsicherheit und Quellenpfad. Keine Residuen als realisierbare Potenziale deklarieren oder KF-/Bons-/Bon-Lücken addieren. Phase-2-Massnahmen bleiben zurückgestellt.

## 7. Dokumentations- und Prüfpflicht
Jeder Hauptordner hat ein README. Jede wichtige Funktion erklärt Zweck, Inputschema/Einheiten, Verarbeitung, Annahmen, Output und Fehler. Kommentare erklären das Warum. Jedes Notebook beginnt mit Frage, Datenbasis, Methode und Grenzen und endet mit Verprobung und offenen Entscheidungen. Deutsche Erklärungen, konsistente englische technische Namen.

Jeder Lauf: Run-ID, Daten-/Code-/Konfigurationsversion, Paketversionen, Coverage, Prüfstatus und Outputmanifest. Jede Lieferung nennt wirklich ausgeführte Tests und getrennt die noch offenen Echtdatenprüfungen. Künstliche Fixtures klar kennzeichnen. Excel exportieren **und zurücklesen**, KPIs und Summen prüfen; Charts visuell verproben.

## 8. Excel-Übergabe
Tabs: Start, Quellen, Definitionen, Abdeckung, Qualität, Spiel-Baseline, Ticket-Vorlauf, Ankunft, Catering-Treiber, Kontext-Ergebnisse, Diagnosekarte, Annahmen. Kennzahlen zentral in Python, kontrollierende Excel-Formeln nur nachvollziehbar ergänzen. Excel ist eine Ergebnisausgabe und kein automatisch neu schätzendes Regressionsmodell. Aktualisierung über neuen Pipeline-Lauf.

## 9. GitHub als zweiter Schritt
**Ja, Code, Dokumentation und freigegebene Analyseartefakte können dem FCSG über ein privates Repo zur Verfügung gestellt werden. Nicht «alles» ungeprüft hochladen.** Eigentümer/Organisation, Zugriffe, Nutzungsrechte und Wartung vereinbaren; keine pauschale Open-Source-Lizenz für Clubprojekt setzen.

- **GitHub Repo:** Dateien/Versionen und Notebook-Anzeige, keine laufende Python-Umgebung. GitHub-Webeditor allein führt Analysen nicht aus.
- **Codespaces:** Cloud-Entwicklungsumgebung mit VS Code/Jupyter. Notebooks und Skripte ausführbar, wenn Umgebung/Abhängigkeiten eingerichtet sind; Ressourcen/Kosten und Cloud-Datenfreigabe prüfen.
- **Actions:** automatisierte oder manuell ausgelöste Jobs, Tests, Notebook-Ausführung und Exporte bei entsprechend eingerichtetem Workflow. Kein interaktives Jupyter-Lab. Gehostete Runner verarbeiten in der Cloud; selbstgehostete Runner laufen auf dem bereitgestellten System, Logs/Artefakte können dennoch bei GitHub landen.

**Empfohlene erste Übergabe:** privates Repo mit bereinigtem Code, READMEs, nicht-sensibler Config, Output-leeren Notebooks, eindeutig künstlichen Testdaten, getesteter Installation und separat freigegebenem Excel. Echte Rohdaten verbleiben in zugelassenem Speicher. CI zunächst nur technische Fixtures; echter Datenlauf lokal beim FCSG.

**Später optional:** Devcontainer/Codespaces-Konfiguration und expliziter Refresh-Workflow. Vorher Datenbeschaffung, Speicher, Zugriffe, Kosten und Aufbewahrung klären. Actions-Artefakte sind kein unbegrenztes Archiv. Sichere Logs, keine Datenläufe aus ungeprüften Pull Requests, minimal erforderliche Workflowberechtigungen.

## 10. Startreihenfolge
Prompt 1 Gerüst und Technik → Prompt 2 Zielbild und Datenverträge → Prompt 3 Inventar → Prompt 4 erster Baseline-Vertikalschnitt → Prompt 5 Analysen/Modelle → Prompt 6 Review und Export → Prompt 7 GitHub-Übergabe vorbereiten.

## Offizielle Referenzen
- Claude-Code-Erweiterung: https://code.claude.com/Quellen und interne Dokumentation/en/vs-code
- Berechtigungen: https://code.claude.com/Quellen und interne Dokumentation/en/permissions
- Codespaces/Jupyter: https://docs.github.com/codespaces/developing-in-a-codespace/getting-started-with-github-codespaces-for-machine-learning

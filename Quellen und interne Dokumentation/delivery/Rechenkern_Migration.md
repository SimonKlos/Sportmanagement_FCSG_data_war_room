# Rechenkern-/Notebook-Migration – 01.11.2026

Freigabe: Simon, D-043. Root `ralf` → `Baseline Analyse Rechnungen/Rechenkern`; Root `notebooks` → `Baseline Analyse Rechnungen/Notebooks_Archiv`. Es wurden keine Inhalte nach Deliverables übernommen, da beide Ordner zur internen Rechnung gehören.

## Erhalt und technische Anpassung

Alle 67 zuvor versionierten Dateien aus beiden Ordnern sind am neuen Ort vorhanden. Inhaltlich angepasst wurden ausschliesslich die Integrationsanleitung, die Pfadanker in `fcsg/config.py`, die Repository-Erkennung im Notebook und dessen Pfadverweise/README. Alle übrigen umgezogenen Dateien, insbesondere analytische Module, Tests, Referenzdaten und Korrekturtabellen, sind byte-identisch zum vorherigen Git-Stand.

Der Codeanker für Overrides/Referenzdaten folgt weiterhin seinem Paketordner. MODEL_DIR/PROJECT_ROOT wurden so angepasst, dass die bisherigen Standard-Ausgabe-, Kontext- und Rohdatenpfade durch die zusätzliche Verschachtelung nicht stillschweigend wechseln. Externe Nutzer sollen explizite lokale Daten-/Kontext-/Ausgabepfade verwenden. Das Notebook sucht den Repository-Root aufwärts anhand von `pyproject.toml`.

## Tatsächlich ausgeführte Prüfungen

- Root-Testsuite: **85 bestanden**, vorhandene Pandas-Warnungen.
- Rechenkern-Start `run_all.py --help`: erfolgreich. Zunächst fehlte statsmodels in der isolierten Prüfumgebung; anschliessend wurden die bereits dokumentierten Paketabhängigkeiten aus der vorhandenen requirements.txt ausschliesslich in dieser Prüfumgebung installiert.
- Rechenkern-Testsuite: **25 bestanden, 25 übersprungen**, weil echte Rohdaten fehlen. Übersprungene Tests sind keine bestätigte Datenvalidierung.
- Initialisierungszelle des Archiv-Notebooks vom neuen verschachtelten Startordner ausgeführt: Repo-Modus findet die archivierte Spieltabelle mit 108 Spielen. Kein vollständiger Notebook-/Baseline-Neulauf und keine Notebook-Ausgaben gespeichert.
- Navigationslinks in Root-, Rechnungs-, Rechenkern- und Notebook-README geprüft.
- Referenz-/Korrektur-CSVs werden am neuen Pfad nicht ignoriert; temporäre Python-Dateien bleiben ausgeschlossen.
- Alte Root-Ordner nicht mehr vorhanden. Alle bisherigen Deliverables und Run-1/2/3-Archive unverändert.
- Staged-Diff ohne Whitespacefehler.

Unabhängige Pfadreview bestanden: keine Sicherheits- oder Logikfehler; Erhalt aller zuvor versionierten Dateien und Paket-/Standardpfadauflösung bestätigt. Remote-Readback erfolgt nach dem Push. Keine fachlichen Rechenregeln geändert, keine Quell-/Ergebnisdateien gelöscht, kein öffentlicher Upload.

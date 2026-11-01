# Rechenkern – verbindliche Zahlenbasis

Dieser Ordner enthält den seit D-028 massgeblichen Analysecode, nicht nur ein altes Ergebnisarchiv. Bis zur Umstrukturierung lag er im Repository-Root unter `ralf/`. Code, Tests, öffentliche Referenzdaten und Korrekturdateien bleiben erhalten; fachliche Rechenlogik unverändert. Die ursprüngliche Paketdokumentation steht in [README.md](README.md).

## Ausführen

Das Paket heisst ebenfalls `fcsg`. Deshalb den Rechenkern immer **aus diesem Ordner** starten; im Repository-Root wird das Paket unter `src/fcsg` geladen.

Beispiel PowerShell, ausgehend vom Repository-Root mit vorhandener `.venv`:

```powershell
Set-Location "Baseline Analyse Rechnungen/Rechenkern"
& "../../.venv/Scripts/python.exe" run_all.py --help
& "../../.venv/Scripts/python.exe" -m pytest -q
```

Für echte Daten explizite, lokal freigegebene Pfade verwenden:

```powershell
& "../../.venv/Scripts/python.exe" run_all.py `
  --daten "C:/FCSG_Daten/raw/20261003_Input Sandro" `
  --kontext "C:/FCSG_Daten/Spielkontext_Tabelle_FCSG_5.xlsx" `
  --ausgabe "../runN_name_datum/ralf_kern_phase1" `
  --ideen-ausgabe "../runN_name_datum/ralf_ideen_grundlage"
```

Mac/Linux: denselben Startordner und den Python-Interpreter der eigenen Umgebung verwenden, z.B. `../../.venv/bin/python`. Rohdaten-/Kontextpfade durch die tatsächlichen lokalen Pfade ersetzen; nicht ins Repo schreiben. Ohne Rohdaten werden datenabhängige Tests übersprungen, nicht als bestanden ausgegeben.

Die bisherige Semantik der Standard-Daten-/Ausgabepfade wurde trotz des tieferen Codeordners beibehalten. Ausgaben ohne expliziten Parameter gehen weiterhin nach `Ergebnisse_Phase1` bzw. `Ergebnisse_Ideen_Grundlage` im Repository-Root (ignoriert). Neue geteilte Rechenstände bewusst unter dem übergeordneten Rechnungsbereich ablegen; historische Runs nie überschreiben.

## Navigation

- [Run 3 / Zahlenbasis](../run3_kontext-v5_2026-10-14/README.md).
- [Quellen und Entscheide](../../Quellen%20und%20interne%20Dokumentation/README.md).
- [Externe Review-Unterlagen](../../Deliverables/README.md).
- [Historisches Notebook](../Notebooks_Archiv/README.md), nicht als zweite aktuelle Zahlenbasis entwickeln.

Wetter-/Resultate-Cache und Korrekturen liegen relativ zum Code unter `external/` bzw. `overrides/`. Keine Dateien entfernt, kein neuer Analyse-Lauf und keine Änderung fachlicher Berechnungen durch die Ordnerumstellung.

# ralf/ – Ralfs Rechenkern im Team-Repo (D-028)

Seit 14.10.2026 ist dieser Code die **Zahlenbasis** des Projekts (Entscheid D-028, Variante A). Ralfs eigene
Anleitung steht unverändert in [README.md](README.md). Diese Datei beschreibt nur, wie der Kern hier eingebunden ist.

| | |
|---|---|
| Herkunft | Übergabe-Paket `FCSG_Uebergabe_v1.1.0` vom 13.10.2026 (Ralf), Ordner `Python_Auswertung/` |
| Änderungen im Repo | nur `fcsg/sources/kontext.py` (+ Test `tests/test_kontext_v5.py`): liest die Spielkontext-Tabelle **Version 5** (D-034), ältere Versionen brechen mit Meldung ab; `fcsg/config.py`: Standarddatei `Spielkontext_Tabelle_FCSG_5.xlsx`. Alle Rechenregeln, Modelle und Korrekturen unverändert |
| Ergebnisse | Ralfs Lauf vom 13.10. (Kontexttabelle v3): `outputs/run2_ralf_2026-10-13/` · Neuberechnung mit v5: `outputs/run3_kontext-v5_2026-10-14/` |
| Paketname | heisst wie Simons Paket `fcsg` → **immer aus diesem Ordner starten** (`cd ralf`), dann wird Ralfs `fcsg` geladen; im Projektroot wird Simons `src/fcsg` geladen |

## Lauf im Repo (Windows, Projekt-`.venv`)

```powershell
cd ralf
..\.venv\Scripts\python.exe run_all.py `
  --daten "C:\FCSG_Daten\raw\20261003_Input Sandro" `
  --kontext "..\Spielkontext_Tabelle_FCSG_5.xlsx" `
  --ausgabe "..\outputs\runN_<name>_<datum>\ralf_kern_phase1" --ohne-ideen
..\.venv\Scripts\python.exe -m pytest        # 50 Tests; 25 brauchen echte Daten (sonst übersprungen)
$env:FCSG_DATA_DIR="C:\FCSG_Daten\raw\20261003_Input Sandro"; $env:FCSG_KONTEXT_FILE="..\Spielkontext_Tabelle_FCSG_5.xlsx"
..\.venv\Scripts\python.exe -m pytest        # mit Daten: alle Integrationstests
```

Mac: dieselben Befehle mit `python` aus der eigenen venv und `/`-Pfaden.

- `--ohne-ideen`, solange D-036 offen ist (Ideen-Grundlage wertet Frauen-Spiele aus, Widerspruch zu D-016).
- Ohne `--ausgabe` schreibt `run_all.py` nach `Ergebnisse_Phase1/` im Projektroot (von Git ausgeschlossen).
- Abhängigkeiten: in `requirements.lock.txt` des Repos enthalten (statsmodels, scipy, xlsxwriter zusätzlich zu Simons Paketen).

## Regeln
- Fachliche Änderungen am Kern nur mit D-Eintrag in `docs/decisions.md` und Changelog (D-027).
- Datenschutz wie im Repo: keine Rohdaten, keine IDs in Ausgaben (Ralfs Test `test_pipeline.py` prüft das mit echten Daten).

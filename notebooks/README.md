# notebooks/

Kurze, erklärende Notebooks als Oberfläche. Die Rechenlogik liegt im Paket `src/fcsg/`; Notebooks rufen nur auf.

| Notebook | Inhalt |
|---|---|
| `01_baseline_hypothesen.ipynb` | Abdeckung, Saison-Baseline, Reto-Abgleich, H1–H3, K1 und Vorlage für eigene Hypothesen |

**Voraussetzungen:** `.venv` mit `requirements.lock.txt` (enthält `ipykernel`). In VS Code den Kernel «.venv»
wählen. Lokale `config/project.local.yaml` und ein bereinigter Lauf in `data/clean/` (Task «Echte Daten
bereinigen/aggregieren») müssen vorhanden sein.

**Regeln:** Ausgaben vor jedem Commit leeren («Clear All Outputs»), da sie echte Zahlen enthalten können.
Headless-Test: `.\.venv\Scripts\python.exe -m jupyter nbconvert --to notebook --execute notebooks/01_baseline_hypothesen.ipynb --output-dir <temp>`.

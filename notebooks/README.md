# notebooks/

Kurze, erklärende Notebooks als Oberfläche. Die Rechenlogik liegt in Paketen; Notebooks rufen nur auf.

| Notebook | Status | Inhalt |
|---|---|---|
| `01_baseline_hypothesen.ipynb` | ⚠️ **Auslaufmodell** (D-037) | Simons Run 1: Abdeckung, Saison-Baseline, Reto-Abgleich, H1–H3, K1. Baut auf `src/fcsg/` auf, nicht auf der Zahlenbasis (Ralfs Kern, D-028). Bleibt lauffähig als Archiv, wird nicht weiterentwickelt |
| `02_…` (geplant) | 💡 Idee, Start Phase 2 | **Analyse-Werkbank** auf Ralfs Rechenkern – siehe unten |

## Geplant: Analyse-Werkbank für Phase 2 (D-037)

Die Phase-1-Baseline braucht kein Notebook. Ihr Ergebnis sind Ralfs Excel, die Methodennotiz und der Run-Ordner,
die fest und reproduzierbar sind. Ein Notebook lohnt sich für Phase 2, um mit den Daten weiterzuarbeiten:

- **Basis:** Ralfs Spieltabelle (`ralf_kern_phase1/Tabellen/mart_match.csv` bzw. voll aus `ralf/`) und Ralfs
  Funktionen. Insbesondere `fcsg/ideen/basis.py::hebel_szenario()`, die einzige Rechenquelle für Python **und** den
  Excel-Hebel-Rechner. Notebook und Excel liefern so immer dieselben Zahlen.
- **Inhalte (je ausgewähltem Chancenfeld):**
  1. Chancenfeld vertiefen (z. B. No-Show nach Bestellkanal, Ankunft nach Tor);
  2. Steckbrief-Szenarien mit φ-Varianten durchrechnen;
  3. **Vorlage Pilot-Auswertung:** Vorher/Nachher gegen die kontextbereinigte Erwartung, mit Vergleichsgruppe
     (Muster: Toröffnungs-Experiment Sektor D, Differenz-in-Differenzen);
  4. eigene Hypothesen testen.
- **Zeitpunkt:** erst nach dem Workshop, in dem 3–5 Chancenfelder ausgewählt werden. So entstehen die Abschnitte passend zur Auswahl, nicht auf Vorrat.
- **FCSG:** Für Management und Sandro sind Excel-Hebel-Rechner und Blatt «Szenarien» das Werkzeug (ohne Python).
  Das Notebook richtet sich an Analysten, im Team und ggf. beim Club, um später neue Saisons und eigene Piloten mit den
  eigenen Rohdaten auszuwerten. Das ist Teil der Übergabe/Aufräumphase.

## Bedienung

**Voraussetzungen:** `.venv` mit `requirements.lock.txt` (enthält `ipykernel`). In VS Code den Kernel «.venv»
wählen. Ohne lokale Config läuft `01_…` im Repo-Modus auf den gespeicherten Run-Ordnern.

**Regeln:** Ausgaben vor jedem Commit leeren («Clear All Outputs»), da sie echte Zahlen enthalten können.
Headless-Test: `.\.venv\Scripts\python.exe -m jupyter nbconvert --to notebook --execute notebooks/<datei>.ipynb --output-dir <temp>`.

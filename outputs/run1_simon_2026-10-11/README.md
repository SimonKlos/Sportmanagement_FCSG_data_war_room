# Run 1 · Simon · 11.10.2026 – erste Baseline-Analyse (vorläufig)

> **Vertraulich – echte FCSG-Daten, aggregiert (keine Personendaten), nur Herren-Pflichtspiele.** Nur für die
> interne Abstimmung im Projektteam (privates Repo, D-024). Alle Kennzahlen sind **vorläufig**, weil die Definitionen
> SOLL/IST/Public Netto und die Umsatzbasis noch offen sind (D-004/D-005).

Dieser Ordner ist ein **eingefrorener Schnappschuss** des ersten Analyse-Laufs. Er wird nicht überschrieben,
auch wenn später neu gerechnet wird. Neue Läufe bekommen einen eigenen Ordner (z. B. `run2_<name>_<datum>/`).

## Wie die Ergebnisse entstanden sind

| Schritt | Befehl | Lauf-ID | Ergebnis |
|---|---|---|---|
| 1 Bereinigung | `python -m fcsg.cli prepare-data --config config/project.local.yaml` | `20261011T191727_clean_33fc` | 18 Tabellen in `data/clean/` (nicht im Repo); 38 Prüfungen OK → `bereinigung/` |
| 2 Analyse | `python -m fcsg.cli analyze --config config/project.local.yaml` | `20261011T195544_baseline_5b22` | Dateien in diesem Ordner; 17 Prüfungen (16 OK, 1 WARN) |
| 3 Excel + Readback | (Teil von `analyze`) | dito | `FCSG_BASELINE_….xlsx`, Readback bestanden → `readback_report.json` |

- **Input:** Datenlieferung «20261003_Input Sandro» (50 Dateien) und `Spielkontext_Tabelle_FCSG_3.xlsx` des Teams.
  Jede Datei ist mit Hash in `sources.csv` bzw. `bereinigung/manifest.json` aufgeführt (so lässt sich prüfen, ob jemand mit
  denselben Rohdaten rechnet).
- **Code:** `fcsg` 0.4.0, Python 3.12.10, pandas 3.0.6, numpy 2.5.3 (vollständige Liste: `requirements.lock.txt`).
- **Bereinigung** (Details: `docs/data_inventory.md`, `docs/data_dictionary_clean.md`, Code `src/fcsg/prepare.py`):
  - Personenbezogene Spalten wurden nie gelesen. Personenbezogene Dateien sind nur aggregiert exportiert.
  - Frauen-Daten fallen ganz weg (D-016).
  - Schulferien vor 26/27 sind recherchiert (D-021).
  - Jede Aggregation ist auf Summenerhalt geprüft.
- **Analyse** (Code `src/fcsg/baseline.py`, `hypotheses.py`; Arbeitsdefinitionen D-025 in `docs/decisions.md`): Spielkalender =
  Herren-Pflichtspiele der Zuschauer-Historie ab 21/22; alle Quellen je Datum aggregiert und 1:1 verknüpft.

## Dateien

| Datei | Inhalt |
|---|---|
| `bericht/01_baseline_erste_erkenntnisse.md` | **Hier anfangen:** Kernaussagen, Saison-Baseline, Reto-Abgleich, H1–H3, K1, offene Punkte (+ `figures/`) |
| `mart_match.csv` | Spieltabelle: 1 Herren-Pflichtspiel pro Zeile, alle Quellen + KPIs (Spalten: `docs/data_dictionary_clean.md`) |
| `season_summary.csv` | gewichtete Saisonwerte (Σ/Σ) mit Stichprobe je KPI |
| `coverage.csv` | welche Saison hat welche Quelle; Stichproben der Hypothesen |
| `quality_checks.csv` | Prüfprotokoll Analyse (Join, Summenerhalt, KPI-Identität, Quellabgleich) |
| `unmatched_report.csv` | Zeilen, die keinem Pflichtspiel zugeordnet wurden, mit Grund |
| `reto_comparison.csv`, `source_total_check.csv` | Abgleich mit Retos Sichtung bzw. mit dem Quell-Tab «Entwicklung» |
| `hypotheses.csv` + `h1_*`, `h2_*`, `h3_*`, `context_associations.csv` | Hypothesenergebnisse und Detailtabellen |
| `FCSG_BASELINE_….xlsx` | alles oben als Excel (16 Blätter, ohne Formeln) |
| `manifest.json`, `readback_report.json` | Laufmetadaten, Versionen, Prüfsummen; Excel-Rückleseprüfung |
| `bereinigung/quality_checks.csv`, `bereinigung/manifest.json` | Prüfprotokoll und Manifest des Bereinigungslaufs (Input-Hashes, Zeilen je Tabelle) |

## Kritisch prüfen – Vorschlag

1. **Prüfprotokolle lesen:** `quality_checks.csv` (hier) und `bereinigung/quality_checks.csv`. Es darf kein FAIL dabei sein. Die eine
   WARN (Q01) ist ein echter Befund: Im Catering-Saison-Tab 23/24 fehlt ein Meisterschaftsspiel, das im Tab «Entwicklung»
   enthalten ist.
2. **Stichprobe gegen die Quelle:** 2–3 Spiele aus `mart_match.csv` mit den Original-Excel vergleichen (IST/SOLL aus der
   Zuschauer-Historie, Umsatz und Transaktionen aus «Umsatz Public Catering»). Dafür braucht es die Rohdaten.
3. **Reto-Abgleich:** `reto_comparison.csv`. 9 von 11 Werten stimmen überein; die 2 Abweichungen sind im Bericht §4 erklärt
   (Abgrenzung «letzte 15 Min.»; Elastizität anders geschätzt).
4. **Definitionen hinterfragen:** KF-Nenner (Public Netto aus der Catering-Datei), Ausschlüsse (`unmatched_report.csv`),
   Regel «Datei mit den meisten Scans» bei doppeltem Zutritt 23/24, Eintrittsfeld nur 21/22–22/23.
5. **Hypothesen:** Die Konfidenzintervalle stehen in `hypotheses.csv`. Saisoneffekte sind herausgerechnet, der Spielkontext aber nicht. Ein «gestützt» ist daher
   ein Hinweis, kein Nachweis.

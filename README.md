# FCSG «Untapped Business» – Datenanalyse Phase 1 (interner Arbeitsstand)

> **Intern – nur für die Abstimmung im Projektteam.** Das Repo enthält aggregierte, **vertrauliche** FCSG-Ergebnisse
> (keine Personendaten) und ist deshalb privat (D-024). Vor einer Übergabe an den FC St.Gallen wird es aufgeräumt
> (siehe [§8](#8-vor-der-übergabe-an-den-fcsg)). Alle Kennzahlen sind **vorläufig**: Die Definitionen SOLL/IST/Public Netto und
> die Umsatzbasis sind mit Sandro noch nicht geklärt (D-004/D-005).

Modellierungsauftrag «Datenverknüpfung & Kontextbereinigung» des FC St.Gallen 1879 (HSG, Sportmanagement in der
Praxis HS26). Phase 1: Ticketing-, Zutritts- und Catering-Daten je Heimspiel verknüpfen, eine saubere Baseline bauen
und den Spielkontext einbeziehen. Steuerungsgrösse ist der **Deckungsbeitrag** (D-003); dafür fehlen noch Kostendaten,
deshalb arbeitet die Baseline vorerst auf Umsatzebene. Fachliche Grundlage: `docs/briefing/` (Arbeitsfassungen der 3 PDFs).

## 1 Stand (11.10.2026)

| Schritt | Stand | Wo |
|---|---|---|
| Datenlieferung inventarisiert (50 Dateien, «20261003_Input Sandro») | ✅ | [docs/data_inventory.md](docs/data_inventory.md) |
| Daten bereinigt und aggregiert (nur Herren, ohne Personendaten) | ✅ 38/38 Prüfungen OK | [§4](#4-wie-die-daten-zustande-kommen-bereinigung) |
| Baseline je Spiel und Saison + Abgleich mit Retos Sichtung | ✅ vorläufig | [Bericht](docs/analysis/01_baseline_erste_erkenntnisse.md) |
| Hypothesen H1–H3 (Verknüpfung der 3 Datenbasen) + K1 (Spielkontext) | ✅ explorativ | Bericht §5–§6 |
| Ergebnisse Run 1 zum Nachprüfen | ✅ | [outputs/run1_simon_2026-10-11/](outputs/run1_simon_2026-10-11/) |
| Kontextmodelle, Diagnosekarte, Deckungsbeitrag | ⏳ erst nach Baseline-Freigabe bzw. Kostendaten | [docs/decisions.md](docs/decisions.md) |

## 2 Einstieg – drei Wege

| Ich will … | Dann … | Rohdaten nötig? |
|---|---|---|
| **verstehen, was rauskam** | [Bericht](docs/analysis/01_baseline_erste_erkenntnisse.md) lesen (Kernaussagen oben), dann [Run-1-README](outputs/run1_simon_2026-10-11/README.md) | nein |
| **mit den Ergebnissen weiterrechnen** (neue Hypothesen auf Spielebene) | [Notebook](notebooks/01_baseline_hypothesen.ipynb) öffnen, Kernel `.venv`. Ohne lokale Config läuft es automatisch im **Repo-Modus** auf `outputs/run1_…/mart_match.csv` | nein |
| **alles neu rechnen** (andere Definitionen, neue Aggregationen, neue Lieferung, H3 neu) | Rohdaten lokal ablegen, `config/project.local.example.yaml` → `config/project.local.yaml` kopieren, dann [§5](#5-befehle-und-wichtigste-funktionen) | **ja** |

### Kann ich mit den Daten im Repo weiterrechnen?

**Teilweise.** Im Repo liegen die **Ergebnisse** von Run 1, nicht die Daten selbst:

| Im Repo | Damit möglich | Nicht im Repo (lokal) |
|---|---|---|
| `outputs/run1_…/mart_match.csv`: 108 Herren-Pflichtspiele × ~65 Spalten (Ticketing, Zutritt, Catering, Kontext, KPIs) | Baseline-Auswertungen, Grafiken, H1/H2/K1 neu testen, **eigene Hypothesen auf Spielebene** | **Rohdaten** (Personendaten; SharePoint bzw. bei Simon), Ablage `C:\FCSG_Daten\raw\` (D-015) |
| `season_summary.csv`, Hypothesen- und Prüftabellen, Excel | nachvollziehen und gegenprüfen | **`data/clean/`**: 18 bereinigte Tabellen (z. B. Ankunft je Minute und Sektor, Tickets nach Vorlauf, Kanal und Block) |
| Code, Tests, künstliche Testdaten | Code ändern und testen (`pytest`) ohne echte Daten | `Spielkontext_Tabelle_FCSG_3.xlsx` (Team, SharePoint) |

Für alles **unterhalb der Spielebene** braucht ihr die Rohdaten und einen eigenen `prepare-data`-Lauf. Dazu gehören Ankunftskurven je Sektor,
Ticketvorlauf nach Kanal, H3 neu, Kiesplatz-Stände und Artikel. Der Lauf dauert einige Minuten; danach stimmen die Prüfsummen mit
`outputs/run1_…/bereinigung/manifest.json` überein, wenn ihr dieselbe Lieferung nutzt.

## 3 Wie das Projekt funktioniert

```text
Rohdaten (lokal)  ──prepare-data──▶  data/clean/<run>/  ──analyze──▶  Spieltabelle mart_match  ──▶  KPIs, Reto-Abgleich,
50 Dateien + Kontext   bereinigen,      18 Tabellen,          1:1 über Spieldatum,    (1 Zeile = 1 Spiel)     Hypothesen H1–H3, K1
                       aggregieren      nur Aggregate         Summen geprüft                                   │
                                                                                                               ▼
                                     Bericht docs/analysis/ (+ Grafiken) · Excel + Readback · Laufordner mit manifest.json
```

**Die drei Datenbasen** (Treiberbaum, `docs/briefing/02_datenquellen_treiberbaum.md`) und was daraus je Spiel wird:

| Datenbasis | Quelle | In der Spieltabelle |
|---|---|---|
| **Ticketing** | Zuschauer-Historie (SOLL/IST, Ausverkauft), Einzeltickets 21/22–24/25, Ticket-CSVs 25/26+, Abo-Snapshot | Spielkalender, Anwesenheitsquote, No-Show, Ticketvorlauf, Eintrittsquote |
| **Zutritt** | Drehkreuz-Scans 22/23–26/27 | Scans, «Zutritt vollständig» (±5 % zu IST), Ankunft ≥ 45 Min. / letzte 15 Min. vor Anpfiff |
| **Catering** | Public Catering ab 18/19, Kiesplatz, Artikel | Umsatz brutto/netto, Public Netto, Bons, KF, Ø Bon |
| Kontext | Spielkontext-Tabelle des Teams 22/23–26/27 | Gegner, Tabelle, Form, Wetter (Tageswerte), TV, Ferien, Feiertag |

## 4 Wie die Daten zustande kommen (Bereinigung)

Code: [src/fcsg/prepare.py](src/fcsg/prepare.py) · Details: [docs/data_inventory.md](docs/data_inventory.md), [docs/data_dictionary_clean.md](docs/data_dictionary_clean.md)

- **Datenschutz:** Personenbezogene Spalten (Name, Geburtstag, PLZ, Kunden-Nr., Sitzplatz, Barcode …) werden **nie gelesen**,
  dafür sorgt eine Positivliste der Spalten. Ticket- und Rechnungsschlüssel werden nur intern gehasht, um zu zählen. Jede Ausgabetabelle durchläuft eine
  Personenbezug-Prüfung (D-001).
- **Scope:** Frauen-Daten sind ganz entfernt (D-016). Freundschaftsspiele, abgesagte Spiele und fremde Events werden
  ausgeschlossen und im Unmatched-Report aufgeführt.
- **Vereinheitlicht:** englische Spaltennamen, Datum/Anstosszeit, CHF-Beträge, Brutto/Netto getrennt. Fehlende Werte bleiben
  leer und werden nie 0. Kennzahlen, die die Quelle selbst berechnet, tragen das Suffix `_reported`.
- **Ergänzt:** Schulferien vor 26/27 sind recherchiert (Stadt St.Gallen, mit Quellen in `config/reference/`, D-021). Die Herkunft je
  Spiel steht in `school_holiday_source`.
- **Geprüft:** Summenerhalt für jede Aggregation (1 046 015 Scans, 180 167 Tickets, 488 293 Einzelticket-Zeilen, 13 052
  Abo-Sitze). In der Analyse kommen Join-Kardinalität, Summenerhalt je Quelle, KF = Bonsrate × Ø Bon und der Abgleich mit dem Quell-Tab
  «Entwicklung» dazu.
- **Bekannte Lücken:**
  - Zutritt 24/25 ist nur für 9 Spiele vollständig.
  - Bons gibt es erst ab 23/24.
  - Das Eintrittsfeld der Einzeltickets ist nur 21/22–22/23 befüllt.
  - Für 6 Spiele aus 25/26 fehlt der Spielkontext.
  - Im Catering-Saison-Tab 23/24 fehlt ein Spiel.

## 5 Befehle und wichtigste Funktionen

Setup: siehe separate Anleitung. Kurz: Python 3.12, `py -3.12 -m venv .venv`, dann `.\.venv\Scripts\python.exe -m pip install -r requirements.lock.txt`
und `.\.venv\Scripts\python.exe -m pip install -e . --no-deps`. In VS Code gibt es alle Befehle auch als Task («Terminal → Task ausführen…»).

| Befehl (`.\.venv\Scripts\python.exe -m …`) | VS-Code-Task | Zweck |
|---|---|---|
| `pytest -q` | FCSG: Tests ausführen | 83 Tests, nur künstliche Daten |
| `fcsg.cli prepare-data --config config/project.local.yaml` | FCSG: Echte Daten bereinigen/aggregieren | Rohdaten → `data/clean/<run>/` |
| `fcsg.cli analyze --config config/project.local.yaml` | FCSG: Baseline-Analyse (echte Daten) | Spieltabelle, KPIs, Hypothesen → Bericht `docs/analysis/`, Excel + Readback |
| `fcsg.cli run --config config/project.example.yaml` | FCSG: Lauf + Excel-Export + Readback (Fixture) | technischer Test mit künstlichen Daten |

| Modul | Wichtigste Funktionen |
|---|---|
| `prepare.py` | `run_prepare` (Gesamtlauf), `prepare_*` je Quelle, `drop_women`, `apply_school_holidays`, `assert_no_personal_columns` |
| `baseline.py` | `load_clean`, `build_mart_match_real` (Join + Prüfungen), `add_real_kpis`, `season_summary_real`, `coverage_real`, `reto_comparison`, `KPI_DEFINITIONS_REAL` |
| `hypotheses.py` | `test_h1`, `test_h2`, `test_h3`, `context_associations`; Helfer `demean`, `spearman`, `bootstrap`, `status_from_ci`; Liste `FURTHER_HYPOTHESES` |
| `analysis.py` / `report.py` / `export.py` | Analyse-Lauf mit Manifest · Bericht + Grafiken · Excel ohne Formeln + Readback |

Mehr dazu: [src/fcsg/README.md](src/fcsg/README.md), [docs/analysis/README.md](docs/analysis/README.md) (mögliche Baseline-Outputs, Regeln für neue Tests).

## 6 Projektstruktur

| Ordner/Datei | Inhalt |
|---|---|
| `docs/analysis/` | Bericht, Grafiken, Übergabe-Doku zur Analyse |
| `docs/briefing/` | Arbeitsfassungen der PDFs (Auftrag, Datenquellen/Treiberbaum, Projektantrag) + Widerspruchsliste |
| `docs/decisions.md` | alle Entscheide und offenen Punkte (D-001 …) |
| `outputs/run1_simon_2026-10-11/` | Ergebnisse Run 1 (eingefroren) inkl. Prüfprotokolle der Bereinigung |
| `notebooks/` | Notebook Baseline + Hypothesen (Repo- und Voll-Modus) |
| `src/fcsg/` | Python-Paket (gesamte Logik) |
| `tests/` | pytest mit künstlichen Daten (Jahr 2099) |
| `config/` | Fixture-Config, Vorlage für die lokale Config, `reference/` (Schulferien) |
| `CLAUDE.md`, `AGENTS.md`, `PROJECT_SETUP.md` | Arbeitsregeln für KI-Agenten und Gesamtplan |

## 7 Arbeitsregeln (kurz)

- **Nie ins Repo:** Rohdaten, `data/`, `config/project.local.yaml`, Quell-PDFs, Notebook-Ausgaben (vor dem Commit «Clear All Outputs»).
  `.gitignore` ist eingerichtet, ersetzt aber nicht den Blick vor dem Commit.
- **Neue Ergebnisse teilen:** als neuer Ordner `outputs/runN_<name>_<datum>/` mit kurzem README (Lauf-IDs, Befehle, Prüfstatus).
  Run 1 nicht überschreiben.
- **Methodik:**
  - Fehlende Werte nie als 0.
  - Saisonwerte gewichtet (Σ/Σ).
  - Zusammenhänge saison-zentriert und mit Konfidenzintervall.
  - Keine Kausalsprache, keine «Potenziale».
  - Lücken von KF, Bonsrate und Ø Bon nie addieren.
  - Modellierung erst nach Baseline-Freigabe.
- **Entscheide** in `docs/decisions.md` nachführen. Neue Logik immer mit Test auf künstlichen Daten.

## 8 Vor der Übergabe an den FCSG

Dieser Stand dient der internen Abstimmung. Für die Übergabe wird aufgeräumt:
- Definitionen mit Sandro klären (D-004/D-005), Kostendaten für den Deckungsbeitrag (D-003), Bestätigung zur lokalen Verarbeitung (D-023).
- Interne Inhalte prüfen und ggf. entfernen: Run-Ordner, Sichtungszahlen und Namen im Briefing, Agentenregeln.
- Lizenz und Repo-Eigentum klären (D-012); finalen Bericht und Excel als freigegebene Version erstellen.

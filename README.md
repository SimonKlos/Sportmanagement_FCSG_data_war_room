# FCSG «Untapped Business» – Baseline und Chancenfelder

## Einstieg nach Verwendungszweck

- **[Deliverables](Deliverables/README.md):** extern ausgerichteter Bericht, Excel, neutrale Diagramme und ausführlicher Folienleitfaden (**keine fertige PPT**); Review-Fassung, nicht automatisch freigegeben.
- **[Baseline Analyse Rechnungen](Baseline%20Analyse%20Rechnungen/README.md):** alle eingefrorenen Rechenstände, Gegenrechnungen und Prüfausgaben; bisher `outputs`.
- **[Quellen und interne Dokumentation](Quellen%20und%20interne%20Dokumentation/README.md):** Quellen, Begriffe, Decision Logs, interne Abstimmungen und Delivery-Prüfungen; bisher `docs`.

Der massgebliche Rechenkern und das Notebook-Archiv liegen im Rechnungsbereich. Die Bereinigungs-/Gegenrechnungspipeline (`src/`), ihre Tests und Konfiguration bleiben technisch am bisherigen Ort und sind aus dem Rechenbereich verlinkt. Keine doppelte Rechenlogik, keine neue Modellschätzung durch die Aufbereitung. Die folgenden Abschnitte dokumentieren weiterhin die interne analytische Herkunft.

> **Intern – nur für die Abstimmung im Projektteam.** Das Repo enthält aggregierte, **vertrauliche** FCSG-Ergebnisse
> (keine Personendaten) und ist deshalb privat (D-024). Vor einer Übergabe an den FC St.Gallen wird es aufgeräumt
> (siehe [§8](#8-vor-der-übergabe-an-den-fcsg)). Alle Kennzahlen sind **vorläufig**: Die Definitionen SOLL/IST/Public Netto und
> die Umsatzbasis sind mit Sandro noch nicht geklärt (D-004/D-005).

Modellierungsauftrag «Datenverknüpfung & Kontextbereinigung» des FC St.Gallen 1879 (HSG, Sportmanagement in der
Praxis HS26). Phase 1: Ticketing-, Zutritts- und Catering-Daten je Heimspiel verknüpfen, eine saubere Baseline bauen
und den Spielkontext einbeziehen. Steuerungsgrösse ist der **Deckungsbeitrag** (D-003); dafür fehlen noch Kostendaten,
deshalb arbeitet die Baseline vorerst auf Umsatzebene. Fachliche Grundlage: `Quellen und interne Dokumentation/briefing/` (Arbeitsfassungen der 3 PDFs).

## Aktueller Nachtrag (01.11.2026)

Partnerantworten und neue Projektfestlegung: [Catering-Klärung und Baseline-Folgen](Quellen%20und%20interne%20Dokumentation/team/2026-11-01_catering_klaerung_und_baseline_folgen.md). Phase-2-Massnahmen werden auf Umsatz bewertet (D-039); Catering-Systemumsatz und Cluberlös bleiben getrennt. 20 % Clubbeteiligung ist nur eine unbestätigte Szenarioannahme (D-040). KF exkl. MwSt. ist fachlich bestätigt, konkretes Nenner-Mapping bleibt offen. Bons-/Bon-Auswertungen sind wegen Erfassungsänderungen 2023/24 erneut auf Vergleichbarkeit zu prüfen (D-041). **Keine Neuberechnung erfolgt**; der folgende technische Stand und historische Outputs bleiben unverändert.

## 1 Stand (14.10.2026)

| Schritt | Stand | Wo |
|---|---|---|
| Datenlieferung inventarisiert (50 Dateien, «20261003_Input Sandro») | ✅ | [Quellen und interne Dokumentation/data_inventory.md](Quellen%20und%20interne%20Dokumentation/data_inventory.md) |
| Daten bereinigt und aggregiert (nur Herren, ohne Personendaten) | ✅ 38/38 Prüfungen OK | [§4](#4-wie-die-daten-zustande-kommen-bereinigung) |
| Baseline je Spiel und Saison + Abgleich mit Retos Sichtung | ✅ vorläufig | [Bericht](Quellen%20und%20interne%20Dokumentation/analysis/01_baseline_erste_erkenntnisse.md) |
| Hypothesen H1–H3 (Verknüpfung der 3 Datenbasen) + K1 (Spielkontext) | ✅ explorativ | Bericht §5–§6 |
| Ergebnisse Run 1 zum Nachprüfen | ✅ | [Baseline Analyse Rechnungen/run1_simon_2026-10-11/](Baseline%20Analyse%20Rechnungen/run1_simon_2026-10-11/) |
| **Ralfs Rechenkern übernommen = Zahlenbasis** (D-028) | ✅ | [Baseline Analyse Rechnungen/Rechenkern/README_REPO.md](Baseline%20Analyse%20Rechnungen/Rechenkern/README_REPO.md) |
| Spielkontext-Tabelle **Version 5** (D-034), Neuberechnung beider Pipelines + Abgleich | ✅ Kernzahlen identisch | [Baseline Analyse Rechnungen/run3_kontext-v5_2026-10-14/](Baseline%20Analyse%20Rechnungen/run3_kontext-v5_2026-10-14/README.md) |
| Kontextmodelle und Diagnosekarte (Ralf) | ✅ gerechnet, Freigabe offen | `Baseline Analyse Rechnungen/run3_…/ralf_kern_phase1/` |
| Vorschlag nächste Schritte Phase 1 → Phase 2 | 💬 zur Diskussion | [Quellen und interne Dokumentation/team/2026-10-14_vorschlag_naechste_schritte.md](Quellen%20und%20interne%20Dokumentation/team/2026-10-14_vorschlag_naechste_schritte.md) |
| Deckungsbeitrag | ⏳ Kostendaten fehlen (D-003/D-029) | [Quellen und interne Dokumentation/decisions.md](Quellen%20und%20interne%20Dokumentation/decisions.md) |

## 2 Einstieg – drei Wege

| Ich will … | Dann … | Rohdaten nötig? |
|---|---|---|
| **verstehen, was rauskam** | [Run-3-README](Baseline%20Analyse%20Rechnungen/run3_kontext-v5_2026-10-14/README.md), dann Ralfs `Methodennotiz_Phase1.md` (Run 3) und die [Vorschläge](Quellen%20und%20interne%20Dokumentation/team/2026-10-14_vorschlag_naechste_schritte.md); Simons erster Bericht: [Run 1](Quellen%20und%20interne%20Dokumentation/analysis/01_baseline_erste_erkenntnisse.md) | nein |
| **mit den Ergebnissen weiterrechnen** (neue Hypothesen auf Spielebene) | [Notebook](Baseline%20Analyse%20Rechnungen/Notebooks_Archiv/01_baseline_hypothesen.ipynb) öffnen, Kernel `.venv`. Ohne lokale Config läuft es automatisch im **Repo-Modus** auf `Baseline Analyse Rechnungen/run1_…/mart_match.csv` | nein |
| **alles neu rechnen** (andere Definitionen, neue Aggregationen, neue Lieferung, H3 neu) | Rohdaten lokal ablegen, `config/project.local.example.yaml` → `config/project.local.yaml` kopieren, dann [§5](#5-befehle-und-wichtigste-funktionen) | **ja** |

### Kann ich mit den Daten im Repo weiterrechnen?

**Teilweise.** Im Repo liegen die **Ergebnisse** von Run 1, nicht die Daten selbst:

| Im Repo | Damit möglich | Nicht im Repo (lokal) |
|---|---|---|
| `Baseline Analyse Rechnungen/run1_…/mart_match.csv`: 108 Herren-Pflichtspiele × ~65 Spalten (Ticketing, Zutritt, Catering, Kontext, KPIs) | Baseline-Auswertungen, Grafiken, H1/H2/K1 neu testen, **eigene Hypothesen auf Spielebene** | **Rohdaten** (Personendaten; SharePoint bzw. bei Simon), Ablage `C:\FCSG_Daten\raw\` (D-015) |
| `season_summary.csv`, Hypothesen- und Prüftabellen, Excel | nachvollziehen und gegenprüfen | **`data/clean/`**: 18 bereinigte Tabellen (z. B. Ankunft je Minute und Sektor, Tickets nach Vorlauf, Kanal und Block) |
| Code, Tests, künstliche Testdaten | Code ändern und testen (`pytest`) ohne echte Daten | `Spielkontext_Tabelle_FCSG_3.xlsx` (Team, SharePoint) |

Für alles **unterhalb der Spielebene** braucht ihr die Rohdaten und einen eigenen `prepare-data`-Lauf. Dazu gehören Ankunftskurven je Sektor,
Ticketvorlauf nach Kanal, H3 neu, Kiesplatz-Stände und Artikel. Der Lauf dauert einige Minuten; danach stimmen die Prüfsummen mit
`Baseline Analyse Rechnungen/run1_…/bereinigung/manifest.json` überein, wenn ihr dieselbe Lieferung nutzt.

## 3 Wie das Projekt funktioniert

```text
Rohdaten (lokal)  ──prepare-data──▶  data/clean/<run>/  ──analyze──▶  Spieltabelle mart_match  ──▶  KPIs, Reto-Abgleich,
50 Dateien + Kontext   bereinigen,      18 Tabellen,          1:1 über Spieldatum,    (1 Zeile = 1 Spiel)     Hypothesen H1–H3, K1
                       aggregieren      nur Aggregate         Summen geprüft                                   │
                                                                                                               ▼
                                     Bericht Quellen und interne Dokumentation/analysis/ (+ Grafiken) · Excel + Readback · Laufordner mit manifest.json
```

**Die drei Datenbasen** (Treiberbaum, `Quellen und interne Dokumentation/briefing/02_datenquellen_treiberbaum.md`) und was daraus je Spiel wird:

| Datenbasis | Quelle | In der Spieltabelle |
|---|---|---|
| **Ticketing** | Zuschauer-Historie (SOLL/IST, Ausverkauft), Einzeltickets 21/22–24/25, Ticket-CSVs 25/26+, Abo-Snapshot | Spielkalender, Anwesenheitsquote, No-Show, Ticketvorlauf, Eintrittsquote |
| **Zutritt** | Drehkreuz-Scans 22/23–26/27 | Scans, «Zutritt vollständig» (±5 % zu IST), Ankunft ≥ 45 Min. / letzte 15 Min. vor Anpfiff |
| **Catering** | Public Catering ab 18/19, Kiesplatz, Artikel | Umsatz brutto/netto, Public Netto, Bons, KF, Ø Bon |
| Kontext | Spielkontext-Tabelle des Teams 22/23–26/27 | Gegner, Tabelle, Form, Wetter (Tageswerte), TV, Ferien, Feiertag |

## 4 Wie die Daten zustande kommen (Bereinigung)

Code: [src/fcsg/prepare.py](src/fcsg/prepare.py) · Details: [Quellen und interne Dokumentation/data_inventory.md](Quellen%20und%20interne%20Dokumentation/data_inventory.md), [Quellen und interne Dokumentation/data_dictionary_clean.md](Quellen%20und%20interne%20Dokumentation/data_dictionary_clean.md)

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
  - Simons Einleser überspringt im Catering-Tab 23/24 die Zeile vom 27.09.2023 (Datum nicht lesbar); Ralfs Kern liest sie.

## 5 Befehle und wichtigste Funktionen

Setup: siehe separate Anleitung. Kurz: Python 3.12, `py -3.12 -m venv .venv`, dann `.\.venv\Scripts\python.exe -m pip install -r requirements.lock.txt`
und `.\.venv\Scripts\python.exe -m pip install -e . --no-deps`. In VS Code gibt es alle Befehle auch als Task («Terminal → Task ausführen…»).

| Befehl (`.\.venv\Scripts\python.exe -m …`) | VS-Code-Task | Zweck |
|---|---|---|
| `pytest -q` | FCSG: Tests ausführen | 83 Tests, nur künstliche Daten |
| `fcsg.cli prepare-data --config config/project.local.yaml` | FCSG: Echte Daten bereinigen/aggregieren | Rohdaten → `data/clean/<run>/` |
| `fcsg.cli analyze --config config/project.local.yaml` | FCSG: Baseline-Analyse (echte Daten) | Spieltabelle, KPIs, Hypothesen → Bericht `Quellen und interne Dokumentation/analysis/`, Excel + Readback |
| `fcsg.cli run --config config/project.example.yaml` | FCSG: Lauf + Excel-Export + Readback (Fixture) | technischer Test mit künstlichen Daten |

| Modul | Wichtigste Funktionen |
|---|---|
| `prepare.py` | `run_prepare` (Gesamtlauf), `prepare_*` je Quelle, `drop_women`, `apply_school_holidays`, `assert_no_personal_columns` |
| `baseline.py` | `load_clean`, `build_mart_match_real` (Join + Prüfungen), `add_real_kpis`, `season_summary_real`, `coverage_real`, `reto_comparison`, `KPI_DEFINITIONS_REAL` |
| `hypotheses.py` | `test_h1`, `test_h2`, `test_h3`, `context_associations`; Helfer `demean`, `spearman`, `bootstrap`, `status_from_ci`; Liste `FURTHER_HYPOTHESES` |
| `analysis.py` / `report.py` / `export.py` | Analyse-Lauf mit Manifest · Bericht + Grafiken · Excel ohne Formeln + Readback |

Mehr dazu: [src/fcsg/README.md](src/fcsg/README.md), [Quellen und interne Dokumentation/analysis/README.md](Quellen%20und%20interne%20Dokumentation/analysis/README.md) (mögliche Baseline-Outputs, Regeln für neue Tests).

## 6 Projektstruktur

| Ordner/Datei | Inhalt |
|---|---|
| `Quellen und interne Dokumentation/analysis/` | Bericht, Grafiken, Übergabe-Doku zur Analyse |
| `Quellen und interne Dokumentation/briefing/` | Arbeitsfassungen der PDFs (Auftrag, Datenquellen/Treiberbaum, Projektantrag) + Widerspruchsliste |
| `Quellen und interne Dokumentation/decisions.md` | alle Entscheide und offenen Punkte (D-001 …) |
| `Baseline Analyse Rechnungen/run1_simon_2026-10-11/` | Ergebnisse Run 1 (eingefroren) inkl. Prüfprotokolle der Bereinigung |
| `Baseline Analyse Rechnungen/Notebooks_Archiv/` | Notebook Baseline + Hypothesen (Repo- und Voll-Modus) |
| `src/fcsg/` | Python-Paket (gesamte Logik) |
| `tests/` | pytest mit künstlichen Daten (Jahr 2099) |
| `config/` | Fixture-Config, Vorlage für die lokale Config, `reference/` (Schulferien) |
| `CLAUDE.md`, `AGENTS.md`, `PROJECT_SETUP.md` | Arbeitsregeln für KI-Agenten und Gesamtplan |

## 7 Arbeitsregeln (kurz)

- **Nie ins Repo:** Rohdaten, `data/`, `config/project.local.yaml`, Quell-PDFs, Notebook-Ausgaben (vor dem Commit «Clear All Outputs»).
  `.gitignore` ist eingerichtet, ersetzt aber nicht den Blick vor dem Commit.
- **Neue Ergebnisse teilen:** als neuer Ordner `Baseline Analyse Rechnungen/runN_<name>_<datum>/` mit kurzem README (Lauf-IDs, Befehle, Prüfstatus).
  Run 1 nicht überschreiben.
- **Methodik:**
  - Fehlende Werte nie als 0.
  - Saisonwerte gewichtet (Σ/Σ).
  - Zusammenhänge saison-zentriert und mit Konfidenzintervall.
  - Keine Kausalsprache, keine «Potenziale».
  - Lücken von KF, Bonsrate und Ø Bon nie addieren.
  - Modellierung erst nach Baseline-Freigabe.
- **Entscheide** in `Quellen und interne Dokumentation/decisions.md` nachführen (auch Hypothesen und Agent-Annahmen, D-027); grössere Änderungen
  im `CHANGELOG.md` festhalten. Neue Logik immer mit Test auf künstlichen Daten.

## 8 Vor der Übergabe an den FCSG

Dieser Stand dient der internen Abstimmung. Für die Übergabe wird aufgeräumt:
- Definitionen mit Sandro klären (D-004/D-005), Kostendaten für den Deckungsbeitrag (D-003), Bestätigung zur lokalen Verarbeitung (D-023).
- Interne Inhalte prüfen und ggf. entfernen: Run-Ordner, Sichtungszahlen und Namen im Briefing, Agentenregeln.
- Lizenz und Repo-Eigentum klären (D-012); finalen Bericht und Excel als freigegebene Version erstellen.

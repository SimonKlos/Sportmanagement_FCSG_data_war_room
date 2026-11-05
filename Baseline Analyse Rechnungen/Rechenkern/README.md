# Python-Auswertung – «Untapped Business» FC St.Gallen 1879 (Phase 1 und Ideen-Grundlage)

Reproduzierbare Umsetzung des **Arbeitsauftrags Modellierung – Datenverknüpfung & Kontextbereinigung** (Simon)
auf Basis der Übersicht **FCSG Datenquellen & Treiberbaum** (Reto). Ein Aufruf liest alle Rohdaten aus
`1. Daten FCSG`, verknüpft sie pro Heimspiel und erzeugt
- die Phase-1-Ergebnisse in `2. Modellierung/Ergebnisse_Phase1` (Version 1.1.0, Änderungen siehe Abschnitt 4) und
- die **Ideen-Grundlage** für Simon und Reto in `2. Modellierung/Ergebnisse_Ideen_Grundlage` (Abschnitt 3).

> **Datenschutz:** Personenfelder (Name, Geburtstag, PLZ, Geschlecht, Kunden-, Ticket- und Barcode-Nummern)
> werden beim Einlesen gar nicht übernommen. Pseudonyme Zutritts-IDs dienen nur zur Deduplizierung und werden
> danach verworfen. Ausgegeben werden ausschliesslich Aggregate; Segmente mit weniger als 10 Tickets/Scans werden
> unterdrückt. Ein automatischer Test prüft, dass keine ID-Spalte in den Ausgaben landet. Alle Ergebnisse sind
> vertraulich (NDA) und bleiben im Datenraum der Projektgruppe; keine Rohdaten oder Personendaten nach Notion.

---

## 1. Schnellstart (ca. 5 Minuten)

Voraussetzung: Python 3.10 oder neuer (getestet mit 3.12).

**Wichtig:** Die virtuelle Umgebung **nicht** im iCloud-/OneDrive-Ordner anlegen (tausende Dateien würden synchronisiert).

macOS / Linux:
```bash
python3 -m venv ~/.venvs/fcsg
source ~/.venvs/fcsg/bin/activate
cd "<Pfad>/Sportmanagement/2. Modellierung/Python_Auswertung"
pip install -r requirements.txt
python run_all.py
```

Windows (PowerShell):
```powershell
py -m venv $HOME\.venvs\fcsg
$HOME\.venvs\fcsg\Scripts\Activate.ps1
cd "<Pfad>\Sportmanagement\2. Modellierung\Python_Auswertung"
pip install -r requirements.txt
python run_all.py
```

Mit [uv](https://docs.astral.sh/uv/) geht es schneller: `uv venv ~/.venvs/fcsg && uv pip install -r requirements.txt --python ~/.venvs/fcsg`.

Laufzeit: rund 100 Sekunden (Phase 1 ≈ 40 s, Ideen-Grundlage ≈ 60 s). Am Ende meldet das Skript
«Importtests: 19 von 19 bestanden» und «Ideen-Grundlage geschrieben … (QA: 18 von 18 bestanden; PDF erstellt)».

**Aus dem Übergabe-ZIP** (`FCSG_Uebergabe_v1.1.0`): Code, Spielkontext-Tabelle und Ergebnisse sind im Paket, die
FCSG-Rohdaten nicht. Deren Ordner beim Start angeben:

```bash
cd "<Pfad>/FCSG_Uebergabe_v1.1.0/Python_Auswertung"
python run_all.py --daten "<Pfad>/1. Daten FCSG"
```

Ohne `--daten` sucht das Skript «1. Daten FCSG» zwei Ebenen über `Python_Auswertung` (Projektablage:
`Sportmanagement/1. Daten FCSG`; beim ZIP: neben dem Ordner `FCSG_Uebergabe_v1.1.0`), die Spielkontext-Tabelle eine
Ebene darüber (anderer Ort: `--kontext "<Datei>"`). Fehlt eine Pflichtdatei, bricht das Skript sofort ab und listet die
fehlenden Dateien auf. Alternativ wirken die Umgebungsvariablen `FCSG_DATA_DIR`, `FCSG_KONTEXT_FILE`, `FCSG_OUTPUT_DIR`
und `FCSG_IDEEN_DIR`.

Weitere Optionen:
- `python run_all.py --ohne-grafiken` – ohne PNG-Grafiken (auch das Dossier dann ohne Grafiken)
- `python run_all.py --ausgabe <Ordner>` – anderer Zielordner für Phase 1 (Standard: `Ergebnisse_Phase1` neben dem Codeordner)
- `python run_all.py --ohne-ideen` – nur Phase 1
- `python run_all.py --ideen-ausgabe <Ordner>` – anderer Zielordner für die Ideen-Grundlage
- `python run4.py --daten <Ordner> --kontext <Datei> --ausgabe <Ordner>` – Vergleich Slot-Modell vs. Run-3-Spezifikation und
  Sensitivitäten 2021/22 / ohne 2023/24 (D-046). Seit D-048 nutzt auch `run_all.py` den Anstoss-Slot in allen Kontextmodellen
  (`config.SLOTS`, `models.VARIABLEN`); die Run-3-Spezifikation bleibt als `models.VARIABLEN_RUN3` für Vergleiche.
- `python -m pytest` – 48 Tests in rund 1.5 Minuten: Einheitentests (Parser, MwSt-Formeln, Bemerkungs-Codierung,
  Hebel-Formeln) und Integrationstests auf den echten Daten (Retos Kernzahlen, Validierungen, Datenschutz, Ideen-Stufe)

Exit-Code von `run_all.py`: 0 = alles bestanden, 1 = Eingaben fehlen, 2 = ein Phase-1-Importtest ist nicht bestanden,
3 = eine Prüfung der Ideen-Grundlage ist nicht bestanden oder die Stufe ist abgebrochen (Phase 1 ist dann trotzdem
vollständig geschrieben; Details im Log und in `QA_Ideen_Grundlage.csv`).

---

## 2. Was herauskommt (`2. Modellierung/Ergebnisse_Phase1`)

| Datei | Inhalt |
|---|---|
| `FCSG_Phase1_Ergebnisse.xlsx` | Alle Tabellen (rund 60 Blätter) mit Inhaltsverzeichnis (`00_Inhalt`, verlinkt) und `00_Aenderungsprotokoll` (v1.0.1 → v1.1.0) |
| `Methodennotiz_Phase1.md` | Methodennotiz mit allen Kernzahlen (Notion-tauglich, Markdown) |
| `Abbildungen/` | 13 Grafiken (KF-Trend, Treiberbaum, Kontext-Effekt-Matrix, Diagnosekarte, Ankunft, Toröffnung …) |
| `Tabellen/` | Wichtigste Tabellen als CSV (UTF-8) |
| `Laufprotokoll.json` | Zeitpunkt, Paketversionen, MD5-Prüfsummen aller Eingabedateien (Nachvollziehbarkeit) |

### Zuordnung zum Arbeitsauftrag

| Auftrag | Umsetzung (Blätter in der Excel-Datei) |
|---|---|
| **A – Datenmodell & Abdeckungsmatrix** | `A1_mart_match`, `A2_dim_match`, `A3_dim_match_context`, `05_Abdeckung`, `06_Gemeinsame_Stichproben`, `07_Unmatched`, `08_Duplikate`, `10_Datenwoerterbuch`, `03_Importtests`, `04_Quelleninventar` |
| **B – Baseline & deskriptive Module** | Paket A: `A4`–`A8`; Paket B (Anwesenheit/Absatz): `B1`–`B11`; Paket C (Catering): `C1`–`C12`; Paket D (Ankunft): `D1`–`D11`; Abgleich mit Reto: `01_Reto_Abgleich` |
| **C – Kontext-Effekt-Matrix** | `K1_Kontext_Effekt_Matrix`, `K2_Modellguete`, `K3_Sensitivitaet`, `K4_LOSO_Folds`, `K5_Variablen_Einordnung` |
| **D – Diagnosekarte** | `K6_Diagnosekarte`, `K7_Diagnose_Muster` (Referenzlücken, keine Potenzialsumme) |
| **E – Übergabe** | Code (dieser Ordner), `Methodennotiz_Phase1.md`, `E1_Klaerungsfragen`, `E2_Phase2_Kandidaten`, Merchandise im Quelleninventar als «nicht geliefert» |

---

## 3. Ideen-Grundlage (`2. Modellierung/Ergebnisse_Ideen_Grundlage`)

Vertiefte Datenanalyse, aus der Simon und Reto Ideen entwickeln. Sie liefert **keine fertigen Ideen**, sondern je
Chancenfeld Befunde, Evidenzstärke, Rechenbausteine, Leitplanken-Check, Datenlücken und Leitfragen («Wie könnten wir …?»).

| Datei | Inhalt |
|---|---|
| `Ideen_Grundlage_FCSG.html` / `.pdf` | **Hauptprodukt** (offline, Grafiken eingebettet, rund 28 Seiten A4): Lesehilfe, 12 Kernbefunde, korrigierte Faustwerte, 9 Chancenfeld-Karten, Daten-Check von Retos 12 Ideen, Korrekturen Phase 1, Datenanfragen, Methodik. Das PDF entsteht über Chrome/Edge (headless), falls installiert. |
| `Ideen_Grundlage_FCSG.xlsx` | Alle Tabellen (rund 60 Blätter) plus **`Hebel_Rechner`** (gelbe Eingabezellen, echte Formeln, φ-Szenarien), **`Szenarien`** (eine Zeile je Idee), **`Ideen_Steckbrief`** (Vorlage), Chancenfelder, Reto-Check, Q1_Qualitaetspruefung |
| `Ideen_Grundlage_FCSG.md` | Kurzfassung für Notion (nur zulässige Aggregate, ohne Grafiken) |
| `Abbildungen/` | 17 Grafiken (PNG); die Zahlen dazu stehen jeweils im Excel (Blattname in der Bildunterschrift) |
| `QA_Ideen_Grundlage.csv` | Ergebnis der 18 automatisierten Prüfungen |

**Analysen (Paket `fcsg/ideen/`):**
- **Rechengrundlage** (`basis.py`): Saisonwerte 2025/26 und Ø 2023/24–2025/26, isolierte Hebelwerte nach Simons §12
  (No-Show mit φ = 0.6/0.8/1.0, Anwesende, Kauffrequenz, Ø Bon, KF), Abgleich mit Retos Faustwerten. `hebel_szenario()`
  ist die einzige Rechenquelle für Python und Excel.
- **Leere Plätze** (`noshow.py`): leere vergebene Plätze, Zweitmarkt je Spiel/Tribüne (CSV-Tarife «… Zweitmarkt» =
  Historie), Tribünen 2026/27 aus Abos bis Anpfiff + Einzeltickets − Zweitmarkt gegenüber Scans je Eingang (UEFA-Spiele
  als Kalibrierung), No-Show der Einzeltickets nach Kanal × Preis × Bestellgrösse.
- **Absatz** (`absatz.py`): regelbasierte Spieltypen mit Permutationstests und Cluster-Stabilität, Frühindikator T-7
  (Rolling Origin, konform kalibriertes 80 %-Band), Preisstruktur (deskriptiv, kein Preishebel).
- **Zeitfenster** (`zeitfenster.py`): Verweilzeit vor Anpfiff je Eingang, Einlass-Spitzen gegenüber Leser-Kapazität.
- **Konsum** (`konsum.py`): KF-Entwicklung (Frequenz × Ø Bon), Warenkorb je 100 Anwesende, Preis/Menge (Fisher),
  Alkohol-Proxy je Spiel aus dem MwSt-Mix des Kassenkanals Payfix (validiert), Kontextmodelle wie Phase 1,
  Durchsatz-Knick (Wild-Bootstrap), mobiler Verkauf, Kiesplatz × Wetter, φ-Evidenz.
- **Ausreisser, Randfelder, Reto-Check, Chancenfelder** (`ausreisser.py`, `randfelder.py`, `reto_check.py`, `chancen.py`).
- **Qualitätssicherung** (`qa_ideen.py`): Phase 1 bleibt unverändert (Fingerabdruck), keine ID-Spalten, kleine Zellen
  unterdrückt, keine Summen-/Potenzialzeile, Leitplanken-Pflichtfelder, Validierungen, Excel-Formeln = Python, HTML offline.

**So arbeitet ihr damit:** Kernbefunde lesen → Chancenfeld wählen → Leitfragen im Workshop nutzen → im Excel-Blatt
`Szenarien` grob beziffern (Hebel wählen, Annahme begründen) → `Ideen_Steckbrief` ausfüllen. **Hebel nie addieren**
(sie überlappen); CHF-Werte sind Caterer-Umsatz exkl. MwSt, kein Ertrag des Clubs.

---

## 4. Aufbau des Codes

```
Python_Auswertung/
├── run_all.py                    Startpunkt: lädt, verknüpft, analysiert, schreibt Ergebnisse
├── requirements.txt / pytest.ini
├── overrides/korrekturen.csv     belegte Korrekturen (Datum/Anpfiff) mit Begründung
├── overrides/artikel_basis.csv   Basis der Artikelauswertung je Saison (brutto/netto) mit Beleg
├── external/                     öffentliche Zusatzdaten (MeteoSchweiz, Resultate) als Cache + QUELLEN.md
├── scripts/externe_daten_aktualisieren.py
├── scripts/aenderungsprotokoll.py   Vergleich zweier Ergebnis-Arbeitsmappen (Blatt für Blatt)
├── tests/                        Einheiten- und Integrationstests (gemeinsame Daten-Fixture in conftest.py)
└── fcsg/
    ├── config.py                 Pfade, Scope, Konstanten (MwSt, Kapazität, Top-Gegner …)
    ├── sources/                  ein Modul pro Quelle: historie, catering, tickets, zutritt, kontext, extern
    ├── datamodel.py              dim_match, Faktentabellen, dim_match_context, Unmatched-/Duplikatreport
    ├── analysis/                 baseline (A), attendance (B), catering (C), arrival (D), models (Kontext/Diagnose), reto
    ├── mart.py, qa.py            mart_match, Abdeckung, Importtests, Quelleninventar
    ├── report/                   Excel, Grafiken, Methodennotiz, Klärungsfragen/Phase-2-Kandidaten, Änderungsprotokoll
    └── ideen/                    Ideen-Grundlage: Analysen (basis, noshow, absatz, zeitfenster, konsum, ausreisser,
                                  randfelder), reto_check, chancen, qa_ideen, stufe; bericht/ (HTML/PDF, Excel-Rechner,
                                  Markdown, Grafiken)
```

**Verknüpfungsregeln** (Auftrag Abschnitt 3): Join ausschliesslich über das Spieldatum, nie über das Gegner-Label;
erst jede Quelle auf Spielebene aggregieren, dann verbinden; pro Datum höchstens ein Pflichtspiel der Herren
(andere Events am selben Tag werden über den Wettbewerb getrennt).

**Korrekturen:** `overrides/korrekturen.csv` enthält sechs belegte Datums-/Anpfiffehler (z.B. Historie 24.08.2024 →
24.09.2024). Eine Korrektur greift nur, solange der dokumentierte Altwert noch in der Quelle steht – korrigiert Sandro
die Datei, erscheint ein Hinweis im Befundbericht. Neue Korrekturen einfach als Zeile ergänzen (Semikolon getrennt).

**Öffentliche Zusatzdaten:** Wetter zur Anpfiffzeit (MeteoSchweiz, Station St. Gallen, Stundenwerte) und Super-League-
Resultate (für Tabellenstand und Form vor dem Spiel, football-data.co.uk) liegen als Cache in `external/`.
Aktualisieren mit `python scripts/externe_daten_aktualisieren.py` (überträgt keine FCSG-Daten).

---

## 5. Methodik in Kürze

- **KPIs:** Anwesenheitsquote = IST/SOLL; KF = Umsatz/Public Netto = (Bons/Public Netto) × Ø Bon; Saisonwerte immer
  Summe/Summe. SOLL-Definition (Ticketsumme vs. Kapazitätswert) und IST-Qualität werden je Spiel als Flag geführt.
- **Kontextmodelle:** je Zielgrösse ein eigenes, sparsames Modell (Anwesenheitsquote, KF, Bons/Anwesende, Ø Bon,
  Frühankunft) mit Saison-Effekten und sechs vorab festgelegten Kontextvariablen; robuste Standardfehler (HC3);
  Validierung Leave-one-season-out gegen das Saisonmittel; sechs Sensitivitätsvarianten. Clubhebel werden nicht
  herauskontrolliert.
- **Diagnosekarte:** Erwartung je Spiel aus Leave-one-match-out-Schätzung, 80 %-Band; Diagnoselücke = erwartet −
  beobachtet; CHF nur als modellbasierte Referenzlücke je Spiel (keine Summe, kein Potenzialversprechen).
- **Natürliches Experiment Toröffnung:** Sektor D öffnet seit 02.04.2023 30 min früher → Differenz-in-Differenzen
  gegenüber A/B/C bei denselben Spielen.
- **Artikelauswertung:** Die Datei-Spalte «Umsatz Netto» enthält 2023/24–2024/25 Brutto-, 2025/26 Nettowerte. Alle
  Saisons werden einheitlich brutto gerechnet (MwSt-Klasse je Artikel; Basis in `overrides/artikel_basis.csv`).

**Version 1.1.0 (13.10.2026)** korrigiert gegenüber der Übergabe v1.0.1 die Codierung der Catering-Bemerkungen (mobiler
Verkauf, Plattform-Events, geschlossene Stände) und die Brutto/Netto-Basis der Artikelauswertung. Kontextmodelle, KPI und
Erwartungswerte sind unverändert. Vorher/Nachher: Blatt `00_Aenderungsprotokoll` und Methodennotiz.

Details, Zahlen, Grenzen und Klärungsfragen: siehe `Methodennotiz_Phase1.md`.

---

## 6. Häufige Probleme

| Problem | Lösung |
|---|---|
| `Nicht gefunden – Rohdatenordner …` oder `… Spielkontext-Tabelle` | Pfade mit `--daten` und `--kontext` angeben (Abschnitt 1) |
| `ImportError: Missing optional dependency 'python_calamine'` | `pip install -r requirements.txt` in der aktivierten Umgebung |
| Excel-Datei lässt sich nicht schreiben | Datei ist in Excel geöffnet – schliessen und erneut starten |
| Wetter/Tabellenstand fehlen | `python scripts/externe_daten_aktualisieren.py` (Internet nötig) |
| Test «Korrektur nicht angewendet» im Befundbericht | Quelle wurde korrigiert → Zeile in `overrides/korrekturen.csv` löschen |
| Befund «Basis der Umsatzspalte … nicht festgelegt» | Neue Saison in der Artikelauswertung → Zeile in `overrides/artikel_basis.csv` ergänzen (Beleg: Erlös je Einheit Bier, Summe vs. Payfix inkl./exkl.) |
| «kein PDF (Chrome/Edge nicht gefunden)» | `Ideen_Grundlage_FCSG.html` im Browser öffnen und als PDF drucken (A4, ohne Kopf-/Fusszeilen) |

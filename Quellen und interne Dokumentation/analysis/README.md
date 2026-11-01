# Quellen und interne Dokumentation/analysis/ – Analyse und Übergabe (Phase 1)

> **Seit 14.10.2026 ist Ralfs Rechenkern die Zahlenbasis (D-028)** – siehe `Baseline Analyse Rechnungen/Rechenkern/README_REPO.md` und
> `Baseline Analyse Rechnungen/run3_kontext-v5_2026-10-14/`. Dieser Ordner beschreibt Simons Pipeline (Bereinigung, Gegenrechnung, Run 1).

Dieser Ordner ist der Einstieg für alle, die die Analyse weiterführen. Ergebnisse:
**[01_baseline_erste_erkenntnisse.md](01_baseline_erste_erkenntnisse.md)** (Bericht mit Zahlen, Grafiken in `figures/`).
Interaktiv weiterarbeiten: **[Baseline Analyse Rechnungen/Notebooks_Archiv/01_baseline_hypothesen.ipynb](../../Baseline%20Analyse%20Rechnungen/Notebooks_Archiv/01_baseline_hypothesen.ipynb)**.

> Alle Zahlen sind **vorläufig** (Definitionen D-004/D-005 offen), aggregiert, nur Herren-Pflichtspiele und **vertraulich**
> (nur privates Projekt-Repo, D-024). Assoziationen sind keine Ursachen, und Residuen sind keine Potenziale.

## 1 Wie das Projekt funktioniert

```text
Rohdaten (lokal, nie im Repo)          C:\FCSG_Daten\raw\<Lieferung>\   + Spielkontext_Tabelle_FCSG_3.xlsx
        │  python -m fcsg.cli prepare-data --config config/project.local.yaml     (src/fcsg/prepare.py)
        ▼  Personenfelder nie gelesen · Frauen raus (D-016) · Schulferien recherchiert (D-021) · Summenerhalt
data/clean/<run_id>/  (18 bereinigte Tabellen, nicht im Repo; LATEST zeigt auf den neuesten Lauf)
        │  python -m fcsg.cli analyze --config config/project.local.yaml          (src/fcsg/analysis.py)
        ▼
Spieltabelle mart_match (1 Herren-Pflichtspiel pro Zeile)                         (src/fcsg/baseline.py)
  = Zuschauer-Historie (Spielkalender, SOLL/IST)
  + Catering (Umsatz, Public Netto, Bons) + Zutritt (Scans, Ankunft) + Tickets (Vorlauf, Eintritt)
  + Spielkontext (Gegner, Wetter, TV, Ferien …)  – je Quelle vorher aggregiert, 1:1 über Datum
        ▼
KPIs je Spiel/Saison · Reto-Abgleich · Hypothesen H1–H3, K1                       (src/fcsg/hypotheses.py)
        ▼
Laufordner <output_dir>/<run_id>/ (CSV, manifest.json, Excel mit Readback – ausserhalb des Repos)
Quellen und interne Dokumentation/analysis/01_baseline_erste_erkenntnisse.md + figures/  (Bericht, im Repo)    (src/fcsg/report.py)
```

Die drei Datenbasen laut Treiberbaum (Briefing `02_datenquellen_treiberbaum.md`) und ihr Schlüssel:

| Datenbasis | Tabellen in `data/clean/` | Ebene in der Spieltabelle |
|---|---|---|
| **Ticketing** | `attendance_history` (SOLL/IST, Ausverkauft), `tickets_single_*` (25/26+), `tickets_hist_*` (21/22–24/25, inkl. Eintrittsfeld), `season_ticket_snapshot_agg` | Spielkalender, No-Show, Vorlauf, Eintrittsquote |
| **Zutritt** | `access_match_summary`, `access_sector_minute`, `access_reader`, `access_coding` | Scans, Vollständigkeit, Ankunftsanteile |
| **Catering** | `catering_match`, `catering_season_summary`, `kiesplatz_event_stand`, `article_season` | Umsatz, Public Netto, Bons, KF, Ø Bon |
| Kontext | `context_match` | Gegner, Tabelle, Form, Wetter, TV, Ferien, Feiertag |

Verknüpfung über **Spieldatum** (D-007). Die Prüfungen laufen bei jedem Lauf mit: Join-Kardinalität, Summenerhalt je Quelle,
Identität KF = Bonsrate × Ø Bon, Abgleich mit dem Quell-Tab «Entwicklung» (Excel-Blatt «Qualität»).

## 2 Neu rechnen (z. B. nach neuer Datenlieferung)
1. Rohdaten unter `C:\FCSG_Daten\raw\<Lieferdatum>_<Absender>\` ablegen (D-015). Eigene `config/project.local.yaml`
   anlegen (nicht im Repo, Vorlage in `config/README.md`).
2. VS Code → «Task ausführen» → **FCSG: Echte Daten bereinigen/aggregieren (data/clean)**.
3. **FCSG: Baseline-Analyse (echte Daten) – Bericht + Excel**. Der Bericht in diesem Ordner wird überschrieben;
   das Excel landet im `output_dir` der lokalen Config.
4. Tests: **FCSG: Tests ausführen** (nur künstliche Daten).

## 3 Mögliche Baseline-Outputs (Ausbaustufen)

| Output | Stand | Datenbasis |
|---|---|---|
| Saison-Baseline: Anwesenheit, No-Show, KF brutto/netto, Bonsrate, Ø Bon | ✅ vorhanden | Historie + Catering |
| Spiel-Baseline mit Verteilungen und Ausreissern (z. B. Top/Flop-KF je Saison) | 🟡 Daten da, Darstellung offen | `mart_match` |
| Wettbewerbsvergleich Liga/Cup/UEFA | 🟡 Daten da | `competition_group` |
| Ankunftskurven je Sektor (Minutenprofil) | 🟡 Daten da (vollständiger Zutritt) | `access_sector_minute` |
| Ticket-Vorlaufkurven (kumulierter Verkauf vs. Tage vor Spiel) | 🟡 Daten da | `tickets_*_leadtime` |
| Standumsätze Kiesplatz / Verkaufsstellen ab 25/26 | 🟡 Daten da, nicht nach Sektor | `kiesplatz_event_stand`, `catering_match` |
| Sortimentsmix je Saison (Alkohol/Food/alkoholfrei) | 🟡 nur Saisonsummen | `article_season` |
| Deckungsbeitrag je Spiel / je Anwesendem | 🔴 Kostendaten fehlen (D-003) | Anfrage Sandro |
| Kontextmodell (erwartet vs. beobachtet, Diagnosekarte) | 🔴 erst nach Baseline-Freigabe | AA S. 8–9 |

## 4 Hypothesen – Stand und nächste Schritte

| ID | Verknüpfung | Kurzfassung | Stand (vorläufig) |
|---|---|---|---|
| H1 | Ticketing × Catering | Umsatz wächst überproportional mit Zuschauern | siehe Bericht §5 |
| H2 | Zutritt × Catering | Frühe Ankunft → mehr Bons je Public | siehe Bericht §5 |
| H3 | Ticketing × Zutritt | Kurzfristig gekaufte Tickets werden häufiger genutzt | siehe Bericht §5 |
| K1 | Kontext → Baseline | Kontext hängt mit Anwesenheit, IST und KF zusammen | siehe Bericht §6 |
| H4–H9 | diverse | noch nicht getestet | Liste in Bericht §7; Vorlage im Notebook §8 |

**Regeln für neue Tests** (CLAUDE.md, AA): Werte innerhalb der Saison zentrieren (Preis- und Trendeffekte), n und
Stichprobe nennen, Konfidenzintervall statt nur Punktwert, keine Kausalsprache, keine Lücken von KF, Bonsrate und Ø Bon
addieren, fehlende Werte nie als 0. Neue Tests als Funktion in `src/fcsg/hypotheses.py` + Test mit künstlichen
Daten in `tests/test_hypotheses.py`; erst dann in den Bericht aufnehmen.

## 5 Offene Punkte (siehe `Quellen und interne Dokumentation/decisions.md`)
- D-004/D-005: Definitionen SOLL/IST/Public Netto, Umsatzbasis → Sandro.
- D-003: Kosten-/Margendaten für den Deckungsbeitrag → Sandro.
- D-023: Bestätigung von FCSG zur lokalen Verarbeitung.
- Datenlücken: Zutritt 24/25, Bons vor 23/24, Catering 23/24 (Simons Parser überspringt 27.09.2023; Ralfs Kern liest es); die 6 Kontextspiele 25/26 sind seit Kontexttabelle v5 ergänzt.

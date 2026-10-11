# Datendictionary – bereinigte echte Daten (`data/clean/<run_id>/`)

Erzeugt mit `python -m fcsg.cli prepare-data --config config/project.local.yaml` (Modul `src/fcsg/prepare.py`,
Datenmodus `release_aggregates`, D-001 c). `data/` ist von Git ausgeschlossen. Der letzte Lauf steht in
`data/clean/LATEST`; jeder Lauf hat `manifest.json` (Input-Hashes, Zeilen, Prüfungen) und `quality_checks.csv`.

**Grundsätze:** Werte werden so übernommen, wie die Quelle sie liefert. Von der Quelle berechnete Kennzahlen
tragen den Suffix `_reported` und sind **nicht** fachlich freigegeben. `_gross` = inkl. MwSt, `_net` = exkl. MwSt.
Leere Zellen bleiben leer (nie 0). Personenbezogene Felder sind in keiner Tabelle enthalten.
**Scope (D-016, ab Lauf vom 11.10.2026):** Frauen-Daten sind in keiner Tabelle mehr enthalten (Frauen-Dateien nicht gelesen,
Frauen-Events entfernt; Anzahlen in `quality_checks.csv`, `D016-*`). Angaben wie «Frauen» unten beschreiben frühere Läufe.

## Aggregat-Quellen (bereinigt übernommen)

| Tabelle | Quelle | 1 Zeile = | Wichtigste Spalten |
|---|---|---|---|
| `context_match` | Spielkontext_Tabelle_FCSG_3.xlsx (Projektteam), Saison-Tabs | Heimspiel 22/23–26/27 | `match_date`, `season`, `kickoff`, `competition(_group)`, `opponent`, `table_rank/points_fcsg/opp` (vor Spiel), `form_*_points`, `tv_free_srf`, `temp_day_mean/min/max_c`, `precip_day_mm`, `wind_day_kmh` (**Tageswerte**), `school_holiday` (vor 26/27 recherchiert, D-017 b/D-021; Herkunft in `school_holiday_source`, Original in `school_holiday_team`, dazu `school_holiday_research`, `school_holiday_period`), `public_holiday`, `parallel_event`, `result_post_match` (**nicht als Prädiktor**) |
| `attendance_history` | Ticketing-Zuschauerzahlen-Historie.xlsx | Event (alle Wettbewerbe seit 2008) | `soll`, `ist`, `ist_vip`, `ist_guests`, `secondary_market`, `sold_out`, `no_show_rate_reported`, `remark`, `competition_group` |
| `catering_match` | Umsatz Public Catering ab 18-19, Saison-Tabs (linker Block) | Spiel/Event | `event_class` (fcsg_herren / fcsg_frauen / anderes_event), `public_attendance`, `transactions`, `revenue_total_gross/net`, `kf_gross/net_reported`, `avg_receipt_*_reported`, Kanalumsätze `rev_*` (Payfix, Just Eat, Pick-up, extern, nicht verbucht), `weather_text`, `remark` |
| `catering_season_summary` | Tab «Entwicklung» | Wettbewerb × Saison | Saisonsummen laut Quelle (Abgleich) |
| `kiesplatz_event_stand` | Abrechnung Kiesplatz 21/22–26/27 | Event × Stand × Kennzahl (lang) | `stand` (inkl. «TOTAL»), `metric` (`brutto_total`, `netto_total`, `brutto_<satz>pct`, `netto_<satz>pct_anteil80/20`), `value`, `sheet` (Haupt- vs. Detailblatt – nicht addieren) |
| `article_season` | Artikelauswertung Meisterschaft | Abschnitt (Gruppe/Artikel) × Saison | `qty_total`, `qty_avg_per_match`, `revenue_net_total`, `revenue_net_avg_per_match`, `revenue_share`, `n_matches_reported` |

## Personenbezogene Quellen – nur Aggregate

| Tabelle | Quelle | 1 Zeile = | Zählgrössen |
|---|---|---|---|
| `access_match_summary` | 4 Zutrittsdateien | Datei × Spieldatum | `scans`, `n_distinct_tickets` (Ticketschlüssel nur intern gezählt), `scans_per_ticket`, `first/last_scan`, `n_readers`, `venue_messages` |
| `access_sector_minute` | dito | Datei × Datum × Sektor (A/B/C/D/HH) × Uhrzeit-Minute | `scans` |
| `access_reader` | dito | Datei × Datum × Leser | `scans`, `first/last_scan` |
| `access_coding` | dito | Datei × Datum × Sektor × `coding` | `scans` (Bedeutung «Coding» offen) |
| `tickets_single_agg` | Ticket-CSVs 25/26–26/27 | Spiel × Tribüne × Block × Tarif × Kanal × Versandart | `n_tickets`, `revenue_chf`, `n_price_missing` |
| `tickets_single_leadtime` | dito | Spiel × Tribüne × Kanal × Vorlauftage | `n_tickets`, `revenue_chf` |
| `tickets_single_purchase_size` | dito | Spiel × Tickets pro Kauf (1–10+) | `n_purchases` (aus Rechnungsnummer gezählt) |
| `season_ticket_snapshot_agg` | Saisonabos Herren (Stand 30.09.2026) und Frauen | Tribüne × Block × Tarif × Kanal × Versandart × Kaufmonat | `n_seats`, `revenue_chf` |
| `tickets_hist_agg` | Einzeltickets-Exporte 21/22–24/25 | Event × Preiskategorie × Kanal × Platzgruppe × Tarif × Versand × Status × `entered` | `n_rows`, `n_tickets`, `revenue_chf` |
| `tickets_hist_leadtime` | dito | Event × Kanal × Platzgruppe × Vorlauftage | `n_tickets`, `n_entered` |
| `tickets_hist_entry_minute` | dito | Event × Eintritts-Minute | `n_entries` |

**Nicht exportiert / nie gelesen:** Kunde, Kundenname, Anrede, Geburtstag, Alter, Geschlecht, Postleitzahl, Land,
Privatperson, Auftrag, Position, Reihe/Sitz/Platznummer, Barcode, Ticketnummer, KundenNr, Interne Nummer,
TicketData, Seatinfo, UTId (nur intern gehasht zum Zählen), Rechnung (nur intern gehasht zum Zählen).

## Abdeckung

| Tabelle | 1 Zeile = | Inhalt |
|---|---|---|
| `match_coverage` | Datum ab 01.07.2021 | je Quelle Wert und `has_<quelle>`: Kontext, Historie (ohne Frauen), Catering (FCSG Herren), Zutritt (Herren), Ticket-CSV (Herren), Einzeltickets (Spiele); `n_sources` |

## Analyse-Ausgaben (`fcsg.cli analyze`, Laufordner `<output_dir>/<run_id>/`)

Vorläufige Arbeitsdefinitionen D-025; Formeln im Excel-Blatt «Definitionen» bzw. `fcsg.baseline.KPI_DEFINITIONS_REAL`.

| Datei | 1 Zeile = | Wichtigste Spalten |
|---|---|---|
| `mart_match.csv` | Herren-Pflichtspiel ab 21/22 | Schlüssel `match_id`, `match_date`, `season`, `competition_group`; Ticketing `soll`, `ist`, `sold_out`, `guest_sector_note`, `single_tickets_n`, `single_share_lead_le1`, `hist_rows`, `hist_entered`, `single_entry_rate`; Catering `public_attendance`, `receipts`, `revenue_gross_chf`, `revenue_net_chf`; Zutritt `access_source_file`, `scan_count`, `share_arrived_45min_before`, `share_last_15min`, `share_after_kickoff`, `arrival_median_min_before`, `access_complete`; Kontext `opponent`, `table_rank_*`, `form_*_points`, `tv_free_srf`, `temp_day_mean_c`, `precip_day_mm`, `wind_day_kmh`, `school_holiday`, `public_holiday`, `parallel_event`, `has_context`; KPIs `attendance_rate`, `no_show_rate`, `no_show_abs`, `kf_gross_chf`, `kf_net_chf`, `receipts_per_public`, `avg_receipt_gross_chf`, `avg_receipt_net_chf`, `scan_vs_ist_rate`, `public_vs_ist_rate` |
| `season_summary.csv` | Saison | Summen und gewichtete Quoten (Σ/Σ) mit Stichprobe je KPI (`n_catering`, `n_receipts`, `n_access_complete`) |
| `coverage.csv` | Saison (+ Total) | `has_*` je Quelle, `sample_H1/H2/K1` |
| `reto_comparison.csv` | Kennzahl | `reto_value`, `our_value`, `abs_diff`, `rel_diff`, `status`, `note` |
| `source_total_check.csv` | Saison | Spielzeilen vs. Tab «Entwicklung» |
| `hypotheses.csv` | Hypothese | `statement`, `data_basis`, `n`, `method`, `estimate`, `ci_low`, `ci_high`, `status`, `limitations`, `next_steps` |
| `h1_sold_out.csv`, `h2_correlations.csv`, `h3_leadtime.csv`, `context_associations.csv` | Detailtabellen je Hypothese | siehe Bericht `docs/analysis/01_baseline_erste_erkenntnisse.md` |

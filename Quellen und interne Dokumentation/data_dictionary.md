# Datendictionary (technischer Vertikalschnitt)

**Status:** gilt für die künstliche Fixture `synthetic_mini`. Spaltennamen sind technische Platzhalter;
die echten Quellspalten (z. B. «SOLL», «Public Netto», «TransactionTime») werden erst nach Freigabe des
Datenmodus über ein Mapping zugeordnet. Das «FCSG_Daten-Handbuch» liegt nicht vor.

## Inputs (Fixture)

### `attendance_match.csv` – 1 Zeile = 1 Heimspiel (entspricht `fact_attendance_match`, AA S. 4)
| Spalte | Typ | Bedeutung | Einheit |
|---|---|---|---|
| data_origin | text | Pflichtmarker `SYNTHETIC_FIXTURE_NOT_CLUB_DATA` | – |
| match_date | Datum YYYY-MM-DD | Spieldatum, Join-Schlüssel | lokal Europe/Zurich |
| season, competition, opponent_label, kickoff_local | text | Saison, Wettbewerb, Gegner-Label (nicht als Schlüssel!), Anpfiff HH:MM | – |
| soll | Zahl | Platzhalter für SOLL (Definition offen, D-004) | Personen/Tickets |
| ist | Zahl, darf fehlen | Platzhalter für IST | Personen |
| ist_vip, ist_guests | Zahl, darf fehlen | IST VIP, IST Gäste | Personen |

### `catering_match.csv` – 1 Zeile = 1 Spiel oder Event (entspricht `fact_catering_match`, AA S. 5)
| Spalte | Typ | Bedeutung | Einheit |
|---|---|---|---|
| event_type | text | `match` oder anderes Event (z. B. `public_viewing`) – nur `match` wird verbunden | – |
| event_label | text | Freitext | – |
| public_attendance | Zahl, darf fehlen | Platzhalter «Public-Anwesende / Public Netto» (= Zuschauer ohne VIP laut Sichtung) | Personen |
| receipts | Zahl | Bons/Transaktionen | Anzahl |
| revenue_gross_chf / revenue_net_chf | Zahl | Umsatz inkl. / exkl. MwSt (Fixture: Netto = Brutto × 0.9, willkürlich) | CHF |

### `access_scans.csv` – 1 Zeile = 1 erlaubter Scan (entspricht `fact_access`, AA S. 5)
| Spalte | Typ | Bedeutung | Einheit |
|---|---|---|---|
| minutes_before_kickoff | Zahl | Minuten vor Anpfiff (negativ = nach Anpfiff) | Minuten |
| reader_sector | text | Sektor (in echten Daten erst via Leser→Sektor-Mapping) | – |

## Output `mart_match` – 1 Zeile = 1 Heimspiel
Zusätzlich zu den Inputspalten: `match_id` (`M` + JJJJMMTT), `scan_count`, `arrival_median_min_before`,
`share_arrived_45min_before`, `share_last_15min`, Verfügbarkeitsflags `has_attendance`, `has_catering`,
`has_access` sowie die KPIs:

| KPI | Formel | Quelle |
|---|---|---|
| attendance_rate | IST / SOLL | AA S. 5 |
| no_show_rate | 1 − IST / SOLL | AA S. 5 |
| no_show_abs | SOLL − IST | AA S. 5 |
| kf_gross_chf, kf_net_chf | Umsatz brutto bzw. netto / Public-Anwesende | AA S. 5 |
| receipts_per_public | Bons / Public-Anwesende (≠ Kaufquote) | AA S. 5–6 |
| avg_receipt_gross_chf, avg_receipt_net_chf | Umsatz / Bons | AA S. 5 |
| scan_vs_ist_rate | Scans / IST − 1 (Scans ≠ Besucher) | AA S. 6 |

Regeln: Nenner ≤ 0 oder fehlend → leer (NaN). Fehlende Werte werden nie zu 0.

## Output `season_summary` – 1 Zeile = 1 Saison
`n_matches`, `n_attendance`, `n_catering`, `n_access` (Stichprobe je KPI), `attendance_rate_weighted` = Σ IST / Σ SOLL,
`kf_gross_weighted_chf` / `kf_net_weighted_chf` = Σ Umsatz / Σ Public-Anwesende, `avg_receipt_gross_weighted_chf`,
`no_show_abs_sum`. `kf_gross_unweighted_mean_chf` nur zur Demonstration des Unterschieds – **nicht verwenden** (AA S. 6).

# Dateninventar und Abdeckung – echte Daten (Stand 10.10.2026)

- **Lieferung:** `C:\FCSG_Daten\raw\20261003_Input Sandro\` (50 Dateien) + `Spielkontext_Tabelle_FCSG_3.xlsx` (Projektteam)
- **Strukturinventar:** `C:\FCSG_Daten\outputs\inventory_20261010T184608\` (Modus `structure_only`, keine Zellinhalte)
- **Bereinigte Daten (aktuell):** `data/clean/20261011T191727_clean_33fc/` (11.10.2026, Modus `release_aggregates`, 18 Tabellen,
  **nur Herren** gemäss D-016). Alle 38 Prüfungen OK: Summenerhalt für 1 046 015 Scans, 180 167 Tickets (25/26–26/27),
  488 293 Einzelticket-Zeilen (21/22–24/25; danach 134 Frauen-Zeilen entfernt), 13 052 Abo-Sitze; keine Ausgabespalte mit
  Personenbezug. Schulferien vor 26/27 durch Recherche ersetzt (76 Spiele, **0 Abweichungen** zu den Teamwerten;
  Gegenprobe 26/27: 14 Spiele, 0 Abweichungen).
- Vorheriger Lauf `20261010T190529_clean_a4d4` (inkl. Frauen, 20 Prüfungen) ist überholt.

Alle Zahlen unten sind **Datenbefunde, keine fachlich freigegebenen Kennzahlen** (Definitionen D-004/D-005 offen).

## 1. Quellen

| Bereich | Datei(en) | Zeitraum | Ebene | Personenbezug → Behandlung |
|---|---|---|---|---|
| Ticketing | Zuschauerzahlen-Historie | 2008–26/27 (401 Events) | Event | keiner → übernommen |
| Ticketing | Einzeltickets_2021-22 … 2024-25 (je 2–3 Tabs à 65 000 Zeilen) | 21/22–24/25 | Ticket | Name, Anrede, Geburtstag, Alter, Geschlecht, PLZ, Land, Kunde → **nicht gelesen**; nur Aggregate |
| Ticketing | 33 Ticket-CSVs (Herren MS, Europacup, Frauen) | 25/26–26/27 | Ticket | KundenNr, Rechnung, Barcode, Reihe/Sitz → nicht exportiert; Aggregate |
| Ticketing | Saisonabos Herren (30.09.2026), Frauen | 26/27 | Abo-Sitz | dito |
| Zutritt | ErlaubteZutritteHerren.xlsx | 25/26–26/27 | Scan | UTId/TicketData/Seatinfo → nicht exportiert; Aggregate |
| Zutritt | zugangsdaten_herren_inhouse.csv (**ohne Kopfzeile**) | 22/23–23/24 | Scan | dito |
| Zutritt | zugangsdaten_herren_alteSaisons.txt | 24/25 (+ Reste 23/24) | Scan | dito |
| Zutritt | zugangsdaten_frauenequipe_alleSpiele.txt | 23/24–26/27 | Scan | dito |
| Catering | Umsatz Public Catering ab 18-19 (9 Saison-Tabs + «Entwicklung») | 18/19–26/27 | Event | keiner → übernommen; **Layout je Saison verschieden** |
| Catering | Abrechnung Kiesplatz 21-22 … 26-27 (je 2 Blätter) | 21/22–26/27 | Event × Stand | keiner |
| Catering | Artikelauswertung Meisterschaft | 23/24–26/27 | Gruppe/Artikel × Saison | keiner |
| Kontext | Spielkontext_Tabelle_FCSG_3.xlsx | 22/23–26/27 (90 Spiele, 7 noch nicht gespielt) | Heimspiel | keiner |

## 2. Abdeckung Herren-Heimspiele (Pflichtspiele, gespielt bis 10.10.2026)

| Saison | Heimspiele | Kontext | Historie | Catering | Zutritt | Zutritt vollständig (±5 % IST) | Ticket-CSV | Einzeltickets-Export | Catering mit Bons |
|---|---|---|---|---|---|---|---|---|---|
| 2021/22 | 19 | 0 | 19 | 19 | 0 | 0 | 0 | 18 | 0 |
| 2022/23 | 19 | 19 | 19 | 18 | 19 | 16 | 0 | 19 | 0 |
| 2023/24 | 19 | 19 | 19 | 18 | 19 | 17 | 0 | 19 | ja |
| 2024/25 | 25 | 24 | 24 | 24 | 24 | **9** | 0 | 17 | ja |
| 2025/26 | 20 | **14** | 20 | 20 | 20 | 20 | 18 | 0 | ja |
| 2026/27 | 7 | 7 | 7 | 7 | 7 | 7 | 7 | 0 | ja |

Gemeinsame Stichprobe **Historie + Catering + Kontext: 80 Spiele**; zusätzlich mit vollständigem Zutritt: **62 Spiele**.
«Catering mit Bons»: Anzahl Transaktionen erst **ab 23/24** vorhanden → Zerlegung KF = Bonsrate × Ø Bon nur ab 23/24.

## 3. Abgleich mit Retos Sichtung (Datenquellen-PDF)

| Aussage im PDF | Befund in den Daten | Status |
|---|---|---|
| Scans Ø 0.4 % unter IST (S. 3) | 25/26: Median −0.1 %, Mittel −0.5 %; 26/27: −0.3 % | bestätigt (für 25/26–26/27) |
| ~13 000 Abo-Sitze (S. 2) | 13 052 Abo-Sitze Herren | bestätigt |
| Eintritt nur 21/22, 22/23 gut befüllt; 23/24 teilweise; 24/25 leer (S. 2) | 89 % / 87 % / 50 % (0–89 %) / 0 % | bestätigt |
| Alkohol 54 % (23/24) → 49 % (25/26), Food 33 %, alkoholfrei 15 % (S. 4) | 53.5 % → 48.6 %, Food 33.2 %, alkoholfrei 15.4 % | bestätigt |
| Public Netto = Zuschauer ohne VIP (S. 3) | Public Netto − (IST − VIP): Median −24, Spanne −130 bis +259 (51 Spiele) | annähernd, nicht exakt → Definition klären |
| KF, Bons 0.95, Ø Bon 16.70 (S. 4) | noch nicht nachgerechnet | nächster Schritt (Baseline) |

## 4. Auffälligkeiten und Datenqualität

1. **Spielkontext 25/26 unvollständig:** 6 Heimspiele fehlen (11.02., 14.02., 28.02., 08.03., 17.03., 06.04.2026); sie sind in Historie, Catering, Zutritt und Ticket-CSVs vorhanden. 21/22 ist nicht enthalten (vom Auftrag auch nicht verlangt).
2. **Datumskonflikte:** (a) Servette: Kontext/Historie 25.01.2026, Ticket-CSV-Datei `20260126_MS21_SFC`. (b) 24.08.2024 nur in der Historie, 24.09.2024 in Kontext, Catering, Zutritt und Einzeltickets → vermutlich Tippfehler in der Historie.
3. **Zutritt 24/25 unvollständig:** nur 9 von 24 Spielen mit plausibler Scanzahl; die übrigen haben nur einzelne Scans. 22/23: 3 Spiele, 23/24: 2 Spiele deutlich unter IST.
4. **Scans pro Ticket = 1.00:** keine Mehrfachscans im Datensatz (Mehrfacheintritt offenbar nicht enthalten oder schon gefiltert).
5. **Feld «Coding»** (6 Codes, z. B. 270 = 77 % der Scans): Bedeutung unbekannt – möglicherweise Ticket-Typ (Abo/Einzel) → wäre für Ankunft nach Ticket-Typ wertvoll.
6. **Zwei Stadionnamen:** «kybunpark» und bei 9 Spielen aus `ErlaubteZutritteHerren` (25/26–26/27) «Berit Sitterstadion» (Begrüssungstext) – Umbenennung bestätigt (Reto, 02.11.2026; D-044): Das Stadion heisst heute «Berit Sitterstadion». Nicht geprüft, ob sich die Leser unterscheiden.
7. **Einzeltickets-Exporte:** nur Status «Aktuell/verkauft» → Stornos/Rückgaben nicht enthalten. Pro Spiel zusätzlich eine «+1 Minute»-Veranstaltung mit ~100 Tickets (separates Kontingent); Nicht-Spiel-Events (Mitgliedschaft, Testspiel, Kids Camp) als `is_match = False` getrennt.
8. **Spielkontext Schulferien:** für alle Saisons Ja/Nein befüllt, laut Anleitung aber nur 26/27 recherchiert → Team klären, ob Werte vor 26/27 verlässlich sind.
9. **Catering:** 15 Länderspiele (WEURO 2025), 57 «Diverse Events», 5 Spiele anderer Clubs → als `anderes_event` getrennt; 36 Frauen-, 2 U21-Spiele separat. Einzelne KF-Zellen nicht numerisch (Events ohne Zuschauerzahl).
10. **Kiesplatz:** MwSt-Sätze 2.5/7.7 % bis 23/24, 2.6/8.1 % ab 24/25; Haupt- und Detailblatt nicht addieren.
11. **Historie:** 2 Zeilen ohne Datum; 17 Formelzellen ohne gespeicherten Wert (werden als fehlend gelesen).
12. **Frauen-Daten** (Tickets, Zutritt, Catering, Abos) sind enthalten → Scope-Entscheid D-016.

## 5. Klärungsfragen an Sandro (datenbezogen, ergänzend zu AA S. 10–11)

1. Was bedeutet «Coding» in den Zutrittsdaten? Lässt es sich Abo/Einzel/Gast/VIP zuordnen?
2. Gibt es einen vollständigen Zutrittsexport für 24/25?
3. Sind Bons/Transaktionen vor 23/24 verfügbar?
4. Ist «Zuschauerzahlen Public Netto» = IST − VIP oder anders abgegrenzt?
5. Datum Servette-Spiel (25. oder 26.01.2026) und 24.08. vs. 24.09.2024 in der Historie.
6. ~~«Berit Sitterstadion» = Umbenennung des kybunpark?~~ Geklärt: ja (Reto, 02.11.2026; D-044).

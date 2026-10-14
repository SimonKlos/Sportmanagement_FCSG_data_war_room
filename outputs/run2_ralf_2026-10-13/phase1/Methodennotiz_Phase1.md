# Methodennotiz Phase 1 – Datenverknüpfung & Kontextbereinigung
*FCSG «Untapped Business» · Auswertung v1.1.0 · erstellt 2026-10-13 19:06:02 · Datenstand: letztes Spiel mit IST 12.09.2026*

> Umsetzung des «Arbeitsauftrags Modellierung» (Pakete A–E) auf Basis von Retos Datenquellen-Übersicht. Alle Zahlen stammen aus den Projektdateien und werden beim Lauf von `run_all.py` neu berechnet. Ausgegeben werden nur Aggregate; Personenfelder werden beim Einlesen verworfen.

## 0. Kurzfassung (das Wichtigste in 11 Punkten)

1. **Datenbasis:** 108 gespielte Pflichtspiele der Herren 2021/22–2026/27 sind über das Datum verknüpft (Historie, Catering, Tickets, Zutritt, Kontext). 6 Datums-/Anpfiffehler in den Quellen wurden belegt korrigiert (Joins laufen nur über das Datum).
2. **Retos Zahlen sind reproduziert** (14 von 16 Aussagen bestätigt, Rest präzisiert/erweitert). Wichtigste Präzisierung: Die Umsatz-Zuschauer-Elastizität liegt auf 96 Spielen bei 1.01 (95 %-KI 0.92–1.10) statt 1.14 – mehr Zuschauer bringen proportional mehr Umsatz, kein Skaleneffekt.
3. **Ältere Zutrittsdaten sind bereits geliefert:** 71 Spiele mit vollständiger Ankunftskurve statt 27 (22/23, 23/24, 2025er-Teil 24/25, 25/26, 26/27).
4. **Kundenfranken:** 14.51 CHF exkl. MwSt (alle Pflichtspiele 25/26, Summe/Summe) = Antragswert 14.50. Meisterschaft inkl. MwSt: 13.68 (21/22) → 15.27 (25/26).
5. **KF-Treiber:** Innerhalb einer Saison erklärt der Ø Bon 50 % und die Bons je Anwesendem 39 % der KF-Streuung – beide Hebel (Frequenz und Warenkorb) zählen.
6. **Kontext wirkt messbar** (10 belastbare Effekte): Top-Gegner (FCB, YB, FCZ) → Anwesenheitsquote +3.5 Pp., Abendspiel (Anpfiff ab 20 Uhr) → Anwesenheitsquote -4.1 Pp., Temperatur bei Anpfiff → Anwesenheitsquote +1.4 Pp., Abendspiel (Anpfiff ab 20 Uhr) → Kundenfranken exkl. MwSt +6.8 %, Temperatur bei Anpfiff → Kundenfranken exkl. MwSt +3.6 %, Abendspiel (Anpfiff ab 20 Uhr) → Bons je Public-Anwesendem +4.6 %, Werktag (Mo–Fr) statt Wochenende → Ø Bon exkl. MwSt -4.0 %, Temperatur bei Anpfiff → Ø Bon exkl. MwSt +2.3 %.
7. **Kontext erklärt** 42 % der saisonbereinigten Streuung der Anwesenheitsquote und 33 % beim Kundenfranken; out-of-sample (Leave-one-season-out) besser als das Saisonmittel.
8. **No-Show steckt im «Rest» (≈ Abos):** Einzeltickets 9 %, Rest 22 %–29 % (21/22–22/23). Bei Einzeltickets fallen Grossbestellungen ab 10 Tickets (26 %), Gratis/Promo (16 %) und Inhouse-Verkäufe (25 %) auf.
9. **Toröffnung ist ein messbarer Hebel:** Tribünen A/B/C öffnen rund 61 min, die Fankurve 91 min, Hospitality 119 min vor Anpfiff. Seit Sektor D 30 min früher öffnet (02.04.2023), kommen D-Fans 23 min früher (95 %-KI 19–26) – die Konsumwirkung ist noch offen (Phase 2).
10. **Kiesplatz ist im Catering-Total enthalten** (21/22 frankengenau belegt) – nie addieren. Anteil je Spiel im Median 8 %–12 %.
11. **Diagnosekarte:** 6 Spiele liegen beim KF unter, 12 über dem 80 %-Erwartungsband. Das sind Prüfkandidaten für Phase 2, kein realisierbares Potenzial (keine Summenbildung).

## Änderungen in Version 1.1.0 (gegenüber der Übergabe v1.0.1)

Bei der vertieften Analyse für die Ideen-Grundlage wurden zwei Codier- bzw. Basisfehler gefunden und korrigiert. Kontextmodelle, KPI und Erwartungswerte sind davon nicht betroffen (die Merkmale sind keine Modellvariablen).

| Bereich | Änderung | vorher (v1.0.1) | nachher (v1.1.0) |
|---|---|---|---|
| Bemerkungs-Codierung: mobiler Verkauf | «Alle Stände geöffnet ausser Runner B, C, D», Runner in «folgende Stände waren geschlossen: …» und «nur einer … im Einsatz» wurden als «Runner im Einsatz» gelesen. Neu zählen nur ausdrückliche Angaben je Sektor (Funktion mobiler_verkauf; Kassenzuteilungen wie «Runner C = Stand C4» sind keine Einsatzangabe). | 13 Pflichtspiele mit «Runner/Bauchläden nicht im Einsatz» | 23 Pflichtspiele «ganz oder teilweise nicht im Einsatz» |
| Bemerkungs-Codierung: Plattform-Event | «Side Event 1: BBQ S1» ist eine Kassenzuteilung und wurde als Plattform-Event gezählt, ebenso «mit Glühwein». Neu zählen nur Programm/Zusatzangebote (Winterzauber, Family/Kids Day, Raclette, Suppe, Sittermarsch); die Espen Kids Days 16.04.2023 und 02.09.2023 werden neu erkannt. | 18 Pflichtspiele | 8 Pflichtspiele |
| Bemerkungs-Codierung: Stände geschlossen | «Alle Stände offen ausser Bier S2» (12.12.2024) und «… ausser Bierbar A3, Bierbar C …» (27.08.2026) gelten neu als geschlossene Stände; die Schreibweise «Allä Stände offen» wird erkannt. | 15 Pflichtspiele | 17 Pflichtspiele |
| Folge: wiederkehrende Muster (K7) | Mit korrekter Codierung liegen Spiele ohne (vollständigen) mobilen Verkauf beim KF unter der Kontexterwartung; 19.02.2023 (FC Luzern) gilt neu als «möglicher Clubhebel» statt «ungeklärt». | n=9, KF −2.4 % (KI90 −6.5 bis +1.8) | n=15, KF −3.4 % (KI90 −6.3 bis −0.6) |
| Artikelauswertung brutto/netto | Die Spalte «Umsatz Netto» enthält 2023/24–2024/25 Bruttowerte, 2025/26 Nettowerte (Bier 4dl je Einheit 6.00 → 5.96 → 5.54, × 1.081 = 5.98 brutto). Neu einheitlich brutto (overrides/artikel_basis.csv; MwSt-Klasse je Artikel, 2025/26 × 1.081 bzw. × 1.026). Die Klärungsfrage «Bier −7.1 %» entfällt (kein Preiseffekt, sondern Basiswechsel). | Alkoholanteil 53.5 % (23/24) → 48.6 % (25/26); Bier je Einheit −7.1 % | Alkoholanteil 53.5 % (23/24) → 49.9 % (25/26), beide brutto; Bier je Einheit stabil (CHF 5.96–6.00 brutto) |
| Importtests | Test «Artikelsumme vs. Catering exkl. ±3 %» bestand nur zufällig (Brutto gegen Netto). Ersetzt durch «Artikelsumme brutto vs. Payfix inkl. ±3 %»; neu «Normalsatz-Artikel = Gruppe Alkohol» und «Erlös je Einheit zwischen Saisons stabil». | 17 von 17 bestanden | 19 von 19 bestanden |

## 1. Auftrag, Scope und Leitplanken

- **Phase 1 (dieser Auftrag):** Quellen validieren, je Heimspiel eine konsistente Baseline, Anwesenheit/No-Show und Catering beschreiben, KF in Bons je Anwesendem × Ø Bon zerlegen, Ankunft und Ticketvorlauf als eigene Module, kontextbereinigte Abweichungen mit Unsicherheit zeigen.
- **Leitplanken:** Kapazität fix, kein Dynamic Pricing, kein Stadionausbau, keine Hospitality; keine Personensegmentierung; Umsatz (nicht DB) als Fokus; Massnahmenquantifizierung erst Phase 2.
- **Kernstichprobe:** Pflichtspiele der Herren im kybunpark (Super League inkl. Meisterschafts-/Abstiegsrunde, Schweizer Cup, UEFA). Baseline ab 2021/22, Kontextmodelle Meisterschaft ab 2022/23 (Kontexttabelle; 21/22 COVID-geprägt). Frauen, Länderspiele, Testspiele und Events sind dokumentiert ausgeschlossen (Unmatched-Report).

## 2. Datenbasis und Abdeckung

Abdeckung je Saison (Pflichtspiele mit Daten je Modul):

| Saison | Wettbewerb | Spiele | Anwesenheit (Historie SOLL/IST) | Catering-Umsatz + Public Netto | Catering-Transaktionen (Bons) | Zutritt vollständig (Ankunft) | Einzeltickets vollständig (Vorlauf) | Eintritt je Einzelticket (ZKS valide) | Spielkontext-Tabelle (Gruppe) | im Kontextmodell (Diagnosekarte) |
|---|---|---|---|---|---|---|---|---|---|---|
| 2021/22 | Cup | 1 | 1 | 1 | 0 | 0 | 0 | 0 | 0 | 0 |
| 2021/22 | SL | 18 | 18 | 18 | 0 | 0 | 18 | 18 | 0 | 0 |
| 2022/23 | Cup | 1 | 1 | 1 | 0 | 1 | 1 | 1 | 1 | 0 |
| 2022/23 | SL | 18 | 18 | 18 | 0 | 15 | 18 | 16 | 18 | 16 |
| 2023/24 | SL | 19 | 19 | 19 | 19 | 19 | 19 | 0 | 19 | 19 |
| 2024/25 | SL | 18 | 18 | 18 | 18 | 9 | 9 | 0 | 18 | 18 |
| 2024/25 | UEFA | 6 | 6 | 6 | 6 | 0 | 5 | 0 | 6 | 0 |
| 2025/26 | Cup | 1 | 1 | 1 | 1 | 1 | 0 | 0 | 1 | 0 |
| 2025/26 | SL | 19 | 19 | 19 | 19 | 19 | 19 | 0 | 13 | 19 |
| 2026/27 | SL | 4 | 4 | 4 | 4 | 4 | 4 | 0 | 4 | 4 |
| 2026/27 | UEFA | 3 | 3 | 3 | 3 | 3 | 3 | 0 | 3 | 0 |
| Total | alle | 108 | 108 | 108 | 70 | 71 | 96 | 35 | 83 | 76 |

Gemeinsame Stichproben (Meisterschaft ab 22/23):

| Kombination | Spiele | Saisons |
|---|---|---|
| Anwesenheit + Kontext | 78 | 2022/23, 2023/24, 2024/25, 2025/26, 2026/27 |
| Anwesenheit + Catering + Kontext | 78 | 2022/23, 2023/24, 2024/25, 2025/26, 2026/27 |
| Catering mit Bons + Kontext | 60 | 2023/24, 2024/25, 2025/26, 2026/27 |
| Ankunft + Catering mit Bons + Kontext | 51 | 2023/24, 2024/25, 2025/26, 2026/27 |
| Einzelticket-Vorlauf + Anwesenheit | 69 | 2022/23, 2023/24, 2024/25, 2025/26, 2026/27 |
| Eintritt je Einzelticket (ZKS) + Anwesenheit | 16 | 2022/23 |
| Alle Module gleichzeitig | 0 |  |

**Nicht geliefert** (und daher nicht ausgewertet): Merchandise (Paket E), Catering je Viertelstunde und Verkaufsstelle inkl. Stand→Sektor-Mapping, Deckungsbeiträge/Einstandspreise, Kapazität je Sektor mit Sperrungen und Verkaufsstand je Tag, Abo-Besuche je Spiel. Einzelticket-Export 2024/25 endet am 09.12.2024; Zutritte Juli–Dezember 2024 nur bruchstückhaft.

## 3. Datenmodell und Verknüpfung

| Tabelle | Granularität | Inhalt |
|---|---|---|
| `dim_match` | Heimspiel | match_id = Datum + Wettbewerb, Anpfiff (Mehrheit aus 5 Quellen), Status |
| `fact_attendance_match` | Heimspiel | SOLL, IST, VIP, Gäste, Zweitmarkt, SOLL-/IST-Definition |
| `fact_ticket_single` | Einzelticket → aggregiert | Kanal, Tarif, Tribüne, Vorlauf, Eintritt (ZKS), Bestellgrösse |
| `snapshot_season_ticket` | Abo-Sitz (Stichtag 30.09.2026) | Tribüne, Tarif, Kanal, Abo-Form, Preis |
| `fact_access` | erster Scan je Ticket → aggregiert | Ankunft relativ zum Anpfiff, Eingang, Leser |
| `fact_catering_match` | Heimspiel | Public Netto, Bons, Umsatz inkl./exkl., Zahlungswege, Bemerkungen |
| `fact_kiesplatz` | Event × Verkaufsstelle | Brutto/Netto (Teilmenge des Catering-Totals) |
| `fact_article_season` | Artikel × Saison | Menge, Umsatz laut Datei (23/24–24/25 brutto, 25/26 netto) und harmonisiert brutto (nur Saisonsummen) |
| `dim_match_context` | Heimspiel | Kontextvariablen mit Quelle und Fehlstatus |
| `mart_match` | Heimspiel | Zielgrössen, Kontext, Diagnose, Verfügbarkeitsflags |

**Regeln:** Join ausschliesslich über das Datum (nie über das Gegner-Label); zuerst jede Quelle auf Spielebene aggregieren, dann verbinden (kein Rohdaten-Join Ticket × Scan × Catering). Pseudonyme IDs (Barcode/UTId) nur technisch zur Deduplizierung, danach verworfen.

**Belegte Korrekturen** (greifen nur, solange der Altwert noch in der Quelle steht):

| Quelle | Blatt/Datei | Zeile | Feld | alt | neu |
|---|---|---|---|---|---|
| Historie | Zuschauerzahlen | 341 | Datum | 2024-08-24 | 2024-09-24 |
| Historie | Zuschauerzahlen | 393 | Anpfiff | 14:00 | 16:30 |
| Catering | 2022-2023 | 5 | Datum | 2022-07-16 | 2022-07-23 |
| Ticket-CSV | 20260126_MS21_SFC.csv | 0 | Datum | 2026-01-26 | 2026-01-25 |
| Kiesplatz | Saison 22-23 | 4 | Datum | 2022-07-14 | 2022-07-23 |
| Kiesplatz | Saison 22-23 | 15 | Datum | 2023-01-23 | 2023-01-22 |

Unmatched-Report: 197 Zeilen ohne Kernspiel, davon 15 zu prüfen (v.a. Kernspiele ohne Ticket-/Kontextdaten); der Rest sind Events, Frauen-, Länder- und Testspiele.

## 4. KPI-Definitionen

```
Anwesenheitsquote = IST / SOLL            No-Show-Quote = 1 − IST / SOLL      No-Show absolut = SOLL − IST
Kundenfranken (KF) = Umsatz / Public Netto = (Bons / Public Netto) × (Umsatz / Bons)
Ø Bon = Umsatz / Bons
Saisonwerte immer Summe/Summe (z.B. KF = Σ Umsatz / Σ Public Netto)
```

- **SOLL** ist je nach Spiel unterschiedlich definiert: Summe der Ticketkomponenten (Einzeltickets je Verkaufsstelle + zwei Abo-Komponenten − Zweitmarkt; Abo-Bestand 25/26 implizit 11'596–11'850) oder bei ausverkauften Spielen ein Kapazitätswert (z.B. 20'036 − 1'930 + Gäste). 36 Pflichtspiele haben ein Kapazitäts-SOLL; dort ist die No-Show-Quote nicht ticketbasiert (Flag `soll_definition`).
- **Public Netto** (KF-Nenner) = IST minus eine VIP-Zahl; 2025/26 liegt der Abzug im Mittel rund 90 Personen über «IST VIP» der Historie, 2026/27 ist er identisch (Effekt auf den KF < 1 %).
- **MwSt:** Netto vor 2020/21 pauschal inkl./1.077, danach effektive Mischsätze (Take-away reduziert) → langfristige Vergleiche inkl. MwSt, Modelle exkl. MwSt mit Saison-Effekten. Die CHF 14.50 des Antrags = KF exkl. MwSt aller Pflichtspiele 25/26.
- **Bons je Anwesendem ≠ Kaufquote:** Eine Person kann mehrfach kaufen, eine Gruppe auf einem Bon.

## 5. Paket A – Baseline und Qualitätsprüfung

| Saison | Spiele | Ø IST | Ø SOLL | No-Show | KF inkl. | KF exkl. | Bons/Anw. | Ø Bon exkl. | Umsatz inkl. CHF |
|---|---|---|---|---|---|---|---|---|---|
| 2021/22 | 18 | 12'042 | 15'514 | 22.4 % | 13.68 | 13.00 | – | – | 2'820'941 |
| 2022/23 | 18 | 14'558 | 17'575 | 17.2 % | 13.32 | 12.62 | – | – | 3'323'225 |
| 2023/24 | 19 | 14'829 | 17'753 | 16.5 % | 14.81 | 13.93 | 0.84 | 16.62 | 3'998'632 |
| 2024/25 | 18 | 14'635 | 18'079 | 19.0 % | 14.48 | 13.74 | 0.88 | 15.58 | 3'632'232 |
| 2025/26 | 19 | 14'510 | 17'718 | 18.1 % | 15.27 | 14.51 | 0.93 | 15.57 | 4'000'583 |
| 2026/27 | 4 | 15'882 | 18'664 | 14.9 % | 16.73 | 15.86 | 0.98 | 16.24 | 1'019'196 |

*Meisterschaft; 2026/27 erst 4 Spiele (Sommer/Frühherbst) – nicht ungewichtet mit Vollsaisons vergleichen.*

**Scan-IST-Abgleich:** 71 von 89 Spieltagen mit vollständiger Lieferung. Ab 2025/26 weichen die Scans im Mittel -0.44 % vom IST ab (IST ≈ Scanzahl), davor liegt IST um 1–3 % über den Scans (manuelle Zählungen). Grosse Lücken sind erklärt (Drehkreuz-/Handscannerprobleme laut Historie, unvollständige Lieferung).

## 6. Paket B – Anwesenheit und Absatz

No-Show nach Kontext (deskriptiv; Merkmale überlagern sich – Effekte siehe Kontext-Effekt-Matrix):

| Merkmal | Ausprägung | Spiele | No-Show | Abw. vom Saisonmittel (Pp.) |
|---|---|---|---|---|
| Wochentag | Wochenende (Sa/So) | 64 | 16.7 % | -1.1 |
| Wochentag | Wochentag (Mo–Fr) | 14 | 22.1 % | +4.8 |
| Anstosszeit | Nachmittag (<17 Uhr) | 34 | 14.9 % | -2.8 |
| Anstosszeit | Abend (ab 20 Uhr) | 21 | 21.3 % | +3.9 |
| Winter (Nov–Feb) | ja | 25 | 20.2 % | +2.7 |
| Top-Gegner (FCB/YB/FCZ) | ja | 23 | 15.1 % | -2.6 |
| Ausverkauft | ja | 35 | 14.0 % | -4.0 |
| Ausverkauft | nein | 43 | 20.8 % | +3.3 |

**Ticket-Typ-Näherung (nur 21/22 und 22/23 mit validem Eintritt je Einzelticket):**

| Saison | Spiele | Rest (≈Abos) am SOLL | No-Show Einzel | No-Show Rest |
|---|---|---|---|---|
| 2021/22 | 18 | 65.0 % | 9.3 % | 29.4 % |
| 2022/23 | 17 | 60.0 % | 9.6 % | 22.5 % |

*Rest = SOLL − Einzeltickets enthält Abos, VIP, Gäste und Freikarten; bei Kapazitäts-SOLL überschätzt. Nur als gekennzeichnete Näherung.*

No-Show der Einzeltickets nach Segment (Spiele 21/22–22/23 mit validem ZKS-Eintritt):

| Merkmal | Ausprägung | Tickets | No-Show |
|---|---|---|---|
| Tickets pro Bestellung | 1 | 38'328 | 9.7 % |
| Tickets pro Bestellung | 2 | 57'240 | 5.2 % |
| Tickets pro Bestellung | 3–4 | 55'393 | 4.6 % |
| Tickets pro Bestellung | 5–9 | 27'140 | 5.8 % |
| Tickets pro Bestellung | 10+ | 37'022 | 25.7 % |
| Tarifgruppe | Vollpreis | 120'890 | 9.3 % |
| Tarifgruppe | Ermässigt | 60'549 | 5.7 % |
| Tarifgruppe | Gratis/Promo | 23'052 | 15.7 % |
| Tarifgruppe | Sponsor/Dritte | 4'653 | 19.1 % |
| Verkaufskanal | Online-Shop | 148'312 | 4.9 % |
| Verkaufskanal | Inhouse (Geschäftsstelle/Kasse) | 45'671 | 25.0 % |
| Verkaufskanal | Partner online (Connect/TDL) | 15'462 | 5.8 % |
| Kaufzeitpunkt vor Spiel | Spieltag | 34'562 | 11.2 % |
| Kaufzeitpunkt vor Spiel | über 30 Tage | 22'535 | 12.9 % |

**Einzelticket-Vorlauf:** Bei ausverkauften Meisterschaftsspielen ist die Hälfte der Einzeltickets 11 Tage vor dem Spiel verkauft (sonst 4 Tage); der Spieltagsanteil liegt bei 4 % vs. 19 %. Die Kurven zeigen nur Einzeltickets (ohne Abos) und den Endbestand nach allfälligen Stornos – keine Stadion-Ausverkaufskurve.

**Saisonabos 2026/27 (Herren, 13'052 Sitze):** Tribüne A 2'127 (16 %), Tribüne B 1'946 (15 %), Tribüne C 4'441 (34 %), Tribüne D 3'679 (28 %), Tribüne Hospitality 859 (7 %).

## 7. Paket C – Catering

- **KF-Zerlegung (Meisterschaft ab 23/24, n=60):** saisonbereinigt Ø Bon 50 %, Bons je Anwesendem 39 %, Kovarianz 11 % der Varianz von ln KF.
- **Retos Korrelationen** (25/26 + 26/27, n=27): r(KF, Ø Bon) = 0.87, r(KF, Bons/Anw.) = 0.75 – algebraisch verknüpft, kein Kausalnachweis.
- **Zahlungswege 25/26:** Payfix (Kasse/Stand) 96.3 %, Just Eat (App) 1.1 %, Gutscheine/nicht verbucht 0.7 %, Extern 1.9 %.
- **Sortiment (Meisterschaft, Umsatzanteile brutto):** Alkohol 53.5 % (23/24) → 49.9 % (25/26); Food 32 %, alkoholfrei 15 %. Die Artikelauswertung liefert 23/24–24/25 brutto, 25/26 netto; verglichen wird einheitlich brutto (overrides/artikel_basis.csv). Artikelwerte nur als Saisonsummen – nie pro Spiel in Modelle.
- **Kiesplatz:** Für Getränke-/Pommes-Contrailer, Fanshop Bar und Bier S2 sind 22 von 24 Spiel-Stand-Werten 21/22 frankengenau identisch mit den Standspalten der Catering-Datei; «BBQ1 Kiesplatz» liegt in 7 von 8 Fällen unter «Contrailer BBQ 1» (Teilmenge, Rest auf der Plattform) → Kiesplatz ist im Catering-Total enthalten und wird nie addiert.
- **Elastizität Umsatz ~ Public-Anwesende:** Retos Stichprobe (SL 25/26 + 26/27): 1.22 [1.04–1.40], n=23; SL 21/22–26/27 mit Saison-Effekten: 1.01 [0.92–1.10], n=96; SL 22/23–26/27 + Kontext (Top-Gegner, Abend, Temperatur): 1.07 [0.93–1.21], n=78. Zusammenhang, keine Kausalität.

## 8. Paket D – Ankunft

- **Retos Stichprobe (25/26 + 26/27, n=27):** Median 37.3 min vor Anpfiff, 41 % ≥ 45 min, 17 % in den letzten 15 min (inkl. nach Anpfiff). **Alle vollständigen Spiele (n=71):** 38.0 min, 41 %, 16 %.
- **Nach Eingang (Median der Spielmediane):** D 70 min, HH (Hospitality) 69 min, B4 (Gäste) 36 min, B 31 min, A 29 min, C 25 min. Sektor = physischer Eingang (Lesername); Seatinfo ist nicht eindeutig und wird nicht verwendet.
- **Einlass:** 1 % der Besucher ist im Median 114 min vor Anpfiff im Stadion (Toröffnung laut Daten); Mehrfachscans derselben Ticket-ID sind selten (0.008 %) – Wiedereintritt praktisch nicht vorhanden.
- **Toröffnung je Eingang (aus Scans):** Einlass-Beginn (1 %-Punkt) im Median HH (Hospitality) 119 min, D 91 min, A 62 min, B 61 min, B4 (Gäste) 61 min, C 61 min vor Anpfiff (Streuung ±2 min → feste Öffnungszeiten). Die Ankunftskurven steigen genau ab diesem Zeitpunkt steil an: Auslöser ist die Toröffnung, nicht das Spiel.
- **Natürliches Experiment:** Ab 02.04.2023 öffnet Sektor D 90 statt 60 min vor Anpfiff (Catering-Bemerkung «Türöffnung 1.5h»; Scans bestätigen +28 min). Differenz-in-Differenzen gegenüber A/B/C bei denselben Spielen (12 Spiele vorher, 59 nachher): Median der Ankunft +22.6 min (95 %-KI 19.0 bis 26.1), Anteil ≥ 60 min +50 Pp. (KI 45 bis 55). Auf Spielebene lag der KF nach der Umstellung +4.8 % über der Kontexterwartung (n=4, KI90 -2.6 bis +11.1 %) – **Wirkung auf die Ankunft belegt, Wirkung auf den Konsum nicht belastbar** (zu wenige Spiele, kein Stand→Sektor-Mapping).
- **Ankunft → Konsum (aggregierte Spiele, n=55):** +10 Pp. Frühankommende gehen mit +3.5 % KF einher (p=0.05); mit Kontextkontrollen -0.5 % (p=0.85). Der Zusammenhang ist **nicht belastbar**; ohne Bon-Zeitstempel bleibt Ankunft→Konsum eine Hypothese.

## 9. Kontextmodelle und Kontext-Effekt-Matrix

**Vorgehen:** Je Zielgrösse ein eigenes Modell (keine Gesamtumsatz-Regression): Anwesenheitsquote und Frühankunft-Anteil (logit), KF, Bons je Anwesendem und Ø Bon (log), jeweils mit Saison-Effekten (Preise, MwSt, Definitionswechsel, Trend) und sechs vorab festgelegten Kontextvariablen: Top-Gegner (FCB/YB/FCZ), Werktag, Abendspiel (≥ 20 Uhr), Temperatur zum Anpfiff (MeteoSchweiz), Regen bei Anreise, Schulferien. Robuste Standardfehler (HC3). Clubhebel (Stände, Zweitmarkt, Kommunikation, Payment) werden bewusst nicht herauskontrolliert.

**Validierung:** (1) Leave-one-season-out auf saisonbereinigten Werten gegen das Saisonmittel als Basislinie; (2) Vorzeichenstabilität über Saisons und sechs Sensitivitätsvarianten (inkl. Cup/UEFA, inkl. Scanproblem-Spiele, Gegnerstärke statt Top-Gegner, Tagesmittel- statt Anpfifftemperatur, ohne Ausreisser, nur ticketbasiertes SOLL). «Belastbar» = 95 %-Intervall ohne 0 und Vorzeichen in ≥ 80 % der Saisons und Varianten stabil. Bei 30 geprüften Effekten wären rund 1–2 zufällig «signifikante» Ergebnisse zu erwarten – deshalb zählt nicht der p-Wert allein, sondern zusätzlich die Stabilität.

| Zielgrösse | Spiele | R² Kontext (saisonbereinigt) | Out-of-sample vs. Saisonmittel (% RMSE) |
|---|---|---|---|
| Anwesenheitsquote (IST/SOLL) | 76 | 42.4 % | +15.9 |
| Kundenfranken exkl. MwSt | 76 | 33.3 % | +7.2 |
| Bons je Public-Anwesendem | 60 | 18.7 % | +1.8 |
| Ø Bon exkl. MwSt | 60 | 34.5 % | +4.8 |
| Anteil Ankunft ≥ 45 min vor Anpfiff (optional) | 66 | 39.2 % | +7.7 |

**Kontext-Effekt-Matrix** (Effekt: log-Ziele in %, Quoten in Prozentpunkten; Temperatur je +5 °C):

| Zielgrösse | Variable | Einordnung | Effekt | KI unten | KI oben | Beurteilung |
|---|---|---|---|---|---|---|
| Anwesenheitsquote (IST/SOLL) | Top-Gegner (FCB, YB, FCZ) | extern (Gegner) | +3.5 | +0.9 | +6.2 | belastbar |
| Anwesenheitsquote (IST/SOLL) | Werktag (Mo–Fr) statt Wochenende | teilweise beeinflussbar (Spielplan/TV durch Liga) | -2.9 | -7.3 | +1.4 | Hinweis (Richtung stabil, Grösse unsicher) |
| Anwesenheitsquote (IST/SOLL) | Abendspiel (Anpfiff ab 20 Uhr) | teilweise beeinflussbar (Anstosszeit/TV durch Liga) | -4.1 | -7.1 | -1.1 | belastbar |
| Anwesenheitsquote (IST/SOLL) | Temperatur bei Anpfiff | extern (Wetter) | +1.4 | +0.7 | +2.1 | belastbar |
| Anwesenheitsquote (IST/SOLL) | Regen bei Anreise (≥ 0.5 mm in 2 h vor Anpfiff) | extern (Wetter) | +0.4 | -3.1 | +3.9 | nicht belastbar schätzbar |
| Anwesenheitsquote (IST/SOLL) | Schulferien Stadt St.Gallen | extern (Kalender) | -1.5 | -4.0 | +1.1 | Hinweis (Richtung stabil, Grösse unsicher) |
| Kundenfranken exkl. MwSt | Top-Gegner (FCB, YB, FCZ) | extern (Gegner) | -0.8 | -5.0 | +3.5 | Hinweis (Richtung stabil, Grösse unsicher) |
| Kundenfranken exkl. MwSt | Werktag (Mo–Fr) statt Wochenende | teilweise beeinflussbar (Spielplan/TV durch Liga) | -4.0 | -7.9 | +0.1 | Hinweis (Richtung stabil, Grösse unsicher) |
| Kundenfranken exkl. MwSt | Abendspiel (Anpfiff ab 20 Uhr) | teilweise beeinflussbar (Anstosszeit/TV durch Liga) | +6.8 | +3.1 | +10.7 | belastbar |
| Kundenfranken exkl. MwSt | Temperatur bei Anpfiff | extern (Wetter) | +3.6 | +1.9 | +5.2 | belastbar |
| Kundenfranken exkl. MwSt | Regen bei Anreise (≥ 0.5 mm in 2 h vor Anpfiff) | extern (Wetter) | +4.7 | -3.8 | +14.0 | Hinweis (Richtung stabil, Grösse unsicher) |
| Kundenfranken exkl. MwSt | Schulferien Stadt St.Gallen | extern (Kalender) | -3.4 | -7.8 | +1.1 | Hinweis (Richtung stabil, Grösse unsicher) |
| Bons je Public-Anwesendem | Top-Gegner (FCB, YB, FCZ) | extern (Gegner) | -0.9 | -4.3 | +2.6 | Hinweis (Richtung stabil, Grösse unsicher) |
| Bons je Public-Anwesendem | Werktag (Mo–Fr) statt Wochenende | teilweise beeinflussbar (Spielplan/TV durch Liga) | -1.7 | -5.9 | +2.8 | Hinweis (Richtung stabil, Grösse unsicher) |
| Bons je Public-Anwesendem | Abendspiel (Anpfiff ab 20 Uhr) | teilweise beeinflussbar (Anstosszeit/TV durch Liga) | +4.6 | +0.5 | +9.0 | belastbar |
| Bons je Public-Anwesendem | Temperatur bei Anpfiff | extern (Wetter) | +0.7 | -0.4 | +1.9 | Hinweis (Richtung stabil, Grösse unsicher) |
| Bons je Public-Anwesendem | Regen bei Anreise (≥ 0.5 mm in 2 h vor Anpfiff) | extern (Wetter) | -2.0 | -7.3 | +3.7 | nicht belastbar schätzbar |
| Bons je Public-Anwesendem | Schulferien Stadt St.Gallen | extern (Kalender) | -0.8 | -4.0 | +2.6 | nicht belastbar schätzbar |
| Ø Bon exkl. MwSt | Top-Gegner (FCB, YB, FCZ) | extern (Gegner) | +0.6 | -2.5 | +3.7 | nicht belastbar schätzbar |
| Ø Bon exkl. MwSt | Werktag (Mo–Fr) statt Wochenende | teilweise beeinflussbar (Spielplan/TV durch Liga) | -4.0 | -7.4 | -0.5 | belastbar |
| Ø Bon exkl. MwSt | Abendspiel (Anpfiff ab 20 Uhr) | teilweise beeinflussbar (Anstosszeit/TV durch Liga) | -0.1 | -3.2 | +3.0 | nicht belastbar schätzbar |
| Ø Bon exkl. MwSt | Temperatur bei Anpfiff | extern (Wetter) | +2.3 | +0.9 | +3.7 | belastbar |
| Ø Bon exkl. MwSt | Regen bei Anreise (≥ 0.5 mm in 2 h vor Anpfiff) | extern (Wetter) | +2.9 | -3.5 | +9.7 | nicht belastbar schätzbar |
| Ø Bon exkl. MwSt | Schulferien Stadt St.Gallen | extern (Kalender) | -2.7 | -6.2 | +1.0 | Hinweis (Richtung stabil, Grösse unsicher) |
| Anteil Ankunft ≥ 45 min vor Anpfiff (optional) | Top-Gegner (FCB, YB, FCZ) | extern (Gegner) | +3.3 | +1.0 | +5.6 | belastbar |
| Anteil Ankunft ≥ 45 min vor Anpfiff (optional) | Werktag (Mo–Fr) statt Wochenende | teilweise beeinflussbar (Spielplan/TV durch Liga) | -4.5 | -10.6 | +1.6 | Hinweis (Richtung stabil, Grösse unsicher) |
| Anteil Ankunft ≥ 45 min vor Anpfiff (optional) | Abendspiel (Anpfiff ab 20 Uhr) | teilweise beeinflussbar (Anstosszeit/TV durch Liga) | +4.1 | +0.9 | +7.3 | belastbar |
| Anteil Ankunft ≥ 45 min vor Anpfiff (optional) | Temperatur bei Anpfiff | extern (Wetter) | +0.9 | -0.1 | +1.8 | Hinweis (Richtung stabil, Grösse unsicher) |
| Anteil Ankunft ≥ 45 min vor Anpfiff (optional) | Regen bei Anreise (≥ 0.5 mm in 2 h vor Anpfiff) | extern (Wetter) | -1.5 | -7.8 | +4.8 | Hinweis (Richtung stabil, Grösse unsicher) |
| Anteil Ankunft ≥ 45 min vor Anpfiff (optional) | Schulferien Stadt St.Gallen | extern (Kalender) | +1.3 | -1.2 | +3.8 | Hinweis (Richtung stabil, Grösse unsicher) |

*Wichtig: KF und Ø Bon/Bons sind algebraisch verknüpft; Effekte sind Zusammenhänge auf Spielebene (Kontext ist vor dem Spiel bekannt), keine Personenaussagen. «Nicht belastbar schätzbar» ist ein zulässiges Ergebnis.*

## 10. Diagnosekarte – kein automatischer Potenzialbeweis

```
Diagnoselücke = erwarteter Wert unter Kontext − beobachteter Wert   (positiv = unter Erwartung)
Referenzlücke Konsum (CHF) = (erwarteter KF − beobachteter KF) × beobachtete Public-Anwesende
```

Erwartungswerte stammen aus Leave-one-match-out-Schätzungen (das Spiel selbst fliesst nicht in seine Erwartung ein); das 80 %-Band entspricht ±1.28 × Prognosefehler. Lücken aus KF, Bons und Ø Bon werden **nicht addiert**; CHF-Werte sind modellbasierte Referenzlücken und werden **nicht summiert**. Anwesenheitslücken in Personen nur bei ticketbasiertem SOLL; CHF nur als Szenario mit explizitem φ = 0.6.

Spiele ausserhalb des KF-Bands:

| Datum | Gegner | KF beob. | KF erw. | Referenzlücke CHF | Einordnung | Mögliche Mechanismen |
|---|---|---|---|---|---|---|
| 2022-10-23 | Servette FC | 11.17 | 12.57 | 19'078 | unter Erwartung – ungeklärte Abweichung (kein dokumentierter Mechanismus) |  |
| 2022-11-05 | Grasshopper Club Zürich | 13.80 | 12.28 | -22'991 | über Erwartung – positiver Ausreisser (was lief gut? Muster prüfen) |  |
| 2023-02-04 | Servette FC | 13.45 | 11.76 | -16'741 | über Erwartung – positiver Ausreisser (was lief gut? Muster prüfen) | Stände geschlossen (Catering-Bemerkung) |
| 2023-02-19 | FC Luzern | 10.69 | 12.35 | 22'570 | unter Erwartung – möglicher Clubhebel (operativer Hinweis dokumentiert) → Prüfkandidat Phase 2 | Runner/Bauchläden ganz oder teilweise nicht im Einsatz |
| 2023-05-29 | FC Sion | 14.12 | 12.59 | -23'431 | über Erwartung – positiver Ausreisser (was lief gut? Muster prüfen) |  |
| 2023-07-22 | FC Basel | 15.93 | 13.95 | -30'568 | über Erwartung – positiver Ausreisser (was lief gut? Muster prüfen) | Stände geschlossen (Catering-Bemerkung); technische Probleme (Kasse/App/Internet); Abweichung v.a. über Bons je Anwesendem (Frequenz) |
| 2023-08-06 | FC Luzern | 11.24 | 14.65 | 51'230 | unter Erwartung – ungeklärte Abweichung (kein dokumentierter Mechanismus) | Abweichung v.a. über Bons je Anwesendem (Frequenz) |
| 2023-11-11 | FC Winterthur | 14.86 | 12.83 | -32'095 | über Erwartung – positiver Ausreisser (was lief gut? Muster prüfen) | Abweichung v.a. über Ø Bon (Warenkorb) |
| 2023-12-16 | FC Zürich | 14.09 | 12.41 | -28'701 | über Erwartung – positiver Ausreisser (was lief gut? Muster prüfen) | Plattform-Event/Zusatzprogramm (z.B. Winterzauber, Kids Day) |
| 2024-02-24 | Stade Lausanne-Ouchy | 14.54 | 12.94 | -19'773 | über Erwartung – positiver Ausreisser (was lief gut? Muster prüfen) | Stände geschlossen (Catering-Bemerkung); technische Probleme (Kasse/App/Internet); Abweichung v.a. über Bons je Anwesendem (Frequenz) |
| 2024-05-12 | Servette FC | 13.08 | 15.00 | 28'588 | unter Erwartung – möglicher Clubhebel (operativer Hinweis dokumentiert) → Prüfkandidat Phase 2 | technische Probleme (Kasse/App/Internet); Abweichung v.a. über Ø Bon (Warenkorb) |
| 2024-09-21 | FC Luzern | 16.39 | 14.27 | -32'782 | über Erwartung – positiver Ausreisser (was lief gut? Muster prüfen) | Abweichung v.a. über Ø Bon (Warenkorb) |
| 2024-11-24 | Yverdon Sport | 11.88 | 13.63 | 21'783 | unter Erwartung – möglicher Clubhebel (operativer Hinweis dokumentiert) → Prüfkandidat Phase 2 | Runner/Bauchläden ganz oder teilweise nicht im Einsatz; technische Probleme (Kasse/App/Internet); Abweichung v.a. über Ø Bon (Warenkorb); kalt (Bemerkung Historie); Schnee/Verschiebung |
| 2024-12-08 | FC Basel | 12.06 | 13.70 | 26'597 | unter Erwartung – möglicher Clubhebel (operativer Hinweis dokumentiert) → Prüfkandidat Phase 2 | Runner/Bauchläden ganz oder teilweise nicht im Einsatz; Plattform-Event/Zusatzprogramm (z.B. Winterzauber, Kids Day); Abweichung v.a. über Ø Bon (Warenkorb) |
| 2025-07-26 | FC Basel | 16.27 | 14.03 | -36'362 | über Erwartung – positiver Ausreisser (was lief gut? Muster prüfen) | Abweichung v.a. über Ø Bon (Warenkorb) |
| 2025-08-09 | FC Winterthur | 17.70 | 15.38 | -36'627 | über Erwartung – positiver Ausreisser (was lief gut? Muster prüfen) | Abweichung v.a. über Bons je Anwesendem (Frequenz) |
| 2026-02-28 | FC Winterthur | 15.81 | 14.00 | -24'457 | über Erwartung – positiver Ausreisser (was lief gut? Muster prüfen) |  |
| 2026-09-12 | FC Sion | 17.00 | 15.18 | -25'543 | über Erwartung – positiver Ausreisser (was lief gut? Muster prüfen) | Abweichung v.a. über Ø Bon (Warenkorb) |

Wiederkehrende Muster (mittlere Abweichung von der Erwartung bei gleichem Kontext):

| Zielgrösse | Merkmal | Spiele | Abweichung % | KI90 unten | KI90 oben |
|---|---|---|---|---|---|
| Anwesenheitsquote (IST/SOLL) | Operativer Hinweis (Stände zu, Runner/Personal fehlt, Technik) | 25 | -3.2 | -5.1 | -1.4 |
| Anwesenheitsquote (IST/SOLL) | Stände geschlossen | 11 | -6.7 | -8.7 | -4.7 |
| Anwesenheitsquote (IST/SOLL) | Runner/Bauchläden ganz oder teilweise nicht im Einsatz | 15 | -3.1 | -5.6 | -0.6 |
| Anwesenheitsquote (IST/SOLL) | technische Probleme | 7 | -3.2 | -6.5 | +0.2 |
| Anwesenheitsquote (IST/SOLL) | Plattform-Event/Zusatzprogramm | 7 | -0.6 | -3.0 | +1.8 |
| Kundenfranken exkl. MwSt | Operativer Hinweis (Stände zu, Runner/Personal fehlt, Technik) | 25 | -0.4 | -3.2 | +2.4 |
| Kundenfranken exkl. MwSt | Stände geschlossen | 11 | +4.2 | +0.2 | +8.1 |
| Kundenfranken exkl. MwSt | Runner/Bauchläden ganz oder teilweise nicht im Einsatz | 15 | -3.4 | -6.3 | -0.6 |
| Kundenfranken exkl. MwSt | technische Probleme | 7 | -0.4 | -6.7 | +5.8 |
| Kundenfranken exkl. MwSt | Plattform-Event/Zusatzprogramm | 7 | -0.8 | -5.5 | +4.0 |
| Bons je Public-Anwesendem | Operativer Hinweis (Stände zu, Runner/Personal fehlt, Technik) | 16 | +0.7 | -1.9 | +3.4 |
| Bons je Public-Anwesendem | Stände geschlossen | 6 | +3.2 | -1.6 | +7.5 |
| Bons je Public-Anwesendem | Runner/Bauchläden ganz oder teilweise nicht im Einsatz | 10 | -1.2 | -4.5 | +2.2 |
| Bons je Public-Anwesendem | technische Probleme | 7 | +1.5 | -2.0 | +5.5 |
| Bons je Public-Anwesendem | Plattform-Event/Zusatzprogramm | 7 | +2.2 | -0.7 | +5.0 |
| Ø Bon exkl. MwSt | Operativer Hinweis (Stände zu, Runner/Personal fehlt, Technik) | 16 | -1.3 | -3.6 | +0.8 |
| Ø Bon exkl. MwSt | Stände geschlossen | 6 | -0.3 | -3.0 | +2.1 |
| Ø Bon exkl. MwSt | Runner/Bauchläden ganz oder teilweise nicht im Einsatz | 10 | -2.0 | -4.6 | +0.7 |
| Ø Bon exkl. MwSt | technische Probleme | 7 | -2.1 | -5.7 | +1.7 |
| Ø Bon exkl. MwSt | Plattform-Event/Zusatzprogramm | 7 | -4.2 | -6.4 | -1.9 |
| Anteil Ankunft ≥ 45 min vor Anpfiff (optional) | Operativer Hinweis (Stände zu, Runner/Personal fehlt, Technik) | 22 | -5.0 | -9.8 | -1.0 |
| Anteil Ankunft ≥ 45 min vor Anpfiff (optional) | Stände geschlossen | 10 | -7.6 | -17.4 | +0.6 |
| Anteil Ankunft ≥ 45 min vor Anpfiff (optional) | Runner/Bauchläden ganz oder teilweise nicht im Einsatz | 13 | -4.1 | -9.0 | -0.1 |
| Anteil Ankunft ≥ 45 min vor Anpfiff (optional) | technische Probleme | 6 | -2.8 | -6.0 | +0.8 |
| Anteil Ankunft ≥ 45 min vor Anpfiff (optional) | Plattform-Event/Zusatzprogramm | 6 | +0.0 | -5.5 | +5.8 |

*Geschlossene Stände treten vor allem bei schwacher Nachfrage auf (umgekehrte Kausalität möglich); Aussagen nur als Prüfkandidaten.*

## 11. Abgleich mit Retos Sichtung

| Retos Aussage | Reproduziert | Status | Erklärung |
|---|---|---|---|
| Ø IST 22/23–25/26 rund 14.5k–14.8k (Meisterschaft) | 14'510–14'829 | bestätigt | Saisonmittel der Meisterschafts-Heimspiele (Historie). |
| Ø SOLL 17.6k–18.1k | 17'575–18'079 | bestätigt | SOLL ist teils Ticketsumme, teils Kapazitätswert (ausverkaufte Spiele) – siehe soll_definition. |
| No-Show 16 %–19 % | 16.5 %–19.0 % | bestätigt | Gewichtet (1 − ΣIST/ΣSOLL). 2021/22 (COVID-Zertifikatspflicht): 22.4 % |
| Abo-Anteil (SOLL − Einzeltickets) 21/22 und 22/23 rund 63–65 % von SOLL | 21/22: 65.0 %, 22/23: 60.0 % | bestätigt mit Präzisierung | Rest enthält neben Abos auch VIP, Gäste und Freikarten; bei Kapazitäts-SOLL überschätzt. 22/23 eher 60 %. |
| No-Show Einzeltickets ca. 9–12 %, Abos ca. 20–29 % (21/22, 22/23) | Einzel: 9.3 % / 9.6 %; Rest (≈Abos): 29.4 % / 22.5 % | bestätigt | Nur valide ZKS-Spiele (ohne 02.04. und 16.04.2023 mit Scanproblemen). |
| Eintrittsquote Webshop und Connect Online ca. 90–95 %, Inhouse ca. 71–74 % | Webshop 95.1 %, Connect 94.2 %, Inhouse 75.0 %, Websales Client 86.0 % | bestätigt mit Präzisierung | Über beide Saisons gepoolt Inhouse 75 %. Inhouse enthält viele Gratis-/Promotickets (tiefere Eintrittsquote). |
| Scans im Schnitt 0.4 % unter IST (meist < 1 %) | -0.44 % (n=27); ältere Saisons (vollständige Lieferungen) -2.0 % | bestätigt | Ab 25/26 ist IST praktisch die Scanzahl; 22/23–24/25 liegt IST 1–3 % über den Scans. |
| Median Ankunft rund 37 min vor Anpfiff, 41 % ≥ 45 min, 17 % in den letzten 15 min | 37.3 min; 40.9 %; 17.4 % (inkl. nach Anpfiff) | bestätigt | Voraussetzung: Anpfiff 17.05.2026 korrigiert (Historie 14:00 statt 16:30). 71 statt 27 Spiele verfügbar. |
| Ältere Saisons folgen | 22/23, 23/24 und 2. Hälfte 24/25 bereits geliefert | erweitert | zugangsdaten_herren_inhouse.csv und _alteSaisons.txt; Juli–Dez. 2024 nur Bruchstücke (5–22 Scans/Spiel). |
| Umsatz inkl. MwSt 21/22 rund 2.8 Mio., 25/26 rund 4.0 Mio. (Meisterschaft) | 2.82 Mio. → 4.00 Mio. | bestätigt |  |
| KF inkl. MwSt 13.68 → 15.27 (Summe/Summe) | 13.68 → 15.27 | bestätigt | Exkl. MwSt alle Pflichtspiele 25/26: 14.51 = Antragswert CHF 14.50. |
| Bons je Anwesendem rund 0.95, Ø Bon rund 16.70 (25/26 + 26/27 inkl. Cup/Europa) | 0.946; Ø Bon inkl. MwSt gewichtet 16.88, ungewichtet 16.75 (n=27) | bestätigt mit Präzisierung | Retos 16.70 entspricht dem ungewichteten Mittel der Spiel-Bons; Summe/Summe ergibt einen etwas höheren Wert (Auftrag: Saisonwerte als Summe/Summe). |
| r(KF, Ø Bon) = 0.87; r(KF, Bons je Anwesendem) = 0.75 | 0.87; 0.75 | bestätigt | Algebraisch verknüpft (KF = Bons/Anw × Ø Bon) – kein unabhängiger Kausalnachweis. Saisonbereinigt erklären Ø Bon rund 50 % und Bons/Anwesende rund 39 % der KF-Streuung. |
| Alkoholanteil 25/26 rund 49 % (23/24: 54 %), Food 33 %, alkoholfrei 15 % | 49.9 % (23/24: 53.5 %); Food 32.3 %; alkoholfrei 15.0 % | bestätigt mit Präzisierung | Saisonsummen Meisterschaft (Artikelauswertung), einheitlich brutto: Die Datei liefert 23/24 und 24/25 Bruttowerte, 25/26 Nettowerte. Retos 49 % vs. 54 % vergleicht Netto (25/26) mit Brutto (23/24); auf gleicher Basis sinkt der Alkoholanteil weniger stark. |
| Elastizität Umsatz ~ Zuschauer rund 1.14 (22 Spiele, Modell) | 25/26+26/27: 1.22 [1.04–1.40]; 21/22–26/27 mit Saison-Effekten: 1.01 [0.92–1.10] | präzisiert | Auf der kleinen Stichprobe > 1, auf 96 Spielen ≈ 1: Mehr Zuschauer bringen proportional mehr Umsatz (KF bleibt etwa gleich) – kein belastbarer Skaleneffekt. |
| 27 Ticket-CSVs, rund 13'000 Abos, rund 394'000 Scans in 27 Spielen, rund 90 Kontextspiele | 26 Herren-Spiel-CSVs (+5 Frauen, 2 Abo-Dateien); 13'052 Abos; 393'739 Scans; 90 Kontextzeilen (83 gespielt) | bestätigt | In der Kontexttabelle fehlen 6 Meisterschaftsspiele 25/26 (11.02.–06.04.2026); ergänzt aus öffentlichen Quellen. |

## 12. Datenqualität und Tests

- Importtests: **19 von 19 bestanden**.
- Befunde: 37 (hoch 7, mittel 7, tief 10, info 13). Befunde mit hoher Relevanz:

  - **Catering – 2022-2023 Zeile 5:** Datum «2022-07-16» ist widersprüchlich: Die Public-Netto-Formel «=12247-520» verwendet das IST 12'247 des Spiels vom 23.07.2022 (Historie). Historie, Kontexttabelle, Zutrittsdatei und football-data.co.uk: Heimspiel gegen Winterthur am 23.07.2022. Am 16./17.07.2022 spielte der FCSG auswärts in Genf. → Belegt korrigiert auf «2022-07-23» (overrides/korrekturen.csv); an Sandro melden.
  - **Historie – Zuschauerzahlen Zeile 341:** Datum «2024-08-24» ist widersprüchlich: Wochentag «Dienstag» passt nur zum 24.09.2024 (24.08.2024 war ein Samstag). Kontexttabelle, Catering-Blatt 2024-2025, Einzelticket-Export (Veranstaltung «2024-09-24 20:30»), Zutrittsdatei und football-data.co.uk nennen übereinstimmend den 24.09.2024. → Belegt korrigiert auf «2024-09-24» (overrides/korrekturen.csv); an Sandro melden.
  - **Historie – Zuschauerzahlen Zeile 393:** Anpfiff «14:00» ist widersprüchlich: Catering-Blatt 2025-2026 (16:30), Kontexttabelle (16:30) und football-data.co.uk (15:30 UK-Zeit = 16:30 CH) nennen 16:30. Mit 14:00 läge der Median der Drehkreuz-Ankunft 111 Minuten nach Anpfiff. → Belegt korrigiert auf «16:30» (overrides/korrekturen.csv); an Sandro melden.
  - **Kiesplatz – Abrechnung Kiesplatz 21/22 vs. Catering-Blatt 2021-2022:** Getränke-/Pommes-Contrailer, Fanshop Bar und Bier S2 stimmen je Spiel zu 92% frankengenau mit den Standspalten der Public-Catering-Datei überein; BBQ1 Kiesplatz ist ein Teil von «Contrailer BBQ 1». → Kiesplatz nur als Anteil/Teilmenge ausgewiesen, nie zum Catering addiert. Für spätere Saisons beim Caterer bestätigen.
  - **Kiesplatz – Saison 22-23 Zeile 15:** Datum «2023-01-23» ist widersprüchlich: Event «FC St.Gallen 1879 vs. FC Basel»: das Heimspiel gegen Basel fand am Sonntag 22.01.2023 um 16:30 statt (Historie, Catering, Kontexttabelle, Zutritt). Der 23.01.2023 war ein Montag ohne Spiel. → Belegt korrigiert auf «2023-01-22» (overrides/korrekturen.csv); an Sandro melden.
  - **Kiesplatz – Saison 22-23 Zeile 4:** Datum «2022-07-14» ist widersprüchlich: Event «FC St.Gallen 1879 vs. FC Winterthur» mit Anpfiff 20:30: das Heimspiel gegen Winterthur fand am 23.07.2022 um 20:30 statt (Historie, Kontexttabelle, Zutritt, football-data.co.uk). Am 14.07.2022 gab es kein Heimspiel. → Belegt korrigiert auf «2022-07-23» (overrides/korrekturen.csv); an Sandro melden.
  - **Ticket-CSV – 20260126_MS21_SFC.csv Zeile 0:** Datum «2026-01-26» ist widersprüchlich: Der Dateiname nennt den 26.01.2026, das Heimspiel gegen Servette fand aber am Sonntag 25.01.2026 statt (Historie, Catering, Kontexttabelle, Zutrittsdatei, football-data.co.uk). Der letzte Verkauf in der Datei datiert vom 25.01.2026 17:02, also nach dem Anpfiff um 16:30. → Belegt korrigiert auf «2026-01-25» (overrides/korrekturen.csv); an Sandro melden.

## 13. Grenzen (was die Daten nicht hergeben)

- Keine Verbindung Ticket/Person ↔ Catering-Bon: Konsum je Ticket-Typ, Sektor oder Person ist nicht messbar.
- Kein Zeitstempel im Catering: Konsum-Timing (Halbzeit, vor Anpfiff) und Durchsatz-Engpässe nicht messbar.
- Kein Stand→Sektor-Mapping: kein Sektor-KF.
- Abo-Besuche nur als Näherung 21/22–22/23; Eintritt je Einzelticket 23/24 unvollständig, 24/25 leer.
- Einzelticket-Kurven ohne Abos und ohne Stornoverlauf; Ausverkaufszeitpunkt ohne Kapazität je Tag nicht bestimmbar.
- Kleine Stichproben (rund 18–19 Meisterschaftsspiele pro Saison); Kontexteffekte sind Zusammenhänge, keine Kausalität.
- Wetter: Station St. Gallen (Stundenwerte) als Näherung für das Stadionwetter.
- Merchandise und Deckungsbeitrag: nicht geliefert.

## 14. Klärungsfragen an Sandro / FCSG

| Priorität | Bereich | Frage | Evidenz |
|---|---|---|---|
| Startblocker | Ticketing | Was umfasst SOLL genau, und weshalb wird SOLL bei ausverkauften Spielen als Kapazitätswert gesetzt? | 36 von 108 Pflichtspielen haben ein Kapazitäts-SOLL (z.B. =20036−1930+Gäste). Ticketbasiertes SOLL 25/26 = Einzeltickets je Verkaufsstelle + 2 Abo-Komponenten (11'596–11'850) − Zweitmarkt. Kapazitätskonstanten wechseln (19'200, 20'029, 20'036, 20'088, 20'144). |
| Startblocker | Ticketing | Wie werden Zweitmarkt, Freikarten, Personal und Abo-Sitze im SOLL gezählt? | SOLL-Formeln ziehen den Zweitmarkt ab (Doppelzählung vermeiden); Gratis-/Promotickets sind im SOLL enthalten (Eintrittsquote Gratis/Promo nur 84 %). |
| Startblocker | Catering | Welche VIP-Zahl wird für «Public Netto» (Nenner des Kundenfrankens) von IST abgezogen? | Formeln «=IST − x»: x liegt 25/26 im Mittel 81 Personen über «IST VIP» der Historie, 26/27 identisch. |
| Startblocker | Catering | Gilt CHF 14.50 als KF exkl. MwSt, Summe/Summe aller Pflichtspiele 2025/26 (wir rechnen 14.51)? | Blatt «Entwicklung»: 14.51 exkl. MwSt (gewichtet) für MS+Cup 25/26; die Meisterschaftszeilen sind ungewichtete Mittel. |
| Startblocker | Catering | Sind die Bons (Transaktionen) über alle Zahlungswege vollständig und über die Saisons vergleichbar? | Transaktionen ab 23/24 als Formelsummen (z.B. =14781+153+286); vor 23/24 keine Transaktionen. |
| Startblocker | Catering | Ist der Kiesplatz im Public-Catering-Total enthalten (auch nach 21/22)? Was bedeuten 80/20 und die Sätze 2.6/8.1 %? | 21/22: Contrailer-/Bier-Stände sind frankengenau in der Catering-Datei enthalten. 80/20 = vermutlich MwSt-Aufteilung Take-away/vor Ort; Netto-Formeln 24/25–25/26 teilen noch durch 1.025/1.077. |
| Startblocker | Daten | Bitte Datumsfehler bestätigen bzw. in den Quelldateien korrigieren. | Historie 24.08.2024→24.09.2024; Anpfiff 17.05.2026 14:00→16:30; Catering 16.07.2022→23.07.2022; Kiesplatz 14.07.2022→23.07.2022 und 23.01.2023→22.01.2023; Ticket-CSV 20260126→25.01.2026. |
| Startblocker | Datenschutz | Welche Personenfelder müssen gelöscht werden; ist technische Deduplizierung über UTId/Barcode zulässig? | Einzelticket-Exporte 21/22–24/25 enthalten Namen, Geburtstag, PLZ, Geschlecht (Widerspruch zum Projektantrag). Sie werden beim Einlesen verworfen; UTId nur zur Deduplizierung. |
| Erweiterung | Zutritt | Können die Zutritte Juli–Dezember 2024 und das Spiel vom 23.07.2022 nachgeliefert werden? | 18 Spieltage mit unvollständiger Lieferung (z.B. 2. Hälfte 2024 nur 5–22 Scans je Spiel). |
| Erweiterung | Zutritt | Bitte Toröffnungszeiten je Tor bestätigen und die Bedeutung der Seatinfo-Codes und Reserveleser erklären. | Aus den Scans: Hospitality ≈ 120 min, Fankurve D ≈ 90 min (seit 02.04.2023, vorher 60), Tribünen A/B/C und Gäste ≈ 60 min vor Anpfiff (gesamt 1 %-Punkt im Median 114 min). Seatinfo vor 25/26 als «Sektor D2», danach Codes 1–77. |
| Erweiterung | Ticketing | Export 2024/25 nach 09.12.2024 und Ticket-CSV Cup-Viertelfinal 04.02.2026 nachliefern? | 12 Pflichtspiele ohne vollständige Einzelticket-Daten. |
| Erweiterung | Ticketing | Gibt es Stornos/Rückgaben, einen historischen Verkaufsstand je Tag und die verfügbare Kapazität je Sektor? | Exporte enthalten nur den Endbestand (keine Stornos sichtbar). Ohne Kapazität je Tag kein Ausverkaufszeitpunkt. |
| Erweiterung | Ticketing | Aggregierte Abo-Bestände und Abo-Besuchsquoten je Spiel 21/22–25/26? | Abo-No-Show heute nur als Näherung (Rest = SOLL − Einzeltickets) für 21/22 und 22/23. |
| Erweiterung | Catering | Catering-Umsätze je Viertelstunde und Verkaufsstelle sowie Stand→Sektor-Mapping? | Heute nur Spieltotale; Kiesplatz als einzige Standebene. |
| Erweiterung | Catering | Bitte bestätigen: Enthält die Spalte «Umsatz Netto» der Artikelauswertung 2023/24 und 2024/25 Bruttowerte (inkl. MwSt) und 2025/26 Nettowerte? Welche Basis gilt für künftige Lieferungen? | Bier 4dl, Umsatz laut Datei je Einheit (CHF): 2023/24: 6.00, 2024/25: 5.96, 2025/26: 5.54 – also 6.00 brutto, 2025/26 6.00 / 1.081. Alle 2025/26-Werte × 1.081 (Alkohol) bzw. × 1.026 (übrige) ergeben runde Bruttobeträge. Bis v1.0.1 wurden die Saisons ungleich verglichen; seit v1.1.0 einheitlich brutto (overrides/artikel_basis.csv). |
| Erweiterung | Merchandise | Merchandise-Umsätze je Kanal (Stadionshop, Online, City) und Tag? | Nicht geliefert; Merchandise ist in Phase 1 keine Voraussetzung. |
| Erweiterung | Deckungsbeitrag | Beteiligungsmodell des Clubs am Catering-Umsatz und Einstandspreise je Artikelkategorie? | Steuerungsgrösse laut Antrag ist der DB pro Anwesendem; Phase 1 bleibt beim Umsatz. |

## 15. Prüfkandidaten für Phase 2 (nicht quantifiziert)

| Prüfkandidat | Hebeltyp | Befund Phase 1 | Benötigte Daten |
|---|---|---|---|
| No-Show bei Gross- und Gratisbestellungen | Zweitmarkt/Kommunikation (Clubhebel) | No-Show Einzeltickets 21/22–22/23: Bestellungen ab 10 Tickets 26 %, Gratis/Promo 16 %, Inhouse 25 % vs. Online-Shop 5 %. | Aktuelle Eintrittsdaten je Einzelticket (ZKS) ab 23/24; Zweitmarkt-Nutzung je Segment. |
| Abendspiele: weniger Anwesende, mehr Konsum | Programm/Angebot (Clubhebel); Anstosszeit selbst = Liga | Anwesenheitsquote -4.1 Pp. (belastbar); KF +6.8 % (belastbar), getragen von Bons/Anwesende. | Viertelstunden-Umsätze, um den Mehrkonsum zeitlich zu verorten. |
| Werktagsspiele: tieferer Ø Bon | Angebot für späte Ankünfte (Clubhebel) | Ø Bon -4.0 % (belastbar); KF -4.0 % (Hinweis (Richtung stabil, Grösse unsicher)). | Zeitdaten Catering; Ankunft nach Eingang an Werktagen. |
| Frühere Toröffnung Tribünen A/B/C | Toröffnung/Programm (Clubhebel) | Einlass-Beginn heute: HH (Hospitality) 119 min, D 91 min, A 62 min, B 61 min, B4 (Gäste) 61 min, C 61 min vor Anpfiff. Natürliches Experiment Sektor D (ab 02.04.2023 90 statt 60 min): Ankunft +22.6 min (95 %-KI 19 bis 26), Anteil ≥ 60 min +50 Pp. gegenüber A/B/C. Median Ankunft je Eingang: D 70 min, HH (Hospitality) 69 min, B4 (Gäste) 36 min, B 31 min, A 29 min, C 25 min. | Pilot mit früherer Öffnung einzelner Tore + Standumsätze je Viertelstunde und Stand→Sektor-Mapping (Konsumwirkung messen). |
| Kälte und Wintersortiment | Sortiment (Clubhebel); Wetter = extern | KF +3.6 % (belastbar) je +5 °C; Ø Bon +2.3 % (belastbar). | Artikel je Spiel (heute nur Saisonsummen). |
| Operative Engpässe (Stände zu, Runner/Personal fehlt, Technik) | Standbesetzung/Personal/Payment (Clubhebel) | Spiele mit dokumentiertem operativem Hinweis: Ø Bon -1.3 %, KF -0.4 % gegenüber Erwartung (nicht belastbar); Schliessungen folgen oft tiefer Nachfrage (umgekehrte Kausalität möglich). | Standöffnungen je Spiel strukturiert erfassen; Viertelstunden-Umsätze. |
| Ausverkaufte Spiele: früher Einzelticket-Absatz | Abo-/Zweitmarktprozess (Clubhebel); kein Dynamic Pricing | Halbe Einzelticket-Menge verkauft 11 Tage vor ausverkauften Spielen vs. 4 Tage sonst; Anteil Spieltagsverkauf 4 % vs. 19 %. | Verfügbare Kapazität und Verkaufsstand je Tag (Projektantrag Paket 2). |

## 16. Reproduzierbarkeit

- Code: `2. Modellierung/Python_Auswertung` (Start: `python run_all.py`; Tests: `python -m pytest`).
- Ergebnisse: `FCSG_Phase1_Ergebnisse.xlsx` (alle Tabellen mit Inhaltsverzeichnis), `Abbildungen/`, `Tabellen/` (CSV), `Laufprotokoll.json` (Versionen, Laufzeit, MD5-Prüfsummen aller Eingabedateien).
- Umgebung dieses Laufs: Python 3.12.13, pandas 3.0.6, numpy 2.5.4, openpyxl 3.1.5, python-calamine 0.8.3, statsmodels 0.15.0, matplotlib 3.11.2, xlsxwriter 3.2.9.
- Öffentliche Zusatzdaten (MeteoSchweiz, football-data.co.uk) liegen als Cache im Ordner `external/`; Aktualisierung mit `python scripts/externe_daten_aktualisieren.py`.

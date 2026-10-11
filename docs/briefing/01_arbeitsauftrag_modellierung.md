# Arbeitsfassung: Arbeitsauftrag Modellierung – Datenverknüpfung & Kontextbereinigung

- **Quelldatei:** `docs/sources/Arbeitsauftrag_Modellierung__Datenverknpfung__Kontextbereinigung.pdf`
- **Dokumentstand:** «Arbeitsstand 08.10.2026» (S. 1); 13 Seiten; SHA-256-Präfix `9E1F2B8F5477669A`
- **Fassung dieser Arbeitskopie:** v1, 10.10.2026; Extraktion siehe `README.md`
- **Rolle:** operativer, massgeblicher Auftrag für Phase 1 (ersetzt laut S. 1 das frühere hypothetische Daten-Zielbild)

Quellnahe Zusammenfassung. Zitate in «…». Eigene Einordnungen sind als **Einordnung** markiert.

## 0. Auftrag in einem Satz (S. 1)
Ticketing-, Zutritts-, Catering- und Kontextdaten zu einer nachvollziehbaren Datenbasis **pro Heimspiel**
verbinden; Anwesenheit und Catering-Konsum beschreiben; externe Kontextzusammenhänge mit **einfachen
Modellen** schätzen; wiederkehrende Abweichungen als **Diagnosepunkte** ausweisen. «Nur Aussagen verlangen,
die durch die tatsächliche Datenstruktur gedeckt sind.» Merchandise und feinere Konsumdaten sind
Erweiterungen, keine Voraussetzung.

Arbeitsstand-Hinweis (S. 1): Dateistrukturen und Zahlen stammen aus Retos Sichtung; das Modellierungsteam
prüft sie beim Import gegen die Rohdaten. **Fokus Umsatz, nicht Deckungsbeitrag** (Quelle; Projekt weicht ab → D-003: Steuerungsgrösse DB); Massnahmenquantifizierung
= Phase 2. Umsatzbasis und spätere DB-Steuerung mit FCSG abstimmen.

## 1. Ziel, Scope, beantwortbare Fragen (S. 1–2)
Phase 1:
- Datenquellen, Definitionen, Abdeckung validieren; pro Heimspiel konsistente Baseline (S. 1).
- Anwesenheit/No-Show und Catering-Umsatz je Public-Anwesendem beschreiben und mit Spielkontext verbinden (S. 1).
- KF zerlegen in Bons je Anwesendem × Ø Bon; **Kontextmodelle je Treiber** statt nur Gesamtumsatzmodell (S. 1–2).
- Ankunftskurven und Ticketverkaufsvorlauf als **eigenständige Module**; Verknüpfung mit Konsum nur auf gemeinsamer Spielebene (S. 2).
- Kontextbereinigte Abweichungen + Unsicherheit zeigen, **nicht automatisch als realisierbares Potenzial** (S. 2).

Leitplanken (S. 2): Kapazität fix; **kein Dynamic Pricing, kein Stadionausbau, keine Hospitality**.
Verkaufsquote als Handlungshebel zurückgestellt, Verkaufsverlauf bleibt Analysegegenstand. Keine
Personensegmentierung, kein Personenprofiling.

Heute belastbar (S. 2): Spielebene für Anwesenheit und Catering; Zutritt nach Leser/Sektor und Ankunftszeit;
Einzelkarten nach Tarif/Kanal/Sektor und Vorlauf.
**Nicht versprechen** (S. 2): Konsum je Ticket-Typ/Person, Catering je Viertelstunde, Besucher-Kaufquote,
historische Abo-Besuche aller Saisons, Merchandise-Potenzial.

Phase 2 (S. 2): Massnahmen, Aktivierungsquoten, inkrementelle Effekte erst nach Abnahme Phase 1.

## 2. Datenlandschaft (S. 2–4) – «laut Sichtung», beim Import zu prüfen

| Block | Quelle | Granularität / Abdeckung | Rolle und Einschränkungen | Seite |
|---|---|---|---|---|
| A Ticketing | Zuschauerzahlen-Historie | 1 Zeile/Heimspiel, 21/22–26/27; SOLL, IST, IST VIP, IST Gäste, Zweitmarkt, No-Show, Ausverkauft, Bemerkungen | Lange Anwesenheits-Baseline. SOLL und Zweitmarkt **fachlich zu definieren**; keine Segment-/Verkaufskurve daraus | 2 |
| A | 27 Ticket-CSVs | 1 Zeile/Einzelticket, 25/26–26/27; Tribüne, Block, Reihe, Sitz, Tarif, Verkaufszeitpunkt, Kanal, Preis | Einzelticketmix, Vorlauf; **kein** kompletter Abo-Verlauf, **kein** Besuch je Ticket | 2 |
| A | Saisonabos 26/27 | Snapshot 30.09.2026, ~13 000 Abo-Sitze | Sektor/Tarif/Kanal/Preis; kein historischer Bestand, kein Besuch je Abo; **nicht rückwirkend übertragen** | 3 |
| A | Einzelticket-Exporte 21/22–24/25 | Ticketmerkmale + ZKS-Eintrittszeitpunkt | Eintritt gut befüllt nur 21/22, 22/23; 23/24 teilweise; 24/25 nicht. **Fehlender Eintritt nur bei verifiziert vollständiger Erfassung = No-Show.** Personenfelder ausschliessen | 3 |
| B Zutritt | ErlaubteZutritteHerren | 1 Zeile/erlaubter Drehkreuzdurchgang; ~394 000 Scans, 27 Spiele 25/26–26/27 bis 12.09.2026 | Felder: Datum/Spieltag, TransactionTime, Lesername, Seatinfo, UTId, Errorcode/DisplayMessage. Minuten relativ zum Anpfiff; Leser→Sektor prüfen; Scans ≠ eindeutige Besucher (Mehrfach-/Wiedereintritt); UTId nur geschützt zur technischen Deduplizierung; **keine Ausgänge → keine Aufenthaltsdauer**. Ältere Saisons angekündigt, nicht als vorhanden behandeln | 3 |
| C Catering | Public-Catering-Tabs ab 18/19 | Spiel/Event je Zeile; Saison-Tabs + «Entwicklung» | Public Netto, Bons/Transaktionen, Umsatz inkl./exkl. MwSt, KF, Ø Bon, Zahlungswege; ab 25/26 Umsatz je Verkaufsstelle; **keine Uhrzeit, kein Stand→Sektor-Mapping** | 3 |
| C | Artikelauswertung 23/24–25/26 | Saison-/Durchschnittsspiel-Ebene | Nur Sortimentsdeskription; **keine künstlichen Artikelwerte je Spiel** in Regression | 3 |
| C | Kiesplatz-Abrechnungen 21/22–26/27 | pro Event inkl. Public Viewing | Steuer-/Beteiligungssätze klären; von Stadion-Catering trennen (Doppelzählung prüfen); **MwSt-Sätze sind keine Margen** | 4 |
| D Kontext | Spielkontext-Tabelle 22/23–26/27 | ~90 Heimspiele | Gegner, Tabellenstände, Form, TV, Wetter, Ferien, Feiertage, Events, Anpfiff/Wochentag. **Leere Zelle = nicht erfasst, nicht «Nein».** Wetter = Tagesmittel. Tabellenstand/Form **vor** dem Spiel; Endresultat kein Prädiktor | 4 |

## 3. Datenarchitektur und Verknüpfung (S. 4–5)
Match-Key (S. 4, Liste visuell bestätigt):
1. **Spieldatum** ist primärer Join-Schlüssel, nicht das uneinheitliche Gegner-Label.
2. Einheitliches Datumsformat, Zeitzone **Europe/Zurich**; Zeitstempel auf lokale Spielzeit prüfen; **vor Join Eindeutigkeit je Quelle testen**.
3. Kalender `dim_match` mit stabiler `match_id`, Datum, Wettbewerb, Heim/Auswärts, Gegner, Anpfiff, Saison. Mehrere Events am selben Datum → mit Event/Wettbewerb auflösen und dokumentieren.
4. Nicht-Heimspiele, Public Viewing, andere Events, Dubletten nicht stillschweigend mit Ligaspielen verbinden.

Tabellen (S. 4–5, Namen visuell zugeordnet):

| Tabelle | Granularität / Inhalt |
|---|---|
| `fact_attendance_match` | 1 Heimspiel; SOLL, IST, VIP, Gäste, Definition/Qualitätsstatus |
| `fact_ticket_single` | 1 Einzelticket; Aggregate Spiel × Sektor/Tarif/Kanal/Vorlauftag |
| `snapshot_season_ticket` | separat, mit Stichtag |
| `fact_access` | 1 erlaubter Scan; Aggregat Spiel × Sektor × Ankunftsintervall, ggf. deduplizierte Besucher |
| `fact_catering_match` | 1 Spiel; Public-Anwesende, Bons, Umsatzbasis, Ø Bon |
| `fact_catering_outlet` | nur tatsächliche Standumsätze |
| `fact_article_season`, `fact_kiesplatz_event` | getrennte Granularitäten, eigener Scope |
| `dim_match_context` | 1 Spiel; Variablen mit Quelle, Messzeitpunkt, Missing-Status |
| `mart_match` | **1 Heimspiel pro Zeile**; Inputverfügbarkeit und Zielgrössen explizit markiert |

**Join-Regel (S. 5):** Erst jede Faktentabelle auf Zielebene aggregieren, dann verbinden. Kein Rohdaten-Join
Ticket × Scan × Catering. **Unmatched- und Duplikatreport sind Pflichtoutput.**

Abdeckung (S. 5): je Modul Saisons, Wettbewerbe, Zahl gemeinsamer Spiele, Missing-Anteile, Ausschlüsse.
27 Zutritts-, ~90 Kontext- oder ~100 angestrebte Spiele sind **keine garantierte Modellstichprobe**.
Die 4 Meisterschafts-Heimspiele 26/27 nicht ungewichtet mit Vollsaisons vergleichen.

## 4. KPI-Definitionen und Treiberbaum (S. 5–6)
Formelblock (S. 5, visuell bestätigt):
```
Anwesenheitsquote     = IST / SOLL
No-Show-Quote         = 1 − IST / SOLL
No-Show absolut       = SOLL − IST
Public-Catering-Umsatz = Public-Anwesende × Kundenfranken
Kundenfranken         = Public-Catering-Umsatz / Public-Anwesende
                      = (Bons / Public-Anwesende) × (Umsatz / Bons)
Ø Bon                 = Umsatz / Bons
```
Bedingungen und offene Definitionen (S. 5–6):
- Identität gilt nur bei **gleichem Scope, gleicher Umsatzbasis und vollständigen Bons**.
- «Public Netto» = laut Sichtung **Zuschauer ohne VIP**, **nicht** Nettoumsatz. Gäste, Personal, Freikarten, Scanbereiche fachlich bestätigen; Gäste nicht pauschal ausschliessen.
- **SOLL** klären: verkauft/ausgegeben/reserviert; Abo-/VIP-/Gäste-/Zweitmarktanteile. Zweitmarktsitz nicht doppelt zählen. Kapazität/Verkaufsquote nur mit verifizierter Kapazität.
- **Umsatz:** Brutto und Netto getrennt führen; primäre Vergleichsbasis mit FCSG abstimmen. CHF 14.50 (Antrag) nur auf gleicher MwSt- und Publikumsbasis vergleichen. Preis-, Steuer-, Scope-, Systemwechsel prüfen. DB erst mit echten Kosten/Margen.
- **Bons je Anwesendem ≠ Kaufquote.**
- **Abo-Schätzung:** SOLL − Einzeltickets = Restbestand, nicht automatisch Abos. Abo-No-Show höchstens als gekennzeichnete Näherung für validierte ältere Saisons.

## 5. Analysepakete (S. 6–7)
| Paket | Status | Kerninhalt |
|---|---|---|
| A Baseline & Qualität | Pflicht | Anwesenheit, No-Show, Public-Anwesende, Umsatz, Bons, KF, Ø Bon je Spiel/Saison/Wettbewerb; Verteilungen, Ausreisser. **Saison-KF = Σ Umsatz / Σ Public-Anwesende** (nicht ungewichteter Mittelwert). IST vs. Scans abgleichen |
| B Anwesenheit & Absatz | Pflicht im verfügbaren Scope | No-Show-Kontextmuster; Ticket-Typ-Näherungen nur nach Validierung; Einzelticket-Vorlaufkurven. Kumulierte Einzeltickets ≠ Stadion-Ausverkaufskurve; Stornos/Vollständigkeit prüfen |
| C Catering | Pflicht | KF, Bons/Public-Anwesendem, Ø Bon getrennt modellieren, gemeinsam plausibilisieren; Standumsätze ab 25/26 und Artikelmix deskriptiv separat. Keine Konsumaussage je Ticket-Typ, keine Sektor-KF ohne Nenner/Mapping, keine Viertelstunden-Peaks |
| D Ankunft | Pflicht deskriptiv, Modell optional | Median, Verteilung, Anteile 45 bzw. 15 Min. vor Anpfiff je Spiel/Sektor; Toröffnung, Leserabdeckung, Anpfiff prüfen. Ankunft→Konsum nur aggregiert auf Spielebene; keine Kausalität |
| E Erweiterungen | nach Lieferung | ältere Zutritte, Abo-Historie, Catering-Zeitdaten, Stand→Sektor, Merchandise, DB-Daten |

## 6. Kontextbereinigung und Modellstrategie (S. 7–8)
1. Variablen vorab einordnen (mit FCSG): **extern** (Gegner, Saisonphase, Wetter, Ferien), **Einzelfall** (Anpfiff/TV, Auflagen, Kontingente), **Clubhebel** (Zweitmarktprozess, Kommunikation, Toröffnung/Programm, Sortiment, Standbesetzung, Payment).
2. Wenige begründete Variablen je Zielgrösse; Saison/Wettbewerb/Definitionswechsel beachten; Clubhebel nicht unbemerkt herauskontrollieren; Ankunft ggf. Mediator.
3. Zielgrössen getrennt: Anwesenheitsquote, KF, Bons je Public-Anwesendem, Ø Bon. Verkaufsquote nur mit belastbarem Nenner. Gesamtumsatz nur Plausibilitätscheck.
4. Start mit Mittelwert-/Saisonbaseline, dann einfache lineare/regularisierte Modelle; Logs nur bei positiven Werten mit dokumentierter Rücktransformation; keine GAMs/hierarchischen Modelle als Pflicht.
5. Zeitlich getrennte Validierung / Leave-one-season-out nur bei genug Saisons; Sektorzeilen sind keine unabhängigen Spielkontexte (S. 8).
6. Out-of-sample-Fehler, Stabilität, Intervalle, Missing-Behandlung, Sensitivität dokumentieren. «nicht belastbar schätzbar» ist zulässig (S. 8).

**Wichtig (S. 8):** KF und Ø Bon/Bons sind algebraisch verknüpft; Retos Korrelationen sind keine Kausalnachweise;
Elastizität aus 22 Spielen ist vorläufig.

## 7. Diagnosekarte (S. 8–9)
```
Diagnoselücke = erwarteter Wert unter Kontext − beobachteter Wert
```
Positiv = unterdurchschnittliche Beobachtung. **Nicht** mit Residuum (beobachtet − erwartet) verwechseln.
Je Spiel: Zielgrösse, Beobachtung, Erwartung, Bandbreite, Datenqualität, plausible Erklärung.
CHF-Übersetzung = **modellbasierte Referenzlücke, kein realisierbarer Mehrumsatz**:
- Konsum: (erwarteter KF − beobachteter KF) × beobachtete Public-Anwesende.
- Anwesenheit: nur bei konsistentem SOLL/Public-Scope; CHF nur mit explizit angenommenem inkrementellem Konsum.
- **Keine Addition** von Lücken aus KF, Bonsrate und Ø Bon (Mehrfachzählung).
- Rest enthält Messfehler, ausgelassene Variablen, Zufall; wiederkehrende Lücken = Prüfkandidaten für Phase 2 (S. 9).

## 8. Datenschutz und QS (S. 9)
Personenfelder vor Analysen ausschliessen; keine Rohdaten/Personeninhalte nach Notion. Pseudonyme IDs bleiben
potenziell personenbezogen. Veröffentlichung nur aggregiert, kleine Gruppen unterdrücken (Regel vereinbaren).
Bereinigung mit Sandro klären. Automatisiert testen: Vollständigkeit, Datum/Zeitzone, Join-Kardinalität,
Umsatzabgleich, Einheiten, Definitionswechsel. **Fehlend ≠ null; fehlender Eintritt ≠ automatisch No-Show.**
Arbeit im Datenraum.

## 9. Deliverables Phase 1 (S. 9–10)
A Datenmodell & Abdeckungsmatrix · B Baseline & deskriptive Module (Retos Zahlen reproduzieren oder Abweichung
erklären, nicht als Soll übernehmen) · C Kontext-Effekt-Matrix · D Diagnosekarte (keine Summe theoretischer
Lücken als Umsatzversprechen) · E Übergabe (Code im Datenraum, Methodennotiz, offene Datenanforderungen,
Prüfkandidaten Phase 2; Merchandise als vorhanden/nicht geliefert dokumentieren).

## 10. Abnahmekriterien (S. 10)
Kernquellen inventarisiert; eindeutige Spielzuordnung, Join-Prüfungen, nicht zuordenbare Fälle dokumentiert ·
jede KPI mit verifiziertem Scope, Nenner, Umsatzbasis, Quellenpfad · tatsächliche gemeinsame Stichprobe je
Analyse · Baseline erstellt, Vorlauf/Ankunft ausgewertet · Kontextmodelle validiert oder Nicht-Schätzbarkeit
belegt · Diagnosekarte trennt Kontextassoziation, ungeklärte Abweichung, potenziellen Clubhebel · keine
Pflicht-Outputs ohne Lieferung; Phase 2 nicht vorweg quantifiziert.

## 11. Klärungsfragen an Sandro / FCSG (S. 10–11)
Vor belastbarer KPI-Berechnung:
1. Was umfassen SOLL, IST, VIP, Gäste, Public Netto? Zählung von Zweitmarkt, Freikarten, Personal, Abo-Sitzen?
2. Umsatz-/MwSt-Basis der CHF 14.50; tatsächliche Clubserlöse; Umsatzfokus Phase 1 bestätigen.
3. Bons über Saisons vollständig/vergleichbar inkl. aller Zahlungswege? Scope-/Systemwechsel?
4. Wieder-/Mehrfachzutritte; Bedeutung UTId, Seatinfo, Reserveleser; Leser-/Sektormappings; Toröffnungszeiten.
5. Welche Personenfelder löschen; ist technische Deduplizierung zulässig?

Für Erweiterungen (nicht Startblocker; S. 11, Nummern visuell bestätigt): 1. ältere Zutritte, Abo-Historie ·
2. Catering-Zeitintervalle, Stand→Sektor · 3. Merchandise nach Kanal/Tag, Matchday-Attribution ·
4. Kiesplatz-Sätze, 80/20, Abgrenzung · 5. welche Kontextfaktoren Clubentscheidungen; Ereignisfelder, Wetter
im Zeitfenster · 6. Stornos/Rückgaben in Ticket-CSVs, historischer Gesamtverkaufsstand, verfügbare Kapazität.

**Nächster Arbeitsschritt laut Auftrag (S. 11):** Dateninventar und KPI-Definitionen freigeben, `mart_match` mit
Abdeckungsreport bauen, dann Baseline und sparsame Kontextmodelle.

## 12. Folgeauftrag Phase 2 – zurückgestellt (S. 11–13)
Nur als Vorarbeit erhalten, **nicht in Phase 1 umsetzen.** Marginal Value Table (CHF Umsatz) je Hebel/Spiel/Sektor:
−1 pp No-Show · +0,1 Catering-Transaktionen je Anwesendem · +CHF 1 Ø Catering-Bon · +CHF 1 Ø Merchandise-Warenkorb ·
+1 pp Merchandise-Konversion (Vorzeichen per Sichtprüfung ergänzt). Rechenlogiken (S. 12): zusätzliche Anwesende =
ausgegebene Tickets × 0,01; zusätzliche Besucher konsumieren nicht automatisch 100 % des Durchschnitts;
Durchsatz-Obergrenze = beobachtete Nachfrage; Merchandise Online/City nur mit Matchday-Attributionsfenster (S. 13).

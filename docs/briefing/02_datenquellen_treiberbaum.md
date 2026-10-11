# Arbeitsfassung: FCSG Datenquellen & Treiberbaum – Übersicht für Modellierungsauftrag

- **Quelldatei:** `docs/sources/FCSG Datenquellen & Treiberbaum – Übersicht für Modellierungsauftrag.pdf`
- **Dokumentstand:** «Oct 8, 2026 · @Reto» (S. 1); «Stand der Analysen: 08.10.2026, Spiele bis 12.09.2026» (S. 7); 7 Seiten; SHA-256-Präfix `0DD5125A4919C06B`
- **Fassung dieser Arbeitskopie:** v1, 10.10.2026; alle Seiten visuell geprüft, Treiberbaum (S. 6) aus Bild transkribiert
- **Rolle:** Sichtung der von Sandro gelieferten Dateien durch Reto. **Alle Zahlen sind Sichtungswerte**, beim Import zu reproduzieren (Arbeitsauftrag S. 1, S. 9) – nicht als Sollergebnis übernehmen.

## Überblick (S. 1)
Drei Datenquellen plus Kontext, gemeinsamer Schlüssel **Spieldatum**, «nie über das Gegner-Label».
Spaltenwörterbuch im Excel «FCSG_Daten-Handbuch» (**liegt hier nicht vor**).

| Quelle | Wichtigste Dateien | 1 Zeile = | Abdeckung | Liefert für Treiberbaum |
|---|---|---|---|---|
| 1 Ticketing | Zuschauerzahlen-Historie, 27 Ticket-CSVs, Saisonabos 26/27, Einzeltickets-Exporte | Spiel (Historie) bzw. verkauftes Ticket | Historie 21/22–26/27, Einzeltickets 21/22–24/25 | Kapazität, verkaufte Tickets (SOLL), Besucher (IST), No-Show, Abo-/Einzelmix, Kanal, Tarif, Vorlauf |
| 2 Zutritt | ErlaubteZutritteHerren | erlaubter Durchgang am Drehkreuz | 25/26 und 26/27 (27 Spiele), ältere folgen | Ankunftszeit vor Anpfiff, Ankunft nach Sektor/Tor, Besucherzahl je Spiel (Scans) |
| 3 Umsätze | Public-Catering-Tabs je Saison, Artikelauswertung, Kiesplatz-Abrechnungen | Spiel bzw. Artikel/Saison | Catering 18/19–26/27, Artikel 23/24–25/26 | Umsatz, Bons, KF, Ø Bon, Sortiment-Mix |
| 4 Kontext | Spielkontext_Tabelle | Heimspiel | 22/23–26/27 | Gegner, Tabelle, Form, TV, Wetter, Ferien, Feiertag, Events |

## Quelle 1 – Ticketing (S. 2)
No-Show definiert als 1 − IST/SOLL.

| Datei | Aufbau | Ablesbare Zahlen | Grenzen |
|---|---|---|---|
| Ticketing-Zuschauerzahlen-Historie | 1 Zeile/Heimspiel, 21/22–26/27 | SOLL, IST, IST VIP, IST Gäste, Zweitmarkt, No-Show, Ausverkauft, Bemerkung | keine Segmente, kein Verkaufsverlauf; SOLL/Zweitmarkt-Definition offen |
| 27 Ticket-CSVs (25/26–26/27) | 1 Zeile/verkauftes Einzelticket: Tribüne, Block, Reihe, Sitz, Tarif, Verkaufsdatum/-zeit, Kanal, Preis | Vorlauf, Kanal-/Tarifmix, Preis je Sektor, Gruppengrösse je Rechnung | nur Einzeltickets; kein Besuch je Ticket |
| Saisonabos Herren 26/27 | 1 Zeile/Abo-Sitz (~13 000), Stand 30.09.2026 | Verteilung nach Sektor, Tarif, Kanal, Preis | Momentaufnahme; keine früheren Saisons; kein Besuch je Abo |
| Einzeltickets-Exporte 21/22–24/25 | 1 Zeile/Ticket: Verkaufsmodul, Block, Preis, Eintrittszeitpunkt (ZKS) | Eintritt je Einzelticket (gut befüllt nur 21/22, 22/23), Kanal, Preis | **enthalten Personendaten**; Eintritt 23/24 teilweise, 24/25 leer |

Sichtungswerte (S. 2, vorläufig): Ø IST 22/23–25/26 ≈ 14.5k–14.8k; Ø SOLL ≈ 17.6k–18.1k; No-Show 16–19 %.
Abo-Anteil (SOLL − Einzeltickets) 21/22, 22/23 ≈ 63–65 % (Näherung, VIP/Gäste mitgezählt). No-Show nach Ticketart
(21/22, 22/23): Einzel ≈ 9–12 %, Abo ≈ 20–29 %. Eintrittsquote Webshop/Connect Online ≈ 90–95 %, Inhouse ≈ 71–74 %.
Nicht ablesbar: Personen-/Segmentebene, Abo-Entwicklung vor 26/27, Preiswirkung.

## Quelle 2 – Zutritt (S. 2–3)
| Spalte | Inhalt | Zweck im Modell |
|---|---|---|
| Datum, Spieltag | Spieldatum, Textlabel mit Wettbewerb und Gegnerkürzel | Schlüssel (nur über Datum) |
| TransactionTime | Zeitstempel Durchgang | Ankunftskurve relativ zum Anpfiff |
| Lesername | Drehkreuz/Leser mit Sektorpräfix (z. B. A1.1, HH-Reserve) | Ankunft nach Sektor und Tor |
| Seatinfo | Platz-/Zusatzinfo am Leser | Bedeutung offen |
| UTId | pseudonyme Ticket-ID | nur technisch, nicht in Resultaten |
| Errorcode, DisplayMessage | 0 = Durchgang erlaubt | Datei enthält nur erlaubte Zutritte |

Umfang ~394 000 Scans, 27 Heimspiele (25/26 und 26/27 bis 12.09.2026). Sichtungswerte (S. 3): Scans Ø 0.4 % unter IST
(meist < 1 %); Median Ankunft ≈ 37 Min. vor Anpfiff; ≈ 41 % ≥ 45 Min. vorher; ≈ 17 % in letzten 15 Min.;
Sektorunterschiede (D, Haupttribüne, A/B, C), «Auslöser ist die Toröffnung» (Diagramm «Ankunftskurve nach Sektor»,
22 Ligaspiele – **liegt nicht vor**). Nicht ablesbar: Aufenthaltsdauer (keine Ausgänge), wer konsumiert, Spiele vor 25/26.

## Quelle 3 – Umsätze (S. 3–4)
KF hier = Umsatz / **Public Netto (Zuschauer ohne VIP)** (S. 3).

| Datei | Aufbau | Ablesbare Zahlen | Grenzen |
|---|---|---|---|
| Umsatz Public Catering ab 18/19 | 1 Zeile/Spiel/Event, Tab je Saison + «Entwicklung» | Public Netto, Transaktionen, Umsatz inkl./exkl. MwSt, KF, Ø Bon, Zahlungsweg (Payfix, Just Eat, Gutschein); ab 25/26 Umsatz je Verkaufsstelle | kein Artikel, keine Uhrzeit, keine Zuordnung Stand→Sektor |
| Artikelauswertung Meisterschaft | 1 Zeile/Artikel bzw. Gruppe, 3 Saisons nebeneinander | Menge, Umsatz netto (Total und pro Spiel), Umsatzanteil | nur Saisonsummen |
| Abrechnung Kiesplatz 21/22–26/27 | 1 Zeile/Event inkl. Public Viewing (z. B. WEURO) | Brutto/Netto nach Satz 2.6 % und 8.1 %, Anteil 80/20 | Bedeutung der Sätze/Anteile offen |

Sichtungswerte (S. 4, vorläufig): Catering-Umsatz inkl. MwSt (Meisterschaft, Herren) ≈ 2.8 Mio. CHF (21/22) →
≈ 4.0 Mio. CHF (25/26); KF inkl. MwSt 13.68 → 15.27 CHF (Σ Umsatz / Σ Zuschauer). Bons ≈ 0.95 je Anwesendem,
Ø Bon ≈ 16.70 CHF (25/26 + 26/27 inkl. Cup/Europa). Korrelation KF–Ø Bon r = 0.87, KF–Bons/Anwesendem r = 0.75
(«Zusammenhang, keine Kausalität»). Alkohol 25/26 ≈ 49 % (23/24: 54 %), Food 33 %, alkoholfrei 15 %; Bier 4 dl
grösster Artikel, dann Bratwurst. Elastizität Umsatz/Zuschauer ≈ 1.14 aus 22 Spielen («Modell, nicht gemessen»).
Nicht ablesbar: Segmentausgaben, Konsumzeitpunkt, Ort, Merchandise, Hospitality.

## Kontext (S. 4–5)
Spielkontext-Tabelle 22/23–26/27, ~90 Heimspiele, über Datum verknüpfbar.

| Kontextvariable | Quelle | Wirkt vermutlich auf | Hinweis |
|---|---|---|---|
| Gegner, Tabellenstand Gegner und FCSG vor dem Spiel, Form (letzte 5) | Spielkontext | Verkaufsquote (SOLL), No-Show | Stand vor Spiel bekannt → als Treiber zulässig |
| Wochentag, Anpfiffzeit, TV | Historie, Spielkontext | Verkaufsquote, Ankunftszeit, Konsum | Anpfiff 14:00–20:30 vorhanden |
| Schulferien, Feiertag, Parallelevents, besondere Anlässe | Spielkontext, Bemerkung Historie | No-Show, Verkaufsquote | **Leere Zelle = nichts erfasst, nicht «Nein»** |
| Temperatur, Niederschlag, Wind | Spielkontext, Wetter-Text im Catering | No-Show, Konsum (Getränkemix) | nur Tagesmittel |
| Resultat | Spielkontext | nichts (erst nach Spiel bekannt) | nicht als Treiber; allenfalls für Folgespiele |

Vorgeschlagene Externalisierung (S. 5): 1. Treiberbaum auf Spielebene (Kapazität, Verkaufsquote, Anwesenheitsquote,
Ausgabe je Anwesendem) · 2. je Treiber ein einfaches Modell (z. B. log-Grösse auf wenige Kontextvariablen) ·
3. «Der Rest (Residuum) ist der Teil, den der Club beeinflussen kann» · 4. ~18 Spiele/Saison, wenige Variablen.
**Einordnung:** Punkt 3 widerspricht dem Arbeitsauftrag S. 8–9 (siehe `10_synthese_widersprueche.md`, W-06);
massgeblich ist der Arbeitsauftrag.

## Treiberbaum (S. 6) – aus Bild transkribiert
Titel im Bild: «Die Menge ist gut messbar, unter dem Bon fehlen die Daten». Legende: Farbe = Datenquelle
(Ticketing blau, Zutritt orange/rot, Umsätze grün), gestrichelt = nicht in den Daten.

```
Catering-Umsatz pro Spiel [Umsätze]
├─ × Anwesende (IST) [Ticketing; Quelle: Historie, Zutritt]
│   ├─ × Verkaufte Tickets [Historie (SOLL)]
│   │   ├─ + Abos (SOLL − Einzel)          [Ticketing, indirekt]
│   │   └─ + Einzeltickets                 [Ticket-CSV, Historie]
│   └─ × Anwesenheitsquote = 1 − No-Show
│       ├─ No-Show Abos                    [nur 21/22, 22/23, Näherung]
│       └─ No-Show Einzeltickets           [Einzeltickets 21/22, 22/23]
└─ × Kundenfranken [Catering]
    ├─ × Bons je Anwesendem [Catering]
    │   ├─ Zeitfenster vor Anpfiff         [Zutritt 25/26 und 26/27]
    │   └─ Wartezeit am Stand              [gestrichelt: nicht in den Daten]
    └─ × Ø Bon (CHF) [Catering]
        ├─ Sortiment-Mix                   [Artikel, nur pro Saison]
        └─ Preis je Artikel                [gestrichelt: nicht in den Daten]
Kontext (Gegner, Tabelle, Ferien, Wetter, TV) → «wirkt auf jeden Knoten»
```
Lesehilfe (S. 6, Text): Umsatz = Anwesende × KF; Anwesende = verkaufte Tickets × Anwesenheitsquote;
KF = Bons je Anwesendem × Ø Bon; Kontext wird pro Treiber modelliert.
**Extraktionsvorbehalt:** Die Kanten unter «Zeitfenster vor Anpfiff» / «Sortiment-Mix» haben im Bild kein
explizites Operatorzeichen; sie sind als erklärende Unterknoten, nicht als Multiplikation zu lesen.

## Datenlücken und Fragen an Sandro (S. 6–7)
- Grösste Lücke: keine Verbindung Ticket ↔ Konsum; Treiberbaum nur auf Spielebene füllbar.
- Segmente nur nach Sektor, Ticket-Typ, Tarif – nie nach Personen.
- Kein Viertelstunden-/Halbzeit-Export; Ankunft→Konsum bleibt Hypothese.
- Standumsatz ab 25/26 ohne Stand→Sektor.
- Abo-Besuch nur näherungsweise, 21/22 und 22/23. Anfrage: Abo-Bestand und Besuchsquote je Spiel, aggregiert.
- Definitionen offen: SOLL, Zweitmarkt, MwSt-Basis der CHF 14.50, Beteiligungsmodell Catering.
- **Datenschutz:** Einzeltickets-Exporte enthalten Personendaten – «widerspricht dem Projektantrag»; nur Aggregate, Klärung mit Sandro.
- Stichprobe 26/27: erst 4 Meisterschafts-Heimspiele.

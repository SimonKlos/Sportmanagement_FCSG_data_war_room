# Arbeitsfassung: Projektantrag – Untapped Business (FC St.Gallen 1879)

- **Quelldatei:** `Quellen und interne Dokumentation/sources/Projektantrag_Untapped_Business_FCSG_2.pdf`
- **Dokumentstand:** 25.09.2026 (S. 1); 2 Seiten; SHA-256-Präfix `A2851DE9CA2CD28B`
- **Fassung dieser Arbeitskopie:** v1, 10.10.2026; reine Textextraktion, keine Sichtprüfung nötig (Fliesstext)
- **Rolle:** ursprünglicher Antrag. Mehrere Annahmen zu Datenpaketen und Steuerungsgrösse sind durch den
  Arbeitsauftrag vom 08.10.2026 überholt (siehe `10_synthese_widersprueche.md`).

## Eckdaten (S. 1)
Modul «Sportmanagement in der Praxis (HS26)», Universität St.Gallen; Praxispartner FC St.Gallen 1879;
Thema 2 von 4 «Untapped Business – Was unsere Daten über Ticketing, Catering und Merchandise verraten».
FCSG-Ansprechpersonen: CEO sowie Sandro dal Farra (Projekt-Ansprechperson). Gruppe: 5 Studierende.
**Termine:** Upload Schlusspräsentation 25.11.2026 (Canvas); Praxistag FCSG 4.12.2026.

## Ausgangslage (S. 1)
«Matchday-Ertrag = Kapazität × Ticketing-Verkaufsquote × Anwesenheitsquote × Ausgabe pro Anwesendem
(Catering, Fanshop)». No-Show «rund 17%»; Kundenfranken Catering **CHF 14.50** (Basis nicht angegeben).
Offen, ob zusätzlich Anwesende gleich viel konsumieren. Spielkontext muss herausgerechnet werden, bevor
Potenzial benannt wird.

## Auftrag (S. 1)
Hauptfrage: «Wo liegt ungenutztes Umsatzpotenzial, wenn der Spielkontext herausgerechnet ist?» Dazu
Veränderung von Auslastung/Konsum über Anspielzeiten, Gegner, Jahreszeiten. Ergänzend Segmente (Sektor,
Ticket-Typ, Tarif – nicht Einzelpersonen). Ergebnis laut Antrag: «quantifizierte Umsatzpotenziale mit einer
Priorisierung».

## Vorgesehene Datenpakete laut Antrag (S. 1–2)
1. **Spielkontext-Tabelle** – baut die Gruppe selbst, 1 Zeile/Spiel, drei Saisons (~100 Spiele): Datum,
   Anstosszeit, Wochentag, Wettbewerb; Gegner, Tabellenstand beider Teams, letzte fünf Resultate; TV,
   Gästefan-Kontingent; **Wetter zur Anstosszeit** (MeteoSchweiz); Schulferien/Feiertage Kanton SG,
   Parallelevents; besondere Anlässe.
2. **Kapazität und Absatzverlauf** – Bruttokapazität je Sektor mit Sperrungen/Sichtqualität; Verkaufsstand je Tag vor Anpfiff.
3. **F&B und Merchandise** – Catering je Spiel, Verkaufsstelle und **Viertelstunde**; Zuordnung Verkaufsstelle→Sektor;
   Umsatz und **Deckungsbeitrag je Artikelkategorie**; Merchandise je Spiel und Kanal (Stadionshop, Online, City).

«Keine Personendaten und keine Einzelbons, sondern nur Aggregate. Gearbeitet wird im Datenraum ohne Export.»
Die Spielkontext-Tabelle bleibt beim FCSG (S. 2).

## Ziele (S. 2)
1. Spielkontext verstehen (Wirkung auf Auslastung, Konsum) · 2. Potenzial bereinigt benennen (Spiele, Sektoren,
Zeitpunkte) · 3. Absatzverlauf lesen (früh/spät/nicht ausverkauft → Preisstruktur vor Saison) ·
4. Datenbasis sichern (Spielkontext-Tabelle als gepflegte Grundlage für FCSG).

## Leitplanken (S. 2)
- **Kein Dynamic Pricing** – weder Massnahme noch Prüfauftrag noch Nebenszenario.
- Steuerungsgrösse **Deckungsbeitrag pro Anwesendem**; KF dient der Kommunikation (Artikelstamm mit Einstandspreisen nötig).
- Fokus Matchday: «Publikum und Hospitality am Spieltag».
- Datenschutz vor Bequemlichkeit: **ausschliesslich im bereitgestellten Datenraum, NDA pro Person.**

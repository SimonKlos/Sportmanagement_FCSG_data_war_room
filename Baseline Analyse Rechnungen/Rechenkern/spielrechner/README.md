# Spielrechner v2 (D-047)

Eine **einzelne HTML-Datei** für den FCSG: Spielplan importieren, Kontext automatisch holen, Erwartung je Heimspiel,
nach dem Spiel IST eintragen. Kein Python, kein Server, keine Installation beim FCSG. Für den automatischen Abruf von
Wetter und Ferien braucht der Browser Internet; ohne Internet rechnet das Tool mit Normalwerten und Handeingaben.

## Ablauf in der Datei

| Schritt | Was passiert |
|---|---|
| 1 Spielplan importieren | CSV-Datei oder Zeilen aus Excel einfügen: Datum, Anstoss, Gegner, optional Wettbewerb, SOLL, VIP. Vorlage im Tool. |
| 2 Kontext holen | Wochentag und **Anstoss-Slot** aus Datum und Anstoss (Regel wie `utils.anstoss_slot`), **Top-Gegner** aus dem Namen (GC ausgenommen), **Schulferien Stadt SG** aus der hinterlegten Liste (Spielkontext-Tabelle v5, bis 31.12.2027), danach **Kanton SG** über OpenHolidays (Hinweis: Stadt kann abweichen, z.B. Sportferien). **Wetter**: Open-Meteo-Prognose (ca. 16 Tage) bzw. Ist-Wetter bis 92 Tage zurück, sonst **Normalwert** (MeteoSchweiz St. Gallen 2018–2026, Monat × Stunde; Regen als Wahrscheinlichkeit). **Parallelanlässe** aus der Kontexttabelle nur als Hinweis (nicht im Modell). |
| 3 Prognose | Anwesenheitsquote, Anwesende, Kundenfranken, Bons je Anwesendem, Ø Bon, Catering-Umsatz mit 80 %-Band; Treiber-Zerlegung des KF je Spiel. |
| 4 IST | Zuschauer, VIP, SOLL, Catering-Umsatz exkl. MwSt, Bons je Spiel (Formular oder CSV). Vergleich beobachtet vs. erwartet; **Saisonniveau lernt** aus den IST-Spielen. |

Weitere Ansichten: Rückblick (Run-4-Spiele und eigene IST-Einträge), Daten (Import, Saisondatei, Quellen), Lesehilfe.

**Gestaltung:** angelehnt an die Impulse-Summit-Seite: dunkler Grundton, Hero mit FCSG-Logo, grosser Typografie und Faktenzeile
(nächstes Heimspiel, erwarteter Saisonumsatz, fehlende IST), Saisonplan als Zeitleiste nach Monaten mit Farbkante je Anstoss-Slot,
Hell/Dunkel umschaltbar, mobil nutzbar. Das Clublogo liegt freigestellt in `assets/fcsg_logo.png` und wird beim Erzeugen eingebettet
(ohne Datei erscheint ein Textzeichen).

**Rechenregeln** (identisch mit dem Rechenkern, geprüft in `tests/spielrechner_logik.test.mjs`):

- Erwartung = Saisonniveau + Kontextterme aus `koeffizienten.csv` (log bzw. logit), Band = ± 1.2816 × RMSE (Leave-one-match-out).
- Wetter wie `fcsg/sources/extern.py`: Temperatur des Stundenintervalls, das den Anpfiff enthält; Regen = ≥ 0.5 mm in den Intervallen mit Ende in (Anpfiff − 2 h, aufgerundete Anpfiffstunde].
- Saisonniveau: Saison mit ≥ 10 Modellspielen = Modellwert. Sonst Startwert (Modellwert der Saison bzw. letzte volle Saison) plus Mittel der IST-Abweichungen, gedämpft (Gewicht = Anzahl Modellspiele, mindestens 3). Das beurteilte Spiel selbst wird beim Vergleich ausgelassen.
- IST-Kennzahlen: Public = IST − VIP; KF = Umsatz / Public; Bons/Kopf = Bons / Public; Ø Bon = Umsatz / Bons. Fehlende Felder bleiben leer (fehlend ≠ 0).

## Speichern

Automatisch im Browser (localStorage). Zusätzlich **Saisondatei** (JSON) zum Sichern, Weitergeben und Laden auf einem
anderen Gerät, und Export der Übersicht als CSV. Testversion und echte Version verwenden getrennte Speicher; eine
Saisondatei mit echten Daten lässt sich nicht in die Testversion laden und umgekehrt.

## Erzeugen

```bash
cd "Baseline Analyse Rechnungen/Rechenkern"
python spielrechner/build.py --testdaten --ausgabe <Ordner>/Spielrechner_TEST.html          # künstliche Testdaten
python spielrechner/build.py --testdaten --demo --kontext "<Spielkontext_Tabelle_FCSG_5.xlsx>" --ausgabe <Ordner>/index.html   # öffentliche Demo (Vercel): künstliche Zahlen, realistische Saisons, echte Ferien/Anlässe
python spielrechner/build.py --run4 "../run4_anstoss-slot_2026-11-02" \
    --mart "../run4_komplett_2026-11-05/kern_phase1/Tabellen/mart_match.csv" \
    --kontext "<Spielkontext_Tabelle_FCSG_5.xlsx>" --ausgabe <Ordner>/FCSG_Spielrechner.html
```

Koeffizienten aus `run4_anstoss-slot_2026-11-02/Tabellen` (gleiche Modellspezifikation wie Run 4 komplett, D-048).

**Vertraulich:** Die Datei mit echten Werten enthält Clubzahlen je Spiel (aggregiert). Nicht ins Repo legen
(`.gitignore`: `*Spielrechner*.html`), nicht öffentlich publizieren; Weitergabe nur an Team und FCSG.

## Externe Dienste und Lizenz

| Dienst | Zweck | Gesendet | Lizenz / Bedingung |
|---|---|---|---|
| Open-Meteo | Wetterprognose und Ist-Wetter | Koordinaten der Station St. Gallen | CC BY 4.0; kostenlos nur nicht-kommerziell. **Für den Betrieb beim FCSG Abo abschliessen oder auf MeteoSchweiz Open Data umstellen** (Entscheid FCSG). Im Tool abschaltbar. |
| OpenHolidays | Schulferien Kanton SG nach Ende der hinterlegten Stadt-Liste | Datumsbereich, Kanton | offene API |
| Google Fonts | Schrift Montserrat | – | ohne Internet Systemschrift |

Keine externen Skripte. Clubzahlen verlassen den Browser nie.

## Prüfungen

- `tests/test_spielrechner.py`: Aufbau, Kennzeichnung Testdaten, Kalender aus der Kontexttabelle, Normalwerte gegen die Stundenwerte, fehlende VIP bleiben leer, keine externen Skripte; startet `tests/spielrechner_logik.test.mjs` (Node.js) für die Rechenlogik im Browsercode.
- Live-Abruf Open-Meteo und OpenHolidays sowie Darstellung (Desktop, 375 px, hell/dunkel) in Chrome geprüft (07.11.2026, Testdaten).

## Offen

- Lizenzentscheid Wetterquelle beim FCSG (siehe oben).
- Pflege: Nach Ende 2027 Stadt-Ferien in der Kontexttabelle nachtragen und Datei neu erzeugen; neue Saison im Modell erst nach Neuschätzung (Rechenkern).
- Weitere Kontextmerkmale (TV, Tabellenstand, Parallelanlässe) sind nicht im Modell und bleiben Hinweise.

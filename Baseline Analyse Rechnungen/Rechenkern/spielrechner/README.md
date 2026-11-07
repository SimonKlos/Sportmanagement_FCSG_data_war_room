# Spielrechner (D-047) – Entwurf

Erzeugt eine **einzelne HTML-Datei**, die beim FCSG ohne Python, Server oder Internet im Browser läuft.

| Bereich | Inhalt |
|---|---|
| Spiel vorab | Saisonniveau, Wochentag + Anstosszeit (automatisch dem Anstoss-Slot zugeordnet, Hinweis bei Ansetzungen mit weniger als 3 Vergleichsspielen), Gegner, Temperatur-/Regenprognose, Ferien, erwartete Tickets und VIP eingeben → erwartete Anwesenheitsquote, Anwesende, Kundenfranken, Bons, Ø Bon, Catering-Umsatz mit 80 %-Band |
| Spiele im Rückblick | Je Spiel beobachtet vs. erwartet, Abweichung, Status über/im/unter Band |
| Saisonübersicht | Anzahl Spiele über/unter dem Erwartungsband je Saison und Kennzahl |
| Lesehilfe | Kontext vs. Clubhebel, Grenzen, Pflege |

Grundlage sind die Run-4-Tabellen (`koeffizienten.csv`, `erwartung_je_spiel.csv`, D-046) und `mart_match.csv`
(Gegner, SOLL, VIP je Spiel).

## Erzeugen

```bash
cd "Baseline Analyse Rechnungen/Rechenkern"
python spielrechner/build.py --testdaten --ausgabe <Ordner>/Spielrechner_TEST.html          # künstliche Testdaten
python spielrechner/build.py --run4 "../run4_anstoss-slot_2026-11-02" \
    --mart "../run3_kontext-v5_2026-10-14/ralf_kern_phase1/Tabellen/mart_match.csv" --ausgabe <Ordner>/FCSG_Spielrechner.html
```

**Vertraulich:** Die Datei mit echten Werten enthält Clubzahlen je Spiel. Nicht ins Repo legen (`.gitignore`), nicht
öffentlich publizieren; Weitergabe nur an Team und FCSG.

## Prüfungen

- `tests/test_spielrechner.py`: Aufbau, Testdaten-Kennzeichnung, Vorhersageformel, fehlende VIP-Werte bleiben leer.
- Die Rechenlogik der Seite (JavaScript) wurde mit einer Browser-Attrappe in Node gegen die Formel nachgerechnet.

## Offen

- Übernahme des Slot-Modells als Zahlenbasis (D-046) und Form/Weitergabe an den FCSG (D-047) durch das Team.
- Pflegeprozess beim FCSG: neue Spiele in der Kontexttabelle → `run4.py` → `build.py`.
- Vorschau nutzt das Saisonniveau einer vergangenen Saison; eine neue Saison hat noch keinen eigenen Saisoneffekt.

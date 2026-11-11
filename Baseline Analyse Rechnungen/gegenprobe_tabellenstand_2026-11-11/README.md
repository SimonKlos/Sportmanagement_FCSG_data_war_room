# Gegenprobe Tabellenstand und Form – 11.11.2026

**Frage:** Erklären Tabellenstand, Punkte pro Spiel und Form (FCSG und Gegner, jeweils vor dem Spiel) Anwesenheit und Konsum **zusätzlich** zum Run-4-Kontext (Anstoss-Slot, Top-Gegner, Temperatur, Regen, Schulferien, Saison)?

**Methode:** Skript `Rechenkern/scripts/gegenprobe_tabellenstand.py`. Gleiche Schätzung wie das Hauptmodell (Meisterschaft ab 2022/23, OLS mit Saisoneffekten, HC3), je Variante ein zusätzliches Merkmal, identische Stichprobe (73 bzw. 57 Spiele). Vergleich: Koeffizient mit 95 %-KI, Zuwachs der erklärten Streuung innerhalb Saison, Vorhersagefehler an ausgelassenen Saisons (LOSO). Merkmale aus den öffentlichen Resultaten (`fcsg/sources/extern.tabelle_vor_spielen`). Ergebnis: `gegenprobe_tabellenstand.csv`. Datenstand Lieferung 01.10.2026, Rechenkern Run 4.

## Ergebnis

| Zielgrösse | Belastbar zusätzlich? | Detail |
|---|---|---|
| Anwesenheitsquote | **nur FCSG Punkte/Spiel**, knapp | +0.5 Punkte/Spiel ≈ **+3 Pp.** Anwesenheit (KI +0.2 bis +5.3 Pp., p = 0.035); erklärte Streuung +2.2 Pp., LOSO +2.7 Pp. FCSG-Rang (p = 0.08) und Form (p = 0.30) nicht belastbar. |
| Kundenfranken | nein | Kein Merkmal belastbar; Vorhersage an ausgelassenen Saisons wird mit FCSG-Werten schlechter (−2 bis −3 Pp.). |
| Bons je Anwesendem, Ø Bon | nein | Kein Merkmal belastbar. |
| Gegner (Punkte/Spiel, Rang, Form) | nein | Bei keiner Zielgrösse belastbar; «Top-Gegner» deckt den Gegnereffekt ab. |

**Lesart:** Ein gut platzierter FCSG lässt etwas mehr Ticketinhaber tatsächlich kommen; auf den Konsum pro Kopf wirkt der Tabellenstand nicht. Vorbehalt: 24 Tests, zufällig wären rund 1 «Treffer» mit p < 0.05 zu erwarten. Der eine Effekt ist plausibel, aber schwach belegt.

**Folge (Vorschlag, D-051):** Hauptmodell unverändert. Im Spielrechner Tabellenrang, Punkte/Spiel und Form beider Teams als **Hinweis** zeigen (Live-Abruf), ohne Einfluss auf KF und Umsatz.

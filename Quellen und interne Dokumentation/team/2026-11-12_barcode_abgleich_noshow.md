# Barcode-Abgleich Einzeltickets × Zutritt – Nicht-Scan-Quote je Saison (D-052)

**Stand:** 12.11.2026 · **Freigabe:** Projektleitung, 12.11.2026 (Club-Bestätigung zu pseudonymen IDs weiterhin offen, D-006/D-035)
**Skript:** `Baseline Analyse Rechnungen/Rechenkern/scripts/barcode_abgleich.py` · **Spielebene:** Run 4 `mart_match.csv` (108 gespielte Herren-Pflichtspiele)
**Datenschutz:** Barcodes nur im Arbeitsspeicher, keine IDs und keine Personenfelder in Ausgaben; nur Zählungen.

## Frage
Bisher gab es Eintritt je Ticket nur aus dem ZKS-Feld der Ticket-Exporte (35 Spiele, 2021/22–2022/23). Lässt sich das über den Barcode der Scans auf spätere Saisons ausweiten?

## Vorgehen
1. Barcodes aus Scans (vier Herren-Lieferungen) und Einzeltickets (Exporte «Barcode_», CSVs «Barcode» in Hochkommas) vereinheitlicht: beide 22-stellig.
2. Pro Spieltag: Ist der Barcode eines verkauften Einzeltickets unter den erlaubten Durchgängen? Abos sind nicht enthalten.
3. Nur Spiele mit vollständigem Zutritt (eindeutige Scans ≥ 95 % IST).

## Validierung
2022/23, 17 Spiele mit ZKS-Feld und Scans, 117'206 Tickets: **Barcode-Treffer und ZKS-Eintritt stimmen bei 99.2 % der Tickets überein** (ZKS ja/kein Scan: 865; ZKS nein/Scan: 54). Die Methode ist damit tragfähig.

## Ergebnis (nur Super League, vollständig gescannte Spiele)

| Saison | Spiele | Einzeltickets | nicht gescannt | Median je Spiel |
|---|---|---|---|---|
| 2022/23 | 15 | 96'356 | **9.6 %** | 10.1 % |
| 2023/24 | 17 | 106'912 | **11.5 %** | 8.7 % |
| 2024/25 | – | – | nicht abgleichbar | – |
| 2025/26 | 18 | 110'162 | **6.9 %** | 5.8 % |
| 2026/27 (bis 12.09.) | 4 | 24'453 | **5.7 %** | 5.5 % |

Alle Wettbewerbe (inkl. Cup/UEFA): 9.4 % / 11.5 % / – / 6.9 % / 5.0 %. Einzeltickets machen rund 40 % der Scans aus (Rest: Abos, Chipkarten u.a.).

Gegenprobe: 2022/23 ≈ 9.4 % passt zur D-049d-Basis (20'345 / 215'123 = 9.5 %, 2021/22–2022/23 via ZKS).

## Nicht abgleichbar
- **2021/22 (19 Spiele):** keine Scan-Datei – dort bleibt das ZKS-Feld die Quelle.
- **2024/25 (24 Spiele):** Scans bis Dezember 2024 praktisch leer, vollständig erst ab Januar 2025; der Einzelticket-Export 2024/25 endet im Dezember 2024 → keine Überschneidung. Die Datei `Saison_2024-25_Transaktionen.csv` (geliefert 15.10.) ist inhaltlich die bekannte Lieferung (+850 Scans) und schliesst die Lücke nicht.
- Einzelne Spiele 2022/23 (3), 2023/24 (2), 2025/26 (1) mit Scans < 95 % IST.

## Lesart und Grenzen
- **«Nicht gescannt» ist eine Obergrenze für No-Show,** kein Nachweis: Neuausstellung eines Tickets (z.B. Zweitmarkt), manueller Einlass oder Leser ohne Datenexport sind möglich.
- Ab 2025/26 enthalten die Ticket-CSVs nur aktuelle Tickets (keine Stornos) – Definition leicht anders als die Exporte.
- Der Rückgang von rund 10–11 % auf rund 6–7 % ist ein **beschriebener Unterschied, keine Ursache.** Mögliche Erklärungen (Ticketart, Tarifmix, Gratis-/Promo-Anteil, Zweitmarkt) sind nicht geprüft.
- Aufschlüsselung nach Tarif/Kanal/Bestellgrösse (wie D-049d) für 2025/26 wäre technisch möglich, ist aber nicht gemacht.

## Ergänzung 13.11.2026: Public-Abo-No-Show (Näherung)

Tabellen und Methode: `Baseline Analyse Rechnungen/barcode_abgleich_2026-11-13/README.md`.

**Rechnung je Spiel** (SL, vollständig gescannte Spiele):
- **Abo-Bestand je Saison** = Median von SOLL − Einzeltickets + Zweitmarkt (Umkehrung der SOLL-Formel «Einzel + Abo − Zweitmarkt») über Spiele ohne Kapazitäts-SOLL. Gegenprobe 2026/27: rund 13'000 ≈ Abo-Snapshot 13'052.
- **Public-Bestand** = Bestand − Hospitality-Anteil 6.6 % (859 von 13'052, Snapshot 2026/27, für frühere Saisons übernommen) − je Spiel die über den Zweitmarkt weiterverkauften Plätze (deren Besucher kommen mit neuem Ticket).
- **Public-Abo-Besuche** = Scans ohne Einzelticket-Treffer, ohne Hospitality-Leser (HH).
- **Gäste:** kein Abzug nötig – Gäste kommen über Einzeltickets; gescannte Einzeltickets am B4 ≈ «IST Gäste» der Historie.

| Saison | Spiele | Public-Abo-Bestand | Abo-Besuche (Median) | **Abo-No-Show** | Spanne je Spiel |
|---|---|---|---|---|---|
| 2022/23 | 15 | ≈ 10'150 | 7'380 | **27.4 %** | 17–40 % |
| 2023/24 | 17 | ≈ 10'630 | 7'800 | **28.1 %** | 18–46 % |
| 2025/26 | 18 | ≈ 11'180 | 7'890 | **28.8 %** | 19–40 % |
| 2026/27 | 4 | ≈ 12'170 | 8'570 | **26.2 %** | 22–30 % |

Varianten: ohne Zweitmarkt-Abzug 27.4 / 28.1 / 30.8 / 29.0 %; inkl. Hospitality 22.9 / 23.7 / 25.5 / 22.9 %.

**Lesart:**
- Rund **jedes vierte Public-Abo bleibt pro Spiel ungenutzt** – etwa das Drei- bis Fünffache der Einzelticket-Quote (6–12 %).
- Eher **Untergrenze** (Rest enthält Freikarten/Mitarbeitende/Medien).
- Grösste Unsicherheit: Bestand (9–11 Spiele je Saison, Hospitality-Anteil vor 2026/27 angenommen, Zweitmarkt vor 2025/26 unbekannt).
- Beschreibung, keine Ursache.

## Offene Rückfragen an den Club (neutral)
1. Ist der technische Abgleich über pseudonyme Barcodes für die Analyse zulässig (D-006/D-035)?
2. Gibt es Scans 2024/25 für Juli–Dezember 2024 und einen Einzelticket-Export ab Januar 2025?
3. Erhält ein über den Zweitmarkt weiterverkauftes Ticket einen neuen Barcode?
4. Wie viele Saisonabos (Herren, davon Hospitality) gab es je Saison 2022/23–2025/26? Damit würde die Bestandsnäherung ersetzt.

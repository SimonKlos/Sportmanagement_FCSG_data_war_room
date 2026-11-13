# Barcode-Abgleich Einzeltickets × Zutritt – 13.11.2026 (D-052)

**Fragen:**
1. Welcher Anteil der Einzeltickets wird pro Saison nicht gescannt?
2. Wie hoch ist die No-Show der Public-Abos?

Bisher gab es Eintritt je Ticket nur für 2021/22–2022/23 aus dem ZKS-Feld.

**Methode:** Skript `Rechenkern/scripts/barcode_abgleich.py`.
- Die Barcodes der Einzeltickets werden pro Spieltag mit den Barcodes der erlaubten Drehkreuz-Durchgänge abgeglichen (alle Herren-Lieferungen).
- Die Barcodes bleiben nur im Arbeitsspeicher. Ausgegeben werden nur Zählungen je Saison.
- Berücksichtigt sind nur Spiele mit vollständigem Zutritt (eindeutige Scans ≥ 95 % IST).
- Spielebene: Run 4 `mart_match.csv`. Datenlieferung 01.10.2026, Datenstand 12.09.2026.

**Ausgeführt:** 13.11.2026.

```
python scripts/barcode_abgleich.py <Rohdaten> ../run4_komplett_2026-11-05/kern_phase1/Tabellen/mart_match.csv ../barcode_abgleich_2026-11-13
```

## Validierung

2022/23 liegen sowohl Scans als auch das ZKS-Feld vor: 17 Spiele, 117'206 Tickets. Barcode-Treffer und ZKS-Eintritt stimmen bei **99.2 %** der Tickets überein (`validierung_zks_barcode.csv`).

## Ergebnis 1: Nicht gescannte Einzeltickets (Super League)

| Saison | Spiele | Einzeltickets | nicht gescannt |
|---|---:|---:|---:|
| 2022/23 | 15 | 96'356 | 9.6 % |
| 2023/24 | 17 | 106'912 | 11.5 % |
| 2024/25 | – | – | nicht abgleichbar |
| 2025/26 | 18 | 110'162 | 6.9 % |
| 2026/27 (bis 12.09.) | 4 | 24'453 | 5.7 % |

Abgleichbar sind 59 von 108 Spielen (`abdeckung_je_saison.csv`). Nicht abgleichbar sind:
- **2021/22:** Es gibt keine Scans.
- **2024/25:** Die Scans sind erst ab Januar 2025 vollständig, der Ticket-Export endet im Dezember 2024. Die Datei `Saison_2024-25_Transaktionen.csv` ist die bekannte Lieferung plus 850 Scans.
- **6 einzelne Spiele** mit Scans unter 95 % IST.

## Ergebnis 2: Public-Abo-No-Show (Näherung, Super League)

**Bestand je Saison**
- Median von SOLL − Einzeltickets + Zweitmarkt, nur über Spiele ohne Kapazitäts-SOLL. Das ist die Umkehrung der SOLL-Formel «Einzeltickets + Abos − Zweitmarkt».
- Gegenprobe 2026/27: rund 13'000 ≈ Abo-Snapshot 13'052.
- Davon abgezogen: Hospitality-Anteil 6.6 % (859 von 13'052 im Snapshot 2026/27, für frühere Saisons übernommen).
- Pro Spiel abgezogen: die über den Zweitmarkt weiterverkauften Plätze. Deren Besucher kommen mit einem neuen Ticket.

**Besuche:** Scans ohne Einzelticket-Treffer, ohne Hospitality-Eingänge (HH). Gäste laufen über Einzeltickets. Am Gästesektor gibt es fast keine Scans ohne Einzelticket.

| Saison | Spiele | Public-Abo-Bestand | Abo-Besuche (Median) | **Abo-No-Show** | Spanne je Spiel | ohne Zweitmarkt-Abzug | inkl. Hospitality |
|---|---:|---:|---:|---:|---:|---:|---:|
| 2022/23 | 15 | ≈ 10'150 | 7'380 | **27.4 %** | 17–40 % | 27.4 % | 22.9 % |
| 2023/24 | 17 | ≈ 10'630 | 7'800 | **28.1 %** | 18–46 % | 28.1 % | 23.7 % |
| 2025/26 | 18 | ≈ 11'180 | 7'890 | **28.8 %** | 19–40 % | 30.8 % | 25.5 % |
| 2026/27 | 4 | ≈ 12'170 | 8'570 | **26.2 %** | 22–30 % | 29.0 % | 22.9 % |

Datei: `abo_noshow_naeherung_je_saison.csv`.

## Lesart und Grenzen

- **«Nicht gescannt» ist eine Obergrenze für No-Show,** kein Nachweis. Möglich sind auch neu ausgestellte Tickets (Zweitmarkt) oder manueller Einlass.
- **Die Abo-Quote ist eher eine Untergrenze.** Bei den Besuchen zählen auch Freikarten, Mitarbeitende und Medien mit.
- **Die grösste Unsicherheit liegt beim Bestand:** Er stützt sich auf 9–11 Spiele pro Saison (2026/27: 2). Der Hospitality-Anteil vor 2026/27 ist angenommen. Für 2022/23 und 2023/24 gibt es keine Zweitmarkt-Zahlen.
- **Ticket-CSVs ab 2025/26** enthalten nur aktuelle Tickets ohne Stornos. Die Definition ist deshalb leicht anders als bei den Exporten.
- **Keine Ursachen:** Unterschiede zwischen den Saisons sind nur beschrieben. Nicht nach Sektor aufgeteilt (Datenagenda).

## Offene Rückfragen an den Club

Siehe `Quellen und interne Dokumentation/team/2026-11-12_barcode_abgleich_noshow.md`. Es geht um vier Punkte:
1. Ist der Abgleich über pseudonyme IDs zulässig?
2. Gibt es Daten für die Lücke 2024/25?
3. Bekommt ein Zweitmarkt-Ticket einen neuen Barcode?
4. Wie viele Abos gab es pro Saison, davon wie viele Hospitality-Abos?

# config/reference/ – öffentliche Referenzdaten

Öffentliche Daten ohne Clubbezug, die die Pipeline als Nachschlagetabellen nutzt (versioniert).

## `school_holidays_stadt_sg.csv` – Schulferien Stadt St.Gallen

Recherchiert vom Agenten am **11.10.2026** (Entscheid D-017 b / D-021). Ersetzt in `context_match` die Spalte
`school_holiday` für alle Saisons **vor 2026/27**; ab 2026/27 gilt weiterhin der Teamwert (dient hier nur zur
Gegenprüfung). Herkunft je Spiel steht in `context_match.school_holiday_source`.

| Spalte | Bedeutung |
|---|---|
| `school_year` | Schuljahr (Aug.–Juli) |
| `holiday` | Herbst-, Weihnachts-, Winter-, Frühlings-, Sommerferien |
| `first_day`, `last_day` | erster und letzter **ferienfreier Kalendertag inklusive** (Samstag nach Schulschluss bis Sonntag vor Schulbeginn) |
| `source_id` | siehe unten |

Quellen:

| `source_id` | Quelle | Stand |
|---|---|---|
| `OD` | Open Data Stadt St.Gallen, Datensatz «Schulferien und Feiertage Stadt St.Gallen» (`daten.stadt.sg.ch`, ID `schulferien-feiertage-stadt-stgallen`, Herausgeber: Schule und Musik, Stadt St.Gallen). Felder `beginnt_am` (Samstag) und `endet_am` (erster Schultag, exklusiv) → `last_day` = `endet_am` − 1 Tag | geändert 26.09.2025, abgerufen 11.10.2026 |
| `FP25` | Ferienplan Stadt St.Gallen, frühere Fassung «SUM Ferienplan 2025_2029» (Schuljahr 2025/26). Die heute abrufbare Fassung beginnt erst mit 2026/27; die Werte 2025/26 stammen aus dem Suchindex dieser früheren Fassung. **Gegenprüfung:** Herbst-, Weihnachts-, Frühlings- und Sommerferien stimmen mit der kantonalen Regel überein (Herbst KW 40–42, Frühling KW 15–16, Sommer KW 28–32, Weihnachten 2 Wochen mit 25.12. in Woche 1; Schulbeginn 10.08.2026). Die **Winterferien 2026 (25.01.–01.02.)** sind nur über den Suchindex belegt | abgerufen 11.10.2026 |
| `FP26` | Ferienplan Stadt St.Gallen 2026/27–2029/30 (PDF «SUM Ferienplan 2025_2029», stadt.sg.ch → Schule & Bildung → Schulferien), Angabe «Sonntag bis Sonntag» → Beginn auf den Samstag davor gesetzt | abgerufen 11.10.2026 |

**Abgrenzung (Annahme, D-021):**
- Massgeblich ist die **Stadt St.Gallen**, also der Stadionstandort. Herbst-, Weihnachts-, Frühlings- und Sommerferien legt
  der Kanton einheitlich fest. Die **Winterferien bestimmt jede Gemeinde selbst** und können im Einzugsgebiet abweichen.
- Einzelne schulfreie Tage (Auffahrtsbrücke, 1. Mai nachmittags, Allerheiligen, Pfingstmontag) zählen **nicht** als
  Schulferien. Feiertage stehen in der eigenen Spalte `public_holiday`.
- Ein Spiel am Samstag zu Ferienbeginn oder am Sonntag vor Schulbeginn zählt als Ferienspiel.

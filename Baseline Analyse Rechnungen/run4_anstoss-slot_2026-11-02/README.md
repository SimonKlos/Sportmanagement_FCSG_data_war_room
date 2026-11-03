# Run 4 · 02.11.2026 – Anstoss-Slot im Kontextmodell, Sensitivitäten 2021/22 und ohne 2023/24

> **Vertraulich – echte FCSG-Daten, aggregiert (keine Personendaten).** Intern, privates Repo (D-024).
> Run 4 **ergänzt** Run 3, ersetzt ihn nicht: Bericht, Excel und Deliverables beruhen weiter auf Run 3, bis das Team die
> Übernahme entscheidet (D-046).

## Was wurde gerechnet

| Teil | Befehl | Stand |
|---|---|---|
| Kontextmodelle mit Anstoss-Slot + Sensitivitäten | `cd "Baseline Analyse Rechnungen/Rechenkern"; python run4.py --daten <Lieferung> --kontext Spielkontext_Tabelle_FCSG_5.xlsx --ausgabe <dieser Ordner>` | 02.11.2026 21:01, Python 3.13.5, Pakete wie Run 3 (pandas 3.0.6, statsmodels 0.15.0); Laufprotokoll.json |

- **Neu im Code:** `fcsg/analysis/anstoss_slot.py`, `run4.py`, `tests/test_anstoss_slot.py`. `models.py` und `run_all.py` unverändert.
- **Tests:** alle 52 Tests bestanden (inkl. Integrationstests auf den echten Daten); `run_all.py` auf derselben Lieferung: Importtests 19/19, Ideen-QA 18/18.
- **Datenlieferung:** lokale Fassung «fcstgallen1879_data_2026-10-01_1149». Sie ist **nicht bytegleich** mit der Lieferung von Run 3
  (15 Dateien mit anderer Prüfsumme). Kontrolle: `run_all.py` auf dieser Lieferung ergibt **identische** Kontext-Effekt-Matrix,
  Modellgüte, Saison-KPI und Phase-2-Kandidaten wie Run 3; Abweichungen nur bei 1 Spiel 2025/26 (Einzelticket-/Ausverkauft-Angabe),
  ZKS-Gültigkeitsflags und Bemerkungstexten. Die Vergleichsvariante «Run 3» in Run 4 reproduziert die Run-3-Modellgüte exakt.

## Anstoss-Slot (Spielplan, für den Club extern – D-045)

Statt «Werktag» + «Abendspiel ab 20 Uhr» vier Slots aus Wochentag und Anpfiff; Referenz = **Samstag 17–19.59 Uhr**.

| Slot | Spiele SL 22/23–26/27 | KF exkl. MwSt (Summe/Summe, unbereinigt) | Anwesenheitsquote (unbereinigt) |
|---|---:|---:|---:|
| Samstag 17–19.59 Uhr | 21 | 15.21 | 82.6 % |
| Samstag ab 20 Uhr | 13 | 14.39 | 81.3 % |
| Nachmittag vor 17 Uhr (Sonntag/Feiertag) | 34 | 12.89 | 85.1 % |
| Werktagabend ab 17 Uhr | 10 | 13.39 | 73.0 % |

**Bereinigte Effekte gegenüber Samstag 17–19.59 Uhr** (Saison, Top-Gegner, Temperatur, Regen, Ferien konstant; 95 %-KI):

| Zielgrösse | Samstag ab 20 Uhr | Nachmittag (So/Feiertag) | Werktagabend |
|---|---|---|---|
| Kundenfranken | −3.6 % (−6.0 bis −1.1) | **−15.7 %** (−17.9 bis −13.3) | **−9.4 %** (−13.1 bis −5.6) |
| Bons je Anwesendem | −1.8 % (n.s.) | −8.2 % (−10.9 bis −5.5) | −1.3 % (n.s.) |
| Ø Bon | −2.1 % (n.s.) | −8.3 % (−10.6 bis −5.9) | −9.5 % (−12.6 bis −6.3) |
| Anwesenheitsquote | −0.4 Pp. (n.s.) | **+3.7 Pp.** (+1.2 bis +6.3) | **−7.4 Pp.** (−10.4 bis −4.4) |

**Modellgüte** (Anteil der saisonbereinigten Streuung, den der Kontext erklärt; Leave-one-season-out gegenüber Saisonmittel):

| Zielgrösse | Run 3 (Werktag + Abend) | Run 4 (Anstoss-Slot) |
|---|---|---|
| Kundenfranken | 33 % · +7 % | **82 % · +53 %** |
| Anwesenheitsquote | 42 % · +16 % | 62 % · +29 % |
| Bons je Anwesendem | 19 % · +2 % | 50 % · +18 % |
| Ø Bon | 35 % · +5 % | 71 % · +39 % |

**Lesart:** Der Anstoss-Slot ist der stärkste bisher gefundene Kontextfaktor für den Konsum. Run 3 hatte Samstag 18 Uhr
und Sonntagnachmittag in derselben Gruppe «kein Abendspiel» – vermutlich erschien «Abendspiel» dort deshalb positiv für den
KF (+6.8 %): Die Abendspiele lagen über dem Mittel aus starkem Samstag 18 Uhr und schwachem Sonntagnachmittag.
Sonntagnachmittag: mehr Anwesende, aber deutlich tieferer Konsum je Person (sowohl seltener als auch kleinere Bons).

**CHF-Baustein (isoliert, nicht addieren):** KF-Effekt × Ø KF 14.51 × Ø 13'785 Public-Anwesende (Meisterschaft 2025/26):
Sonntagnachmittag ≈ **−31'000 CHF Catering-Umsatz je Spiel** (KI −36'000 bis −27'000) gegenüber Samstag 18 Uhr bei gleicher
Besucherzahl; Werktagabend ≈ −19'000; Samstag ab 20 Uhr ≈ −7'000. Der Anwesenheitseffekt kommt separat dazu bzw. wirkt
gegenläufig (Sonntag +3.7 Pp.) und wird nicht addiert.

## Sensitivitäten

- **Inkl. 2021/22 mit Covid-Variable** (94 statt 76 Spiele für Anwesenheit/KF): Slot-Effekte praktisch gleich (KF Sonntag −15.1 %,
  Werktag −8.7 %). Covid-Massnahmen (11 Spiele): Anwesenheitsquote −6.6 Pp. (−11.4 bis −1.7), KF n.s. Für Bons/Ø Bon nicht schätzbar
  (Bons erst ab 2023/24).
- **Ohne 2023/24** (Kassensystemwechsel, D-041): Slot-Effekte stabil (KF Sonntag −14.6 %, Bons −7.0 %, Ø Bon −8.5 %). Der
  Erfassungsbruch 2023/24 verändert die Slot-Aussagen nicht. Bons-Modell schwächer (LOSO +4 % statt +18 %), weil nur 41 Spiele.

## Grenzen

- Zusammenhänge, keine Kausalnachweise: Die Liga verteilt Slots nicht zufällig (TV, Topspiele). Gegner, Saison und Wetter sind
  kontrolliert, anderes nicht.
- Werktagabend nur 10 Spiele, Samstag ab 20 Uhr 13 Spiele – breite Intervalle.
- Der Slot ist für den Club extern; der Nutzen liegt in Planung (Personal/Ware je Slot), Erwartungswerten je Spiel und als
  Argument gegenüber Liga/TV – nicht als eigene Massnahme.

## Dateien

| Datei | Inhalt |
|---|---|
| `FCSG_Run4_Anstoss_Slot.xlsx` | Alle Tabellen mit Inhaltsverzeichnis |
| `Tabellen/modellguete.csv` | Modellgüte je Variante und Zielgrösse |
| `Tabellen/effekte.csv` | Effekte aller Variablen je Variante (95 %-KI) |
| `Tabellen/deskriptiv.csv` | Spiele, KF, Anwesenheitsquote je Slot (unbereinigt) |
| `Tabellen/chf_baustein.csv` | Isolierter Konsum-Baustein je Slot |
| `Tabellen/erwartung_je_spiel.csv` | Beobachtung vs. Erwartung je Spiel (Leave-one-match-out) – Grundlage Spielrechner |
| `Tabellen/koeffizienten.csv` | Koeffizienten des Slot-Modells – Grundlage Spielrechner |
| `Laufprotokoll.json` | Zeitpunkt, Versionen, Eingabedateien mit Prüfsumme |

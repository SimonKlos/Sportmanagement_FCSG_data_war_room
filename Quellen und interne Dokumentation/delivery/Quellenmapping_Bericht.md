# Technische Quellenzuordnung – vertraulich

Bericht: `FCSG_Baseline_und_Chancenfelder.html`. Nur bestehende Aggregate, keine Neuschätzung. Quellpfade sind unveränderte technische Identifikatoren, keine redaktionellen Vergleiche. JSON enthält Originalwerte und SHA-256 der Quellen.

## G01 · Kundenfranken je Saison

- Quelle: `Baseline Analyse Rechnungen/run4_komplett_2026-11-05/kern_phase1/Tabellen/saison_kpi.csv`
- Auswahl: wettbewerbe=SL; saison,spiele,kf_inkl
- Leseregel: Summe/Summe; inkl. MwSt.; letzte Saison nur vier Spiele
- SHA-256: `1edf9f1297d75a8ce1837478bb5c4172acffc0ede029733e075b04d1474fdafa`

## G02 · No-Show je Saison

- Quelle: `Baseline Analyse Rechnungen/run4_komplett_2026-11-05/kern_phase1/Tabellen/saison_kpi.csv`
- Auswahl: wettbewerbe=SL; saison,spiele,noshow_quote
- Leseregel: 1 − ΣIST/ΣSOLL; teils kapazitätsbasiertes SOLL; keine reine Abo-Quote
- SHA-256: `1edf9f1297d75a8ce1837478bb5c4172acffc0ede029733e075b04d1474fdafa`

## G03 · Vor-Anpfiff-Zeit nach physischem Eingang

- Quelle: `Baseline Analyse Rechnungen/run4_komplett_2026-11-05/ideen_grundlage/Ideen_Grundlage_FCSG.xlsx`
- Auswahl: Z1_Verweilzeit_Eingang!A1:K6
- Leseregel: verweil_mittel = Median der spielweisen mittleren Verweilminuten; nach Anpfiff auf 0 gesetzt; B4 n=64, übrige n=71
- SHA-256: `6a986e9c685e775a4ee7c302abd47eeaeff6edcaa072c91575f431c8f2db8a37`

## G04 · Historische Modellvalidierung

- Quelle: `Baseline Analyse Rechnungen/run4_komplett_2026-11-05/kern_phase1/Tabellen/modellguete.csv`
- Auswahl: alle fünf Zielgrössen; spiele,verbesserung_loso_pct
- Leseregel: RMSE-Verbesserung relativ zum Saisonmittel auf transformierten saisonbereinigten Werten; keine operative Zukunftsprognose
- SHA-256: `3032658633d7fb97b8c49382febf16e0a13d5e6e5ca907fe64f9c9aee48c1fcb`

## G05 · T-7 Prognosevergleich

- Quelle: `Baseline Analyse Rechnungen/run4_komplett_2026-11-05/ideen_grundlage/Ideen_Grundlage_FCSG.xlsx`
- Auswahl: A6_Fruehindikator!A1:L2
- Leseregel: 54 retrospektive Vorhersagen; Bandabdeckung nur 44 Spiele mit Band, nicht 54
- SHA-256: `6a986e9c685e775a4ee7c302abd47eeaeff6edcaa072c91575f431c8f2db8a37`

## G06 · Treiberlogik

- Quelle: `Baseline Analyse Rechnungen/run4_komplett_2026-11-05/kern_phase1/Methodennotiz_Phase1.md`
- Auswahl: §4 KPI-Definitionen, Zeilen 102–114
- Leseregel: Schematische Darstellung, keine Schätzung
- SHA-256: `42655cf0ad33fffa06b6b3c130e19f7449660d8be49b4985afffa1f2b34db289`

## G07 · Drei Themen

- Quelle: `Baseline Analyse Rechnungen/run4_komplett_2026-11-05/ideen_grundlage/Ideen_Grundlage_FCSG.xlsx`
- Auswahl: 02_Chancenfelder!A2:B10
- Leseregel: Gruppierung redaktionell; keine neue Modellierung
- SHA-256: `6a986e9c685e775a4ee7c302abd47eeaeff6edcaa072c91575f431c8f2db8a37`

## T01 · Saison-Baseline

- Quelle: `Baseline Analyse Rechnungen/run4_komplett_2026-11-05/kern_phase1/Tabellen/saison_kpi.csv`
- Auswahl: wettbewerbe=SL
- Leseregel: Alle Tabellenwerte direkt gerundet; keine Mittelwerte über Saisons
- SHA-256: `1edf9f1297d75a8ce1837478bb5c4172acffc0ede029733e075b04d1474fdafa`

## T02 · Modulabdeckung

- Quelle: `Baseline Analyse Rechnungen/run4_komplett_2026-11-05/kern_phase1/Tabellen/abdeckung.csv`
- Auswahl: Total/alle
- Leseregel: 108 gespielte Pflichtspiele; unterschiedliche Modulstichproben
- SHA-256: `b7c4af1e851c8e1e07e5b2bc496c8894dc3ab3511fe714fa88893f026e81f6c2`

## N01 · Definitionen, Ankunft und Grenzen

- Quelle: `Baseline Analyse Rechnungen/run4_komplett_2026-11-05/kern_phase1/Methodennotiz_Phase1.md`
- Auswahl: §§1–4, 6–10, 13; insbesondere 146–174, 185–208, 254
- Leseregel: Werte aus historischer Methodennotiz; keine Rohdaten-Revalidierung
- SHA-256: `42655cf0ad33fffa06b6b3c130e19f7449660d8be49b4985afffa1f2b34db289`

## N02 · Chancenfelder und Belege

- Quelle: `Baseline Analyse Rechnungen/run4_komplett_2026-11-05/ideen_grundlage/Ideen_Grundlage_FCSG.xlsx`
- Auswahl: 02_Chancenfelder!A1:W10; K14_Kiesplatz_Wetter!A1:J10; K13_Zahlungswege_Ideen!A1:H19
- Leseregel: Kausale Kurzformulierungen aus Quelle redaktionell als Assoziationen begrenzt; Bons-Trend vorläufig
- SHA-256: `6a986e9c685e775a4ee7c302abd47eeaeff6edcaa072c91575f431c8f2db8a37`

## N03 · Leere Plätze und Zweitmarkt

- Quelle: `Baseline Analyse Rechnungen/run4_komplett_2026-11-05/ideen_grundlage/Ideen_Grundlage_FCSG.xlsx`
- Auswahl: N1_Leere_Plaetze_Saison!A6:I6; N3_Zweitmarkt_Saison!A2:N2
- Leseregel: 60’942 = SOLL−IST, nicht vollständig nachgewiesen bezahlte Plätze; 41’442 in 11 Spielen mit ticketbasiertem SOLL. Historischer Wiederbesetzungsindikator 8,6 % nutzt 5’716/(60’942+5’716), nicht 5’716/60’942.
- SHA-256: `6a986e9c685e775a4ee7c302abd47eeaeff6edcaa072c91575f431c8f2db8a37`

## N04 · Kundenfranken-Entwicklung

- Quelle: `Baseline Analyse Rechnungen/run4_komplett_2026-11-05/ideen_grundlage/Ideen_Grundlage_FCSG.xlsx`
- Auswahl: K1_KF_Entwicklung!A1:I6
- Leseregel: Bonsrate/Bon über 23/24 vorläufig, Sensitivität ohne Übergangssaison fehlt
- SHA-256: `6a986e9c685e775a4ee7c302abd47eeaeff6edcaa072c91575f431c8f2db8a37`

## N05 · Aktuelle methodische Einschränkungen

- Quelle: `Quellen und interne Dokumentation/team/2026-11-01_catering_klaerung_und_baseline_folgen.md`
- Auswahl: §§1–4, entsprechend D-038 bis D-041
- Leseregel: Dokumentationsstand 01.11.2026; keine Ergebnisänderung, keine Modellfreigabe
- SHA-256: `b53f0f1f46e1b7612c234e641281120cfd728ba0d045f57a4834ece3bba599c8`

## N06 · Einzelticket-Vorlauf

- Quelle: `Baseline Analyse Rechnungen/run4_komplett_2026-11-05/kern_phase1/FCSG_Phase1_Ergebnisse.xlsx`
- Auswahl: B8_Absatz_Ausverkauft!A1:F3
- Leseregel: Vorlauf: 34 ausverkaufte und 53 nicht ausverkaufte Meisterschaftsspiele; kein Ausverkaufszeitpunkt
- SHA-256: `a87fd32140aa85687edbf90809a1411428b1fecd4002cd866fc2e169d242c75a`

## T03 · Ausgewählte Kontexteffekte

- Quelle: `Baseline Analyse Rechnungen/run4_komplett_2026-11-05/kern_phase1/Tabellen/kontext_effekt_matrix.csv`
- Auswahl: Ziel Anwesenheit/KF/Ø Bon, Variablen Top-Gegner/Anstoss-Slot/Temperatur; Auswahl wie HTML (T03_ZEILEN)
- Leseregel: Effekte gerundet; vollständige Tabelle ist kanonische Quelle
- SHA-256: `8cbd921fec78c91ff164d86fd7adababd2dd4929de1506b888a94fd84a2544bf`

## Redaktionelle Herkunft

Die Erklärung der Spielebene, der getrennten Module und der Hypothesenlogik nutzt zusätzlich den bestehenden Baseline-Erklärtext. Dessen abweichende Ergebniszahlen, Prüfzählungen und Grafiken wurden nicht übernommen. Massgeblich sind die oben zugeordneten kanonischen Aggregate.

## Offene Prüfungen

Rohdaten fehlen. Keine neue Verprobung von Eingaben, Bons-Sensitivität oder Modellfreigabe. D-038 bis D-041 dokumentieren den aktuellen Einordnungsstand. Keine automatische Baseline-Freigabe durch diesen Bericht.

# Technische Quellenzuordnung – vertraulich

Bericht: `FCSG_Baseline_und_Chancenfelder.html`. Nur bestehende Aggregate, keine Neuschätzung. Quellpfade sind unveränderte technische Identifikatoren, keine redaktionellen Vergleiche. JSON enthält Originalwerte und SHA-256 der Quellen.

## G01 · Kundenfranken je Saison

- Quelle: `/data/cache/scratch/fcsg-review/Baseline Analyse Rechnungen/run3_kontext-v5_2026-10-14/ralf_kern_phase1/Tabellen/saison_kpi.csv`
- Auswahl: wettbewerbe=SL; saison,spiele,kf_inkl
- Leseregel: Summe/Summe; inkl. MwSt.; letzte Saison nur vier Spiele
- SHA-256: `1edf9f1297d75a8ce1837478bb5c4172acffc0ede029733e075b04d1474fdafa`

## G02 · No-Show je Saison

- Quelle: `/data/cache/scratch/fcsg-review/Baseline Analyse Rechnungen/run3_kontext-v5_2026-10-14/ralf_kern_phase1/Tabellen/saison_kpi.csv`
- Auswahl: wettbewerbe=SL; saison,spiele,noshow_quote
- Leseregel: 1 − ΣIST/ΣSOLL; teils kapazitätsbasiertes SOLL; keine reine Abo-Quote
- SHA-256: `1edf9f1297d75a8ce1837478bb5c4172acffc0ede029733e075b04d1474fdafa`

## G03 · Vor-Anpfiff-Zeit nach physischem Eingang

- Quelle: `/data/cache/scratch/fcsg-review/Baseline Analyse Rechnungen/run3_kontext-v5_2026-10-14/ralf_ideen_grundlage/Ideen_Grundlage_FCSG.xlsx`
- Auswahl: Z1_Verweilzeit_Eingang!A1:K6
- Leseregel: verweil_mittel = Median der spielweisen mittleren Verweilminuten; nach Anpfiff auf 0 gesetzt; B4 n=64, übrige n=71
- SHA-256: `67f1c5e19462f4b42b73d727b83f88d65d84415ad37b3412451e23b65cd55bc4`

## G04 · Historische Modellvalidierung

- Quelle: `/data/cache/scratch/fcsg-review/Baseline Analyse Rechnungen/run3_kontext-v5_2026-10-14/ralf_kern_phase1/Tabellen/modellguete.csv`
- Auswahl: alle fünf Zielgrössen; spiele,verbesserung_loso_pct
- Leseregel: RMSE-Verbesserung relativ zum Saisonmittel auf transformierten saisonbereinigten Werten; keine operative Zukunftsprognose
- SHA-256: `bf92775002ce4dfb0a96271f953b3470879d9be7da6337f7cacbdf72446b8c0a`

## G05 · T-7 Prognosevergleich

- Quelle: `/data/cache/scratch/fcsg-review/Baseline Analyse Rechnungen/run3_kontext-v5_2026-10-14/ralf_ideen_grundlage/Ideen_Grundlage_FCSG.xlsx`
- Auswahl: A6_Fruehindikator!A1:L2
- Leseregel: 54 retrospektive Vorhersagen; Bandabdeckung nur 44 Spiele mit Band, nicht 54
- SHA-256: `67f1c5e19462f4b42b73d727b83f88d65d84415ad37b3412451e23b65cd55bc4`

## G06 · Treiberlogik

- Quelle: `/data/cache/scratch/fcsg-review/Baseline Analyse Rechnungen/run3_kontext-v5_2026-10-14/ralf_kern_phase1/Methodennotiz_Phase1.md`
- Auswahl: §4 KPI-Definitionen, Zeilen 102–114
- Leseregel: Schematische Darstellung, keine Schätzung
- SHA-256: `362938e533c4160524d29eb8aec9e866ea51c5064d246ff0b4978055271585f5`

## G07 · Drei Themen

- Quelle: `/data/cache/scratch/fcsg-review/Baseline Analyse Rechnungen/run3_kontext-v5_2026-10-14/ralf_ideen_grundlage/Ideen_Grundlage_FCSG.xlsx`
- Auswahl: 02_Chancenfelder!A2:B10
- Leseregel: Gruppierung redaktionell; keine neue Modellierung
- SHA-256: `67f1c5e19462f4b42b73d727b83f88d65d84415ad37b3412451e23b65cd55bc4`

## T01 · Saison-Baseline

- Quelle: `/data/cache/scratch/fcsg-review/Baseline Analyse Rechnungen/run3_kontext-v5_2026-10-14/ralf_kern_phase1/Tabellen/saison_kpi.csv`
- Auswahl: wettbewerbe=SL
- Leseregel: Alle Tabellenwerte direkt gerundet; keine Mittelwerte über Saisons
- SHA-256: `1edf9f1297d75a8ce1837478bb5c4172acffc0ede029733e075b04d1474fdafa`

## T02 · Modulabdeckung

- Quelle: `/data/cache/scratch/fcsg-review/Baseline Analyse Rechnungen/run3_kontext-v5_2026-10-14/ralf_kern_phase1/Tabellen/abdeckung.csv`
- Auswahl: Total/alle
- Leseregel: 108 gespielte Pflichtspiele; unterschiedliche Modulstichproben
- SHA-256: `169efca86b056a5fe999df47d1ef3d62501ba51e5c28ef66c44b8a8c1b5eb1b0`

## N01 · Definitionen, Ankunft und Grenzen

- Quelle: `/data/cache/scratch/fcsg-review/Baseline Analyse Rechnungen/run3_kontext-v5_2026-10-14/ralf_kern_phase1/Methodennotiz_Phase1.md`
- Auswahl: §§1–4, 6–10, 13; insbesondere 146–174, 185–208, 254
- Leseregel: Werte aus historischer Methodennotiz; keine Rohdaten-Revalidierung
- SHA-256: `362938e533c4160524d29eb8aec9e866ea51c5064d246ff0b4978055271585f5`

## N02 · Chancenfelder und Belege

- Quelle: `/data/cache/scratch/fcsg-review/Baseline Analyse Rechnungen/run3_kontext-v5_2026-10-14/ralf_ideen_grundlage/Ideen_Grundlage_FCSG.xlsx`
- Auswahl: 02_Chancenfelder!A1:W10; K14_Kiesplatz_Wetter!A1:J10; K13_Zahlungswege_Ideen!A1:H19
- Leseregel: Kausale Kurzformulierungen aus Quelle redaktionell als Assoziationen begrenzt; Bons-Trend vorläufig
- SHA-256: `67f1c5e19462f4b42b73d727b83f88d65d84415ad37b3412451e23b65cd55bc4`

## N03 · Leere Plätze und Zweitmarkt

- Quelle: `/data/cache/scratch/fcsg-review/Baseline Analyse Rechnungen/run3_kontext-v5_2026-10-14/ralf_ideen_grundlage/Ideen_Grundlage_FCSG.xlsx`
- Auswahl: N1_Leere_Plaetze_Saison!A6:I6; N3_Zweitmarkt_Saison!A2:N2
- Leseregel: 60’942 = SOLL−IST, nicht vollständig nachgewiesen bezahlte Plätze; 41’442 in 11 Spielen mit ticketbasiertem SOLL. Historischer Wiederbesetzungsindikator 8,6 % nutzt 5’716/(60’942+5’716), nicht 5’716/60’942.
- SHA-256: `67f1c5e19462f4b42b73d727b83f88d65d84415ad37b3412451e23b65cd55bc4`

## N04 · Kundenfranken-Entwicklung

- Quelle: `/data/cache/scratch/fcsg-review/Baseline Analyse Rechnungen/run3_kontext-v5_2026-10-14/ralf_ideen_grundlage/Ideen_Grundlage_FCSG.xlsx`
- Auswahl: K1_KF_Entwicklung!A1:I6
- Leseregel: Bonsrate/Bon über 23/24 vorläufig, Sensitivität ohne Übergangssaison fehlt
- SHA-256: `67f1c5e19462f4b42b73d727b83f88d65d84415ad37b3412451e23b65cd55bc4`

## N05 · Aktuelle methodische Einschränkungen

- Quelle: `/data/cache/scratch/fcsg-review/Quellen und interne Dokumentation/team/2026-11-01_catering_klaerung_und_baseline_folgen.md`
- Auswahl: §§1–4, entsprechend D-038 bis D-041
- Leseregel: Dokumentationsstand 01.11.2026; keine Ergebnisänderung, keine Modellfreigabe
- SHA-256: `b82e066f86bc82c0df0c07684f941d56b4177d1f153f7f9babbe1ff3959698e3`

## N06 · Einzelticket-Vorlauf

- Quelle: `/data/cache/scratch/fcsg-review/Baseline Analyse Rechnungen/run3_kontext-v5_2026-10-14/ralf_kern_phase1/FCSG_Phase1_Ergebnisse.xlsx`
- Auswahl: B8_Absatz_Ausverkauft!A1:F3
- Leseregel: Vorlauf: 34 ausverkaufte und 53 nicht ausverkaufte Meisterschaftsspiele; kein Ausverkaufszeitpunkt
- SHA-256: `b4eadb584674d1128ce3fdbe11273f66b78e9a186c5a18c3416485d126852c0d`

## T03 · Ausgewählte Kontexteffekte

- Quelle: `/data/cache/scratch/fcsg-review/Baseline Analyse Rechnungen/run3_kontext-v5_2026-10-14/ralf_kern_phase1/Tabellen/kontext_effekt_matrix.csv`
- Auswahl: Ziel Anwesenheit/KF, Variablen Top-Gegner/Abend/Temperatur; Auswahl wie HTML
- Leseregel: Effekte gerundet; vollständige Tabelle ist kanonische Quelle
- SHA-256: `b68f3d968cec535df2774ffae3052c834cd0d4d71756bc0def5ce550a317e71e`

## Redaktionelle Herkunft

Die Erklärung der Spielebene, der getrennten Module und der Hypothesenlogik nutzt zusätzlich den bestehenden Baseline-Erklärtext. Dessen abweichende Ergebniszahlen, Prüfzählungen und Grafiken wurden nicht übernommen. Massgeblich sind die oben zugeordneten kanonischen Aggregate.

## Offene Prüfungen

Rohdaten fehlen. Keine neue Verprobung von Eingaben, Bons-Sensitivität oder Modellfreigabe. D-038 bis D-041 dokumentieren den aktuellen Einordnungsstand. Keine automatische Baseline-Freigabe durch diesen Bericht.

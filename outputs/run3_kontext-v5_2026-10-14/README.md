# Run 3 · 14.10.2026 – Neuberechnung mit Spielkontext-Tabelle Version 5

> **Vertraulich – echte FCSG-Daten, aggregiert (keine Personendaten).** Intern, privates Repo (D-024).
> **Zahlenbasis des Projekts ist `ralf_kern_phase1/`** (D-028). `simon_baseline/` dient nur als Gegenrechnung.

## Was wurde gerechnet

| Teil | Befehl | Lauf-ID / Stand | Prüfstatus |
|---|---|---|---|
| `ralf_kern_phase1/` + `ralf_ideen_grundlage/` | `cd ralf; run_all.py --daten <Lieferung> --kontext Spielkontext_Tabelle_FCSG_5.xlsx --ausgabe …/ralf_kern_phase1 --ideen-ausgabe …/ralf_ideen_grundlage` | 14.10.2026 21:50, Code v1.1.0 + Anpassungen Kontext v5 (D-034) und ohne Frauen/Länderspiele (D-036) | Importtests 19/19; 6 Datumskorrekturen angewendet (D-030); 35 Befunde (7 hoch = Korrekturen + Kiesplatz-Doppelzählungshinweis) |
| `simon_baseline/` | `fcsg.cli prepare-data` + `fcsg.cli analyze` | bereinigt `20261014T215420_clean_0cf1` (ohne Frauen und Länderspiele), Analyse `20261014T215526_baseline_24bd` | Analyse 16 OK / 1 WARN (Q01 Catering 23/24), Readback bestanden |
| `abgleich_simon_ralf/` | `python -m fcsg.abgleich …` | – | siehe unten |

- **Rohdaten:** Lieferung «20261003_Input Sandro» (unverändert; Prüfsummen in `ralf_kern_phase1/Laufprotokoll.json` und `simon_baseline/bereinigung/manifest.json`).
- **Spielkontext:** `Spielkontext_Tabelle_FCSG_5.xlsx` (SHA-256 `a04128384abca267`, D-034): 114 Heimspiele 21/22–26/27, 108 gespielt.
- **Ideen-Grundlage** neu gerechnet (`ralf_ideen_grundlage/`, QA 18/18): **ohne Frauen und Länderspiele** (D-016/D-036); Chancenfeld 9 heisst jetzt «Das Stadion an weiteren Anlässen» (Testspiele, U21, Events). Kein PDF (kein Chrome/Edge auf dem Rechner) – `Ideen_Grundlage_FCSG.html` im Browser öffnen und bei Bedarf als PDF drucken. Phase 1 durch den erneuten Lauf unverändert (alle Tabellen identisch, nur Zeitstempel).

## Ergebnis 1: Version 5 bestätigt Run 2 (Ralf, Version 3)

Zellweiser Vergleich der Tabellen von Run 2 und Run 3 (Ralfs Kern):
- **Unverändert:** Saison-KPI, Modellgüte aller 5 Kontextmodelle (R², LOSO-Verbesserung), alle Effekte und
  Konfidenzintervalle der Kontext-Effekt-Matrix, Phase-2-Kandidaten, Klärungsfragen.
- **Nur Lücken gefüllt:** Schulferien (10 Spiele 21/22) und Free-TV (21/22 + 6 Spiele 25/26) jetzt aus der
  Teamtabelle statt leer; 24 Spiele neu «in der Kontexttabelle».
- **Eine Kleinigkeit:** Vorzeichenstabilität über die Sensitivitäten für «Ø Bon × Abendspiel» 0.50 → 0.67, weil die
  Sensitivität «Temperatur aus Kontexttabelle» jetzt die Anstossstunde statt des Tagesmittels nutzt.

Der Grund: Ralfs Modelle nutzen für Wetter und Tabellenstand bereits dieselben öffentlichen Quellen (MeteoSchweiz,
football-data.co.uk) und hatten die 6 fehlenden Spiele schon ergänzt; die Modellstichprobe beginnt 22/23.

## Ergebnis 2: Beide Pipelines liefern dieselben Kernzahlen

`abgleich_simon_ralf/abgleich_zusammenfassung.csv` (je Spiel: `abgleich_je_spiel.csv`):

| Kennzahl | gleich | Bemerkung |
|---|---|---|
| SOLL, IST | 108 / 108 | identisch |
| IST VIP | 44 (64 beide leer) | identisch |
| Public Netto, Umsatz inkl./exkl., KF | 105 / 105 | identisch; 4 Zeilen nur bei Ralf: 23.07.2022 und 24.09.2024 (Datumskorrekturen D-030), **27.09.2023** (Zeile, die Simons Einleser mangels lesbarem Datum übersprungen hat – genau die CHF 207'730 Differenz zum Tab «Entwicklung», WARN Q01 ist damit ein Parserfehler bei Simon, keine Datenlücke), 14.03.2026 (abgesagtes Spiel, bei Ralf mit dem Catering-Umsatz der Quelle als «abgesagt» geführt, bei Simon ausgeschlossen) |
| Transaktionen | 68 / 68 | identisch |
| Scans | 88 / 88 (±0.5 %) | identisch |
| Anteil Ankunft ≥ 45 Min. | 6 gleich, 65 abweichend | Definition: Simon rundet Scans auf die Minute (+1.2 Pp. systematisch), Ralf sekundengenau; 1 Ausreisser (17.05.2026, −44 Pp.) = falsche Anstosszeit in der Historie, nur bei Ralf korrigiert (D-030) |
| Eintrittsquote Einzeltickets | 37 / 37 | identisch; Ralf wertet zusätzlich 23/24–24/25 aus (Simon nur Saisons mit ≥ 80 % befülltem Eintrittsfeld) |

## Ergebnis 3: Inhaltliche Kernaussagen (Ralfs Kontext-Effekt-Matrix, «belastbar»)

Saison-Effekte im Modell, 76 Spiele 22/23–26/27 (Bons/Ø Bon: 60 Spiele ab 23/24). Zusammenhänge, keine Ursachen.

| Zielgrösse | Belastbarer Kontext-Zusammenhang |
|---|---|
| Anwesenheitsquote | Top-Gegner +3.5 Pp.; Abendspiel ab 20 Uhr −4.1 Pp.; je +5 °C +1.4 Pp. |
| KF exkl. MwSt | Abendspiel +6.8 %; je +5 °C +3.6 % |
| Bons je Anwesendem | Abendspiel +4.6 % |
| Ø Bon exkl. MwSt | Werktag −4.0 %; je +5 °C +2.3 % |
| Ankunft ≥ 45 Min. | Top-Gegner +3.3 Pp.; Abendspiel +4.1 Pp. |

Simons explorative K1 (106 Spiele) zeigt dieselben Richtungen (Anstosszeit ↔ KF ρ = +0.57, Temperatur ↔ KF ρ = +0.33,
UEFA ↔ Anwesenheit ρ = +0.37).

## Tests

- Ralfs Suite mit echten Daten und Version 5: **50 von 50 bestanden** (inkl. 25 Integrationstests: Retos Kernzahlen, Validierungen, Datenschutz/keine ID-Spalten, 2 neue Tests für das Einlesen von Version 5).
- Simons Suite (künstliche Daten): siehe Changelog 0.5.0.

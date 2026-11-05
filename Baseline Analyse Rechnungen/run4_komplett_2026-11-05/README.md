# Run 4 (komplett) · 05.11.2026 – Ganzer Rechenkern mit Anstoss-Slot

> **Vertraulich – echte FCSG-Daten, aggregiert (keine Personendaten).** Intern, privates Repo (D-024).
> **Zahlenbasis des Projekts ab 05.11.2026** (D-048). Löst Run 3 als Referenz ab. Run 3 bleibt als Archiv unverändert.

## Was wurde gerechnet

| Teil | Befehl | Stand | Prüfstatus |
|---|---|---|---|
| `kern_phase1/` + `ideen_grundlage/` | `cd "Baseline Analyse Rechnungen/Rechenkern"; python run_all.py --daten <Lieferung> --kontext Spielkontext_Tabelle_FCSG_5.xlsx --ausgabe …/kern_phase1 --ideen-ausgabe …/ideen_grundlage` | 05.11.2026 17:59, Code v1.1.0 + D-048, Python 3.13.5, Pakete wie Run 3 (pandas 3.0.6, numpy 2.5.3, statsmodels 0.15.0); Prüfsummen aller 62 Eingabedateien in `kern_phase1/Laufprotokoll.json` | Importtests 19/19; Ideen-QA 18/18; 34 Befunde (7 hoch, wie Run 3: Korrekturen + Kiesplatz-Hinweis); Testsuite 52/52 inkl. Integrationstests auf den echten Daten |

**Einzige fachliche Änderung gegenüber Run 3:** In allen Kontextmodellen ersetzt der **Anstoss-Slot** die Variablen «Werktag» und «Abendspiel ab 20 Uhr». Slots: Samstag 17–19.59 Uhr (Referenz), Samstag ab 20 Uhr, Nachmittag vor 17 Uhr (Sonntag/Feiertag), Werktagabend ab 17 Uhr. Betroffen sind:

- die Phase-1-Kontextmodelle, die Kontext-Effekt-Matrix und die Diagnosekarte;
- die Nebenmodelle: Elastizität, Ankunft–Konsum, Durchsatz-Knick, Kiesplatz–Wetter, Promo-Tickets, Gästeanteil und Frühindikator T-7.

Datenaufbereitung, Definitionen (SOLL/IST/Public Netto, KF exkl. MwSt), Stichproben und Validierungslogik sind unverändert. Deskriptive Auswertungen nach Werktag/Wochenende oder «abends ab 20 Uhr» (z.B. No-Show nach Kontext) bleiben als Beschreibung erhalten.

**Datenlieferung:** lokale Fassung «fcstgallen1879_data_2026-10-01_1149». Sie ist nicht bytegleich mit der Lieferung von Run 3 (siehe Run-4-Voranalyse). **Kontrolle:** Gegenüber dem Run-3-Code auf genau dieser Lieferung sind Saison-KPI, Abdeckung, Abgleich und Klärungsfragen **identisch**. Abweichungen gibt es nur in modellabhängigen Werten: Erwartungswerte, Diagnose, Phase-2-Kandidaten und Befund-Texte zur Modellgüte. Phase 1 reproduziert die Run-4-Voranalyse (`run4_anstoss-slot_2026-11-02/`) **exakt**.

## Modellgüte (Anteil der saisonbereinigten Streuung, den der Kontext erklärt · Fehlerreduktion Leave-one-season-out)

| Zielgrösse | Run 3 | Run 4 |
|---|---|---|
| Kundenfranken exkl. MwSt | 33 % · +7 % | **82 % · +53 %** |
| Anwesenheitsquote | 42 % · +16 % | 62 % · +29 % |
| Bons je Public-Anwesendem | 19 % · +2 % | 50 % · +18 % |
| Ø Bon exkl. MwSt | 35 % · +5 % | 71 % · +39 % |
| Anteil Ankunft ≥ 45 min | 39 % · +8 % | 48 % · +17 % |

**Gegenproben zur KF-Erklärungsquote (03.11.2026, nur Aggregate):**
- Der Slot allein erklärt 64 %, Gegner/Wetter/Ferien allein 24 %, zusammen 82 %.
- Permutationstest (Slots innerhalb der Saison 1000-mal gemischt): Median 27 %, Maximum 41 %.
- Vorhersagefehler je ausgelassener Saison −48 bis −84 %.
- In jeder Saison hat Sonntagnachmittag den tiefsten und Samstag 17–19.59 Uhr den höchsten Ø KF.
- **Lesart:** Die 82 % beschreiben Unterschiede **zwischen Spielen innerhalb einer Saison**. Clubhebel verschieben vor allem das Niveau aller Spiele; der Rest von 18 % ist nicht «der Anteil des Clubs».

## Kernaussagen (belastbar = 95 %-KI ohne 0 und Vorzeichen stabil; gegenüber Samstag 17–19.59 Uhr; Zusammenhänge, keine Ursachen)

| Zielgrösse | Samstag ab 20 Uhr | Nachmittag (So/Feiertag) | Werktagabend | übrige belastbare Effekte |
|---|---|---|---|---|
| Kundenfranken | −3.6 % | **−15.7 %** | **−9.4 %** | +5 °C: +2.8 % |
| Bons je Anwesendem | n.s. | −8.2 % | n.s. | Regen bei Anreise −4.3 % |
| Ø Bon | n.s. | −8.3 % | −9.5 % | +5 °C: +1.9 % |
| Anwesenheitsquote | n.s. | **+3.7 Pp.** | **−7.4 Pp.** | Top-Gegner +3.4 Pp.; +5 °C +1.3 Pp.; Schulferien −2.6 Pp. |

**Ideen-Grundlage, Warenkorb nach Anstoss** (Alkohol-Proxy aus dem MwSt-Mix, 2023/24–2026/27):
- Samstag ab 20 Uhr: KF Alkohol +6 %, KF Food & alkoholfrei −15 %, Alkoholanteil am Umsatz +5.6 Pp.
- Sonntagnachmittag: Alkohol −26 %, Food & alkoholfrei −5 %.
- Werktagabend: Alkohol −12 %, Food & alkoholfrei −10 %.
- Kiesplatz je Anwesendem: Sonntagnachmittag −20 %, Werktagabend −29 %.

Die Elastizität Umsatz ~ Public-Anwesende mit Kontext liegt bei 1.01 (Run 3: 1.07), also bei proportionalem Wachstum; der Durchsatz-Knick ist weiterhin nicht nachweisbar (alle p ≥ 0.23).

**Diagnose:** Im KF-Modell liegen jetzt 6 Spiele über und 8 unter Erwartung (Run 3: 12 über, 6 unter). In Run 3 waren die «auffälligen» Spiele vor allem Samstag-18-Uhr-Spiele (über) bzw. Sonntagnachmittage (unter). Das war ein Effekt der Anstosszeit, kein Lernfall. Diagnosefälle in Run 4 sind deshalb die bessere Grundlage für Phase-2-Prüfkandidaten.

## Grenzen

- 76 Spiele (Bons/Ø Bon: 60), Teilsaison 2026/27 mit 4 Spielen. Freitag und Sonntag ab 17 Uhr kamen in der Stichprobe nicht vor.
- Anstosszeit und Spielplan sind für den Club extern (Liga/TV, D-045). Die Slot-Effekte sind kein Hebel, sondern Kontext. Für Massnahmen relevant ist, *was* an starken Terminen anders läuft.
- Hinweis «divide by zero» im Lauf (neu gegenüber Run 3), geprüft am 05.11.2026: Er stammt aus der Sensitivitätsvariante **«inkl. Cup und UEFA»** für Bons je Anwesendem und Ø Bon. Dort bestimmt ein einzelnes Spiel seinen eigenen Wert allein (Hebelwert 1), deshalb ist der robuste Standardfehler nicht bestimmbar. Blatt K3 zeigt für diese 14 Zeilen p = 1.0, und dieser Wert ist nicht zu interpretieren. Die Koeffizienten selbst sind geschätzt. Die Beurteilung «belastbar» nutzt aus den Sensitivitäten nur das Vorzeichen; Hauptschätzung, Intervalle und Urteile sind daher nicht betroffen.

## Reproduktion von Run 3

Run 3 lässt sich mit dem Code-Stand auf `main` vor Branch `feature/run4-komplett` reproduzieren. Die Run-3-Spezifikation bleibt zudem als `models.VARIABLEN_RUN3` für Vergleiche erhalten (`run4.py`).

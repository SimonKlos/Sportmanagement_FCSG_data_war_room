# Vorschlag: nächste Schritte Phase 1 und Übergang in Phase 2

Stand 14.10.2026 · erstellt von Simon (mit Claude Code) · intern, vertraulich (D-024) · **Vorschlag zur Diskussion im
Team, nichts davon ist entschieden** (Entscheide → `docs/decisions.md`, D-027).

Grundlage: Run 3 (`outputs/run3_kontext-v5_2026-10-14/`, Ralfs Kern mit Kontexttabelle v5 = Zahlenbasis, D-028),
Ralfs Ideen-Grundlage (`outputs/run2_ralf_2026-10-13/ideen_grundlage/`), Abgleich Simon/Ralf
(`docs/team/2026-10-14_abgleich_ralf_und_entscheide.md`).

---

## 1. Wo wir stehen

1. **Eine Zahlenbasis:** Ralfs Rechenkern ist im Repo (D-028). Unsere unabhängige Pipeline liefert für alle
   gemeinsamen Spiele **identische Kernzahlen** (SOLL, IST, Public Netto, Umsatz, Bons, KF, Scans). Die Unterschiede
   lassen sich vollständig erklären, nämlich mit den Datumskorrekturen und einer Rundungsfrage bei der Ankunft.
2. **Kontexttabelle v5 bestätigt die Ergebnisse:** Modellgüte, Effekte und Saison-KPI sind gegenüber Ralfs Lauf vom 13.10.
   unverändert (Run-3-README).
3. **Die Baseline steht inhaltlich**, ist aber formal noch nicht freigegeben. Offen sind die Definitionen (D-004/D-005, Sandro 16.10.)
   und die Steuerungsgrösse (D-003 vs. D-029).
4. **Erste Indikationen** für Massnahmenfelder liegen vor (Abschnitt 2). Es sind Zusammenhänge mit Evidenzgrad,
   **keine Wirkungsnachweise und keine Potenzialsummen**.

## 2. Erste Indikationen: wo Massnahmen ansetzen könnten

Wir haben Ralfs 9 Chancenfelder und die belastbaren Effekte der Kontext-Effekt-Matrix zu **drei Stossrichtungen** gebündelt. Die
CHF-Werte sind Caterer-Umsatz exkl. MwSt (kein Club-Ertrag, kein DB) und isolierte Rechenbausteine. Sie werden **nie
addiert**. Rechengrundlage 25/26: 13'785 Public-Anwesende je Spiel, KF exkl. MwSt CHF 14.51.

### A · Bezahlte, aber leere Plätze (Chancenfelder 1, 2, 6)
| Befund | Evidenz | Quelle |
|---|---|---|
| ~61'000 vergebene, aber leere Plätze pro Saison (25/26); der Zweitmarkt füllt nur 9 % davon, 70 % der Weiterverkäufe in den letzten 2 Tagen | stark | Ideen-Grundlage, Befund «Leere Plätze» |
| No-Show bei Inhouse-Grossbestellungen 29 % (bezahlt) bzw. 24 % (gratis), Online 2–4 Tickets 3.7 % (21/22–22/23) | mittel (alte Saisons) | Phase-2-Kandidat 1; unser H3 bestätigt: Frühkäufe > 30 Tage 17 % No-Show vs. 9 % kurzfristig |
| Fankurve D mit tiefster Abo-Anwesenheit (71–74 % vs. C 86–89 %, Näherung 26/27) | mittel | Blatt Tribuene_2627 |
| Frühindikator T-7 senkt den Prognosefehler der Anwesenden um 31 % | stark | Chancenfeld 6 |

**Mögliche Massnahmenrichtung:** Zweitmarkt früher und sichtbarer machen, Gruppen- und Gratiskontingente mit
Nutzungsbestätigung versehen, Spieltagsplanung über den T-7-Frühindikator (Personal, Ware). Rechenbaustein:
−1 Pp. No-Show ≈ CHF 29–49k Catering-Umsatz je Saison (φ 0.6–1.0). **Fehlt:** Eintrittsdaten je Ticket ab 23/24,
Abo-Anwesenheit je Spiel, Zweitmarkt-Angebot (Datenanfragen 2–4).

### B · Zeitfenster vor dem Anpfiff (Chancenfelder 3, 4)
| Befund | Evidenz | Quelle |
|---|---|---|
| **Natürliches Experiment:** Sektor D öffnet seit 02.04.2023 30 min früher → Ankunft +22.6 min (KI 19–26) gegenüber A/B/C | stark (Ankunft); Konsumwirkung **unbelegt** | Phase-2-Kandidat 4 |
| Tribüne C ist im Median nur 27 min vor Anpfiff im Stadion, 23 % kommen in den letzten 15 min | stark | Ideen-Grundlage |
| Ohne mobilen Verkauf (Runner/Bauchläden) KF −3.4 % unter Erwartung, mit +3.8 % darüber | an der Nachweisgrenze | Chancenfeld 4, Reto-Idee 5 |
| KF-Wachstum 23/24→25/26 kommt aus der **Kaufhäufigkeit** (+11 %), nicht aus Preisen | stark | Reto-Idee 7 |

**Mögliche Massnahmenrichtung:** Pilot «frühere Toröffnung» für einzelne Tore A/B/C, Angebot vor dem Anpfiff,
verlässliche Besetzung mit mobilem Verkauf. **Fehlt:** Payfix-Umsatz je Kasse und Viertelstunde mit Zuordnung
Kasse→Stand→Sektor (Datenanfrage 1). Ohne diese Daten bleibt die Konsumwirkung früherer Ankunft unmessbar. Unser H2 findet
auf Spielebene keinen Zusammenhang zwischen früher Ankunft und Bonsrate, wohl aber mit dem Ø Bon.

### C · Sortiment und Warenkorb nach Spieltyp und Wetter (Chancenfelder 5, 7)
| Befund | Evidenz | Quelle |
|---|---|---|
| Abendspiele ab 20 Uhr: Anwesenheit −4.1 Pp., aber KF +6.8 % und Bons/Anwesende +4.6 % | belastbar | Kontext-Effekt-Matrix |
| Abendspiele sind Getränkespiele: Alkohol-KF +22 %, Food −12 % (validierter MwSt-Proxy) | stark | Ideen-Grundlage |
| je +5 °C: KF +3.6 %, Ø Bon +2.3 %; Kiesplatz +10 % (Stadion +2.6 %), keine Verlagerung zwischen beiden | belastbar | Kontext-Effekt-Matrix, Chancenfeld 7 |
| Werktagsspiele: Ø Bon −4.0 % | belastbar | Kontext-Effekt-Matrix |

**Mögliche Massnahmenrichtung:** Sortiment und Standbesetzung nach Spieltyp (Abend/Werktag/Kälte), ein
Wetter-/Kiesplatz-Playbook und ein Angebot für späte Ankünfte an Werktagen. **Fehlt:** Artikel je Spiel statt Saison und
Einstandspreise/Marge (Datenanfrage 5). Ohne sie gibt es **keinen Deckungsbeitrag** (D-003).

**Nachrangig:** Chancenfeld 8 «Erfolgsmuster» (schwache Evidenz: 11 von 12 KF-Spitzenspielen samstags, 10 davon um
18:00) und Chancenfeld 9 «Nicht-Herren-Tage» (erst D-036 entscheiden).

## 3. Was in Phase 1 noch fehlt (Vorschlag, priorisiert)

| Prio | Was | Wer | Bis |
|---|---|---|---|
| 1 | **Termin Sandro 16.10.:** SOLL/IST/VIP/Public Netto (D-004), Umsatz-/MwSt-Basis inkl. CHF 14.51 = KF exkl. MwSt (D-005), Pseudonym-IDs (D-035), Information über die 6 Datumskorrekturen (D-030), Datenanfragen 1–7 priorisiert übergeben | Simon, Reto | 16.10. |
| 2 | **Steuerungsgrösse klären:** D-003 (DB) und Ralfs Rechnung auf Umsatz (D-029) widersprechen sich formal. Vorschlag: Phase 1 = Umsatz als belastbare Basis, DB-Ziel bleibt, sobald Kosten und Beteiligungsmodell vorliegen | Team | 23.10. |
| 3 | **Offene Methodenentscheide** D-031 (externe Daten), D-032 (Abgrenzung «letzte 15 Min.»), D-033 (Variablen und Schwellen, u. a. Anstosszeit als Slots: Sa 18:00), D-036 (Frauen in der Ideen-Grundlage), D-026 (unsere H1–H3 in Ralfs Effekt-Matrix überführen oder archivieren) | Team mit Ralf | 23.10. |
| 4 | **Baseline-Freigabe dokumentieren** (neuer D-Eintrag), dann Kontextmodelle und Diagnosekarte als Phase-1-Ergebnis final; die Diagnosekarte nur als Prüfkandidaten, ohne Potenzialsumme | Team | 06.11. |
| 5 | **Technik:** Ralfs Einverständnis zur Übernahme dokumentieren; unsere Tests mit künstlichen Daten auf Ralfs Kern übertragen (laufen ohne Rohdaten, auch auf dem Mac); Notebook auf Ralfs `mart_match` umstellen; unsere Analyse-Pipeline danach stilllegen, Bereinigung und Datenschutzprüfung behalten. Bekannte Schwäche unserer Pipeline: Datumsparser (27.09.2023 übersprungen) | Simon | 30.10. |
| 6 | **Ideen-Grundlage neu rechnen**, sobald D-036 entschieden ist (heute noch auf Kontexttabelle v3, Phase 1 unverändert) | Simon | nach D-036 |

## 4. Übergang in Phase 2 (09.–20.11.)

1. **Workshop Chancenfelder (ca. 2 h):** aus den Stossrichtungen A–C 3–5 Felder auswählen. Kriterien: Evidenz, Steuerbarkeit
   durch den Club, Leitplanken (kein Dynamic Pricing, keine Hospitality oder Kapazität, keine Personensegmentierung),
   Datenreife. **Unser Vorschlag als Startauswahl:** A (Gruppen-/Gratiskontingente + Zweitmarkt), B (Toröffnung-Pilot),
   C (Sortiment nach Spieltyp/Wetter). Begründung: alle drei hoch steuerbar und mit mindestens einem belastbaren oder
   natürlich-experimentellen Befund.
2. **Je Feld ein Steckbrief** (Vorlage `Ideen_Steckbrief` in Ralfs Excel): Mechanismus, Annahmen, Grobrechnung im
   `Hebel_Rechner` (φ-Szenarien), Messdesign für einen Pilot (z. B. Toröffnung: Differenz-in-Differenzen wie bei Sektor D;
   Gruppenkontingente: Vorher/Nachher-Vergleich der Nutzungsquote je Kanal).
3. **Von Umsatz zu DB:** Steckbriefe zunächst auf Umsatz exkl. MwSt. Für den Deckungsbeitrag ist Datenanfrage 5
   (Marge, Beteiligungsmodell) die Voraussetzung; ohne sie markieren wir DB als «nicht bezifferbar».
4. **Regeln für die Schlusspräsentation:**
   - Hebel nie addieren.
   - Jede Zahl mit Quelle (Arbeitsauftrag, Datenbefund, Test).
   - «Zusammenhang» statt «Effekt», wo kein Experiment vorliegt.
   - Die Diagnosekarte zeigt Referenzlücken, kein Potenzial.

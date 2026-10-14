# Abgleich Simon (Run 1) und Ralf (v1.1.0) – offene Entscheide und Integrationsplan

Stand 14.10.2026 · erstellt von Reto (mit Claude Code) · intern, vertraulich (NDA, D-024)

**Zweck:** Wir haben zwei Phase-1-Auswertungen desselben Auftrags. Dieses Dokument zeigt, wo sie übereinstimmen,
wo und warum sie abweichen, was wir als Team entscheiden müssen und wie wir Ralfs Vorschläge konkret in dieses Repo
und in unser weiteres Vorgehen einbauen. Die offenen Entscheide sind zusätzlich als D-028 bis D-035 in
`docs/decisions.md` erfasst (Regel D-027).

Quellen:
- Simon: dieses Repo, Run 1 vom 11.10.2026 (`docs/analysis/01_baseline_erste_erkenntnisse.md`, `outputs/run1_simon_2026-10-11/`)
- Ralf: Übergabe-Paket `FCSG_Uebergabe_v1.1.0` vom 13.10.2026 (`Ergebnisse_Phase1/Methodennotiz_Phase1.md`,
  `Ergebnisse_Ideen_Grundlage/Ideen_Grundlage_FCSG.md`, `Python_Auswertung/README.md`). Das Paket ist (noch) nicht
  in diesem Repo.

---

## 1. Kurzfazit

1. **Die Kernzahlen stimmen überein.** Beide verknüpfen 108 Herren-Pflichtspiele, beide kommen auf KF inkl. MwSt
   13.68 → 15.27 (Liga 21/22 → 25/26) und auf eine Elastizität von ungefähr 1.
2. **Ralf ist weiter:** Kontextmodelle, Kontext-Effekt-Matrix, Diagnosekarte, belegte Datumskorrekturen, externe
   Wetter-/Tabellendaten und eine Ideen-Grundlage für Phase 2. Simon hat bewusst bei der Baseline angehalten
   (Regel «Modellierung erst nach Baseline-Freigabe»).
3. **Ralf klärt drei offene Punkte** aus Simons Run 1 (Abschnitt 3).
4. **Wir brauchen eine einzige Zahlenbasis**, spätestens für Sandro und die Schlusspräsentation.
   Vorschlag: Ralfs Rechenkern in dieses Repo übernehmen; dieses Repo bleibt das Zuhause (Git, Decisions, Changelog,
   Regeln, Tests).

## 2. Gleich und anders

| Thema | Simon Run 1 | Ralf v1.1.0 | Grund der Abweichung |
|---|---|---|---|
| Spiele verknüpft | 108 | 108 | – |
| KF inkl. MwSt Liga 21/22 → 25/26 | 13.68 → 15.27 | 13.68 → 15.27 | – |
| Elastizität Umsatz/Zuschauer | 0.97 (KI 0.87–1.08, 105 Spiele) | 1.01 (KI 0.92–1.10, 96 Spiele) | Methode (saison-zentriert vs. Saison-Effekte im Modell), Stichprobe. Aussage identisch: ≈ proportional |
| Abgleich Retos Sichtung | 9 von 11 | 14 von 16 | Ralf prüft mehr Aussagen; R-10 und R-11 siehe Abschnitt 3 |
| Catering 23/24 | 18 Spiele, ein Spiel fehlt (Frage an Sandro) | 19 Spiele, Summe = Quell-Tab «Entwicklung» | Wie Ralf das fehlende Spiel zuordnet, im Code nachprüfen |
| Datumsfehler | im Unmatched-Report, Frage an Sandro | 6 belegte Korrekturen (`overrides/korrekturen.csv`) | Ralf korrigiert mit Belegen aus mehreren Quellen |
| Wetter | Tagesmittel aus Kontexttabelle | Temperatur/Regen zur Anpfiffzeit (MeteoSchweiz) | externe Daten |
| Kontextlücken 25/26 (6 Spiele) | bleiben leer (D-017) | aus öffentlichen Quellen ergänzt | externe Daten |
| Spielkontext-Tabelle | Version im lokalen Projektordner (welche?) | Version von Yves vom 09.10. 18:45 (zusätzliche Blätter «Ferien», «Paralellevent») | **Simon: bitte prüfen, welche Version Run 1 verwendet hat** |
| Steuerungsgrösse | Deckungsbeitrag (D-003) | Umsatz (wie Arbeitsauftrag) | Phase 1 rechnen beide faktisch auf Umsatz |
| Kontext | 45 Einzelkorrelationen (K1, explorativ) | 5 Modelle mit 6 vorab gewählten Variablen, Validierung | Simon wartet auf Baseline-Freigabe |
| Hypothesen | H1–H3 (Agent, D-026) | keine H1–H3; Effekt-Matrix + Vortest von Retos 12 Ideen | unterschiedlicher Ansatz |
| Tests | 83, nur künstliche Daten | 48, viele auf echten Daten | beide sinnvoll, ergänzen sich |
| Ablage | Git-Repo mit Decisions/Changelog | ZIP-Paket, Änderungsprotokoll im Excel | – |

## 3. Was Ralfs Auswertung bereits klärt

| Offener Punkt | Klärung durch Ralf | Status |
|---|---|---|
| R-10 «letzte 15 Min.»: Reto 17 %, Simon 12.9 % | Ralf 17.4 % **inkl. Scans nach Anpfiff**. Reto hat Zuspätkommende mitgezählt, Simon nicht (D-008) | Definition entscheiden (E-5) |
| CHF 14.50 vs. KF 15.27 | 14.50 = KF **exkl. MwSt**, alle Pflichtspiele 25/26, Summe/Summe = 14.51 | von Sandro bestätigen lassen |
| R-11 Elastizität 1.14 (Reto, 22 Spiele) | auf 25/26 + 26/27 = 1.22, auf allen Spielen 1.01: kleine Stichprobe, kein belastbarer Skaleneffekt | erledigt |
| Gäste im KF-Nenner | Gästefans ≈ 4.7 % des Public Netto; mehr Gäste gehen mit **höherem** KF einher | in Frage an Sandro einbeziehen |
| Retos Faustwerte | 13'785 Public-Anwesende statt 18'000 → Faustwerte 23–31 % zu hoch | Reto prüft und übernimmt |

## 4. Offene Entscheide (Vorschlag)

Alle auch in `docs/decisions.md` (D-028 bis D-035), Status **offen**.

| ID | Entscheid | Optionen | Vorschlag |
|---|---|---|---|
| E-1 (D-028) | **Eine Zahlenbasis** für Sandro und Schlusspräsentation | A: Ralfs Rechenkern ins Repo · B: Simons Code, Ralfs Teile nachbauen | **A** (weiter, spart Zeit bis 06.11.); Repo-Regeln, Decisions, Changelog und Simons Tests bleiben |
| E-2 (D-029) | Steuerungsgrösse | Umsatz (AA) · DB (D-003) | Phase 1 Umsatz, DB als Ziel für Phase 2 sobald Kosten/Beteiligungsmodell vorliegen; D-003 entsprechend präzisieren |
| E-3 (D-030) | Ralfs 6 Datumskorrekturen übernehmen | ja · nein | ja, mit Belegen; Sandro trotzdem informieren |
| E-4 (D-031) | Externe Daten (MeteoSchweiz, football-data.co.uk, öffentliche Ergänzung der 6 Kontextspiele) | zulassen · nicht | zulassen (öffentlich, keine FCSG-Daten fliessen ab), Quellen dokumentiert |
| E-5 (D-032) | «Letzte 15 Min.» | nur vor Anpfiff (Simon) · inkl. nach Anpfiff (Ralf/Reto) | beide ausweisen, klar beschriften; für Pausen-/Zuspät-Analysen inkl. nach Anpfiff |
| E-6 (D-033) | Die 6 Modellvariablen und Schwellen (Top-Gegner = FCB/YB/FCZ, Werktag, Abendspiel ≥ 20 Uhr, Temperatur, Regen ≥ 0.5 mm in 2 h, Schulferien) | bestätigen · anpassen | mit Ralf durchgehen; **Anstosszeit als Slots** prüfen (FCSG: Sa 18:00 am stärksten, ≥ 20 Uhr bildet das nicht ab) |
| E-7 (D-034) | Spielkontext-Tabelle: welche Version gilt | Projektordner · Version Yves 09.10. | eine Version festlegen, Ablage und Pflege klären |
| E-8 (D-035) | Pseudonyme Zutritts-IDs zur Deduplizierung (wie Ralf) | zulassen · nicht | erst nach Sandros Antwort (D-006, D-023) |

Dazu bestehende offene Punkte: D-004/D-005 (Definitionen, Sandro), D-023 (Datenraum), D-026 (Hypothesen H1–H3).

## 5. Wie wir Ralfs Vorschläge konkret einbauen

### 5.1 Technisch: Ralfs Rechenkern in dieses Repo

1. **Ralfs Einverständnis** einholen; Paket ohne Ergebnisse mit Rohdatenbezug übernehmen (enthält keine Rohdaten).
2. Branch `feature/ralf-pipeline`: Ralfs `Python_Auswertung/` als eigenen Ordner (z. B. `ralf/`) ablegen, **Simons
   Code bleibt zunächst unverändert**. Ergebnisse von Ralfs Lauf als `outputs/run2_ralf_2026-10-13/` mit README.
3. **Abgleichstest** schreiben: Kennzahlen beider Pipelines je Spiel vergleichen (gleich / Abweichung mit Grund).
4. Nach E-1: Simons Code für die Analyse ersetzen oder stilllegen; Simons Tests auf künstlichen Daten auf Ralfs Kern
   übertragen (laufen ohne Rohdaten, z. B. für alle im Team auf dem Mac).
5. `.vscode/tasks.json`, README und Setup für **Windows und Mac**; jede Änderung mit Decision und Changelog.

### 5.2 Inhaltlich Phase 1: was direkt in Baseline und Bericht fliesst

| Ralfs Vorschlag | Wohin | Was wir tun |
|---|---|---|
| 6 Datumskorrekturen | Pipeline + D-030 | übernehmen, Sandro informieren |
| Präzisere Fragen an Sandro (SOLL-Kapazitätswert, VIP-Abzug, 14.51, Kiesplatz, Artikel brutto/netto) | Folie 8, `docs/team/2026-10-14_fragen_sandro_v2.md` | am 16.10. vorlegen |
| Kontext-Effekt-Matrix und Diagnosekarte | Bericht Phase 1 | nach Baseline-Freigabe und E-6 übernehmen; Diagnosekarte nur als Prüfkandidaten, keine Potenzialsumme |
| 7 Prüfkandidaten Phase 2 (No-Show Gross-/Gratisbestellungen, Abendspiele, Werktage, Toröffnung, Kälte/Sortiment, operative Engpässe, Ausverkaufskurven) | Abschluss Phase 1 | als «Kandidaten für Phase 2» im Bericht, ohne Quantifizierung |
| Datenanfragen (u. a. Payfix je Kasse/Viertelstunde, Abo-Anwesenheit je Spiel, Zweitmarkt-Angebot) | Data Request an FCSG | nach dem 16.10. priorisiert nachreichen |

### 5.3 Inhaltlich Phase 2 (09.–20.11.): Chancenfelder → Massnahmen

Ralfs Ideen-Grundlage liefert **keine fertigen Massnahmen**, sondern je Chancenfeld Befund, Evidenz, Steuerbarkeit,
Leitfragen und einen Hebel-Rechner. Vorgehen:

1. **Workshop** (Team, ca. 2 h): 9 Chancenfelder durchgehen, 3–5 auswählen. Kriterien: Evidenz, Steuerbarkeit durch den
   Club, Leitplanken (kein Dynamic Pricing, keine Hospitality/Kapazität, keine Personensegmentierung), Datenreife.
2. **Je Auswahl ein Steckbrief** (Vorlage `Ideen_Steckbrief` in Ralfs Excel): Massnahme, Mechanismus, Annahmen,
   Grobrechnung im Blatt `Szenarien`/`Hebel_Rechner`, wie ein Pilot messbar wäre.
3. **Retos 12 Ideen** sind bereits vorgetestet (erledigt / weiterverfolgen / umformulieren / zurückstellen /
   nicht bauen) und fliessen in den Workshop ein.
4. **Regeln für die Präsentation:** Hebel nie addieren; CHF = Caterer-Umsatz exkl. MwSt, nicht Club-Ertrag; Begründung
   jeder Zahl mit Quelle (Arbeitsauftrag, Datenbefund, Test).

| Nr. | Chancenfeld (Ralf) | Evidenz | Steuerbarkeit |
|---|---|---|---|
| 1 | Leere bezahlte Plätze aktivieren | stark | hoch |
| 2 | Gruppen- und Gratistickets, die nicht genutzt werden | mittel | hoch |
| 3 | Das Zeitfenster vor dem Anpfiff | mittel | hoch |
| 4 | Mehr Kaufmomente: die Kauffrequenz | mittel | hoch |
| 5 | Warenkorb und Sortiment nach Spieltyp | stark | hoch |
| 6 | Spieltage planbar machen (Frühindikator) | stark | mittel |
| 7 | Wetter und Kiesplatz | stark | mittel |
| 8 | Erfolgsmuster wiederholen | schwach | mittel |
| 9 | Das Stadion an Nicht-Herren-Tagen | schwach | hoch |

### 5.4 Begründbarkeit (für die Präsentation)

| Element | Begründung vorhanden? |
|---|---|
| Ein Modell je Zielgrösse, Saison-Effekte, wenige Variablen | ja – Arbeitsauftrag S. 7–8 |
| Validierung Leave-one-season-out gegen Saisonmittel, Sensitivitäten, Vorzeichenstabilität | ja – Arbeitsauftrag + Ergebnis (`K2_Modellguete`) |
| Ausgeschlossene Variablen | ja – Blatt `K5_Variablen_Einordnung` |
| **Wahl und Schwellen der 6 Variablen** | **offen** – wer hat sie wann festgelegt? (E-6, Frage an Ralf) |
| **Herleitung der 9 Chancenfelder** | **offen** – explorativ; Ralf um kurze Entstehungsnotiz bitten |

## 6. Nächste Schritte

| Wann | Was | Wer |
|---|---|---|
| bis 15.10. | E-1 entscheiden: welche Zahlen zeigen wir Sandro? Deck anpassen (Kontext- statt Kausaleffekte, «inkl. MwSt», Elastizität vorsichtig) | Team |
| 16.10. | Termin Sandro mit Fragenliste v2 | Simon, Reto |
| bis 23.10. | Durchsprache mit Ralf (E-6, Chancenfelder-Herleitung); E-2 bis E-8 entscheiden | Team, Ralf |
| bis 30.10. | Ralfs Kern ins Repo (5.1), Sandros Antworten einarbeiten, neu rechnen | Simon, Ralf |
| bis 06.11. | Baseline-Freigabe dokumentieren, Kontextmodelle und Diagnosekarte final | Team |
| 09.–20.11. | Phase 2: Workshop Chancenfelder, Steckbriefe | Team |
| 16.–25.11. | Schlusspräsentation | Team |

# Synthese: Zielbild, Widersprüche, offene Punkte

Fassung v1, 10.10.2026. Grundlage: `01_…`, `02_…`, `03_…`. Diese Datei enthält **Einordnungen des Agenten**;
die Fundstellen sind angegeben. Der Status «quellengeprüft» gilt nur für Aussagen mit Seitenverweis.
**Kein Teil davon ist mit echten Daten verprobt.**

## Arbeitsrangfolge (Annahme, Freigabe offen → D-002)
Arbeitsauftrag 08.10.2026 > Datenquellen & Treiberbaum 08.10.2026 > Projektantrag 25.09.2026.
Begründung: Der Arbeitsauftrag sagt, dass Retos Aufbereitung das hypothetische Daten-Zielbild ersetzt (AA S. 1).

## Fachliches Zielbild Phase 1 (quellengeprüft gegen PDFs, nicht gegen Daten)
- Eine Zeile pro Heimspiel (`mart_match`), Schlüssel Spieldatum + Auflösung bei Mehrfach-Events (AA S. 4–5).
- Zielgrössen getrennt: Anwesenheitsquote, KF, Bons je Public-Anwesendem, Ø Bon (AA S. 7).
- Ankunft und Einzelticket-Vorlauf als eigenständige Module (AA S. 2, S. 6–7).
- Diagnosekarte = erwartet − beobachtet, ohne Potenzialbehauptung (AA S. 8–9).
- Steuerungsgrösse **Deckungsbeitrag** (Entscheid D-003, 11.10.2026; weicht bewusst von AA S. 1 ab). Umsatz bleibt Grundlage; DB nur mit belegten Kostendaten.

## Widersprüche zwischen den Quellen

| ID | Thema | Projektantrag (PA) | Datenquellen (DQ) | Arbeitsauftrag (AA) | Arbeitsregel |
|---|---|---|---|---|---|
| W-01 | Steuerungsgrösse | DB pro Anwesendem (S. 2) | – | Umsatz; DB später, mit FCSG abstimmen (S. 1, S. 6) | **Deckungsbeitrag** (D-003, entschieden 11.10.2026) |
| W-02 | Hospitality | Fokus «Publikum und Hospitality» (S. 2) | nicht in Daten (S. 4) | keine Hospitality (S. 2) | ausgeschlossen |
| W-03 | Catering-Granularität | je Viertelstunde, Verkaufsstelle→Sektor (S. 2) | keine Uhrzeit, kein Stand→Sektor (S. 3–4, 6–7) | nicht versprechen (S. 2, S. 7) | keine Zeit-/Sektor-Konsumoutputs |
| W-04 | Kapazität/Absatzverlauf | Kapazität je Sektor, Verkaufsstand je Tag (S. 2) | Kapazität als Treiber genannt (S. 1), aber keine Kapazitätsdatei beschrieben | nur mit verifizierter Kapazität; Verkaufsquote als Hebel zurückgestellt (S. 2, S. 6) | Kapazität out of scope als Hebel; Sektorsperren als Kontext (D-022, entschieden 11.10.2026) |
| W-05 | Wetter | zur Anstosszeit (S. 2) | Tagesmittel (S. 5) | Tagesmittel (S. 4) | als Tagesmittel kennzeichnen |
| W-06 | Bedeutung Rest | – | «Residuum ist der Teil, den der Club beeinflussen kann»; negatives Residuum = zu wenig Umsatz (S. 5) | Diagnoselücke = erwartet − beobachtet; Rest enthält Messfehler/Zufall; kein Potenzialbeweis (S. 8–9) | AA-Definition und -Vorzeichen |
| W-07 | Personendaten | keine Personendaten (S. 2) | Einzeltickets-Exporte enthalten Personendaten (S. 2, S. 7) | Personenfelder ausschliessen, mit Sandro klären (S. 3, S. 9) | Blocker vor Import dieser Dateien |
| W-08 | Arbeitsort | ausschliesslich im Datenraum, ohne Export, NDA (S. 2) | – | Arbeit im Datenraum (S. 9) | **Lokaler Agent mit externem Modell ist ohne Freigabe kein zulässiger Ort für echte Daten** |
| W-09 | Anwesende im Treiberbaum | – | Knoten «Anwesende (IST)» (S. 6), KF aber über Public Netto (S. 3) | Public-Anwesende × KF (S. 5) | Scope «Public» explizit führen |
| W-10 | Ergebnisart | «quantifizierte Umsatzpotenziale mit Priorisierung» (S. 1) | – | Phase 2, zurückgestellt (S. 2, S. 11) | keine Potenzialquantifizierung in Phase 1 |
| W-11 | Spielkontext-Tabelle | Gruppe baut selbst, ~100 Spiele (S. 1) | existiert, 22/23–26/27, ~90 Spiele (S. 4) | ~90 laut Sichtung (S. 4) | vorhandene Tabelle inventarisieren |
| W-12 | Ausverkauft-Analyse | früh/spät/nicht ausverkauft (S. 2) | – | nur mit verifizierter Ausverkauft-Info/vollständigem Bestand (S. 6) | nur unter Vorbehalt |

## Blocker vor echtem Datenimport (nicht vor technischem Aufbau)
1. **Datenmodus** (D-001): Code-only oder freigegebener Datenmodus? W-08 spricht gegen Rohdaten im Agentenkontext.
2. Personenfelder/Deduplizierung klären (AA S. 11, Frage 5).
3. Definitionen SOLL/IST/VIP/Gäste/Public Netto und Umsatzbasis (AA S. 10, Fragen 1–2).
4. Spaltenwörterbuch «FCSG_Daten-Handbuch» liegt nicht vor.

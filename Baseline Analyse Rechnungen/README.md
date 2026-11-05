# Baseline Analyse Rechnungen

Interner Sammelpunkt für alle Rechenstände, Gegenrechnungen und analytischen Prüfoutputs. Dieser Ordner hiess bis 01.11.2026 `outputs`. **Keine externe Übergabe dieses Ordners.** Die Laufdateien wurden nur verschoben und nicht inhaltlich verändert; historische Pfadangaben in eingefrorenen Artefakten können weiterhin den alten Namen enthalten.

## Verbindliche Zahlenbasis

- [Run 4 (komplett) – Anstoss-Slot](run4_komplett_2026-11-05/README.md): **Zahlenbasis ab 05.11.2026** (D-048). Ganzer Rechenkern mit Anstoss-Slot statt Werktag + Abendspiel.
- [Phase-1-Rechnung](run4_komplett_2026-11-05/kern_phase1/): Baseline, Modelle, Tabellen, Prüfprotokoll und Ergebnis-Excel.
- [Ideen-Grundlage](run4_komplett_2026-11-05/ideen_grundlage/): vertiefende Analysen, Chancenfelder und Szenariobausteine derselben Zahlenbasis.
- [Run-4-Voranalyse](run4_anstoss-slot_2026-11-02/README.md): Slot-Modell mit Sensitivitäten (2021/22 mit Covid, ohne 2023/24) und Koeffizienten für den Spielrechner.
- [Run 3 – Kontext v5](run3_kontext-v5_2026-10-14/README.md): bisherige Zahlenbasis (D-028/D-034), jetzt eingefrorenes Archiv.
- [Gegenrechnung](run3_kontext-v5_2026-10-14/abgleich_simon_ralf/): interner Abgleich der Kernzahlen.
- [Frühere Baseline](run3_kontext-v5_2026-10-14/simon_baseline/): Gegenrechnung/Erklärmaterial, keine konkurrierende freigegebene Zahlenbasis.

- [Run 4 – Anstoss-Slot](run4_anstoss-slot_2026-11-02/README.md): ergänzende Kontextmodelle mit Anstoss-Slot und Sensitivitäten (D-046); Übernahme als Zahlenbasis offen.

Run 1 bis Run 3 bleiben als historische Archive erhalten. Doppelte Diagramme und interne Abstimmungen werden dort zur Nachvollziehbarkeit **nicht gelöscht oder nachträglich umgeschrieben**.

## Wo liegt die Rechenlogik?

Dieser Ordner ist der fachliche Einstieg zu den Rechnungen und enthält jetzt auch den massgeblichen Rechenkern sowie das Notebook-Archiv. Die Bereinigungs-/Gegenrechnungspipeline bleibt technisch unter `src/`:

- [Rechenkern](Rechenkern/README_REPO.md) – kanonische Analyse.
- [Notebooks_Archiv](Notebooks_Archiv/README.md) – vorhandene historische Notebooks, nicht Teil der externen Deliverables.
- [Bereinigung und Gegenrechnung](../src/fcsg/README.md).
- [Tests](../tests/) – künstliche Fixtures; reale Daten werden dadurch nicht neu verprobt.
- [Konfiguration](../config/README.md) – keine lokalen Datenpfade oder Geheimnisse versionieren.

Neue geteilte Rechenstände erhalten eigene `runN_<name>_<datum>/`-Ordner mit Quellen-/Laufreferenz und Prüfstatus; alte Stände werden nicht überschrieben. Technische Fixture-Läufe bleiben ignoriert. Lokale echte Daten und Rechenläufe bleiben ausserhalb des Repos gemäss lokaler Konfiguration.

## Trennung zur Übergabe

Nur kuratierte, neutral formulierte Unterlagen gehören nach [Deliverables](../Deliverables/README.md). Definitionen, Entscheide und interne Abstimmungen stehen in [Quellen und interne Dokumentation](../Quellen%20und%20interne%20Dokumentation/README.md). Kein neues Modell und keine neue Baseline-Rechnung durch diese Umstrukturierung.

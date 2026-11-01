# Baseline Analyse Rechnungen

Interner Sammelpunkt für alle Rechenstände, Gegenrechnungen und analytischen Prüfoutputs. Dieser Ordner hiess bis 01.11.2026 `outputs`. **Keine externe Übergabe dieses Ordners.** Die Laufdateien wurden nur verschoben und nicht inhaltlich verändert; historische Pfadangaben in eingefrorenen Artefakten können weiterhin den alten Namen enthalten.

## Verbindliche Zahlenbasis

- [Run 3 – Kontext v5](run3_kontext-v5_2026-10-14/README.md): jüngster geteilter Analyse-Stand, fachliche Zahlenbasis gemäss D-028/D-034.
- [Phase-1-Rechnung](run3_kontext-v5_2026-10-14/ralf_kern_phase1/): Baseline, Modelle, Tabellen, Prüfprotokoll und Ergebnis-Excel.
- [Ideen-Grundlage](run3_kontext-v5_2026-10-14/ralf_ideen_grundlage/): vertiefende Analysen, bestehende Chancenfelder und Szenariobausteine derselben Zahlenbasis.
- [Gegenrechnung](run3_kontext-v5_2026-10-14/abgleich_simon_ralf/): interner Abgleich der Kernzahlen.
- [Frühere Baseline](run3_kontext-v5_2026-10-14/simon_baseline/): Gegenrechnung/Erklärmaterial, keine konkurrierende freigegebene Zahlenbasis.

Run 1 und Run 2 bleiben als historische Archive erhalten. Doppelte Diagramme und interne Abstimmungen werden dort zur Nachvollziehbarkeit **nicht gelöscht oder nachträglich umgeschrieben**.

## Wo liegt die Rechenlogik?

Dieser Ordner ist der fachliche Einstieg zu den Rechnungen. Der ausführbare Code bleibt aus Gründen der Paket-/Importstruktur ohne Duplizierung an seinen bestehenden Stellen:

- [Rechenkern](../ralf/README_REPO.md) – kanonische Analyse.
- [Bereinigung und Gegenrechnung](../src/fcsg/README.md).
- [Tests](../tests/) – künstliche Fixtures; reale Daten werden dadurch nicht neu verprobt.
- [Konfiguration](../config/README.md) – keine lokalen Datenpfade oder Geheimnisse versionieren.

Neue geteilte Rechenstände erhalten eigene `runN_<name>_<datum>/`-Ordner mit Quellen-/Laufreferenz und Prüfstatus; alte Stände werden nicht überschrieben. Technische Fixture-Läufe bleiben ignoriert. Lokale echte Daten und Rechenläufe bleiben ausserhalb des Repos gemäss lokaler Konfiguration.

## Trennung zur Übergabe

Nur kuratierte, neutral formulierte Unterlagen gehören nach [Deliverables](../Deliverables/README.md). Definitionen, Entscheide und interne Abstimmungen stehen in [Quellen und interne Dokumentation](../Quellen%20und%20interne%20Dokumentation/README.md). Kein neues Modell und keine neue Baseline-Rechnung durch diese Umstrukturierung.

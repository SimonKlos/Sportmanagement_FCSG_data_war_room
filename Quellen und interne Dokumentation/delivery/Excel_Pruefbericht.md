# FCSG – Baseline und Chancenfelder

**Datei:** `FCSG_Baseline_und_Chancenfelder.xlsx`
**Status:** privater Entwurf zur Partnerprüfung, keine Baseline- oder Massnahmenfreigabe.

## Aufbau

Einstieg und Navigation → KPI-Definitionen → Abdeckung → Saison- und Spielbaseline → thematische Details → neun bestehende Chancenfelder → Ideensteckbrief, Hebel-Rechner und Szenarien → Kontextmodelle, Grenzen und Quellen.

Analytische Blätter enthalten statische Werte aus den bestehenden Exporten vom 14.10.2026. Es gibt keine Rohdatenverbindung und keine automatische Aktualisierung der Baseline. Nur der isolierte Szenariorechner enthält Formeln. Die Vergleichssektion des alten Rechners und interne Vergleichsblätter wurden nicht übernommen; Basiswerte und Berechnungszellen des isolierten Rechners blieben erhalten.

## Tatsächlich ausgeführte Prüfung

- Ausgabe erneut mit openpyxl geöffnet, getrennt mit Formeln und gespeicherten Ergebniswerten.
- 10’705 numerische, boolesche und Datumszellen der übernommenen Quelltabellen zellgenau identisch.
- 39 Formeltexte und ihre 39 gespeicherten Quellergebnisse identisch; neun definierte Namen unverändert. Zahlenformate und Datenvalidierungen der Rechnerblätter ebenfalls identisch.
- Alle sechs isolierten Jahreshebel sowie beide vorbelegten Szenarien unabhängig arithmetisch gegen die gespeicherten Ergebnisse geprüft.
- Alle 17 Saison-/Wettbewerbssichten mit den passenden Spielaggregaten abgestimmt: Spielzahl, IST, Public-Netto und Umsatz exkl. MwSt. Kleine Summationsabweichungen unter CHF 0.0000001 sind reine Gleitkommaeffekte; keine Quellzellen wurden dafür gerundet oder verändert.
- Spielbaseline: 109 Exportzeilen, davon 108 gespielte Kernspiele. Der abgesagte Anlass vom 14.03.2026 ist als `kernscope = FALSCH` gekennzeichnet und aus den Saisonabstimmungen ausgeschlossen. Nicht ungefiltert alle Zeilen summieren.
- Keine defekten Formel-Blattverweise, Fehlerzellen, externen Arbeitsmappenverbindungen oder übernommenen Grafikbilder gefunden. Keine Zellkommentare oder persönlichen Autorenmetadaten; Autor ist generisch „FCSG Projektteam“. Interne Personennamen im Zelltext geprüft und ausgeschlossen.
- SHA-256-Vorher-/Nachher-Abgleich: alle 149 Dateien im historischen Analysearchiv byte-identisch.

### Konkrete Abstimmung, Meisterschaft 2025/26

| Kennzahl | Übernommener Wert |
|---|---:|
| Gespielte Kernspiele | 19 |
| IST gesamt | 275’692 |
| Public-Anwesende gesamt | 261’924 |
| Public-Catering-Systemumsatz exkl. MwSt. | CHF 3’799’454.503672526 |
| Hebel_Rechner!G19: 1 Pp. weniger No-Show, φ = 1 | CHF 48’831.93473638525 |
| Hebel_Rechner!G24: CHF 1 höherer Kundenfranken | CHF 261’924 |

Die letzte Spalte des Rechners sind isolierte Umsatzszenarien, keine gemessenen Potenziale und keine Cluberlöse. Nicht addieren.

## Ehrliche Grenzen

- Keine Excel-/LibreOffice-Rechenengine in dieser Umgebung verfügbar. Quell-Caches wurden erhalten und die vorbelegten Ergebnisse unabhängig arithmetisch geprüft; eine Neuberechnung in Microsoft Excel wurde nicht behauptet. Die Datei fordert beim Öffnen automatische Neuberechnung an. Kein visueller Rendering-Test in Excel durchgeführt.
- Keine erneute Rohdatenprüfung, keine Änderung der bestehenden analytischen Modelle und keine Sensitivitäts-Neuberechnung.
- Gutschein-Transaktionszählung im Übergang 2023/24 begrenzt die Vergleichbarkeit von Bonsrate und Durchschnittsbon; dies ist kein Nachweis falscher Umsätze.
- Durchgängige Definition des Public-Nenners sowie vertraglicher Club-Beteiligungssatz und -basis sind offen. Eine Quote von 20 % ist unbestätigt und wurde nirgends auf die Baseline oder den Rechner angewendet.
- Phase 2 prüft primär inkrementellen Umsatz. Systemumsatz, Cluberlös und Deckungsbeitrag bleiben getrennt. Historische Assoziationen sind keine kausalen Massnahmeneffekte.

Maschinenlesbare Nachweise einschließlich Quellhashes, Zellabgleich und Rechenbeispielen: `FCSG_Excel_Pruefprotokoll.json`.

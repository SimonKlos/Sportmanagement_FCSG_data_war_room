# Prüfbericht – vertraulich

## Ergebnis

Der Offline-HTML-Reviewentwurf wurde in Chrome 145 Headless über eine lokale `file://`-Adresse geöffnet und geprüft. Kein Webserver, keine Veröffentlichung. Desktop 1440 × 1000 und Mobil 390 × 844; Screenshots wurden visuell geprüft.

- 9 Berichtskapitel inklusive Quellenanhang; 9 Chancenfelder in 3 Themen.
- 7 neu gezeichnete SVG; alle separat als gültiges XML lesbar und inline im Bericht enthalten.
- 6 Methodik-Foldouts; Öffnen/Schliessen im Browser erfolgreich.
- Keine doppelten IDs, fehlenden Sprungziele oder defekten lokalen Dateilinks.
- Keine externen Ressourcen, Skripte oder HTTP(S)-Anfragen; einziges geladenes Dokument war die lokale HTML-Datei.
- Kein horizontaler Seitenüberlauf bei Desktop oder Mobil; mobile Diagramme sind innerhalb ihrer Abbildung scrollbar.
- SVG-Texte bleiben innerhalb der ViewBox.
- Im gerenderten Bericht keine internen Personennamen oder Personenvergleiche.
- Quellenmapping: 16 Zuordnungen mit ungerundeten Aggregaten, Selektoren und SHA-256; Quellhashes nach Erstellung unverändert.
- A4-Prüfdruck tatsächlich erzeugt: 17 Seiten. Navigation ausgeblendet. Textauslese bestätigt Inhalte aller 6 Methodik-Foldouts im PDF, auch wenn im HTML geschlossen. Druckseiten 1 und 7 visuell geprüft.

Maschinenlesbare Nachweise: `Browserpruefung.json`, `Abschlusspruefung.json`, `Druckpruefung.json`. Der neuere `Abschlusspruefung.json` enthält die vollständige Prüfung aller sechs Foldouts. `Pruefdruck.pdf` ist ein QA-Export, kein fachlich freigegebenes Veröffentlichungsdokument.

## Technische Stolperstelle und Behebung

Der Standard-Browserstart scheiterte zunächst an fehlenden Systembibliotheken. Für den lokalen Test wurden Bibliotheken ausschliesslich in einem temporären Unterordner des Berichtsordners entpackt; keine Systeminstallation vorgenommen. Nach den Tests wurden diese Hilfsdateien entfernt. Der Testläufer `../verify_report.mjs` benötigt für eine Wiederholung Chrome samt dessen Laufzeitbibliotheken. Das HTML selbst benötigt diese Hilfsdateien nicht.

Ein erster Prüfdruck zeigte, dass reine `display:block`-Regeln geschlossene `details`-Inhalte nicht zuverlässig drucken. Die Druck-CSS wurde um `details::details-content { content-visibility: visible }` ergänzt; ein zweiter realer PDF-Export und Textauslese bestätigten die vollständigen Methoden. Die zusätzlichen Bibliotheken und Python-Pakete waren nur QA-Hilfen und sind nicht Teil der Auslieferung.

## Inhaltliche Leitplanken

- Nur historische Aggregate übernommen; keine Neuberechnung, Modelländerung oder Rohdatenprüfung.
- Datenstichtag 12.09.2026; Berichtsstand 01.11.2026; neutraler, vertraulicher Reviewentwurf ohne Release-Freigabe.
- Meisterschaft, Pflichtspiele, Modulstichproben und Teil-Saison 2026/27 klar getrennt.
- 60’942 als Differenz SOLL−IST bezeichnet, nicht pauschal als bezahlte Plätze; ticketbasierter Teil separat benannt.
- KF/Umsatz und Kausalwirkung nicht gleichgesetzt; keine erfundenen Kosten oder addierten Potenziale.
- Bonsrate/Ø Bon und deren historische Entwicklung unter Erfassungsvorbehalt; Sensitivitätsprüfung ohne Übergangssaison 2023/24 offen.
- Gutschein-/unverbuchter Umsatzanteil 2023/24: 0,7581 %, ausdrücklich keine Transaktionsfehlerquote.
- Phase 2 primär inkrementeller Umsatz exkl. MwSt.; Catering-Systemumsatz vom Cluberlös getrennt. 20 % nur unbestätigte optionale Rechenannahme, keine angewandte Baseline-Skalierung.

## Grenzen der Prüfung

Keine Cross-Browser-Zertifizierung oder vollständige WCAG-Prüfung. Visuelle Stichproben und DOM-/Drucktests ersetzen keine fachliche Abnahme. Original-Rohdaten fehlen; offene Definitions- und Vertragsfragen sowie die Bons-Sensitivität bleiben echte Freigabepunkte.

# Abnahmecheck der Review-Unterlagen – 01.11.2026

## Gelieferter Umfang

- Eigenständiger HTML-Bericht mit neun Kapiteln, neun bestehenden Chancenfeldern in drei Themen und sieben neu gestalteten SVG-Diagrammen.
- Strukturierte Excel mit 31 Blättern; bestehender isolierter Hebel-/Szenariorechner erhalten.
- Ausführlicher Folienleitfaden: 14 Kernfolien plus sechs Backup-Folien, keine PPT/PPTX.
- Externe Methodik-Lesehilfe und Excel-Leseanleitung.
- Technische Build-/QA-Dateien bewusst nur hier in der internen Delivery-Dokumentation, nicht im externen Paket.

## Prüfungen

Der Hauptagent hat 10’705 numerische/boolesche/Datumszellen unabhängig gegen die angegebenen Quelltabellen und 39 Formeltexte gegen den ursprünglichen Chancen-Rechner abgeglichen. Exportprüfung des Builders bestätigt zusätzlich 39 erhaltene Formel-Caches, neun definierte Namen und Abstimmung aller 17 Saison-/Wettbewerbssichten. Keine versteckte 20-%-Skalierung oder neue analytische Modellierung.

148 historische Laufdateien wurden gegen den Git-Stand vor der Umstrukturierung per Blob-Hash geprüft: byte-identisch. Das neu gestaltete übergeordnete README ist davon ausgenommen. Die Builder prüften ausserdem ihre jeweiligen vollständigen aktuellen Archiv-Snapshots; deren 149 Dateien enthalten dieses neue README und sind deshalb eine andere Zählbasis, kein Widerspruch.

Die erste Berichtsfassung wurde durch die Produktion in Chrome auf Desktop/Mobil sowie im Druck geprüft, Screenshots wurden auch vom Hauptagenten gesichtet. Nach der fachlichen Review wurden drei Darstellungsfehler korrigiert: G06 verwendet Public-Anwesende statt IST/SOLL als ersten Umsatzfaktor; Kiesplatz-Effekte mit Einheit Pp. erhalten Pp.-Format; das erste Chancenfeld vermeidet die Gleichsetzung der SOLL−IST-Differenz mit bezahlten Plätzen bzw. nachgewiesener zusätzlicher Wiederbesetzung. Nur Texte/Format/Schema geändert, keine Werte oder Rechenformeln.

Nach diesen Korrekturen hat der Hauptagent G06 gegen die identische HTML-Einbettung, Excel-Labels und Einheiten, alle lokalen HTML-Verweise, SVG-Struktur, Archiv-Hashes, Builder-Syntax und Abwesenheit von PPT-Dateien geprüft. `git diff --check` und JavaScript-Syntaxprüfung ohne Befund. Browser-/Druck-Screenshots beziehen sich auf den Stand vor den beschränkten Text-/Schema-Korrekturen; kein erneuter Browser- oder Excel-Engine-Test der Schlussfassung behauptet.

## Schlussfassung: Identifikation

- HTML SHA-256: `140bbbe8780a8e1109b70be78060d45616c5af9aec9417388c229dec3f073470`
- Excel SHA-256: `827872bd26cc16904561c04d38fecf4a427907ad62bd8bfea2e23deec32b7ff8`

## Verbleibende Grenzen

Keine Rohdatenprüfung, kein neuer Baseline-/Sensitivitätslauf, keine Microsoft-Excel-/LibreOffice-Neuberechnung oder visuelle Excel-Prüfung. Offene Nenner-/Vertragsfragen und Bons-Erfassung bleiben sichtbar. Auslieferung als vertraulicher Reviewentwurf, nicht als fachlich bereits freigegebene Baseline oder öffentliche Veröffentlichung. Die abschliessende unabhängige Wiederholungsreview der drei korrigierten Stellen ist bestanden: keine Sicherheitsbedenken, Logikfehler oder weiteren Hinweise. Remote-Readback wird nach dem Push separat geprüft.

# tests/fixtures/ – KÜNSTLICHE TESTDATEN

**`synthetic_mini/` enthält ausschliesslich erfundene Daten. Keine FCSG-Clubdaten, keine Clubresultate.**

Erkennungsmerkmale: Spalte `data_origin = SYNTHETIC_FIXTURE_NOT_CLUB_DATA` in jeder Zeile; Spieldaten in
2099/2100; Saisons «FX1»/«FX2»; Gegner «Testgegner A–D/X»; Zuschauerzahlen um 100.

Erzeugt mit `python -m fcsg.cli make-fixture` (Quelle: `src/fcsg/fixtures.py`). Ein Test stellt sicher, dass
die eingecheckten CSVs exakt dem Generator entsprechen.

Absichtlich eingebaute Sonderfälle: fehlendes IST (2100-08-21), Spiel ohne Catering (2099-08-29),
Public Viewing am Spieltag 2100-08-07, Catering-Zeile ohne Heimspiel (2100-09-18), Zutritt nur Saison FX2.

# tests/

Ausführen: `.\.venv\Scripts\python.exe -m pytest -q` oder VS-Code-Task **FCSG: Tests ausführen**.

| Datei | Prüft |
|---|---|
| `test_fixtures_and_io.py` | Fixture = Generator, Marker, Schemafehler ohne Zellinhalte, Missing ≠ 0, Datenmodus-Sperre, Inventar |
| `test_joins.py` | 1 Zeile je Heimspiel, Public Viewing/Unmatched, Dubletten-Abbruch, Summenerhalt, Ankunftsanteile |
| `test_metrics.py` | KPIs gegen Handrechnung, NaN-Verhalten, gewichtete vs. ungewichtete Saison-KF |
| `test_inventory.py` | Strukturinventar: Kopfzeile, versteckte Tabs, Formeln, Encoding/Trennzeichen, Personenbezug; **kein Zellinhalt im Output** (Sentinel-Werte) |
| `test_exports.py` | Lauf → Excel → Readback; Readback erkennt manipulierte Werte, Formeln, fehlendes Banner; CLI |

Alle Tests nutzen nur `fixtures/synthetic_mini/` bzw. temporäre Ordner.

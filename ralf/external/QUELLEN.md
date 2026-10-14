# Öffentliche Zusatzdaten (Cache)

Erzeugt mit `python scripts/externe_daten_aktualisieren.py`. Es werden keine FCSG-Daten übertragen.

| Datei | Quelle | Inhalt | Hinweise |
|---|---|---|---|
| `meteoschweiz_stg_stuendlich.csv` | MeteoSchweiz, Open Government Data (SwissMetNet), Station St. Gallen (STG), Lizenz CC BY 4.0 – «Quelle: MeteoSchweiz» | Stundenwerte ab 01.07.2018: Temperatur 2 m (°C), Niederschlag (mm), Wind (km/h), Sonnenscheindauer (min), relative Feuchte (%) | `zeit_ende_utc` = Ende des Stundenintervalls in UTC (Wert 16:00 = 15:00–16:00 UTC). Umrechnung auf Europe/Zurich im Code. |
| `football_data_super_league.csv` | football-data.co.uk, Datei `SWZ.csv` | Super-League-Resultate ab 2017/18 (Datum, Anstoss, Heim, Gast, Tore) | Anstosszeit in UK-Zeit (CH-Zeit = UK-Zeit + 1 Stunde, ganzjährig). Dient für Tabellenstand/Form vor dem Spiel und als Gegenprobe zu Datum/Anpfiff. |

"""Lädt die öffentlichen Zusatzdaten neu und speichert sie kompakt im Ordner «external/».

* MeteoSchweiz, Station St. Gallen (STG), Stundenwerte (Open Government Data, Quelle: MeteoSchweiz)
* football-data.co.uk, Super League Resultate (für Tabellenstand und Form vor dem Spiel)

Es werden keine FCSG-Daten übertragen; abgefragt werden nur öffentliche Dateien.
Aufruf (im Ordner Python_Auswertung):  python scripts/externe_daten_aktualisieren.py
"""
from __future__ import annotations

import io
import sys
import urllib.request
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from fcsg import config  # noqa: E402

METEO_URLS = [
    "https://data.geo.admin.ch/ch.meteoschweiz.ogd-smn/stg/ogd-smn_stg_h_historical_2010-2019.csv",
    "https://data.geo.admin.ch/ch.meteoschweiz.ogd-smn/stg/ogd-smn_stg_h_historical_2020-2029.csv",
    "https://data.geo.admin.ch/ch.meteoschweiz.ogd-smn/stg/ogd-smn_stg_h_recent.csv",
]
METEO_PARAMETER = {"tre200h0": "temp_c", "rre150h0": "niederschlag_mm", "fu3010h0": "wind_kmh",
                   "sre000h0": "sonne_min", "ure200h0": "feuchte_pct"}
RESULTATE_URL = "https://www.football-data.co.uk/new/SWZ.csv"


def _download(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (HSG Projektarbeit)"})
    with urllib.request.urlopen(req, timeout=120) as resp:
        return resp.read()


def wetter() -> pd.DataFrame:
    teile = []
    for url in METEO_URLS:
        roh = pd.read_csv(io.BytesIO(_download(url)), sep=";", dtype=str, encoding="latin-1")
        teile.append(roh[["reference_timestamp", *METEO_PARAMETER]])
    df = pd.concat(teile, ignore_index=True).drop_duplicates("reference_timestamp", keep="last")
    df["zeit_ende_utc"] = pd.to_datetime(df["reference_timestamp"], format="%d.%m.%Y %H:%M")
    df = df[df["zeit_ende_utc"] >= "2018-07-01"].rename(columns=METEO_PARAMETER)
    for c in METEO_PARAMETER.values():
        df[c] = pd.to_numeric(df[c], errors="coerce")
    return df.sort_values("zeit_ende_utc")[["zeit_ende_utc", *METEO_PARAMETER.values()]]


def resultate() -> pd.DataFrame:
    roh = pd.read_csv(io.BytesIO(_download(RESULTATE_URL)), encoding="utf-8-sig", dtype=str)
    roh = roh[roh["League"] == "Super League"]
    df = pd.DataFrame({
        "saison": roh["Season"].str.replace(r"(\d{4})/\d{2}(\d{2})", r"\1/\2", regex=True),
        "datum": pd.to_datetime(roh["Date"], format="%d/%m/%Y"),
        "zeit_uk": roh["Time"], "heim": roh["Home"], "gast": roh["Away"],
        "tore_heim": pd.to_numeric(roh["HG"]), "tore_gast": pd.to_numeric(roh["AG"]),
    })
    return df[df["datum"] >= "2017-07-01"].sort_values(["datum", "zeit_uk"])


def main() -> None:
    config.EXTERNAL_DIR.mkdir(parents=True, exist_ok=True)
    w = wetter()
    w.to_csv(config.WETTER_FILE, index=False, encoding="utf-8")
    print(f"Wetter: {len(w):,} Stunden bis {w['zeit_ende_utc'].max()} -> {config.WETTER_FILE.name}")
    r = resultate()
    r.to_csv(config.RESULTATE_FILE, index=False, encoding="utf-8")
    print(f"Resultate: {len(r):,} Spiele bis {r['datum'].max():%d.%m.%Y} -> {config.RESULTATE_FILE.name}")


if __name__ == "__main__":
    main()

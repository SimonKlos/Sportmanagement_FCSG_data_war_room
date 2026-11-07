"""Spielrechner v2 (D-047) mit künstlichen, markierten Testdaten – keine Clubzahlen."""
import json
import math
import re
import shutil
import subprocess
import sys
from pathlib import Path

import pandas as pd
import pytest

KERN = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(KERN / "spielrechner"))

import build  # noqa: E402
import testdaten  # noqa: E402

WETTER = KERN / "external" / "meteoschweiz_stg_stuendlich.csv"


def _payload(html: str) -> dict:
    roh = re.search(r'<script id="daten-json" type="application/json">(.*?)</script>', html, re.S).group(1)
    return json.loads(roh.replace("<\\/", "</"))


@pytest.fixture()
def test_html(tmp_path):
    tab, mart, kontext = testdaten.erzeuge(tmp_path / "td")
    ziel = tmp_path / "Spielrechner_TEST.html"
    build.schreibe(build.daten(tab, mart, kontext, WETTER, testdaten=True), ziel)
    return ziel


def test_aufbau_und_kennzeichnung(test_html):
    html = test_html.read_text(encoding="utf-8")
    d = _payload(html)
    assert "__DATEN__" not in html
    assert d["meta"]["testdaten"] is True and d["meta"]["untertitel"].startswith("TESTDATEN")
    assert d["meta"]["basis_saison"] == "T3/T4"
    assert len(d["spiele"]) == 4 * 3 * 12                       # 4 Kennzahlen × 3 Saisons × 12 Spiele
    assert {s["code"] for s in d["slots"]} == {"referenz", "slot_sa_abend", "slot_nachmittag", "slot_werktag_abend"}
    assert d["ansetzungen"]["Samstag"] == {"referenz": 9, "slot_sa_abend": 9}
    k = d["modelle"]["kf_exkl"]["terme"]
    assert round(math.exp(k["Intercept"] + k["C(saison)[T.T3/T4]"] + k["temp_anpfiff_c"] * 12), 2) == 15.49
    # keine externen Skripte; einzige externe Ressource ist die Schrift
    assert not re.search(r"<script[^>]+src=", html)


def test_kalender_aus_kontexttabelle(test_html):
    d = _payload(test_html.read_text(encoding="utf-8"))
    assert d["ferien_stadt"] == [{"von": "2099-07-01", "bis": "2099-07-14", "name": "Testferien"},
                                 {"von": "2099-10-10", "bis": "2099-10-20", "name": "Testferien"}]
    assert d["ferien_stadt_bis"] == "2099-12-31"
    assert d["anlaesse"] == [{"datum": "2099-10-18", "name": "Testanlass", "gross": False}]


def test_klima_wie_rechenkern():
    """Normalwerte: Temperatur des Intervalls bis zur Stunde, Regen ≥ 0.5 mm in 2 bzw. 3 Intervallen (öffentliche MeteoSchweiz-Daten)."""
    kl = build.klima(WETTER)
    assert set(kl["temp"]) == {str(m) for m in range(1, 13)}
    jan, jul = kl["temp"]["1"]["18"], kl["temp"]["7"]["18"]
    assert -5 < jan < 5 and 15 < jul < 25
    for m in ("1", "7"):
        assert 0 <= kl["regen2"][m]["18"] <= kl["regen3"][m]["18"] <= 1     # 3 Intervalle ≥ 2 Intervalle
    # Gegenprobe direkt aus den Stundenwerten: Juli, Intervall endet 18 Uhr Lokalzeit
    w = pd.read_csv(WETTER, parse_dates=["zeit_ende_utc"])
    t = w["zeit_ende_utc"].dt.tz_localize("UTC").dt.tz_convert("Europe/Zurich")
    x = w[(t.dt.month == 7) & (t.dt.hour == 18)]
    assert abs(x["temp_c"].mean() - jul) < 0.01


def test_fehlender_vip_bleibt_leer(tmp_path):
    tab, mart, kontext = testdaten.erzeuge(tmp_path / "td")
    m = pd.read_csv(mart)
    m["ist_vip"] = None                                       # TESTDATEN: VIP nicht erfasst
    m.to_csv(mart, index=False)
    d = build.daten(tab, mart, kontext, WETTER, testdaten=True)
    assert all(v["ist_vip"] is None for v in d["saison_mittel"].values())


@pytest.mark.skipif(shutil.which("node") is None, reason="Node.js nicht installiert")
def test_rechenlogik_im_browsercode(test_html):
    """Die JavaScript-Rechenlogik der Seite gegen dieselbe Formel wie in Python (tests/spielrechner_logik.test.mjs)."""
    r = subprocess.run(["node", "--test", str(KERN / "tests" / "spielrechner_logik.test.mjs")], capture_output=True, text=True,
                       env={"SPIELRECHNER_HTML": str(test_html), "TZ": "Europe/Zurich", "PATH": "/usr/bin:/bin:/usr/local/bin:/opt/homebrew/bin"}, timeout=120)
    assert r.returncode == 0, r.stdout[-3000:] + r.stderr[-2000:]

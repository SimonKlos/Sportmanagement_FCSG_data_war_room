"""Spielrechner (D-047) mit künstlichen, markierten Testdaten – keine Clubzahlen."""
import json
import math
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "spielrechner"))

import build  # noqa: E402
import testdaten  # noqa: E402


def _payload(html: str) -> dict:
    roh = re.search(r'<script id="daten" type="application/json">(.*?)</script>', html, re.S).group(1)
    return json.loads(roh.replace("<\\/", "</"))


def test_spielrechner_testdaten(tmp_path):
    tab, mart = testdaten.erzeuge(tmp_path / "td")
    ziel = tmp_path / "Spielrechner_TEST.html"
    build.schreibe(build.daten(tab, mart, testdaten=True), ziel)
    html = ziel.read_text(encoding="utf-8")
    d = _payload(html)
    assert "__DATEN__" not in html
    assert d["meta"]["testdaten"] is True and d["meta"]["untertitel"].startswith("TESTDATEN")
    assert d["meta"]["basis_saison"] == "T3/T4"
    assert len(d["spiele"]) == 4 * 3 * 12                       # 4 Kennzahlen × 3 Saisons × 12 Spiele
    assert {s["code"] for s in d["slots"]} == {"referenz", "slot_sa_abend", "slot_nachmittag", "slot_werktag_abend"}
    # Vorhersage wie im Browser: Referenz-Slot, Basis T3/T4, 12 °C
    k = d["modelle"]["kf_exkl"]["terme"]
    kf = math.exp(k["Intercept"] + k["C(saison)[T.T3/T4]"] + k["temp_anpfiff_c"] * 12)
    assert round(kf, 2) == 15.49


def test_fehlender_vip_bleibt_leer(tmp_path):
    tab, mart = testdaten.erzeuge(tmp_path / "td")
    import pandas as pd
    m = pd.read_csv(mart)
    m["ist_vip"] = None                                       # TESTDATEN: VIP nicht erfasst
    m.to_csv(mart, index=False)
    d = build.daten(tab, mart, testdaten=True)
    assert all(v["ist_vip"] is None for v in d["saison_mittel"].values())

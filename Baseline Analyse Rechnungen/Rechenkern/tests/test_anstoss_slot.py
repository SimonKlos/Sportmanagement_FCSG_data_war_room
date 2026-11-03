"""Einheitentests Anstoss-Slot (Run 4) – künstliche, markierte Testwerte, keine Clubdaten."""
import numpy as np
import pandas as pd

from fcsg.analysis import anstoss_slot as a


def test_slot_zuordnung():
    assert a.slot("Samstag", "18:00") == a.REFERENZ_SLOT
    assert a.slot("Samstag", "19:59") == a.REFERENZ_SLOT
    assert a.slot("Samstag", "20:30") == a.SLOTS["slot_sa_abend"]
    assert a.slot("Sonntag", "16:30") == a.SLOTS["slot_nachmittag"]
    assert a.slot("Montag", "14:15") == a.SLOTS["slot_nachmittag"]       # Feiertag-Montag am Nachmittag
    assert a.slot("Mittwoch", "20:30") == a.SLOTS["slot_werktag_abend"]
    assert a.slot("Samstag", None) is None


def test_dummies_und_covid():
    # TESTDATEN (künstlich): drei Spiele, Covid nur beim ersten
    d = pd.DataFrame({"datum": pd.to_datetime(["2021-08-07", "2022-08-07", "2022-08-10"]),
                      "wochentag": ["Samstag", "Sonntag", "Mittwoch"], "anpfiff": ["18:00", "16:30", None]})
    k = pd.DataFrame({"datum": pd.to_datetime(["2021-08-07", "2022-08-07"]), "covid": [True, False]})
    x = a.ergaenze_slot(d, k)
    assert x["slot_nachmittag"].tolist()[:2] == [0.0, 1.0]
    assert np.isnan(x["slot_werktag_abend"].iloc[2])                      # fehlender Anpfiff bleibt fehlend
    assert x["covid"].iloc[0] == 1.0 and x["covid"].iloc[1] == 0.0 and np.isnan(x["covid"].iloc[2])

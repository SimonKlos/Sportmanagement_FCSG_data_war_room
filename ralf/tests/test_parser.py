"""Einheitentests der Parser (laufen ohne Rohdaten)."""
import numpy as np
import pandas as pd

from fcsg.analysis.models import _ruecktransform, _transform
from fcsg.datamodel import _konsens
from fcsg.sources.catering import _formel_ist_abzug, _operativ
from fcsg.sources.tickets import tarifgruppe, tribuene_gruppe
from fcsg.sources.zutritt import sektor_gruppe
from fcsg.utils import (form_punkte, gegner_kanonisch, parse_anpfiff, parse_chf, parse_datum, parse_rang,
                        saison_von)


def test_anpfiff_excel_zahlen_und_texte():
    assert parse_anpfiff(20.3) == "20:30"
    assert parse_anpfiff(14.15) == "14:15"
    assert parse_anpfiff(21) == "21:00"
    assert parse_anpfiff("16.30") == "16:30"
    assert parse_anpfiff("18.45 ") == "18:45"
    assert parse_anpfiff("14.15 Uhr") == "14:15"
    assert parse_anpfiff("13.00 - 17.00 Uhr") is None
    assert parse_anpfiff("ab 15.00 Uhr") is None


def test_datum_formate_und_mehrtaegige_events():
    assert parse_datum("Mittwoch, 27. September 2023") == pd.Timestamp("2023-09-27")
    assert parse_datum("Sonntag, 17, Mai 2026") == pd.Timestamp("2026-05-17")
    assert parse_datum("17.05.2026") == pd.Timestamp("2026-05-17")
    assert parse_datum("2025-07-26 00:00:00") == pd.Timestamp("2025-07-26")
    for mehrtaegig in ["15./16. August 2025", "29.05.-02.06.2023", "30. Mai - 2. Juni 2024",
                       "Freitag, 18.August und Samstag, 19. August"]:
        assert pd.isna(parse_datum(mehrtaegig))


def test_saison_und_betraege():
    assert saison_von("2025-07-26") == "2025/26"
    assert saison_von("2026-05-17") == "2025/26"
    assert parse_chf("1.303,00\xa0CHF") == 1303.0
    assert parse_chf("25,00 CHF") == 25.0
    assert np.isnan(parse_chf("-"))


def test_tabellenstand_und_form():
    assert parse_rang("7. Platz, 0 Pkt") == (7.0, 0.0)
    assert all(np.isnan(x) for x in parse_rang("– (noch keine SL-Runde gespielt)"))
    assert form_punkte("S-U-N-S") == (7.0, 4.0)


def test_gegner_kanonisch():
    assert gegner_kanonisch("BSL25/26: FCB") == "Basel"
    assert gegner_kanonisch("20251123_MS14_LS") == "Lausanne"
    assert gegner_kanonisch("FCSG vs. FC Lausanne Ouchy") == "Lausanne Ouchy"
    assert gegner_kanonisch("FC St.Gallen 1879 - Grasshopper Club Zürich") == "Grasshoppers"
    assert gegner_kanonisch("FCSG - FC Winterhtur") == "Winterthur"


def test_tarif_und_tribuene():
    assert tarifgruppe("A1 aussen / A6 (exkl. Familiensektor) Promo A1aussen/B/C/D Gratisticket", 0) == "Gratis/Promo"
    assert tarifgruppe("A Business V-ZUG Lounge Premium 0.- Ticket", 0) == "Hospitality"
    assert tarifgruppe("50% MA FCSG", 25) == "Mitarbeitende"
    assert tarifgruppe("D2/D3 Ausbildung", 17) == "Ermässigt"
    assert tarifgruppe("WEB Vollpreis", 25) == "Vollpreis"
    assert tribuene_gruppe("B4", None, "B | Osttribüne") == "B4 (Gäste)"
    assert tribuene_gruppe("A3 Business", None, "A | Mettler") == "Hospitality"
    assert tribuene_gruppe("Sektor D3", "D2/D3 Heimsektor Stehplatz") == "D"


def test_zutritt_sektor_aus_lesername():
    assert sektor_gruppe("A1.2 (62)") == "A"
    assert sektor_gruppe("B4.3") == "B4 (Gäste)"
    assert sektor_gruppe("HH-VIP1") == "HH (Hospitality)"


def test_catering_formeln_und_bemerkungen():
    assert _formel_ist_abzug("=16908-707") == (16908.0, 707.0)
    assert _formel_ist_abzug("=16462-(296+24)") == (16462.0, 320.0)
    ges = (r"geschlossen|geschossen|nicht alle stände geöffnet", r"gästesektor|geschlossenem|nach dem spiel|nach der pause")
    assert _operativ("Bier 2 geschlossen", *ges)
    assert not _operativ("Gästesektor geschlossen, Luzern Fans im B3", *ges)
    assert not _operativ("BBQ 2 > Plattform Sektor B inkl. Pause, nach dem Spiel geschlossen", *ges)


def test_anpfiff_konsens_mehrheit():
    wahl, quellen, abw = _konsens({"historie": "14:00", "catering": "16:30", "kontext": "16:30", "resultate": "16:30"})
    assert wahl == "16:30" and "historie: 14:00" in abw


def test_transformationen_umkehrbar():
    x = pd.Series([0.2, 0.5, 0.9])
    assert np.allclose(_ruecktransform(_transform(x, "logit"), "logit"), x)
    y = pd.Series([12.5, 15.0])
    assert np.allclose(_ruecktransform(_transform(y, "log"), "log"), y)

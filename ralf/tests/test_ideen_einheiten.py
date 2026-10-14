"""Einheitentests der Ideen-Grundlage und der Korrekturen v1.1.0 (laufen ohne Rohdaten)."""
from types import SimpleNamespace

import numpy as np
import pandas as pd
import pytest

from fcsg import config
from fcsg.ideen import absatz, basis, noshow
from fcsg.ideen.konsum import netto_anteil, normalsatz_anteil
from fcsg.ideen.qa_ideen import VERBOTENE_ZEILEN
from fcsg.report.methodennotiz import _tab
from fcsg.sources import catering
from fcsg.sources.catering import artikel_mwst_klasse, codiere_bemerkung


@pytest.mark.parametrize("datum, normal, reduziert", [("2023-12-31", 0.077, 0.025), ("2024-01-01", 0.081, 0.026)])
def test_mwst_proxy_rechnet_anteil_exakt_zurueck(datum, normal, reduziert):
    s = 0.55                                                     # Normalsatz-Anteil am Brutto-Umsatz
    netto_normal, netto_reduziert = s / (1 + normal), (1 - s) / (1 + reduziert)
    faktor = 1 / (netto_normal + netto_reduziert)                # Payfix inkl. / exkl.
    assert normalsatz_anteil(faktor, datum) == pytest.approx(s)
    assert netto_anteil(s, datum) == pytest.approx(netto_normal / (netto_normal + netto_reduziert))
    assert normalsatz_anteil(1 + normal, datum) == pytest.approx(1)
    assert normalsatz_anteil(1 + reduziert, datum) == pytest.approx(0)


def test_mwst_saetze_je_saison():
    assert catering._saetze_mwst("2022/23") == (config.MWST_ALT, config.MWST_REDUZIERT_ALT)
    assert catering._saetze_mwst("2023/24") is None              # Satzwechsel 1.1.2024 mitten in der Saison
    assert catering._saetze_mwst("2025/26") == (config.MWST_NEU, config.MWST_REDUZIERT_NEU)


def test_artikel_mwst_klasse_nach_name():
    for name in ["Bier 4dl.", "Klosterbräu 4dl.", "Wein 2dl", "Glühwein", "Hot Apple Cider", "Kafi Lutz"]:
        assert artikel_mwst_klasse(name) == "normal", name
    for name in ["alk.-freies Bier 4dl", "Punsch 2dl", "Mineral 4dl", "Bratwurst", "Kaffee / Espresso"]:
        assert artikel_mwst_klasse(name) == "reduziert", name
    assert artikel_mwst_klasse("Alkoholische Getränke", "Gruppe") == "normal"
    assert artikel_mwst_klasse("Food", "Gruppe") == "reduziert"


def test_artikel_einheitlich_brutto(monkeypatch):
    monkeypatch.setattr(catering, "lade_artikel_basis", lambda: {"2024/25": "brutto", "2025/26": "netto"})
    df = pd.DataFrame({"saison": ["2024/25", "2024/25", "2025/26", "2025/26", "2022/23"], "ebene": "Artikel",
                       "name": ["Bier 4dl.", "Bratwurst", "Bier 4dl.", "Bratwurst", "Bier 4dl."],
                       "umsatz_netto": [600.0, 700.0, 600 / 1.081, 700 / 1.026, 600.0], "menge": [100] * 5})
    h = catering._harmonisiere_artikel(df)
    assert np.allclose(h["umsatz_brutto"].iloc[:4], [600, 700, 600, 700])
    assert np.allclose(h["erloes_pro_einheit_brutto"].iloc[:4], [6, 7, 6, 7])
    assert np.isnan(h["umsatz_brutto"].iloc[4])                  # Basis nicht festgelegt → keine stille Umrechnung


def test_bemerkungen_mobiler_verkauf():
    def status(text):
        return codiere_bemerkung(text)["mobil_status"]

    assert status("Alle Stände geöffnet ausser Runner B, C, D") == "nicht im Einsatz"
    assert status("Alle Stände geöffnet inkl. Bauchläden im Sektor B, C, D") == "im Einsatz"
    assert status("Bierrucksäcke nur einer im Einsatz") == "eingeschränkt"
    assert status("folgende Stände waren geschlossen:\nBBQ S1, Bier S2, A3, Runner B und D") == "eingeschränkt"
    assert status("Runner C = Stand C4") == "keine Angabe"       # Kassenzuteilung, keine Einsatzangabe
    c = codiere_bemerkung("Alle Stände geöffnet ausser Runner B, C, D")
    assert c["mobiler_verkauf_reduziert"] and c["alle_staende_offen"] and not c["stand_geschlossen"]


def test_bemerkungen_staende_und_events():
    assert codiere_bemerkung("Alle Stände offen ausser Bier S2")["stand_geschlossen"]
    assert codiere_bemerkung("Allä Stände offen")["alle_staende_offen"]
    assert not codiere_bemerkung("Gästesektor geschlossen, Luzern Fans im B3")["stand_geschlossen"]
    assert not codiere_bemerkung("Side Event 1: BBQ S1")["event_plattform"]
    assert codiere_bemerkung("Winterzauber auf dem Kiesplatz")["event_plattform"]
    assert codiere_bemerkung(None)["mobil_status"] == "keine Angabe"


def test_abo_anwesenheit_zweitmarkt_nur_einmal_und_begrenzt():
    # 1000 Abos, 50 davon über den Zweitmarkt weiterverkauft; die übrigen 950 Inhaber kommen zu 80 %,
    # die 200 Einzeltickets (inkl. der 50 Zweitmarkt-Käufer) zu 90 %
    scans = 0.8 * 950 + 0.9 * 200
    assert noshow.abo_anwesenheit(scans, 200, 1000, 50, 0.9) == pytest.approx(0.8)
    assert noshow.abo_anwesenheit(scans, 200, 1000, 50, 0.95) < noshow.abo_anwesenheit(scans, 200, 1000, 50, 0.9)
    assert noshow.abo_anwesenheit(5000, 200, 1000, 50, 0.9) == 1
    assert noshow.abo_anwesenheit(0, 200, 1000, 50, 0.9) == 0


def test_zweitmarkt_am_tarifnamen_erkannt():
    m = SimpleNamespace(tickets=pd.DataFrame({
        "quelle": ["CSV"] * 4 + ["Export"],
        "tarif_roh": ["WEB Vollpreis", "Vollpreis Zweitmarkt", "ZWEITMARKT Ermässigt", None, "Zweitmarkt"]}))
    assert noshow._csv_tickets(m)["zweitmarkt"].tolist() == [False, True, True, False]


def test_hebel_szenario_formeln():
    b = {"soll_mittel": 20000.0, "kf_exkl": 15.0, "public_netto_mittel": 14000.0, "bon_exkl": 6.0,
         "umsatz_exkl_mittel": 210000.0, "bons_mittel": 35000.0, "spiele": 19}
    erwartet = {"noshow_pp": 200 * 15.0, "zusatz_anwesende": 1000 * 15.0, "bons_pro_anwesende": 1400 * 6.0,
                "frequenz_pct": 2100.0, "bon_chf": 35000.0, "kf_chf": 14000.0}
    assert set(erwartet) == set(basis.HEBEL)
    for hebel, chf_spiel in erwartet.items():
        h = basis.hebel_szenario(b, hebel)
        assert h["chf_pro_spiel"] == pytest.approx(chf_spiel), hebel
        assert h["chf_pro_saison"] == pytest.approx(chf_spiel * 19), hebel
    assert basis.hebel_szenario(b, "noshow_pp", phi=0.6)["chf_pro_spiel"] == pytest.approx(0.6 * 3000)
    assert basis.hebel_szenario(b, "kf_chf", phi=0.6)["chf_pro_spiel"] == pytest.approx(14000)   # φ nur für Anwesenheitshebel
    assert basis.hebel_szenario(b, "bon_chf", anteil_spiele=0.5)["chf_pro_saison"] == pytest.approx(35000 * 9.5)
    with pytest.raises(ValueError):
        basis.hebel_szenario(b, "gesamtpotenzial")


def test_potenzial_summen_werden_erkannt():
    for text in ["Gesamtpotenzial", "Total Potenzial", "Potenzial gesamt", "Summe Potential"]:
        assert VERBOTENE_ZEILEN.search(text), text
    for text in ["Potenzial je Spiel (isoliert)", "Referenzlücke", "Summe/Summe"]:
        assert not VERBOTENE_ZEILEN.search(text), text


def test_markdown_tabelle_ohne_spaltenbruch():
    df = pd.DataFrame({"a": ["x | y", "z\nw"], "b": [1.5, np.nan]})
    md = _tab(df, {"a": ("A", "text"), "b": ("B", "z2")})
    assert len({zeile.count("|") for zeile in md.splitlines()}) == 1


def test_bootstrap_reproduzierbar():
    rng = np.random.default_rng(0)
    x = np.vstack([rng.normal(0, 1, (20, 2)), rng.normal(4, 1, (20, 2))])
    a = absatz._ward_stabilitaet(x, 2, n_boot=50)
    b = absatz._ward_stabilitaet(x, 2, n_boot=50)
    assert np.array_equal(a[0], b[0]) and a[1:] == b[1:]

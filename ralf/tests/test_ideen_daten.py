"""Integrationstests der Ideen-Grundlage und der Korrekturen v1.1.0 auf den echten Daten (übersprungen ohne Datenordner)."""
import re
from html.parser import HTMLParser

import numpy as np
import pandas as pd
import pytest

from fcsg.ideen import chancen, noshow, qa_ideen
from fcsg.ideen.bericht import excel_rechner
from fcsg.qa import verbotene_spalten


@pytest.fixture(scope="module")
def ideen(phase1, tmp_path_factory):
    from fcsg.ideen import stufe
    r, m, res = phase1
    vorher = qa_ideen.fingerabdruck(res)
    ziel = tmp_path_factory.mktemp("ideen")
    out = stufe.erstelle(r, m, res, ziel, mit_grafiken=False, pdf=False)
    return {**out, "ziel": ziel, "fingerabdruck_vorher": vorher, "fingerabdruck_nachher": qa_ideen.fingerabdruck(res)}


def test_qualitaetspruefungen_bestanden(ideen):
    qa = ideen["qa"]
    assert qa["bestanden"].all(), qa.loc[~qa["bestanden"], ["test", "detail"]].to_string()


def test_phase1_bleibt_unveraendert(ideen):
    assert ideen["fingerabdruck_vorher"] == ideen["fingerabdruck_nachher"]


def test_rechengrundlage_2526(ideen):
    b = ideen["ergebnisse"]["basis_saison"].set_index("basis")
    assert round(b.loc["2025/26", "public_netto_summe"]) == 261924
    assert b.loc["2025/26", "spiele"] == 19


def test_keine_id_spalten(ideen):
    verboten = verbotene_spalten()
    for name, df in ideen["ergebnisse"].items():
        if isinstance(df, pd.DataFrame):
            assert not verboten & {str(c).lower() for c in df.columns}, name


def test_kleine_zellen_unterdrueckt(ideen):
    for tabelle, spalte in qa_ideen.KLEINZELLEN.items():
        assert (ideen["ergebnisse"][tabelle][spalte] >= 10).all(), tabelle


def test_artikel_mwst_klasse_passt_zum_erloesverhaeltnis(phase1):
    """Name-Regel = Klasse, die das Verhältnis Erlös je Einheit 25/26 (netto) zu 24/25 (brutto) zeigt (1/1.081 vs. 1/1.026)."""
    _, _, res = phase1
    art = res["artikel_alle"]
    art = art[art["ebene"] == "Artikel"]
    x = art.pivot_table(index=["name", "mwst_klasse"], columns="saison", values="umsatz_laut_datei", aggfunc="sum")
    q = art.pivot_table(index=["name", "mwst_klasse"], columns="saison", values="menge", aggfunc="sum")
    gross = (q["2024/25"] >= 200) & (q["2025/26"] >= 200)
    v = ((x["2025/26"] / q["2025/26"]) / (x["2024/25"] / q["2024/25"]))[gross].dropna()
    implizit = np.where((v - 1 / 1.081).abs() < (v - 1 / 1.026).abs(), "normal", "reduziert")
    assert len(v) >= 20
    assert (implizit == v.index.get_level_values("mwst_klasse")).all()


def test_brutto_netto_bruch_korrigiert(phase1):
    _, _, res = phase1
    art = res["artikel_alle"]
    bier = art[(art["ebene"] == "Artikel") & (art["name"] == "Bier 4dl.")].set_index("saison")
    bier = bier.loc[["2023/24", "2024/25", "2025/26"]]
    assert bier.loc["2025/26", "basis_datei"] == "netto"
    assert bier.loc["2025/26", "umsatz_laut_datei"] / bier.loc["2025/26", "menge"] < 5.6       # Datei: netto
    assert np.allclose(bier["erloes_pro_einheit_brutto"], 6.0, atol=0.06)                     # brutto: CHF 6.00 je Saison


def test_zweitmarkt_csv_gleich_historie(ideen):
    s = ideen["ergebnisse"]["zweitmarkt_saison"].set_index("saison")
    assert s["csv_gleich_historie"].all()
    assert int(s.loc["2025/26", "zweitmarkt"]) == 5716


def test_tribuenen_2627_kalibrierung_und_bandbreite(ideen):
    t = ideen["ergebnisse"]["tribuene_2627"].set_index("tribuene").loc[list(noshow.TRIBUENEN)]
    assert t["einzel_anwesenheit_uefa"].between(0.93, 1.02).all()
    unten, oben = t["abo_anwesenheit_bei_r_unten"], t["abo_anwesenheit_bei_r_oben"]
    assert unten.between(0, 1).all() and oben.between(0, 1).all()
    assert (unten >= oben).all()                                  # höheres r → tiefere Abo-Anwesenheit


def test_abo_bestand_nur_bis_anpfiff(ideen):
    j = ideen["ergebnisse"]["tribuene_2627_je_spiel"]
    for _, g in j[j["wettbewerb"] == "SL"].sort_values("datum").groupby("tribuene"):
        assert g["abos_bis_anpfiff"].is_monotonic_increasing
    assert (j.loc[j["wettbewerb"] == "UEFA", "abos_bis_anpfiff"] == 0).all()    # UEFA: Abos nicht gültig


def test_fruehindikator_ohne_blick_in_die_zukunft(ideen):
    v = ideen["ergebnisse"]["fruehindikator_vorhersagen"]
    assert len(v) and (v["training_bis"] < v["datum"]).all()
    f = ideen["ergebnisse"]["fruehindikator"]
    assert f["abdeckung_pi80"].dropna().between(0, 1).all()


def test_cluster_mit_stabilitaetsangabe(ideen):
    rb = ideen["ergebnisse"]["spieltypen_robustheit"]
    assert rb["min_bootstrap_jaccard"].between(0, 1).all()
    assert (rb["stabil"] == (rb["min_bootstrap_jaccard"] >= 0.75)).all()


def test_chancenfelder_mit_leitplanken_und_leitfragen(ideen):
    felder = ideen["chancenfelder"]
    assert len(felder) == 9
    for f in felder:
        assert all(str(f.leitplanken.get(k, "")).strip() for k in chancen.LEITPLANKEN_SCHLUESSEL), f.titel
        assert 2 <= len(f.leitfragen) <= 5 and f.pilot_messung.strip(), f.titel


def test_excel_formeln_gleich_python(ideen):
    f = excel_rechner.pruefe_formeln(ideen["ziel"] / "Ideen_Grundlage_FCSG.xlsx", ideen["ergebnisse"])
    assert len(f) == 6 and f["gleich"].all(), f.to_string()


def test_html_offline_und_parsebar(ideen):
    html = (ideen["ziel"] / "Ideen_Grundlage_FCSG.html").read_text(encoding="utf-8")

    class Quellen(HTMLParser):
        def __init__(self):
            super().__init__()
            self.urls = []

        def handle_starttag(self, tag, attrs):
            self.urls += [v for k, v in attrs if k in ("src", "href") and v]

    p = Quellen()
    p.feed(html)
    p.close()
    assert not [u for u in p.urls if re.match(r"(https?:)?//", u)]
    assert html.rstrip().endswith("</html>")


def test_markdown_tabellen_konsistent(ideen):
    md = (ideen["ziel"] / "Ideen_Grundlage_FCSG.md").read_text(encoding="utf-8")
    bloecke, block = [], []
    for zeile in md.splitlines() + [""]:
        if zeile.startswith("|"):
            block.append(zeile.count("|"))
        elif block:
            bloecke.append(block)
            block = []
    assert len(bloecke) >= 5 and all(len(set(b)) == 1 for b in bloecke)


def test_bootstrap_auf_daten_reproduzierbar(phase1):
    _, m, res = phase1
    pd.testing.assert_frame_equal(noshow.einzel_noshow_segmente(m, res, n_boot=200),
                                  noshow.einzel_noshow_segmente(m, res, n_boot=200))

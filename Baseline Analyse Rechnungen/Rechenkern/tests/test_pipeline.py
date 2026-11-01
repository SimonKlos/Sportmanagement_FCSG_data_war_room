"""Integrationstests auf den echten Daten (werden übersprungen, wenn der Datenordner fehlt)."""
import pandas as pd
import pytest


@pytest.fixture(scope="module")
def ergebnis(phase1):
    return phase1


def test_spielschluessel_eindeutig(ergebnis):
    _, m, _ = ergebnis
    assert m.dim_match["match_id"].is_unique
    gespielt = m.dim_match[m.dim_match["spielstatus"] == "gespielt"]
    assert not gespielt["datum"].duplicated().any()


def test_korrekturen_greifen(ergebnis):
    _, m, _ = ergebnis
    daten = set(m.dim_match["datum"])
    assert pd.Timestamp("2024-09-24") in daten and pd.Timestamp("2024-08-24") not in daten
    assert m.dim_match.set_index("datum").loc[pd.Timestamp("2026-05-17"), "anpfiff"] == "16:30"


def test_keine_personenfelder(ergebnis):
    _, m, _ = ergebnis
    verboten = {"kunde", "kundenname", "geburtstag", "postleitzahl", "kundennr", "barcode", "barcode_", "auftrag",
                "rechnung", "utid", "ticketnummer", "alter", "geschlecht-bez."}
    assert not verboten & {c.lower() for c in m.tickets.columns}


def test_jedes_kernspiel_hat_historie_und_catering(ergebnis):
    _, _, res = ergebnis
    k = res["spiel_kpi"]
    kern = k[k["spielstatus"] == "gespielt"]
    assert kern["ist"].notna().all() and kern["umsatz_inkl"].notna().all()


def test_reto_zahlen_reproduziert(ergebnis):
    _, _, res = ergebnis
    s = res["saison_kpi"]
    sl = s[s["wettbewerbe"] == "SL"].set_index("saison")
    assert round(sl.loc["2021/22", "kf_inkl"], 2) == 13.68
    assert round(sl.loc["2025/26", "kf_inkl"], 2) == 15.27
    alle = s[s["wettbewerbe"] == "SL+Cup+UEFA"].set_index("saison")
    assert round(alle.loc["2025/26", "kf_exkl"], 2) == 14.51
    reto = res["ankunft_reto"].iloc[0]
    assert 36 <= reto["median_min_vor_anpfiff_mittel"] <= 38.5
    korr = res["kf_korrelationen"].iloc[0]
    assert round(korr["r_kf_bon"], 2) == 0.87 and round(korr["r_kf_bons_pro_anwesende"], 2) == 0.75


def test_kf_identitaet(ergebnis):
    _, _, res = ergebnis
    k = res["spiel_kpi"].dropna(subset=["kf_exkl", "bons_pro_anwesende", "bon_exkl"])
    assert ((k["kf_exkl"] - k["bons_pro_anwesende"] * k["bon_exkl"]).abs() < 1e-9).all()


def test_kiesplatz_teilmenge_des_caterings(ergebnis):
    _, _, res = ergebnis
    dz = res["kiesplatz_doppelzaehlung"]
    x = dz[(dz["verkaufsstelle_kiesplatz"] != "BBQ1 Kiesplatz") & (dz["brutto_kiesplatz"] > 0)]
    assert x["identisch"].mean() >= 0.9


def test_modelle_vollstaendig(ergebnis):
    _, _, res = ergebnis
    mx = res["kontext_effekt_matrix"]
    assert mx["zielgroesse"].nunique() == 5
    assert mx["beurteilung"].isin(["belastbar", "Hinweis (Richtung stabil, Grösse unsicher)",
                                   "nicht belastbar schätzbar"]).all()

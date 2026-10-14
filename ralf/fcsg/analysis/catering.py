"""Paket C – Catering (Pflicht).

* Zerlegung KF = Bons je Public-Anwesendem × Ø Bon (nur Spiele mit Transaktionen, ab 2023/24)
* Zahlungswege, Artikelmix je Saison (deskriptiv, keine Artikelwerte pro Einzelspiel)
* Kiesplatz separat inkl. Doppelzählungsprüfung gegen die Standspalten 2021/22
* Elastizität Umsatz ~ Anwesende (Association, keine Kausalität; Retos 1.14 als vorläufige Schätzung)

Keine Konsumaussage je Ticket-Typ, kein Sektor-KF, keine Viertelstunden-Peaks (Daten fehlen).
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import statsmodels.formula.api as smf

from .. import config
from ..datamodel import Modell, Rohdaten
from ..log import befund

KIESPLATZ_ZU_STANDSPALTE = {
    "Getränke Contrailer": "contrailer getränke inkl. mwst.", "Pommes Contrailer": "contrailer pommes inkl. mwst.",
    "Fanshop Bar": "fanshop bar inkl. mwst.", "Bier S2": "bier 2 (zusatzwagen schüga) inkl. mwst.",
    "BBQ1 Kiesplatz": "contrailer bbq 1 inkl. mwst.",
}


def _kern_gespielt(k: pd.DataFrame) -> pd.DataFrame:
    return k[k["wettbewerb"].isin(config.KERN_WETTBEWERBE) & (k["spielstatus"] == "gespielt")]


def kf_zerlegung(k: pd.DataFrame) -> dict[str, pd.DataFrame]:
    d = _kern_gespielt(k).dropna(subset=["transaktionen", "public_netto", "umsatz_exkl"]).copy()
    d["ln_kf"] = np.log(d["kf_exkl"])
    d["ln_bons"] = np.log(d["bons_pro_anwesende"])
    d["ln_bon"] = np.log(d["bon_exkl"])
    rows = []
    for scope, x in [("SL ab 2023/24", d[d["wettbewerb"] == "SL"]), ("SL+Cup+UEFA ab 2023/24", d)]:
        for variante, y in [("Streuung über alle Spiele", x),
                            ("Streuung innerhalb der Saison", x.assign(**{
                                c: x[c] - x.groupby("saison")[c].transform("mean") for c in ["ln_kf", "ln_bons", "ln_bon"]}))]:
            v = y["ln_kf"].var()
            rows.append({"scope": scope, "variante": variante, "spiele": len(y),
                         "anteil_bons_pro_anwesende": y["ln_bons"].var() / v,
                         "anteil_bon": y["ln_bon"].var() / v,
                         "anteil_kovarianz": 2 * y[["ln_bons", "ln_bon"]].cov().iloc[0, 1] / v,
                         "korrelation_bons_bon": y[["ln_bons", "ln_bon"]].corr().iloc[0, 1]})
    zerlegung = pd.DataFrame(rows)

    korr = []
    reto = d[d["saison"].isin(["2025/26", "2026/27"])]
    for scope, x in [("Retos Stichprobe: alle Spiele 25/26 + 26/27 mit Catering (inkl. Cup/UEFA)", reto),
                     ("SL ab 2023/24", d[d["wettbewerb"] == "SL"])]:
        korr.append({"scope": scope, "spiele": len(x),
                     "r_kf_bon": x["kf_inkl"].corr(x["bon_inkl"]),
                     "r_kf_bons_pro_anwesende": x["kf_inkl"].corr(x["bons_pro_anwesende"]),
                     "bons_pro_anwesende_gewichtet": x["transaktionen"].sum() / x["public_netto"].sum(),
                     "bon_inkl_gewichtet": x["umsatz_inkl"].sum() / x["transaktionen"].sum(),
                     "hinweis": "KF = Bons/Anwesende × Ø Bon ist eine Identität: Korrelationen sind algebraisch "
                                "verknüpft und kein unabhängiger Kausalnachweis."})
    return {"kf_zerlegung": zerlegung, "kf_korrelationen": pd.DataFrame(korr),
            "kf_je_spiel": d[["match_id", "datum", "saison", "wettbewerb", "gegner_anzeige", "public_netto",
                              "transaktionen", "umsatz_exkl", "kf_exkl", "bons_pro_anwesende", "bon_exkl",
                              "ln_kf", "ln_bons", "ln_bon"]]}


def zahlungswege(m: Modell) -> pd.DataFrame:
    c = m.fact_catering_match[m.fact_catering_match["match_id"].notna()].copy()
    kanaele = {"Payfix (Kasse/Stand)": "kanal_payfix_inkl", "Just Eat (App)": "kanal_justeat_inkl",
               "Pick Up (App)": "kanal_pickup_inkl", "Gutscheine/nicht verbucht": "kanal_gutscheine_inkl",
               "Extern": "kanal_extern_inkl", "Stadion (bis 22/23)": "kanal_stadion_inkl",
               "Contrailer (21/22)": "kanal_contrailer_inkl"}
    rows = []
    for s, g in c.groupby("saison"):
        total = g["umsatz_inkl"].sum()
        for name, col in kanaele.items():
            if col in g and g[col].sum() > 0:
                rows.append({"saison": s, "zahlungsweg": name, "umsatz_inkl": g[col].sum(), "anteil": g[col].sum() / total,
                             "spiele": int((g[col] > 0).sum())})
    return pd.DataFrame(rows)


def artikelmix(r: Rohdaten, m: Modell, k: pd.DataFrame) -> dict[str, pd.DataFrame]:
    """Sortimentsmix auf einheitlicher Brutto-Basis (die Datei liefert 23/24–24/25 brutto, 25/26 netto)."""
    a = r.artikel.rename(columns={"umsatz_netto": "umsatz_laut_datei",
                                  "umsatz_netto_pro_spiel_blatt": "umsatz_pro_spiel_laut_datei"})
    gruppen = a[a["ebene"] == "Gruppe"].copy()
    gruppen["anteil"] = gruppen["umsatz_brutto"] / gruppen.groupby("saison")["umsatz_brutto"].transform("sum")
    art = a[a["ebene"] == "Artikel"].copy()
    art["anteil"] = art["umsatz_brutto"] / art.groupby("saison")["umsatz_brutto"].transform("sum")
    art["menge_pro_spiel"] = art["menge"] / art["spiele"]
    art = art.sort_values(["name", "saison"])
    art["erloes_pro_einheit_veraenderung"] = art.groupby("name")["erloes_pro_einheit_brutto"].pct_change(fill_method=None)
    top = art[art.groupby("saison")["umsatz_brutto"].rank(ascending=False) <= 15].sort_values(
        ["saison", "umsatz_brutto"], ascending=[True, False])

    # Abgleich: Artikelsumme (brutto) vs. Payfix inkl. und Catering-Umsatz inkl. (Meisterschaft); Normalsatz-Artikel vs.
    # Gruppe «Alkoholische Getränke» (prüft die MwSt-Klassen der Artikel)
    c = m.fact_catering_match
    c = c[(c["wettbewerb"] == "SL") & c["match_id"].isin(k.loc[k["spielstatus"] == "gespielt", "match_id"])]
    sl = c.groupby("saison").agg(spiele_catering=("match_id", "size"), payfix_inkl_catering=("kanal_payfix_inkl", "sum"),
                                 umsatz_inkl_catering=("umsatz_inkl", "sum"), umsatz_exkl_catering=("umsatz_exkl", "sum"))
    abgl = gruppen.groupby("saison").agg(spiele_artikel=("spiele", "first"), basis_datei=("basis_datei", "first"),
                                         umsatz_artikel_laut_datei=("umsatz_laut_datei", "sum"),
                                         umsatz_artikel_brutto=("umsatz_brutto", "sum"))
    alk_gruppe = gruppen[gruppen["mwst_klasse"] == "normal"].groupby("saison")["umsatz_laut_datei"].sum()
    alk_artikel = art[art["mwst_klasse"] == "normal"].groupby("saison")["umsatz_laut_datei"].sum()
    abgl = abgl.join(sl, how="left").reset_index()
    abgl["verhaeltnis_artikel_brutto_zu_payfix_inkl"] = abgl["umsatz_artikel_brutto"] / abgl["payfix_inkl_catering"]
    abgl["verhaeltnis_artikel_brutto_zu_catering_inkl"] = abgl["umsatz_artikel_brutto"] / abgl["umsatz_inkl_catering"]
    abgl["verhaeltnis_datei_zu_payfix_inkl"] = abgl["umsatz_artikel_laut_datei"] / abgl["payfix_inkl_catering"]
    abgl["verhaeltnis_alkohol_artikel_zu_gruppe"] = abgl["saison"].map(alk_artikel / alk_gruppe)
    return {"artikel_gruppen": gruppen, "artikel_top15": top, "artikel_abgleich": abgl, "artikel_alle": art}


def kiesplatz(r: Rohdaten, m: Modell, k: pd.DataFrame) -> dict[str, pd.DataFrame]:
    kp = m.fact_kiesplatz
    tot = kp[kp["ist_total"]]
    je_spiel = tot[tot["match_id"].notna()][["match_id", "datum", "saison", "event", "beginn_pause", "brutto_total",
                                             "netto_total"]].merge(
        k[["match_id", "wettbewerb", "umsatz_inkl", "public_netto", "anpfiff"]], on="match_id", how="left")
    je_spiel["anteil_am_catering_total"] = je_spiel["brutto_total"] / je_spiel["umsatz_inkl"]
    je_spiel["kiesplatz_chf_pro_anwesende"] = je_spiel["brutto_total"] / je_spiel["public_netto"]
    staende = kp[~kp["ist_total"] & kp["match_id"].notna()].groupby(["saison", "verkaufsstelle"]).agg(
        events=("match_id", "nunique"), brutto=("brutto_total", "sum")).reset_index()

    # Doppelzählungsprüfung 2021/22: Kiesplatz-Stände vs. Standspalten im Catering-Blatt
    st = r.catering_staende_2122
    st = st[st["stand_spalte"].str.contains("inkl")]
    piv = st.pivot_table(index="datum", columns="stand_spalte", values="wert", aggfunc="sum")
    rows = []
    for _, x in kp[(kp["saison"] == "2021/22") & ~kp["ist_total"]].iterrows():
        spalte = KIESPLATZ_ZU_STANDSPALTE.get(x["verkaufsstelle"])
        if spalte is None or x["datum"] not in piv.index or spalte not in piv.columns:
            continue
        wert_cat = piv.loc[x["datum"], spalte]
        rows.append({"datum": x["datum"], "event": x["event"], "verkaufsstelle_kiesplatz": x["verkaufsstelle"],
                     "brutto_kiesplatz": x["brutto_total"], "standspalte_catering": spalte, "wert_catering": wert_cat,
                     "identisch": bool(abs(x["brutto_total"] - wert_cat) < 1)})
    dz = pd.DataFrame(rows)
    if not dz.empty:
        ohne_bbq = dz[dz["verkaufsstelle_kiesplatz"] != "BBQ1 Kiesplatz"]
        quote = ohne_bbq.loc[ohne_bbq["brutto_kiesplatz"] > 0, "identisch"].mean()
        befund("Kiesplatz", "hoch", "Abrechnung Kiesplatz 21/22 vs. Catering-Blatt 2021-2022",
               f"Getränke-/Pommes-Contrailer, Fanshop Bar und Bier S2 stimmen je Spiel zu {quote:.0%} frankengenau mit den "
               "Standspalten der Public-Catering-Datei überein; BBQ1 Kiesplatz ist ein Teil von «Contrailer BBQ 1».",
               "Kiesplatz-Umsätze sind im Public-Catering-Total enthalten. Addieren wäre eine Doppelzählung.",
               "Kiesplatz nur als Anteil/Teilmenge ausgewiesen, nie zum Catering addiert. Für spätere Saisons beim Caterer bestätigen.")
    return {"kiesplatz_je_spiel": je_spiel, "kiesplatz_staende": staende, "kiesplatz_doppelzaehlung": dz}


def elastizitaet(k: pd.DataFrame, ctx: pd.DataFrame) -> pd.DataFrame:
    d = k[(k["wettbewerb"] == "SL") & (k["spielstatus"] == "gespielt")].dropna(subset=["umsatz_exkl", "public_netto"]).copy()
    d = d.merge(ctx[["match_id", "temp_anpfiff_c"]], on="match_id", how="left")
    d["ln_umsatz"] = np.log(d["umsatz_exkl"])
    d["ln_anwesende"] = np.log(d["public_netto"])
    rows = []
    varianten = [
        ("Retos Stichprobe (SL 25/26 + 26/27)", d[d["saison"] >= "2025/26"], "ln_umsatz ~ ln_anwesende + C(saison)"),
        ("SL 21/22–26/27 mit Saison-Effekten", d, "ln_umsatz ~ ln_anwesende + C(saison)"),
        ("SL 22/23–26/27 + Kontext (Top-Gegner, Abend, Temperatur)", d[d["saison"] >= config.MODELL_AB_SAISON],
         "ln_umsatz ~ ln_anwesende + C(saison) + top_gegner + abendspiel + temp_anpfiff_c"),
    ]
    for name, x, formel in varianten:
        x = x.dropna(subset=["temp_anpfiff_c"]) if "temp" in formel else x
        fit = smf.ols(formel, data=x.assign(top_gegner=x["top_gegner"].astype(float),
                                            abendspiel=x["abendspiel"].astype(float))).fit(cov_type="HC3")
        b, se = fit.params["ln_anwesende"], fit.bse["ln_anwesende"]
        rows.append({"variante": name, "spiele": int(fit.nobs), "elastizitaet": b, "ki95_unten": b - 1.96 * se,
                     "ki95_oben": b + 1.96 * se, "p_wert_gegen_1": 2 * (1 - _phi(abs((b - 1) / se))),
                     "interpretation": "Umsatz wächst proportional (≈1), über- (>1) oder unterproportional (<1) mit den "
                                       "Public-Anwesenden; Zusammenhang, keine Kausalität (Gegner/Wetter wirken auf beides)."})
    return pd.DataFrame(rows)


def _phi(z: float) -> float:
    from math import erf, sqrt
    return 0.5 * (1 + erf(z / sqrt(2)))


def operative_hinweise(m: Modell) -> pd.DataFrame:
    c = m.fact_catering_match[m.fact_catering_match["match_id"].notna()]
    flags = ["stand_geschlossen", "mobiler_verkauf_reduziert", "personalmangel", "technische_probleme",
             "operativer_hinweis", "aktion_gratis_gutschein", "event_plattform", "alle_staende_offen"]
    out = c.groupby("saison")[flags].sum().reset_index()
    out["spiele"] = c.groupby("saison").size().values
    return out


def catering(r: Rohdaten, m: Modell, k: pd.DataFrame) -> dict[str, pd.DataFrame]:
    out = kf_zerlegung(k)
    out["zahlungswege"] = zahlungswege(m)
    out.update(artikelmix(r, m, k))
    out.update(kiesplatz(r, m, k))
    out["elastizitaet"] = elastizitaet(k, m.dim_match_context)
    out["operative_hinweise"] = operative_hinweise(m)
    return out

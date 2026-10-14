"""Konsum: Woher kommt der Kundenfranken, was kauft der Durchschnittsfan, was steckt im Alkohol-Anteil je Spiel?

* KF-Entwicklung zerlegt in Kauffrequenz (Bons je Anwesendem) und Warenkorb (Ø Bon).
* Artikel (Saisonsummen, einheitliche Brutto-Basis): Warenkorb je 100 Anwesende und Fisher-Zerlegung «Erlös je
  Einheit × Einheiten je Anwesendem».
* Normalsatz-Anteil je Spiel aus dem MwSt-Mix des Kassenkanals Payfix = Näherung für den Alkoholanteil (alkoholische
  Getränke: Normalsatz; Speisen und alkoholfreie Getränke als Take-away: reduzierter Satz). Validiert gegen die
  Artikelauswertung (Saisonebene) und den Kiesplatz (Spielebene). Interpretation innerhalb der Saison.
* Durchsatz-Knick, mobiler Verkauf, Zahlungswege, Kiesplatz und Wetter, φ-Evidenz.
Alles Zusammenhänge auf Spielebene – keine Kausalität, keine Personenaussage.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import statsmodels.formula.api as smf

from .. import config
from . import modell

SEED = 1879


def _saetze(datum) -> tuple[float, float]:
    if pd.Timestamp(datum) >= pd.Timestamp(config.MWST_WECHSEL):
        return config.MWST_NEU, config.MWST_REDUZIERT_NEU
    return config.MWST_ALT, config.MWST_REDUZIERT_ALT


def normalsatz_anteil(faktor: float, datum) -> float:
    """Anteil des Normalsatz-Umsatzes am Brutto-Umsatz aus dem Faktor inkl./exkl. (zwei Sätze)."""
    h, t = _saetze(datum)
    return (1 / (1 + t) - 1 / faktor) / (1 / (1 + t) - 1 / (1 + h))


def netto_anteil(s_brutto: float, datum) -> float:
    """Normalsatz-Anteil am Netto-Umsatz (Basis des KF exkl. MwSt)."""
    h, t = _saetze(datum)
    a, b = s_brutto / (1 + h), (1 - s_brutto) / (1 + t)
    return a / (a + b)


# --------------------------------------------------------------------------------------------
# KF-Entwicklung
# --------------------------------------------------------------------------------------------
def kf_entwicklung(basis: pd.DataFrame) -> pd.DataFrame:
    b = basis[basis["basis"].str.match(r"^\d{4}/\d{2}$")].sort_values("basis").copy()
    b = b[b["bons_pro_anwesende"].notna()]
    rows, vorher = [], None
    for _, r_ in b.iterrows():
        row = {"saison": r_["basis"], "spiele": r_["spiele"], "kf_exkl": r_["kf_exkl"], "bons_pro_anwesende": r_["bons_pro_anwesende"],
               "bon_exkl": r_["bon_exkl"]}
        if vorher is not None:
            d_kf = np.log(r_["kf_exkl"] / vorher["kf_exkl"])
            d_freq = np.log(r_["bons_pro_anwesende"] / vorher["bons_pro_anwesende"])
            d_bon = np.log(r_["bon_exkl"] / vorher["bon_exkl"])
            row.update({"veraenderung_kf_pct": (np.exp(d_kf) - 1) * 100,
                        "veraenderung_frequenz_pct": (np.exp(d_freq) - 1) * 100, "veraenderung_bon_pct": (np.exp(d_bon) - 1) * 100})
        rows.append(row)
        vorher = r_
    out = pd.DataFrame(rows)
    erst, letzt = b.iloc[0], b[b["basis"] == "2025/26"].iloc[0] if (b["basis"] == "2025/26").any() else b.iloc[-1]
    d_kf = np.log(letzt["kf_exkl"] / erst["kf_exkl"])
    zeile = {"saison": f"{erst['basis']} → {letzt['basis']}", "kf_exkl": letzt["kf_exkl"],
             "veraenderung_kf_pct": (np.exp(d_kf) - 1) * 100,
             "veraenderung_frequenz_pct": (letzt["bons_pro_anwesende"] / erst["bons_pro_anwesende"] - 1) * 100,
             "veraenderung_bon_pct": (letzt["bon_exkl"] / erst["bon_exkl"] - 1) * 100}
    out = pd.concat([out, pd.DataFrame([zeile])], ignore_index=True)
    out["lesart"] = ("(1 + Δ KF) = (1 + Δ Kauffrequenz) × (1 + Δ Ø Bon); Meisterschaft, exkl. MwSt. Steigen Frequenz und sinkt der Bon "
                     "gleichzeitig, kaufen Fans öfter, aber kleinere Warenkörbe.")
    return out


# --------------------------------------------------------------------------------------------
# Artikel: Warenkorb und Preis-/Mengen-Zerlegung
# --------------------------------------------------------------------------------------------
def _art(res: dict) -> pd.DataFrame:
    return res["artikel_alle"].copy()


def warenkorb(res: dict, basis: pd.DataFrame) -> dict[str, pd.DataFrame]:
    a = _art(res)
    b = basis.set_index("basis")
    a["public_netto"] = a["saison"].map(b["public_netto_summe"])
    a["bons"] = a["saison"].map(b["bons_summe"])
    a["einheiten_je_100_anwesende"] = a["menge"] / a["public_netto"] * 100
    a["umsatz_brutto_je_anwesenden"] = a["umsatz_brutto"] / a["public_netto"]
    top = a[a.groupby("saison")["umsatz_brutto"].rank(ascending=False) <= 15]
    korb = top.pivot_table(index=["name", "mwst_klasse"], columns="saison", values="einheiten_je_100_anwesende").reset_index()
    korb["sortierung"] = korb.filter(regex=r"^\d{4}/").mean(axis=1)
    korb = korb.sort_values("sortierung", ascending=False).drop(columns="sortierung")
    g = res["artikel_gruppen"].copy()
    g["public_netto"] = g["saison"].map(b["public_netto_summe"])
    g["einheiten_je_100_anwesende"] = g["menge"] / g["public_netto"] * 100
    g["umsatz_brutto_je_anwesenden"] = g["umsatz_brutto"] / g["public_netto"]
    je_bon = a.groupby("saison").agg(einheiten=("menge", "sum"), bons=("bons", "first"), public_netto=("public_netto", "first")).reset_index()
    je_bon["einheiten_je_bon"] = je_bon["einheiten"] / je_bon["bons"]
    je_bon["einheiten_je_anwesenden"] = je_bon["einheiten"] / je_bon["public_netto"]
    hinweis = ("Artikel decken den Kassenkanal Payfix ab (≈ 96 % des Umsatzes); je Anwesendem daher leicht unterschätzt. "
               "Einheiten je 100 Public-Anwesende (Meisterschaft, Saisonsummen).")
    for df in (korb, g, je_bon):
        df["hinweis"] = hinweis
    return {"warenkorb_artikel": korb, "warenkorb_gruppen": g[["saison", "name", "mwst_klasse", "menge", "umsatz_brutto", "anteil",
                                                                "einheiten_je_100_anwesende", "umsatz_brutto_je_anwesenden", "hinweis"]],
            "warenkorb_je_bon": je_bon}


def preis_menge(res: dict, basis: pd.DataFrame) -> pd.DataFrame:
    """Fisher-Zerlegung des Artikel-Umsatzes je Anwesendem (brutto) in Erlös je Einheit und Einheiten je Anwesendem."""
    a = _art(res)
    pn = basis.set_index("basis")["public_netto_summe"]
    a = a[a["menge"] > 0]
    saisons = sorted(a["saison"].unique())
    paare = list(zip(saisons, saisons[1:])) + ([(saisons[0], saisons[-1])] if len(saisons) > 2 else [])
    rows = []
    for s0, s1 in paare:
        x0 = a[a["saison"] == s0].set_index("name")
        x1 = a[a["saison"] == s1].set_index("name")
        gem = x0.index.intersection(x1.index)
        p0, p1 = x0.loc[gem, "erloes_pro_einheit_brutto"], x1.loc[gem, "erloes_pro_einheit_brutto"]
        q0, q1 = x0.loc[gem, "menge"] / pn[s0], x1.loc[gem, "menge"] / pn[s1]
        v0, v1 = (p0 * q0).sum(), (p1 * q1).sum()
        laspeyres = (p1 * q0).sum() / v0
        paasche = (p1 * q1).sum() / (p0 * q1).sum()
        fisher_p = np.sqrt(laspeyres * paasche)
        fisher_q = (v1 / v0) / fisher_p
        gesamt0 = x0["umsatz_brutto"].sum() / pn[s0]
        gesamt1 = x1["umsatz_brutto"].sum() / pn[s1]
        rows.append({"von": s0, "bis": s1, "artikel_gemeinsam": len(gem),
                     "umsatz_brutto_je_anwesenden_von": gesamt0, "umsatz_brutto_je_anwesenden_bis": gesamt1,
                     "veraenderung_gesamt_pct": (gesamt1 / gesamt0 - 1) * 100,
                     "preisindex_fisher_pct": (fisher_p - 1) * 100, "preisindex_laspeyres_pct": (laspeyres - 1) * 100,
                     "preisindex_paasche_pct": (paasche - 1) * 100, "mengenindex_fisher_pct": (fisher_q - 1) * 100,
                     "sortimentswechsel_pct": ((gesamt1 / gesamt0) / (v1 / v0) - 1) * 100,
                     "identitaet_pruefung": float(fisher_p * fisher_q - v1 / v0)})
    out = pd.DataFrame(rows)
    out["lesart"] = ("Preisindex = Veränderung des Erlöses je Einheit (brutto, inkl. Rabatte/Gutscheine) bei festem Korb; "
                     "Mengenindex = Veränderung der Einheiten je Anwesendem; Sortimentswechsel = neue/weggefallene Artikel. "
                     "Laspeyres/Paasche zeigen die Spannweite. Buchhaltung, keine Schätzung (kein Konfidenzintervall).")
    return out


# --------------------------------------------------------------------------------------------
# Alkohol-Proxy je Spiel (MwSt-Mix Payfix)
# --------------------------------------------------------------------------------------------
def alkohol_proxy(m, res: dict) -> dict[str, pd.DataFrame]:
    c = m.fact_catering_match.dropna(subset=["match_id"])
    c = c[c["wettbewerb"].isin(config.KERN_WETTBEWERBE) & c["kanal_payfix_inkl"].gt(0) & c["kanal_payfix_exkl"].gt(0)].copy()
    c["faktor_payfix"] = c["kanal_payfix_inkl"] / c["kanal_payfix_exkl"]
    c["s_brutto"] = [normalsatz_anteil(f, d) for f, d in zip(c["faktor_payfix"], c["datum"])]
    c["s_netto"] = [netto_anteil(s, d) for s, d in zip(c["s_brutto"], c["datum"])]
    flach = [abs(f - (1 + _saetze(d)[0])) < 2e-4 or abs(f - (1 + _saetze(d)[1])) < 2e-4 for f, d in zip(c["faktor_payfix"], c["datum"])]
    c["ausschluss"] = np.select(
        [np.array(flach), ~c["s_brutto"].between(0.3, 0.7), c["merch_verkauf"].fillna(False).astype(bool)],
        ["Netto pauschal gerechnet", "Anteil ausserhalb 0.3–0.7", "Fanartikel über Catering-Kassen"], default="")
    # gültig ab 2023/24 (Payfix ≈ 96 % des Umsatzes); Spiele mit Fanartikel-Verkauf über die Catering-Kassen ausgeschlossen
    c["proxy_gueltig"] = (c["ausschluss"] == "") & (c["saison"] >= "2023/24")
    k = res["spiel_kpi"][["match_id", "public_netto", "umsatz_exkl", "kf_exkl", "kf_inkl", "gegner_anzeige"]]
    c = c.merge(k, on="match_id", how="left", suffixes=("", "_kpi"))
    c["kf_alkohol_exkl"] = c["kf_exkl"] * c["s_netto"]
    c["kf_uebrige_exkl"] = c["kf_exkl"] * (1 - c["s_netto"])
    je_spiel = c[["match_id", "datum", "saison", "wettbewerb", "gegner_anzeige", "faktor_payfix", "s_brutto", "s_netto",
                  "kf_exkl", "kf_alkohol_exkl", "kf_uebrige_exkl", "proxy_gueltig", "ausschluss"]].sort_values("datum")

    # Validierung 1: Saisonmittel (Payfix-gewichtet) vs. Alkoholanteil der Artikelauswertung (brutto, Meisterschaft)
    g = c[c["proxy_gueltig"] & (c["wettbewerb"] == "SL")]
    sais = g.groupby("saison").apply(lambda x: pd.Series({
        "spiele": len(x), "proxy_s_brutto": np.average(x["s_brutto"], weights=x["kanal_payfix_inkl"]),
        "proxy_streuung_sd": x["s_brutto"].std()}), include_groups=False).reset_index()
    art = res["artikel_gruppen"]
    alk = art[art["mwst_klasse"] == "normal"].set_index("saison")["anteil"]
    sais["artikel_alkoholanteil_brutto"] = sais["saison"].map(alk)
    sais["differenz_pp"] = (sais["proxy_s_brutto"] - sais["artikel_alkoholanteil_brutto"]) * 100
    # Validierung 2: innerhalb der Saison mit dem Normalsatz-Anteil des Kiesplatzes (gleiche Logik, eigene Abrechnung)
    kp = m.fact_kiesplatz[m.fact_kiesplatz["ist_total"] & m.fact_kiesplatz["match_id"].notna()].copy()
    kp = kp[(kp["brutto_total"] > 0) & kp["brutto_normal"].notna() & kp["brutto_reduziert"].notna()]
    kp["kies_normal_anteil"] = kp["brutto_normal"] / kp["brutto_total"]
    v2 = g.merge(kp[["match_id", "kies_normal_anteil"]], on="match_id")
    v2 = v2.assign(a=v2["s_brutto"] - v2.groupby("saison")["s_brutto"].transform("mean"),
                   b=v2["kies_normal_anteil"] - v2.groupby("saison")["kies_normal_anteil"].transform("mean"))
    validierung = sais.copy()
    validierung["r_innerhalb_saison_mit_kiesplatz"] = float(v2["a"].corr(v2["b"])) if len(v2) > 10 else np.nan
    validierung["spiele_mit_kiesplatz"] = len(v2)
    validierung["lesart"] = ("Gültig, wenn Saisonmittel ±2 Pp. zur Artikelauswertung und Spielwerte innerhalb der Saison mit dem "
                             "Kiesplatz-Normalsatzanteil korrelieren. Empfindlich: 0.001 Fehler im Faktor ≈ 1.8 Pp. Anteil – "
                             "daher Abweichungen innerhalb der Saison deuten, keine Niveaus über Saisons.")
    return {"alkohol_je_spiel": je_spiel, "alkohol_validierung": validierung}


def alkohol_modelle(alk: pd.DataFrame, d: pd.DataFrame) -> dict[str, pd.DataFrame]:
    x = d.merge(alk.loc[alk["proxy_gueltig"], ["match_id", "s_brutto", "kf_alkohol_exkl", "kf_uebrige_exkl"]], on="match_id", how="inner")
    teile = [modell.kontextmodell(x, "s_brutto", "logit", "Alkoholanteil am Umsatz (Normalsatz-Proxy)"),
             modell.kontextmodell(x, "kf_alkohol_exkl", "log", "KF Alkohol (exkl. MwSt)"),
             modell.kontextmodell(x, "kf_uebrige_exkl", "log", "KF Food & alkoholfrei (exkl. MwSt)")]
    mx = pd.concat([t["matrix"] for t in teile], ignore_index=True)
    mx["hinweis"] = ("KF Alkohol und KF übrige teilen sich denselben Proxy (Messfehler gegenläufig) – Unterschiede nur über den "
                     "Alkoholanteil selbst beurteilen. Saisons 2023/24–2026/27.")
    return {"alkohol_effekt_matrix": mx, "alkohol_modellguete": pd.concat([t["guete"] for t in teile], ignore_index=True)}


# --------------------------------------------------------------------------------------------
# Durchsatz-Knick
# --------------------------------------------------------------------------------------------
def durchsatz_knick(d: pd.DataFrame, n_boot: int = 999) -> pd.DataFrame:
    x = d[d["hauptstichprobe"] & d["transaktionen"].notna() & d["temp_anpfiff_c"].notna()].copy()
    x["log_bons"] = np.log(x["transaktionen"])
    x["log_umsatz"] = np.log(x["umsatz_exkl"])
    x["log_anw"] = np.log(x["public_netto"])
    rng = np.random.default_rng(SEED)
    rows = []
    for ziel, label in (("log_bons", "Bons (Anzahl Transaktionen)"), ("log_umsatz", "Umsatz exkl. MwSt")):
        for q in (0.60, 0.75, 0.90):
            c = float(np.quantile(x["log_anw"], q))
            x["knick"] = np.clip(x["log_anw"] - c, 0, None)
            formel = f"{ziel} ~ log_anw + knick + C(saison) + top_gegner + werktag + abendspiel + temp_anpfiff_c"
            fit = smf.ols(formel, data=x).fit(cov_type="HC3")
            # Wild-Bootstrap (Rademacher) unter H0: kein Knick
            f0 = smf.ols(formel.replace(" + knick", ""), data=x).fit()
            boot = []
            for _ in range(n_boot):
                yb = f0.fittedvalues + f0.resid * rng.choice([-1.0, 1.0], len(x))
                fb = smf.ols(formel.replace(ziel, "yb"), data=x.assign(yb=yb)).fit()
                boot.append(fb.params["knick"])
            p_boot = (np.sum(np.abs(boot) >= abs(fit.params["knick"])) + 1) / (n_boot + 1)
            rows.append({"zielgroesse": label, "knoten_quantil": q, "knoten_anwesende": float(np.exp(c)),
                         "elastizitaet_unter_knoten": fit.params["log_anw"],
                         "steigungsaenderung_ueber_knoten": fit.params["knick"],
                         "ki95_unten": fit.params["knick"] - 1.96 * fit.bse["knick"],
                         "ki95_oben": fit.params["knick"] + 1.96 * fit.bse["knick"],
                         "p_wild_bootstrap": p_boot, "p_bonferroni_3_knoten": min(1.0, 3 * p_boot), "spiele": int(fit.nobs)})
    out = pd.DataFrame(rows)
    out["lesart"] = ("Knick = Elastizität sinkt oberhalb des Knotens (negativer Wert) – z.B. weil Stände bei vollem Haus an die "
                     "Grenze kommen. Kontrolle: Saison, Top-Gegner, Werktag, Abend, Temperatur. Nicht belastbar, wenn p (Bonferroni) ≥ 0.05.")
    return out


# --------------------------------------------------------------------------------------------
# Mobiler Verkauf (Runner/Bauchläden) und operative Merkmale
# --------------------------------------------------------------------------------------------
def mobiler_verkauf(m, res: dict, n_boot: int = 2000) -> dict[str, pd.DataFrame]:
    lang = res["diagnosekarte_lang"]
    c = m.fact_catering_match.dropna(subset=["match_id"]).drop_duplicates("match_id")
    status = c.set_index("match_id")["mobil_status"]
    rng = np.random.default_rng(SEED)
    rows = []
    for ziel in ("kf_exkl", "bons_pro_anwesende", "bon_exkl"):
        l_ = lang[lang["ziel_code"] == ziel].copy()
        l_["abw_pct"] = (l_["beobachtet"] / l_["erwartet"] - 1) * 100
        l_["status"] = l_["match_id"].map(status).fillna("keine Angabe")
        l_["gruppe"] = np.where(l_["status"].isin(["eingeschränkt", "nicht im Einsatz"]), "ganz/teilweise nicht im Einsatz",
                                np.where(l_["status"] == "im Einsatz", "im Einsatz", "keine Angabe"))
        sd = l_["abw_pct"].std()
        a_ = l_.loc[l_["gruppe"] == "ganz/teilweise nicht im Einsatz", "abw_pct"].to_numpy()
        b_ = l_.loc[l_["gruppe"] == "im Einsatz", "abw_pct"].to_numpy()
        for gruppe, g in l_.groupby("gruppe"):
            v = g["abw_pct"].to_numpy()
            boot = [rng.choice(v, len(v)).mean() for _ in range(n_boot)]
            rows.append({"zielgroesse": g["zielgroesse"].iloc[0], "gruppe": gruppe, "spiele": len(v),
                         "abweichung_von_erwartung_pct": v.mean(), "ki90_unten": np.quantile(boot, 0.05),
                         "ki90_oben": np.quantile(boot, 0.95)})
        if len(a_) >= 3 and len(b_) >= 3:
            diff_boot = [rng.choice(a_, len(a_)).mean() - rng.choice(b_, len(b_)).mean() for _ in range(n_boot)]
            rows.append({"zielgroesse": l_["zielgroesse"].iloc[0], "gruppe": "Differenz (nicht im Einsatz − im Einsatz)",
                         "spiele": len(a_) + len(b_), "abweichung_von_erwartung_pct": a_.mean() - b_.mean(),
                         "ki90_unten": np.quantile(diff_boot, 0.05), "ki90_oben": np.quantile(diff_boot, 0.95),
                         "mde_80pct_power_pct": 2.8 * sd * np.sqrt(1 / len(a_) + 1 / len(b_))})
    out = pd.DataFrame(rows)
    out["lesart"] = ("Abweichung = beobachtet / kontextbereinigt erwartet − 1 (Leave-one-match-out, Phase 1). MDE = kleinster "
                     "Unterschied, den diese Stichprobe mit 80 % Power erkennen könnte. Codierung nur aus ausdrücklichen Bemerkungen; "
                     "fehlende Angabe ≠ kein Einsatz. Schwache Nachfrage kann sowohl Ursache als auch Folge sein.")
    tab = c[c["wettbewerb"].isin(config.KERN_WETTBEWERBE)].groupby(["saison", "mobil_status"]).size().unstack(fill_value=0).reset_index()
    return {"mobiler_verkauf_effekt": out, "mobiler_verkauf_codierung": tab}


# --------------------------------------------------------------------------------------------
# Zahlungswege und digitale Kanäle
# --------------------------------------------------------------------------------------------
def zahlungswege(m) -> pd.DataFrame:
    c = m.fact_catering_match.dropna(subset=["match_id"])
    c = c[c["wettbewerb"] == "SL"]
    kan = {"Payfix (Kasse/Stand)": "kanal_payfix_inkl", "Just Eat (App)": "kanal_justeat_inkl", "Pick Up (App)": "kanal_pickup_inkl",
           "Gutscheine/nicht verbucht": "kanal_gutscheine_inkl", "Extern (Partner-Stände)": "kanal_extern_inkl"}
    rows = []
    for s, g in c.groupby("saison"):
        if g.get("kanal_payfix_inkl", pd.Series(dtype=float)).sum() <= 0:
            continue
        total = g["umsatz_inkl"].sum()
        for name, col in kan.items():
            if col not in g or g[col].fillna(0).sum() <= 0:
                continue
            anteil_spiel = g[col].fillna(0) / g["umsatz_inkl"]
            rows.append({"saison": s, "kanal": name, "umsatz_inkl": g[col].sum(), "anteil": g[col].sum() / total,
                         "anteil_min_spiel": anteil_spiel.min(), "anteil_max_spiel": anteil_spiel.max(),
                         "spiele_mit_umsatz": int((g[col].fillna(0) > 0).sum())})
    out = pd.DataFrame(rows)
    out["lesart"] = "Meisterschaft; Anteile am Catering-Umsatz inkl. MwSt. Pick Up ersetzt ab 2026/27 Just Eat."
    return out


# --------------------------------------------------------------------------------------------
# Kiesplatz und Wetter
# --------------------------------------------------------------------------------------------
def kiesplatz_wetter(m, d: pd.DataFrame) -> dict[str, pd.DataFrame]:
    kp = m.fact_kiesplatz[m.fact_kiesplatz["ist_total"] & m.fact_kiesplatz["match_id"].notna()]
    kp = kp.groupby("match_id").agg(kies_brutto=("brutto_total", "sum"), kies_normal=("brutto_normal", "sum")).reset_index()
    x = d[(d["wettbewerb"] == "SL")].merge(kp, on="match_id", how="inner")
    x = x[(x["kies_brutto"] > 0) & x["umsatz_inkl"].notna() & x["temp_anpfiff_c"].notna()].copy()
    x["kies_je_anw"] = x["kies_brutto"] / x["public_netto"]
    x["stadion_je_anw"] = (x["umsatz_inkl"] - x["kies_brutto"]) / x["public_netto"]
    x["anteil_kies"] = x["kies_brutto"] / x["umsatz_inkl"]
    x["regen"] = x["regen_anreise"].astype(float)
    rows, resid = [], {}
    for ziel, label in (("kies_je_anw", "Kiesplatz CHF je Anwesendem (brutto)"), ("stadion_je_anw", "Stadion (ohne Kiesplatz) CHF je Anwesendem"),
                        ("anteil_kies", "Kiesplatz-Anteil am Catering")):
        y = np.log(x[ziel]) if ziel != "anteil_kies" else x[ziel] * 100
        fit = smf.ols("y ~ temp_anpfiff_c + regen + abendspiel + werktag + top_gegner + C(saison)",
                      data=x.assign(y=y, abendspiel=x["abendspiel"].astype(float), werktag=x["werktag"].astype(float),
                                    top_gegner=x["top_gegner"].astype(float))).fit(cov_type="HC3")
        resid[ziel] = fit.resid
        for var, schritt, einheit in (("temp_anpfiff_c", 5, "+5 °C"), ("regen", 1, "Regen bei Anreise"), ("abendspiel", 1, "Abendspiel")):
            b, se = fit.params[var] * schritt, fit.bse[var] * schritt
            if ziel == "anteil_kies":
                eff, lo, hi, eh = b, b - 1.96 * se, b + 1.96 * se, "Pp."
            else:
                eff, lo, hi, eh = (np.exp(b) - 1) * 100, (np.exp(b - 1.96 * se) - 1) * 100, (np.exp(b + 1.96 * se) - 1) * 100, "%"
            rows.append({"zielgroesse": label, "variable": einheit, "effekt": eff, "ki95_unten": lo, "ki95_oben": hi,
                         "einheit": eh, "p_wert": float(fit.pvalues[var]), "spiele": int(fit.nobs)})
    out = pd.DataFrame(rows)
    r_sub = float(np.corrcoef(resid["kies_je_anw"], resid["stadion_je_anw"])[0, 1])
    out["residuen_korrelation_kies_stadion"] = r_sub
    out["lesart"] = ("Negative Residuen-Korrelation spräche für Verlagerung zwischen Kiesplatz und Stadion (Substitution), positive "
                     "für gemeinsame Schwankung (Stimmung/Nachfrage). Kiesplatz ist im Catering-Total enthalten – nie addieren.")
    return {"kiesplatz_wetter": out, "kiesplatz_je_spiel_ideen": x[["match_id", "datum", "saison", "kies_brutto", "kies_je_anw",
                                                                   "stadion_je_anw", "anteil_kies", "temp_anpfiff_c", "regen"]]}


# --------------------------------------------------------------------------------------------
# φ: Konsumieren zusätzliche Anwesende wie der Schnitt?
# --------------------------------------------------------------------------------------------
def phi_evidenz(res: dict, d: pd.DataFrame, absatz_merkmale: pd.DataFrame) -> pd.DataFrame:
    el = res["elastizitaet"].copy()
    el["art"] = "Elastizität Umsatz ~ Public-Anwesende (Phase 1)"
    x = d[d["hauptstichprobe"] & d["temp_anpfiff_c"].notna()].merge(
        absatz_merkmale[["match_id", "einzel_alle", "anteil_gratis"]], on="match_id", how="inner").copy()
    x["gratis_anteil_ist"] = x["anteil_gratis"] * x["einzel_alle"] / x["ist"] * 100
    x["log_kf"] = np.log(x["kf_exkl"])
    fit = smf.ols("log_kf ~ gratis_anteil_ist + C(saison) + top_gegner + werktag + abendspiel + temp_anpfiff_c",
                  data=x.astype({"top_gegner": float, "werktag": float, "abendspiel": float})).fit(cov_type="HC3")
    b, se = fit.params["gratis_anteil_ist"] * 5, fit.bse["gratis_anteil_ist"] * 5
    promo = pd.DataFrame([{"art": "KF und Anteil Gratis-/Promotickets am IST (je +5 Pp.)", "variante": "SL ab 2022/23, Kontextkontrollen",
                           "spiele": int(fit.nobs), "elastizitaet": np.nan, "effekt_pct": (np.exp(b) - 1) * 100,
                           "ki95_unten": (np.exp(b - 1.96 * se) - 1) * 100, "ki95_oben": (np.exp(b + 1.96 * se) - 1) * 100,
                           "p_wert": float(fit.pvalues["gratis_anteil_ist"]),
                           "mittel_gratis_anteil_ist_pct": x["gratis_anteil_ist"].mean()}])
    out = pd.concat([el.rename(columns={"p_wert_gegen_1": "p_wert"}), promo], ignore_index=True)
    out["lesart"] = ("φ ≈ Elastizität: 1 = zusätzliche Anwesende konsumieren wie der Schnitt. Ein negativer Promo-Effekt wiese auf "
                     "unterdurchschnittlichen Konsum der Grenzbesucher hin (φ < 1). Zusammenhänge, keine Kausalität.")
    return out


def rechne(r, m, res: dict, basis: pd.DataFrame, absatz_merkmale: pd.DataFrame) -> dict[str, pd.DataFrame]:
    d = res["modell_daten"]
    out = {"kf_entwicklung": kf_entwicklung(basis)}
    out.update(warenkorb(res, basis))
    out["preis_menge"] = preis_menge(res, basis)
    out.update(alkohol_proxy(m, res))
    out.update(alkohol_modelle(out["alkohol_je_spiel"], d))
    out["durchsatz_knick"] = durchsatz_knick(d)
    out.update(mobiler_verkauf(m, res))
    out["zahlungswege_ideen"] = zahlungswege(m)
    out.update(kiesplatz_wetter(m, d))
    out["phi_evidenz"] = phi_evidenz(res, d, absatz_merkmale)
    return out

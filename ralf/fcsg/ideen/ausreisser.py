"""Positive Ausreisser: Was lief bei Spielen über der Kontexterwartung anders? (deskriptiv, kleine Fallzahlen)

Ausserhalb des 80 %-Bands liegen schon zufällig rund 10 % der Spiele je Seite – deshalb steht die erwartete
Zufallszahl neben der beobachteten. Merkmalsvergleiche sind Hinweise für Hypothesen, keine Belege.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from scipy import stats

ZIELE = {"kf_exkl": "Kundenfranken exkl. MwSt", "anwesenheitsquote": "Anwesenheitsquote (IST/SOLL)"}


def ausreisser(res: dict, ctx: pd.DataFrame, m, alk: pd.DataFrame, typen: pd.DataFrame) -> dict[str, pd.DataFrame]:
    karte = res["diagnosekarte"]
    c = m.fact_catering_match.dropna(subset=["match_id"]).drop_duplicates("match_id").set_index("match_id")
    alk = alk[alk["proxy_gueltig"]].copy()
    alk["alkohol_abw_pp"] = (alk["s_brutto"] - alk.groupby("saison")["s_brutto"].transform("mean")) * 100
    zaehl, listen, merkmale = [], [], []
    for code, label in ZIELE.items():
        z = f"z_wert_{code}"
        if z not in karte:
            continue
        x = karte.dropna(subset=[z]).copy()
        n = len(x)
        x["lage"] = np.select([x[z] > 1.2816, x[z] < -1.2816], ["über Erwartung", "unter Erwartung"], default="im Band")
        for lage in ("über Erwartung", "unter Erwartung"):
            zaehl.append({"zielgroesse": label, "lage": lage, "spiele_beobachtet": int((x["lage"] == lage).sum()),
                          "spiele_erwartet_zufall": n * 0.10, "spiele_total": n,
                          "binomial_p_mehr_als_zufall": float(stats.binomtest(int((x["lage"] == lage).sum()), n, 0.10,
                                                                               alternative="greater").pvalue)})
        x = x.merge(ctx[["match_id", "temp_anpfiff_c", "schulferien"]], on="match_id", how="left")
        x["abendspiel"] = x["anpfiff"].astype(str).str[:2].astype(float) >= 20
        x["wochenende"] = x["wochentag"].isin(["Samstag", "Sonntag"])
        x["mobil"] = x["match_id"].map(c["mobil_status"]).fillna("keine Angabe")
        x["plattform_event"] = x["match_id"].map(c["event_plattform"]).fillna(False).astype(bool)
        x["alkohol_abw_pp"] = x["match_id"].map(alk.set_index("match_id")["alkohol_abw_pp"])
        x["spieltyp"] = x["match_id"].map(typen.set_index("match_id")["spieltyp"]) if len(typen) else np.nan
        top = x[x["lage"] == "über Erwartung"].sort_values(z, ascending=False)
        for _, r_ in top.iterrows():
            listen.append({"zielgroesse": label, "datum": r_["datum"], "gegner": r_["gegner_anzeige"], "wochentag": r_["wochentag"],
                           "anpfiff": r_["anpfiff"], "temperatur_c": r_["temp_anpfiff_c"],
                           "beobachtet": r_[f"beobachtet_{code}"], "erwartet": r_[f"erwartet_{code}"],
                           "abweichung_pct": (r_[f"beobachtet_{code}"] / r_[f"erwartet_{code}"] - 1) * 100,
                           "mobiler_verkauf": r_["mobil"], "plattform_event": r_["plattform_event"],
                           "alkoholanteil_abw_pp": r_["alkohol_abw_pp"], "spieltyp": r_["spieltyp"],
                           "mechanismen": r_.get("mechanismen")})
        rest = x[x["lage"] != "über Erwartung"]
        for merkmal, serie in [("Abendspiel (ab 20 Uhr)", "abendspiel"), ("Wochenende", "wochenende"),
                               ("Plattform-Event/Zusatzprogramm", "plattform_event")]:
            a_, b_ = top[serie].astype(bool), rest[serie].astype(bool)
            tab = [[int(a_.sum()), int((~a_).sum())], [int(b_.sum()), int((~b_).sum())]]
            merkmale.append({"zielgroesse": label, "merkmal": merkmal, "anteil_positive_ausreisser": a_.mean() if len(a_) else np.nan,
                             "anteil_uebrige": b_.mean(), "p_fisher": float(stats.fisher_exact(tab)[1]) if len(a_) else np.nan})
        for merkmal, serie in [("Temperatur bei Anpfiff (°C)", "temp_anpfiff_c"), ("Alkoholanteil, Abw. vom Saisonmittel (Pp.)", "alkohol_abw_pp")]:
            merkmale.append({"zielgroesse": label, "merkmal": merkmal, "anteil_positive_ausreisser": top[serie].mean(),
                             "anteil_uebrige": rest[serie].mean(), "p_fisher": np.nan})
        im = x["mobil"] == "im Einsatz"
        merkmale.append({"zielgroesse": label, "merkmal": "Mobiler Verkauf ausdrücklich im Einsatz",
                         "anteil_positive_ausreisser": im[x["lage"] == "über Erwartung"].mean(),
                         "anteil_uebrige": im[x["lage"] != "über Erwartung"].mean(), "p_fisher": np.nan})
    zaehl = pd.DataFrame(zaehl)
    zaehl["lesart"] = "80 %-Band: je Seite liegen rund 10 % der Spiele schon zufällig ausserhalb."
    m_ = pd.DataFrame(merkmale)
    m_["lesart"] = "Vergleich positive Ausreisser vs. übrige Spiele (Anteile bzw. Mittelwerte); Hinweise, keine Belege."
    return {"ausreisser_zaehlung": zaehl, "ausreisser_positiv": pd.DataFrame(listen), "ausreisser_merkmale": m_}

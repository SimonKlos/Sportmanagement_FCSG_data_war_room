"""Kontextmodelle je Zielgrösse (Kontext-Effekt-Matrix) und Diagnosekarte (Auftrag Abschnitte 6 und 7).

Modellstrategie
* Je Zielgrösse ein eigenes, sparsames Modell (keine Gesamtumsatz-Regression):
  Anwesenheitsquote (logit), Kundenfranken, Bons je Anwesendem, Ø Bon (je log) und optional der Anteil
  Frühankommender (logit). Immer mit Saison-Effekten (Preise, MwSt, Definitionswechsel, Trends).
* Wenige, vorab festgelegte Kontextvariablen; Clubhebel (Stände, Zweitmarkt, Kommunikation, Payment)
  werden bewusst NICHT herauskontrolliert, sondern erscheinen in der Diagnosekarte als Mechanismen.
* Validierung: Leave-one-season-out auf saisonbereinigten Werten (Basislinie = Saisonmittel) und
  Leave-one-match-out für die Erwartungswerte der Diagnosekarte. «Nicht belastbar schätzbar» ist ein
  zulässiges Ergebnis.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import statsmodels.formula.api as smf

from .. import config
from ..log import befund
from ..utils import text, als_bool

ZIELE = {
    "anwesenheitsquote": {"label": "Anwesenheitsquote (IST/SOLL)", "transform": "logit", "daten": "anwesenheit"},
    "kf_exkl": {"label": "Kundenfranken exkl. MwSt", "transform": "log", "daten": "catering"},
    "bons_pro_anwesende": {"label": "Bons je Public-Anwesendem", "transform": "log", "daten": "catering"},
    "bon_exkl": {"label": "Ø Bon exkl. MwSt", "transform": "log", "daten": "catering"},
    "anteil_ab_45_min": {"label": "Anteil Ankunft ≥ 45 min vor Anpfiff (optional)", "transform": "logit", "daten": "zutritt"},
}
_ANSTOSS = "extern (Spielplan/Anstosszeit durch Liga/TV, D-045)"
# Run-3-Spezifikation (Werktag + Abendspiel ab 20 Uhr) – nur noch für Vergleiche (run4.py, Sensitivität)
VARIABLEN_RUN3 = {
    "top_gegner": {"label": "Top-Gegner (FCB, YB, FCZ)", "schritt": 1, "einheit": "ja vs. nein",
                   "einordnung": "extern (Gegner)"},
    "werktag": {"label": "Werktag (Mo–Fr) statt Wochenende", "schritt": 1, "einheit": "ja vs. nein",
                "einordnung": "teilweise beeinflussbar (Spielplan/TV durch Liga)"},
    "abendspiel": {"label": "Abendspiel (Anpfiff ab 20 Uhr)", "schritt": 1, "einheit": "ja vs. nein",
                   "einordnung": "teilweise beeinflussbar (Anstosszeit/TV durch Liga)"},
    "temp_anpfiff_c": {"label": "Temperatur bei Anpfiff", "schritt": 5, "einheit": "+5 °C",
                       "einordnung": "extern (Wetter)"},
    "regen_anreise": {"label": "Regen bei Anreise (≥ 0.5 mm in 2 h vor Anpfiff)", "schritt": 1, "einheit": "ja vs. nein",
                      "einordnung": "extern (Wetter)"},
    "schulferien": {"label": "Schulferien Stadt St.Gallen", "schritt": 1, "einheit": "ja vs. nein",
                    "einordnung": "extern (Kalender)"},
}
NICHT_IM_MODELL = [
    ("Werktag und Abendspiel ab 20 Uhr (Run 3)", "extern (Spielplan/Anstosszeit durch Liga/TV, D-045)", "nein (ersetzt)",
     "Ab Run 4 durch den Anstoss-Slot ersetzt (D-048): Run 3 legte Samstag 18 Uhr und Sonntag 16.30 Uhr in dieselbe Kategorie."),
    ("Gegnerstärke (Punkte/Spiel vor dem Spiel)", "extern (sportlich)", "nur Sensitivität",
     "Alternative zu Top-Gegner; beide zusammen wären kollinear."),
    ("Form/Tabellenplatz FCSG", "extern (sportlich)", "nein", "Zu wenige Spiele für zusätzliche Variablen; Resultat erst nach dem Spiel bekannt."),
    ("Free-TV (SRF)", "teilweise beeinflussbar (Liga/TV)", "nein", "Nur in der Kontexttabelle, 6 Spiele 25/26 fehlen; selten (13 Spiele)."),
    ("Parallelevents/Feiertage", "extern", "nein", "Sehr selten erfasst (≤ 5 Spiele); nicht schätzbar."),
    ("Verkaufsquote (SOLL/Kapazität)", "Zielgrösse", "nein", "Nenner (verfügbare Kapazität je Spiel inkl. Sperrungen) nicht verifiziert."),
    ("Standbesetzung/geschlossene Stände", "Clubhebel", "nein (bewusst)", "Clubhebel nicht herauskontrollieren; erscheint in der Diagnosekarte."),
    ("Zweitmarkt, Kommunikation, Toröffnung/Programm, Sortiment, Payment", "Clubhebel", "nein (bewusst)",
     "Clubhebel; keine Messgrösse je Spiel bzw. Phase 2."),
    ("Ankunftszeit", "Vermittler einer Clubmassnahme", "nein", "Nicht pauschal externer Kontext (Auftrag 6.2); eigene Zielgrösse."),
]
HAUPT_RUN3 = list(VARIABLEN_RUN3)
# Ab Run 4 (D-048): Anstoss-Slot statt Werktag + Abendspiel; übrige Variablen unverändert
VARIABLEN = {"top_gegner": VARIABLEN_RUN3["top_gegner"],
             **{c: {"label": f"{lab} (vs. {config.REFERENZ_SLOT})", "schritt": 1, "einheit": f"vs. {config.REFERENZ_SLOT}",
                    "einordnung": _ANSTOSS} for c, lab in config.SLOTS.items()},
             **{c: VARIABLEN_RUN3[c] for c in ("temp_anpfiff_c", "regen_anreise", "schulferien")}}
HAUPT = list(VARIABLEN)
ZEIT_TERME = list(config.SLOTS)          # Anstoss-Kontrolle in Nebenmodellen (Ideen-Grundlage, Elastizität, Ankunft)
ALLE_VARIABLEN = {**VARIABLEN_RUN3, **VARIABLEN}


def zeit_formel() -> str:
    """Formelteil der Anstoss-Kontrolle, z.B. für «y ~ x + C(saison) + top_gegner + <zeit_formel()>»."""
    return " + ".join(ZEIT_TERME)


def label(var: str) -> str:
    """Anzeigename einer Kontextvariable (Run-4- oder Run-3-Spezifikation)."""
    return ALLE_VARIABLEN[var]["label"]
BAND_Z = 1.2816     # 80 %-Band


# --------------------------------------------------------------------------------------------
# Daten
# --------------------------------------------------------------------------------------------
def modell_daten(k: pd.DataFrame, ctx: pd.DataFrame, ankunft: pd.DataFrame) -> pd.DataFrame:
    d = k.merge(ctx[["match_id", "temp_anpfiff_c", "regen_anreise", "schulferien", "ppg_gegner_gestuetzt",
                     "temp_tagesmittel", "niederschlag_anreise_mm"]], on="match_id", how="left")
    d = d.merge(ankunft[["match_id", "anteil_ab_45_min", "median_min_vor_anpfiff"]], on="match_id", how="left")
    d = d[d["spielstatus"] == "gespielt"].copy()
    d["werktag"] = ~d["wochenende"].astype(bool)
    for c in ["top_gegner", "werktag", "abendspiel", "regen_anreise", "schulferien", *config.SLOTS]:
        d[c] = d[c].astype("Float64").astype(float)
    d["qualitaet_ok"] = d["ist_qualitaet"] != "IST geschätzt/Scanprobleme"
    d["hauptstichprobe"] = (d["wettbewerb"] == "SL") & (d["saison"] >= config.MODELL_AB_SAISON)
    return d


def _transform(y: pd.Series, art: str) -> pd.Series:
    if art == "log":
        return np.log(y.where(y > 0))
    p = y.clip(0.001, 0.999)
    return np.log(p / (1 - p))


def _ruecktransform(z, art: str):
    return np.exp(z) if art == "log" else 1 / (1 + np.exp(-z))


def _stichprobe(d: pd.DataFrame, ziel: str, preds: list[str], nur_qualitaet: bool = True,
                scope: str = "haupt") -> pd.DataFrame:
    x = d[d["hauptstichprobe"]] if scope == "haupt" else d[d["wettbewerb"].isin(config.KERN_WETTBEWERBE) &
                                                               (d["saison"] >= config.MODELL_AB_SAISON)]
    if nur_qualitaet:
        x = x[x["qualitaet_ok"]]
    x = x.assign(y=_transform(x[ziel], ZIELE[ziel]["transform"]))
    x = x.dropna(subset=["y", *preds])
    # Saisons mit nur einem Spiel können keinen Saisoneffekt tragen
    return x[x.groupby("saison")["y"].transform("size") >= 3].copy()


# --------------------------------------------------------------------------------------------
# Schätzung, Validierung
# --------------------------------------------------------------------------------------------
def _fit(x: pd.DataFrame, preds: list[str], extra: str = ""):
    formel = "y ~ " + " + ".join(preds + ["C(saison)"]) + extra
    return smf.ols(formel, data=x).fit(cov_type="HC3")


def _demean(x: pd.DataFrame, cols: list[str]) -> pd.DataFrame:
    return x[cols] - x.groupby("saison")[cols].transform("mean")


def loso(x: pd.DataFrame, preds: list[str]) -> tuple[pd.DataFrame, dict]:
    """Leave-one-season-out auf saisonbereinigten Werten. Basislinie = Saisonmittel (Abweichung 0)."""
    folds, res_m, res_b = [], [], []
    for s in sorted(x["saison"].unique()):
        tr, te = x[x["saison"] != s], x[x["saison"] == s]
        if te["saison"].size < 3 or tr["saison"].nunique() < 2:
            continue
        xtr, ytr = _demean(tr, preds).to_numpy(), _demean(tr, ["y"]).to_numpy().ravel()
        beta, *_ = np.linalg.lstsq(xtr, ytr, rcond=None)
        xte, yte = _demean(te, preds).to_numpy(), _demean(te, ["y"]).to_numpy().ravel()
        e_m, e_b = yte - xte @ beta, yte
        res_m.append(e_m)
        res_b.append(e_b)
        folds.append({"saison_ausgelassen": s, "spiele": len(te), "rmse_modell": float(np.sqrt(np.mean(e_m ** 2))),
                      "rmse_saisonmittel": float(np.sqrt(np.mean(e_b ** 2))), **{f"beta_{p}": b for p, b in zip(preds, beta)}})
    f = pd.DataFrame(folds)
    if not res_m:
        return f, {}
    em, eb = np.concatenate(res_m), np.concatenate(res_b)
    gesamt = {"rmse_modell_loso": float(np.sqrt(np.mean(em ** 2))), "rmse_saisonmittel_loso": float(np.sqrt(np.mean(eb ** 2)))}
    gesamt["verbesserung_loso_pct"] = (1 - gesamt["rmse_modell_loso"] / gesamt["rmse_saisonmittel_loso"]) * 100
    return f, gesamt


def lomo(x: pd.DataFrame, preds: list[str]) -> pd.Series:
    """Leave-one-match-out-Vorhersage (mit Saison-Effekten aus den übrigen Spielen derselben Saison)."""
    dummies = pd.get_dummies(x["saison"], drop_first=True, dtype=float)
    X = np.column_stack([np.ones(len(x)), x[preds].to_numpy(float), dummies.to_numpy()])
    y = x["y"].to_numpy()
    pred = np.empty(len(x))
    for i in range(len(x)):
        mask = np.ones(len(x), dtype=bool)
        mask[i] = False
        beta, *_ = np.linalg.lstsq(X[mask], y[mask], rcond=None)
        pred[i] = X[i] @ beta
    return pd.Series(pred, index=x.index)


def _effekt(beta: float, se: float, ziel: str, var: str, pbar: float) -> tuple[float, float, float]:
    s = ALLE_VARIABLEN[var]["schritt"]
    if ZIELE[ziel]["transform"] == "log":
        f = lambda b: (np.exp(b * s) - 1) * 100
    else:
        f = lambda b: b * s * pbar * (1 - pbar) * 100
    return f(beta), f(beta - 1.96 * se), f(beta + 1.96 * se)


# --------------------------------------------------------------------------------------------
# Sensitivität
# --------------------------------------------------------------------------------------------
def _varianten(d: pd.DataFrame, ziel: str) -> list[tuple[str, pd.DataFrame, list[str], str]]:
    preds = HAUPT
    v = [("Hauptmodell (SL ab 22/23, Datenqualität ok)", _stichprobe(d, ziel, preds), preds, "")]
    v.append(("inkl. Spiele mit Scanproblemen/geschätztem IST", _stichprobe(d, ziel, preds, nur_qualitaet=False), preds, ""))
    x = _stichprobe(d, ziel, preds, scope="kern")
    v.append(("inkl. Cup und UEFA (mit Wettbewerbs-Effekt)", x, preds, " + C(wettbewerb)" if x["wettbewerb"].nunique() > 1 else ""))
    alt = [p if p != "top_gegner" else "ppg_gegner_gestuetzt" for p in preds]
    v.append(("Gegnerstärke als Punkte/Spiel statt Top-Gegner", _stichprobe(d, ziel, alt), alt, ""))
    alt = [p if p != "temp_anpfiff_c" else "temp_tagesmittel" for p in preds]
    v.append(("Tagesmittel-Temperatur (Kontexttabelle) statt Anpfiff", _stichprobe(d, ziel, alt), alt, ""))
    x = _stichprobe(d, ziel, preds)
    z = (x["y"] - x.groupby("saison")["y"].transform("median")).abs()
    v.append(("ohne Ausreisser (> 3 robuste SD vom Saisonmedian)", x[z <= 3 * 1.4826 * z.median()], preds, ""))
    v.append(("nur Spiele mit ticketbasiertem SOLL (ohne Kapazitätswert)", x[als_bool(x["soll_ticketbasiert"])], preds, ""))
    return v


# --------------------------------------------------------------------------------------------
# Hauptfunktion
# --------------------------------------------------------------------------------------------
def kontextmodelle(d: pd.DataFrame) -> dict[str, pd.DataFrame]:
    matrix, guete, sens_rows, folds_all, diag = [], [], [], [], []
    for ziel, meta in ZIELE.items():
        x = _stichprobe(d, ziel, HAUPT)
        if len(x) < 20:
            guete.append({"zielgroesse": meta["label"], "spiele": len(x), "hinweis": "zu wenige Spiele – nicht geschätzt"})
            continue
        fit = _fit(x, HAUPT)
        nur_saison = smf.ols("y ~ C(saison)", data=x).fit()
        folds, loso_g = loso(x, HAUPT)
        folds_all.append(folds.assign(zielgroesse=meta["label"]))
        pbar = float(_ruecktransform(x["y"], meta["transform"]).mean())

        # Sensitivität
        sens = {}
        for name, xs, preds, extra in _varianten(d, ziel):
            if len(xs) < 20:
                continue
            fs = _fit(xs, preds, extra)
            for p in preds:
                basis = "top_gegner" if p == "ppg_gegner_gestuetzt" else ("temp_anpfiff_c" if p == "temp_tagesmittel" else p)
                if not name.startswith("Hauptmodell"):
                    sens.setdefault(basis, []).append(np.sign(fs.params[p]))
                sens_rows.append({"zielgroesse": meta["label"], "variante": name, "variable": p, "spiele": int(fs.nobs),
                                  "koeffizient": fs.params[p], "p_wert": fs.pvalues[p]})

        for var in HAUPT:
            b, se = fit.params[var], fit.bse[var]
            eff, lo, hi = _effekt(b, se, ziel, var, pbar)
            vz = np.sign(b)
            loso_stab = float((np.sign(folds[f"beta_{var}"]) == vz).mean()) if len(folds) else np.nan
            sens_stab = float(np.mean(np.array(sens.get(var, [])) == vz)) if sens.get(var) else np.nan
            ki_ohne_null = (lo > 0) or (hi < 0)
            if ki_ohne_null and loso_stab >= 0.8 and sens_stab >= 0.8:
                urteil = "belastbar"
            elif loso_stab >= 0.8 and sens_stab >= 0.8:
                urteil = "Hinweis (Richtung stabil, Grösse unsicher)"
            else:
                urteil = "nicht belastbar schätzbar"
            matrix.append({"zielgroesse": meta["label"], "variable": VARIABLEN[var]["label"],
                           "einordnung": VARIABLEN[var]["einordnung"], "veraenderung": VARIABLEN[var]["einheit"],
                           "effekt": eff, "einheit_effekt": "%" if meta["transform"] == "log" else "Prozentpunkte",
                           "ki95_unten": lo, "ki95_oben": hi, "p_wert": float(fit.pvalues[var]),
                           "vorzeichen_stabil_loso": loso_stab, "vorzeichen_stabil_sensitivitaet": sens_stab,
                           "beurteilung": urteil, "spiele": int(fit.nobs)})

        # Erwartungswerte für die Diagnosekarte (Leave-one-match-out)
        x["erwartet_t"] = lomo(x, HAUPT)
        resid = x["y"] - x["erwartet_t"]
        rmse_lomo = float(np.sqrt(np.mean(resid ** 2)))
        smearing = float(np.mean(np.exp(fit.resid))) if meta["transform"] == "log" else np.nan
        r2_kontext = 1 - fit.ssr / nur_saison.ssr
        guete.append({"zielgroesse": meta["label"], "transformation": meta["transform"], "spiele": int(fit.nobs),
                      "saisons": ", ".join(sorted(x["saison"].unique())), "r2_gesamt": fit.rsquared,
                      "r2_kontext_innerhalb_saison": r2_kontext, **loso_g, "rmse_lomo_transformiert": rmse_lomo,
                      "smearing_faktor": smearing,
                      "hinweis": "R² innerhalb Saison = Anteil der saisonbereinigten Streuung, den der Kontext erklärt."})
        diag.append(_diagnose(x, ziel, meta, rmse_lomo))

    out = {"kontext_effekt_matrix": pd.DataFrame(matrix), "modellguete": pd.DataFrame(guete),
           "sensitivitaet": pd.DataFrame(sens_rows), "loso_folds": pd.concat(folds_all, ignore_index=True),
           "diagnosekarte_lang": pd.concat(diag, ignore_index=True),
           "variablen_einordnung": _einordnung()}
    _befunde(out)
    return out


def _einordnung() -> pd.DataFrame:
    rows = [{"variable": v["label"], "einordnung": v["einordnung"], "im_hauptmodell": "ja",
             "begruendung": "vorab festgelegt, vor dem Spiel bekannt"} for v in VARIABLEN.values()]
    rows += [{"variable": a, "einordnung": b, "im_hauptmodell": c, "begruendung": d} for a, b, c, d in NICHT_IM_MODELL]
    return pd.DataFrame(rows)


def _diagnose(x: pd.DataFrame, ziel: str, meta: dict, rmse: float) -> pd.DataFrame:
    art = meta["transform"]
    beob = _ruecktransform(x["y"], art)
    erw = _ruecktransform(x["erwartet_t"], art)
    unten = _ruecktransform(x["erwartet_t"] - BAND_Z * rmse, art)
    oben = _ruecktransform(x["erwartet_t"] + BAND_Z * rmse, art)
    z = (x["y"] - x["erwartet_t"]) / rmse
    out = pd.DataFrame({"match_id": x["match_id"], "zielgroesse": meta["label"], "ziel_code": ziel,
                        "beobachtet": beob, "erwartet": erw, "band80_unten": unten, "band80_oben": oben,
                        "diagnoseluecke": erw - beob, "z_wert": z,
                        "status": np.select([z < -BAND_Z, z > BAND_Z], ["unter Erwartung", "über Erwartung"],
                                            default="im Erwartungsband"),
                        "saisonmittel": _ruecktransform(x.groupby("saison")["y"].transform("mean"), art)})
    return out


def _befunde(out: dict[str, pd.DataFrame]) -> None:
    g = out["modellguete"]
    for _, r in g.iterrows():
        if "verbesserung_loso_pct" in r and not pd.isna(r.get("verbesserung_loso_pct")):
            befund("Modelle", "info", r["zielgroesse"],
                   f"Kontext erklärt {r['r2_kontext_innerhalb_saison']:.0%} der saisonbereinigten Streuung; "
                   f"out-of-sample (Leave-one-season-out) {r['verbesserung_loso_pct']:+.0f} % RMSE gegenüber Saisonmittel.",
                   "Nur Spielebene; kleine Stichprobe.", "Siehe Kontext-Effekt-Matrix und Sensitivität.")


# --------------------------------------------------------------------------------------------
# Diagnosekarte (eine Zeile pro Spiel) und wiederkehrende Muster
# --------------------------------------------------------------------------------------------
def _ja(v) -> bool:
    return (not pd.isna(v)) and bool(v)


def diagnosekarte(lang: pd.DataFrame, d: pd.DataFrame, att: pd.DataFrame, cat: pd.DataFrame) -> dict[str, pd.DataFrame]:
    breit = lang.pivot_table(index="match_id", columns="ziel_code",
                             values=["beobachtet", "erwartet", "band80_unten", "band80_oben", "z_wert", "status"],
                             aggfunc="first")
    breit.columns = [f"{a}_{b}" for a, b in breit.columns]
    breit = breit.reset_index()
    info = d[["match_id", "datum", "saison", "wettbewerb", "gegner_anzeige", "anpfiff", "wochentag", "public_netto",
              "soll", "ist", "soll_ticketbasiert", "ist_qualitaet", "kf_exkl"]]
    c = cat.dropna(subset=["match_id"]).drop_duplicates("match_id")[
        ["match_id", "stand_geschlossen", "mobiler_verkauf_reduziert", "personalmangel", "technische_probleme",
         "operativer_hinweis", "aktion_gratis_gutschein", "event_plattform", "bemerkung"]].rename(
        columns={"bemerkung": "bemerkung_catering"})
    h = att[["match_id", "bemerkung"]].rename(columns={"bemerkung": "bemerkung_historie"})
    out = info.merge(breit, on="match_id", how="inner").merge(c, on="match_id", how="left").merge(h, on="match_id", how="left")

    # CHF-Referenzlücke Konsum: (erwarteter KF − beobachteter KF) × beobachtete Public-Anwesende
    if "erwartet_kf_exkl" in out:
        out["referenzluecke_konsum_chf"] = (out["erwartet_kf_exkl"] - out["beobachtet_kf_exkl"]) * out["public_netto"]
    if "erwartet_anwesenheitsquote" in out:
        fehl = (out["erwartet_anwesenheitsquote"] - out["beobachtet_anwesenheitsquote"]) * out["soll"]
        out["fehlende_anwesende_ref"] = np.where(als_bool(out["soll_ticketbasiert"]), fehl, np.nan)
        out["chf_szenario_phi_0_6"] = out["fehlende_anwesende_ref"] * 0.6 * out["kf_exkl"]
    out["mechanismen"] = out.apply(_mechanismen, axis=1)
    out["einordnung_konsum"] = out.apply(_einordnung_spiel, axis=1)
    out["einordnung_anwesenheit"] = out.apply(_einordnung_anwesenheit, axis=1)
    out = out.sort_values("datum").reset_index(drop=True)
    muster = _muster(lang, out)
    return {"diagnosekarte": out, "diagnose_muster": muster}


def _mechanismen(r) -> str:
    m = []
    for flag, beschreibung in [("stand_geschlossen", "Stände geschlossen (Catering-Bemerkung)"),
                       ("mobiler_verkauf_reduziert", "Runner/Bauchläden ganz oder teilweise nicht im Einsatz"),
                       ("personalmangel", "Personalmangel"), ("technische_probleme", "technische Probleme (Kasse/App/Internet)"),
                       ("aktion_gratis_gutschein", "Gratis-/Gutscheinaktion"), ("event_plattform", "Plattform-Event/Zusatzprogramm (z.B. Winterzauber, Kids Day)")]:
        if _ja(r.get(flag)):
            m.append(beschreibung)
    if r.get("ist_qualitaet") == "IST geschätzt/Scanprobleme":
        m.append("Datenqualität: IST geschätzt")
    zb, zo = r.get("z_wert_bons_pro_anwesende"), r.get("z_wert_bon_exkl")
    if pd.notna(zb) and pd.notna(zo) and max(abs(zb), abs(zo)) >= BAND_Z:
        m.append("Abweichung v.a. über " + ("Bons je Anwesendem (Frequenz)" if abs(zb) > abs(zo) else "Ø Bon (Warenkorb)"))
    bem = text(r.get("bemerkung_historie")).lower()
    for wort, beschreibung in [("kalt", "kalt (Bemerkung Historie)"), ("nebel", "Nebel"), ("schnee", "Schnee/Verschiebung"),
                       ("ferien", "Ferienbeginn"), ("boykott", "Boykott Gästefans"), ("wahl", "Abstimmungs-/Wahlsonntag"),
                       ("abstimmung", "Abstimmungs-/Wahlsonntag")]:
        if wort in bem:
            m.append(beschreibung)
    return "; ".join(dict.fromkeys(m))


def _einordnung_spiel(r) -> str:
    z = r.get("z_wert_kf_exkl")
    if pd.isna(z):
        return "kein Konsummodell"
    operativ = _ja(r.get("operativer_hinweis"))
    if abs(z) < BAND_Z:
        return "im Erwartungsband (Abweichung vom Saisonmittel durch Kontext erklärt)"
    if z > 0:
        return "über Erwartung – positiver Ausreisser (was lief gut? Muster prüfen)"
    if operativ:
        return "unter Erwartung – möglicher Clubhebel (operativer Hinweis dokumentiert) → Prüfkandidat Phase 2"
    return "unter Erwartung – ungeklärte Abweichung (kein dokumentierter Mechanismus)"


def _einordnung_anwesenheit(r) -> str:
    z = r.get("z_wert_anwesenheitsquote")
    if pd.isna(z):
        return "kein Anwesenheitsmodell"
    if abs(z) < BAND_Z:
        return "im Erwartungsband"
    richtung = "unter" if z < 0 else "über"
    hinweis = text(r.get("bemerkung_historie"))
    if not r.get("soll_ticketbasiert", True):
        return f"{richtung} Erwartung – SOLL ist Kapazitätswert (nur bedingt interpretierbar)"
    return f"{richtung} Erwartung – " + (f"Bemerkung: {hinweis}" if hinweis else "ungeklärt (keine Bemerkung)")


def _muster(lang: pd.DataFrame, karte: pd.DataFrame) -> pd.DataFrame:
    """Mittlere Restabweichung je operativem Merkmal (wiederkehrende Lücken = Prüfkandidaten Phase 2)."""
    rng = np.random.default_rng(1879)
    flags = {"operativer_hinweis": "Operativer Hinweis (Stände zu, Runner/Personal fehlt, Technik)",
             "stand_geschlossen": "Stände geschlossen", "mobiler_verkauf_reduziert": "Runner/Bauchläden ganz oder teilweise nicht im Einsatz",
             "technische_probleme": "technische Probleme", "event_plattform": "Plattform-Event/Zusatzprogramm",
             "aktion_gratis_gutschein": "Gratis-/Gutscheinaktion"}
    rows = []
    for ziel in lang["ziel_code"].unique():
        l = lang[lang["ziel_code"] == ziel].merge(karte[["match_id", *flags]], on="match_id", how="left")
        l["abw_pct"] = (l["beobachtet"] / l["erwartet"] - 1) * 100
        for f, label in flags.items():
            for wert in (True, False):
                g = l[l[f].map(_ja) == wert]["abw_pct"].to_numpy()
                if len(g) < 3:
                    continue
                boot = [rng.choice(g, len(g)).mean() for _ in range(2000)]
                rows.append({"zielgroesse": l["zielgroesse"].iloc[0], "merkmal": label, "auspraegung": "ja" if wert else "nein",
                             "spiele": len(g), "mittlere_abweichung_von_erwartung_pct": g.mean(),
                             "ki90_unten": np.quantile(boot, 0.05), "ki90_oben": np.quantile(boot, 0.95)})
    out = pd.DataFrame(rows)
    out["lesart"] = ("Negative Werte: unter Erwartung bei gleichem Kontext. Wiederkehrende, operativ erklärbare Lücken sind "
                     "Prüfkandidaten für Phase 2 – kein Nachweis eines hebbaren Potenzials.")
    return out

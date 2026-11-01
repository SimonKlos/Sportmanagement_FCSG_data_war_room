"""Kontextmodelle für zusätzliche Zielgrössen – gleiche Logik wie Phase 1 (Saison-Effekte, sechs vorab festgelegte
Kontextvariablen, HC3, Leave-one-season-out, Vorzeichenstabilität), damit die Effekte direkt vergleichbar sind.

Die Phase-1-Zielgrössen (models.ZIELE) bleiben unverändert; hier werden nur neue Zielgrössen geschätzt.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import statsmodels.formula.api as smf

from .. import config
from ..analysis import models as m1


def _effekt(beta: float, se: float, transform: str, var: str, pbar: float) -> tuple[float, float, float]:
    schritt = m1.VARIABLEN[var]["schritt"]
    if transform == "log":
        def f(b):
            return (np.exp(b * schritt) - 1) * 100
    else:
        def f(b):
            return b * schritt * pbar * (1 - pbar) * 100
    return f(beta), f(beta - 1.96 * se), f(beta + 1.96 * se)


def _stichprobe(d: pd.DataFrame, spalte: str, transform: str, preds: list[str], scope: str = "haupt") -> pd.DataFrame:
    if scope == "haupt":
        x = d[d["hauptstichprobe"]]
    else:
        x = d[d["wettbewerb"].isin(config.KERN_WETTBEWERBE) & (d["saison"] >= config.MODELL_AB_SAISON)]
    x = x[x["qualitaet_ok"]].assign(y=m1._transform(x.loc[x["qualitaet_ok"], spalte], transform))
    x = x.dropna(subset=["y", *preds])
    return x[x.groupby("saison")["y"].transform("size") >= 3].copy()


def kontextmodell(d: pd.DataFrame, spalte: str, transform: str, label: str) -> dict[str, pd.DataFrame]:
    """Schätzt ein Kontextmodell für ``spalte`` (transform 'log' oder 'logit') und beurteilt jeden Effekt wie Phase 1."""
    preds = list(m1.HAUPT)
    x = _stichprobe(d, spalte, transform, preds)
    if len(x) < 20:
        return {"matrix": pd.DataFrame(), "guete": pd.DataFrame([{"zielgroesse": label, "spiele": len(x),
                                                                    "hinweis": "zu wenige Spiele – nicht geschätzt"}])}
    fit = m1._fit(x, preds)
    folds, loso_g = m1.loso(x, preds)
    nur_saison = smf.ols("y ~ C(saison)", data=x).fit()
    pbar = float(m1._ruecktransform(x["y"], transform).mean())

    varianten = []
    xs = _stichprobe(d, spalte, transform, preds, scope="kern")
    if xs["wettbewerb"].nunique() > 1:
        varianten.append(("inkl. Cup und UEFA", xs, preds, " + C(wettbewerb)"))
    alt = [p if p != "temp_anpfiff_c" else "temp_tagesmittel" for p in preds]
    varianten.append(("Tagesmittel-Temperatur", _stichprobe(d, spalte, transform, alt), alt, ""))
    alt = [p if p != "top_gegner" else "ppg_gegner_gestuetzt" for p in preds]
    varianten.append(("Gegnerstärke statt Top-Gegner", _stichprobe(d, spalte, transform, alt), alt, ""))
    z = (x["y"] - x.groupby("saison")["y"].transform("median")).abs()
    varianten.append(("ohne Ausreisser", x[z <= 3 * 1.4826 * z.median()], preds, ""))
    vorz: dict[str, list[float]] = {}
    for _, xv, pv, extra in varianten:
        if len(xv) < 20:
            continue
        fv = m1._fit(xv, pv, extra)
        for p in pv:
            basis = {"temp_tagesmittel": "temp_anpfiff_c", "ppg_gegner_gestuetzt": "top_gegner"}.get(p, p)
            vorz.setdefault(basis, []).append(np.sign(fv.params[p]))

    rows = []
    for var in preds:
        b, se = fit.params[var], fit.bse[var]
        eff, lo, hi = _effekt(b, se, transform, var, pbar)
        loso_stab = float((np.sign(folds[f"beta_{var}"]) == np.sign(b)).mean()) if len(folds) else np.nan
        sens_stab = float(np.mean(np.array(vorz.get(var, [])) == np.sign(b))) if vorz.get(var) else np.nan
        ki_ohne_null = (lo > 0) or (hi < 0)
        if ki_ohne_null and loso_stab >= 0.8 and sens_stab >= 0.8:
            urteil = "belastbar"
        elif loso_stab >= 0.8 and sens_stab >= 0.8:
            urteil = "Hinweis (Richtung stabil, Grösse unsicher)"
        else:
            urteil = "nicht belastbar schätzbar"
        rows.append({"zielgroesse": label, "variable": m1.VARIABLEN[var]["label"], "einordnung": m1.VARIABLEN[var]["einordnung"],
                     "veraenderung": m1.VARIABLEN[var]["einheit"], "effekt": eff,
                     "einheit_effekt": "%" if transform == "log" else "Prozentpunkte", "ki95_unten": lo, "ki95_oben": hi,
                     "p_wert": float(fit.pvalues[var]), "vorzeichen_stabil_loso": loso_stab,
                     "vorzeichen_stabil_sensitivitaet": sens_stab, "beurteilung": urteil, "spiele": int(fit.nobs)})
    guete = pd.DataFrame([{"zielgroesse": label, "transformation": transform, "spiele": int(fit.nobs),
                           "saisons": ", ".join(sorted(x["saison"].unique())),
                           "r2_kontext_innerhalb_saison": 1 - fit.ssr / nur_saison.ssr, **loso_g}])
    return {"matrix": pd.DataFrame(rows), "guete": guete}

"""Run 4 – Anstoss-Slot im Kontextmodell und Sensitivitäten 2021/22 (Covid) und ohne 2023/24 (D-041).

Ergänzt die Phase-1-Kontextmodelle (models.py), ohne sie zu verändern:
* Hauptvariante Run 4: «Werktag» und «Abendspiel ab 20 Uhr» werden durch einen Anstoss-Slot ersetzt
  (Referenz Samstag 17–19.59 Uhr). Übrige Kontextvariablen wie in Run 3 (Top-Gegner, Temperatur, Regen, Ferien).
* Sensitivitäten: Run-3-Spezifikation zum Vergleich, inkl. 2021/22 mit Covid-Variable, ohne 2023/24
  (Kassensystemwechsel, eingeschränkte Bons-Vergleichbarkeit).
* Erwartungswerte je Spiel (Leave-one-match-out) und Koeffizienten als Grundlage für den Spielrechner.

Anstoss und Spielplan sind für den Club extern (Liga/TV, D-045). Effekte sind Zusammenhänge, keine Kausalnachweise.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import statsmodels.formula.api as smf

from .. import config
from ..utils import anstoss_slot
from . import models

REFERENZ_SLOT = config.REFERENZ_SLOT
SLOTS = config.SLOTS
UEBRIGE = ["top_gegner", "temp_anpfiff_c", "regen_anreise", "schulferien"]
PREDS_SLOT = [*SLOTS, *UEBRIGE]
PREDS_RUN3 = models.HAUPT_RUN3
MIN_SPIELE = 20


def slot(wochentag: str, anpfiff: str | None) -> str | None:
    """Anstoss-Slot aus Wochentag und Anpfiffzeit (HH:MM). Fehlende Anpfiffzeit bleibt fehlend (utils.anstoss_slot)."""
    return anstoss_slot(wochentag, anpfiff)


def ergaenze_slot(d: pd.DataFrame, kontext: pd.DataFrame) -> pd.DataFrame:
    """Modelldaten (models.modell_daten) um Anstoss-Slot-Dummies und die Covid-Spalte der Kontexttabelle ergänzen."""
    d = d.copy()
    d["anstoss_slot"] = [slot(w, a) for w, a in zip(d["wochentag"], d["anpfiff"])]
    for col, label in SLOTS.items():
        d[col] = np.where(d["anstoss_slot"].isna(), np.nan, (d["anstoss_slot"] == label).astype(float))
    if "covid" in kontext:
        cov = kontext.dropna(subset=["datum"]).drop_duplicates("datum").set_index("datum")["covid"]
        d["covid"] = d["datum"].map(cov).astype("Float64").astype(float)
    else:
        d["covid"] = np.nan
    return d


def _stichprobe(d: pd.DataFrame, ziel: str, preds: list[str], variante: str) -> pd.DataFrame:
    if variante == "inkl_2122":
        x = d[(d["wettbewerb"] == "SL") & (d["saison"] >= "2021/22") & d["qualitaet_ok"]]
    else:
        x = d[d["hauptstichprobe"] & d["qualitaet_ok"]]
    if variante == "ohne_2324":
        x = x[x["saison"] != "2023/24"]
    x = x.assign(y=models._transform(x[ziel], models.ZIELE[ziel]["transform"])).dropna(subset=["y", *preds])
    return x[x.groupby("saison")["y"].transform("size") >= 3].copy()


VARIANTEN = [
    ("run4_anstoss_slot", "Run 4: Anstoss-Slot (SL ab 22/23)", PREDS_SLOT, "haupt"),
    ("run3_werktag_abend", "Vergleich Run 3: Werktag + Abendspiel (SL ab 22/23)", PREDS_RUN3, "haupt"),
    ("inkl_2122_covid", "Sensitivität: inkl. 2021/22 mit Covid-Variable", [*PREDS_SLOT, "covid"], "inkl_2122"),
    ("ohne_2324", "Sensitivität: ohne 2023/24 (Kassensystemwechsel, D-041)", PREDS_SLOT, "ohne_2324"),
]


def _effekt(b: float, se: float, art: str, pbar: float, schritt: float = 1.0) -> tuple[float, float, float]:
    if art == "log":
        f = lambda v: (np.exp(v * schritt) - 1) * 100
    else:
        f = lambda v: v * schritt * pbar * (1 - pbar) * 100
    return f(b), f(b - 1.96 * se), f(b + 1.96 * se)


def _label(var: str) -> str:
    if var == "covid":
        return "Covid-Massnahmen (Kontexttabelle)"
    return models.label(var)


def _schritt(var: str) -> float:
    return models.ALLE_VARIABLEN[var]["schritt"] if var in models.ALLE_VARIABLEN else 1.0


def schaetze(d: pd.DataFrame) -> dict[str, pd.DataFrame]:
    """Alle Varianten je Zielgrösse schätzen: Modellgüte, Effekte, Koeffizienten, Erwartung je Spiel."""
    guete, effekte, koeff, erwartung = [], [], [], []
    for code, name, preds_variante, scope in VARIANTEN:
        for ziel, meta in models.ZIELE.items():
            preds = [p for p in preds_variante if p != "covid"]
            x = _stichprobe(d, ziel, preds, scope)
            # Covid nur, wo es in der Stichprobe variiert (Bons gibt es erst ab 2023/24)
            if "covid" in preds_variante and x["covid"].dropna().nunique() > 1:
                x = x.dropna(subset=["covid"])
                preds = [*preds, "covid"]
            if len(x) < MIN_SPIELE:
                guete.append({"variante": name, "zielgroesse": meta["label"], "spiele": len(x),
                              "hinweis": "zu wenige Spiele – nicht geschätzt"})
                continue
            fit = models._fit(x, preds)
            nur_saison = smf.ols("y ~ C(saison)", data=x).fit()
            _, loso_g = models.loso(x, preds)
            x["erwartet_t"] = models.lomo(x, preds)
            rmse = float(np.sqrt(np.mean((x["y"] - x["erwartet_t"]) ** 2)))
            pbar = float(models._ruecktransform(x["y"], meta["transform"]).mean())
            guete.append({"variante": name, "zielgroesse": meta["label"], "spiele": int(fit.nobs),
                          "saisons": ", ".join(sorted(x["saison"].unique())),
                          "r2_kontext_innerhalb_saison": 1 - fit.ssr / nur_saison.ssr,
                          "verbesserung_loso_pct": loso_g.get("verbesserung_loso_pct", np.nan),
                          "rmse_lomo_transformiert": rmse})
            for var in preds:
                eff, lo, hi = _effekt(fit.params[var], fit.bse[var], meta["transform"], pbar, _schritt(var))
                n_var = int((x[var] == 1).sum()) if var in SLOTS or var == "covid" else int(fit.nobs)
                effekte.append({"variante": name, "zielgroesse": meta["label"], "variable": _label(var),
                                "effekt": eff, "einheit_effekt": "%" if meta["transform"] == "log" else "Prozentpunkte",
                                "ki95_unten": lo, "ki95_oben": hi, "p_wert": float(fit.pvalues[var]),
                                "spiele_mit_merkmal": n_var, "spiele_modell": int(fit.nobs),
                                "ki_ohne_null": bool(lo > 0 or hi < 0)})
            if code == "run4_anstoss_slot":
                for term, wert in fit.params.items():
                    koeff.append({"zielgroesse": meta["label"], "ziel_code": ziel, "transformation": meta["transform"],
                                  "term": term, "koeffizient": float(wert), "standardfehler": float(fit.bse[term]),
                                  "rmse_lomo_transformiert": rmse, "mittel_rueck": pbar})
                art = meta["transform"]
                erwartung.append(pd.DataFrame({
                    "match_id": x["match_id"], "datum": x["datum"], "saison": x["saison"],
                    "anstoss_slot": x["anstoss_slot"], "zielgroesse": meta["label"], "ziel_code": ziel,
                    "beobachtet": models._ruecktransform(x["y"], art),
                    "erwartet": models._ruecktransform(x["erwartet_t"], art),
                    "band80_unten": models._ruecktransform(x["erwartet_t"] - models.BAND_Z * rmse, art),
                    "band80_oben": models._ruecktransform(x["erwartet_t"] + models.BAND_Z * rmse, art)}))
    return {"modellguete": pd.DataFrame(guete), "effekte": pd.DataFrame(effekte),
            "koeffizienten": pd.DataFrame(koeff),
            "erwartung_je_spiel": pd.concat(erwartung, ignore_index=True) if erwartung else pd.DataFrame()}


def deskriptiv(d: pd.DataFrame) -> pd.DataFrame:
    """Meisterschaft ab 22/23: Spiele, KF (Summe/Summe) und Anwesenheitsquote je Slot – ohne Kontextbereinigung."""
    x = d[d["hauptstichprobe"] & d["anstoss_slot"].notna()]
    rows = []
    for s, g in x.groupby("anstoss_slot"):
        c = g.dropna(subset=["kf_exkl", "public_netto"])
        a = g.dropna(subset=["soll", "ist"])
        rows.append({"anstoss_slot": s, "spiele": len(g),
                     "kf_exkl_summe_summe": (c["kf_exkl"] * c["public_netto"]).sum() / c["public_netto"].sum() if len(c) else np.nan,
                     "anwesenheitsquote_summe_summe": a["ist"].sum() / a["soll"].sum() if len(a) else np.nan,
                     "saisons": ", ".join(sorted(g["saison"].unique()))})
    return pd.DataFrame(rows).sort_values("spiele", ascending=False)


def chf_baustein(effekte: pd.DataFrame, d: pd.DataFrame, saison: str = "2025/26") -> pd.DataFrame:
    """Isolierter Konsum-Baustein je Slot und Spiel: KF-Effekt × Ø KF × Ø Public-Anwesende der Referenzsaison.

    Nur der Konsumeffekt bei gleicher Besucherzahl; Anwesenheitseffekt separat (Prozentpunkte), nicht addieren.
    """
    x = d[d["hauptstichprobe"] & (d["saison"] == saison)].dropna(subset=["kf_exkl", "public_netto"])
    kf = (x["kf_exkl"] * x["public_netto"]).sum() / x["public_netto"].sum()
    pub = x["public_netto"].mean()
    e = effekte[(effekte["variante"].str.startswith("Run 4")) & (effekte["zielgroesse"] == models.ZIELE["kf_exkl"]["label"])
                & effekte["variable"].str.contains("vs. Samstag")]
    out = e[["variable", "effekt", "ki95_unten", "ki95_oben", "spiele_mit_merkmal"]].copy()
    for c in ("effekt", "ki95_unten", "ki95_oben"):
        out[f"chf_je_spiel_{c}"] = out[c] / 100 * kf * pub
    out["basis"] = f"Ø KF exkl. MwSt {kf:.2f} × Ø {pub:,.0f} Public-Anwesende".replace(",", "'") + f" ({saison}, Meisterschaft)"
    out["lesart"] = ("Umsatzunterschied je Spiel gegenüber Samstag 17–19.59 Uhr bei gleicher Besucherzahl; "
                     "Zusammenhang, kein Kausalnachweis; Anstoss ist für den Club extern (Liga/TV).")
    return out.reset_index(drop=True)

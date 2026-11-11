"""Gegenprobe: Erklären Tabellenstand und Form (FCSG und Gegner) zusätzlich zum Run-4-Kontext Anwesenheit und Konsum?

    python scripts/gegenprobe_tabellenstand.py [--ausgabe <Ordner>]

Gleiche Stichprobe und Schätzung wie das Hauptmodell (models.kontextmodelle: Meisterschaft ab 2022/23, OLS mit
Saisoneffekten, HC3). Je Variante kommt ein Merkmal zu den Run-4-Variablen dazu. Vergleich auf identischer Stichprobe:
Koeffizient mit 95 %-KI, Zuwachs der erklärten Streuung innerhalb Saison und Vorhersagefehler an ausgelassenen Saisons
(LOSO). Merkmale vor dem Spiel aus den öffentlichen Resultaten (fcsg/sources/extern.tabelle_vor_spielen). Nur Aggregate.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd
import statsmodels.formula.api as smf

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from fcsg import config  # noqa: E402
from fcsg.analysis import arrival, attendance, baseline, catering, models  # noqa: E402
from fcsg.datamodel import baue_modell  # noqa: E402
from fcsg.pipeline import lade_rohdaten  # noqa: E402

MERKMALE = {
    "ppg_fcsg_gestuetzt": "FCSG Punkte/Spiel vor dem Spiel (gestützt)",
    "rang_fcsg": "FCSG Tabellenrang vor dem Spiel (1 = Leader)",
    "form5_fcsg_punkte": "FCSG Form: Punkte aus den letzten 5 Spielen",
    "ppg_gegner_gestuetzt": "Gegner Punkte/Spiel vor dem Spiel (zusätzlich zu Top-Gegner)",
    "rang_gegner": "Gegner Tabellenrang vor dem Spiel",
    "form5_gegner_punkte": "Gegner Form: Punkte aus den letzten 5 Spielen",
}
ZIELE = ["anwesenheitsquote", "kf_exkl", "bons_pro_anwesende", "bon_exkl"]


def modell_daten() -> pd.DataFrame:
    r = lade_rohdaten()
    m = baue_modell(r)
    res: dict = {}
    res.update(baseline.baseline(r, m))
    k = res["spiel_kpi"]
    res.update(attendance.anwesenheit(r, m, k))
    res.update(catering.catering(r, m, k))
    res.update(arrival.ankunft(r, m, k, res["scan_ist"]))
    d = models.modell_daten(k, m.dim_match_context, res["ankunft_je_spiel"])
    extra = [c for c in MERKMALE if c not in d.columns]
    return d.merge(m.dim_match_context[["match_id", *extra]], on="match_id", how="left")


def r2_innerhalb(x: pd.DataFrame, preds: list[str]) -> float:
    fit = smf.ols("y ~ " + " + ".join(preds + ["C(saison)"]), data=x).fit()
    nur_saison = smf.ols("y ~ C(saison)", data=x).fit()
    return 1 - fit.ssr / nur_saison.ssr


def gegenprobe(d: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for ziel in ZIELE:
        alle = models.HAUPT + list(MERKMALE)
        x = models._stichprobe(d, ziel, alle)          # identische Stichprobe für alle Varianten
        _, basis = models.loso(x, models.HAUPT)
        r2_basis = r2_innerhalb(x, models.HAUPT)
        rows.append({"zielgroesse": models.ZIELE[ziel]["label"], "merkmal": "Run-4-Modell (Basis)", "spiele": len(x),
                     "r2_innerhalb_saison": r2_basis, "loso_verbesserung_pct": basis.get("verbesserung_loso_pct")})
        for var, lab in MERKMALE.items():
            preds = models.HAUPT + [var]
            fit = models._fit(x, preds)
            _, g = models.loso(x, preds)
            lo, hi = fit.conf_int().loc[var]
            rows.append({"zielgroesse": models.ZIELE[ziel]["label"], "merkmal": lab, "spiele": len(x),
                         "koeffizient": fit.params[var], "ki95_unten": lo, "ki95_oben": hi, "p_wert": fit.pvalues[var],
                         "r2_innerhalb_saison": r2_innerhalb(x, preds),
                         "r2_zuwachs_pp": (r2_innerhalb(x, preds) - r2_basis) * 100,
                         "loso_verbesserung_pct": g.get("verbesserung_loso_pct"),
                         "loso_aenderung_pp": g.get("verbesserung_loso_pct", float("nan")) - basis.get("verbesserung_loso_pct", float("nan")),
                         "belastbar": bool(lo > 0 or hi < 0)})
    return pd.DataFrame(rows)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--ausgabe", type=Path, default=None, help="Ordner für gegenprobe_tabellenstand.csv")
    a = ap.parse_args()
    config.setze_datenpfade(None, None)
    t = gegenprobe(modell_daten())
    pd.set_option("display.width", 220)
    print(t.round(4).to_string(index=False))
    if a.ausgabe:
        a.ausgabe.mkdir(parents=True, exist_ok=True)
        t.to_csv(a.ausgabe / "gegenprobe_tabellenstand.csv", index=False, encoding="utf-8-sig")
    return 0


if __name__ == "__main__":
    sys.exit(main())

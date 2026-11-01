"""Paket D – Ankunft (Pflicht deskriptiv; Modell optional).

Grundlage ist der erste erlaubte Drehkreuz-Durchgang je Ticket und Spiel. Ankunftskennzahlen werden
nur für Spiele mit vollständiger Zutrittslieferung (Scans ≥ 90 % des IST) berechnet. Ankunft → Konsum
wird ausschliesslich als Zusammenhang aggregierter Spiele ausgewiesen (keine Bon-Zeitstempel, keine
Verbindung Person–Kauf).
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import statsmodels.formula.api as smf

from .. import config
from ..datamodel import Modell, Rohdaten
from ..log import befund

KURVE_MINUTEN = np.arange(-180, 35, 5)    # negativ = vor Anpfiff


def _ankunft_mit_anpfiff(r: Rohdaten, m: Modell, voll: set[str]) -> pd.DataFrame:
    a = r.ankuenfte.merge(m.dim_match[["datum", "match_id", "anpfiff_ts"]], on="datum", how="inner")
    a = a[a["match_id"].isin(voll) & a["anpfiff_ts"].notna()].copy()
    a["min_vor_anpfiff"] = (a["anpfiff_ts"] - a["ts"]).dt.total_seconds() / 60
    return a


def _kennzahlen(x: pd.Series) -> dict:
    v = x.to_numpy()
    return {"median_min_vor_anpfiff": float(np.median(v)), "mittel_min_vor_anpfiff": float(v.mean()),
            "p25_min": float(np.quantile(v, 0.25)), "p75_min": float(np.quantile(v, 0.75)),
            "anteil_ab_90_min": float((v >= 90).mean()), "anteil_ab_60_min": float((v >= 60).mean()),
            "anteil_ab_45_min": float((v >= config.ANKUNFT_FRUEH_MIN).mean()),
            "anteil_letzte_15_min_inkl_nach_anpfiff": float((v < config.ANKUNFT_SPAET_MIN).mean()),
            "anteil_letzte_15_min_vor_anpfiff": float(((v < config.ANKUNFT_SPAET_MIN) & (v >= 0)).mean()),
            "anteil_nach_anpfiff": float((v < 0).mean()),
            "einlass_1pct_min_vor_anpfiff": float(np.quantile(v, 0.99))}


def ankunft_je_spiel(a: pd.DataFrame, k: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for mid, g in a.groupby("match_id"):
        d = _kennzahlen(g["min_vor_anpfiff"])
        # nach Minute sortiert: bei Gleichstand gilt die Minute näher am Anpfiff (unabhängig von der pandas-Version)
        pro_min = g["min_vor_anpfiff"].round().value_counts().sort_index()
        d.update({"match_id": mid, "besucher_scans": len(g), "spitze_scans_pro_minute": int(pro_min.max()),
                  "spitze_min_vor_anpfiff": float(pro_min.idxmax()),
                  "anteil_hospitality_eingaenge": float((g["sektor"] == "HH (Hospitality)").mean()),
                  "anteil_chipkarte": float((g["kartentyp"] == "Chipkarte").mean()), "leser_aktiv": g["leser"].nunique()})
        rows.append(d)
    out = pd.DataFrame(rows).merge(k[["match_id", "datum", "saison", "wettbewerb", "gegner_anzeige", "anpfiff",
                                      "wochentag", "anpfiff_slot", "abendspiel", "wochenende"]], on="match_id")
    out["anpfiff_plausibel"] = out["median_min_vor_anpfiff"].between(0, 120)
    for _, row in out[~out["anpfiff_plausibel"]].iterrows():
        befund("Zutritt", "hoch", f"{row['datum']:%d.%m.%Y}", f"Median der Ankunft {row['median_min_vor_anpfiff']:.0f} min vor "
               f"Anpfiff {row['anpfiff']} – Anpfiffzeit vermutlich falsch.", "Ankunftskennzahlen verzerrt.", "Anpfiff prüfen.")
    return out.sort_values("datum").reset_index(drop=True)


def ankunft_je_sektor(a: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for (mid, sek), g in a.groupby(["match_id", "sektor"]):
        d = _kennzahlen(g["min_vor_anpfiff"]) if len(g) >= config.MIN_ZELLE else {}
        rows.append({"match_id": mid, "sektor": sek, "besucher_scans": len(g), **d})
    return pd.DataFrame(rows)


def ankunftskurven(a: pd.DataFrame, k: pd.DataFrame) -> dict[str, pd.DataFrame]:
    """Kumulierte Ankunftsanteile je Spiel und Durchschnittskurven je Sektor/Anstosszeit."""
    rows = []
    for (mid, sek), g in pd.concat([a.assign(sektor="Alle"), a]).groupby(["match_id", "sektor"]):
        v = np.sort(-g["min_vor_anpfiff"].to_numpy())          # Minuten relativ zum Anpfiff
        anteil = np.searchsorted(v, KURVE_MINUTEN, side="right") / len(v)
        rows.append(pd.DataFrame({"match_id": mid, "sektor": sek, "minute_relativ": KURVE_MINUTEN,
                                  "anteil_angekommen": anteil, "n": len(v)}))
    je_spiel = pd.concat(rows, ignore_index=True)
    je_spiel = je_spiel.merge(k[["match_id", "saison", "anpfiff_slot", "wettbewerb"]], on="match_id")
    mittel_sektor = je_spiel[je_spiel["n"] >= config.MIN_ZELLE].groupby(["sektor", "minute_relativ"]).agg(
        anteil_mittel=("anteil_angekommen", "mean"), spiele=("match_id", "nunique")).reset_index()
    mittel_slot = je_spiel[je_spiel["sektor"] == "Alle"].groupby(["anpfiff_slot", "minute_relativ"]).agg(
        anteil_mittel=("anteil_angekommen", "mean"), spiele=("match_id", "nunique")).reset_index()
    return {"ankunftskurven_je_spiel": je_spiel, "ankunftskurve_sektor": mittel_sektor,
            "ankunftskurve_anstosszeit": mittel_slot}


def leserabdeckung(r: Rohdaten, m: Modell, voll: set[str]) -> pd.DataFrame:
    """Aktive Leser je Saison, nur Spiele mit vollständiger Zutrittslieferung."""
    a = r.ankuenfte.merge(m.dim_match[["datum", "match_id", "saison"]], on="datum", how="inner")
    a = a[a["match_id"].isin(voll)]
    akt = a.groupby(["saison", "match_id", "leser"]).size().rename("scans").reset_index()
    spiele = akt.groupby("saison")["match_id"].nunique()
    rows = []
    for (s, leser), g in akt.groupby(["saison", "leser"]):
        rows.append({"saison": s, "leser": leser, "spiele_aktiv": g["match_id"].nunique(), "spiele_saison": spiele[s],
                     "scans_mittel_wenn_aktiv": g["scans"].mean()})
    out = pd.DataFrame(rows)
    out["anteil_spiele_aktiv"] = out["spiele_aktiv"] / out["spiele_saison"]
    out["hinweis"] = np.where(out["leser"].str.startswith("B4") & (out["anteil_spiele_aktiv"] < 1),
                              "Gästesektor-Leser: bei kleinen Gästekontingenten nur teilweise geöffnet", "")
    return out.sort_values(["saison", "leser"]).reset_index(drop=True)


def ankunft_konsum(je_spiel: pd.DataFrame, k: pd.DataFrame, ctx: pd.DataFrame) -> pd.DataFrame:
    d = je_spiel.merge(k[["match_id", "bons_pro_anwesende", "kf_exkl", "bon_exkl", "spielstatus", "top_gegner"]],
                       on="match_id").merge(ctx[["match_id", "temp_anpfiff_c"]], on="match_id", how="left")
    d = d[d["wettbewerb"].isin(config.KERN_WETTBEWERBE) & d["bons_pro_anwesende"].notna()].copy()
    d["frueh_10pp"] = d["anteil_ab_45_min"] * 10          # Effekt je +10 Prozentpunkte Frühankommende
    rows = []
    for ziel, label in [("bons_pro_anwesende", "Bons je Public-Anwesendem"), ("kf_exkl", "Kundenfranken exkl. MwSt"),
                        ("bon_exkl", "Ø Bon exkl. MwSt")]:
        d[f"ln_{ziel}"] = np.log(d[ziel])
        for spez, formel in [("nur Saisoneffekte", f"ln_{ziel} ~ frueh_10pp + C(saison)"),
                             ("plus Kontext (Abend, Wochentag, Temperatur, Top-Gegner)",
                              f"ln_{ziel} ~ frueh_10pp + C(saison) + abendspiel + wochenende + temp_anpfiff_c + top_gegner")]:
            x = d.dropna(subset=["temp_anpfiff_c"]).astype({"abendspiel": float, "wochenende": float, "top_gegner": float})
            fit = smf.ols(formel, data=x).fit(cov_type="HC3")
            b, se = fit.params["frueh_10pp"], fit.bse["frueh_10pp"]
            dm = x.assign(a=x["anteil_ab_45_min"] - x.groupby("saison")["anteil_ab_45_min"].transform("mean"),
                          z=x[ziel] - x.groupby("saison")[ziel].transform("mean"))
            rows.append({"zielgroesse": label, "spezifikation": spez, "spiele": int(fit.nobs),
                         "korrelation_innerhalb_saison": dm["a"].corr(dm["z"]),
                         "effekt_pct_je_10pp_frueh": (np.exp(b) - 1) * 100,
                         "ki95_unten_pct": (np.exp(b - 1.96 * se) - 1) * 100, "ki95_oben_pct": (np.exp(b + 1.96 * se) - 1) * 100,
                         "p_wert": float(fit.pvalues["frueh_10pp"]),
                         "lesart": "Zusammenhang über Spiele (aggregiert), keine Kausalität: frühe Ankunft und Konsum "
                                   "können gemeinsam von Stimmung, Wetter oder Gegner abhängen."})
    return pd.DataFrame(rows)


def einlass_je_eingang(je_sektor: pd.DataFrame) -> pd.DataFrame:
    """Geschätzte Toröffnung je Eingang: Zeitpunkt, an dem 1 % der Besucher dieses Eingangs drin sind."""
    d = je_sektor.dropna(subset=["einlass_1pct_min_vor_anpfiff"])
    out = d.groupby("sektor").agg(
        spiele=("match_id", "nunique"), einlass_1pct_median=("einlass_1pct_min_vor_anpfiff", "median"),
        einlass_1pct_p25=("einlass_1pct_min_vor_anpfiff", lambda x: x.quantile(0.25)),
        einlass_1pct_p75=("einlass_1pct_min_vor_anpfiff", lambda x: x.quantile(0.75)),
        ankunft_median=("median_min_vor_anpfiff", "median"), anteil_ab_45_min=("anteil_ab_45_min", "median"),
        besucher_mittel=("besucher_scans", "mean")).reset_index()
    out["konsumfenster_vor_anpfiff_min"] = out["einlass_1pct_median"]
    out["lesart"] = ("Einlass-Beginn (1 %-Punkt) als Näherung der Toröffnung; die Ankunftskurven steigen genau ab diesem "
                     "Zeitpunkt steil an – die Toröffnung ist der Auslöser, nicht das Spiel.")
    return out.sort_values("einlass_1pct_median", ascending=False).reset_index(drop=True)


def reto_ankunft(je_spiel: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for name, x in [("Retos Stichprobe: 25/26 + 26/27 (alle Kernspiele)", je_spiel[je_spiel["saison"] >= "2025/26"]),
                    ("Alle vollständigen Spiele 22/23–26/27", je_spiel)]:
        rows.append({"stichprobe": name, "spiele": len(x),
                     "median_min_vor_anpfiff_mittel": x["median_min_vor_anpfiff"].mean(),
                     "anteil_ab_45_min_mittel": x["anteil_ab_45_min"].mean(),
                     "anteil_letzte_15_min_inkl_nach_anpfiff_mittel": x["anteil_letzte_15_min_inkl_nach_anpfiff"].mean(),
                     "anteil_nach_anpfiff_mittel": x["anteil_nach_anpfiff"].mean(),
                     "einlass_1pct_min_vor_anpfiff_median": x["einlass_1pct_min_vor_anpfiff"].median()})
    return pd.DataFrame(rows)


def ankunft(r: Rohdaten, m: Modell, k: pd.DataFrame, scan_ist: pd.DataFrame) -> dict[str, pd.DataFrame]:
    voll = set(scan_ist.loc[scan_ist["zutritt_vollstaendig"] & scan_ist["wettbewerb"].isin(config.KERN_WETTBEWERBE),
                            "match_id"])
    a = _ankunft_mit_anpfiff(r, m, voll)
    je_spiel = ankunft_je_spiel(a, k)
    out = {"ankunft_je_spiel": je_spiel, "ankunft_je_sektor": ankunft_je_sektor(a),
           "leserabdeckung": leserabdeckung(r, m, voll), "ankunft_konsum": ankunft_konsum(je_spiel, k, m.dim_match_context),
           "ankunft_reto": reto_ankunft(je_spiel)}
    out.update(ankunftskurven(a, k))
    out["einlass_je_eingang"] = einlass_je_eingang(out["ankunft_je_sektor"])
    ein = out["einlass_je_eingang"].set_index("sektor")["einlass_1pct_median"]
    befund("Zutritt", "info", "Toröffnung je Eingang (aus Scans geschätzt)",
           "Einlass-Beginn (1 %-Punkt) im Median: " + ", ".join(f"{s_}: {v:.0f} min" for s_, v in ein.items()) + " vor Anpfiff.",
           "Das mögliche Konsumfenster vor Anpfiff ist je Eingang sehr unterschiedlich (Clubhebel Toröffnung/Programm).",
           "Toröffnungszeiten je Tor bei Sandro bestätigen lassen.")
    sek = out["ankunft_je_sektor"].dropna(subset=["median_min_vor_anpfiff"]).groupby("sektor")["median_min_vor_anpfiff"].median()
    befund("Zutritt", "info", "Ankunft nach Eingang",
           "Median der Ankunft (Minuten vor Anpfiff, Median über Spiele): " +
           ", ".join(f"{s}: {v:.0f}" for s, v in sek.sort_values(ascending=False).items()) + ".",
           "Zeitfenster für Konsum vor Anpfiff unterscheidet sich je Eingang.",
           "Sektor = physischer Eingang (Lesername), nicht Sitzplatz; Seatinfo wird nicht verwendet.")
    return out


TOROEFFNUNG_D_AB = pd.Timestamp("2023-04-02")   # Catering-Bemerkung: «Sektor D und B4: Türöffnung 1.5h vor Spielbeginn»


def toroeffnung_experiment(je_sektor: pd.DataFrame, k: pd.DataFrame, diagnose_lang: pd.DataFrame) -> dict[str, pd.DataFrame]:
    """Natürliches Experiment: Sektor D öffnet ab 02.04.2023 rund 30 min früher (A/B/C unverändert).

    Differenz-in-Differenzen innerhalb derselben Spiele: Spiel-Effekte (Wetter, Gegner, Anpfiff) und
    Sektor-Effekte werden kontrolliert; der Koeffizient D × nachher misst die Verschiebung der Ankunft
    in D gegenüber A/B/C. Standardfehler geclustert nach Spiel.
    """
    d = je_sektor[je_sektor["sektor"].isin(["A", "B", "C", "D"])].dropna(subset=["median_min_vor_anpfiff"])
    d = d.merge(k[["match_id", "datum", "saison"]], on="match_id")
    d["nachher"] = (d["datum"] >= TOROEFFNUNG_D_AB).astype(float)
    d["sektor_d"] = (d["sektor"] == "D").astype(float)
    d["d_x_nachher"] = d["sektor_d"] * d["nachher"]
    rows = []
    for ziel, label in [("einlass_1pct_min_vor_anpfiff", "Einlass-Beginn (1 %-Punkt), min vor Anpfiff"),
                        ("median_min_vor_anpfiff", "Median Ankunft, min vor Anpfiff"),
                        ("anteil_ab_60_min", "Anteil Ankunft ≥ 60 min vor Anpfiff"),
                        ("anteil_ab_45_min", "Anteil Ankunft ≥ 45 min vor Anpfiff")]:
        fit = smf.ols(f"{ziel} ~ C(sektor) + C(match_id) + d_x_nachher", data=d).fit(
            cov_type="cluster", cov_kwds={"groups": pd.factorize(d["match_id"])[0]})
        b, se = fit.params["d_x_nachher"], fit.bse["d_x_nachher"]
        mittel = d.groupby(["sektor_d", "nachher"])[ziel].mean()
        rows.append({"zielgroesse": label, "D_vorher": mittel.get((1.0, 0.0)), "D_nachher": mittel.get((1.0, 1.0)),
                     "ABC_vorher": mittel.get((0.0, 0.0)), "ABC_nachher": mittel.get((0.0, 1.0)),
                     "did_effekt": b, "ki95_unten": b - 1.96 * se, "ki95_oben": b + 1.96 * se,
                     "p_wert": float(fit.pvalues["d_x_nachher"]),
                     "spiele_vorher": int(d.loc[d["nachher"] == 0, "match_id"].nunique()),
                     "spiele_nachher": int(d.loc[d["nachher"] == 1, "match_id"].nunique())})
    did = pd.DataFrame(rows)
    did["lesart"] = ("Verschiebung in Sektor D relativ zu A/B/C bei denselben Spielen (Differenz-in-Differenzen). "
                     "Zeigt die Wirkung der Toröffnung auf die ANKUNFT – nicht auf den Konsum (kein Stand→Sektor-Mapping).")

    # Konsum auf Spielebene: KF-Abweichung von der Kontexterwartung innerhalb 2022/23 vor/nach der Umstellung
    kf = diagnose_lang[diagnose_lang["ziel_code"] == "kf_exkl"].merge(k[["match_id", "datum", "saison"]], on="match_id")
    kf = kf[kf["saison"] == "2022/23"].assign(abw_pct=lambda x: (x["beobachtet"] / x["erwartet"] - 1) * 100)
    rng = np.random.default_rng(1879)
    konsum = []
    for nach, g in kf.groupby(kf["datum"] >= TOROEFFNUNG_D_AB):
        v = g["abw_pct"].to_numpy()
        boot = [rng.choice(v, len(v)).mean() for _ in range(2000)] if len(v) else [np.nan]
        konsum.append({"phase_2022_23": "ab 02.04.2023 (D öffnet 90 min vorher)" if nach else "bis März 2023 (D öffnet 60 min vorher)",
                       "spiele": len(v), "kf_abweichung_von_erwartung_pct": v.mean() if len(v) else np.nan,
                       "ki90_unten": np.quantile(boot, 0.05), "ki90_oben": np.quantile(boot, 0.95)})
    konsum = pd.DataFrame(konsum)
    konsum["lesart"] = ("Nur 2022/23 enthält Spiele vor und nach der Umstellung; sehr kleine Stichprobe, Saisonphase "
                        "(Frühling) nicht vollständig kontrolliert → kein belastbarer Konsumnachweis.")
    verlauf = d[d["sektor"].isin(["A", "C", "D"])][["datum", "saison", "sektor", "einlass_1pct_min_vor_anpfiff",
                                                     "median_min_vor_anpfiff", "anteil_ab_60_min"]].sort_values("datum")
    return {"toroeffnung_did": did, "toroeffnung_konsum": konsum, "toroeffnung_verlauf": verlauf}

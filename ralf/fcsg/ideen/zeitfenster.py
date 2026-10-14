"""Zeitfenster vor Anpfiff: Verweilminuten, späte Ankünfte und Einlass-Spitzen je Eingang (nur vollständige Lieferungen).

Grundlage: erster erlaubter Scan je Ticket und Spiel (ohne IDs). Eingang = physischer Leser (A, B, B4 Gäste, C, D, HH).
Ohne Catering-Zeitstempel ist offen, ob mehr Verweilzeit mehr Konsum bringt (Hypothese, nicht belegt).
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from .. import config

EINGAENGE = ["A", "B", "C", "D", "B4 (Gäste)", "HH (Hospitality)"]


def _ankuenfte(r, m, res: dict) -> pd.DataFrame:
    s = res["scan_ist"]
    voll = set(s.loc[s["zutritt_vollstaendig"] & s["wettbewerb"].isin(config.KERN_WETTBEWERBE), "match_id"])
    a = r.ankuenfte.merge(m.dim_match[["datum", "match_id", "anpfiff_ts", "saison", "wettbewerb", "anpfiff_slot",
                                       "wochentag_typ", "abendspiel"]], on="datum", how="inner")
    a = a[a["match_id"].isin(voll) & a["anpfiff_ts"].notna()].copy()
    a["min_vor_anpfiff"] = (a["anpfiff_ts"] - a["ts"]).dt.total_seconds() / 60
    a["verweil_min"] = a["min_vor_anpfiff"].clip(lower=0)
    return a


def verweilzeit(a: pd.DataFrame, ctx: pd.DataFrame) -> dict[str, pd.DataFrame]:
    g = a.groupby(["match_id", "sektor"]).agg(
        besucher=("verweil_min", "size"), verweil_mittel=("verweil_min", "mean"), verweil_median=("verweil_min", "median"),
        anteil_nach_anpfiff=("min_vor_anpfiff", lambda x: (x < 0).mean()),
        anteil_letzte_15_min=("min_vor_anpfiff", lambda x: ((x >= 0) & (x < 15)).mean()),
        anteil_ab_60_min=("min_vor_anpfiff", lambda x: (x >= 60).mean()),
        besucher_minuten=("verweil_min", "sum")).reset_index()
    g = g[g["besucher"] >= config.MIN_ZELLE]
    info = a.drop_duplicates("match_id")[["match_id", "saison", "wettbewerb", "anpfiff_slot", "wochentag_typ", "abendspiel"]]
    g = g.merge(info, on="match_id").merge(ctx[["match_id", "temp_anpfiff_c"]], on="match_id", how="left")
    je_eingang = g.groupby("sektor").agg(spiele=("match_id", "nunique"), besucher_je_spiel=("besucher", "mean"),
                                         verweil_mittel=("verweil_mittel", "median"), verweil_median=("verweil_median", "median"),
                                         anteil_letzte_15_min=("anteil_letzte_15_min", "median"),
                                         anteil_nach_anpfiff=("anteil_nach_anpfiff", "median"),
                                         anteil_ab_60_min=("anteil_ab_60_min", "median"),
                                         besucher_minuten_je_spiel=("besucher_minuten", "mean")).reindex(EINGAENGE).dropna(how="all")
    je_eingang = je_eingang.reset_index()
    je_eingang["besucher_letzte_15_min_je_spiel"] = je_eingang["besucher_je_spiel"] * je_eingang["anteil_letzte_15_min"]
    je_eingang["lesart"] = ("Verweilminuten = Minuten zwischen Drehkreuz und Anpfiff (Ankunft nach Anpfiff = 0); Median über die "
                            "Spiele. Besucher-Minuten = Summe aller Minuten vor Anpfiff je Spiel und Eingang (Konsumfenster).")
    # Kontext: Spielebene (alle Eingänge), Abweichung vom Saisonmittel
    sp = a.groupby("match_id").agg(verweil_mittel=("verweil_min", "mean"),
                                   anteil_letzte_15=("min_vor_anpfiff", lambda x: ((x >= 0) & (x < 15)).mean()),
                                   anteil_nach_anpfiff=("min_vor_anpfiff", lambda x: (x < 0).mean())).reset_index()
    sp = sp.merge(info, on="match_id").merge(ctx[["match_id", "temp_anpfiff_c"]], on="match_id", how="left")
    sp["temperatur"] = pd.cut(sp["temp_anpfiff_c"], [-50, 5, 15, 50], labels=["unter 5 °C", "5–15 °C", "über 15 °C"]).astype(str)
    sp["verweil_dm"] = sp["verweil_mittel"] - sp.groupby("saison")["verweil_mittel"].transform("mean")
    rows = []
    for col, label in [("anpfiff_slot", "Anstosszeit"), ("wochentag_typ", "Wochentag"), ("temperatur", "Temperatur bei Anpfiff"),
                       ("wettbewerb", "Wettbewerb")]:
        for wert, x in sp.groupby(sp[col].astype(str)):
            if wert in ("nan", "None"):
                continue
            rows.append({"merkmal": label, "auspraegung": wert, "spiele": len(x), "verweil_mittel": x["verweil_mittel"].mean(),
                         "abweichung_vom_saisonmittel_min": x["verweil_dm"].mean(),
                         "anteil_letzte_15_min": x["anteil_letzte_15"].mean(), "anteil_nach_anpfiff": x["anteil_nach_anpfiff"].mean()})
    kontext = pd.DataFrame(rows)
    kontext["lesart"] = "Deskriptiv; Merkmale überlagern sich. Abweichung in Minuten gegenüber dem Saisonmittel."
    return {"verweilzeit_eingang": je_eingang, "verweilzeit_kontext": kontext, "verweilzeit_je_spiel_eingang": g}


def einlass_spitzen(a: pd.DataFrame) -> dict[str, pd.DataFrame]:
    """Scans pro Minute je Eingang und je Leser: Ist der Einlass vor Anpfiff ein Engpass?"""
    a = a.assign(minute=np.floor(a["min_vor_anpfiff"]))
    je_leser_min = a.groupby(["match_id", "leser", "minute"]).size().rename("scans").reset_index()
    kap = je_leser_min.groupby(["match_id", "leser"])["scans"].max()
    kap_p95 = float(kap.quantile(0.95))
    rows = []
    for (mid, sek), g in a.groupby(["match_id", "sektor"]):
        if len(g) < config.MIN_ZELLE:
            continue
        pm = g.groupby("minute").size()
        leser = g["leser"].nunique()
        vor = pm[(pm.index >= 0) & (pm.index < 30)]
        rows.append({"match_id": mid, "sektor": sek, "leser_aktiv": leser, "spitze_scans_pro_min": int(pm.max()),
                     "spitze_min_vor_anpfiff": float(pm.idxmax()), "spitze_je_leser": pm.max() / leser,
                     "mittel_letzte_30_min_je_leser": vor.mean() / leser if len(vor) else np.nan})
    df = pd.DataFrame(rows)
    out = df.groupby("sektor").agg(spiele=("match_id", "nunique"), leser_aktiv=("leser_aktiv", "median"),
                                   spitze_scans_pro_min=("spitze_scans_pro_min", "median"),
                                   spitze_min_vor_anpfiff=("spitze_min_vor_anpfiff", "median"),
                                   spitze_je_leser=("spitze_je_leser", "median"),
                                   mittel_letzte_30_min_je_leser=("mittel_letzte_30_min_je_leser", "median")).reindex(EINGAENGE)
    out = out.dropna(how="all").reset_index()
    out["leser_kapazitaet_p95"] = kap_p95
    out["auslastung_spitze"] = out["spitze_je_leser"] / kap_p95
    out["lesart"] = (f"Leser-Kapazität = 95 %-Quantil der höchsten Scans pro Minute eines Lesers über alle Spiele ({kap_p95:.0f}/min). "
                     "Auslastung der Spitze deutlich unter 1 → der Einlass ist im Mittel kein Engpass; spätes Kommen ist eher "
                     "Verhalten als Stau (Wartezeiten vor dem Drehkreuz sind nicht gemessen).")
    return {"einlass_spitzen": out, "einlass_spitzen_je_spiel": df}


def rechne(r, m, res: dict) -> dict[str, pd.DataFrame]:
    a = _ankuenfte(r, m, res)
    out = {}
    out.update(verweilzeit(a, m.dim_match_context))
    out.update(einlass_spitzen(a))
    did = res["toroeffnung_did"].copy()
    did["quelle"] = "Phase 1, Blatt D9 (Differenz-in-Differenzen Sektor D vs. A/B/C)"
    out["toroeffnung_beleg"] = did
    return out

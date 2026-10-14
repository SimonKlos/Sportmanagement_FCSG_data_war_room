"""Absatz: Spieltypen aus dem Einzelticket-Vorlauf, Frühindikator T-7 und Preisstruktur (deskriptiv).

* Spieltypen sind ausdrücklich KEIN Input für Preise (kein Dynamic Pricing) – sie dienen Planung und Ansprache.
* Der Frühindikator ist retrospektiv getestet (Rolling Origin: Training strikt mit früheren Spielen) und nutzt nur
  Merkmale, die 7 Tage vor dem Spiel bekannt sind (kein gemessenes Wetter).
* Einzeltickets ohne Abos und ohne Stornoverlauf (Endbestand) – keine Stadion-Ausverkaufskurve.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from scipy import stats
from scipy.cluster.hierarchy import fcluster, linkage

from .. import config

SEED = 1879
T_VORLAUF = 7


# --------------------------------------------------------------------------------------------
# Merkmale je Spiel
# --------------------------------------------------------------------------------------------
def spiel_merkmale(m, k: pd.DataFrame, ctx: pd.DataFrame) -> pd.DataFrame:
    """Einzelticket-Merkmale je Meisterschaftsspiel mit vollständigen Einzelticket-Daten."""
    voll = k[(k["wettbewerb"] == "SL") & (k["spielstatus"] == "gespielt") & k["einzeltickets_vollstaendig"].astype(bool)]
    t = m.tickets[m.tickets["match_id"].isin(voll["match_id"]) & (m.tickets["vorlauf_tage"] >= 0)].copy()
    t["zweitmarkt"] = t["tarif_roh"].astype(str).str.contains("Zweitmarkt", case=False)
    bez = t[~t["gratis"] & ~t["zweitmarkt"]]
    g_all = t[~t["zweitmarkt"]].groupby("match_id")
    g = bez.groupby("match_id")
    f = pd.DataFrame({
        "einzel_bezahlt": g.size(),
        "einzel_alle": g_all.size(),
        "einzel_bis_t7": t[~t["zweitmarkt"] & (t["vorlauf_tage"] >= T_VORLAUF)].groupby("match_id").size(),
        "anteil_letzte_7_tage": g["vorlauf_tage"].apply(lambda v: (v < T_VORLAUF).mean()),
        "anteil_spieltag": g["vorlauf_tage"].apply(lambda v: (v == 0).mean()),
        "anteil_gratis": g_all["gratis"].mean(),
    }).fillna({"einzel_bis_t7": 0}).reset_index()
    d = voll.merge(f, on="match_id", how="inner").merge(
        ctx[["match_id", "schulferien", "ppg_gegner_gestuetzt", "temp_anpfiff_c"]], on="match_id", how="left")
    d["ausverkauft"] = d["ausverkauft"].fillna(False).astype(bool)
    d["werktag"] = ~d["wochenende"].astype(bool)
    d["schulferien"] = d["schulferien"].astype("Float64").fillna(0).astype(float)
    d["anteil_t7_am_ist"] = d["einzel_bis_t7"] / d["ist"]
    # Lage innerhalb der Saison, nur unter nicht ausverkauften Spielen (ausverkaufte sind durch die Kapazität begrenzt)
    offen = ~d["ausverkauft"]
    for c in ("einzel_bezahlt", "anteil_letzte_7_tage"):
        g = d[offen].groupby("saison")[c]
        d[f"ueber_median_{c}"] = np.where(offen, d[c] > d["saison"].map(g.median()), np.nan)
        d[f"z_{c}"] = np.where(offen, (d[c] - d["saison"].map(g.mean())) / d["saison"].map(g.std(ddof=0)), np.nan)
    return d


# --------------------------------------------------------------------------------------------
# Spieltypen
# --------------------------------------------------------------------------------------------
TYPEN = {
    (True, False): "Starke, frühe Nachfrage",
    (True, True): "Starke, späte Nachfrage",
    (False, False): "Kernpublikum (wenig Laufkundschaft)",
    (False, True): "Spontanpublikum (spät, wenig)",
}
AUSVERKAUFT = "Ausverkauft (Absatz durch Kapazität begrenzt)"


def _typ(row) -> str:
    if row["ausverkauft"]:
        return AUSVERKAUFT
    return TYPEN[(bool(row["ueber_median_einzel_bezahlt"]), bool(row["ueber_median_anteil_letzte_7_tage"]))]


def _permutation_chi2(gruppen: np.ndarray, merkmal: np.ndarray, saisons: np.ndarray, n: int = 2000) -> float:
    """p-Wert der Chi²-Statistik (Spieltyp × Merkmal), Merkmal innerhalb jeder Saison permutiert (keine Zellgrössen-Annahme)."""
    def stat(mm):
        tab = pd.crosstab(gruppen, mm).to_numpy(float)
        erw = tab.sum(axis=1, keepdims=True) * tab.sum(axis=0, keepdims=True) / tab.sum()
        return float(((tab - erw) ** 2 / np.where(erw > 0, erw, 1)).sum())
    beob = stat(merkmal)
    rng = np.random.default_rng(SEED)
    zaehl = 0
    for _ in range(n):
        perm = merkmal.copy()
        for s in np.unique(saisons):
            idx = np.where(saisons == s)[0]
            perm[idx] = rng.permutation(perm[idx])
        zaehl += stat(perm) >= beob
    return (zaehl + 1) / (n + 1)


def _permutation_kruskal(werte: np.ndarray, gruppen: np.ndarray, saisons: np.ndarray, n: int = 2000) -> float:
    """p-Wert der Kruskal-Wallis-Statistik, Gruppen innerhalb jeder Saison permutiert (Saisonniveau bleibt erhalten)."""
    def stat(gr):
        teile = [werte[gr == u] for u in np.unique(gr) if (gr == u).sum() >= 2]
        return stats.kruskal(*teile).statistic if len(teile) >= 2 else 0.0
    beob = stat(gruppen)
    rng = np.random.default_rng(SEED)
    zaehl = 0
    for _ in range(n):
        perm = gruppen.copy()
        for s in np.unique(saisons):
            idx = np.where(saisons == s)[0]
            perm[idx] = rng.permutation(perm[idx])
        zaehl += stat(perm) >= beob
    return (zaehl + 1) / (n + 1)


def _ward_stabilitaet(x: np.ndarray, k: int, n_boot: int = 200) -> tuple[np.ndarray, float, float]:
    """Ward-Clustering und mittlere Bootstrap-Jaccard-Stabilität der Cluster (Hennig 2007)."""
    from scipy.spatial.distance import pdist, squareform
    basis = fcluster(linkage(x, "ward"), k, "maxclust")
    rng = np.random.default_rng(SEED)
    jacc = {c: [] for c in np.unique(basis)}
    for _ in range(n_boot):
        idx = np.unique(rng.integers(0, len(x), len(x)))
        if len(idx) <= k:
            continue
        lab = fcluster(linkage(x[idx], "ward"), k, "maxclust")
        for c in jacc:
            a = set(np.where(basis == c)[0])
            beste = 0.0
            for c2 in np.unique(lab):
                b_ = set(idx[lab == c2])
                a_ = a & set(idx)
                if a_:
                    beste = max(beste, len(a_ & b_) / len(a_ | b_))
            jacc[c].append(beste)
    mittel = {c: float(np.mean(v)) if v else np.nan for c, v in jacc.items()}
    d = squareform(pdist(x))
    sil = []
    for i in range(len(x)):
        same = basis == basis[i]
        a_i = d[i, same & (np.arange(len(x)) != i)].mean() if same.sum() > 1 else 0.0
        b_i = min(d[i, basis == c].mean() for c in np.unique(basis) if c != basis[i])
        sil.append((b_i - a_i) / max(a_i, b_i) if max(a_i, b_i) > 0 else 0.0)
    return basis, float(np.nanmin(list(mittel.values()))), float(np.mean(sil))


def spieltypen(d: pd.DataFrame) -> dict[str, pd.DataFrame]:
    x = d[d["saison"] >= config.MODELL_AB_SAISON].copy()
    x["spieltyp"] = x.apply(_typ, axis=1)
    rows = []
    for typ, g in x.groupby("spieltyp"):
        c = g.dropna(subset=["umsatz_exkl", "public_netto"])
        rows.append({"spieltyp": typ, "spiele": len(g), "noshow_quote": 1 - g["ist"].sum() / g["soll"].sum(),
                     "kf_exkl": c["umsatz_exkl"].sum() / c["public_netto"].sum(), "ist_mittel": g["ist"].mean(),
                     "einzel_bezahlt_mittel": g["einzel_bezahlt"].mean(), "anteil_letzte_7_tage": g["anteil_letzte_7_tage"].mean(),
                     "anteil_spieltag": g["anteil_spieltag"].mean(), "anteil_top_gegner": g["top_gegner"].astype(bool).mean(),
                     "anteil_werktag": g["werktag"].mean(), "anteil_abendspiel": g["abendspiel"].astype(bool).mean(),
                     "anteil_winter": g["winter"].astype(bool).mean(), "ppg_gegner_mittel": g["ppg_gegner_gestuetzt"].mean()})
    typen = pd.DataFrame(rows).sort_values("spiele", ascending=False)

    nicht_ausv = x[~x["ausverkauft"]]
    p_ppg = _permutation_kruskal(nicht_ausv["ppg_gegner_gestuetzt"].to_numpy(float), nicht_ausv["spieltyp"].to_numpy(),
                                 nicht_ausv["saison"].to_numpy())
    p_top = _permutation_chi2(x["spieltyp"].to_numpy(), x["top_gegner"].astype(bool).to_numpy(), x["saison"].to_numpy())
    p_noshow = _permutation_kruskal(nicht_ausv["noshow_quote"].to_numpy(float), nicht_ausv["spieltyp"].to_numpy(),
                                    nicht_ausv["saison"].to_numpy())
    p_abend = _permutation_chi2(nicht_ausv["spieltyp"].to_numpy(), nicht_ausv["abendspiel"].astype(bool).to_numpy(),
                                nicht_ausv["saison"].to_numpy())
    p_winter = _permutation_chi2(nicht_ausv["spieltyp"].to_numpy(), nicht_ausv["winter"].astype(bool).to_numpy(),
                                 nicht_ausv["saison"].to_numpy())
    tests = pd.DataFrame([
        {"test": "Spieltyp ~ Gegnerstärke (Punkte/Spiel vor dem Spiel), nicht ausverkaufte Spiele", "p_wert": p_ppg},
        {"test": "Spieltyp ~ Top-Gegner (FCB/YB/FCZ), alle Spiele inkl. ausverkaufte", "p_wert": p_top},
        {"test": "Spieltyp ~ Abendspiel (ab 20 Uhr), nicht ausverkaufte Spiele", "p_wert": p_abend},
        {"test": "Spieltyp ~ Winter (Nov–Feb), nicht ausverkaufte Spiele", "p_wert": p_winter},
        {"test": "No-Show-Quote unterscheidet sich zwischen Spieltypen, nicht ausverkaufte Spiele", "p_wert": p_noshow},
    ])
    tests["methode"] = "Permutationstest (2'000 Permutationen innerhalb jeder Saison; Kruskal-Wallis bzw. Chi²-Statistik)"
    tests["lesart"] = ("Kleiner p-Wert = Spieltyp hängt mit dem Merkmal zusammen. Spiegelt der Typ v.a. die Gegnerstärke, ist sein "
                       "Zusatznutzen klein (Retos eigener Test zu Idee 2).")

    # Robustheit: Ward-Clustering auf denselben (saisonstandardisierten) Merkmalen, nur nicht ausverkaufte Spiele
    feat = nicht_ausv[["z_einzel_bezahlt", "z_anteil_letzte_7_tage"]].to_numpy(float)
    rob = []
    for k_ in (2, 3, 4):
        lab, jac, sil = _ward_stabilitaet(feat, k_)
        ari = _adjusted_rand(lab, nicht_ausv["spieltyp"].to_numpy())
        rob.append({"k": k_, "silhouette": sil, "min_bootstrap_jaccard": jac, "stabil": jac >= 0.75,
                    "uebereinstimmung_mit_regeltypen_ari": ari})
    robust = pd.DataFrame(rob)
    robust["lesart"] = "Cluster gelten nur als stabil, wenn jeder Cluster im Bootstrap eine Jaccard-Ähnlichkeit ≥ 0.75 behält."
    zuordnung = x[["match_id", "datum", "saison", "gegner_anzeige", "spieltyp", "einzel_bezahlt", "anteil_letzte_7_tage",
                   "anteil_spieltag", "noshow_quote", "kf_exkl", "ausverkauft", "top_gegner", "wochentag_typ", "anpfiff_slot"]]
    return {"spieltypen": typen, "spieltypen_tests": tests, "spieltypen_robustheit": robust,
            "spieltypen_zuordnung": zuordnung.sort_values("datum").reset_index(drop=True)}


def _adjusted_rand(a: np.ndarray, b: np.ndarray) -> float:
    from math import comb
    tab = pd.crosstab(a, b).to_numpy()
    n = tab.sum()
    s_ij = sum(comb(int(v), 2) for v in tab.ravel())
    s_a = sum(comb(int(v), 2) for v in tab.sum(axis=1))
    s_b = sum(comb(int(v), 2) for v in tab.sum(axis=0))
    erw = s_a * s_b / comb(int(n), 2)
    maxi = (s_a + s_b) / 2
    return float((s_ij - erw) / (maxi - erw)) if maxi != erw else 0.0


# --------------------------------------------------------------------------------------------
# Frühindikator T-7
# --------------------------------------------------------------------------------------------
KONTEXT_T7 = ["top_gegner", "werktag", "abendspiel", "winter", "schulferien"]


def _design(x: pd.DataFrame, preds: list[str], saisons: list[str]) -> np.ndarray:
    cols = [np.ones(len(x))] + [x[p].astype(float).to_numpy() for p in preds]
    cols += [(x["saison_modell"] == s).astype(float).to_numpy() for s in saisons[1:]]
    return np.column_stack(cols)


def _rolling(d: pd.DataFrame, ziel: str, preds: list[str], min_train: int = 15, min_kalib: int = 10) -> pd.DataFrame:
    """Rolling-Origin-Vorhersage: für jedes Spiel nur frühere Spiele im Training; Saisonniveau aus der laufenden
    Saison (falls schon Spiele) bzw. der Vorsaison.

    80 %-Band konform kalibriert: 80 %-Quantil der absoluten Fehler aller früheren Rolling-Vorhersagen (ehrlicher als
    Trainingsresiduen, die den Fehler neuer Spiele unterschätzen). Ohne genügend frühere Fehler: kein Band.
    """
    d = d.sort_values("datum").reset_index(drop=True)
    out, fehler = [], []
    for i in range(len(d)):
        tr = d.iloc[:i]
        if len(tr) < min_train:
            continue
        te = d.iloc[[i]].copy()
        saisons = sorted(tr["saison"].unique())
        s_te = te["saison"].iloc[0]
        tr = tr.assign(saison_modell=tr["saison"])
        te["saison_modell"] = s_te if s_te in saisons else saisons[-1]
        X, y = _design(tr, preds, saisons), tr[ziel].to_numpy(float)
        beta, *_ = np.linalg.lstsq(X, y, rcond=None)
        pred = float((_design(te, preds, saisons) @ beta)[0])
        breite = float(np.quantile(np.abs(fehler), 0.80)) if len(fehler) >= min_kalib else np.nan
        beob = float(te[ziel].iloc[0])
        out.append({"match_id": te["match_id"].iloc[0], "datum": te["datum"].iloc[0], "beobachtet": beob,
                    "vorhersage": pred, "pi80_unten": pred - breite, "pi80_oben": pred + breite,
                    "training_bis": tr["datum"].max(), "ausverkauft": bool(te["ausverkauft"].iloc[0])})
        fehler.append(beob - pred)
    return pd.DataFrame(out)


def _saison_bis_dato(d: pd.DataFrame, ziel: str, min_train: int = 15) -> pd.DataFrame:
    d = d.sort_values("datum").reset_index(drop=True)
    out = []
    for i in range(min_train, len(d)):
        tr, te = d.iloc[:i], d.iloc[i]
        gleiche = tr[tr["saison"] == te["saison"]]
        basis = gleiche if len(gleiche) else tr[tr["saison"] == tr["saison"].iloc[-1]]
        out.append({"match_id": te["match_id"], "vorhersage_basis": float(basis[ziel].mean())})
    return pd.DataFrame(out)


def fruehindikator(d: pd.DataFrame) -> dict[str, pd.DataFrame]:
    x = d[d["saison"] >= config.MODELL_AB_SAISON].copy()
    x["log_einzel_t7"] = np.log1p(x["einzel_bis_t7"])
    for c in KONTEXT_T7:
        x[c] = x[c].astype(float)
    ergebnisse, vorhersagen = [], []
    for ziel, label, stichprobe in [
        ("ist", "IST (Anwesende)", x),
        ("noshow_quote", "No-Show-Quote (nur ticketbasiertes SOLL)", x[x["soll_ticketbasiert"].fillna(False).astype(bool)]),
    ]:
        s = stichprobe.dropna(subset=[ziel, "log_einzel_t7"])
        basis = _saison_bis_dato(s, ziel)
        m_ktx = _rolling(s, ziel, KONTEXT_T7)
        m_t7 = _rolling(s, ziel, KONTEXT_T7 + ["log_einzel_t7"])
        v = m_t7.merge(m_ktx[["match_id", "vorhersage"]].rename(columns={"vorhersage": "vorhersage_kontext"}), on="match_id")
        v = v.merge(basis, on="match_id")
        v["zielgroesse"] = label
        vorhersagen.append(v)
        for teil, vv in [("alle Testspiele", v), ("nicht ausverkauft", v[~v["ausverkauft"]]), ("ausverkauft", v[v["ausverkauft"]])]:
            if len(vv) < 5:
                continue
            mae_b = (vv["beobachtet"] - vv["vorhersage_basis"]).abs().mean()
            mae_k = (vv["beobachtet"] - vv["vorhersage_kontext"]).abs().mean()
            mae_t = (vv["beobachtet"] - vv["vorhersage"]).abs().mean()
            mb = vv.dropna(subset=["pi80_unten"])
            abdeckung = ((mb["beobachtet"] >= mb["pi80_unten"]) & (mb["beobachtet"] <= mb["pi80_oben"])).mean() if len(mb) else np.nan
            ergebnisse.append({"zielgroesse": label, "testspiele": teil, "n": len(vv), "mae_saison_bis_dato": mae_b,
                               "mae_kontext": mae_k, "mae_kontext_plus_t7": mae_t,
                               "verbesserung_gegen_kontext_pct": (1 - mae_t / mae_k) * 100,
                               "verbesserung_gegen_saisonmittel_pct": (1 - mae_t / mae_b) * 100,
                               "abdeckung_pi80": abdeckung, "spiele_mit_band": len(mb),
                               "erfolg_regel_10pct": bool((1 - mae_t / mae_k) * 100 >= 10)})
    erg = pd.DataFrame(ergebnisse)
    erg["lesart"] = ("Rolling Origin: jedes Spiel wird nur mit früheren Spielen vorhergesagt (retrospektiv getestet). Erfolg = MAE "
                     "mindestens 10 % tiefer als das reine Kontextmodell. Prädiktoren: nur bei T-7 bekannt (Gegner, Wochentag, "
                     "Anstosszeit, Winter, Schulferien) plus verkaufte Einzeltickets bis T-7.")
    korr = []
    for s, g in x.groupby("saison"):
        if len(g) >= 5:
            korr.append({"saison": s, "spiele": len(g), "r_t7_ist": g["log_einzel_t7"].corr(np.log(g["ist"])),
                         "r_t7_noshow": g["log_einzel_t7"].corr(g["noshow_quote"])})
    return {"fruehindikator": erg, "fruehindikator_vorhersagen": pd.concat(vorhersagen, ignore_index=True),
            "fruehindikator_korrelation": pd.DataFrame(korr)}


# --------------------------------------------------------------------------------------------
# Preisstruktur (deskriptiv, kein Preishebel)
# --------------------------------------------------------------------------------------------
def preisstruktur(r, m, k: pd.DataFrame) -> dict[str, pd.DataFrame]:
    sl = set(k.loc[(k["wettbewerb"] == "SL") & (k["spielstatus"] == "gespielt"), "match_id"])
    t = m.tickets[(m.tickets["quelle"] == "CSV") & m.tickets["match_id"].isin(sl)].copy()
    t["zweitmarkt"] = t["tarif_roh"].astype(str).str.contains("Zweitmarkt", case=False)
    rows = []
    for (s, tr), g in t.groupby(["saison", "tribuene"]):
        if len(g) < config.MIN_ZELLE:
            continue
        rows.append({"saison": s, "tribuene": tr, "einzeltickets": len(g), "spiele": g["match_id"].nunique(),
                     "einzeltickets_je_spiel": len(g) / g["match_id"].nunique(), "erloes_chf": g["preis"].sum(),
                     "preis_mittel_bezahlt": g.loc[~g["gratis"], "preis"].mean(), "anteil_gratis": g["gratis"].mean(),
                     "anteil_ermaessigt": (g["tarifgruppe"] == "Ermässigt").mean(), "anteil_zweitmarkt": g["zweitmarkt"].mean()})
    einzel = pd.DataFrame(rows)
    a = r.abos[(r.abos["team"] == "Herren") & (r.abos["tribuene"] != "Hospitality")]
    abo = a.groupby("tribuene").agg(abos=("preis", "size"), erloes_chf=("preis", "sum"),
                                    preis_mittel_bezahlt=("preis", lambda p: p[p > 0].mean()),
                                    anteil_gratis_sponsor=("preis", lambda p: (p == 0).mean())).reset_index()
    abo["stichtag"] = "Abo-Snapshot 30.09.2026 (ohne Hospitality-Abos)"
    gesamt = t.groupby("saison").agg(spiele=("match_id", "nunique"), einzeltickets=("preis", "size"),
                                     erloes_einzel_chf=("preis", "sum")).reset_index()
    gesamt["erloes_einzel_je_spiel"] = gesamt["erloes_einzel_chf"] / gesamt["spiele"]
    hinweis = "Preise laut Ticket-Export (CHF, inkl. allfälliger Gebühren); deskriptiv – Preise sind kein Hebel (kein Dynamic Pricing)."
    for df in (einzel, abo, gesamt):
        df["hinweis"] = hinweis
    return {"preis_einzel_tribuene": einzel, "preis_abo_tribuene": abo, "erloes_einzel_saison": gesamt}


def rechne(r, m, res: dict) -> dict[str, pd.DataFrame]:
    k = res["spiel_kpi"]
    d = spiel_merkmale(m, k, m.dim_match_context)
    out = {"absatz_merkmale": d[["match_id", "datum", "saison", "gegner_anzeige", "ausverkauft", "soll", "ist", "noshow_quote",
                                 "einzel_bezahlt", "einzel_alle", "einzel_bis_t7", "anteil_letzte_7_tage", "anteil_spieltag",
                                 "anteil_gratis", "anteil_t7_am_ist"]]}
    out.update(spieltypen(d))
    out.update(fruehindikator(d))
    out.update(preisstruktur(r, m, k))
    return out

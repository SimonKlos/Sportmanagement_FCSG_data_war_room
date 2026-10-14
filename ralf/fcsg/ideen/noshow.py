"""Leere bezahlte Plätze: Umfang, Kontext, Zweitmarkt, Tribünen 2026/27 und No-Show-Segmente der Einzeltickets.

Nur Aggregate. Tribünenwerte 2026/27 sind eine gekennzeichnete Näherung (Abo-Snapshot mit Kaufzeitpunkt, Einzeltickets,
Scans je Eingang); A und Hospitality sind wegen VIP-Gästen ausserhalb der Ticketdaten nicht identifiziert.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from .. import config

RNG_SEED = 1879
TRIBUENEN = ("B", "C", "D")
ZM_MUSTER = "Zweitmarkt"


def _sl(k: pd.DataFrame) -> pd.DataFrame:
    return k[(k["wettbewerb"] == "SL") & (k["spielstatus"] == "gespielt")].dropna(subset=["soll", "ist"])


# --------------------------------------------------------------------------------------------
# Umfang und Kontext
# --------------------------------------------------------------------------------------------
def leere_plaetze(k: pd.DataFrame, ctx: pd.DataFrame) -> dict[str, pd.DataFrame]:
    d = _sl(k).merge(ctx[["match_id", "schulferien", "temp_anpfiff_c"]], on="match_id", how="left").copy()
    d["leer"] = d["soll"] - d["ist"]
    d["ticketbasiert"] = d["soll_ticketbasiert"].fillna(False).astype(bool)
    saison = d.groupby("saison").agg(spiele=("match_id", "size"), leere_plaetze=("leer", "sum"),
                                     leere_plaetze_je_spiel=("leer", "mean"), soll=("soll", "sum"), ist=("ist", "sum"),
                                     spiele_ticketbasiert=("ticketbasiert", "sum")).reset_index()
    saison["noshow_quote"] = 1 - saison["ist"] / saison["soll"]
    tb = d[d["ticketbasiert"]].groupby("saison")["leer"].sum()
    saison["leere_plaetze_ticketbasiert"] = saison["saison"].map(tb)

    x = d[d["saison"].between(config.MODELL_AB_SAISON, "2025/26")].copy()
    x["temperatur"] = pd.cut(x["temp_anpfiff_c"], [-50, 5, 15, 50], labels=["unter 5 °C", "5–15 °C", "über 15 °C"]).astype(str)
    x["monat_name"] = x["datum"].dt.month.map({7: "Jul", 8: "Aug", 9: "Sep", 10: "Okt", 11: "Nov", 12: "Dez", 1: "Jan",
                                                2: "Feb", 3: "Mär", 4: "Apr", 5: "Mai", 6: "Jun"})
    n_saisons = x["saison"].nunique()
    rows = []
    for col, label in [("wochentag_typ", "Wochentag"), ("anpfiff_slot", "Anstosszeit"), ("winter", "Winter (Nov–Feb)"),
                       ("top_gegner", "Top-Gegner (FCB/YB/FCZ)"), ("ausverkauft", "Ausverkauft"),
                       ("temperatur", "Temperatur bei Anpfiff"), ("monat_name", "Monat")]:
        for wert, g in x.groupby(x[col].astype(str)):
            if wert in ("nan", "<NA>", "None"):
                continue
            rows.append({"merkmal": label, "auspraegung": wert.replace("True", "ja").replace("False", "nein"),
                         "spiele": len(g), "leere_plaetze_je_spiel": g["leer"].mean(),
                         "leere_plaetze_je_saison": g["leer"].sum() / n_saisons,
                         "noshow_quote": 1 - g["ist"].sum() / g["soll"].sum(),
                         "anteil_ticketbasiert": g["ticketbasiert"].mean()})
    kontext = pd.DataFrame(rows)
    kontext["basis"] = f"Meisterschaft {config.MODELL_AB_SAISON}–2025/26 ({n_saisons} Saisons); deskriptiv, Merkmale überlagern sich"
    return {"leere_plaetze_saison": saison, "leere_plaetze_kontext": kontext}


# --------------------------------------------------------------------------------------------
# Zweitmarkt
# --------------------------------------------------------------------------------------------
def _csv_tickets(m) -> pd.DataFrame:
    t = m.tickets[m.tickets["quelle"] == "CSV"].copy()
    t["zweitmarkt"] = t["tarif_roh"].astype(str).str.contains(ZM_MUSTER, case=False)
    return t


def zweitmarkt(m, k: pd.DataFrame) -> dict[str, pd.DataFrame]:
    t = _csv_tickets(m)
    zm = t[t["zweitmarkt"]]
    d = _sl(k)
    d = d[d["saison"] >= "2025/26"].copy()
    je_trib = zm.groupby(["match_id", "tribuene"]).size().unstack(fill_value=0)
    spiel = d[["match_id", "datum", "saison", "gegner_anzeige", "wochentag_typ", "anpfiff_slot", "ausverkauft", "soll", "ist",
               "zweitmarkt"]].rename(columns={"zweitmarkt": "zweitmarkt_historie"}).copy()
    spiel["leere_plaetze"] = spiel["soll"] - spiel["ist"]
    spiel["zweitmarkt_csv"] = spiel["match_id"].map(zm.groupby("match_id").size()).fillna(0).astype(int)
    spiel["zweitmarkt_anteil_soll"] = spiel["zweitmarkt_historie"] / spiel["soll"]
    spiel["wiederbesetzung_untergrenze"] = spiel["zweitmarkt_historie"] / (spiel["zweitmarkt_historie"] + spiel["leere_plaetze"])
    for tr in ("A", "B", "C", "D"):
        spiel[f"zweitmarkt_{tr}"] = spiel["match_id"].map(je_trib[tr]).fillna(0).astype(int) if tr in je_trib else 0

    rows = []
    for s, g in spiel.groupby("saison"):
        rows.append({"saison": s, "spiele": len(g), "zweitmarkt": g["zweitmarkt_historie"].sum(),
                     "leere_bezahlte_plaetze": g["leere_plaetze"].sum(),
                     "wiederbesetzung_untergrenze": g["zweitmarkt_historie"].sum() / (g["zweitmarkt_historie"].sum() + g["leere_plaetze"].sum()),
                     "zweitmarkt_je_spiel": g["zweitmarkt_historie"].mean(),
                     "zweitmarkt_ausverkauft_je_spiel": g.loc[g["ausverkauft"].fillna(False).astype(bool), "zweitmarkt_historie"].mean(),
                     "zweitmarkt_uebrige_je_spiel": g.loc[~g["ausverkauft"].fillna(False).astype(bool), "zweitmarkt_historie"].mean(),
                     **{f"anteil_tribuene_{tr}": g[f"zweitmarkt_{tr}"].sum() / g["zweitmarkt_historie"].sum() for tr in ("A", "B", "C", "D")},
                     "spiele_ohne_zweitmarkt_D": int((g["zweitmarkt_D"] == 0).sum()),
                     "csv_gleich_historie": bool((g["zweitmarkt_csv"] == g["zweitmarkt_historie"]).all())})
    saison = pd.DataFrame(rows)

    # Wann wird weiterverkauft? (Tage vor dem Spiel) und Preis gegenüber dem gleichen Tarif ohne Zweitmarkt
    zm_sl = zm[zm["match_id"].isin(spiel["match_id"])]
    v = zm_sl["vorlauf_tage"]
    vorlauf = pd.DataFrame([{"zweitmarkt_tickets": len(zm_sl), "vorlauf_median_tage": v.median(),
                             "anteil_am_spieltag": (v == 0).mean(), "anteil_letzte_2_tage": (v <= 2).mean(),
                             "anteil_ueber_7_tage": (v > 7).mean()}])
    # Aufpreis: Zweitmarkt-Ticket gegenüber dem gleichen Tarif ohne Zweitmarkt im selben Spiel (Preise ändern je Saison)
    t["tarif_basis"] = t["tarif_roh"].astype(str).str.replace(r"\s*Zweitmarkt\s*", "", regex=True, case=False).str.strip()
    p = t[t["match_id"].isin(spiel["match_id"])].groupby(["match_id", "tarif_basis", "zweitmarkt"])["preis"].agg(["size", "mean"])
    p = p.unstack("zweitmarkt").dropna()
    p.columns = [f"{a}_{'zm' if b else 'normal'}" for a, b in p.columns]
    p = p[p["mean_normal"] > 0].reset_index()
    zm_preis = p.groupby("tarif_basis").apply(lambda g: pd.Series({
        "zweitmarkt_tickets": g["size_zm"].sum(), "spiele": g["match_id"].nunique(),
        "preis_zweitmarkt": np.average(g["mean_zm"], weights=g["size_zm"]),
        "preis_ohne_zweitmarkt": np.average(g["mean_normal"], weights=g["size_zm"])}), include_groups=False)
    zm_preis["aufpreis_pct"] = (zm_preis["preis_zweitmarkt"] / zm_preis["preis_ohne_zweitmarkt"] - 1) * 100
    zm_preis = zm_preis[zm_preis["zweitmarkt_tickets"] >= config.MIN_ZELLE].sort_values("zweitmarkt_tickets", ascending=False)
    zm_preis = zm_preis.rename_axis("tarif")
    return {"zweitmarkt_je_spiel": spiel.sort_values("datum").reset_index(drop=True), "zweitmarkt_saison": saison,
            "zweitmarkt_vorlauf": vorlauf, "zweitmarkt_preis": zm_preis.reset_index()}


# --------------------------------------------------------------------------------------------
# Tribünen 2026/27
# --------------------------------------------------------------------------------------------
def _gruppe_ticket(tr: str) -> str:
    return "A + Hospitality" if tr in ("A", "Hospitality") else tr


def _gruppe_eingang(sek: str) -> str:
    return "A + Hospitality" if sek in ("A", "HH (Hospitality)") else sek


def einzelticket_anwesenheit_zks(res: dict) -> float:
    """Anwesenheitsquote der Einzeltickets in den validen ZKS-Spielen 2021/22–2022/23 (untere Annahme für r)."""
    z = res["zks_spiele"]
    z = z[z["zks_valide"]]
    return float(z["einzel_eingetreten"].sum() / z["einzel"].sum())


def abo_anwesenheit(scans, einzeltickets, abos, zweitmarkt, r):
    """Anwesenheit der Abo-Plätze = (Scans − r × Einzeltickets) / (Abos − Zweitmarkt), begrenzt auf [0, 1].

    Ein weiterverkaufter Abo-Platz zählt nur einmal: als Einzelticket des Käufers (Anwesenheit r), nicht als Abo.
    """
    return np.clip((scans - r * einzeltickets) / (abos - zweitmarkt), 0, 1)


def tribuene_2627(r, m, k: pd.DataFrame, res: dict) -> dict[str, pd.DataFrame]:
    spiele = k[(k["saison"] == "2026/27") & k["wettbewerb"].isin(["SL", "UEFA"]) & (k["spielstatus"] == "gespielt")]
    abos = r.abos[r.abos["team"] == "Herren"].copy()
    abos["gruppe"] = abos["tribuene"].map(_gruppe_ticket)
    abos["sonder"] = abos["tarifgruppe"].isin(["Sponsor/Dritte", "Mitarbeitende"]) | (abos["preis"].fillna(0) == 0)
    t = _csv_tickets(m)
    t["gruppe"] = t["tribuene"].map(_gruppe_ticket)
    a = r.ankuenfte.copy()
    a["gruppe"] = a["sektor"].map(_gruppe_eingang)
    rows = []
    for _, g in spiele.iterrows():
        ist_sl = g["wettbewerb"] == "SL"
        ab = abos[abos["verkauf_ts"] <= g["anpfiff_ts"]] if ist_sl else abos.iloc[0:0]
        ti = t[t["match_id"] == g["match_id"]]
        sc = a[a["datum"] == g["datum"]]
        for gruppe in ("B", "C", "D", "B4 (Gäste)", "A + Hospitality"):
            n_abo = int((ab["gruppe"] == gruppe).sum())
            n_sonder = int(((ab["gruppe"] == gruppe) & ab["sonder"]).sum())
            n_einzel = int((ti["gruppe"] == gruppe).sum())
            n_zm = int(((ti["gruppe"] == gruppe) & ti["zweitmarkt"]).sum())
            n_scan = int((sc["gruppe"] == gruppe).sum())
            plaetze = n_abo + n_einzel - n_zm
            rows.append({"match_id": g["match_id"], "datum": g["datum"], "wettbewerb": g["wettbewerb"], "gegner_anzeige": g["gegner_anzeige"],
                         "tribuene": gruppe, "abos_bis_anpfiff": n_abo, "abos_sponsor_ma_gratis": n_sonder, "einzeltickets": n_einzel,
                         "davon_zweitmarkt": n_zm, "plaetze_vergeben": plaetze, "scans_eingang": n_scan,
                         "scans_je_platz": n_scan / plaetze if plaetze else np.nan, "leere_plaetze": plaetze - n_scan,
                         "identifiziert": gruppe in TRIBUENEN or gruppe == "B4 (Gäste)"})
    df = pd.DataFrame(rows)

    # Kalibrierung: UEFA-Spiele (keine Abos gültig) zeigen die Anwesenheit von Einzeltickets je Tribüne
    uefa = df[df["wettbewerb"] == "UEFA"].groupby("tribuene")[["scans_eingang", "einzeltickets"]].sum()
    r_uefa = (uefa["scans_eingang"] / uefa["einzeltickets"]).to_dict()
    r_zks = einzelticket_anwesenheit_zks(res)
    sl = df[df["wettbewerb"] == "SL"].copy()
    sl["r_annahme_unten"] = [min(r_zks, r_uefa.get(tr, r_zks)) for tr in sl["tribuene"]]
    sl["r_annahme_oben"] = [max(r_zks, r_uefa.get(tr, r_zks)) for tr in sl["tribuene"]]
    for name in ("unten", "oben"):
        sl[f"abo_anwesenheit_bei_r_{name}"] = abo_anwesenheit(sl["scans_eingang"], sl["einzeltickets"], sl["abos_bis_anpfiff"],
                                                              sl["davon_zweitmarkt"], sl[f"r_annahme_{name}"])
    sl.loc[~sl["tribuene"].isin(TRIBUENEN), ["abo_anwesenheit_bei_r_unten", "abo_anwesenheit_bei_r_oben"]] = np.nan

    gesamt = sl.groupby("tribuene").agg(spiele=("match_id", "nunique"), abos=("abos_bis_anpfiff", "mean"),
                                        einzeltickets=("einzeltickets", "sum"), zweitmarkt=("davon_zweitmarkt", "sum"),
                                        plaetze=("plaetze_vergeben", "sum"), scans=("scans_eingang", "sum"),
                                        leere_plaetze=("leere_plaetze", "sum"), abos_summe=("abos_bis_anpfiff", "sum"),
                                        r_unten=("r_annahme_unten", "first"), r_oben=("r_annahme_oben", "first")).reset_index()
    gesamt["scans_je_platz"] = gesamt["scans"] / gesamt["plaetze"]
    gesamt["leere_plaetze_je_spiel"] = gesamt["leere_plaetze"] / gesamt["spiele"]
    for name in ("unten", "oben"):
        gesamt[f"abo_anwesenheit_bei_r_{name}"] = abo_anwesenheit(gesamt["scans"], gesamt["einzeltickets"], gesamt["abos_summe"],
                                                                  gesamt["zweitmarkt"], gesamt[f"r_{name}"])
    gesamt.loc[~gesamt["tribuene"].isin(TRIBUENEN), ["abo_anwesenheit_bei_r_unten", "abo_anwesenheit_bei_r_oben"]] = np.nan
    gesamt["einzel_anwesenheit_uefa"] = gesamt["tribuene"].map(r_uefa)
    gesamt["hinweis"] = np.select(
        [gesamt["tribuene"].isin(TRIBUENEN), gesamt["tribuene"] == "B4 (Gäste)"],
        ["Abo-Anwesenheit = (Scans − r × Einzeltickets) / (Abos − Zweitmarkt); r = Anwesenheit der Einzeltickets "
         "(unten: ZKS 21/22–22/23, oben: UEFA 26/27).",
         "Gästesektor: nur Einzeltickets; Scans je Ticket = Anwesenheit der Gäste-Tickets."],
        default="nicht identifiziert: Hospitality-/VIP-Gäste betreten über HH-Eingänge, sind aber teils nicht in den Ticketdaten.")
    gesamt["basis"] = "4 Meisterschaftsspiele 2026/27 (Juli–September, Sommerwetter) – Momentaufnahme, keine Saisonaussage"
    return {"tribuene_2627_je_spiel": df, "tribuene_2627": gesamt}


# --------------------------------------------------------------------------------------------
# No-Show der Einzeltickets nach Segment (ZKS 2021/22–2022/23)
# --------------------------------------------------------------------------------------------
def _bestellklasse(n: pd.Series) -> pd.Series:
    return pd.cut(n, [0, 1, 4, 9, 10_000], labels=["1", "2–4", "5–9", "10+"]).astype(str)


def einzel_noshow_segmente(m, res: dict, n_boot: int = 2000) -> pd.DataFrame:
    valide = set(res["zks_spiele"].loc[res["zks_spiele"]["zks_valide"], "match_id"])
    t = m.tickets[m.tickets["match_id"].isin(valide)].copy()
    t["noshow"] = t["eintritt_ts"].isna()
    t["preis_typ"] = np.where(t["gratis"], "gratis", "bezahlt")
    t["bestellung"] = _bestellklasse(t["bestellung_groesse"])
    t["kanal_kurz"] = t["kanal"].str.replace(r" \(.*\)", "", regex=True)
    total = t["noshow"].sum()
    rng = np.random.default_rng(RNG_SEED)
    spiele = np.array(sorted(valide))
    rows = []
    for (kanal, preis, best), g in t.groupby(["kanal_kurz", "preis_typ", "bestellung"]):
        if len(g) < config.MIN_ZELLE:
            continue
        je_spiel = g.groupby("match_id")["noshow"].agg(["size", "sum"]).reindex(spiele, fill_value=0)
        n, s_ = je_spiel["size"].to_numpy(), je_spiel["sum"].to_numpy()
        idx = rng.integers(0, len(spiele), size=(n_boot, len(spiele)))
        quoten = s_[idx].sum(axis=1) / np.maximum(n[idx].sum(axis=1), 1)
        rows.append({"kanal": kanal, "preis": preis, "tickets_pro_bestellung": best, "tickets": len(g),
                     "noshows": int(g["noshow"].sum()), "noshow_quote": g["noshow"].mean(),
                     "ki90_unten": np.quantile(quoten, 0.05), "ki90_oben": np.quantile(quoten, 0.95),
                     "anteil_an_allen_noshows": g["noshow"].sum() / total, "spiele": g["match_id"].nunique()})
    out = pd.DataFrame(rows).sort_values("noshows", ascending=False).reset_index(drop=True)
    out["kumuliert"] = out["anteil_an_allen_noshows"].cumsum()
    out["basis"] = (f"Einzeltickets der {len(valide)} Spiele 2021/22–2022/23 mit valider Eintrittserfassung (ZKS); 2021/22 COVID-geprägt; "
                    "KI90: Bootstrap über Spiele. Segmente < 10 Tickets unterdrückt.")
    return out


def rechne(r, m, res: dict) -> dict[str, pd.DataFrame]:
    k = res["spiel_kpi"]
    out = {}
    out.update(leere_plaetze(k, m.dim_match_context))
    out.update(zweitmarkt(m, k))
    out.update(tribuene_2627(r, m, k, res))
    out["einzel_noshow_segmente"] = einzel_noshow_segmente(m, res)
    return out

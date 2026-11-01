"""Paket A – Baseline und Qualitätsprüfung (Pflicht).

Saisonwerte werden immer als Summe/Summe gebildet (z.B. KF = Σ Umsatz / Σ Public-Anwesende), nicht als
ungewichteter Mittelwert der Spielwerte (Auftrag Paket A). Der ungewichtete Mittelwert wird nur zum
Vergleich mit der Caterer-Auswertung («Entwicklung») ausgewiesen.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from .. import config
from ..datamodel import Modell, Rohdaten
from ..log import befund
from ..utils import text, als_bool

KPI_AUSREISSER = ["noshow_quote", "kf_exkl", "bons_pro_anwesende", "bon_exkl"]


def zutritt_spiel(r: Rohdaten, m: Modell) -> pd.DataFrame:
    """Scans je Spiel inkl. Vollständigkeitsprüfung gegen IST."""
    z = r.zutritt_info.merge(m.dim_match[["datum", "match_id"]], on="datum", how="inner")
    z = z.merge(m.fact_attendance_match[["match_id", "ist", "ist_vip", "ist_definition", "ist_qualitaet", "bemerkung"]],
                on="match_id", how="left")
    z["abweichung_scans_ist"] = z["besucher_scans"] / z["ist"] - 1
    z["zutritt_vollstaendig"] = z["abweichung_scans_ist"] >= -0.10
    return z


def _erklaerung_scan(row) -> str:
    bem = text(row.get("bemerkung")).lower()
    a = row["abweichung_scans_ist"]
    if pd.isna(a):
        return "kein IST"
    if a < -0.5:
        return "Zutrittslieferung unvollständig (nur Bruchteil der Scans vorhanden)"
    if "drehkreuze" in bem or "handscanner" in bem:
        return "Scanprobleme laut Bemerkung Historie (IST geschätzt)"
    if "keine scans beim vip" in bem:
        return "VIP-Eingang nicht gescannt (laut Historie), IST = Scans + VIP"
    if "gästesektor" in bem and a < -0.03:
        return "Zusatz-Gästesektor/Gästebereich vermutlich nicht vollständig gescannt"
    if abs(a) <= 0.01:
        return "konsistent (≤ 1 %)"
    if a < 0:
        return "Scans unter IST: IST enthält vermutlich manuell gezählte Zutritte (z.B. Personal, Medien, Kinder)"
    return "Scans über IST"


def scan_ist_abgleich(z: pd.DataFrame, dim: pd.DataFrame) -> pd.DataFrame:
    out = z.merge(dim[["match_id", "saison", "wettbewerb", "gegner_anzeige"]], on="match_id")
    out["erklaerung"] = out.apply(_erklaerung_scan, axis=1)
    cols = ["match_id", "datum", "saison", "wettbewerb", "gegner_anzeige", "lieferung", "besucher_scans", "ist",
            "abweichung_scans_ist", "zutritt_vollstaendig", "tickets_mehrfach_gescannt", "leser_aktiv",
            "ist_definition", "erklaerung", "bemerkung"]
    return out[cols].sort_values("datum").reset_index(drop=True)


def spiel_kpi(r: Rohdaten, m: Modell, z: pd.DataFrame) -> pd.DataFrame:
    dim = m.dim_match
    att = m.fact_attendance_match.drop(columns=["bemerkung"]).rename(columns={"korrektur": "korrektur_historie"})
    cat = m.fact_catering_match.dropna(subset=["match_id"]).drop_duplicates("match_id")
    cat = cat[["match_id", "public_netto", "transaktionen", "umsatz_inkl", "umsatz_exkl", "kf_inkl", "kf_exkl",
               "bons_pro_anwesende", "bon_inkl", "bon_exkl", "gaeste_catering", "formel_abzug_vip",
               "stand_geschlossen", "mobiler_verkauf_reduziert", "personalmangel", "technische_probleme",
               "operativer_hinweis", "aktion_gratis_gutschein", "event_plattform"]]
    k = dim.merge(att, on="match_id", how="left").merge(cat, on="match_id", how="left")
    k = k.merge(z[["match_id", "besucher_scans", "abweichung_scans_ist", "zutritt_vollstaendig"]], on="match_id", how="left")
    t = m.tickets.groupby("match_id").agg(einzeltickets=("anzahl", "sum")).reset_index()
    k = k.merge(t, on="match_id", how="left")
    k["einzeltickets_vollstaendig"] = _ticket_vollstaendig(r, k)
    k["public_ist_minus_vip"] = k["ist"] - k["ist_vip"]
    k["public_netto_minus_ist_minus_vip"] = k["public_netto"] - k["public_ist_minus_vip"]
    k["umsatz_total_check"] = k["public_netto"] * k["kf_exkl"] - k["umsatz_exkl"]
    k["anteil_gaeste"] = k["ist_gaeste"] / k["ist"]
    _ausreisser(k)
    return k


def _ticket_vollstaendig(r: Rohdaten, k: pd.DataFrame) -> pd.Series:
    """Einzelticket-Daten gelten als vollständig, wenn der Export über das Spieldatum hinaus reicht."""
    ende = r.tickets_export.groupby("saison")["verkauf_ts"].max().dt.normalize()
    voll = []
    for _, row in k.iterrows():
        if pd.isna(row.get("einzeltickets")):
            voll.append(False)
        elif row["saison"] in ende.index:
            voll.append(bool(row["datum"] <= ende[row["saison"]]))
        else:
            voll.append(True)   # CSV-Saisons: eine Datei pro Spiel
    return pd.Series(voll, index=k.index)


def _ausreisser(k: pd.DataFrame) -> None:
    """Robuster z-Wert (Median/MAD) je KPI innerhalb der gespielten SL-Spiele ab Baseline-Saison."""
    basis = k[(k["wettbewerb"] == "SL") & (k["spielstatus"] == "gespielt")]
    flags = []
    for kpi in KPI_AUSREISSER:
        x = basis[kpi].dropna()
        if len(x) < 10:
            continue
        med, mad = x.median(), (x - x.median()).abs().median() * 1.4826
        z = (k[kpi] - med) / mad if mad > 0 else np.nan
        k[f"z_{kpi}"] = z
        flags.append(np.where(z.abs() > 3.5, kpi, ""))
    k["ausreisser"] = [", ".join(f for f in fs if f) for fs in zip(*flags)] if flags else ""


def saison_kpi(k: pd.DataFrame, wettbewerbe: tuple[str, ...]) -> pd.DataFrame:
    """Saisonwerte (Summe/Summe) für die gewählten Wettbewerbe; nur gespielte Spiele."""
    d = k[k["wettbewerb"].isin(wettbewerbe) & (k["spielstatus"] == "gespielt")]
    rows = []
    for s, g in d.groupby("saison"):
        a = g.dropna(subset=["soll", "ist"])
        c = g.dropna(subset=["public_netto", "umsatz_inkl"])
        tx = c.dropna(subset=["transaktionen"])
        rows.append({
            "saison": s, "wettbewerbe": "+".join(wettbewerbe), "spiele": len(g),
            "spiele_mit_soll_ist": len(a), "ist_summe": a["ist"].sum(), "ist_mittel": a["ist"].mean(),
            "soll_mittel": a["soll"].mean(), "noshow_quote": 1 - a["ist"].sum() / a["soll"].sum() if len(a) else np.nan,
            "noshow_quote_ungewichtet": a["noshow_quote"].mean(),
            "spiele_ausverkauft": int(als_bool(g["ausverkauft"]).sum()),
            "spiele_mit_catering": len(c), "public_netto_summe": c["public_netto"].sum(),
            "umsatz_inkl": c["umsatz_inkl"].sum(), "umsatz_exkl": c["umsatz_exkl"].sum(),
            "kf_inkl": c["umsatz_inkl"].sum() / c["public_netto"].sum() if len(c) else np.nan,
            "kf_exkl": c["umsatz_exkl"].sum() / c["public_netto"].sum() if len(c) else np.nan,
            "kf_inkl_ungewichtet": c["kf_inkl"].mean(),
            "spiele_mit_bons": len(tx),
            "bons_pro_anwesende": tx["transaktionen"].sum() / tx["public_netto"].sum() if len(tx) else np.nan,
            "bon_inkl": tx["umsatz_inkl"].sum() / tx["transaktionen"].sum() if len(tx) else np.nan,
            "bon_exkl": tx["umsatz_exkl"].sum() / tx["transaktionen"].sum() if len(tx) else np.nan,
        })
    return pd.DataFrame(rows)


def catering_trend(r: Rohdaten) -> pd.DataFrame:
    """Langfristiger Trend ab 2018/19 (Saisonebene, inkl. MwSt wegen Netto-Methodenwechsel 2020/21)."""
    c = r.catering[r.catering["wettbewerb"].isin(config.KERN_WETTBEWERBE) & r.catering["public_netto"].notna()]
    rows = []
    for (s, scope), g in pd.concat([c.assign(scope="SL"), c.assign(scope="SL+Cup+UEFA")]).groupby(["saison", "scope"]):
        if scope == "SL":
            g = g[g["wettbewerb"] == "SL"]
        rows.append({"saison": s, "scope": scope, "spiele": len(g), "public_netto": g["public_netto"].sum(),
                     "umsatz_inkl": g["umsatz_inkl"].sum(), "kf_inkl": g["umsatz_inkl"].sum() / g["public_netto"].sum(),
                     "public_netto_mittel": g["public_netto"].mean(),
                     "covid_hinweis": "COVID-Einschränkungen" if s in ("2019/20", "2020/21") else ""})
    return pd.DataFrame(rows).sort_values(["scope", "saison"]).reset_index(drop=True)


def entwicklung_abgleich(r: Rohdaten, k: pd.DataFrame) -> pd.DataFrame:
    """Gegenprobe: eigene Saisonsummen vs. Blatt «Entwicklung» des Caterers."""
    e = r.entwicklung
    rows = []
    for _, row in e.iterrows():
        lab = row["label"].lower()
        if lab.startswith("meisters") and "frauen" not in lab and "u21" not in lab:
            scope = ("SL",)
        elif lab.startswith("total spiele fcsg"):
            scope = config.KERN_WETTBEWERBE
        else:
            continue
        d = r.catering[r.catering["wettbewerb"].isin(scope) & (r.catering["saison"] == row["saison"])]
        if d.empty:
            continue
        rows.append({"label_entwicklung": row["label"], "saison": row["saison"], "events_blatt": row["events"],
                     "events_eigen": len(d), "anwesende_blatt": row["anwesende"], "anwesende_eigen": d["public_netto"].sum(),
                     "umsatz_inkl_blatt": row["umsatz_inkl"], "umsatz_inkl_eigen": d["umsatz_inkl"].sum(),
                     "kf_exkl_blatt": row["kf_exkl_blatt"],
                     "kf_exkl_gewichtet_eigen": d["umsatz_exkl"].sum() / d["public_netto"].sum(),
                     "kf_exkl_ungewichtet_eigen": d["kf_exkl"].mean()})
    out = pd.DataFrame(rows)
    if not out.empty:
        out["umsatz_differenz"] = out["umsatz_inkl_eigen"] - out["umsatz_inkl_blatt"]
    return out


def baseline(r: Rohdaten, m: Modell) -> dict[str, pd.DataFrame]:
    z = zutritt_spiel(r, m)
    k = spiel_kpi(r, m, z)
    saison = pd.concat([saison_kpi(k, ("SL",)), saison_kpi(k, ("Cup", "UEFA")), saison_kpi(k, config.KERN_WETTBEWERBE)],
                       ignore_index=True)
    out = {
        "spiel_kpi": k,
        "saison_kpi": saison,
        "catering_trend": catering_trend(r),
        "scan_ist": scan_ist_abgleich(z, m.dim_match),
        "entwicklung_abgleich": entwicklung_abgleich(r, k),
    }
    _befunde(out)
    return out


def _befunde(out: dict[str, pd.DataFrame]) -> None:
    k = out["spiel_kpi"]
    sl = k[(k["wettbewerb"] == "SL") & (k["spielstatus"] == "gespielt")]
    diff = sl.dropna(subset=["public_netto_minus_ist_minus_vip"])
    if len(diff):
        befund("Catering", "mittel", "Public-Netto-Formeln (Nenner Kundenfranken)",
               f"Public Netto = IST minus abgezogene VIP-Zahl. Der Abzug weicht vom «IST VIP» der Historie im Mittel um "
               f"{(diff['formel_abzug_vip'] - diff['ist_vip']).mean():.0f} Personen ab (Saison 2025/26: "
               f"{(diff[diff['saison'] == '2025/26']['formel_abzug_vip'] - diff[diff['saison'] == '2025/26']['ist_vip']).mean():.0f}; "
               f"2026/27: {(diff[diff['saison'] == '2026/27']['formel_abzug_vip'] - diff[diff['saison'] == '2026/27']['ist_vip']).mean():.0f}).",
               "Nenner des Kundenfrankens nicht über alle Saisons identisch definiert (Effekt auf KF < 1 %).",
               "Public Netto wie geliefert verwendet; VIP-Definition beim Caterer/FCSG bestätigen.")
    s = out["scan_ist"]
    voll = s[s["zutritt_vollstaendig"]]
    befund("Zutritt", "info", "Scan-IST-Abgleich",
           f"{len(voll)} von {len(s)} Spielen mit Zutrittsdaten sind vollständig (Scans ≥ 90 % des IST); "
           f"Abweichung im Mittel {voll['abweichung_scans_ist'].mean():+.1%}.",
           "Unvollständige Spiele verfälschen Ankunftsanteile nicht, aber die Besucherzahl.",
           "Ankunftsanalysen nur mit vollständigen Spielen.")

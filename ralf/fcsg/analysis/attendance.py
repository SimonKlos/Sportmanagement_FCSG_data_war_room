"""Paket B – Anwesenheit und Absatz (Pflicht im verfügbaren Scope).

* No-Show-Kontextmuster (deskriptiv, saisonbereinigt)
* Ticket-Typ-Näherung (Einzel vs. Rest) nur für Saisons mit validiertem Eintritt (ZKS 2021/22, 2022/23)
* Eintrittsquote der Einzeltickets nach Kanal, Tarif, Tribüne, Vorlauf und Bestellgrösse
* Einzelticket-Absatzkurven – ausdrücklich KEINE vollständige Stadion-Ausverkaufskurve (Abos fehlen)
* Saisonabo-Snapshot 2026/27 und Zerlegung der SOLL-Formeln 2025/26 (Abo-Bestand)
"""
from __future__ import annotations

import re

import numpy as np
import pandas as pd

from .. import config
from ..datamodel import Modell, Rohdaten
from ..log import befund

VORLAUF_KLASSEN = [(-1, 0, "Spieltag"), (0, 2, "1–2 Tage"), (2, 7, "3–7 Tage"), (7, 14, "8–14 Tage"),
                   (14, 30, "15–30 Tage"), (30, 10_000, "über 30 Tage")]
ZKS_SAISONS = ("2021/22", "2022/23")


def _vorlauf_klasse(t: pd.Series) -> pd.Series:
    out = pd.Series(pd.NA, index=t.index, dtype="object")
    for lo, hi, name in VORLAUF_KLASSEN:
        out[(t > lo) & (t <= hi)] = name
    return out


def _bestell_klasse(n: pd.Series) -> pd.Series:
    return pd.cut(n, [0, 1, 2, 4, 9, 10_000], labels=["1", "2", "3–4", "5–9", "10+"]).astype(str)


def _unterdruecken(df: pd.DataFrame, n_col: str, wert_cols: list[str]) -> pd.DataFrame:
    df = df.copy()
    klein = df[n_col] < config.MIN_ZELLE
    df.loc[klein, wert_cols] = np.nan
    df["unterdrueckt"] = klein
    return df


# --------------------------------------------------------------------------------------------
# No-Show-Kontext
# --------------------------------------------------------------------------------------------
def _temp_klasse(t: pd.Series) -> pd.Series:
    return pd.cut(t, [-50, 5, 15, 50], labels=["unter 5 °C", "5–15 °C", "über 15 °C"]).astype(str)


def noshow_kontext(k: pd.DataFrame, ctx: pd.DataFrame) -> pd.DataFrame:
    d = k.merge(ctx[["match_id", "temp_anpfiff_c", "regen_anreise", "schulferien", "free_tv_srf", "feiertag"]],
                on="match_id", how="left")
    d = d[(d["wettbewerb"] == "SL") & (d["spielstatus"] == "gespielt") & (d["saison"] >= config.MODELL_AB_SAISON)
          & d["soll"].notna() & d["ist"].notna()].copy()
    d["noshow_saisonbereinigt_pp"] = (d["noshow_quote"] - d.groupby("saison")["noshow_quote"].transform("mean")) * 100
    d["temperatur"] = _temp_klasse(d["temp_anpfiff_c"])
    dims = {"wochentag_typ": "Wochentag", "anpfiff_slot": "Anstosszeit", "winter": "Winter (Nov–Feb)",
            "top_gegner": "Top-Gegner (FCB/YB/FCZ)", "schulferien": "Schulferien SG", "regen_anreise": "Regen bei Anreise",
            "temperatur": "Temperatur Anpfiff", "free_tv_srf": "Free-TV (SRF)", "ausverkauft": "Ausverkauft",
            "soll_ticketbasiert": "SOLL ticketbasiert (nicht Kapazitätswert)"}
    rows = []
    for col, label in dims.items():
        for wert, g in d.groupby(d[col].astype(str)):
            if wert in ("<NA>", "nan", "None"):
                continue
            rows.append({"merkmal": label, "auspraegung": wert, "spiele": len(g),
                         "noshow_gewichtet": 1 - g["ist"].sum() / g["soll"].sum(),
                         "noshow_median": g["noshow_quote"].median(),
                         "abweichung_vom_saisonmittel_pp": g["noshow_saisonbereinigt_pp"].mean(),
                         "ist_mittel": g["ist"].mean()})
    out = pd.DataFrame(rows)
    out["hinweis"] = "deskriptiv, Merkmale überlagern sich (z.B. Winter und Abendspiel); Modell siehe Kontext-Effekt-Matrix"
    return out


# --------------------------------------------------------------------------------------------
# Ticket-Typ-Näherung und Eintrittsquoten (nur ZKS-Saisons)
# --------------------------------------------------------------------------------------------
def _zks_spiele(m: Modell, k: pd.DataFrame) -> pd.DataFrame:
    t = m.tickets[(m.tickets["quelle"] == "Export XLSX")]
    g = t.groupby("match_id").agg(einzel=("anzahl", "sum"), einzel_eingetreten=("eintritt_ts", "count"),
                                  uebergeben=("uebergabe_ts", "count")).reset_index()
    g = g.merge(k[["match_id", "datum", "saison", "wettbewerb", "gegner_anzeige", "soll", "ist", "soll_definition",
                   "ist_qualitaet", "ausverkauft"]], on="match_id")
    g["eintrittsquote_einzel"] = g["einzel_eingetreten"] / g["einzel"]
    g["uebergabequote"] = g["uebergeben"] / g["einzel"]
    g["zks_valide"] = g["saison"].isin(ZKS_SAISONS) & (g["uebergabequote"] >= 0.95) & \
        (g["ist_qualitaet"] != "IST geschätzt/Scanprobleme") & (g["eintrittsquote_einzel"] >= 0.75)
    g["grund_nicht_valide"] = np.select(
        [~g["saison"].isin(ZKS_SAISONS), g["ist_qualitaet"] == "IST geschätzt/Scanprobleme",
         g["eintrittsquote_einzel"] < 0.75, g["uebergabequote"] < 0.95],
        ["Saison ohne vollständige ZKS-Erfassung (23/24 teilweise, 24/25 leer)", "Scanprobleme laut Historie",
         "Eintrittsquote < 75 % (Erfassungslücke)", "Übergabe an Zutrittssystem < 95 %"], default="")
    return g


def tickettyp_noshow(g: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Retos Näherung: Rest = SOLL − Einzeltickets (≈ Abos inkl. VIP/Gäste/Freikarten)."""
    d = g[g["saison"].isin(ZKS_SAISONS)].copy()
    d["rest_soll"] = d["soll"] - d["einzel"]
    d["rest_anwesend"] = d["ist"] - d["einzel_eingetreten"]
    d["noshow_einzel"] = 1 - d["eintrittsquote_einzel"]
    d["noshow_rest"] = 1 - d["rest_anwesend"] / d["rest_soll"]
    d["anteil_rest_am_soll"] = d["rest_soll"] / d["soll"]
    d["soll_kapazitaetswert"] = d["soll_definition"].str.contains("Kapazität")
    rows = []
    for (s, scope), x in pd.concat([d.assign(scope="alle validen Spiele"),
                                    d[~d["soll_kapazitaetswert"]].assign(scope="nur SOLL ticketbasiert")]).groupby(["saison", "scope"]):
        x = x[x["zks_valide"]]
        if x.empty:
            continue
        rows.append({"saison": s, "scope": scope, "spiele": len(x),
                     "anteil_rest_am_soll": x["rest_soll"].sum() / x["soll"].sum(),
                     "noshow_einzel": 1 - x["einzel_eingetreten"].sum() / x["einzel"].sum(),
                     "noshow_rest_naeherung": 1 - x["rest_anwesend"].sum() / x["rest_soll"].sum(),
                     "noshow_gesamt": 1 - x["ist"].sum() / x["soll"].sum(),
                     "spannweite_noshow_rest": f"{x['noshow_rest'].min():.0%}–{x['noshow_rest'].max():.0%}",
                     "spannweite_noshow_einzel": f"{x['noshow_einzel'].min():.0%}–{x['noshow_einzel'].max():.0%}"})
    zusammen = pd.DataFrame(rows)
    zusammen["hinweis"] = ("Näherung: Rest enthält Abos, VIP, Gäste und Freikarten; bei Kapazitäts-SOLL (ausverkauft) "
                           "ist der Rest überschätzt. Nur als gekennzeichnete Näherung verwenden.")
    return d, zusammen


def eintritt_segmente(m: Modell, g: pd.DataFrame) -> pd.DataFrame:
    valide = set(g.loc[g["zks_valide"], "match_id"])
    t = m.tickets[m.tickets["match_id"].isin(valide)].copy()
    t["eingetreten"] = t["eintritt_ts"].notna()
    t["vorlauf_klasse"] = _vorlauf_klasse(t["vorlauf_tage"])
    t["bestellgroesse"] = _bestell_klasse(t["bestellung_groesse"])
    t["preis_typ"] = np.where(t["gratis"], "Gratis (0 CHF)", "bezahlt")
    rows = []
    for col, label in [("kanal", "Verkaufskanal"), ("tarifgruppe", "Tarifgruppe"), ("tribuene", "Tribüne"),
                       ("vorlauf_klasse", "Kaufzeitpunkt vor Spiel"), ("bestellgroesse", "Tickets pro Bestellung"),
                       ("preis_typ", "Preis"), ("kanal_roh", "Verkaufsmodul (Rohwert)")]:
        for wert, x in t.groupby(col):
            rows.append({"merkmal": label, "auspraegung": wert, "tickets": len(x), "spiele": x["match_id"].nunique(),
                         "eintrittsquote": x["eingetreten"].mean(), "noshow_quote": 1 - x["eingetreten"].mean()})
    out = _unterdruecken(pd.DataFrame(rows), "tickets", ["eintrittsquote", "noshow_quote"])
    out["basis"] = f"Einzeltickets der validen ZKS-Spiele {', '.join(ZKS_SAISONS)} (n Spiele = {len(valide)})"
    gaeste = out["auspraegung"].astype(str).str.contains("Gäste")
    out["hinweis"] = np.where(gaeste, "Gäste-Kontingente teils als eigene Veranstaltung erfasst; Eintritt im ZKS "
                                      "vermutlich unvollständig – Quote eher unterschätzt", "")
    return out


# --------------------------------------------------------------------------------------------
# Absatzkurven (Vorlauf)
# --------------------------------------------------------------------------------------------
def absatz(m: Modell, k: pd.DataFrame) -> dict[str, pd.DataFrame]:
    voll = set(k.loc[k["einzeltickets_vollstaendig"] & (k["spielstatus"] == "gespielt"), "match_id"])
    t = m.tickets[m.tickets["match_id"].isin(voll)].copy()
    negativ = t[t["vorlauf_tage"] < 0]
    if len(negativ):
        befund("Ticketing", "tief", "Einzelticket-Exporte",
               f"{len(negativ)} Tickets haben ein Bestelldatum nach dem Spieltag.",
               "Für Vorlaufkurven unbrauchbar.", "Aus Absatzkurven ausgeschlossen (in Summen enthalten).")
    t = t[t["vorlauf_tage"] >= 0]
    info = k.set_index("match_id")
    rows, kurven = [], []
    tage = np.arange(0, 61)
    for mid, x in t.groupby("match_id"):
        v = x["vorlauf_tage"].to_numpy()
        n = len(v)
        anteil_ab = [(v >= d).mean() for d in tage]
        kurven.append(pd.DataFrame({"match_id": mid, "tage_vor_spiel": tage, "anteil_bereits_verkauft": anteil_ab}))
        rows.append({"match_id": mid, "einzeltickets": n,
                     "anteil_am_spieltag": (v == 0).mean(), "anteil_letzte_3_tage": (v <= 2).mean(),
                     "anteil_letzte_7_tage": (v <= 6).mean(), "anteil_ueber_30_tage": (v > 30).mean(),
                     "vorlauf_median_tage": float(np.median(v)),
                     "t50_tage": float(np.quantile(v, 0.50)), "t80_tage": float(np.quantile(v, 0.20)),
                     "t95_tage": float(np.quantile(v, 0.05)),
                     "anteil_gratis": x["gratis"].mean(), "anteil_gaeste_b4": (x["tribuene"] == "B4 (Gäste)").mean()})
    je_spiel = pd.DataFrame(rows).merge(
        info[["datum", "saison", "wettbewerb", "gegner_anzeige", "top_gegner", "ausverkauft", "soll", "ist",
              "wochentag_typ", "anpfiff_slot"]].reset_index(), on="match_id")
    kurven = pd.concat(kurven, ignore_index=True)

    seg_rows = []
    t["vorlauf_klasse"] = _vorlauf_klasse(t["vorlauf_tage"])
    for col, label in [("tribuene", "Tribüne"), ("tarifgruppe", "Tarifgruppe"), ("kanal", "Verkaufskanal")]:
        for (quelle, wert), x in t.groupby(["quelle", col]):
            seg_rows.append({"datenbasis": "Exporte 2021/22–2024/25" if quelle == "Export XLSX" else "CSV 2025/26–2026/27",
                             "merkmal": label, "auspraegung": wert, "tickets": len(x),
                             "vorlauf_median_tage": x["vorlauf_tage"].median(),
                             "anteil_am_spieltag": (x["vorlauf_tage"] == 0).mean(),
                             "anteil_ueber_14_tage": (x["vorlauf_tage"] > 14).mean()})
    seg = _unterdruecken(pd.DataFrame(seg_rows), "tickets", ["vorlauf_median_tage", "anteil_am_spieltag", "anteil_ueber_14_tage"])

    ausv = je_spiel[je_spiel["wettbewerb"] == "SL"].groupby("ausverkauft").agg(
        spiele=("match_id", "size"), t50_median=("t50_tage", "median"), t80_median=("t80_tage", "median"),
        anteil_spieltag_median=("anteil_am_spieltag", "median")).reset_index()
    ausv["hinweis"] = ("Ausverkauft gemäss Historie (Flag oder Bemerkung). Ohne Kapazitäts- und Bestandsdaten pro Tag "
                       "kann der Zeitpunkt des Ausverkaufs nicht bestimmt werden – nur der Einzelticket-Vorlauf.")
    return {"absatz_je_spiel": je_spiel, "absatzkurven": kurven, "absatz_segmente": seg, "absatz_ausverkauft": ausv}


def bestellgroesse(m: Modell) -> pd.DataFrame:
    t = m.tickets.copy()
    t["klasse"] = _bestell_klasse(t["bestellung_groesse"])
    out = t.groupby(["saison", "klasse"]).size().rename("tickets").reset_index()
    out["anteil_tickets"] = out["tickets"] / out.groupby("saison")["tickets"].transform("sum")
    return out


# --------------------------------------------------------------------------------------------
# Abos: Snapshot 2026/27 und Bestand 2025/26 aus SOLL-Formeln
# --------------------------------------------------------------------------------------------
def abo_snapshot(r: Rohdaten) -> pd.DataFrame:
    a = r.abos.copy()
    rows = []
    for team, x in a.groupby("team"):
        for col, label in [("tribuene", "Tribüne"), ("tarifgruppe", "Tarifgruppe"), ("kanal", "Verkaufskanal"),
                           ("versand", "Abo-Form (Versandart)")]:
            for wert, y in x.groupby(col):
                rows.append({"team": team, "merkmal": label, "auspraegung": wert, "abos": len(y),
                             "anteil": len(y) / len(x), "preis_mittel_chf": y["preis"].mean(),
                             "anteil_preis_0": (y["preis"] == 0).mean(), "umsatz_chf": y["preis"].sum()})
    out = _unterdruecken(pd.DataFrame(rows), "abos", ["preis_mittel_chf", "anteil_preis_0"])
    out["stichtag"] = "Export 30.09.2026 (Herren); Frauen: Dateiname ohne gültiges Datum"
    return out


def soll_zerlegung(r: Rohdaten, k: pd.DataFrame) -> pd.DataFrame:
    """SOLL-Formeln mit Ticketkomponenten gegen die Einzelticket-CSV abgleichen.

    Aus den Summanden der Formel wird die Teilmenge gesucht, deren Summe der Anzahl Einzeltickets in
    der CSV am nächsten kommt; die übrigen Summanden gelten als Abo-Komponenten (impliziter Abo-Bestand).
    """
    from itertools import combinations

    att = k[k["soll_formel"].notna() & k["soll_definition"].str.contains("Ticketkomponenten")]
    csv = r.tickets_csv.groupby(["match_datum", "kanal_roh"]).size().unstack(fill_value=0)
    rows = []
    for _, row in att.iterrows():
        if row["datum"] not in csv.index:
            continue                       # ohne Einzelticket-CSV kein Abgleich möglich (z.B. Cup 04.02.2026)
        terme = [int(x) for x in re.findall(r"\d+", row["soll_formel"].split("-K")[0])]
        einzel_csv = int(csv.loc[row["datum"]].sum())
        beste = min((c for n in range(1, len(terme)) for c in combinations(range(len(terme)), n)),
                    key=lambda c: abs(sum(terme[i] for i in c) - einzel_csv))
        einzel_terme = [terme[i] for i in beste]
        abo_terme = [terme[i] for i in range(len(terme)) if i not in beste]
        diff = sum(einzel_terme) - einzel_csv
        rows.append({"match_id": row["match_id"], "datum": row["datum"], "soll_formel": row["soll_formel"],
                     "soll": row["soll"], "einzeltickets_csv": einzel_csv,
                     "einzel_terme": "+".join(map(str, einzel_terme)), "differenz_einzel_formel_vs_csv": diff,
                     "abo_terme": "+".join(map(str, abo_terme)), "abo_bestand_implizit": sum(abo_terme),
                     "zuordnung": "eindeutig (≤ 1 %)" if abs(diff) <= 0.01 * einzel_csv else "Näherung (> 1 % Differenz)",
                     "zweitmarkt": row["zweitmarkt"]})
    out = pd.DataFrame(rows)
    if not out.empty:
        befund("Ticketing", "info", "Historie, SOLL-Formeln 2025/26",
               "SOLL = Einzeltickets (stimmen mit den CSV-Zählungen je Verkaufsstelle überein) + zwei Abo-Komponenten "
               f"(zusammen {out['abo_bestand_implizit'].min():,.0f}–{out['abo_bestand_implizit'].max():,.0f}) − Zweitmarkt. "
               "Bei ausverkauften Spielen wird SOLL stattdessen als Kapazität (z.B. 20'036 − 1'930 + Gäste) gesetzt.",
               "SOLL ist je nach Spiel Ticketsumme ODER Kapazitätswert; No-Show bei ausverkauften Spielen nicht ticketbasiert.",
               "Definition je Spiel als Flag geführt (soll_definition); Bestätigung durch Sandro einholen.")
    return out


def anwesenheit(r: Rohdaten, m: Modell, k: pd.DataFrame) -> dict[str, pd.DataFrame]:
    g = _zks_spiele(m, k)
    je_spiel, typ = tickettyp_noshow(g)
    out = {"noshow_kontext": noshow_kontext(k, m.dim_match_context), "zks_spiele": g,
           "tickettyp_je_spiel": je_spiel, "tickettyp_noshow": typ, "eintritt_segmente": eintritt_segmente(m, g),
           "bestellgroesse": bestellgroesse(m), "abo_snapshot": abo_snapshot(r), "soll_zerlegung": soll_zerlegung(r, k)}
    out.update(absatz(m, k))
    return out

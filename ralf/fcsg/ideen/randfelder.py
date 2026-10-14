"""Randfelder ausserhalb des Phase-1-Kernscopes (explorativ): Frauen, Länderspiele/WEURO, Testspiele und Events.

Phase 1 schliesst diese Anlässe dokumentiert aus (Unmatched-Report). Für die Ideenfindung zeigen sie, wie das Stadion
an Nicht-Herren-Tagen genutzt wird. Nur Aggregate; kleine Anlässe sind teils im Espenmoos (nicht kybunpark).
"""
from __future__ import annotations

import re

import numpy as np
import pandas as pd

KATEGORIE = {"SL": "Herren Meisterschaft", "Cup": "Herren Cup", "UEFA": "Herren UEFA", "Frauen": "Frauen",
             "Nati": "Länderspiele (inkl. WEURO 2025)", "Test": "Testspiele", "Event": "Events ohne Spiel", "U21": "U21",
             "Fremdclub": "Fremdclubs"}


def kategorien(r) -> pd.DataFrame:
    c = r.catering[(r.catering["saison"] >= "2022/23") & r.catering["wettbewerb"].isin(KATEGORIE)].copy()
    c["kategorie"] = c["wettbewerb"].map(KATEGORIE)
    rows = []
    for (s, kat), g in c.groupby(["saison", "kategorie"]):
        pn = g["public_netto"].where(g["public_netto"] > 0)
        mit = g[pn.notna()]
        tx = mit[mit["transaktionen"] > 0]
        rows.append({"saison": s, "kategorie": kat, "anlaesse": len(g), "anlaesse_mit_zuschauerzahl": len(mit),
                     "public_anwesende": mit["public_netto"].sum(), "umsatz_inkl": g["umsatz_inkl"].sum(),
                     "kf_inkl": mit["umsatz_inkl"].sum() / mit["public_netto"].sum() if len(mit) else np.nan,
                     "bons_pro_anwesende": tx["transaktionen"].sum() / tx["public_netto"].sum() if len(tx) else np.nan,
                     "bon_inkl": tx["umsatz_inkl"].sum() / tx["transaktionen"].sum() if len(tx) else np.nan})
    out = pd.DataFrame(rows)
    out["anteil_am_catering_umsatz"] = out["umsatz_inkl"] / out.groupby("saison")["umsatz_inkl"].transform("sum")
    out["hinweis"] = np.where(out["kategorie"] == "Events ohne Spiel",
                              "Events: KF wenig aussagekräftig (Zuschauerzahl oft geschätzt/fehlend, teils mehrtägig)",
                              np.where(out["kategorie"].str.startswith("Herren"), "Kernscope Phase 1", "ausserhalb Kernscope – explorativ"))
    return out


def _promo(text) -> float:
    m = re.search(r"Promo-Tickets:\s*([\d']+)", str(text or ""))
    return float(m.group(1).replace("'", "")) if m else np.nan


def frauen(r) -> pd.DataFrame:
    h = r.historie[(r.historie["wettbewerb"] == "Frauen") & (r.historie["saison"] >= "2022/23")]
    c = r.catering[(r.catering["wettbewerb"] == "Frauen") & (r.catering["saison"] >= "2022/23")]
    z = r.zutritt_frauen.set_index("datum")["besucher"] if not r.zutritt_frauen.empty else pd.Series(dtype=float)
    rows = []
    for _, x in c.iterrows():
        hh = h[h["datum"] == x["datum"]]
        bem = str(x.get("bemerkung") or "")
        if "espenmoos" in bem.lower():
            ort = "Espenmoos"
        elif not pd.isna(z.get(x["datum"], np.nan)) or re.search(r"kybunpark|sektor|stand|haupttribüne|plattform|\b[abcd]\d\b", bem, re.I):
            ort = "kybunpark"
        else:
            ort = "unbekannt"
        hz = hh.iloc[0] if len(hh) else None
        rows.append({"datum": x["datum"], "saison": x["saison"], "spiel": x["spiel"], "ort": ort,
                     "familyday": bool(re.search(r"family ?day", bem + " " + str(hz["bemerkung"] if hz is not None else ""), re.I)),
                     "soll": hz["soll"] if hz is not None else np.nan, "ist": hz["ist"] if hz is not None else np.nan,
                     "scans": z.get(x["datum"], np.nan),
                     "promo_tickets": _promo(hz["bemerkung"]) if hz is not None else np.nan,
                     "public_anwesende_catering": x["public_netto"], "umsatz_inkl": x["umsatz_inkl"],
                     "kf_inkl": x["umsatz_inkl"] / x["public_netto"] if x["public_netto"] and x["public_netto"] > 0 else np.nan,
                     "bons_pro_anwesende": x["transaktionen"] / x["public_netto"] if x["public_netto"] and x["public_netto"] > 0 else np.nan})
    out = pd.DataFrame(rows).sort_values("datum")
    out["noshow_quote"] = 1 - out["ist"] / out["soll"]
    out["hinweis"] = "ausserhalb Kernscope; Espenmoos = kleines Stadion ohne Zutrittsdaten; Promo-Tickets laut Bemerkung Historie"
    return out


def rechne(r) -> dict[str, pd.DataFrame]:
    return {"randfelder_kategorien": kategorien(r), "randfelder_frauen": frauen(r)}

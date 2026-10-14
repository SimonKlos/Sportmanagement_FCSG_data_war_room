"""Randfelder ausserhalb des Phase-1-Kernscopes (explorativ): Testspiele, U21, Fremdclubs und Events.

Phase 1 schliesst diese Anlässe dokumentiert aus (Unmatched-Report). Für die Ideenfindung zeigen sie, wie das Stadion
an weiteren Anlässen genutzt wird. Nur Aggregate.

**Team-Repo (D-016/D-036, 14.10.2026):** Frauen-Spiele und Länderspiele (inkl. WEURO 2025) werden ignoriert – sie
erscheinen weder als Kategorie noch in einer eigenen Auswertung (früher Blatt F2_Randfelder_Frauen).
"""
from __future__ import annotations

import numpy as np
import pandas as pd

# Frauen ("Frauen") und Länderspiele ("Nati", "Nati Frauen") bewusst nicht enthalten (D-016/D-036).
KATEGORIE = {"SL": "Herren Meisterschaft", "Cup": "Herren Cup", "UEFA": "Herren UEFA", "Test": "Testspiele",
             "Event": "Events ohne Spiel", "U21": "U21", "Fremdclub": "Fremdclubs"}


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



def rechne(r) -> dict[str, pd.DataFrame]:
    return {"randfelder_kategorien": kategorien(r)}

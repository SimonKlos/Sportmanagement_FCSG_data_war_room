"""Abgleich der Spieltabellen beider Pipelines (Simon `src/fcsg` vs. Ralfs Rechenkern `ralf/`), D-028.

Vergleicht je Spieldatum die Kernzahlen, die beide Pipelines aus denselben Rohdaten bilden. Ziel ist keine
neue Kennzahl, sondern der Nachweis, wo die Zahlenbasis übereinstimmt und wo und warum sie abweicht
(Integrationsplan 5.1, Schritt 3).

Aufruf (Projektroot)::

    python -m fcsg.abgleich <simon/mart_match.csv> <ralf/Tabellen/mart_match.csv> <ausgabeordner>
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

# (Kennzahl, Spalte Simon, Spalte Ralf, Toleranz relativ)
PAIRS = [
    ("SOLL", "soll", "soll", 0.0),
    ("IST", "ist", "ist", 0.0),
    ("IST VIP", "ist_vip", "ist_vip", 0.0),
    ("Public Netto", "public_attendance", "public_netto", 0.0),
    ("Transaktionen", "receipts", "transaktionen", 0.0),
    ("Umsatz inkl. MwSt", "revenue_gross_chf", "umsatz_inkl", 1e-6),
    ("Umsatz exkl. MwSt", "revenue_net_chf", "umsatz_exkl", 1e-6),
    ("KF inkl. MwSt", "kf_gross_chf", "kf_inkl", 1e-6),
    ("Scans", "scan_count", "besucher_scans", 0.005),
    ("Anteil Ankunft ≥ 45 Min.", "share_arrived_45min_before", "anteil_ab_45_min", 0.02),
    ("Eintrittsquote Einzeltickets", "single_entry_rate", "eintrittsquote_einzel", 0.01),
]

# Bekannte, dokumentierte Ursachen (werden in der Spalte «grund» vermerkt)
KNOWN_DATE_CORRECTIONS = {"2024-08-24": "2024-09-24"}  # D-030: Historie-Datum, nur Ralf korrigiert


def compare_marts(simon: pd.DataFrame, ralf: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Vergleicht beide Spieltabellen je Datum.

    Args:
        simon: ``mart_match.csv`` aus ``fcsg.cli analyze`` (Spalte ``match_date``).
        ralf: ``Tabellen/mart_match.csv`` aus ``ralf/run_all.py`` (Spalte ``datum``; nur gespielte Kernspiele).

    Returns:
        (je Spiel und Kennzahl: Werte, Status, Grund; Zusammenfassung je Kennzahl)
    """
    s = simon.copy()
    s["datum"] = s["match_date"].astype(str).replace(KNOWN_DATE_CORRECTIONS)
    r = ralf.copy()
    r["datum"] = r["datum"].astype(str).str[:10]
    if "spielstatus" in r:
        r = r[~r["spielstatus"].astype(str).str.contains("geplant|künftig", case=False, na=False)]
    m = s.merge(r, on="datum", how="outer", suffixes=("_s", "_r"), indicator=True)
    rows = []
    for _, g in m.iterrows():
        for label, cs, cr, tol in PAIRS:
            vs = g.get(cs if cs in m else f"{cs}_s", np.nan)
            vr = g.get(cr if cr in m else f"{cr}_r", np.nan)
            vs = pd.to_numeric(pd.Series([vs]), errors="coerce").iat[0]
            vr = pd.to_numeric(pd.Series([vr]), errors="coerce").iat[0]
            if g["_merge"] != "both":
                status = "nur Simon" if g["_merge"] == "left_only" else "nur Ralf"
            elif pd.isna(vs) and pd.isna(vr):
                status = "beide leer"
            elif pd.isna(vs) or pd.isna(vr):
                status = "nur Simon" if pd.isna(vr) else "nur Ralf"
            else:
                rel = abs(vs - vr) / max(abs(vr), 1e-9)
                status = "gleich" if rel <= tol else "abweichend"
            reason = ""
            if g.get("match_date") in KNOWN_DATE_CORRECTIONS or g["datum"] in KNOWN_DATE_CORRECTIONS.values():
                reason = "Datumskorrektur D-030 (Simon via Datumszuordnung im Abgleich)"
            rows.append({"datum": g["datum"], "saison": g.get("season", g.get("saison")), "kennzahl": label,
                         "simon": vs, "ralf": vr, "status": status, "grund": reason})
    per_game = pd.DataFrame(rows)
    summary = (per_game.groupby(["kennzahl", "status"]).size().unstack(fill_value=0)
               .reindex([p[0] for p in PAIRS]).reset_index())
    return per_game, summary


def main(argv: list[str] | None = None) -> int:
    a = argv if argv is not None else sys.argv[1:]
    if len(a) != 3:
        print(__doc__)
        return 2
    simon = pd.read_csv(a[0])
    ralf = pd.read_csv(a[1], sep=None, engine="python", encoding="utf-8-sig")
    per_game, summary = compare_marts(simon, ralf)
    out = Path(a[2])
    out.mkdir(parents=True, exist_ok=True)
    per_game.to_csv(out / "abgleich_je_spiel.csv", index=False, encoding="utf-8", lineterminator="\n")
    summary.to_csv(out / "abgleich_zusammenfassung.csv", index=False, encoding="utf-8", lineterminator="\n")
    print(summary.to_string(index=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())

"""KPI-Berechnung auf Spiel- und Saisonebene.

Formeln nach Arbeitsauftrag S. 5–6. **Status: technischer Entwurf.** Die fachlichen Definitionen von
SOLL, IST, Public-Anwesenden und Umsatzbasis sind noch offen (AA S. 10, Fragen 1–2). Brutto- und
Nettoumsatz werden deshalb strikt getrennt geführt, nie vermischt.

Regeln: Missing bleibt Missing (NaN), Division durch 0 oder Missing ergibt NaN. Saisonwerte sind
gewichtet (Σ Zähler / Σ Nenner über Spiele mit beiden Werten), nicht Mittelwerte von Spielquoten.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

KPI_DEFINITIONS: list[dict] = [
    {"kpi": "attendance_rate", "label": "Anwesenheitsquote", "formula": "IST / SOLL", "source": "AA S. 5"},
    {"kpi": "no_show_rate", "label": "No-Show-Quote", "formula": "1 − IST / SOLL", "source": "AA S. 5"},
    {"kpi": "no_show_abs", "label": "No-Show absolut", "formula": "SOLL − IST", "source": "AA S. 5"},
    {"kpi": "kf_gross_chf", "label": "Kundenfranken brutto (inkl. MwSt)",
     "formula": "Umsatz brutto / Public-Anwesende", "source": "AA S. 5; Basis offen (AA S. 6)"},
    {"kpi": "kf_net_chf", "label": "Kundenfranken netto (exkl. MwSt)",
     "formula": "Umsatz netto / Public-Anwesende", "source": "AA S. 5; Basis offen (AA S. 6)"},
    {"kpi": "receipts_per_public", "label": "Bons je Public-Anwesendem",
     "formula": "Bons / Public-Anwesende", "source": "AA S. 5 (≠ Kaufquote, AA S. 6)"},
    {"kpi": "avg_receipt_gross_chf", "label": "Ø Bon brutto", "formula": "Umsatz brutto / Bons", "source": "AA S. 5"},
    {"kpi": "avg_receipt_net_chf", "label": "Ø Bon netto", "formula": "Umsatz netto / Bons", "source": "AA S. 5"},
    {"kpi": "scan_vs_ist_rate", "label": "Scans vs. IST", "formula": "Scans / IST − 1",
     "source": "AA S. 6 (Abgleich IST/Scans); Scans ≠ eindeutige Besucher"},
    {"kpi": "share_arrived_45min_before", "label": "Anteil Scans ≥ 45 Min. vor Anpfiff",
     "formula": "Scans mit Minuten vor Anpfiff ≥ 45 / Scans", "source": "AA S. 7 (Paket D); Abgrenzung technisch"},
    {"kpi": "share_last_15min", "label": "Anteil Scans in letzten 15 Min.",
     "formula": "Scans mit 0 ≤ Minuten vor Anpfiff < 15 / Scans", "source": "AA S. 7 (Paket D); Abgrenzung technisch"},
]


def safe_ratio(numerator: pd.Series, denominator: pd.Series) -> pd.Series:
    """Quotient mit NaN statt Fehler/Unendlich, wenn Nenner ≤ 0 oder ein Wert fehlt."""
    num = numerator.astype("float64")
    den = denominator.astype("float64")
    return num.where(den > 0).div(den.where(den > 0))


def add_match_kpis(mart: pd.DataFrame) -> pd.DataFrame:
    """Ergänzt ``mart_match`` um Spiel-KPIs (siehe ``KPI_DEFINITIONS``)."""
    out = mart.copy()
    out["attendance_rate"] = safe_ratio(out["ist"], out["soll"])
    out["no_show_rate"] = 1 - out["attendance_rate"]
    out["no_show_abs"] = out["soll"] - out["ist"]
    out["kf_gross_chf"] = safe_ratio(out["revenue_gross_chf"], out["public_attendance"])
    out["kf_net_chf"] = safe_ratio(out["revenue_net_chf"], out["public_attendance"])
    out["receipts_per_public"] = safe_ratio(out["receipts"], out["public_attendance"])
    out["avg_receipt_gross_chf"] = safe_ratio(out["revenue_gross_chf"], out["receipts"])
    out["avg_receipt_net_chf"] = safe_ratio(out["revenue_net_chf"], out["receipts"])
    out["scan_vs_ist_rate"] = safe_ratio(out["scan_count"], out["ist"]) - 1
    return out


def kpi_checks(mart: pd.DataFrame) -> list[dict]:
    """Plausibilitätsprüfungen der KPIs (Identität KF = Bonsrate × Ø Bon, Wertebereiche)."""
    checks = []
    both = mart[["kf_gross_chf", "receipts_per_public", "avg_receipt_gross_chf"]].dropna()
    identity_ok = bool(np.allclose(both["kf_gross_chf"], both["receipts_per_public"] * both["avg_receipt_gross_chf"]))
    checks.append({"check_id": "K01", "description": "Identität KF = Bons/Public × Ø Bon (brutto)",
                   "status": "OK" if identity_ok else "FAIL", "detail": f"{len(both)} Spiele geprüft"})
    rate = mart["attendance_rate"].dropna()
    range_ok = bool(((rate >= 0) & (rate <= 1)).all())
    checks.append({"check_id": "K02", "description": "Anwesenheitsquote im Bereich [0, 1]",
                   "status": "OK" if range_ok else "WARN", "detail": f"{len(rate)} Spiele mit Wert"})
    n_missing_ist = int(mart["ist"].isna().sum())
    checks.append({"check_id": "M01", "description": "Fehlendes IST bleibt Missing (nicht 0)",
                   "status": "OK" if mart.loc[mart["ist"].isna(), "attendance_rate"].isna().all() else "FAIL",
                   "detail": f"{n_missing_ist} Spiel(e) ohne IST"})
    return checks


def season_summary(mart: pd.DataFrame) -> pd.DataFrame:
    """Gewichtete Saisonwerte (Σ Zähler / Σ Nenner) mit ausgewiesener Stichprobe je KPI."""
    rows = []
    for season, g in mart.groupby("season", sort=True):
        att = g[g["soll"].notna() & g["ist"].notna()]
        cat = g[g["public_attendance"].notna() & g["revenue_gross_chf"].notna()]
        rec = cat[cat["receipts"].notna()]
        rows.append({
            "season": season,
            "n_matches": len(g),
            "n_attendance": len(att),
            "attendance_rate_weighted": _ratio(att["ist"].sum(), att["soll"].sum()),
            "no_show_abs_sum": att["soll"].sum() - att["ist"].sum() if len(att) else np.nan,
            "n_catering": len(cat),
            "kf_gross_weighted_chf": _ratio(cat["revenue_gross_chf"].sum(), cat["public_attendance"].sum()),
            "kf_net_weighted_chf": _ratio(cat["revenue_net_chf"].sum(), cat["public_attendance"].sum()),
            "kf_gross_unweighted_mean_chf": cat["kf_gross_chf"].mean() if len(cat) else np.nan,
            "avg_receipt_gross_weighted_chf": _ratio(rec["revenue_gross_chf"].sum(), rec["receipts"].sum()),
            "n_access": int(g["has_access"].sum()),
        })
    return pd.DataFrame(rows)


def _ratio(num: float, den: float) -> float:
    return float(num) / float(den) if den and den > 0 else np.nan

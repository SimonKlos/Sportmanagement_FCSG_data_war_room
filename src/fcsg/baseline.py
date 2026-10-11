"""Baseline auf den bereinigten echten Daten (``data/clean/<run_id>/``): Spieltabelle, KPIs, Saisonwerte.

**Status: vorläufig.** Definitionen von SOLL/IST/Public Netto und Umsatzbasis sind offen (D-004/D-005);
die hier verwendeten Arbeitsdefinitionen stehen in ``docs/decisions.md`` (D-025). Deckungsbeitrag wird nicht
berechnet, solange keine Kostendaten vorliegen (D-003).

Ablauf (Join-Regel AA S. 4–5): Die Zuschauer-Historie liefert den Spielkalender (Herren-Pflichtspiele ab 21/22).
Jede andere Quelle wird **vor** dem Join auf ein Datum aggregiert und 1:1 angehängt; nicht zuordenbare Zeilen
landen im Unmatched-Report; jede Aggregation wird auf Summenerhalt geprüft.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

from fcsg.joins import JoinError, _check, assert_unique
from fcsg.metrics import safe_ratio

COMPETITIONS = ("Liga", "Cup", "UEFA")  # Herren-Pflichtspiele (D-016)
SINCE = "2021-07-01"
ENTRY_MIN_SEASON_SHARE = 0.8  # Eintrittsfeld der Einzeltickets nur verwendet, wenn je Saison ≥ 80 % befüllt
ACCESS_COMPLETE_TOL = 0.05  # D-018
LEAD_BUCKETS = [(0, 1, "0–1 Tage"), (2, 7, "2–7 Tage"), (8, 30, "8–30 Tage"), (31, 10_000, "> 30 Tage")]

KPI_DEFINITIONS_REAL: list[dict] = [
    {"kpi": "attendance_rate", "label": "Anwesenheitsquote", "formula": "IST / SOLL", "source": "AA S. 5; Definition offen (D-004)"},
    {"kpi": "no_show_rate", "label": "No-Show-Quote", "formula": "1 − IST / SOLL", "source": "AA S. 5"},
    {"kpi": "no_show_abs", "label": "No-Show absolut", "formula": "SOLL − IST", "source": "AA S. 5"},
    {"kpi": "kf_gross_chf", "label": "Kundenfranken brutto", "formula": "Catering-Umsatz inkl. MwSt / Public Netto (Catering-Datei)",
     "source": "AA S. 5; DQ S. 3; Basis offen (D-005)"},
    {"kpi": "kf_net_chf", "label": "Kundenfranken netto", "formula": "Catering-Umsatz exkl. MwSt / Public Netto", "source": "AA S. 5"},
    {"kpi": "receipts_per_public", "label": "Bons je Public-Anwesendem", "formula": "Transaktionen / Public Netto (ab 23/24)",
     "source": "AA S. 5; D-019"},
    {"kpi": "avg_receipt_gross_chf", "label": "Ø Bon brutto", "formula": "Umsatz inkl. MwSt / Transaktionen (ab 23/24)", "source": "AA S. 5; D-019"},
    {"kpi": "avg_receipt_net_chf", "label": "Ø Bon netto", "formula": "Umsatz exkl. MwSt / Transaktionen (ab 23/24)", "source": "AA S. 5; D-019"},
    {"kpi": "scan_vs_ist_rate", "label": "Scans vs. IST", "formula": "Scans / IST − 1", "source": "AA S. 6; Scans ≠ eindeutige Besucher"},
    {"kpi": "access_complete", "label": "Zutritt vollständig", "formula": "|Scans / IST − 1| ≤ 5 %", "source": "D-018"},
    {"kpi": "share_arrived_45min_before", "label": "Anteil Scans ≥ 45 Min. vor Anpfiff", "formula": "Scans mit ≥ 45 Min. Vorlauf / Scans",
     "source": "AA S. 7; D-008; nur bei vollständigem Zutritt auswerten"},
    {"kpi": "share_last_15min", "label": "Anteil Scans in letzten 15 Min.", "formula": "Scans mit 0 ≤ Min. < 15 / Scans", "source": "AA S. 7; D-008"},
    {"kpi": "arrival_median_min_before", "label": "Median Ankunft (Min. vor Anpfiff)", "formula": "scan-gewichteter Median", "source": "DQ S. 3"},
    {"kpi": "single_entry_rate", "label": "Eintrittsquote Einzeltickets", "formula": "eingetretene / verkaufte Einzelticket-Positionen",
     "source": "Einzeltickets-Export; nur Saisons mit Eintrittsfeld ≥ 80 % befüllt"},
    {"kpi": "deckungsbeitrag", "label": "Deckungsbeitrag", "formula": "nicht berechnet – keine Kosten-/Margendaten (D-003)", "source": "PA S. 2"},
]


# ----------------------------------------------------------------------------------------------------
# Laden
# ----------------------------------------------------------------------------------------------------

def load_clean(clean_root: Path) -> tuple[str, dict[str, pd.DataFrame], dict]:
    """Lädt den neuesten bereinigten Lauf (``clean_root/LATEST``).

    Returns:
        (clean_run_id, Tabellen, Manifest)

    Raises:
        ValueError: kein Lauf vorhanden, falscher Datenmodus oder Prüfungen mit FAIL.
    """
    latest = clean_root / "LATEST"
    if not latest.is_file():
        raise ValueError("Kein bereinigter Lauf gefunden (data/clean/LATEST fehlt); zuerst prepare-data ausführen.")
    run_id = latest.read_text(encoding="utf-8").strip()
    run_dir = clean_root / run_id
    manifest = json.loads((run_dir / "manifest.json").read_text(encoding="utf-8"))
    if manifest.get("data_mode") != "release_aggregates":
        raise ValueError(f"Bereinigter Lauf {run_id}: unerwarteter Datenmodus.")
    fails = [c["check_id"] for c in manifest.get("checks", []) if c["status"] == "FAIL"]
    if fails:
        raise ValueError(f"Bereinigter Lauf {run_id} hat FAIL-Prüfungen: {', '.join(fails)}")
    tables = {name: pd.read_csv(run_dir / f"{name}.csv") for name in manifest["outputs"]}
    return run_id, tables, manifest


# ----------------------------------------------------------------------------------------------------
# Hilfsfunktionen
# ----------------------------------------------------------------------------------------------------

def hhmm_to_min(s: pd.Series) -> pd.Series:
    """``'18:30'`` → 1110 (Minuten seit Mitternacht); ungültig → NaN."""
    parts = s.astype("string").str.extract(r"^(\d{1,2}):(\d{2})")
    minutes = pd.to_numeric(parts[0], errors="coerce") * 60 + pd.to_numeric(parts[1], errors="coerce")
    return minutes.astype("float64")


def guest_sector_note(remark: pd.Series) -> pd.Series:
    """Bemerkung der Historie → ``'geschlossen/exkl.'``, ``'zusatz'`` oder leer (D-022)."""
    t = remark.astype("string").str.lower()
    guest = t.str.contains("gäste|gaeste|b3", na=False)
    zusatz = guest & t.str.contains("zusatz", na=False)
    closed = guest & ~zusatz & t.str.contains("exkl|gesperrt|geschlossen|ohne", na=False)
    out = pd.Series(None, index=remark.index, dtype="object")
    out[closed] = "geschlossen/exkl."
    out[zusatz] = "zusatz"
    return out


def lead_bucket(days: pd.Series) -> pd.Series:
    out = pd.Series(pd.NA, index=days.index, dtype="string")
    for lo, hi, label in LEAD_BUCKETS:
        out[(days >= lo) & (days <= hi)] = label
    out[days < 0] = "ungültig (< 0)"
    return out


def weighted_median(values: pd.Series, weights: pd.Series) -> float:
    ok = values.notna() & weights.notna() & (weights > 0)
    if not ok.any():
        return np.nan
    v, w = values[ok].to_numpy(float), weights[ok].to_numpy(float)
    order = np.argsort(v)
    cum = np.cumsum(w[order])
    return float(v[order][np.searchsorted(cum, cum[-1] / 2)])


# ----------------------------------------------------------------------------------------------------
# Spieltabelle
# ----------------------------------------------------------------------------------------------------

@dataclass
class MartResult:
    mart: pd.DataFrame
    unmatched: pd.DataFrame
    checks: list[dict]


def _spine(history: pd.DataFrame) -> pd.DataFrame:
    h = history[history["competition_group"].isin(COMPETITIONS) & (history["match_date"] >= SINCE)].copy()
    assert_unique(h, ["match_date"], "attendance_history (Pflichtspiele)")
    spine = h[["match_date", "season", "competition", "competition_group", "weekday", "kickoff", "match_label",
               "soll", "ist", "ist_vip", "ist_guests", "secondary_market", "sold_out", "remark"]].copy()
    spine["guest_sector_note"] = guest_sector_note(spine["remark"])
    spine.insert(0, "match_id", "M" + spine["match_date"].str.replace("-", "", regex=False))
    return spine.sort_values("match_date").reset_index(drop=True)


def _unmatched_rows(df: pd.DataFrame, date_col: str, spine: pd.DataFrame, source: str, reason: str,
                    extra: pd.Series | None = None) -> pd.DataFrame:
    mask = ~df[date_col].isin(spine["match_date"])
    out = pd.DataFrame({"source": source, "match_date": df.loc[mask, date_col], "reason": reason})
    if extra is not None:
        out["detail"] = extra.reindex(df.index)[mask].astype("string")
    return out


def build_mart_match_real(t: dict[str, pd.DataFrame], today: str | None = None) -> MartResult:
    """Baut die Spieltabelle (1 Herren-Pflichtspiel pro Zeile) aus den bereinigten Tabellen.

    Args:
        t: Tabellen aus :func:`load_clean`.
        today: ISO-Datum; Kontextzeilen danach gelten als «noch nicht gespielt» (Default: heute).

    Returns:
        :class:`MartResult` mit Spieltabelle, Unmatched-Report und Prüfprotokoll.

    Raises:
        JoinError: Schlüssel nicht eindeutig oder Join-Kardinalität verletzt.
    """
    today = today or pd.Timestamp.today().strftime("%Y-%m-%d")
    checks: list[dict] = []
    unmatched: list[pd.DataFrame] = []
    spine = _spine(t["attendance_history"])
    checks.append(_check("J01", "Spielkalender: Herren-Pflichtspiele ab 21/22, Datum eindeutig", True, f"{len(spine)} Spiele"))

    # --- Catering (Herren, nicht abgesagt) -----------------------------------------------------------
    cat = t["catering_match"]
    cat = cat[(cat["event_class"] == "fcsg_herren") & (cat["match_date"] >= SINCE)]
    cancelled = cat[cat["cancelled_flag"].astype(bool)]
    cat = cat[~cat["cancelled_flag"].astype(bool)]
    assert_unique(cat, ["match_date"], "catering_match (Herren)")
    unmatched.append(pd.DataFrame({"source": "catering_match", "match_date": cancelled["match_date"],
                                   "reason": "Spiel abgesagt – ausgeschlossen"}))
    unmatched.append(_unmatched_rows(cat, "match_date", spine, "catering_match",
                                     "kein Pflichtspiel der Historie an diesem Datum (Freundschaftsspiel oder Datumskonflikt)",
                                     cat["competition"]))
    cat_cols = cat[["match_date", "public_attendance", "transactions", "revenue_total_gross", "revenue_total_net",
                    "kf_gross_reported", "guest_sector_attendance"]].rename(columns={
        "transactions": "receipts", "revenue_total_gross": "revenue_gross_chf", "revenue_total_net": "revenue_net_chf",
        "kf_gross_reported": "kf_gross_reported_chf"})

    # --- Zutritt: je Datum die Datei mit den meisten Scans (23/24 liegt in zwei Dateien) -------------
    acc = t["access_match_summary"]
    acc = acc[acc["team"] == "Herren"].sort_values(["match_date", "scans"], ascending=[True, False])
    chosen = acc.drop_duplicates("match_date", keep="first")
    secondary = acc[acc.duplicated("match_date", keep="first")]
    checks.append(_check("A01", "Zutritt: Datum in mehreren Dateien → Datei mit den meisten Scans", True,
                         f"{secondary['match_date'].nunique()} Daten doppelt; {int(secondary['scans'].sum())} Scans der "
                         f"Zweitdatei nicht addiert (von {int(acc['scans'].sum())})"))
    unmatched.append(_unmatched_rows(chosen, "match_date", spine, "access_match_summary",
                                     "Zutritt an Datum ohne Pflichtspiel der Historie", chosen["match_label"]))
    acc_cols = chosen[["match_date", "source_file", "scans"]].rename(columns={"source_file": "access_source_file",
                                                                             "scans": "scan_count"})

    # --- Ankunft aus Sektor-Minuten-Profil (nur gewählte Datei je Datum) -----------------------------
    sm = t["access_sector_minute"].merge(chosen[["source_file", "match_date"]], on=["source_file", "match_date"])
    sm = sm.merge(spine[["match_date", "kickoff"]], on="match_date", how="left")
    sm["min_before"] = hhmm_to_min(sm["kickoff"]) - hhmm_to_min(sm["scan_minute"])
    arrival = sm.groupby("match_date").apply(lambda g: pd.Series({
        "arrival_scans": g["scans"].sum(),
        "share_arrived_45min_before": g.loc[g["min_before"] >= 45, "scans"].sum() / g["scans"].sum(),
        "share_last_15min": g.loc[(g["min_before"] >= 0) & (g["min_before"] < 15), "scans"].sum() / g["scans"].sum(),
        "share_after_kickoff": g.loc[g["min_before"] < 0, "scans"].sum() / g["scans"].sum(),
        "arrival_median_min_before": weighted_median(g["min_before"], g["scans"]),
    }), include_groups=False).reset_index()

    # --- Kontext ---------------------------------------------------------------------------------------
    ctx = t["context_match"]
    assert_unique(ctx, ["match_date"], "context_match")
    future = ctx["match_date"] > today
    unmatched.append(_unmatched_rows(ctx[future], "match_date", spine, "context_match", "noch nicht gespielt"))
    unmatched.append(_unmatched_rows(ctx[~future], "match_date", spine, "context_match",
                                     "kein Pflichtspiel der Historie an diesem Datum (Datumskonflikt?)", ctx["opponent"]))
    ctx_cols = ctx[["match_date", "opponent", "table_rank_fcsg", "table_rank_opp", "table_points_opp", "form_fcsg_points",
                    "form_opp_points", "tv_free_srf", "temp_day_mean_c", "precip_day_mm", "wind_day_kmh", "school_holiday",
                    "school_holiday_source", "public_holiday", "parallel_event"]].copy()
    ctx_cols["has_context"] = True

    # --- Einzeltickets 25/26+ (Ticket-CSVs) -----------------------------------------------------------
    sl = t["tickets_single_leadtime"]
    sl = sl[sl["team"] == "Herren"]
    single = sl.groupby("match_date").agg(single_tickets_n=("n_tickets", "sum"),
                                          single_tickets_lead_le1=("n_tickets", lambda s: s[sl.loc[s.index, "lead_days"] <= 1].sum()),
                                          single_revenue_chf=("revenue_chf", "sum")).reset_index()
    unmatched.append(_unmatched_rows(single, "match_date", spine, "tickets_single_leadtime", "Ticketdatei ohne Pflichtspiel"))

    # --- Einzeltickets-Exporte 21/22–24/25 (inkl. Eintrittsfeld) --------------------------------------
    hl = t["tickets_hist_leadtime"]
    hl = hl[hl["is_match"].astype(bool)]
    season_fill = hl.groupby("season_label")["n_entered"].sum() / hl.groupby("season_label")["n_rows"].sum()
    entry_ok = set(season_fill[season_fill >= ENTRY_MIN_SEASON_SHARE].index)
    hist = hl.groupby("event_date").agg(hist_rows=("n_rows", "sum"), hist_entered=("n_entered", "sum"),
                                        hist_lead_le1=("n_rows", lambda s: s[hl.loc[s.index, "lead_days"].between(0, 1)].sum()),
                                        season_label=("season_label", "first")).reset_index()
    hist = hist.rename(columns={"event_date": "match_date"})
    hist["entry_field_reliable"] = hist["season_label"].isin(entry_ok)
    unmatched.append(_unmatched_rows(hist, "match_date", spine, "tickets_hist_leadtime", "Einzelticket-Event ohne Pflichtspiel"))
    checks.append(_check("E01", "Eintrittsfeld Einzeltickets: verwendete Saisons (≥ 80 % befüllt)", True,
                         "; ".join(f"{s}: {v:.0%}" for s, v in season_fill.items())))

    # --- Join -----------------------------------------------------------------------------------------
    mart = spine
    for part in (cat_cols, acc_cols, arrival, ctx_cols, single, hist.drop(columns=["season_label"])):
        assert_unique(part, ["match_date"], "Teiltabelle")
        mart = mart.merge(part, on="match_date", how="left", validate="one_to_one")
    if len(mart) != len(spine):
        raise JoinError(f"Join-Kardinalität verletzt: {len(mart)} statt {len(spine)} Zeilen")
    checks.append(_check("J02", "Spieltabelle: Zeilen = Pflichtspiele (1:1-Join)", True, f"{len(mart)} Zeilen"))
    mart["has_context"] = mart["has_context"].fillna(False).astype(bool)
    mart["entry_field_reliable"] = mart["entry_field_reliable"].astype("boolean").fillna(False).astype(bool)

    # --- Summenerhalt (zugeordnete Quellzeilen → Spieltabelle) ----------------------------------------
    def keep(df, col="match_date"):
        return df[df[col].isin(spine["match_date"])]
    sums = [
        ("S01", "Catering-Umsatz brutto", keep(cat)["revenue_total_gross"].sum(), mart["revenue_gross_chf"].sum()),
        ("S02", "Catering-Umsatz netto", keep(cat)["revenue_total_net"].sum(), mart["revenue_net_chf"].sum()),
        ("S03", "Catering-Transaktionen", keep(cat)["transactions"].sum(), mart["receipts"].sum()),
        ("S04", "Scans (gewählte Datei)", keep(chosen)["scans"].sum(), mart["scan_count"].sum()),
        ("S05", "Scans Ankunftsprofil = Scans Zusammenfassung", keep(chosen)["scans"].sum(), mart["arrival_scans"].sum()),
        ("S06", "Einzeltickets 25/26+", keep(single)["single_tickets_n"].sum(), mart["single_tickets_n"].sum()),
        ("S07", "Einzelticket-Positionen 21/22–24/25", keep(hist)["hist_rows"].sum(), mart["hist_rows"].sum()),
    ]
    for cid, label, src, dst in sums:
        ok = abs(float(src) - float(dst)) <= 1e-6 * max(1.0, abs(float(src)))
        checks.append(_check(cid, f"Summenerhalt {label} (Quelle → Spieltabelle)", ok, f"Quelle {src:,.2f} / Spieltabelle {dst:,.2f}"))

    um = pd.concat([u for u in unmatched if len(u)], ignore_index=True)
    checks.append(_check("U01", "Unmatched-Report erzeugt (Pflichtoutput)", True, f"{len(um)} Einträge"))
    return MartResult(mart, um, checks)


# ----------------------------------------------------------------------------------------------------
# KPIs und Saisonwerte
# ----------------------------------------------------------------------------------------------------

def add_real_kpis(mart: pd.DataFrame) -> pd.DataFrame:
    """Spiel-KPIs (``KPI_DEFINITIONS_REAL``); fehlende Werte bleiben fehlend."""
    m = mart.copy()
    m["attendance_rate"] = safe_ratio(m["ist"], m["soll"])
    m["no_show_rate"] = 1 - m["attendance_rate"]
    m["no_show_abs"] = m["soll"] - m["ist"]
    m["kf_gross_chf"] = safe_ratio(m["revenue_gross_chf"], m["public_attendance"])
    m["kf_net_chf"] = safe_ratio(m["revenue_net_chf"], m["public_attendance"])
    m["receipts_per_public"] = safe_ratio(m["receipts"], m["public_attendance"])
    m["avg_receipt_gross_chf"] = safe_ratio(m["revenue_gross_chf"], m["receipts"])
    m["avg_receipt_net_chf"] = safe_ratio(m["revenue_net_chf"], m["receipts"])
    m["scan_vs_ist_rate"] = safe_ratio(m["scan_count"], m["ist"]) - 1
    m["access_complete"] = np.where(m["scan_vs_ist_rate"].isna(), np.nan,
                                    (m["scan_vs_ist_rate"].abs() <= ACCESS_COMPLETE_TOL).astype(float))
    m["single_entry_rate"] = safe_ratio(m["hist_entered"], m["hist_rows"]).where(m["entry_field_reliable"])
    m["single_share_lead_le1"] = safe_ratio(m["single_tickets_lead_le1"], m["single_tickets_n"]).fillna(
        safe_ratio(m["hist_lead_le1"], m["hist_rows"]))
    m["public_vs_ist_rate"] = safe_ratio(m["public_attendance"], m["ist"]) - 1
    return m


def kpi_checks_real(m: pd.DataFrame) -> list[dict]:
    """Plausibilität: Identität KF = Bonsrate × Ø Bon, KF vs. von der Quelle berechneter KF, Wertebereiche."""
    checks = []
    b = m[["kf_gross_chf", "receipts_per_public", "avg_receipt_gross_chf"]].dropna()
    checks.append(_check("K01", "Identität KF = Bons/Public × Ø Bon (brutto)",
                         bool(np.allclose(b["kf_gross_chf"], b["receipts_per_public"] * b["avg_receipt_gross_chf"])),
                         f"{len(b)} Spiele geprüft"))
    r = m[["kf_gross_chf", "kf_gross_reported_chf"]].dropna()
    diff = (r["kf_gross_chf"] - r["kf_gross_reported_chf"]).abs()
    checks.append(_check("K02", "KF brutto = von der Quelle berechneter KF (± 0.05 CHF)", bool((diff <= 0.05).all()),
                         f"{len(r)} Spiele; max. Abweichung {diff.max():.3f} CHF", warn_only=True))
    rate = m["attendance_rate"].dropna()
    checks.append(_check("K03", "Anwesenheitsquote im Bereich [0, 1]", bool(rate.between(0, 1).all()),
                         f"{len(rate)} Spiele; Spanne {rate.min():.3f}–{rate.max():.3f}", warn_only=True))
    rb = m.loc[m["season"] < "2023/24", "receipts"]
    checks.append(_check("K04", "Bons erst ab 23/24 vorhanden (D-019)", bool(rb.isna().all()),
                         f"{int(rb.notna().sum())} Spiele vor 23/24 mit Bons", warn_only=True))
    return checks


def _wr(num: pd.Series, den: pd.Series) -> float:
    ok = num.notna() & den.notna() & (den > 0)
    return float(num[ok].sum() / den[ok].sum()) if ok.any() else np.nan


def season_summary_real(m: pd.DataFrame) -> pd.DataFrame:
    """Gewichtete Saisonwerte (Σ/Σ) über alle Herren-Pflichtspiele; Stichprobe je KPI ausgewiesen."""
    rows = []
    for season, g in m.groupby("season", sort=True):
        cat = g[g["public_attendance"].notna() & g["revenue_gross_chf"].notna()]
        rec = cat[cat["receipts"].notna()]
        acc = g[g["access_complete"] == 1]
        rows.append({
            "season": season, "n_matches": len(g),
            "ist_sum": g["ist"].sum(), "attendance_rate_weighted": _wr(g["ist"], g["soll"]),
            "no_show_abs_sum": (g["soll"] - g["ist"]).sum(),
            "n_catering": len(cat), "public_attendance_sum": cat["public_attendance"].sum(),
            "revenue_gross_chf_sum": cat["revenue_gross_chf"].sum(), "revenue_net_chf_sum": cat["revenue_net_chf"].sum(),
            "kf_gross_weighted_chf": _wr(cat["revenue_gross_chf"], cat["public_attendance"]),
            "kf_net_weighted_chf": _wr(cat["revenue_net_chf"], cat["public_attendance"]),
            "kf_gross_unweighted_mean_chf": cat["kf_gross_chf"].mean() if len(cat) else np.nan,
            "n_receipts": len(rec), "receipts_per_public_weighted": _wr(rec["receipts"], rec["public_attendance"]),
            "avg_receipt_gross_weighted_chf": _wr(rec["revenue_gross_chf"], rec["receipts"]),
            "n_access_complete": len(acc),
            "share_45min_weighted": _wr(acc["share_arrived_45min_before"] * acc["scan_count"], acc["scan_count"]),
            "share_last15_weighted": _wr(acc["share_last_15min"] * acc["scan_count"], acc["scan_count"]),
        })
    return pd.DataFrame(rows)


def coverage_real(m: pd.DataFrame) -> pd.DataFrame:
    """Abdeckung je Saison und gemeinsame Stichproben der Hypothesen (keine fiktive Gesamtstichprobe)."""
    flags = {
        "has_catering": m["revenue_gross_chf"].notna(), "has_receipts": m["receipts"].notna(),
        "has_access": m["scan_count"].notna(), "access_complete": m["access_complete"] == 1,
        "has_context": m["has_context"], "has_ticket_leadtime": m["single_share_lead_le1"].notna(),
        "has_entry_rate": m["single_entry_rate"].notna(),
        "sample_H1": m["revenue_gross_chf"].notna() & (m["ist"] > 0),
        "sample_H2": (m["access_complete"] == 1) & m["receipts"].notna() & m["share_arrived_45min_before"].notna(),
        "sample_K1": m["has_context"] & m["revenue_gross_chf"].notna(),
    }
    df = pd.DataFrame(flags).assign(season=m["season"])
    out = df.groupby("season").sum().astype(int)
    out.insert(0, "n_matches", m.groupby("season").size())
    out.loc["Total"] = out.sum()
    return out.reset_index()


# ----------------------------------------------------------------------------------------------------
# Abgleich mit Retos Sichtung (DQ S. 3–4) und Quell-Tab «Entwicklung»
# ----------------------------------------------------------------------------------------------------

RETO_VALUES = [
    # (ID, Kennzahl, Scope, Retos Wert, Einheit, Quelle)
    ("R-01", "Catering-Umsatz brutto, Meisterschaft", "Liga 2021/22", 2.8e6, "CHF", "DQ S. 4 (≈)"),
    ("R-02", "Catering-Umsatz brutto, Meisterschaft", "Liga 2025/26", 4.0e6, "CHF", "DQ S. 4 (≈)"),
    ("R-03", "KF brutto (Σ Umsatz / Σ Public)", "Liga 2021/22", 13.68, "CHF", "DQ S. 4"),
    ("R-04", "KF brutto (Σ Umsatz / Σ Public)", "Liga 2025/26", 15.27, "CHF", "DQ S. 4"),
    ("R-05", "Bons je Public-Anwesendem", "Pflicht 2025/26–2026/27", 0.95, "Bons", "DQ S. 4 (≈)"),
    ("R-06", "Ø Bon brutto", "Pflicht 2025/26–2026/27", 16.70, "CHF", "DQ S. 4 (≈)"),
    ("R-07", "Scans vs. IST (Mittel)", "Pflicht 2025/26–2026/27", -0.004, "Anteil", "DQ S. 3"),
    ("R-08", "Median Ankunft vor Anpfiff", "Pflicht 2025/26–2026/27", 37.0, "Min.", "DQ S. 3 (≈)"),
    ("R-09", "Anteil Scans ≥ 45 Min. vorher", "Pflicht 2025/26–2026/27", 0.41, "Anteil", "DQ S. 3 (≈)"),
    ("R-10", "Anteil Scans letzte 15 Min.", "Pflicht 2025/26–2026/27", 0.17, "Anteil", "DQ S. 3 (≈)"),
    ("R-11", "Elastizität Catering-Umsatz / Zuschauer", "Retos 22 Spiele", 1.14, "–", "DQ S. 4 («Modell»)"),
]


def reto_comparison(m: pd.DataFrame, elasticity: float | None = None) -> pd.DataFrame:
    """Vergleicht eigene Werte (vorläufige Definitionen) mit Retos Sichtungswerten."""
    liga = m[m["competition_group"] == "Liga"]
    recent = m[m["season"].isin(["2025/26", "2026/27"])]
    rec = recent[recent["receipts"].notna() & recent["public_attendance"].notna()]
    acc = recent[recent["scan_count"].notna()]
    ours = {
        "R-01": liga.loc[liga["season"] == "2021/22", "revenue_gross_chf"].sum(),
        "R-02": liga.loc[liga["season"] == "2025/26", "revenue_gross_chf"].sum(),
        "R-03": _wr(*(liga.loc[liga["season"] == "2021/22", c] for c in ("revenue_gross_chf", "public_attendance"))),
        "R-04": _wr(*(liga.loc[liga["season"] == "2025/26", c] for c in ("revenue_gross_chf", "public_attendance"))),
        "R-05": _wr(rec["receipts"], rec["public_attendance"]),
        "R-06": _wr(rec["revenue_gross_chf"], rec["receipts"]),
        "R-07": acc["scan_vs_ist_rate"].mean(),
        "R-08": weighted_median(acc["arrival_median_min_before"], acc["scan_count"]),
        "R-09": _wr(acc["share_arrived_45min_before"] * acc["scan_count"], acc["scan_count"]),
        "R-10": _wr(acc["share_last_15min"] * acc["scan_count"], acc["scan_count"]),
        "R-11": elasticity if elasticity is not None else np.nan,
    }
    n = {"R-01": (liga["season"] == "2021/22").sum(), "R-02": (liga["season"] == "2025/26").sum(),
         "R-03": (liga["season"] == "2021/22").sum(), "R-04": (liga["season"] == "2025/26").sum(),
         "R-05": len(rec), "R-06": len(rec), "R-07": len(acc), "R-08": len(acc), "R-09": len(acc), "R-10": len(acc)}
    rows = []
    for rid, label, scope, reto, unit, src in RETO_VALUES:
        val = ours[rid]
        rel = (val - reto) / abs(reto) if pd.notna(val) else np.nan
        # Anteile in Prozentpunkten vergleichen (relative Abweichung bei Werten nahe 0 irreführend), sonst ≤ 5 % relativ.
        same = abs(val - reto) <= 0.01 if unit == "Anteil" else abs(rel) <= 0.05
        rule = "≤ 1 Pp." if unit == "Anteil" else "≤ 5 %"
        rows.append({"id": rid, "kpi": label, "scope": scope, "reto_value": reto, "our_value": val, "unit": unit,
                     "abs_diff": val - reto, "rel_diff": rel, "n_matches": n.get(rid, np.nan), "reto_source": src,
                     "status": "nicht berechnet" if pd.isna(val) else (f"übereinstimmend ({rule})" if same
                                                                         else "abweichend – Definition prüfen")})
    df = pd.DataFrame(rows)
    df.loc[df["id"] == "R-08", "note"] = "Median der Spielmediane (scan-gewichtet), nicht Median aller Scans"
    df.loc[df["id"] == "R-10", "note"] = "eigene Abgrenzung 0 ≤ Min. < 15 vor Anpfiff (D-008), Scans nach Anpfiff nicht enthalten"
    df.loc[df["id"] == "R-11", "note"] = "eigener Wert = H1 (log-log, saison-zentriert, alle Pflichtspiele)"
    return df


def source_total_check(t: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """Σ Catering-Umsatz Meisterschaft je Saison aus den Spielzeilen vs. Quell-Tab «Entwicklung»."""
    cat = t["catering_match"]
    cat = cat[(cat["event_class"] == "fcsg_herren") & cat["competition"].astype("string").str.startswith("Meisterschaft")
              & ~cat["cancelled_flag"].astype(bool)]  # abgesagte Spiele fehlen auch im Tab «Entwicklung»
    own = cat.groupby("season").agg(rows_revenue_gross=("revenue_total_gross", "sum"), rows_n=("match_date", "size"))
    dev = t["catering_season_summary"]
    dev = dev[dev["competition_label"].astype("string").str.match(r"Meister\w+ \d{2}/\d{2}$", na=False)].copy()
    dev["season"] = dev["season"].astype("string").str.replace(r"^(\d{4})/\d{2}(\d{2})$", r"\1/\2", regex=True)
    dev = dev.set_index("season")[["revenue_total_gross", "n_events"]].rename(
        columns={"revenue_total_gross": "entwicklung_revenue_gross", "n_events": "entwicklung_n"})
    out = own.join(dev, how="outer").reset_index()
    out = out[out["season"] >= SINCE[:4]].reset_index(drop=True)
    out["rel_diff"] = out["rows_revenue_gross"] / out["entwicklung_revenue_gross"] - 1
    out["status"] = np.where(out["rel_diff"].abs() <= 0.005, "OK",
                             np.where(out["rows_n"] != out["entwicklung_n"], "WARN – Anzahl Spiele weicht ab", "WARN"))
    return out

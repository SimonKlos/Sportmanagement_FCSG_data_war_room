"""Spielkalender, Aggregation der Faktentabellen und Join zu ``mart_match``.

Umsetzung der Join-Regel aus dem Arbeitsauftrag (S. 4–5): Jede Faktentabelle wird **vor** dem Join
auf die Spielebene aggregiert; der Join erfolgt eins-zu-eins über ``match_date``; nicht zuordenbare
Zeilen landen im Unmatched-Report statt stillschweigend zu verschwinden.
"""

from __future__ import annotations

import pandas as pd


class JoinError(ValueError):
    """Schlüssel nicht eindeutig oder Join-Kardinalität verletzt."""


def assert_unique(df: pd.DataFrame, key: list[str], source: str) -> None:
    """Bricht ab, wenn ``key`` in ``df`` nicht eindeutig ist (nur Anzahl in der Meldung)."""
    n_dup = int(df.duplicated(subset=key, keep=False).sum())
    if n_dup:
        raise JoinError(f"[{source}] Schlüssel {key} nicht eindeutig: {n_dup} betroffene Zeilen")


def build_dim_match(attendance: pd.DataFrame) -> pd.DataFrame:
    """Spielkalender ``dim_match`` aus der Anwesenheitsquelle.

    Annahme (technisch, nicht fachlich freigegeben): Die Anwesenheitsquelle definiert die Menge der
    Heimspiele. Mehrere Heimspiele am selben Datum sind nicht vorgesehen und führen zum Abbruch,
    weil Datum allein dann nicht als Schlüssel reicht (AA S. 4).
    """
    assert_unique(attendance, ["match_date"], "attendance_match")
    dim = attendance[["match_date", "season", "competition", "opponent_label", "kickoff_local"]].copy()
    dim.insert(0, "match_id", "M" + pd.to_datetime(dim["match_date"]).dt.strftime("%Y%m%d"))
    return dim.sort_values("match_date").reset_index(drop=True)


def split_catering_events(catering: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Trennt Spiel-Zeilen (``event_type == 'match'``) von anderen Events (z. B. Public Viewing).

    Returns:
        ``(match_rows, excluded_rows)``; ausgeschlossene Zeilen werden im Report ausgewiesen.
    """
    is_match = catering["event_type"] == "match"
    return catering[is_match].copy(), catering[~is_match].copy()


def aggregate_access(scans: pd.DataFrame) -> pd.DataFrame:
    """Aggregiert Einzelscans auf ein Spiel pro Zeile.

    Kennzahlen (technische Entwürfe, siehe Quellen und interne Dokumentation/data_dictionary.md):
    ``scan_count``, ``arrival_median_min_before``, ``share_arrived_45min_before`` (Scan ≥ 45 Min. vor
    Anpfiff), ``share_last_15min`` (0 ≤ Minuten vor Anpfiff < 15). Scans sind **keine** eindeutigen
    Besucher (Mehrfach-/Wiedereintritt ungeprüft).
    """
    minutes = scans["minutes_before_kickoff"]
    tmp = scans.assign(
        _early=(minutes >= 45).astype(float),
        _late=((minutes >= 0) & (minutes < 15)).astype(float),
    )
    agg = tmp.groupby("match_date", as_index=False).agg(
        scan_count=("minutes_before_kickoff", "size"),
        arrival_median_min_before=("minutes_before_kickoff", "median"),
        share_arrived_45min_before=("_early", "mean"),
        share_last_15min=("_late", "mean"),
    )
    agg["scan_count"] = agg["scan_count"].astype("float64")
    return agg


def _unmatched(fact: pd.DataFrame, dim: pd.DataFrame, source: str, reason: str) -> pd.DataFrame:
    """Zeilen aus ``fact``, deren ``match_date`` nicht im Spielkalender vorkommt."""
    mask = ~fact["match_date"].isin(dim["match_date"])
    return pd.DataFrame({"source": source, "match_date": fact.loc[mask, "match_date"], "reason": reason})


def build_mart_match(
    attendance: pd.DataFrame, catering: pd.DataFrame, scans: pd.DataFrame
) -> tuple[pd.DataFrame, pd.DataFrame, list[dict]]:
    """Baut ``mart_match`` (1 Heimspiel pro Zeile) mit Prüfprotokoll.

    Returns:
        ``(mart, unmatched_report, checks)``. ``checks`` ist eine Liste von Dicts mit
        ``check_id, description, status (OK/WARN/FAIL), detail``.

    Raises:
        JoinError: bei nicht eindeutigen Schlüsseln oder verletzter Join-Kardinalität.
    """
    checks: list[dict] = []
    dim = build_dim_match(attendance)
    checks.append(_check("J01", "attendance_match: match_date eindeutig", True, f"{len(dim)} Heimspiele"))

    cat_match, cat_excluded = split_catering_events(catering)
    assert_unique(cat_match, ["match_date"], "catering_match (event_type=match)")
    checks.append(_check("J02", "catering_match: Spiel-Zeilen je Datum eindeutig", True, f"{len(cat_match)} Spiel-Zeilen"))
    checks.append(_check(
        "J03", "catering_match: Nicht-Spiel-Events ausgeschlossen (nicht mit Spielen verbunden)",
        len(cat_excluded) == 0, f"{len(cat_excluded)} Event-Zeile(n) ausgeschlossen", warn_only=True,
    ))

    access_agg = aggregate_access(scans)
    assert_unique(access_agg, ["match_date"], "access_scans (aggregiert)")

    unmatched = pd.concat(
        [
            pd.DataFrame({"source": "catering_match", "match_date": cat_excluded["match_date"],
                          "reason": "event_type != match (z. B. Public Viewing) – bewusst ausgeschlossen"}),
            _unmatched(cat_match, dim, "catering_match", "Datum nicht im Spielkalender"),
            _unmatched(access_agg, dim, "access_scans", "Datum nicht im Spielkalender"),
        ],
        ignore_index=True,
    )

    att_cols = ["match_date", "soll", "ist", "ist_vip", "ist_guests"]
    cat_cols = ["match_date", "public_attendance", "receipts", "revenue_gross_chf", "revenue_net_chf"]
    mart = (
        dim.merge(attendance[att_cols], on="match_date", how="left", validate="one_to_one")
        .merge(cat_match[cat_cols], on="match_date", how="left", validate="one_to_one")
        .merge(access_agg, on="match_date", how="left", validate="one_to_one")
    )

    if len(mart) != len(dim):
        raise JoinError(f"Join-Kardinalität verletzt: {len(mart)} Zeilen statt {len(dim)}")
    checks.append(_check("J04", "mart_match: Zeilen = Heimspiele (1:1-Join)", True, f"{len(mart)} Zeilen"))

    mart["has_attendance"] = mart["soll"].notna() & mart["ist"].notna()
    mart["has_catering"] = mart["match_date"].isin(cat_match["match_date"])
    mart["has_access"] = mart["match_date"].isin(access_agg["match_date"])

    # Summenerhalt: alles, was zuordenbar war, muss im Mart wieder vollständig auftauchen.
    matched_cat = cat_match[cat_match["match_date"].isin(dim["match_date"])]
    for i, col in enumerate(("revenue_gross_chf", "revenue_net_chf", "receipts"), start=1):
        ok = _close(matched_cat[col].sum(), mart[col].sum())
        checks.append(_check(f"S0{i}", f"Summenerhalt {col} (Catering zugeordnet → Mart)", ok,
                             f"Quelle {matched_cat[col].sum():.2f} / Mart {mart[col].sum():.2f}"))
    matched_scans = int(scans["match_date"].isin(dim["match_date"]).sum())
    checks.append(_check("S04", "Summenerhalt Scans (zugeordnet → Mart)",
                         _close(matched_scans, mart["scan_count"].sum()),
                         f"Quelle {matched_scans} / Mart {mart['scan_count'].sum():.0f}"))
    checks.append(_check("U01", "Unmatched-Report erzeugt (Pflichtoutput)", True, f"{len(unmatched)} Einträge"))
    return mart, unmatched, checks


def _close(a: float, b: float, tol: float = 1e-6) -> bool:
    return abs(float(a) - float(b)) <= tol


def _check(check_id: str, description: str, ok: bool, detail: str, warn_only: bool = False) -> dict:
    status = "OK" if ok else ("WARN" if warn_only else "FAIL")
    return {"check_id": check_id, "description": description, "status": status, "detail": detail}

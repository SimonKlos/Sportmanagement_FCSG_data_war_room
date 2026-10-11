"""Gemeinsame Test-Fixtures. Alle Tests arbeiten ausschliesslich mit künstlichen Daten."""

import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from fcsg.io import load_all_sources

FIXTURE_DIR = Path(__file__).parent / "fixtures" / "synthetic_mini"


@pytest.fixture
def sources():
    return load_all_sources(FIXTURE_DIR)


@pytest.fixture
def tmp_config(tmp_path: Path) -> Path:
    """Konfiguration, die die Fixture liest und in ``tmp_path/outputs`` schreibt."""
    cfg = tmp_path / "project.yaml"
    cfg.write_text(
        "data_mode: synthetic_fixture\n"
        f"input_dir: '{FIXTURE_DIR.as_posix()}'\n"
        f"output_dir: '{(tmp_path / 'outputs').as_posix()}'\n"
        "timezone: Europe/Zurich\n",
        encoding="utf-8",
    )
    return cfg


# ----------------------------------------------------------------------------------------------------
# Künstliche Tabellen im Format von data/clean/<run_id>/ (KEINE Clubdaten; Daten 2098–2100)
# ----------------------------------------------------------------------------------------------------

N_GAMES = 10  # je Saison


def make_clean_tables() -> dict[str, pd.DataFrame]:
    """Zwei Saisons à 10 Liga-Heimspiele mit bekannten Effekten.

    - Catering-Umsatz = 15 CHF × IST (Elastizität genau 1).
    - Bons nur in Saison 2099/00; Bons je Public steigt mit dem Anteil früher Scans.
    - Zutritt: 1 Datum zusätzlich in einer Zweitdatei (weniger Scans) → Regel «meiste Scans».
    - Einzeltickets 2098/99: Kurzfristkäufe 95 % Eintritt, Frühkäufe (> 30 Tage) 80 %.
    - Nicht zuordenbar: 1 Freundschaftsspiel, 1 abgesagtes Spiel, 1 Kontextzeile in der Zukunft.
    """
    rng = np.random.default_rng(7)
    rows_h, rows_c, rows_a, rows_sm, rows_k, rows_sl, rows_hl = [], [], [], [], [], [], []
    for s_i, (season, year) in enumerate((("2098/99", 2098), ("2099/00", 2099))):
        for g in range(N_GAMES):
            date = f"{year}-{8 + g // 3:02d}-{1 + 7 * (g % 3):02d}"
            soll = 18000.0
            ist = float(round(soll * (0.70 + 0.02 * g)))
            public = ist - 500
            early = 0.30 + 0.03 * g  # Anteil früher Scans steigt mit g
            rows_h.append({"season": season, "competition": "Meisterschaft", "match_date": date, "weekday": "Samstag",
                           "kickoff_raw": "18:00", "match_label": f"FCSG - Test {g}", "soll": soll, "ist": ist,
                           "ist_vip": np.nan, "ist_guests": np.nan, "secondary_market": np.nan,
                           "no_show_rate_reported": np.nan, "no_show_impact_secondary_reported": np.nan,
                           "utilization_excl_guests_reported": np.nan, "sold_out": float(g >= 7),
                           "remark": "ausverkauft (exkl. Gästesektor)" if g >= 8 else None, "kickoff": "18:00",
                           "competition_group": "Liga"})
            rev = 15.0 * ist
            tx = public * (0.5 + early) if s_i == 1 else np.nan
            rows_c.append({"source_tab": season, "match_date": date, "match_label": f"FCSG - Test {g}",
                           "competition": "Meisterschaft", "public_attendance": public, "transactions": tx,
                           "revenue_total_gross": rev, "revenue_total_net": rev / 1.081, "kf_gross_reported": rev / public,
                           "guest_sector_attendance": np.nan, "event_class": "fcsg_herren", "cancelled_flag": False,
                           "season": season})
            # Zutritt: Scans = IST (vollständig); Anteil «early» 60 Min. vor Anpfiff, Rest 10 Min. vorher
            scans = int(ist)
            n_early = int(round(scans * early))
            rows_a.append({"source_file": "zutritt_a.txt", "team": "Herren", "match_date": date, "match_label": "BSL",
                           "scans": scans, "n_distinct_tickets": scans, "first_scan": "17:00:00", "last_scan": "18:10:00",
                           "n_readers": 4, "venue_messages": "", "scans_per_ticket": 1.0, "season": season})
            rows_sm += [{"source_file": "zutritt_a.txt", "team": "Herren", "match_date": date, "sector": "A",
                         "scan_minute": "17:00", "scans": n_early},
                        {"source_file": "zutritt_a.txt", "team": "Herren", "match_date": date, "sector": "B",
                         "scan_minute": "17:50", "scans": scans - n_early}]
            rows_k.append({"match_date": date, "season": season, "opponent": f"Test {g}", "table_rank_fcsg": 5.0,
                           "table_rank_opp": float(1 + g), "table_points_opp": float(30 - g), "form_fcsg_points": 7.0,
                           "form_opp_points": float(rng.integers(0, 15)), "tv_free_srf": float(g % 2),
                           "temp_day_mean_c": 10.0 + g, "precip_day_mm": float(rng.integers(0, 5)),
                           "wind_day_kmh": 10.0, "school_holiday": float(g % 3 == 0), "school_holiday_source": "team",
                           "public_holiday": 0.0, "parallel_event": 0.0})
            if s_i == 1:
                rows_sl += [{"source_file": "x.csv", "season_folder": "2099", "folder": "MS", "team": "Herren",
                             "match_date": date, "event_code": "MS", "tribune": "A", "channel": "Web", "lead_days": ld,
                             "n_tickets": n, "revenue_chf": 25.0 * n} for ld, n in ((0, 100), (20, 300))]
            else:
                for ld, n, rate in ((1, 1000, 0.95), (5, 1000, 0.93), (15, 1000, 0.90), (60, 1000, 0.80), (-3, 10, 1.0)):
                    rows_hl.append({"source_file": "E.xlsx", "season_label": "2098/2099", "event_date": date,
                                    "event_id": g, "event_label": "FC St.Gallen 1879 - Test", "opponent": "Test",
                                    "is_match": True, "channel": "Web", "seat_group": "A", "lead_days": ld,
                                    "n_rows": n, "n_tickets": float(n), "n_entered": int(n * rate)})
    # Zweitdatei für 1 Datum (weniger Scans, darf nicht addiert werden)
    rows_a.append(dict(rows_a[0], source_file="zutritt_b.txt", scans=40, n_distinct_tickets=40))
    rows_sm.append({"source_file": "zutritt_b.txt", "team": "Herren", "match_date": rows_a[0]["match_date"],
                    "sector": "A", "scan_minute": "17:30", "scans": 40})
    # nicht zuordenbar
    rows_c.append(dict(rows_c[0], match_date="2098-07-15", competition="Freundschaftsspiel", season="2098/99"))
    rows_c.append(dict(rows_c[1], match_date="2099-06-01", competition="Meisterschaft  Spiel abgesagt",
                       cancelled_flag=True, season="2098/99"))
    rows_k.append(dict(rows_k[-1], match_date="2100-05-30", season="2099/00"))
    rows_h.append(dict(rows_h[0], match_date="2098-07-20", competition="Testspiel", competition_group="Testspiel"))

    hist = pd.DataFrame(rows_h)
    cat = pd.DataFrame(rows_c)
    liga = cat[cat["competition"] == "Meisterschaft"]
    dev = pd.DataFrame([{"competition_label": f"Meisterschaft {s[2:]}", "season": f"{s[:4]}/{int(s[:4]) + 1}",
                         "n_events": float(len(g)), "attendance": g["public_attendance"].sum(),
                         "revenue_total_gross": g["revenue_total_gross"].sum(), "revenue_total_net": np.nan,
                         "revenue_per_event_gross": np.nan, "revenue_per_event_net": np.nan,
                         "kf_gross_avg_reported": np.nan, "kf_net_avg_reported": np.nan,
                         "avg_receipt_gross_reported": np.nan, "avg_receipt_net_reported": np.nan}
                        for s, g in liga.groupby("season")])
    return {"attendance_history": hist, "catering_match": cat, "catering_season_summary": dev,
            "access_match_summary": pd.DataFrame(rows_a), "access_sector_minute": pd.DataFrame(rows_sm),
            "context_match": pd.DataFrame(rows_k), "tickets_single_leadtime": pd.DataFrame(rows_sl),
            "tickets_hist_leadtime": pd.DataFrame(rows_hl)}


@pytest.fixture
def clean_tables() -> dict[str, pd.DataFrame]:
    return make_clean_tables()


@pytest.fixture
def clean_config(tmp_path: Path) -> Path:
    """Künstlicher bereinigter Lauf auf Platte + Konfiguration im Modus release_aggregates (Outputs in tmp)."""
    clean = tmp_path / "clean"
    run = clean / "20990101T000000_clean_test"
    run.mkdir(parents=True)
    tables = make_clean_tables()
    for name, df in tables.items():
        df.to_csv(run / f"{name}.csv", index=False)
    manifest = {"run_id": run.name, "data_mode": "release_aggregates", "checks": [],
                "inputs": [{"file": "synthetisch.csv", "sha256_16": "0" * 16, "bytes": 0}],
                "outputs": {n: {} for n in tables}}
    (run / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    (clean / "LATEST").write_text(run.name, encoding="utf-8")
    cfg = tmp_path / "project.yaml"
    cfg.write_text("data_mode: release_aggregates\n"
                   f"input_dir: '{tmp_path.as_posix()}'\n"
                   f"output_dir: '{(tmp_path / 'outputs').as_posix()}'\n"
                   f"clean_dir: '{clean.as_posix()}'\n"
                   "timezone: Europe/Zurich\n", encoding="utf-8")
    return cfg

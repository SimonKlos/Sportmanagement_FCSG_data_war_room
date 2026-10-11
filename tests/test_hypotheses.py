"""Hypothesentests (fcsg.hypotheses): bekannte Effekte werden erkannt, Zufall bleibt «unklar»."""

import numpy as np
import pandas as pd
import pytest

from fcsg.baseline import add_real_kpis, build_mart_match_real
import fcsg.hypotheses as hyp
from fcsg.hypotheses import context_associations, spearman, status_from_ci


@pytest.fixture
def mart(clean_tables):
    return add_real_kpis(build_mart_match_real(clean_tables, today="2099-12-31").mart)


def test_status_rules():
    assert status_from_ci(0.1, 0.5, 0.0) == "gestützt (vorläufig)"
    assert status_from_ci(-0.5, -0.1, 0.0) == "gegenteilig (vorläufig)"
    assert status_from_ci(-0.1, 0.5, 0.0) == "unklar (vorläufig)"
    assert status_from_ci(np.nan, np.nan, 0.0) == "nicht testbar"


def test_h1_proportional_revenue(mart):
    r = hyp.test_h1(mart)  # Umsatz = 15 × IST → Elastizität exakt 1
    assert r.estimate == pytest.approx(1.0)  # Status an der Grenze (KI ≈ [1, 1]) bewusst nicht geprüft
    assert r.n == 20 and set(r.table["sold_out"]) == {"ausverkauft", "nicht ausverkauft"}


def test_h2_detects_positive_effect(mart):
    r = hyp.test_h2(mart)  # Bons je Public steigt monoton mit Anteil früher Scans (nur 2099/00)
    assert r.n == 10 and r.estimate == pytest.approx(1.0, abs=1e-9)
    assert r.status == "gestützt (vorläufig)"


def test_h2_random_is_unclear(mart):
    rng = np.random.default_rng(3)
    m = mart.copy()
    m["receipts_per_public"] = np.where(m["receipts_per_public"].notna(), rng.normal(0.9, 0.05, len(m)), np.nan)
    m = pd.concat([m] * 3, ignore_index=True)  # mehr Spiele, damit das Intervall aussagekräftig ist
    m["receipts_per_public"] = np.where(m["receipts_per_public"].notna(), rng.normal(0.9, 0.05, len(m)), np.nan)
    assert hyp.test_h2(m).status == "unklar (vorläufig)"


def test_h3_entry_rate_by_leadtime(clean_tables, mart):
    r = hyp.test_h3(clean_tables, mart)
    rates = r.table.set_index("bucket")["entry_rate"]
    assert rates["0–1 Tage"] == pytest.approx(0.95) and rates["> 30 Tage"] == pytest.approx(0.80)
    assert r.estimate == pytest.approx(0.15) and r.status == "gestützt (vorläufig)"
    assert "100 Positionen mit negativem Vorlauf" in r.data_basis and "2098/2099" in r.data_basis


def test_context_associations(mart):
    r = context_associations(mart, n_boot=200)
    t = r.table
    assert set(t["target"]) == {"Anwesenheitsquote", "KF brutto", "IST Zuschauer"}
    # Temperatur = 10 + g und IST steigt mit g → perfekte Rangkorrelation innerhalb der Saison
    row = t[(t["target"] == "IST Zuschauer") & (t["feature"].str.startswith("Temperatur"))].iloc[0]
    assert row["spearman_within_season"] == pytest.approx(1.0) and row["ci_excludes_0"]


def test_spearman_guards():
    assert np.isnan(spearman(pd.Series([1, 1, 1]), pd.Series([1, 2, 3])))
    assert spearman(pd.Series([1, 2, 3, 4]), pd.Series([10, 20, 30, 40])) == pytest.approx(1.0)

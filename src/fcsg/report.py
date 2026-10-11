"""Bericht «Baseline – erste Erkenntnisse» (Markdown) und Grafiken (PNG) aus einem Analyse-Lauf.

Der Bericht liest ausschliesslich die Laufartefakte (CSV/JSON im Laufordner), damit Bericht, Excel und
Notebook dieselben Zahlen zeigen. Alle Zahlen sind **vorläufig** (Definitionen D-004/D-005 offen) und
aggregiert (keine Personendaten). Echte Zahlen dürfen ins private Repo (D-024).
"""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")  # ohne Bildschirm rendern
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from fcsg.hypotheses import FURTHER_HYPOTHESES  # noqa: E402

# Farben: Referenzpalette des dataviz-Skills (helle Fläche); eine Serie je Grafik → Slot 1.
SURFACE, INK, INK_2, GRID = "#fcfcfb", "#0b0b0b", "#52514e", "#e4e3df"
SERIES_1, SERIES_2 = "#2a78d6", "#eb6834"

BANNER = ("> **VORLÄUFIG – echte FCSG-Daten (aggregiert, nur Herren-Pflichtspiele, keine Personendaten).** "
          "Definitionen von SOLL/IST/Public Netto und Umsatzbasis sind noch offen (D-004/D-005). "
          "Alle Zusammenhänge sind Assoziationen, keine Ursachen; keine Potenzialaussagen. "
          "Vertraulich – nur privates Projekt-Repo (D-024).")


def _style(ax, title: str, xlabel: str = "", ylabel: str = "") -> None:
    ax.set_facecolor(SURFACE)
    ax.set_title(title, loc="left", fontsize=11, color=INK, pad=8)
    ax.set_xlabel(xlabel, color=INK_2, fontsize=9)
    ax.set_ylabel(ylabel, color=INK_2, fontsize=9)
    ax.tick_params(colors=INK_2, labelsize=8, length=0)
    ax.grid(axis="y", color=GRID, linewidth=0.8)
    ax.set_axisbelow(True)
    for side in ("top", "right", "left"):
        ax.spines[side].set_visible(False)
    ax.spines["bottom"].set_color(GRID)


def _fig(ncols: int = 1, width: float = 6.4, height: float = 3.6):
    fig, axes = plt.subplots(1, ncols, figsize=(width, height), dpi=150, facecolor=SURFACE)
    return fig, np.atleast_1d(axes)


def _save(fig, path: Path) -> Path:
    fig.tight_layout()
    fig.savefig(path, facecolor=SURFACE)
    plt.close(fig)
    return path


def _bars(ax, labels, values, fmt: str) -> None:
    x = np.arange(len(labels))
    ax.bar(x, values, width=0.55, color=SERIES_1, edgecolor=SURFACE, linewidth=2)
    ax.set_xticks(x, labels)
    for xi, v in zip(x, values):
        if np.isfinite(v):
            ax.annotate(fmt.format(v), (xi, v), xytext=(0, 3), textcoords="offset points", ha="center",
                        fontsize=7.5, color=INK_2)


def make_figures(run_dir: Path, fig_dir: Path) -> dict[str, Path]:
    """Erzeugt die PNG-Grafiken des Berichts aus den Laufartefakten."""
    fig_dir.mkdir(parents=True, exist_ok=True)
    mart = pd.read_csv(run_dir / "mart_match.csv")
    season = pd.read_csv(run_dir / "season_summary.csv")
    out = {}

    # 1 Saison-Baseline als kleine Mehrfachgrafik (keine Doppelachse)
    fig, axes = _fig(3, width=9.6, height=3.2)
    s = season["season"].str.replace("20", "", n=1)
    _bars(axes[0], s, season["attendance_rate_weighted"] * 100, "{:.0f}")
    _style(axes[0], "Anwesenheitsquote (%)")
    axes[0].set_ylim(0, 100)
    _bars(axes[1], s, season["kf_gross_weighted_chf"], "{:.2f}")
    _style(axes[1], "KF brutto (CHF je Public)")
    _bars(axes[2], s, season["receipts_per_public_weighted"], "{:.2f}")
    _style(axes[2], "Bons je Public (ab 23/24)")
    for ax in axes:
        ax.tick_params(axis="x", rotation=0)
    out["baseline"] = _save(fig, fig_dir / "01_saison_baseline.png")

    # 2 H1: Elastizität (saison-zentriert, log)
    d = mart[(mart["ist"] > 0) & (mart["revenue_gross_chf"] > 0)].copy()
    for c, src in (("x", "ist"), ("y", "revenue_gross_chf")):
        d[c] = np.log(d[src]) - np.log(d[src]).groupby(d["season"]).transform("mean")
    slope = float((d["x"] * d["y"]).sum() / (d["x"] ** 2).sum())
    fig, axes = _fig(1, width=6.0, height=4.0)
    ax = axes[0]
    ax.scatter(d["x"], d["y"], s=22, color=SERIES_1, edgecolor=SURFACE, linewidth=1, zorder=3)
    xs = np.linspace(d["x"].min(), d["x"].max(), 50)
    ax.plot(xs, slope * xs, color=INK, linewidth=2, label=f"Steigung {slope:.2f}")
    ax.plot(xs, xs, color=INK_2, linewidth=1.2, linestyle=(0, (4, 3)), label="Elastizität 1 (proportional)")
    _style(ax, "H1 · Catering-Umsatz vs. Zuschauer (je Saison zentriert)", "log IST − Saisonmittel",
           "log Umsatz − Saisonmittel")
    ax.legend(frameon=False, fontsize=8, labelcolor=INK_2)
    out["h1"] = _save(fig, fig_dir / "02_h1_elastizitaet.png")

    # 3 H2: frühe Ankunft vs. Bonsrate / Ø Bon
    d = mart[(mart["access_complete"] == 1) & mart["receipts_per_public"].notna()].copy()
    fig, axes = _fig(2, width=9.0, height=3.6)
    for ax, (ycol, ylabel) in zip(axes, (("receipts_per_public", "Bons je Public"), ("avg_receipt_gross_chf", "Ø Bon brutto (CHF)"))):
        x = d["share_arrived_45min_before"] - d.groupby("season")["share_arrived_45min_before"].transform("mean")
        y = d[ycol] - d.groupby("season")[ycol].transform("mean")
        ax.scatter(x * 100, y, s=22, color=SERIES_1, edgecolor=SURFACE, linewidth=1, zorder=3)
        _style(ax, f"H2 · {ylabel}", "Anteil ≥ 45 Min. vorher (Pp. vs. Saisonmittel)", f"{ylabel} vs. Saisonmittel")
    out["h2"] = _save(fig, fig_dir / "03_h2_ankunft_catering.png")

    # 4 H3: Eintrittsquote nach Kaufvorlauf
    h3 = pd.read_csv(run_dir / "h3_leadtime.csv")
    fig, axes = _fig(1, width=6.0, height=3.4)
    _bars(axes[0], h3["bucket"], h3["entry_rate"] * 100, "{:.1f}")
    _style(axes[0], "H3 · Eintrittsquote Einzeltickets nach Kaufvorlauf (%)", "Kauf … vor dem Spiel")
    axes[0].set_ylim(0, 100)  # Balken immer ab 0 (keine abgeschnittene Achse)
    out["h3"] = _save(fig, fig_dir / "04_h3_vorlauf_eintritt.png")

    # 5 K1: Zusammenhänge Kontext (Punkt + KI), je Zielgrösse ein Panel
    k = pd.read_csv(run_dir / "context_associations.csv")
    targets = list(dict.fromkeys(k["target"]))
    # Gleiche Variablenreihenfolge in allen Panels (nach stärkstem |ρ| über alle Zielgrössen) → Namen nur links.
    order = (k.assign(a=k["spearman_within_season"].abs()).groupby("feature")["a"].max().sort_values().index.tolist())
    fig, axes = plt.subplots(1, len(targets), figsize=(11.0, 5.4), dpi=150, facecolor=SURFACE, sharey=True)
    axes = np.atleast_1d(axes)
    for ax, tgt in zip(axes, targets):
        g = k[k["target"] == tgt].set_index("feature").reindex(order)
        y = np.arange(len(g))
        sig = g["ci_excludes_0"].fillna(False).astype(bool).to_numpy()
        ax.hlines(y, g["ci_low"], g["ci_high"], color=INK_2, linewidth=1.2)
        ax.scatter(g["spearman_within_season"], y, s=34, zorder=3, edgecolor=SURFACE, linewidth=1,
                   color=np.where(sig, SERIES_1, "#b4b2ab"))
        ax.axvline(0, color=INK_2, linewidth=0.8)
        ax.set_yticks(y, order, fontsize=8)
        ax.set_xlim(-1, 1)
        _style(ax, tgt, "Spearman ρ")
        ax.grid(axis="x", color=GRID, linewidth=0.8)
        ax.grid(axis="y", visible=False)
    fig.suptitle("K1 · Spielkontext und Baseline (saison-zentriert, 95 %-KI; blau = KI ohne 0, grau = unklar)",
                 x=0.01, ha="left", fontsize=11, color=INK)
    out["k1"] = _save(fig, fig_dir / "05_k1_kontext.png")
    return out


# ----------------------------------------------------------------------------------------------------
# Markdown
# ----------------------------------------------------------------------------------------------------

def _md_table(df: pd.DataFrame, fmt: dict[str, str] | None = None) -> str:
    fmt = fmt or {}
    cols = list(df.columns)
    lines = ["| " + " | ".join(cols) + " |", "|" + "---|" * len(cols)]
    for _, r in df.iterrows():
        cells = []
        for c in cols:
            v = r[c]
            if isinstance(v, (float, np.floating)) and not np.isfinite(v):
                cells.append("–")
            elif c in fmt and isinstance(v, (int, float, np.integer, np.floating)):
                cells.append(fmt[c].format(v))
            else:
                cells.append(str(v).replace("|", "/").replace("\n", " "))
        lines.append("| " + " | ".join(cells) + " |")
    return "\n".join(lines)


def write_report(run_dir: Path, report_dir: Path) -> Path:
    """Schreibt ``01_baseline_erste_erkenntnisse.md`` und Grafiken nach ``report_dir``."""
    report_dir.mkdir(parents=True, exist_ok=True)
    figs = make_figures(run_dir, report_dir / "figures")
    rel = {k: f"figures/{p.name}" for k, p in figs.items()}
    man = json.loads((run_dir / "manifest.json").read_text(encoding="utf-8"))
    season = pd.read_csv(run_dir / "season_summary.csv")
    cov = pd.read_csv(run_dir / "coverage.csv")
    reto = pd.read_csv(run_dir / "reto_comparison.csv")
    src = pd.read_csv(run_dir / "source_total_check.csv")
    hyp = pd.read_csv(run_dir / "hypotheses.csv")
    checks = pd.read_csv(run_dir / "quality_checks.csv")
    k1 = pd.read_csv(run_dir / "context_associations.csv")
    h1 = pd.read_csv(run_dir / "h1_sold_out.csv")
    h2 = pd.read_csv(run_dir / "h2_correlations.csv")
    h3 = pd.read_csv(run_dir / "h3_leadtime.csv")
    H = hyp.set_index("hid")

    def hblock(hid: str, fig_key: str, table: pd.DataFrame, fmt: dict) -> str:
        r = H.loc[hid]
        ci = "" if pd.isna(r["ci_low"]) else f" (95 %-KI {r['ci_low']:.3f} bis {r['ci_high']:.3f})"
        est = f"{r['estimate']:.0f}" if pd.isna(r["ci_low"]) else f"{r['estimate']:.3f}"
        return f"""### {hid} · {r['link']} – **{r['status']}**

**Hypothese:** {r['statement']}

- **Daten:** {r['data_basis']}
- **Methode:** {r['method']}
- **Ergebnis:** {r['effect_label']} = **{est}**{ci}. {r['interpretation']}
- **Einschränkungen:** {r['limitations']}
- **Nächster Test (für die Weiterarbeit):** {r['next_steps']}

![{hid}]({rel[fig_key]})

{_md_table(table, fmt)}
"""

    n_fail = int((checks["status"] == "FAIL").sum())
    n_warn = int((checks["status"] == "WARN").sum())
    season_view = season[["season", "n_matches", "ist_sum", "attendance_rate_weighted", "no_show_abs_sum",
                          "revenue_gross_chf_sum", "kf_gross_weighted_chf", "kf_net_weighted_chf",
                          "receipts_per_public_weighted", "avg_receipt_gross_weighted_chf", "n_access_complete",
                          "share_45min_weighted", "share_last15_weighted"]]
    k1_sig = k1[k1["ci_excludes_0"].astype(bool)][["target", "feature", "n", "spearman_within_season", "ci_low", "ci_high",
                                                    "diff_group1_minus_group0"]]
    further = pd.DataFrame(FURTHER_HYPOTHESES, columns=["ID", "Verknüpfung", "Hypothese", "Daten / Hinweis"])

    # Kernaussagen – aus den Laufergebnissen berechnet (keine handgeschriebenen Zahlen)
    full = season[season["n_matches"] >= 15] if (season["n_matches"] >= 15).any() else season
    first, last = full.iloc[0], full.iloc[-1]
    n_reto_ok = int(reto["status"].str.startswith("übereinstimmend").sum())
    h2c = h2.set_index(["x", "y"])["spearman_within_season"]
    h3r = h3.set_index("bucket")["entry_rate"]
    top = k1[k1["ci_excludes_0"].astype(bool)].assign(a=lambda x: x["spearman_within_season"].abs()).sort_values(
        "a", ascending=False).head(3)
    key = [
        f"**Baseline:** KF brutto steigt von {first['kf_gross_weighted_chf']:.2f} CHF ({first['season']}) auf "
        f"{last['kf_gross_weighted_chf']:.2f} CHF ({last['season']}); die Anwesenheitsquote liegt bei "
        f"{full['attendance_rate_weighted'].min():.0%}–{full['attendance_rate_weighted'].max():.0%} (volle Saisons).",
        f"**Verknüpfung belastbar:** {n_reto_ok} von {len(reto)} Sichtungswerten von Reto werden reproduziert; Summen bleiben "
        f"über alle Joins erhalten ({len(checks)} Prüfungen, {n_fail} FAIL).",
        f"**H1 (Ticketing × Catering):** Catering-Umsatz vs. Zuschauer (Elastizität "
        f"{H.loc['H1', 'estimate']:.2f}, KI {H.loc['H1', 'ci_low']:.2f}–{H.loc['H1', 'ci_high']:.2f}) – " + (
            "überproportional." if H.loc["H1", "ci_low"] > 1 else "unterproportional." if H.loc["H1", "ci_high"] < 1
            else "kein Beleg für überproportionalen Konsum bei vollen Spielen."),
        f"**H2 (Zutritt × Catering):** Frühe Ankunft hängt nicht mit der Bonsrate zusammen (ρ = "
        f"{h2c.get(('share_arrived_45min_before', 'receipts_per_public'), np.nan):+.2f}), aber mit einem höheren Ø Bon "
        f"(ρ = {h2c.get(('share_arrived_45min_before', 'avg_receipt_gross_chf'), np.nan):+.2f}); viele späte Scans gehen mit "
        f"tieferem Ø Bon einher (ρ = {h2c.get(('share_last_15min', 'avg_receipt_gross_chf'), np.nan):+.2f}). Nicht für Kontext kontrolliert.",
        f"**H3 (Ticketing × Zutritt):** Früh gekaufte Einzeltickets (> 30 Tage) werden seltener genutzt "
        f"({h3r.get('> 30 Tage', np.nan):.1%} Eintritt) als kurzfristig gekaufte ({h3r.get('0–1 Tage', np.nan):.1%}).",
        "**K1 (Kontext):** stärkste Zusammenhänge – " + "; ".join(
            f"{r.feature} ↔ {r.target} (ρ = {r.spearman_within_season:+.2f})" for r in top.itertuples()) + ".",
    ]
    key_md = "\n".join(f"{i}. {k}" for i, k in enumerate(key, 1))

    text = f"""# Baseline – erste Erkenntnisse (Phase 1)

{BANNER}

| | |
|---|---|
| Analyse-Lauf | `{man['run_id']}` (erstellt {man['created_at']}) |
| Datenbasis | bereinigter Lauf `{man['clean_run_id']}` (Lieferung «20261003_Input Sandro» + Spielkontext-Tabelle) |
| Umfang | {man['coverage']['home_matches']} Herren-Pflichtspiele (Liga, Cup, UEFA) 2021/22 bis heute |
| Prüfungen | {len(checks)} gesamt · {n_fail} FAIL · {n_warn} WARN (Details: `quality_checks.csv` im Laufordner bzw. Excel-Blatt «Qualität») |
| Code | `fcsg` {man['code_version']}, Python {man['python']}; neu rechnen: `python -m fcsg.cli analyze --config config/project.local.yaml` |

## Kernaussagen (vorläufig)

{key_md}

Alle Aussagen beschreiben Zusammenhänge auf Spielebene, keine Ursachen. Sie sind Hypothesen für die Weiterarbeit (§5–§7).

## 1 Was wurde gemacht
1. **Verknüpfung** (Schritt 1): Spielkalender aus der Zuschauer-Historie; Catering, Zutritt, Ticketing und Spielkontext
   je Datum aggregiert und 1:1 angehängt (Summenerhalt geprüft, nicht zuordenbare Zeilen im Unmatched-Report).
2. **Baseline-Kennzahlen** (Schritt 2) je Spiel und Saison: Anwesenheit/No-Show, KF brutto/netto, Bonsrate, Ø Bon,
   Ankunft – Brutto und Netto getrennt, Saisonwerte gewichtet (Σ/Σ). **Deckungsbeitrag nicht berechenbar** (keine
   Kosten-/Margendaten, D-003).
3. **Abgleich mit Retos Sichtung** und mit dem Quell-Tab «Entwicklung» (Schritt 3).
4. **Excel-Export mit Readback** (Schritt 4): liegt ausserhalb des Repos unter `<output_dir>/{man['run_id']}/`.
5. **Drei Hypothesen** zur Verknüpfung der Datenbasen + **Kontextverbindung** (unten).

## 2 Abdeckung (gemeinsame Stichproben)

{_md_table(cov)}

`sample_H1/H2/K1` = Spiele, die in die jeweilige Hypothese eingehen. Zutritt 24/25 nur für 9 Spiele vollständig (D-018);
Bons erst ab 23/24 (D-019); Eintrittsfeld der Einzeltickets nur 21/22–22/23 verlässlich; Spielkontext ab 22/23.

## 3 Baseline je Saison (Herren-Pflichtspiele, vorläufig)

![Saison-Baseline]({rel['baseline']})

{_md_table(season_view, {"ist_sum": "{:,.0f}", "attendance_rate_weighted": "{:.1%}", "no_show_abs_sum": "{:,.0f}",
                         "revenue_gross_chf_sum": "{:,.0f}", "kf_gross_weighted_chf": "{:.2f}", "kf_net_weighted_chf": "{:.2f}",
                         "receipts_per_public_weighted": "{:.3f}", "avg_receipt_gross_weighted_chf": "{:.2f}",
                         "share_45min_weighted": "{:.1%}", "share_last15_weighted": "{:.1%}"})}

Lesehilfe: KF = Catering-Umsatz / Public Netto; 2026/27 umfasst erst 7 Spiele (Saisonbeginn, teils UEFA).

## 4 Abgleich mit Retos Sichtung und mit der Quelle

{_md_table(reto[["id", "kpi", "scope", "reto_value", "our_value", "unit", "status", "n_matches", "note"]].fillna(""),
           {"reto_value": "{:,.3f}", "our_value": "{:,.3f}", "n_matches": "{:.0f}"})}

Summe der Spielzeilen «Meisterschaft» je Saison vs. Quell-Tab «Entwicklung» (Konsistenz der Catering-Datei):

{_md_table(src, {"rows_revenue_gross": "{:,.0f}", "entwicklung_revenue_gross": "{:,.0f}", "rel_diff": "{:+.2%}",
                 "rows_n": "{:.0f}", "entwicklung_n": "{:.0f}"})}

## 5 Hypothesen zur Verknüpfung der drei Datenbasen

Einheitliche Statuslogik: «gestützt» = 95 %-Konfidenzintervall vollständig auf der erwarteten Seite; «unklar» = Intervall
schliesst den neutralen Wert ein; «gegenteilig» = vollständig auf der Gegenseite. Alle Tests saison-zentriert
(Preis-/Trendeffekte entfernt), explorativ und **vorläufig**.

{hblock("H1", "h1", h1, {"kf_gross_mean": "{:.2f}", "kf_vs_season_mean": "{:+.2f}", "ist_mean": "{:,.0f}"})}
{hblock("H2", "h2", h2, {"spearman_within_season": "{:+.2f}"})}
{hblock("H3", "h3", h3, {"entry_rate": "{:.1%}", "no_show_rate": "{:.1%}", "n_positions": "{:,.0f}", "n_entered": "{:,.0f}"})}

## 6 Verbindung zur Spielkontext-Tabelle (K1)

{hblock("K1", "k1", k1_sig, {"spearman_within_season": "{:+.2f}", "ci_low": "{:+.2f}", "ci_high": "{:+.2f}",
                              "diff_group1_minus_group0": "{:+.3f}"})}
Tabelle oben: nur Zusammenhänge mit Konfidenzintervall ohne 0; alle {len(k1)} Kombinationen in
`context_associations.csv` bzw. Excel-Blatt «Kontext».

## 7 Weitere Hypothesen für die Weiterarbeit (noch nicht getestet)

{_md_table(further)}

## 8 Offene Punkte und Grenzen
- **Definitionen offen:** SOLL/IST/VIP/Public Netto (D-004), Umsatz-/MwSt-Basis (D-005) – Zahlen können sich verschieben.
- **Deckungsbeitrag:** Steuerungsgrösse (D-003), aber keine Kosten-/Margendaten → Datenanforderung an Sandro.
- **Catering 23/24:** Der Quell-Tab «Entwicklung» zählt 19 Meisterschaftsspiele, der Saison-Tab nur 18 (Differenz
  ≈ CHF 0.21 Mio. brutto); ein Pflichtspiel der Historie hat keine Catering-Zeile → Frage an Sandro.
- **Datenlücken:** Zutritt 24/25 unvollständig; Bons erst ab 23/24; 6 Heimspiele 25/26 ohne Spielkontext (D-017);
  Datumskonflikte (Servette 25./26.01.2026; 24.08./24.09.2024) im Unmatched-Report.
- **Methodik:** Assoziationen auf Spielebene, keine Kausalität, keine Potenziale; viele Tests in K1 → Zufallstreffer möglich.
  Modellierung erst nach Baseline-Freigabe.
- **Datenraum:** Bestätigung durch FCSG zur lokalen Verarbeitung offen (D-023).
"""
    path = report_dir / "01_baseline_erste_erkenntnisse.md"
    path.write_text(text, encoding="utf-8")
    return path

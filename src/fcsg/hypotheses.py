"""Erste Hypothesentests zur Verknüpfung der drei Datenbasen (Ticketing, Zutritt, Catering) und zum Spielkontext.

**Explorativ und vorläufig.** Die Tests messen Zusammenhänge (Assoziation), keine Ursachen; sie sind kein
Kontextmodell (Modellierung erst nach Baseline-Freigabe) und quantifizieren kein Potenzial (CLAUDE.md, AA S. 8–9).
Unsicherheit: Bootstrap-Konfidenzintervalle (95 %, fester Seed → reproduzierbar). Saisoneffekte (Preise, Trend)
werden entfernt, indem Werte innerhalb jeder Saison zentriert werden.

Status-Regeln (einheitlich):
- «gestützt»: Konfidenzintervall liegt vollständig auf der erwarteten Seite.
- «gegenteilig»: Konfidenzintervall liegt vollständig auf der Gegenseite.
- «unklar»: Konfidenzintervall schliesst den neutralen Wert ein.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field

import numpy as np
import pandas as pd

from fcsg.baseline import LEAD_BUCKETS, lead_bucket

SEED = 1879
N_BOOT = 2000


@dataclass
class HypothesisResult:
    """Einheitliches Ergebnisformat je Hypothese (für Bericht, Excel und Notebook)."""

    hid: str
    link: str
    statement: str
    data_basis: str
    n: int
    method: str
    effect_label: str
    estimate: float
    ci_low: float
    ci_high: float
    neutral: float
    status: str
    interpretation: str
    limitations: str
    next_steps: str
    table: pd.DataFrame = field(default_factory=pd.DataFrame, repr=False)

    def summary_row(self) -> dict:
        row = asdict(self)
        row.pop("table")
        return row


def status_from_ci(lo: float, hi: float, neutral: float, expected_sign: int = 1) -> str:
    if np.isnan(lo) or np.isnan(hi):
        return "nicht testbar"
    if (lo > neutral and expected_sign > 0) or (hi < neutral and expected_sign < 0):
        return "gestützt (vorläufig)"
    if (hi < neutral and expected_sign > 0) or (lo > neutral and expected_sign < 0):
        return "gegenteilig (vorläufig)"
    return "unklar (vorläufig)"


def bootstrap(df: pd.DataFrame, stat, n_boot: int = N_BOOT, seed: int = SEED, cluster: str | None = None) -> tuple[float, float]:
    """95-%-Perzentil-Intervall von ``stat(df)``; zieht Zeilen bzw. ganze Cluster (z. B. Spiele) mit Zurücklegen."""
    rng = np.random.default_rng(seed)
    vals = []
    if cluster:
        groups = {k: g for k, g in df.groupby(cluster)}
        keys = np.array(list(groups))
        for _ in range(n_boot):
            vals.append(stat(pd.concat([groups[k] for k in rng.choice(keys, len(keys))], ignore_index=True)))
    else:
        for _ in range(n_boot):
            vals.append(stat(df.iloc[rng.integers(0, len(df), len(df))]))
    vals = np.array([v for v in vals if np.isfinite(v)])
    return (float(np.percentile(vals, 2.5)), float(np.percentile(vals, 97.5))) if len(vals) else (np.nan, np.nan)


def demean(df: pd.DataFrame, col: str, by: str = "season") -> pd.Series:
    return df[col] - df.groupby(by)[col].transform("mean")


def spearman(x: pd.Series, y: pd.Series) -> float:
    ok = x.notna() & y.notna()
    if ok.sum() < 3 or x[ok].nunique() < 2 or y[ok].nunique() < 2:
        return np.nan
    return float(x[ok].rank().corr(y[ok].rank()))


def _slope(d: pd.DataFrame) -> float:
    var = (d["x"] ** 2).sum()
    return float((d["x"] * d["y"]).sum() / var) if var > 0 else np.nan


# ----------------------------------------------------------------------------------------------------
# H1 – Ticketing × Catering
# ----------------------------------------------------------------------------------------------------

def test_h1(m: pd.DataFrame) -> HypothesisResult:
    """H1: Catering-Umsatz wächst überproportional mit den Zuschauern (Elastizität > 1)."""
    d = m[(m["ist"] > 0) & (m["revenue_gross_chf"] > 0)].copy()
    d["lx"], d["ly"] = np.log(d["ist"]), np.log(d["revenue_gross_chf"])
    d["x"], d["y"] = demean(d, "lx"), demean(d, "ly")
    est = _slope(d)
    lo, hi = bootstrap(d[["x", "y"]], _slope)
    # Sensitivität: Public Netto (Catering-Datei) statt IST (Ticketing) als Zuschauergrösse
    p = d[d["public_attendance"] > 0].copy()
    p["x"] = demean(p.assign(lp=np.log(p["public_attendance"])), "lp")
    p["y"] = demean(p, "ly")
    est_pub = _slope(p)
    # KF nach Ausverkauft (Ticketing) – innerhalb der Saison zentriert
    d["kf_dm"] = demean(d, "kf_gross_chf")
    tab = d.groupby(d["sold_out"].map({1.0: "ausverkauft", 0.0: "nicht ausverkauft"}).fillna("unbekannt")).agg(
        n=("match_id", "size"), kf_gross_mean=("kf_gross_chf", "mean"), kf_vs_season_mean=("kf_dm", "mean"),
        ist_mean=("ist", "mean")).reset_index(names="sold_out")
    diff = tab.set_index("sold_out")["kf_vs_season_mean"]
    so = d[d["sold_out"].notna()]
    so_lo, so_hi = bootstrap(so[["sold_out", "kf_dm"]], lambda x: x.loc[x.sold_out == 1, "kf_dm"].mean()
                             - x.loc[x.sold_out == 0, "kf_dm"].mean())
    so_diff = diff.get("ausverkauft", np.nan) - diff.get("nicht ausverkauft", np.nan)
    status = status_from_ci(lo, hi, 1.0)
    return HypothesisResult(
        hid="H1", link="Ticketing × Catering",
        statement="Der Catering-Umsatz eines Spiels wächst überproportional mit der Zuschauerzahl (Elastizität > 1); "
                  "pro Kopf wird bei vollen Spielen mehr konsumiert.",
        data_basis=f"{len(d)} Herren-Pflichtspiele {d['season'].min()}–{d['season'].max()} mit IST (Zuschauer-Historie) "
                   "und Catering-Umsatz brutto",
        n=len(d),
        method="Steigung log(Umsatz brutto) auf log(IST), beide innerhalb der Saison zentriert (entfernt Preis-/Trendeffekte); "
               "Bootstrap über Spiele. Zusatz: KF ausverkauft vs. nicht ausverkauft (saison-zentriert).",
        effect_label="Elastizität Umsatz / IST", estimate=est, ci_low=lo, ci_high=hi, neutral=1.0, status=status,
        interpretation=(f"1 % mehr Zuschauer geht mit {est:.2f} % mehr Catering-Umsatz einher (95 %-KI {lo:.2f}–{hi:.2f}); "
                        f"mit Public Netto statt IST: {est_pub:.2f}. Retos Wert: 1.14. KF ausverkaufter Spiele liegt "
                        f"{so_diff:+.2f} CHF gegenüber nicht ausverkauften (saison-zentriert, KI {so_lo:+.2f} bis {so_hi:+.2f})."),
        limitations="Zusammenhang, keine Ursache: attraktive Gegner/Wetter erhöhen Zuschauer und Konsum zugleich. "
                    "IST- und Public-Definition offen (D-004). Umsatz ≠ Deckungsbeitrag (D-003).",
        next_steps="Kontrolle für Kontext (Wetter, Anstosszeit, Gegner) im Kontextmodell; Elastizität getrennt nach "
                   "Bonsrate und Ø Bon (ab 23/24); Prüfung, ob Gästesektor-Zuschauer (guest_sector_attendance) den Effekt treiben.",
        table=tab,
    )


# ----------------------------------------------------------------------------------------------------
# H2 – Zutritt × Catering
# ----------------------------------------------------------------------------------------------------

def test_h2(m: pd.DataFrame) -> HypothesisResult:
    """H2: Mehr frühe Ankunft (≥ 45 Min. vorher) → mehr Bons je Public-Anwesendem."""
    d = m[(m["access_complete"] == 1) & m["receipts_per_public"].notna() & m["share_arrived_45min_before"].notna()].copy()
    for c in ("share_arrived_45min_before", "receipts_per_public", "avg_receipt_gross_chf", "kf_gross_chf", "share_last_15min"):
        d[f"{c}_dm"] = demean(d, c)
    est = spearman(d["share_arrived_45min_before_dm"], d["receipts_per_public_dm"])
    lo, hi = bootstrap(d, lambda x: spearman(x["share_arrived_45min_before_dm"], x["receipts_per_public_dm"]))
    rows = []
    for x in ("share_arrived_45min_before", "share_last_15min"):
        for y in ("receipts_per_public", "avg_receipt_gross_chf", "kf_gross_chf"):
            rows.append({"x": x, "y": y, "spearman_within_season": spearman(d[f"{x}_dm"], d[f"{y}_dm"]), "n": len(d)})
    tab = pd.DataFrame(rows)
    status = status_from_ci(lo, hi, 0.0)
    return HypothesisResult(
        hid="H2", link="Zutritt × Catering",
        statement="Je grösser der Anteil der Zuschauer, die mindestens 45 Minuten vor Anpfiff eintreten, desto mehr "
                  "Catering-Bons je Public-Anwesendem (mehr Zeit im Stadion → mehr Käufe).",
        data_basis=f"{len(d)} Spiele {d['season'].min()}–{d['season'].max()} mit vollständigem Zutritt (D-018) und Bons (ab 23/24, D-019)",
        n=len(d),
        method="Spearman-Rangkorrelation zwischen Anteil früher Scans und Bons je Public, beide saison-zentriert; Bootstrap über Spiele. "
               "Zusatz: Korrelationen mit Ø Bon, KF und Anteil später Scans.",
        effect_label="Spearman ρ (früh vs. Bonsrate)", estimate=est, ci_low=lo, ci_high=hi, neutral=0.0, status=status,
        interpretation=f"ρ = {est:.2f} (95 %-KI {lo:.2f} bis {hi:.2f}) auf Spielebene; Details zu Ø Bon und KF in der Tabelle.",
        limitations="Spielebene, nicht Person: Wer früh kommt, ist nicht unbedingt der, der kauft (ökologischer Fehlschluss). "
                    "Anstosszeit/Wochentag beeinflussen Ankunft und Konsum gleichzeitig. Scans ≠ eindeutige Besucher; "
                    "Toröffnungszeiten unbekannt.",
        next_steps="Kontrolle für Anstosszeit und Wetter; Ankunft nach Sektor (access_sector_minute) vs. Kiesplatz-/Standumsätze "
                   "ab 25/26; Toröffnungszeiten bei Sandro erfragen.",
        table=tab,
    )


# ----------------------------------------------------------------------------------------------------
# H3 – Ticketing × Zutritt
# ----------------------------------------------------------------------------------------------------

def test_h3(t: dict[str, pd.DataFrame], m: pd.DataFrame) -> HypothesisResult:
    """H3: Kurzfristig gekaufte Einzeltickets werden häufiger genutzt als früh gekaufte."""
    hl = t["tickets_hist_leadtime"]
    hl = hl[hl["is_match"].astype(bool) & hl["event_date"].isin(m.loc[m["entry_field_reliable"], "match_date"])].copy()
    hl["bucket"] = lead_bucket(hl["lead_days"])
    invalid = int(hl.loc[hl["bucket"] == "ungültig (< 0)", "n_rows"].sum())
    hl = hl[hl["bucket"] != "ungültig (< 0)"]
    order = [b[2] for b in LEAD_BUCKETS]
    tab = hl.groupby("bucket").agg(n_positions=("n_rows", "sum"), n_entered=("n_entered", "sum"),
                                   n_matches=("event_date", "nunique")).reindex(order).reset_index()
    tab["entry_rate"] = tab["n_entered"] / tab["n_positions"]
    tab["no_show_rate"] = 1 - tab["entry_rate"]

    def diff(x: pd.DataFrame) -> float:
        g = x.groupby("bucket")[["n_entered", "n_rows"]].sum()
        if not {order[0], order[-1]} <= set(g.index):
            return np.nan
        r = g["n_entered"] / g["n_rows"]
        return float(r[order[0]] - r[order[-1]])

    est = diff(hl)
    lo, hi = bootstrap(hl[["event_date", "bucket", "n_entered", "n_rows"]], diff, n_boot=1000, cluster="event_date")
    g = m[m["single_entry_rate"].notna()]
    rho = spearman(g["single_share_lead_le1"], g["attendance_rate"])
    status = status_from_ci(lo, hi, 0.0)
    return HypothesisResult(
        hid="H3", link="Ticketing × Zutritt",
        statement="Kurzfristig gekaufte Einzeltickets (0–1 Tage vor dem Spiel) werden häufiger tatsächlich genutzt "
                  "(Eintritt am Drehkreuz) als früh gekaufte (> 30 Tage) – No-Show entsteht eher bei Frühkäufen.",
        data_basis=f"Einzeltickets-Exporte, {hl['event_date'].nunique()} Pflichtspiele in Saisons mit befülltem Eintrittsfeld "
                   f"({', '.join(sorted(hl['season_label'].unique()))}), {int(tab['n_positions'].sum()):,} Ticketpositionen; "
                   f"{invalid} Positionen mit negativem Vorlauf ausgeschlossen",
        n=int(hl["event_date"].nunique()),
        method="Eintrittsquote = eingetretene / verkaufte Positionen je Vorlauf-Klasse; Effekt = Quote(0–1 Tage) − Quote(> 30 Tage); "
               "Bootstrap über Spiele (Cluster). Zusatz: Spielebene Last-Minute-Anteil vs. Anwesenheitsquote.",
        effect_label="Differenz Eintrittsquote (kurzfristig − früh)", estimate=est, ci_low=lo, ci_high=hi, neutral=0.0,
        status=status,
        interpretation=(f"Eintrittsquote kurzfristig minus früh: {est:+.1%} (95 %-KI {lo:+.1%} bis {hi:+.1%}). "
                        f"Spielebene: ρ(Last-Minute-Anteil, Anwesenheitsquote) = {rho:.2f} (n = {len(g)}) – negativ, weil "
                        "ein hoher Last-Minute-Anteil vor allem bei Spielen mit schwachem Vorverkauf auftritt (Nennereffekt); "
                        "kein Widerspruch zur Ticketebene."),
        limitations="Nur Einzeltickets (keine Abos) und nur 21/22–22/23; Eintrittsfeld ~88–89 % befüllt (fehlender Eintritt "
                    "≠ sicher No-Show). Vorlauf-Klassen mischen Kanäle und Preiskategorien. Stornos nicht enthalten.",
        next_steps="Nach Kanal und Platzgruppe aufteilen (tickets_hist_leadtime); mit Zutritt 22/23 abgleichen; "
                   "für 25/26+ ist kein Eintritt je Ticket geliefert → bei Sandro anfragen (Barcode-Abgleich nur intern).",
        table=tab,
    )


# ----------------------------------------------------------------------------------------------------
# K1 – Spielkontext → Baseline
# ----------------------------------------------------------------------------------------------------

CONTEXT_FEATURES = {
    "temp_day_mean_c": "Temperatur Tagesmittel (°C)",
    "precip_day_mm": "Niederschlag Tag (mm)",
    "wind_day_kmh": "Wind Tag (km/h)",
    "kickoff_hour": "Anstosszeit (Stunde)",
    "weekend": "Wochenende (Sa/So)",
    "table_rank_opp": "Tabellenrang Gegner (vor Spiel; hoch = schwach)",
    "table_rank_fcsg": "Tabellenrang FCSG (vor Spiel)",
    "form_fcsg_points": "Form FCSG (Punkte letzte 5)",
    "form_opp_points": "Form Gegner (Punkte letzte 5)",
    "tv_free_srf": "Free-TV (SRF)",
    "school_holiday": "Schulferien Stadt SG",
    "public_holiday": "Feiertag",
    "parallel_event": "Parallel-Event Stadt SG",
    "uefa": "UEFA-Spiel",
    "guest_sector_closed": "Gästesektor geschlossen/exkl. (Bemerkung)",
}
CONTEXT_TARGETS = {"attendance_rate": "Anwesenheitsquote", "kf_gross_chf": "KF brutto", "ist": "IST Zuschauer"}


def context_frame(m: pd.DataFrame) -> pd.DataFrame:
    d = m[m["has_context"]].copy()
    d["kickoff_hour"] = pd.to_numeric(d["kickoff"].astype("string").str[:2], errors="coerce")
    d["weekend"] = d["weekday"].isin(["Sa", "So", "Samstag", "Sonntag"]).astype(float)
    d["uefa"] = (d["competition_group"] == "UEFA").astype(float)
    d["guest_sector_closed"] = (d["guest_sector_note"] == "geschlossen/exkl.").astype(float)
    return d


def context_associations(m: pd.DataFrame, n_boot: int = 1000) -> HypothesisResult:
    """K1: Zusammenhänge Kontext ↔ Anwesenheitsquote, KF, IST (saison-zentriert, Spearman, Bootstrap)."""
    d = context_frame(m)
    rows = []
    for tgt, tlabel in CONTEXT_TARGETS.items():
        d["_y"] = demean(d, tgt)
        for feat, flabel in CONTEXT_FEATURES.items():
            sub = d[[feat, "_y"]].dropna()
            rho = spearman(sub[feat], sub["_y"])
            lo, hi = bootstrap(sub, lambda x: spearman(x[feat], x["_y"]), n_boot=n_boot)
            binary = sub[feat].dropna().isin([0, 1]).all()
            gap = (sub.loc[sub[feat] == 1, "_y"].mean() - sub.loc[sub[feat] == 0, "_y"].mean()) if binary else np.nan
            rows.append({"target": tlabel, "feature": flabel, "n": len(sub),
                         "n_group_1": int((sub[feat] == 1).sum()) if binary else np.nan,
                         "spearman_within_season": rho, "ci_low": lo, "ci_high": hi,
                         "diff_group1_minus_group0": gap,
                         "ci_excludes_0": bool(np.isfinite(lo) and (lo > 0 or hi < 0))})
    tab = pd.DataFrame(rows)
    tab = (tab.assign(_abs=tab["spearman_within_season"].abs()).sort_values(["target", "_abs"], ascending=[True, False])
           .drop(columns="_abs").reset_index(drop=True))
    n_sig = int(tab["ci_excludes_0"].sum())
    top = tab[tab["ci_excludes_0"]].assign(a=lambda x: x["spearman_within_season"].abs()).sort_values("a", ascending=False)
    top_txt = "; ".join(f"{r.feature} → {r.target}: ρ = {r.spearman_within_season:+.2f}" for r in top.head(5).itertuples())
    return HypothesisResult(
        hid="K1", link="Spielkontext → Baseline (Ticketing, Catering)",
        statement="Spielkontext (Wetter, Wochentag/Anstosszeit, Gegner- und eigene Stärke, Wettbewerb, Ferien, Free-TV, "
                  "Gästesektor) hängt mit Anwesenheitsquote, IST und KF zusammen.",
        data_basis=f"{len(d)} Herren-Pflichtspiele 22/23–26/27 mit Spielkontext-Tabelle",
        n=len(d),
        method="Je Kontextvariable × Zielgrösse: Spearman-Korrelation mit saison-zentrierter Zielgrösse, Bootstrap-KI; "
               "bei Ja/Nein-Variablen zusätzlich Differenz der Mittelwerte. Explorativ, kein Modell.",
        effect_label="Anzahl Zusammenhänge mit KI ohne 0", estimate=float(n_sig), ci_low=np.nan, ci_high=np.nan,
        neutral=np.nan, status="explorativ (vorläufig)",
        interpretation=(f"{n_sig} von {len(tab)} Kombinationen mit Konfidenzintervall ohne 0 (bei {len(tab)} Tests sind "
                        f"~{0.05 * len(tab):.0f} zufällige Treffer zu erwarten). Stärkste: {top_txt or '–'}."),
        limitations="Viele Tests → Zufallstreffer möglich; Variablen hängen untereinander zusammen (z. B. Anstosszeit und "
                    "Wochentag, UEFA und Sommer). Wetter = Tageswerte, nicht Anstosszeit. Schulferien vor 26/27 recherchiert (D-021). "
                    "«Gästesektor geschlossen/exkl.» stammt meist aus der Bemerkung «ausverkauft (exkl. Gästesektor)» und ist "
                    "daher eher ein Nachfrage-Indikator als ein Kapazitätseffekt (D-022).",
        next_steps="Sparsames Kontextmodell je Zielgrösse mit zeitbasierter Validierung (nach Baseline-Freigabe); "
                   "fehlende 6 Kontextspiele 25/26 ergänzen; Gegnerattraktivität (z. B. Zuschauerschnitt des Gegners) ergänzen.",
        table=tab,
    )


def run_all(t: dict[str, pd.DataFrame], m: pd.DataFrame) -> list[HypothesisResult]:
    return [test_h1(m), test_h2(m), test_h3(t, m), context_associations(m)]


FURTHER_HYPOTHESES = [
    ("H4", "Ticketing × Zutritt", "Spiele mit hohem Abo-Anteil haben höhere No-Show-Quoten (Abo-Inhaber lassen Spiele eher aus).",
     "Abo-Snapshot nur 26/27; Abo-Historie bei Sandro anfragen; Coding-Feld klären."),
    ("H5", "Ticketing × Zutritt", "Online gekaufte Tickets (Webshop) führen zu späterer Ankunft als Kassen-Tickets.",
     "Kanal je Ticket nur in Ticketdaten; Verknüpfung zur Ankunft nur aggregiert je Spiel möglich."),
    ("H6", "Zutritt", "Die Ankunftskurve unterscheidet sich nach Sektor (Fankurve D früher, Haupttribüne später).",
     "access_sector_minute je Sektor; nur Spiele mit vollständigem Zutritt."),
    ("H7", "Zutritt × Catering", "Spiele mit mehr Scans nach Anpfiff haben tieferen Ø Bon (weniger Zeit vor dem Spiel).",
     "share_after_kickoff in der Spieltabelle; Bons ab 23/24."),
    ("H8", "Catering", "Hohe Temperaturen erhöhen den Getränke-Anteil (Ø Bon steigt, Bonsrate steigt).",
     "Artikel nur als Saisonsummen → nur Spielebene Ø Bon/Bonsrate vs. Temperatur testbar."),
    ("H9", "Ticketing", "Kurzfristiger Last-Minute-Verkauf ist bei schwachem Gegner und schlechtem Wetter-Forecast höher.",
     "tickets_single_leadtime (25/26+) und tickets_hist_leadtime (21/22–24/25) mit Kontext verbinden."),
]

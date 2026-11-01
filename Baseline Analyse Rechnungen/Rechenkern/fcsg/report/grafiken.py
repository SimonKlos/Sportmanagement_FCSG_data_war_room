"""Grafiken (PNG) für Gruppe und Methodennotiz. Nur Aggregate; Beschriftung auf Deutsch."""
from __future__ import annotations

from pathlib import Path

import matplotlib
import matplotlib.ticker

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

GRUEN, GRAU, ORANGE, ROT, BLAU = "#0B6E4F", "#8C8C8C", "#E07B00", "#B22222", "#2F5D8A"
STATUS_FARBE = {"belastbar": GRUEN, "Hinweis (Richtung stabil, Grösse unsicher)": ORANGE, "nicht belastbar schätzbar": GRAU}

plt.rcParams.update({"figure.dpi": 110, "savefig.dpi": 200, "font.size": 9.5, "axes.spines.top": False,
                     "axes.spines.right": False, "axes.titleweight": "bold", "axes.titlesize": 11})


def _speichern(fig, pfad: Path, liste: list, titel: str, text: str, layout: bool = True) -> None:
    if layout:
        fig.tight_layout()
    fig.savefig(pfad, bbox_inches="tight")
    plt.close(fig)
    liste.append({"datei": pfad.name, "titel": titel, "aussage": text})


def kf_trend(res, ordner, liste):
    t = res["catering_trend"]
    t = t[t["scope"] == "SL"]
    fig, ax = plt.subplots(figsize=(8, 4))
    farben = [GRAU if s in ("2019/20", "2020/21") else (ORANGE if s == "2026/27" else GRUEN) for s in t["saison"]]
    ax.bar(t["saison"], t["kf_inkl"], color=farben)
    for x, y, n in zip(t["saison"], t["kf_inkl"], t["spiele"]):
        ax.text(x, y + 0.2, f"{y:.2f}\n({n} Sp.)", ha="center", fontsize=8)
    ax.set_ylabel("CHF je Public-Anwesendem (inkl. MwSt)")
    ax.set_title("Kundenfranken Meisterschaft je Saison (Summe Umsatz / Summe Public-Anwesende)")
    ax.set_ylim(0, t["kf_inkl"].max() * 1.25)
    ax.text(0.01, 0.97, "grau: COVID-Saisons · orange: laufende Saison (4 Spiele)", transform=ax.transAxes, fontsize=8,
            va="top", color=GRAU)
    erst, letzt = t.iloc[0], t[t["saison"] == "2025/26"].iloc[0]
    _speichern(fig, ordner / "abb01_kundenfranken_trend.png", liste, "Kundenfranken-Trend",
               f"Der KF (inkl. MwSt) stieg von {erst['kf_inkl']:.2f} ({erst['saison']}) auf {letzt['kf_inkl']:.2f} (2025/26); "
               "Basis inkl. MwSt wegen Netto-Methodenwechsel 2020/21.")


def treiber_saison(res, ordner, liste):
    s = res["saison_kpi"]
    s = s[s["wettbewerbe"] == "SL"]
    kpis = [("ist_mittel", "Ø IST je Spiel", "{:,.0f}"), ("noshow_quote", "No-Show (gewichtet)", "{:.1%}"),
            ("kf_exkl", "KF exkl. MwSt (CHF)", "{:.2f}"), ("bons_pro_anwesende", "Bons je Anwesendem", "{:.2f}"),
            ("bon_exkl", "Ø Bon exkl. MwSt (CHF)", "{:.2f}")]
    fig, axes = plt.subplots(1, 5, figsize=(14, 3.2))
    for ax, (col, titel, f) in zip(axes, kpis):
        d = s.dropna(subset=[col])
        ax.plot(d["saison"].str[2:], d[col], marker="o", color=GRUEN)
        for x, y in zip(d["saison"].str[2:], d[col]):
            ax.annotate(f.format(y).replace(",", "'"), (x, y), textcoords="offset points", xytext=(0, 6), ha="center", fontsize=7.5)
        ax.set_title(titel, fontsize=9.5)
        ax.tick_params(axis="x", rotation=45, labelsize=8)
        ax.margins(y=0.25)
        if col == "noshow_quote":
            ax.yaxis.set_major_formatter(matplotlib.ticker.PercentFormatter(1.0, decimals=0))
    fig.suptitle("Treiberbaum je Saison – Meisterschaft (Umsatz = Anwesende × Bons/Anwesende × Ø Bon; 26/27: erst 4 Spiele)",
                 fontweight="bold")
    _speichern(fig, ordner / "abb02_treiberbaum_saisons.png", liste, "Treiberbaum je Saison",
               "Mengen- und Konsumtreiber je Saison; Bons erst ab 2023/24 verfügbar.")


def effekt_matrix(res, ordner, liste):
    mx = res["kontext_effekt_matrix"]
    ziele = list(dict.fromkeys(mx["zielgroesse"]))
    fig, axes = plt.subplots(1, len(ziele), figsize=(3.4 * len(ziele), 4.2), sharey=True)
    variablen = list(dict.fromkeys(mx["variable"]))
    for ax, z in zip(np.atleast_1d(axes), ziele):
        d = mx[mx["zielgroesse"] == z].set_index("variable").reindex(variablen)
        y = np.arange(len(variablen))
        for i, (_, r) in enumerate(d.iterrows()):
            c = STATUS_FARBE.get(r["beurteilung"], GRAU)
            ax.plot([r["ki95_unten"], r["ki95_oben"]], [i, i], color=c, lw=2)
            ax.plot(r["effekt"], i, "o", color=c, ms=6)
        ax.axvline(0, color="black", lw=0.8)
        ax.set_yticks(y)
        ax.set_yticklabels([v.replace(" (", "\n(") for v in variablen], fontsize=8)
        ax.invert_yaxis()
        einheit = d["einheit_effekt"].dropna().iloc[0] if d["einheit_effekt"].notna().any() else ""
        ax.set_title(z.replace(" (optional)", "").replace(" (IST/SOLL)", ""), fontsize=9.5)
        ax.set_xlabel(f"Effekt in {einheit} (Temperatur: je +5 °C)", fontsize=8)
    handles = [plt.Line2D([0], [0], marker="o", color=c, lw=2, label=l) for l, c in STATUS_FARBE.items()]
    fig.suptitle("Kontext-Effekt-Matrix: Effekt mit 95 %-Intervall je Zielgrösse (Meisterschaft ab 22/23, mit Saison-Effekten)",
                 fontweight="bold")
    fig.tight_layout(rect=(0, 0.08, 1, 0.97))
    fig.legend(handles=handles, loc="lower center", ncol=3, frameon=False, fontsize=8.5, bbox_to_anchor=(0.5, 0.0))
    _speichern(fig, ordner / "abb03_kontext_effekt_matrix.png", liste, "Kontext-Effekt-Matrix",
               "Grün = belastbar (Intervall ohne 0, Vorzeichen stabil über Saisons und Varianten), orange = Hinweis, grau = nicht belastbar.",
               layout=False)


def diagnose_kf(res, ordner, liste):
    k = res["diagnosekarte"].dropna(subset=["erwartet_kf_exkl"]).sort_values("datum")
    fig, ax = plt.subplots(figsize=(13, 4.3))
    x = np.arange(len(k))
    ax.fill_between(x, k["band80_unten_kf_exkl"], k["band80_oben_kf_exkl"], color=GRUEN, alpha=0.15, label="80 %-Erwartungsband")
    ax.plot(x, k["erwartet_kf_exkl"], color=GRUEN, lw=1.2, label="erwartet unter Kontext")
    farben = np.where(k["status_kf_exkl"] == "unter Erwartung", ROT, np.where(k["status_kf_exkl"] == "über Erwartung", BLAU, "black"))
    ax.scatter(x, k["beobachtet_kf_exkl"], c=farben, s=18, zorder=3, label="beobachtet")
    grenzen = np.where(k["saison"].ne(k["saison"].shift()))[0]
    for g in grenzen:
        ax.axvline(g - 0.5, color=GRAU, lw=0.6, ls=":")
        ax.text(g, k["band80_oben_kf_exkl"].max() * 1.02, k["saison"].iloc[g], fontsize=8, color=GRAU)
    ax.set_xticks(x)
    ax.set_xticklabels(k["datum"].dt.strftime("%d.%m.%y"), rotation=90, fontsize=6.5)
    ax.set_ylabel("KF exkl. MwSt (CHF)")
    ax.set_title("Diagnosekarte Kundenfranken: beobachtet vs. erwartet unter Kontext (rot = unter, blau = über dem Band)")
    ax.legend(loc="lower left", fontsize=8, frameon=False)
    _speichern(fig, ordner / "abb04_diagnosekarte_kf.png", liste, "Diagnosekarte Kundenfranken",
               "Punkte ausserhalb des Bands sind Prüfkandidaten, kein Potenzialnachweis (Messfehler, fehlende Variablen, Zufall möglich).")


def ankunft_sektor(res, ordner, liste):
    k = res["ankunftskurve_sektor"]
    fig, ax = plt.subplots(figsize=(8.5, 4.5))
    farben = {"Alle": "black", "D": GRUEN, "HH (Hospitality)": BLAU, "B4 (Gäste)": ORANGE, "B": "#6AA84F", "A": "#9E7AC2", "C": ROT}
    for sek, g in k.groupby("sektor"):
        ax.plot(g["minute_relativ"], g["anteil_mittel"] * 100, label=sek, color=farben.get(sek, GRAU),
                lw=2.4 if sek == "Alle" else 1.4)
    ax.axvline(0, color="black", lw=0.8)
    ax.axvline(-45, color=GRAU, lw=0.8, ls="--")
    ax.text(-44, 3, "45 min vor Anpfiff", fontsize=8, color=GRAU)
    ax.set_xlabel("Minuten relativ zum Anpfiff")
    ax.set_ylabel("bereits eingetreten (%)")
    ax.set_xlim(-150, 30)
    ax.set_title("Ankunftskurve nach Eingang (Mittel über alle vollständigen Spiele 22/23–26/27)")
    ax.legend(fontsize=8, frameon=False)
    _speichern(fig, ordner / "abb05_ankunft_nach_eingang.png", liste, "Ankunftskurve nach Eingang",
               "Fankurve (D) und Hospitality kommen früh, Tribünen A und C spät – das Konsumfenster vor Anpfiff ist ungleich verteilt.")


def absatzkurven(res, ordner, liste):
    k = res["absatzkurven"].merge(res["absatz_je_spiel"][["match_id", "ausverkauft", "wettbewerb"]], on="match_id")
    k = k[(k["wettbewerb"] == "SL") & (k["tage_vor_spiel"] <= 45)]
    fig, ax = plt.subplots(figsize=(8, 4.2))
    for ausv, farbe, label in [(True, GRUEN, "ausverkaufte Spiele"), (False, ORANGE, "nicht ausverkauft")]:
        g = k[k["ausverkauft"] == ausv].groupby("tage_vor_spiel")["anteil_bereits_verkauft"]
        med, q1, q3 = g.median(), g.quantile(0.25), g.quantile(0.75)
        ax.plot(med.index, med * 100, color=farbe, lw=2, label=f"{label} (Median)")
        ax.fill_between(med.index, q1 * 100, q3 * 100, color=farbe, alpha=0.15)
    ax.invert_xaxis()
    ax.set_xlabel("Tage vor dem Spiel")
    ax.set_ylabel("Anteil der Einzeltickets bereits verkauft (%)")
    ax.set_title("Einzelticket-Absatzkurven Meisterschaft (ohne Abos – keine Stadion-Ausverkaufskurve)")
    ax.legend(frameon=False, fontsize=8.5)
    a = res["absatz_ausverkauft"].set_index("ausverkauft")
    _speichern(fig, ordner / "abb06_einzelticket_absatzkurven.png", liste, "Einzelticket-Absatzkurven",
               f"Ausverkaufte Spiele: 50 % der Einzeltickets {a.loc[True, 't50_median']:.0f} Tage vor dem Spiel verkauft "
               f"(sonst {a.loc[False, 't50_median']:.0f} Tage); Spieltagsanteil {a.loc[True, 'anteil_spieltag_median']:.0%} "
               f"vs. {a.loc[False, 'anteil_spieltag_median']:.0%}.")


def noshow_segmente(res, ordner, liste):
    s = res["eintritt_segmente"]
    wahl = [("Tickets pro Bestellung", None), ("Tarifgruppe", None), ("Verkaufskanal", None)]
    fig, axes = plt.subplots(1, 3, figsize=(13, 3.8))
    for ax, (m, _) in zip(axes, wahl):
        d = s[(s["merkmal"] == m) & s["noshow_quote"].notna() & (s["tickets"] >= 500)]
        if m == "Tickets pro Bestellung":
            reihenfolge = {"1": 0, "2": 1, "3–4": 2, "5–9": 3, "10+": 4}
            d = d.assign(_o=d["auspraegung"].map(reihenfolge)).sort_values("_o", ascending=False)
        else:
            d = d.sort_values("noshow_quote")
        ax.barh(d["auspraegung"].astype(str), d["noshow_quote"] * 100, color=GRUEN)
        for y, (v, n) in enumerate(zip(d["noshow_quote"], d["tickets"])):
            ax.text(v * 100 + 0.5, y, f"{v:.0%}  (n={n:,})".replace(",", "'"), va="center", fontsize=7.5)
        ax.set_title(m, fontsize=9.5)
        ax.set_xlabel("No-Show Einzeltickets (%)")
        ax.set_xlim(0, max(35, d["noshow_quote"].max() * 130) if len(d) else 35)
    fig.suptitle("No-Show der Einzeltickets nach Segment (valide ZKS-Spiele 2021/22–2022/23)", fontweight="bold")
    _speichern(fig, ordner / "abb07_noshow_segmente.png", liste, "No-Show nach Segment",
               "Grossbestellungen, Gratis-/Promotickets und Inhouse-Verkäufe haben deutlich höhere No-Show-Quoten.")


def kf_zerlegung(res, ordner, liste):
    d = res["kf_je_spiel"]
    fig, ax = plt.subplots(figsize=(7, 5))
    saisons = sorted(d["saison"].unique())
    farben = dict(zip(saisons, [GRAU, BLAU, ORANGE, GRUEN, ROT][: len(saisons)]))
    for s in saisons:
        g = d[d["saison"] == s]
        ax.scatter(g["bons_pro_anwesende"], g["bon_exkl"], s=22, color=farben[s], label=s)
    xs = np.linspace(d["bons_pro_anwesende"].min() * 0.97, d["bons_pro_anwesende"].max() * 1.03, 50)
    for kf in [12, 13, 14, 15, 16, 17, 18]:
        ax.plot(xs, kf / xs, color=GRAU, lw=0.6, ls=":")
        ax.text(xs[-1], kf / xs[-1], f"KF {kf}", fontsize=7, color=GRAU)
    ax.set_xlabel("Bons je Public-Anwesendem")
    ax.set_ylabel("Ø Bon exkl. MwSt (CHF)")
    ax.set_title("KF = Bons je Anwesendem × Ø Bon (je Pflichtspiel, ab 2023/24)")
    ax.legend(frameon=False, fontsize=8)
    z = res["kf_zerlegung"]
    z = z[(z["scope"] == "SL ab 2023/24") & (z["variante"] == "Streuung innerhalb der Saison")].iloc[0]
    _speichern(fig, ordner / "abb08_kf_zerlegung.png", liste, "Zerlegung Kundenfranken",
               f"Innerhalb der Saison erklärt der Ø Bon {z['anteil_bon']:.0%} und Bons/Anwesende {z['anteil_bons_pro_anwesende']:.0%} "
               "der KF-Streuung (Rest: Kovarianz); gepunktete Linien = gleicher KF.")


def scan_ist(res, ordner, liste):
    s = res["scan_ist"].copy()
    s = s[s["abweichung_scans_ist"] > -0.5]
    fig, ax = plt.subplots(figsize=(11, 3.6))
    farben = np.where(s["abweichung_scans_ist"].abs() <= 0.01, GRUEN, np.where(s["abweichung_scans_ist"] < -0.03, ROT, ORANGE))
    ax.scatter(s["datum"], s["abweichung_scans_ist"] * 100, c=farben, s=18)
    ax.axhline(0, color="black", lw=0.8)
    ax.set_ylabel("Scans / IST − 1 (%)")
    ax.set_title("Abgleich Drehkreuz-Scans vs. IST je Spiel (Spiele mit vollständiger Lieferung)")
    neu = s[s["saison"] >= "2025/26"]["abweichung_scans_ist"].mean()
    alt = s[s["saison"] < "2025/26"]["abweichung_scans_ist"].mean()
    _speichern(fig, ordner / "abb09_scans_vs_ist.png", liste, "Scans vs. IST",
               f"Ab 2025/26 liegen die Scans im Mittel {neu:+.1%} vom IST entfernt, davor {alt:+.1%} (IST mit manuellen Zählungen).")


def artikelmix(res, ordner, liste):
    g = res["artikel_gruppen"]
    g = g[g["name"].isin(["Alkoholische Getränke", "Food", "Alk.-freie Getränke", "Kiosk"])]
    piv = g.pivot_table(index="saison", columns="name", values="anteil")
    fig, ax = plt.subplots(figsize=(7, 3.8))
    unten = np.zeros(len(piv))
    farben = {"Alkoholische Getränke": ORANGE, "Food": GRUEN, "Alk.-freie Getränke": BLAU, "Kiosk": GRAU}
    for c in ["Alkoholische Getränke", "Food", "Alk.-freie Getränke", "Kiosk"]:
        if c in piv:
            ax.bar(piv.index, piv[c] * 100, bottom=unten, color=farben[c], label=c)
            for i, (b, v) in enumerate(zip(unten, piv[c])):
                if v > 0.05:
                    ax.text(i, b + v * 50, f"{v:.0%}", ha="center", va="center", color="white", fontsize=8.5)
            unten += piv[c].fillna(0).to_numpy() * 100
    ax.set_ylabel("Anteil am Umsatz, brutto (%)")
    ax.set_title("Sortimentsmix Meisterschaft je Saison (einheitliche Brutto-Basis)")
    ax.legend(frameon=False, fontsize=8, bbox_to_anchor=(1, 1))
    alk = piv["Alkoholische Getränke"] if "Alkoholische Getränke" in piv else pd.Series(dtype=float)
    _speichern(fig, ordner / "abb10_sortimentsmix.png", liste, "Sortimentsmix",
               f"Der Alkoholanteil sinkt von {alk.iloc[0]:.0%} ({alk.index[0]}) auf {alk.iloc[-1]:.0%} ({alk.index[-1]}); "
               "Food und alkoholfreie Getränke gewinnen Anteile (Anteile auf einheitlicher Brutto-Basis).")


def kiesplatz(res, ordner, liste):
    k = res["kiesplatz_je_spiel"].dropna(subset=["anteil_am_catering_total"])
    k = k[k["wettbewerb"].isin(["SL", "Cup", "UEFA"])]
    fig, ax = plt.subplots(figsize=(7.5, 3.6))
    saisons = sorted(k["saison"].unique())
    ax.boxplot([k[k["saison"] == s]["anteil_am_catering_total"] * 100 for s in saisons])
    ax.set_xticks(range(1, len(saisons) + 1))
    ax.set_xticklabels(saisons)       # versionsunabhängig (tick_labels erst ab matplotlib 3.9)
    ax.set_ylabel("Kiesplatz in % des Catering-Totals")
    ax.set_title("Kiesplatz-Anteil je Spiel (Teilmenge des Catering-Totals – nicht addieren)")
    med = k.groupby("saison")["anteil_am_catering_total"].median()
    _speichern(fig, ordner / "abb11_kiesplatz_anteil.png", liste, "Kiesplatz-Anteil",
               f"Der Kiesplatz macht im Median {med.min():.0%}–{med.max():.0%} des Catering-Umsatzes eines Spiels aus und ist im "
               "Total bereits enthalten.")


def ankunft_konsum(res, ordner, liste):
    a = res["ankunft_je_spiel"].merge(res["spiel_kpi"][["match_id", "bons_pro_anwesende", "kf_exkl"]], on="match_id")
    a = a.dropna(subset=["bons_pro_anwesende"])
    a["frueh_dm"] = (a["anteil_ab_45_min"] - a.groupby("saison")["anteil_ab_45_min"].transform("mean")) * 100
    a["kf_dm"] = (a["kf_exkl"] / a.groupby("saison")["kf_exkl"].transform("mean") - 1) * 100
    fig, ax = plt.subplots(figsize=(6.5, 4.3))
    ax.scatter(a["frueh_dm"], a["kf_dm"], s=20, color=GRUEN)
    if len(a) > 3:
        b = np.polyfit(a["frueh_dm"], a["kf_dm"], 1)
        xs = np.linspace(a["frueh_dm"].min(), a["frueh_dm"].max(), 10)
        ax.plot(xs, np.polyval(b, xs), color=ORANGE, lw=1.2)
    ax.axhline(0, color=GRAU, lw=0.6)
    ax.axvline(0, color=GRAU, lw=0.6)
    ax.set_xlabel("Frühankommende (≥ 45 min) – Abweichung vom Saisonmittel (Pp.)")
    ax.set_ylabel("KF – Abweichung vom Saisonmittel (%)")
    ax.set_title("Ankunft und Konsum je Spiel (saisonbereinigt)")
    _speichern(fig, ordner / "abb12_ankunft_und_konsum.png", liste, "Ankunft und Konsum",
               "Schwacher, nach Kontextkontrolle nicht belastbarer Zusammenhang – Ankunft→Konsum bleibt Hypothese (keine Bon-Zeitstempel).")


def toroeffnung(res, ordner, liste):
    v = res["toroeffnung_verlauf"]
    did = res["toroeffnung_did"].set_index("zielgroesse")
    fig, axes = plt.subplots(1, 2, figsize=(13, 4))
    farben = {"D": GRUEN, "A": "#9E7AC2", "C": ROT}
    for ax, (col, titel) in zip(axes, [("einlass_1pct_min_vor_anpfiff", "Einlass-Beginn je Eingang (≈ Toröffnung)"),
                                       ("median_min_vor_anpfiff", "Median der Ankunft je Eingang")]):
        for sek, g in v.groupby("sektor"):
            ax.plot(g["datum"], g[col], marker="o", ms=3, lw=1, color=farben.get(sek, GRAU), label=f"Sektor {sek}")
        ax.axvline(pd.Timestamp("2023-04-02"), color="black", ls="--", lw=0.8)
        ax.text(pd.Timestamp("2023-04-10"), ax.get_ylim()[1] * 0.97, "D öffnet ab 02.04.2023\n90 statt 60 min vorher",
                fontsize=8, va="top")
        ax.set_title(titel)
        ax.set_ylabel("Minuten vor Anpfiff")
        ax.legend(frameon=False, fontsize=8, loc="lower right")
    eff = did.loc["Median Ankunft, min vor Anpfiff"]
    fig.suptitle("Natürliches Experiment Toröffnung: Sektor D vs. A/C (gleiche Spiele)", fontweight="bold")
    _speichern(fig, ordner / "abb13_toroeffnung_experiment.png", liste, "Toröffnung als Hebel",
               f"30 min frühere Öffnung verschiebt die Ankunft in D um {eff['did_effekt']:+.1f} min "
               f"(95 %-KI {eff['ki95_unten']:.1f} bis {eff['ki95_oben']:.1f}) gegenüber A/B/C; Konsumwirkung noch offen.")


def erstelle_grafiken(res: dict[str, pd.DataFrame], ordner: Path) -> pd.DataFrame:
    ordner.mkdir(parents=True, exist_ok=True)
    liste: list = []
    for f in [kf_trend, treiber_saison, effekt_matrix, diagnose_kf, ankunft_sektor, absatzkurven, noshow_segmente,
              kf_zerlegung, scan_ist, artikelmix, kiesplatz, ankunft_konsum, toroeffnung]:
        f(res, ordner, liste)
    return pd.DataFrame(liste)

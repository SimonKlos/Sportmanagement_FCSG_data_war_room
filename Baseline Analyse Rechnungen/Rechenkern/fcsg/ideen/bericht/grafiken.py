"""Grafiken der Ideen-Grundlage (PNG). Gestaltung nach dem dataviz-Verfahren: validierte Palette (Blau/Orange/Aqua,
CVD-geprüft), dünne Marken, Haarlinien-Raster, eine y-Achse, Legende ab zwei Reihen, selektive Direktbeschriftung.
Die Datentabelle zu jeder Grafik steht im Excel (Blattname in der Bildunterschrift).
"""
from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import matplotlib.ticker as mtick  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from ..fmt import chf_k, p, pct, z  # noqa: E402

BLAU, ORANGE, AQUA = "#2a78d6", "#eb6834", "#1baf7a"
GRAU, GRAU_HELL = "#898781", "#c3c2b7"
INK, INK2, RASTER, FLAECHE = "#0b0b0b", "#52514e", "#e1e0d9", "#fcfcfb"

plt.rcParams.update({
    "font.family": ["Helvetica Neue", "Helvetica", "Arial", "DejaVu Sans"], "font.size": 9.5,
    "figure.facecolor": FLAECHE, "axes.facecolor": FLAECHE, "savefig.facecolor": FLAECHE, "figure.dpi": 110, "savefig.dpi": 200,
    "axes.edgecolor": GRAU_HELL, "axes.linewidth": 0.8, "axes.labelcolor": INK2, "axes.titlecolor": INK, "axes.titlesize": 11,
    "axes.titleweight": "bold", "axes.titlelocation": "left", "axes.titlepad": 12, "xtick.color": INK2, "ytick.color": INK2,
    "axes.spines.top": False, "axes.spines.right": False, "axes.spines.left": False, "axes.grid": True, "axes.grid.axis": "y",
    "grid.color": RASTER, "grid.linewidth": 0.6, "grid.linestyle": "-", "legend.frameon": False, "legend.fontsize": 8.5,
    "axes.axisbelow": True,
})


def _speichern(fig, ordner: Path, datei: str, titel: str, aussage: str, blatt: str, liste: list) -> None:
    fig.savefig(ordner / datei, bbox_inches="tight", pad_inches=0.15)
    plt.close(fig)
    liste.append({"datei": datei, "titel": titel, "aussage": aussage, "tabelle_im_excel": blatt})


def _pct_fmt(dez: int = 0):
    def f(v, _):
        if abs(v) < 1e-9:
            return "0 %"
        return f"{v:+.{dez}f} %".replace("-", "−")
    return mtick.FuncFormatter(f)


KURZ = {"FC Basel": "Basel", "BSC Young Boys": "YB", "FC Zürich": "FCZ", "Grasshopper Club Zürich": "GC", "FC Luzern": "Luzern",
        "FC Lugano": "Lugano", "Servette FC": "Servette", "FC Sion": "Sion", "FC Lausanne-Sport": "Lausanne",
        "Stade Lausanne-Ouchy": "SLO", "FC Winterthur": "Winterthur", "FC Thun": "Thun", "Yverdon Sport": "Yverdon"}


def _hbar_raster(ax):
    ax.grid(axis="y", visible=False)
    ax.grid(axis="x", visible=True)
    ax.spines["left"].set_visible(False)
    ax.spines["bottom"].set_visible(False)
    ax.tick_params(axis="y", length=0)


# --------------------------------------------------------------------------------------------
def faustwerte(e, kz, ordner, liste):
    rv = e["reto_faustwerte"].set_index("kennzahl")
    zeilen = [("Anwesende je Spiel (A1)", "Anwesende je Spiel", "{:,.0f}"),
              ("Catering-Umsatz Meisterschaft je Saison (CHF)", "Catering-Umsatz je Saison", "CHF"),
              ("+CHF 1 Kundenfranken je Saison (CHF)", "+CHF 1 Kundenfranken", "CHF"),
              ("1 Pp. No-Show: CHF je Saison (φ = 1)", "1 Pp. weniger No-Show (φ = 1)", "CHF"),
              ("+1 % Kauffrequenz je Saison (CHF)", "+1 % Kauffrequenz", "CHF")]
    fig, ax = plt.subplots(figsize=(8.2, 3.6))
    y = np.arange(len(zeilen))[::-1]
    for yi, (key, label, f) in zip(y, zeilen):
        r = rv.loc[key]
        ax.barh(yi, r["faktor_daten_zu_reto"] * 100, color=BLAU, height=0.55)
        reto = chf_k(r["reto_annahme"]) if f == "CHF" else z(r["reto_annahme"])
        daten = chf_k(r["daten_2025_26"]) if f == "CHF" else z(r["daten_2025_26"])
        ax.text(r["faktor_daten_zu_reto"] * 100 + 1.5, yi, f"{r['faktor_daten_zu_reto'] * 100:.0f} %", va="center", fontsize=8.5, color=INK)
        ax.text(103, yi, f"Daten {daten} statt {reto}", va="center", fontsize=8.5, color=INK)
    ax.axvline(100, color=INK2, lw=1)
    ax.text(98.5, y.min() - 0.72, "Retos Annahme = 100 %", ha="right", va="center", fontsize=8, color=INK2)
    ax.set_ylim(y.min() - 1.0, y.max() + 0.5)
    ax.set_yticks(y)
    ax.set_yticklabels([z_[1] for z_ in zeilen])
    ax.set_xlim(0, 175)
    ax.set_xticks([0, 25, 50, 75, 100])
    ax.xaxis.set_major_formatter(mtick.PercentFormatter(100, decimals=0))
    _hbar_raster(ax)
    ax.set_title("Korrigierte Faustwerte: Daten 2025/26 in Prozent von Retos Annahmen")
    _speichern(fig, ordner, "abb_i01_faustwerte.png", "Korrigierte Faustwerte",
               f"Retos Sizings beruhen auf 18'000 Anwesenden; real sind es {z(kz['b_public_netto_mittel'])} – alle Hebelwerte liegen "
               "rund ein Viertel tiefer.", "Reto_Faustwerte", liste)


def leere_plaetze(e, kz, ordner, liste):
    d = e["zweitmarkt_je_spiel"]
    d = d[d["saison"] == "2025/26"].sort_values("datum")
    fig, ax = plt.subplots(figsize=(10.5, 3.9))
    x = np.arange(len(d))
    ax.bar(x - 0.2, d["leere_plaetze"], width=0.4, color=GRAU_HELL, label="leere, vergebene Plätze (SOLL − IST)", edgecolor=FLAECHE, lw=1)
    ax.bar(x + 0.2, d["zweitmarkt_historie"], width=0.4, color=BLAU, label="über den Zweitmarkt weiterverkauft", edgecolor=FLAECHE, lw=1)
    ax.set_xticks(x)
    ax.set_xticklabels([f"{t:%d.%m.}\n{KURZ.get(g, g)}" for t, g in zip(d["datum"], d["gegner_anzeige"])], fontsize=7)
    ax.yaxis.set_major_formatter(mtick.FuncFormatter(lambda v, _: f"{v:,.0f}".replace(",", "'")))
    ax.set_ylabel("Plätze je Spiel")
    ax.legend(loc="upper left", ncol=2)
    ax.set_ylim(0, d["leere_plaetze"].max() * 1.22)
    ax.set_title("Leere Plätze und Zweitmarkt je Meisterschaftsspiel 2025/26")
    _speichern(fig, ordner, "abb_i02_leere_plaetze_zweitmarkt.png", "Leere Plätze und Zweitmarkt",
               f"{z(kz['b_noshow_summe'])} leere, vergebene Plätze; der Zweitmarkt besetzte {z(kz['zm_2526'])} davon neu "
               f"({p(kz['zm_wb_2526'])}).", "Zweitmarkt_je_Spiel", liste)


def tribuenen(e, kz, ordner, liste):
    t = e["tribuene_2627"].set_index("tribuene").reindex(["B", "C", "D"])
    namen = {"B": "Osttribüne B", "C": "Tribüne C", "D": "Fankurve D"}
    fig, ax = plt.subplots(figsize=(8.2, 3.2))
    y = np.arange(len(t))[::-1]
    for yi, (tr, r) in zip(y, t.iterrows()):
        lo, hi = sorted([r["abo_anwesenheit_bei_r_unten"], r["abo_anwesenheit_bei_r_oben"]])
        ax.plot([lo * 100, hi * 100], [yi - 0.12, yi - 0.12], color=ORANGE, lw=5, solid_capstyle="round",
                label="Abo-Plätze genutzt (Bandbreite)" if yi == y[0] else None)
        ax.plot(r["scans_je_platz"] * 100, yi + 0.12, "o", color=BLAU, ms=8, label="alle vergebenen Plätze genutzt" if yi == y[0] else None)
        ax.text(101, yi, f"{z(r['leere_plaetze_je_spiel'])} leere Plätze je Spiel", va="center", fontsize=8.5, color=INK)
    ax.set_yticks(y)
    ax.set_yticklabels([namen[tr] for tr in t.index])
    ax.set_xlim(60, 125)
    ax.xaxis.set_major_formatter(mtick.PercentFormatter(100, decimals=0))
    ax.set_xticks([60, 70, 80, 90, 100])
    _hbar_raster(ax)
    ax.legend(loc="upper center", bbox_to_anchor=(0.4, -0.13), ncol=2, fontsize=8)
    ax.set_title("Wer kommt? Nutzung der vergebenen Plätze je Tribüne (4 Meisterschaftsspiele 2026/27)")
    _speichern(fig, ordner, "abb_i03_tribuenen.png", "Tribünen 2026/27",
               f"Abo-Plätze in der Fankurve D werden am seltensten genutzt ({p(kz['tr_D_abo_lo'])}–{p(kz['tr_D_abo_hi'])}); Näherung aus "
               "Abo-Snapshot, Einzeltickets und Scans je Eingang.", "Tribuene_2627", liste)


def noshow_segmente(e, kz, ordner, liste):
    s = e["einzel_noshow_segmente"].head(8).copy()
    s["label"] = s["kanal"] + " · " + s["preis"] + " · " + s["tickets_pro_bestellung"] + np.where(s["tickets_pro_bestellung"] == "1", " Ticket", " Tickets")
    fig, ax = plt.subplots(figsize=(8.4, 3.8))
    y = np.arange(len(s))[::-1]
    farben = [BLAU if (k == "Inhouse" and b == "10+") else GRAU_HELL for k, b in zip(s["kanal"], s["tickets_pro_bestellung"])]
    ax.barh(y, s["anteil_an_allen_noshows"] * 100, color=farben, height=0.6)
    for yi, (_, r) in zip(y, s.iterrows()):
        ax.text(r["anteil_an_allen_noshows"] * 100 + 0.6, yi, f"{p(r['anteil_an_allen_noshows'])} der No-Shows · Quote {p(r['noshow_quote'], 1)}",
                va="center", fontsize=8, color=INK)
    ax.set_yticks(y)
    ax.set_yticklabels(s["label"], fontsize=8.5)
    ax.set_xlim(0, s["anteil_an_allen_noshows"].max() * 100 * 1.75)
    ax.xaxis.set_major_formatter(mtick.PercentFormatter(100, decimals=0))
    _hbar_raster(ax)
    ax.set_title("Woher die No-Shows der Einzeltickets kommen (2021/22–2022/23)")
    _speichern(fig, ordner, "abb_i04_noshow_segmente.png", "No-Show-Segmente",
               f"Inhouse-Bestellungen ab 10 Tickets (blau) verursachen {p(kz['seg_inhouse10_anteil'])} aller Einzelticket-No-Shows.",
               "Einzel_NoShow_Segmente", liste)


def spieltypen(e, kz, ordner, liste):
    t = e["spieltypen"].sort_values("noshow_quote")
    fig, ax = plt.subplots(figsize=(8.2, 3.2))
    y = np.arange(len(t))
    farben = [BLAU if "Spontan" in s else GRAU_HELL for s in t["spieltyp"]]
    ax.barh(y, t["noshow_quote"] * 100, color=farben, height=0.6)
    for yi, (_, r) in zip(y, t.iterrows()):
        ax.text(r["noshow_quote"] * 100 + 0.4, yi, f"{p(r['noshow_quote'], 1)} No-Show · {int(r['spiele'])} Spiele · KF {r['kf_exkl']:.2f}",
                va="center", fontsize=8, color=INK)
    ax.set_yticks(y)
    ax.set_yticklabels(t["spieltyp"], fontsize=8.5)
    ax.set_xlim(0, t["noshow_quote"].max() * 100 * 1.65)
    ax.xaxis.set_major_formatter(mtick.PercentFormatter(100, decimals=0))
    _hbar_raster(ax)
    ax.set_title("Spieltypen aus dem Einzelticket-Vorlauf und ihre No-Show-Quote (Meisterschaft ab 2022/23)")
    _speichern(fig, ordner, "abb_i05_spieltypen.png", "Spieltypen",
               f"«Spontanpublikum» (späte, schwache Nachfrage) hat die höchste No-Show-Quote – unabhängig von der Gegnerstärke "
               f"(p = {kz['typ_p_gegner']:.2f}).", "Spieltypen", liste)


def fruehindikator(e, kz, ordner, liste):
    v = e["fruehindikator_vorhersagen"]
    v = v[v["zielgroesse"] == "IST (Anwesende)"]
    fig, ax = plt.subplots(figsize=(6.2, 4.6))
    for ausv, farbe, label in ((False, BLAU, "nicht ausverkauft"), (True, ORANGE, "ausverkauft")):
        x = v[v["ausverkauft"] == ausv]
        ax.scatter(x["vorhersage"] / 1000, x["beobachtet"] / 1000, s=34, color=farbe, label=label, edgecolor=FLAECHE, lw=1.5, zorder=3)
    lo, hi = v[["vorhersage", "beobachtet"]].min().min() / 1000 * 0.95, v[["vorhersage", "beobachtet"]].max().max() / 1000 * 1.03
    ax.plot([lo, hi], [lo, hi], color=INK2, lw=1)
    ax.text(hi - (hi - lo) * 0.02, hi - (hi - lo) * 0.06, "Linie = perfekte Prognose", fontsize=8, color=INK2, va="top", ha="right")
    ax.set_xlim(lo, hi)
    ax.set_ylim(lo, hi)
    ax.grid(axis="x", visible=True)
    ax.set_xlabel("Prognose 7 Tage vorher (Tausend Anwesende)")
    ax.set_ylabel("tatsächlich anwesend (Tausend)")
    ax.legend(loc="upper left")
    ax.set_title("Frühindikator: Prognose der Anwesenden 7 Tage vor dem Spiel")
    _speichern(fig, ordner, "abb_i06_fruehindikator.png", "Frühindikator T-7",
               f"Jedes Spiel nur mit früheren Spielen vorhergesagt: mittlerer Fehler {z(kz['fi_mae_t7'])} Anwesende "
               f"(nur Kontext: {z(kz['fi_mae_ktx'])}).", "Fruehindikator_Vorhersagen", liste)


def verweilzeit(e, kz, ordner, liste):
    v = e["verweilzeit_eingang"].set_index("sektor").reindex(["A", "B", "C", "D", "B4 (Gäste)"]).dropna(how="all")
    namen = {"A": "Haupttribüne A", "B": "Osttribüne B", "C": "Tribüne C", "D": "Fankurve D", "B4 (Gäste)": "Gästesektor B4"}
    fig, ax = plt.subplots(figsize=(8.2, 3.3))
    y = np.arange(len(v))[::-1]
    farben = [BLAU if s == "C" else GRAU_HELL for s in v.index]
    ax.barh(y, v["verweil_mittel"], color=farben, height=0.6)
    for yi, (s, r) in zip(y, v.iterrows()):
        ax.text(r["verweil_mittel"] + 1, yi, f"{r['verweil_mittel']:.0f} min · {p(r['anteil_letzte_15_min'])} in den letzten 15 min · "
                f"Ø {z(r['besucher_je_spiel'])} Besucher", va="center", fontsize=8, color=INK)
    ax.set_yticks(y)
    ax.set_yticklabels([namen[s] for s in v.index])
    ax.set_xlim(0, v["verweil_mittel"].max() * 2.0)
    ax.set_xlabel("Minuten im Stadion vor dem Anpfiff (Mittel je Besucher)")
    _hbar_raster(ax)
    ax.set_title("Zeitfenster vor dem Anpfiff je Eingang (71 Spiele mit vollständigen Zutrittsdaten)")
    _speichern(fig, ordner, "abb_i07_verweilzeit.png", "Verweilzeit vor Anpfiff",
               f"Die grösste Tribüne C hat das kürzeste Zeitfenster ({z(kz['vw_C'])} min); die Fankurve D ist dank früher Toröffnung "
               f"{z(kz['vw_D'])} min vor Anpfiff drin.", "Verweilzeit_Eingang", liste)


def einlass(e, kz, ordner, liste):
    s = e["einlass_spitzen"].set_index("sektor").reindex(["A", "B", "C", "D", "B4 (Gäste)"]).dropna(how="all")
    kap = float(s["leser_kapazitaet_p95"].iloc[0])
    fig, ax = plt.subplots(figsize=(8.2, 3.0))
    y = np.arange(len(s))[::-1]
    ax.barh(y, s["spitze_je_leser"], color=BLAU, height=0.55)
    ax.axvline(kap, color=INK2, lw=1)
    ax.text(kap + 0.3, y.min() - 0.7, f"Kapazität eines Lesers ≈ {kap:.0f} Scans/min", ha="left", va="center", fontsize=8, color=INK2)
    ax.set_ylim(y.min() - 1.0, y.max() + 0.5)
    for yi, (sek, r) in zip(y, s.iterrows()):
        ax.text(r["spitze_je_leser"] + 0.4, yi, f"{r['spitze_je_leser']:.1f}/min je Leser · Spitze {r['spitze_min_vor_anpfiff']:.0f} min vor Anpfiff",
                va="center", fontsize=8, color=INK)
    ax.set_yticks(y)
    ax.set_yticklabels(s.index)
    ax.set_xlim(0, kap * 1.9)
    ax.set_xlabel("Scans pro Minute je aktivem Leser in der Spitzenminute (Median über Spiele)")
    _hbar_raster(ax)
    ax.set_title("Einlass-Spitzen: Ist das Drehkreuz der Engpass?")
    _speichern(fig, ordner, "abb_i08_einlass.png", "Einlass-Spitzen",
               "Nur der Einlassbeginn in D kommt nahe an die Leser-Kapazität; in A/B/C ist spätes Kommen eher Verhalten als Stau.",
               "Einlass_Spitzen", liste)


def kf_entwicklung(e, kz, ordner, liste):
    b = e["basis_saison"]
    b = b[b["basis"].isin(["2023/24", "2024/25", "2025/26"])].set_index("basis")
    reihen = [("kf_exkl", "Kundenfranken", BLAU), ("bons_pro_anwesende", "Kauffrequenz (Bons je Anwesendem)", ORANGE),
              ("bon_exkl", "Ø Bon", AQUA)]
    fig, ax = plt.subplots(figsize=(7.6, 3.9))
    x = np.arange(len(b))
    for col, label, farbe in reihen:
        idx = b[col] / b[col].iloc[0] * 100
        ax.plot(x, idx, color=farbe, lw=2, marker="o", ms=6, label=label)
        ax.text(x[-1] + 0.07, idx.iloc[-1], f"{idx.iloc[-1] - 100:+.1f} %".replace("-", "−"), va="center", fontsize=8.5, color=INK)
    ax.axhline(100, color=GRAU_HELL, lw=0.8)
    ax.set_xticks(x)
    ax.set_xticklabels(b.index)
    ax.set_xlim(-0.2, len(b) - 0.55)
    ax.set_ylabel("Index 2023/24 = 100")
    ax.yaxis.set_major_formatter(mtick.FuncFormatter(lambda v, _: f"{v:.0f}"))
    ax.legend(loc="upper left")
    ax.set_title("Woher das KF-Wachstum kommt: mehr Käufe, kleinere Bons (Meisterschaft, exkl. MwSt)")
    _speichern(fig, ordner, "abb_i09_kf_entwicklung.png", "KF-Entwicklung",
               f"KF {pct(kz['kf_entw_kf'])} = Frequenz {pct(kz['kf_entw_freq'])} × Ø Bon {pct(kz['kf_entw_bon'])}; Preise je Einheit "
               f"{pct(kz['pm_preis'], 1)}.", "KF_Entwicklung", liste)


def warenkorb(e, kz, ordner, liste):
    w = e["warenkorb_artikel"].head(10).set_index("name")
    saisons = [c for c in ("2023/24", "2024/25", "2025/26") if c in w.columns]
    fig, ax = plt.subplots(figsize=(8.0, 4.2))
    y = np.arange(len(w))[::-1]
    for s, farbe in zip(saisons, (GRAU_HELL, ORANGE, BLAU)):
        ax.scatter(w[s], y, color=farbe, s=40, label=s, zorder=3, edgecolor=FLAECHE, lw=1.5)
    for yi, (_, r) in zip(y, w.iterrows()):
        if "2025/26" in w.columns and pd.notna(r["2025/26"]):
            ax.text(np.nanmax(r[saisons].to_numpy(float)) * 1.12, yi, f"{r['2025/26']:.0f}", va="center", fontsize=8, color=INK)
    ax.set_yticks(y)
    ax.set_yticklabels(w.index)
    ax.set_xscale("log")
    ax.set_xlim(right=float(np.nanmax(w[saisons].to_numpy(float))) * 1.6)
    ax.xaxis.set_major_formatter(mtick.FuncFormatter(lambda v, _: f"{v:g}"))
    ax.set_xlabel("Einheiten je 100 Public-Anwesende (log. Skala)")
    _hbar_raster(ax)
    ax.legend(loc="lower right", title=None)
    ax.set_title("Warenkorb je 100 Anwesende (Meisterschaft, Top-10-Artikel)")
    _speichern(fig, ordner, "abb_i10_warenkorb.png", "Warenkorb",
               f"Je 100 Anwesende 2025/26: {z(kz['wk_bier_total'])} Bier, {z(kz['wk_soft'])} Süssgetränke, {z(kz['wk_bratwurst'])} Bratwürste.",
               "Warenkorb_Artikel", liste)


def preis_menge(e, kz, ordner, liste):
    r = e["preis_menge"]
    r = r[(r["von"] == "2023/24") & (r["bis"] == "2025/26")].iloc[0]
    teile = [("Artikel-Umsatz je Anwesendem", r["veraenderung_gesamt_pct"]), ("Erlös je Einheit (Preis)", r["preisindex_fisher_pct"]),
             ("Einheiten je Anwesendem (Menge)", r["mengenindex_fisher_pct"]), ("Sortimentswechsel", r["sortimentswechsel_pct"])]
    fig, ax = plt.subplots(figsize=(7.6, 2.9))
    y = np.arange(len(teile))[::-1]
    for yi, (label, wert) in zip(y, teile):
        ax.barh(yi, wert, color=BLAU if yi == y[0] else GRAU, height=0.55)
        ax.text(wert + (0.15 if wert >= 0 else -0.15), yi, pct(wert, 1), va="center", ha="left" if wert >= 0 else "right", fontsize=8.5, color=INK)
    ax.axvline(0, color=INK2, lw=0.8)
    ax.set_yticks(y)
    ax.set_yticklabels([t[0] for t in teile])
    ax.set_xlim(min(-1, min(t[1] for t in teile) - 1.5), max(t[1] for t in teile) + 2.5)
    ax.xaxis.set_major_formatter(_pct_fmt())
    _hbar_raster(ax)
    ax.set_title("Preis oder Menge? Zerlegung 2023/24 → 2025/26 (Artikel, brutto)")
    _speichern(fig, ordner, "abb_i11_preis_menge.png", "Preis- und Mengeneffekt",
               "Das Wachstum kommt aus Menge und neuem Sortiment, nicht aus höheren Preisen je Einheit.", "Preis_Menge", liste)


def alkohol_validierung(e, kz, ordner, liste):
    a = e["alkohol_je_spiel"]
    a = a[a["proxy_gueltig"] & (a["wettbewerb"] == "SL")]
    v = e["alkohol_validierung"].dropna(subset=["artikel_alkoholanteil_brutto"])
    fig, ax = plt.subplots(figsize=(7.6, 3.8))
    saisons = sorted(a["saison"].unique())
    pos = {s: i for i, s in enumerate(saisons)}
    jitter = np.random.default_rng(1879).uniform(-0.18, 0.18, len(a))
    ax.scatter(a["saison"].map(pos) + jitter, a["s_brutto"] * 100, s=14, color=GRAU_HELL, label="einzelne Spiele (Proxy)", zorder=2)
    ax.scatter(v["saison"].map(pos) - 0.06, v["proxy_s_brutto"] * 100, s=60, color=BLAU, label="Proxy, Saisonmittel", zorder=3,
               edgecolor=FLAECHE, lw=1.5)
    ax.scatter(v["saison"].map(pos) + 0.06, v["artikel_alkoholanteil_brutto"] * 100, s=60, color=ORANGE, marker="D",
               label="Artikelauswertung (brutto)", zorder=3, edgecolor=FLAECHE, lw=1.5)
    ax.set_xticks(range(len(saisons)))
    ax.set_xticklabels(saisons)
    ax.yaxis.set_major_locator(mtick.MultipleLocator(5))
    ax.yaxis.set_major_formatter(mtick.PercentFormatter(100, decimals=0))
    ax.set_ylabel("Alkoholanteil am Umsatz (brutto)")
    ax.legend(loc="upper right", fontsize=8)
    ax.set_title("Neuer Spiel-Indikator: Alkoholanteil aus dem MwSt-Mix der Kassen – validiert")
    _speichern(fig, ordner, "abb_i12_alkohol_validierung.png", "Alkohol-Proxy validiert",
               f"Saisonmittel des Proxys und Artikelauswertung liegen höchstens {kz['alk_val_maxdiff']:.1f} Pp. auseinander.",
               "Alkohol_Validierung", liste)


def alkohol_kontext(e, kz, ordner, liste):
    m = e["alkohol_effekt_matrix"]
    vars_ = ["Abendspiel (Anpfiff ab 20 Uhr)", "Werktag (Mo–Fr) statt Wochenende", "Temperatur bei Anpfiff", "Top-Gegner (FCB, YB, FCZ)"]
    namen = {"Abendspiel (Anpfiff ab 20 Uhr)": "Abendspiel (ab 20 Uhr)", "Werktag (Mo–Fr) statt Wochenende": "Werktag statt Wochenende",
             "Temperatur bei Anpfiff": "+5 °C bei Anpfiff", "Top-Gegner (FCB, YB, FCZ)": "Top-Gegner (FCB/YB/FCZ)"}
    reihen = [("KF Alkohol (exkl. MwSt)", "KF Alkohol", BLAU), ("KF Food & alkoholfrei (exkl. MwSt)", "KF Food & alkoholfrei", ORANGE)]
    fig, ax = plt.subplots(figsize=(8.0, 3.9))
    y = np.arange(len(vars_))[::-1]
    for i, (ziel, label, farbe) in enumerate(reihen):
        x = m[m["zielgroesse"] == ziel].set_index("variable").reindex(vars_)
        off = 0.16 if i == 0 else -0.16
        ax.barh(y + off, x["effekt"], height=0.3, color=farbe, label=label)
        ax.errorbar(x["effekt"], y + off, xerr=[x["effekt"] - x["ki95_unten"], x["ki95_oben"] - x["effekt"]], fmt="none",
                    ecolor=INK2, elinewidth=0.8, capsize=2)
    ax.axvline(0, color=INK2, lw=0.8)
    ax.set_yticks(y)
    ax.set_yticklabels([namen[v] for v in vars_])
    ax.xaxis.set_major_formatter(_pct_fmt())
    _hbar_raster(ax)
    ax.legend(loc="lower right")
    ax.set_title("Was Alkohol- und Food-Umsatz je Anwesendem bewegt (Effekt mit 95 %-Intervall, 2023/24–2026/27)")
    _speichern(fig, ordner, "abb_i13_alkohol_kontext.png", "Alkohol vs. Food nach Kontext",
               f"Abends steigt der Alkohol-KF um {pct(kz['alk_abend_kf'], 0)}, Food & alkoholfrei sinkt um {pct(kz['food_abend_kf'], 0)}.",
               "Alkohol_Effekt_Matrix", liste)


def mobiler_verkauf(e, kz, ordner, liste):
    m = e["mobiler_verkauf_effekt"]
    m = m[(m["zielgroesse"] == "Kundenfranken exkl. MwSt") & ~m["gruppe"].str.startswith("Differenz")].set_index("gruppe")
    reihen = ["im Einsatz", "keine Angabe", "ganz/teilweise nicht im Einsatz"]
    m = m.reindex(reihen)
    fig, ax = plt.subplots(figsize=(7.6, 2.8))
    y = np.arange(len(m))[::-1]
    farben = [BLAU, GRAU_HELL, ORANGE]
    ax.barh(y, m["abweichung_von_erwartung_pct"], color=farben, height=0.55)
    ax.errorbar(m["abweichung_von_erwartung_pct"], y, xerr=[m["abweichung_von_erwartung_pct"] - m["ki90_unten"],
                                                            m["ki90_oben"] - m["abweichung_von_erwartung_pct"]],
                fmt="none", ecolor=INK2, elinewidth=0.8, capsize=2)
    for yi, (g, r) in zip(y, m.iterrows()):
        ax.text(max(r["ki90_oben"], 0) + 0.3, yi, f"{pct(r['abweichung_von_erwartung_pct'])} · {int(r['spiele'])} Spiele", va="center",
                fontsize=8, color=INK)
    ax.axvline(0, color=INK2, lw=0.8)
    ax.set_yticks(y)
    ax.set_yticklabels(["Runner/Bauchläden im Einsatz", "keine Angabe", "ganz/teilweise nicht im Einsatz"])
    ax.set_xlim(m["ki90_unten"].min() - 1, m["ki90_oben"].max() + 6)
    ax.xaxis.set_major_locator(mtick.MultipleLocator(2))
    ax.xaxis.set_major_formatter(_pct_fmt())
    _hbar_raster(ax)
    ax.set_title("KF gegenüber Kontexterwartung nach mobilem Verkauf (90 %-Intervall)")
    _speichern(fig, ordner, "abb_i14_mobiler_verkauf.png", "Mobiler Verkauf",
               f"Differenz {pct(kz['mob_diff'])} zwischen Spielen ohne und mit mobilem Verkauf – an der Nachweisgrenze.",
               "Mobiler_Verkauf_Effekt", liste)


def kiesplatz_wetter(e, kz, ordner, liste):
    k = e["kiesplatz_je_spiel_ideen"].copy()
    for c in ("kies_je_anw", "stadion_je_anw"):
        k[f"{c}_abw"] = (np.log(k[c]) - k.groupby("saison")[c].transform(lambda s: np.log(s).mean())) * 100
    fig, ax = plt.subplots(figsize=(7.6, 4.2))
    for col, label, farbe in (("kies_je_anw_abw", "Kiesplatz", BLAU), ("stadion_je_anw_abw", "Stadion (ohne Kiesplatz)", ORANGE)):
        ax.scatter(k["temp_anpfiff_c"], k[col], s=18, color=farbe, alpha=0.75, label=label, edgecolor=FLAECHE, lw=0.8)
        b = np.polyfit(k["temp_anpfiff_c"], k[col], 1)
        xs = np.linspace(k["temp_anpfiff_c"].min(), k["temp_anpfiff_c"].max(), 20)
        ax.plot(xs, np.polyval(b, xs), color=farbe, lw=2)
    ax.axhline(0, color=GRAU_HELL, lw=0.8)
    unten = -70
    n_aus = int((k[["kies_je_anw_abw", "stadion_je_anw_abw"]] < unten).sum().sum())
    ax.set_ylim(unten, max(50, float(k[["kies_je_anw_abw", "stadion_je_anw_abw"]].max().max()) + 5))
    if n_aus:
        ax.text(k["temp_anpfiff_c"].max(), unten + 3, f"{n_aus} Spiel(e) unter −70 % nicht dargestellt (Linie enthält sie)",
                ha="right", fontsize=7.5, color=INK2)
    ax.yaxis.set_major_formatter(_pct_fmt())
    ax.grid(axis="x", visible=True)
    ax.set_xlabel("Temperatur bei Anpfiff (°C)")
    ax.set_ylabel("Umsatz je Anwesendem vs. Saisonmittel")
    ax.legend(loc="upper left")
    ax.set_title("Wärme hilft vor allem dem Kiesplatz (Meisterschaft 2021/22–2026/27)")
    _speichern(fig, ordner, "abb_i15_kiesplatz_wetter.png", "Kiesplatz und Wetter",
               f"Je +5 °C: Kiesplatz {pct(kz['kies_temp'], 0)}, Stadion {pct(kz['stadion_temp'])} je Anwesendem (mit Kontextkontrollen).",
               "Kiesplatz_Wetter", liste)


def ausreisser(e, kz, res, ordner, liste):
    k = res["diagnosekarte"].dropna(subset=["z_wert_kf_exkl"]).sort_values("datum").copy()
    k["abw"] = (k["beobachtet_kf_exkl"] / k["erwartet_kf_exkl"] - 1) * 100
    k["samstag18"] = (k["wochentag"] == "Samstag") & (k["anpfiff"] == "18:00")
    ueber = k["z_wert_kf_exkl"] > 1.2816
    unter = k["z_wert_kf_exkl"] < -1.2816
    fig, ax = plt.subplots(figsize=(10.5, 3.8))
    x = np.arange(len(k))
    ax.scatter(x[~ueber & ~unter], k.loc[~ueber & ~unter, "abw"], s=16, color=GRAU_HELL, label="im Erwartungsband")
    ax.scatter(x[ueber & k["samstag18"]], k.loc[ueber & k["samstag18"], "abw"], s=40, color=BLAU, label="über Erwartung – Samstag 18:00",
               edgecolor=FLAECHE, lw=1.2, zorder=3)
    ax.scatter(x[ueber & ~k["samstag18"]], k.loc[ueber & ~k["samstag18"], "abw"], s=40, color=AQUA, label="über Erwartung – übrige",
               edgecolor=FLAECHE, lw=1.2, zorder=3)
    ax.scatter(x[unter], k.loc[unter, "abw"], s=40, color=ORANGE, label="unter Erwartung", edgecolor=FLAECHE, lw=1.2, zorder=3)
    ax.axhline(0, color=INK2, lw=0.8)
    grenzen = np.where(k["saison"].ne(k["saison"].shift()))[0]
    oben = k["abw"].max() + 6
    ax.set_ylim(k["abw"].min() - 3, oben + 2)
    for g in grenzen:
        ax.axvline(g - 0.5, color=RASTER, lw=0.8)
        ax.text(g + 0.3, oben, k["saison"].iloc[g], fontsize=8, color=INK2, va="center")
    ax.set_xticks([])
    ax.set_ylabel("KF beobachtet vs. erwartet")
    ax.yaxis.set_major_formatter(_pct_fmt())
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.04), ncol=4, fontsize=8)
    ax.set_title("Positive Ausreisser beim Kundenfranken – viele davon Samstag 18:00")
    _speichern(fig, ordner, "abb_i16_ausreisser.png", "Erfolgsmuster",
               f"{kz['aus_kf_samstag']} von {kz['aus_kf_n']} Spielen über der Erwartung waren Samstagsspiele.", "Ausreisser_Positiv", liste)


def randfelder(e, kz, ordner, liste):
    """KF je Anlass-Kategorie ohne Frauen und Länderspiele (D-016/D-036)."""
    rk = e["randfelder_kategorien"]
    sl = rk[(rk["kategorie"] == "Herren Meisterschaft") & (rk["saison"] == "2025/26")]
    werte = [("Herren Meisterschaft 2025/26", sl["umsatz_inkl"].sum() / sl["public_anwesende"].sum(), GRAU)]
    for kat in ("Testspiele", "U21", "Fremdclubs"):
        g = rk[rk["kategorie"] == kat]
        if len(g) and g["public_anwesende"].sum() > 0:
            werte.append((f"{kat} (2022/23–)", g["umsatz_inkl"].sum() / g["public_anwesende"].sum(), BLAU))
    fig, ax = plt.subplots(figsize=(7.6, 0.6 + 0.55 * len(werte)))
    y = np.arange(len(werte))[::-1]
    for yi, (label, wert, farbe) in zip(y, werte):
        ax.barh(yi, wert, color=farbe, height=0.55)
        ax.text(wert + 0.2, yi, f"CHF {wert:.2f}", va="center", fontsize=8.5, color=INK)
    ax.set_yticks(y)
    ax.set_yticklabels([w[0] for w in werte])
    ax.set_xlim(0, max(w[1] for w in werte) * 1.25)
    ax.xaxis.set_major_formatter(mtick.FuncFormatter(lambda v, _: f"{v:.0f}"))
    ax.set_xlabel("Kundenfranken inkl. MwSt in CHF (Summe Umsatz / Summe Public-Anwesende)")
    _hbar_raster(ax)
    ax.set_title("Kundenfranken an weiteren Anlässen (ausserhalb Kernscope, explorativ)")
    _speichern(fig, ordner, "abb_i17_randfelder.png", "Weitere Anlässe",
               "Test- und U21-Spiele im Vergleich zur Herren-Meisterschaft; Frauen und Länderspiele ausgeklammert (D-016).",
               "Randfelder_Kategorien", liste)


def erstelle(e: dict, kz: dict, res: dict, ordner: Path) -> pd.DataFrame:
    ordner.mkdir(parents=True, exist_ok=True)
    liste: list = []
    for f in (faustwerte, leere_plaetze, tribuenen, noshow_segmente, spieltypen, fruehindikator, verweilzeit, einlass, kf_entwicklung,
              warenkorb, preis_menge, alkohol_validierung, alkohol_kontext, mobiler_verkauf, kiesplatz_wetter, randfelder):
        f(e, kz, ordner, liste)
    ausreisser(e, kz, res, ordner, liste)
    return pd.DataFrame(liste)

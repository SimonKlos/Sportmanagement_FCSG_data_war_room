"""Rechengrundlage für Ideen: Saisonbasis, Hebel-Arithmetik (Simon §12) und Korrektur von Retos Faustwerten.

Alle CHF-Werte sind Catering-Umsatz exkl. MwSt (Caterer-Umsatz, nicht Club-Ertrag) und **isolierte Rechenbeispiele je
Hebel** – keine Potenzialschätzung. Hebel überlappen (KF = Bons/Anwesende × Ø Bon) und werden nie addiert.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from .. import config

REFERENZ_SAISON = "2025/26"
MITTEL_SAISONS = ("2023/24", "2024/25", "2025/26")
MITTEL_LABEL = "Ø 2023/24–2025/26"

# Hebel nach Simons Arbeitsauftrag §12 (Rechenlogiken Umsatzebene). Einheit der Veränderung und Formel als Text,
# damit Python, Excel-Rechner und Dossier dieselbe Definition verwenden.
HEBEL = {
    "noshow_pp": ("−1 Prozentpunkt No-Show", "Pp. weniger No-Show",
                  "Δ Pp./100 × Ø SOLL je Spiel × KF exkl. × φ"),
    "zusatz_anwesende": ("+1'000 Anwesende je Spiel", "zusätzliche Anwesende je Spiel",
                         "Anwesende × KF exkl. × φ"),
    "bons_pro_anwesende": ("+0.1 Bons je Anwesendem", "zusätzliche Bons je Anwesendem",
                           "Δ Bons/Anw. × Ø Public-Anwesende je Spiel × Ø Bon exkl."),
    "frequenz_pct": ("+1 % Kauffrequenz (Ø Bon gleich)", "% mehr Bons je Anwesendem",
                     "Δ %/100 × Ø Umsatz exkl. je Spiel"),
    "bon_chf": ("+CHF 1 Ø Bon (Frequenz gleich)", "CHF höherer Ø Bon",
                "Δ CHF × Ø Bons je Spiel"),
    "kf_chf": ("+CHF 1 Kundenfranken", "CHF höherer KF",
               "Δ CHF × Ø Public-Anwesende je Spiel"),
}
STANDARD_VERAENDERUNG = {"noshow_pp": 1.0, "zusatz_anwesende": 1000.0, "bons_pro_anwesende": 0.1, "frequenz_pct": 1.0,
                         "bon_chf": 1.0, "kf_chf": 1.0}
MIT_PHI = ("noshow_pp", "zusatz_anwesende")


def _sl_gespielt(k: pd.DataFrame) -> pd.DataFrame:
    return k[(k["wettbewerb"] == "SL") & (k["spielstatus"] == "gespielt")]


def _summen(g: pd.DataFrame) -> dict:
    a = g.dropna(subset=["soll", "ist"])
    c = g.dropna(subset=["public_netto", "umsatz_exkl"])
    b = c.dropna(subset=["transaktionen"])
    ticket = a[a["soll_ticketbasiert"].fillna(False).astype(bool)]
    ausv = a[a["ausverkauft"].fillna(False).astype(bool)]
    return {
        "spiele": len(g), "spiele_mit_bons": len(b), "spiele_ausverkauft": len(ausv),
        "soll_summe": a["soll"].sum(), "ist_summe": a["ist"].sum(), "noshow_summe": (a["soll"] - a["ist"]).sum(),
        "noshow_summe_ticketbasiert": (ticket["soll"] - ticket["ist"]).sum(), "spiele_ticketbasiert": len(ticket),
        "noshow_summe_ausverkauft": (ausv["soll"] - ausv["ist"]).sum(),
        "public_netto_summe": c["public_netto"].sum(), "umsatz_exkl": c["umsatz_exkl"].sum(),
        "umsatz_inkl": c["umsatz_inkl"].sum(), "bons_summe": b["transaktionen"].sum(),
        "public_netto_summe_mit_bons": b["public_netto"].sum(), "umsatz_exkl_mit_bons": b["umsatz_exkl"].sum(),
    }


def _kennzahlen(s: dict, divisor: float = 1.0) -> dict:
    """Leitet Mittelwerte und Quoten aus Summen ab (divisor > 1 für Saison-Äquivalente über mehrere Saisons)."""
    out = {k_: v / divisor for k_, v in s.items()}
    sp, spb = s["spiele"], s["spiele_mit_bons"]
    out.update({
        "soll_mittel": s["soll_summe"] / sp if sp else np.nan,
        "ist_mittel": s["ist_summe"] / sp if sp else np.nan,
        "public_netto_mittel": s["public_netto_summe"] / sp if sp else np.nan,
        "umsatz_exkl_mittel": s["umsatz_exkl"] / sp if sp else np.nan,
        "bons_mittel": s["bons_summe"] / spb if spb else np.nan,
        "noshow_quote": s["noshow_summe"] / s["soll_summe"] if s["soll_summe"] else np.nan,
        "noshow_mittel": s["noshow_summe"] / sp if sp else np.nan,
        "kf_exkl": s["umsatz_exkl"] / s["public_netto_summe"] if s["public_netto_summe"] else np.nan,
        "kf_inkl": s["umsatz_inkl"] / s["public_netto_summe"] if s["public_netto_summe"] else np.nan,
        "bons_pro_anwesende": s["bons_summe"] / s["public_netto_summe_mit_bons"] if spb else np.nan,
        "bon_exkl": s["umsatz_exkl_mit_bons"] / s["bons_summe"] if spb else np.nan,
    })
    return out


def saison_basis(k: pd.DataFrame) -> pd.DataFrame:
    """Je Meisterschaftssaison Summen (Summe/Summe) und Mittelwerte je Spiel; dazu das Saison-Äquivalent 23/24–25/26."""
    d = _sl_gespielt(k)
    rows = []
    for s, g in d.groupby("saison"):
        rows.append({"basis": s, **_kennzahlen(_summen(g))})
    drei = d[d["saison"].isin(MITTEL_SAISONS)]
    if drei["saison"].nunique() == len(MITTEL_SAISONS):
        summe = _summen(drei)
        row = _kennzahlen(summe, divisor=len(MITTEL_SAISONS))
        rows.append({"basis": MITTEL_LABEL, **row})
    out = pd.DataFrame(rows)
    out["hinweis"] = np.where(out["basis"] == "2026/27", "erst wenige Spiele (Sommer/Frühherbst) – nicht als Basis verwenden",
                              np.where(out["basis"] == "2021/22", "COVID-geprägt (Zertifikatspflicht)", ""))
    return out


def basis_zeile(basis: pd.DataFrame, name: str = REFERENZ_SAISON) -> dict:
    return basis.set_index("basis").loc[name].to_dict()


def hebel_szenario(b: dict, hebel: str, veraenderung: float | None = None, phi: float = 1.0,
                   anteil_spiele: float = 1.0) -> dict:
    """Isolierter Umsatzeffekt (CHF exkl. MwSt) eines Hebels je Spiel und je Saison.

    ``b``: Basiszeile aus saison_basis(). ``phi``: Konsum eines zusätzlichen Anwesenden relativ zum Durchschnitt
    (nur für Anwesenheitshebel). ``anteil_spiele``: Anteil der Saisonspiele, für die der Hebel gilt.
    Rechenhilfe für Phase 2 – kein realisierbares Potenzial; Hebel nicht addieren.
    """
    if hebel not in HEBEL:
        raise ValueError(f"Unbekannter Hebel: {hebel}")
    v = STANDARD_VERAENDERUNG[hebel] if veraenderung is None else veraenderung
    if hebel == "noshow_pp":
        menge = v / 100 * b["soll_mittel"]
        chf_spiel = menge * b["kf_exkl"] * phi
    elif hebel == "zusatz_anwesende":
        menge = v
        chf_spiel = v * b["kf_exkl"] * phi
    elif hebel == "bons_pro_anwesende":
        menge = v * b["public_netto_mittel"]
        chf_spiel = menge * b["bon_exkl"]
    elif hebel == "frequenz_pct":
        menge = np.nan
        chf_spiel = v / 100 * b["umsatz_exkl_mittel"]
    elif hebel == "bon_chf":
        menge = np.nan
        chf_spiel = v * b["bons_mittel"]
    else:  # kf_chf
        menge = np.nan
        chf_spiel = v * b["public_netto_mittel"]
    spiele = b["spiele"] * anteil_spiele
    return {"hebel": hebel, "veraenderung": v, "phi": phi if hebel in MIT_PHI else np.nan, "anteil_spiele": anteil_spiele,
            "zusatz_menge_je_spiel": menge, "chf_pro_spiel": chf_spiel, "chf_pro_saison": chf_spiel * spiele,
            "spiele": spiele}


def faustwerte(basis: pd.DataFrame) -> pd.DataFrame:
    """Standard-Hebel für Referenzsaison und Saison-Äquivalent, Anwesenheitshebel mit φ-Szenarien."""
    rows = []
    for name in (REFERENZ_SAISON, MITTEL_LABEL):
        if name not in set(basis["basis"]):
            continue
        b = basis_zeile(basis, name)
        for hebel, (titel, einheit, formel) in HEBEL.items():
            for phi in (config.IDEEN_PHI if hebel in MIT_PHI else (1.0,)):
                r = hebel_szenario(b, hebel, phi=phi)
                rows.append({"basis": name, "hebel": titel, "hebel_code": hebel, "veraenderung": r["veraenderung"],
                             "einheit": einheit, "phi": r["phi"], "zusatz_menge_je_spiel": r["zusatz_menge_je_spiel"],
                             "chf_pro_spiel": r["chf_pro_spiel"], "chf_pro_saison": r["chf_pro_saison"],
                             "spiele": r["spiele"], "formel": formel})
    out = pd.DataFrame(rows)
    out["lesart"] = ("Isolierter Rechenwert je Hebel (Catering-Umsatz exkl. MwSt, Caterer-Umsatz). Hebel überlappen und werden "
                     "nicht addiert; realisierbare Anteile sind Phase-2-Annahmen.")
    return out


def reto_vergleich(basis: pd.DataFrame) -> pd.DataFrame:
    """Retos Faustwerte (Ideenphase, 05.10.2026, Annahme A1: 18'000 Anwesende) gegenüber den Daten 2025/26."""
    b = basis_zeile(basis, REFERENZ_SAISON)
    noshow = hebel_szenario(b, "noshow_pp", phi=1.0)
    rows = [
        ("Anwesende je Spiel (A1)", 18000, b["public_netto_mittel"],
         "Daten: Ø Public-Anwesende (KF-Nenner) 25/26; Ø IST inkl. VIP/Gäste: " + f"{b['ist_mittel']:,.0f}".replace(",", "'")),
        ("Verkaufte Tickets je Spiel (A1: 18'000 / 0.83)", 21700, b["soll_mittel"], "Daten: Ø SOLL 25/26"),
        ("Catering-Umsatz Meisterschaft je Saison (CHF)", 18000 * 14.50 * 19, b["umsatz_exkl"],
         "Daten: Umsatz exkl. MwSt 25/26 (19 Spiele)"),
        ("+CHF 1 Kundenfranken je Saison (CHF)", 342000, hebel_szenario(b, "kf_chf")["chf_pro_saison"], "Σ Public-Anwesende"),
        ("1 Pp. No-Show: zusätzliche Anwesende je Spiel", 217, noshow["zusatz_menge_je_spiel"], "1 % des Ø SOLL"),
        ("1 Pp. No-Show: CHF je Spiel (φ = 1)", 3145, noshow["chf_pro_spiel"], "× KF exkl. 25/26"),
        ("1 Pp. No-Show: CHF je Saison (φ = 1)", 60000, noshow["chf_pro_saison"], "19 Spiele"),
        ("+1 % Kauffrequenz je Saison (CHF)", 49600, hebel_szenario(b, "frequenz_pct")["chf_pro_saison"], "1 % des Umsatzes exkl."),
        ("+CHF 0.50 Kundenfranken je Saison (CHF)", 171000, hebel_szenario(b, "kf_chf", 0.5)["chf_pro_saison"], ""),
    ]
    out = pd.DataFrame(rows, columns=["kennzahl", "reto_annahme", "daten_2025_26", "erlaeuterung"])
    out["faktor_daten_zu_reto"] = out["daten_2025_26"] / out["reto_annahme"]
    out["lesart"] = ("Retos Werte beruhen auf 18'000 Anwesenden je Spiel; tatsächlich sind es rund 13'800 Public-Anwesende. "
                     "Sizings aus dem Ideenpapier sind entsprechend zu senken.")
    return out


def noshow_kosten(basis: pd.DataFrame, k: pd.DataFrame) -> pd.DataFrame:
    """Was kostet ein leerer, bezahlter Platz? Getrennt nach ausverkauften und übrigen Spielen (Referenzsaison und Ø)."""
    d = _sl_gespielt(k).dropna(subset=["soll", "ist"])
    rows = []
    for name, saisons in ((REFERENZ_SAISON, (REFERENZ_SAISON,)), (MITTEL_LABEL, MITTEL_SAISONS)):
        g = d[d["saison"].isin(saisons)]
        if g.empty:
            continue
        b = basis_zeile(basis, name)
        n = len(saisons)
        for ausv, x in g.groupby(g["ausverkauft"].fillna(False).astype(bool)):
            leer = (x["soll"] - x["ist"]).sum() / n
            rows.append({"basis": name, "spieltyp": "ausverkauft" if ausv else "nicht ausverkauft",
                         "spiele_je_saison": len(x) / n, "leere_bezahlte_plaetze_je_saison": leer,
                         "leere_plaetze_je_spiel": leer / (len(x) / n),
                         "noshow_quote": 1 - x["ist"].sum() / x["soll"].sum(),
                         "soll_ticketbasiert_anteil": x["soll_ticketbasiert"].fillna(False).astype(bool).mean(),
                         "konsum_referenz_je_platz_phi_0_6": b["kf_exkl"] * 0.6,
                         "konsum_referenz_je_platz_phi_1_0": b["kf_exkl"]})
    out = pd.DataFrame(rows)
    out["lesart"] = ("Ticketerlös ist bereits verbucht. Ein leerer Platz kostet Konsum (φ × KF) und Stimmung. «Aktivieren» "
                     "(Inhaber kommt) wirkt in jedem Spiel; «Weiterverkaufen» (Zweitmarkt) bringt nur dann zusätzliche Anwesende, "
                     "wenn die Nachfrage das freie Angebot übersteigt – also v.a. bei ausverkauften Spielen/Sektoren. Bei Kapazitäts-"
                     "SOLL (ausverkauft) ist die Zahl der leeren Plätze nicht ticketbasiert.")
    return out


def rechne(res: dict) -> dict[str, pd.DataFrame]:
    k = res["spiel_kpi"]
    basis = saison_basis(k)
    return {"basis_saison": basis, "faustwerte": faustwerte(basis), "reto_faustwerte": reto_vergleich(basis),
            "noshow_kosten": noshow_kosten(basis, k)}

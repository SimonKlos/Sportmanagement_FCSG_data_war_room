"""Qualitätssicherung der Ideen-Grundlage: Datenschutz, Leitplanken, Validierungen und Unverändertheit von Phase 1."""
from __future__ import annotations

import hashlib
import re
from pathlib import Path

import pandas as pd

from .. import config
from ..qa import verbotene_spalten
from .chancen import LEITPLANKEN_SCHLUESSEL

VERBOTENE_ZEILEN = re.compile(r"(gesamt|total|summe)\s*(potenzial|potential)|potenzial\s*(gesamt|total|summe)", re.I)
KLEINZELLEN = {"einzel_noshow_segmente": "tickets", "preis_einzel_tribuene": "einzeltickets", "zweitmarkt_preis": "zweitmarkt_tickets"}


def fingerabdruck(res: dict) -> dict[str, str]:
    """MD5 je Phase-1-Tabelle (Inhalt), um nachzuweisen, dass die Ideen-Stufe nichts verändert."""
    out = {}
    for k, v in res.items():
        if isinstance(v, pd.DataFrame):
            try:
                h = pd.util.hash_pandas_object(v.astype(str), index=True).values
                out[k] = hashlib.md5(h.tobytes()).hexdigest()
            except TypeError:
                out[k] = hashlib.md5(v.to_csv().encode()).hexdigest()
    return out


def pruefe(e: dict[str, pd.DataFrame], felder: list, res: dict, fp_vorher: dict) -> pd.DataFrame:
    tests = []

    def t(name, ok, detail=""):
        tests.append({"test": name, "bestanden": bool(ok), "detail": detail})

    fp_nachher = fingerabdruck(res)
    geaendert = [k for k in fp_vorher if fp_vorher[k] != fp_nachher.get(k)]
    t("Phase-1-Ergebnisse durch die Ideen-Stufe unverändert", not geaendert, ", ".join(geaendert) or f"{len(fp_vorher)} Tabellen geprüft")

    treffer = [f"{n}.{c}" for n, df in e.items() if isinstance(df, pd.DataFrame) for c in df.columns
               if str(c).lower() in verbotene_spalten()]
    t("Datenschutz: keine Personen- oder ID-Spalten in den Ideen-Tabellen", not treffer, ", ".join(treffer) or "keine")

    klein = []
    for name, col in KLEINZELLEN.items():
        if name in e and col in e[name] and len(e[name]):
            n_klein = int((e[name][col] < config.MIN_ZELLE).sum())
            if n_klein:
                klein.append(f"{name}: {n_klein}")
    tj = e.get("tribuene_2627_je_spiel")
    t("Datenschutz: Segmente unter 10 Tickets unterdrückt", not klein, ", ".join(klein) or "alle Segmente ≥ 10 Tickets")

    zeilen = [f"{n}" for n, df in e.items() if isinstance(df, pd.DataFrame)
              for v in df.select_dtypes(exclude="number").to_numpy().ravel() if VERBOTENE_ZEILEN.search(str(v))]
    t("Keine Summen- oder Gesamtpotenzial-Zeile", not zeilen, ", ".join(sorted(set(zeilen))) or "keine")

    fehlend = [f"{f.nr}: {k}" for f in felder for k in LEITPLANKEN_SCHLUESSEL if not f.leitplanken.get(k)]
    verletzt = [f"{f.nr}" for f in felder for v in f.leitplanken.values() if "verletzt" in v.lower()]
    t("Leitplanken-Pflichtfelder in allen Chancenfeldern ausgefüllt, keine Verletzung", not fehlend and not verletzt,
      "; ".join(fehlend + verletzt) or f"{len(felder)} Chancenfelder")
    t("Jedes Chancenfeld hat 2–5 Leitfragen und ein Pilot-Messdesign",
      all(2 <= len(f.leitfragen) <= 5 and f.pilot_messung for f in felder), "")

    av = e["alkohol_validierung"].dropna(subset=["differenz_pp"])
    t("Alkohol-Proxy: Saisonmittel ±2 Pp. zur Artikelauswertung", (av["differenz_pp"].abs() <= 2).all(),
      ", ".join(f"{s}: {d:+.2f} Pp." for s, d in zip(av["saison"], av["differenz_pp"])))
    r_k = e["alkohol_validierung"]["r_innerhalb_saison_mit_kiesplatz"].iloc[0]
    t("Alkohol-Proxy: Korrelation mit Kiesplatz-Normalsatzanteil innerhalb der Saison > 0.3", r_k > 0.3, f"r = {r_k:.2f}")

    zs = e["zweitmarkt_saison"]
    t("Zweitmarkt: CSV-Tarife = Spalte Zweitmarkt der Historie (jedes Spiel)", zs["csv_gleich_historie"].all(),
      ", ".join(f"{s}: {int(n)}" for s, n in zip(zs["saison"], zs["zweitmarkt"])))

    tr = e["tribuene_2627"].set_index("tribuene")["einzel_anwesenheit_uefa"]
    werte = tr.reindex(["B", "C", "D"])
    t("Tribünen-Kalibrierung: UEFA-Scans je Einzelticket in B/C/D zwischen 0.93 und 1.02", werte.between(0.93, 1.02).all(),
      ", ".join(f"{k}: {v:.3f}" for k, v in werte.items()))

    b = e["basis_saison"].set_index("basis")
    s = res["saison_kpi"]
    sl = s[s["wettbewerbe"] == "SL"].set_index("saison")
    t("Basis = Phase-1-Saisonwerte (Σ Public-Anwesende, KF exkl.)",
      all(abs(b.loc[x, "public_netto_summe"] - sl.loc[x, "public_netto_summe"]) < 1e-6 and abs(b.loc[x, "kf_exkl"] - sl.loc[x, "kf_exkl"]) < 1e-9
          for x in sl.index if x in b.index), f"{len(sl)} Saisons")

    v = e["fruehindikator_vorhersagen"]
    t("Frühindikator ohne Blick in die Zukunft (Training endet vor jedem Testspiel)", (v["training_bis"] < v["datum"]).all(),
      f"{len(v)} Vorhersagen")
    rb = e["spieltypen_robustheit"]
    t("Clustering mit Stabilitätsangabe (Bootstrap-Jaccard)", rb["min_bootstrap_jaccard"].notna().all() and "stabil" in rb, "")

    pm = e["preis_menge"]
    t("Fisher-Zerlegung: Preisindex × Mengenindex = Wertverhältnis", pm["identitaet_pruefung"].abs().max() < 1e-9, "")

    if tj is not None:
        sl_t = tj[tj["wettbewerb"] == "SL"]
        t("Tribünen 26/27: Zweitmarkt nur einmal gezählt (Plätze = Abos + Einzel − Zweitmarkt)",
          (sl_t["plaetze_vergeben"] == sl_t["abos_bis_anpfiff"] + sl_t["einzeltickets"] - sl_t["davon_zweitmarkt"]).all(), "")
    return pd.DataFrame(tests)


def pruefe_dateien(html_pfad: Path, md_pfad: Path) -> pd.DataFrame:
    tests = []
    html = html_pfad.read_text(encoding="utf-8")
    extern = re.findall(r"""(?:src|href)\s*=\s*["'](https?:)""", html)
    tests.append({"test": "HTML offline (keine externen Quellen, Grafiken eingebettet)", "bestanden": not extern,
                  "detail": f"{len(re.findall(r'data:image/png;base64', html))} eingebettete Grafiken"})
    md = md_pfad.read_text(encoding="utf-8")
    fehler = 0
    block = []
    for zeile in md.splitlines() + [""]:
        if zeile.startswith("|"):
            block.append(zeile.count("|"))
        else:
            if block and len(set(block)) > 1:
                fehler += 1
            block = []
    tests.append({"test": "Markdown-Tabellen mit konsistenter Spaltenzahl", "bestanden": fehler == 0, "detail": f"{fehler} fehlerhafte Tabellen"})
    return pd.DataFrame(tests)

"""Spielrechner v2 (D-047): erzeugt eine einzelne HTML-Datei aus den Run-4-Tabellen.

    python spielrechner/build.py --run4 "<Run-4-Ordner>" --mart "<mart_match.csv>" --kontext "<Spielkontext_Tabelle_FCSG_5.xlsx>" \
        --ausgabe FCSG_Spielrechner.html
    python spielrechner/build.py --testdaten --ausgabe Spielrechner_TEST.html   # künstliche, markierte Testdaten

Eingaben: Run-4-Tabellen `koeffizienten.csv` und `erwartung_je_spiel.csv`, `mart_match.csv` (Gegner, SOLL, VIP je Spiel),
die Spielkontext-Tabelle v5 (Blätter «Ferien» = Schulferien Stadt SG, «Paralellevent») und der öffentliche
MeteoSchweiz-Stundencache `external/meteoschweiz_stg_stuendlich.csv` (Normalwerte für Spiele ohne Prognose).

Die Seite holt im Browser selbst: Wetterprognose (Open-Meteo, austauschbar) und Schulferien Kanton SG (OpenHolidays)
als Rückfallebene. Übertragen werden nur Koordinaten und Datumsbereiche, nie Clubzahlen.
Die Ausgabe mit echten Werten enthält Clubzahlen je Spiel (aggregiert) und ist vertraulich (D-047, .gitignore).
"""
from __future__ import annotations

import argparse
import base64
import json
import sys
from datetime import date, datetime
from pathlib import Path

import numpy as np
import pandas as pd

HIER = Path(__file__).resolve().parent
KERN = HIER.parent
sys.path.insert(0, str(KERN))

from fcsg import config  # noqa: E402
from fcsg.analysis.anstoss_slot import REFERENZ_SLOT, SLOTS  # noqa: E402

WERKTAGE = ("Montag", "Dienstag", "Mittwoch", "Donnerstag", "Freitag")
ZIELE = [
    {"code": "anwesenheitsquote", "label": "Anwesenheitsquote (IST/SOLL)", "kurz": "Anwesenheit", "prozent": True},
    {"code": "kf_exkl", "label": "Kundenfranken exkl. MwSt", "kurz": "KF", "prozent": False},
    {"code": "bons_pro_anwesende", "label": "Bons je Public-Anwesendem", "kurz": "Bons/Kopf", "prozent": False},
    {"code": "bon_exkl", "label": "Ø Bon exkl. MwSt", "kurz": "Ø Bon", "prozent": False},
]
# Namensvarianten im Spielplan → Top-Gegner (config.TOP_GEGNER: Basel, Young Boys, Zurich)
TOP_GEGNER_MUSTER = ["basel", "young boys", "bsc yb", "yb", "zürich", "zurich", "fcz"]
# MeteoSchweiz-Station St. Gallen (STG): Basis des Modells (Temperatur Anpfiffstunde, Regen 2 h vor Anpfiff)
STATION = {"name": "St. Gallen (MeteoSchweiz STG)", "lat": 47.4253, "lon": 9.3985, "hoehe_m": 776}

LESEHILFE = """
<h3>Wozu?</h3>
<p>Der Spielrechner zeigt, was ein Heimspiel unter seinen Bedingungen erwarten lässt: vor dem Spiel für die Planung von Personal
und Ware, nach dem Spiel als fairer Vergleich. Der Kontext (Anstoss, Gegner, Wetter, Ferien) ist für den Club extern und wird
herausgerechnet.</p>
<h3>So entsteht die Erwartung</h3>
<p>Saisonniveau × Anstoss-Slot × Top-Gegner × Temperatur × Regen bei Anreise × Schulferien, geschätzt aus den
Meisterschaftsspielen ab 2022/23 (Run 4). Der Kontext erklärt rund 82 % der Schwankung des Kundenfrankens zwischen Spielen
derselben Saison. Das Band zeigt die typische Streuung vergleichbarer Spiele (80 %), keine Garantie.</p>
<h3>Wetter</h3>
<p><b>Prognose</b> rund 16 Tage im Voraus, danach <b>Normalwert</b> (Mittel der MeteoSchweiz-Messungen in St. Gallen
2018–2026 für Monat und Uhrzeit; Regen als Wahrscheinlichkeit). Nach dem Spiel ersetzt der Abruf die Prognose durch das
tatsächliche Wetter, damit der Vergleich fair ist.</p>
<h3>Neue Saison</h3>
<p>Für eine Saison ohne eigenen Modellwert startet der Rechner mit dem Niveau der letzten vollen Saison. Mit jedem
eingetragenen IST-Spiel lernt er das neue Niveau (gedämpft, damit ein einzelnes Spiel nicht alles verschiebt).</p>
<h3>Grenzen</h3>
<p>Zusammenhänge, keine Kausalnachweise. Modell aus Meisterschaftsspielen; Cup und Europacup nur grob. Parallelanlässe,
TV und Tabellenstand sind nicht im Modell und werden nur als Hinweis gezeigt. Umsatz = Public-Anwesende × Kundenfranken
(exkl. MwSt), Catering-Systemumsatz, nicht Cluberlös. Abweichungen sind Prüfhinweise, kein entgangener Umsatz.</p>
<h3>Datenschutz und Quellen</h3>
<p>Alle Clubzahlen bleiben in dieser Datei und im Browser. Für Wetter und Ferien werden nur Koordinaten bzw. Datumsbereiche
an die Anbieter gesendet. Wetter: Open-Meteo (CC BY 4.0; kostenlose Nutzung nur nicht-kommerziell, für den Betrieb beim
FCSG Abo oder Umstellung auf MeteoSchweiz Open Data klären). Normalwerte: Quelle MeteoSchweiz. Ferien: Stadt St. Gallen
(Spielkontext-Tabelle v5), Rückfall Kanton SG über OpenHolidays.</p>
"""


# --------------------------------------------------------------------------------------------
# Modell und Rückblick
# --------------------------------------------------------------------------------------------
def modell(run4_tab: Path, mart: Path) -> dict:
    k = pd.read_csv(run4_tab / "koeffizienten.csv")
    e = pd.read_csv(run4_tab / "erwartung_je_spiel.csv")
    m = pd.read_csv(mart)
    modelle = {}
    for ziel, g in k.groupby("ziel_code"):
        modelle[ziel] = {"transformation": g["transformation"].iloc[0], "rmse": float(g["rmse_lomo_transformiert"].iloc[0]),
                         "terme": {t: float(v) for t, v in zip(g["term"], g["koeffizient"])}}
    terme = k["term"].astype(str)
    saisons = sorted({t[len("C(saison)[T."):-1] for t in terme if t.startswith("C(saison)")} | set(e["saison"]))
    je_saison = e.groupby("saison")["match_id"].nunique()
    voll = je_saison[je_saison >= 15]
    basis = str((voll if len(voll) else je_saison).index.max())
    sl = m[(m["wettbewerb"] == "SL") & (m["spielstatus"] == "gespielt")]
    # Mittel nur über erfasste Werte (fehlend ≠ 0); ohne Werte bleibt das Feld leer (null)
    mittel = {s: {c: (float(g[c].mean()) if g[c].notna().any() else None) for c in ("soll", "ist_vip")}
              for s, g in sl.groupby("saison")}
    e = e.merge(m[["match_id", "gegner_anzeige", "wochentag"]], on="match_id", how="left")
    e = e[e["ziel_code"].isin([z["code"] for z in ZIELE])]
    spiele = [{"datum": pd.Timestamp(r.datum).strftime("%Y-%m-%d"), "saison": r.saison,
               "gegner": r.gegner_anzeige if isinstance(r.gegner_anzeige, str) else "", "anstoss_slot": r.anstoss_slot,
               "ziel_code": r.ziel_code, "beobachtet": float(r.beobachtet), "erwartet": float(r.erwartet),
               "band80_unten": float(r.band80_unten), "band80_oben": float(r.band80_oben)}
              for r in e.sort_values("datum").itertuples()]
    slots = [{"code": "referenz", "label": REFERENZ_SLOT}] + [{"code": c, "label": l} for c, l in SLOTS.items()]
    code_von = {s["label"]: s["code"] for s in slots}
    kf = e[e["ziel_code"] == "kf_exkl"].copy()
    kf["gruppe"] = kf["wochentag"].map(lambda t: "Werktag" if t in WERKTAGE else t)
    ansetzungen: dict = {}
    for (gr, sl_), n in kf.groupby(["gruppe", "anstoss_slot"]).size().items():
        ansetzungen.setdefault(gr, {})[code_von[sl_]] = int(n)
    return {"saisons": saisons, "basis_saison": basis, "slots": slots, "ansetzungen": ansetzungen, "modelle": modelle,
            "saison_mittel": mittel, "spiele": spiele}


# --------------------------------------------------------------------------------------------
# Normalwerte Wetter (öffentliche MeteoSchweiz-Stundenwerte)
# --------------------------------------------------------------------------------------------
def klima(wetter_csv: Path) -> dict:
    """Normalwerte je Monat und Stunde (Lokalzeit, Ende des Stundenintervalls).

    temp[monat][stunde] = mittlere Temperatur des Intervalls, das um «stunde» endet (= Anpfiffstunde aufgerundet).
    regen2/regen3[monat][stunde] = Anteil Tage mit ≥ 0.5 mm in den 2 bzw. 3 Intervallen bis «stunde»
    (2 Intervalle bei Anpfiff zur vollen Stunde, 3 bei Anpfiff dazwischen – gleiche Regel wie fcsg/sources/extern.py).
    """
    w = pd.read_csv(wetter_csv, parse_dates=["zeit_ende_utc"])
    w["t"] = w["zeit_ende_utc"].dt.tz_localize("UTC").dt.tz_convert(config.ZEITZONE).dt.tz_localize(None)
    w = w.set_index("t").sort_index()
    w = w[~w.index.duplicated()]
    n = w["niederschlag_mm"]
    s2 = n.rolling(2, min_periods=2).sum()
    s3 = n.rolling(3, min_periods=3).sum()
    df = pd.DataFrame({"temp": w["temp_c"], "r2": (s2 >= 0.5).where(s2.notna()), "r3": (s3 >= 0.5).where(s3.notna())})
    df["monat"], df["stunde"] = df.index.month, df.index.hour
    g = df.groupby(["monat", "stunde"])
    out = {"temp": {}, "regen2": {}, "regen3": {}, "jahre": f"{w.index.min():%Y}–{w.index.max():%Y}"}
    for (mo, st), x in g:
        for key, col in (("temp", "temp"), ("regen2", "r2"), ("regen3", "r3")):
            v = x[col].astype(float).mean()
            out[key].setdefault(str(mo), {})[str(st)] = None if np.isnan(v) else round(float(v), 3)
    return out


# --------------------------------------------------------------------------------------------
# Ferien Stadt SG und Parallelanlässe aus der Spielkontext-Tabelle (öffentliche Kalenderinformation)
# --------------------------------------------------------------------------------------------
def _als_datum(v) -> date | None:
    if isinstance(v, datetime):
        return v.date()
    return v if isinstance(v, date) else None


def kalender(kontext_xlsx: Path) -> dict:
    import openpyxl
    wb = openpyxl.load_workbook(kontext_xlsx, read_only=True, data_only=True)
    ferien, perioden = [], []
    if "Ferien" in wb.sheetnames:
        rows = list(wb["Ferien"].iter_rows(values_only=True))
        kopf = [str(c).strip() if c else "" for c in rows[0]]
        i_d, i_f = kopf.index("Datum"), kopf.index("Schulferien Stadt SG")
        i_a = kopf.index("Ferienart") if "Ferienart" in kopf else None
        for r in rows[1:]:
            d = _als_datum(r[i_d])
            if d is None:
                continue
            ja = str(r[i_f]).strip().lower() == "ja"
            if ja and perioden and (d - perioden[-1]["bis"]).days == 1:
                perioden[-1]["bis"] = d
            elif ja:
                perioden.append({"von": d, "bis": d, "name": (r[i_a] if i_a is not None else None) or "Schulferien"})
        ferien = [{"von": p["von"].isoformat(), "bis": p["bis"].isoformat(), "name": str(p["name"])} for p in perioden]
        ende = max(_als_datum(r[i_d]) for r in rows[1:] if _als_datum(r[i_d]))
    anlaesse = []
    if "Paralellevent" in wb.sheetnames:
        rows = list(wb["Paralellevent"].iter_rows(values_only=True))
        kopf = [str(c).strip() if c else "" for c in rows[0]]
        i_d = kopf.index("Datum")
        i_rel = next(i for i, h in enumerate(kopf) if h.startswith("relevanter Parallelevent"))
        i_n = kopf.index("Parallelevents") if "Parallelevents" in kopf else None
        i_g = next((i for i, h in enumerate(kopf) if h.startswith("Grossevent")), None)
        for r in rows[1:]:
            d = _als_datum(r[i_d])
            if d and str(r[i_rel]).strip().lower() == "ja":
                anlaesse.append({"datum": d.isoformat(), "name": str(r[i_n] or "Parallelanlass") if i_n is not None else "Parallelanlass",
                                 "gross": str(r[i_g]).strip().lower() == "ja" if i_g is not None else False})
    return {"ferien_stadt": ferien, "ferien_stadt_bis": ende.isoformat() if ferien else None, "anlaesse": anlaesse}


def daten(run4_tab: Path, mart: Path, kontext_xlsx: Path | None, wetter_csv: Path, testdaten: bool) -> dict:
    m = modell(run4_tab, mart)
    kal = kalender(kontext_xlsx) if kontext_xlsx else {"ferien_stadt": [], "ferien_stadt_bis": None, "anlaesse": []}
    return {"meta": {"testdaten": testdaten, "basis_saison": m["basis_saison"], "erzeugt": date.today().isoformat(),
                     "untertitel": ("TESTDATEN · " if testdaten else "") + f"Kontextmodell Run 4 · Meisterschaft · Basis {m['basis_saison']}",
                     "lesehilfe": LESEHILFE},
            "ziele": ZIELE, "top_gegner_muster": TOP_GEGNER_MUSTER, "station": STATION, "klima": klima(wetter_csv),
            **{k: v for k, v in m.items() if k != "basis_saison"}, **kal}


LOGO = HIER / "assets" / "fcsg_logo.png"     # Clublogo (freigestellt), eingebettet als data-URI


def _logo_html() -> str:
    if not LOGO.exists():
        return '<div class="logo-text">SG</div>'
    b64 = base64.b64encode(LOGO.read_bytes()).decode("ascii")
    return f'<img class="logo" src="data:image/png;base64,{b64}" alt="FC St.Gallen 1879">'


def schreibe(d: dict, ziel: Path) -> None:
    html = (HIER / "vorlage.html").read_text(encoding="utf-8")
    payload = json.dumps(d, ensure_ascii=False, allow_nan=False).replace("</", "<\\/")
    ziel.write_text(html.replace("__LOGO__", _logo_html()).replace("__DATEN__", payload), encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--run4", type=Path, help="Run-4-Ordner (mit Unterordner Tabellen)")
    ap.add_argument("--mart", type=Path, help="mart_match.csv (Gegner, SOLL, VIP je Spiel)")
    ap.add_argument("--kontext", type=Path, help="Spielkontext_Tabelle_FCSG_5.xlsx (Ferien Stadt SG, Parallelanlässe)")
    ap.add_argument("--wetter", type=Path, default=KERN / "external" / "meteoschweiz_stg_stuendlich.csv")
    ap.add_argument("--ausgabe", type=Path, required=True)
    ap.add_argument("--testdaten", action="store_true", help="künstliche, markierte Testdaten verwenden")
    ap.add_argument("--demo", action="store_true", help="mit --testdaten: realistische Saisons, Kalender aus --kontext (öffentliche Vorschau)")
    a = ap.parse_args()
    if a.testdaten:
        from testdaten import erzeuge
        tab, mart, kontext = erzeuge(a.ausgabe.parent / "_testdaten", demo=a.demo)
        if a.demo and a.kontext:
            kontext = a.kontext            # öffentliche Kalenderinformation (Ferien Stadt SG, Parallelanlässe)
    else:
        if not (a.run4 and a.mart and a.kontext):
            ap.error("--run4, --mart und --kontext angeben (oder --testdaten)")
        tab, mart, kontext = a.run4 / "Tabellen", a.mart, a.kontext
    schreibe(daten(tab, mart, kontext, a.wetter, a.testdaten), a.ausgabe)
    print(f"Spielrechner geschrieben: {a.ausgabe}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

"""Spielrechner (D-047): erzeugt eine einzelne, offline nutzbare HTML-Datei aus den Run-4-Tabellen.

    python spielrechner/build.py --run4 "<Run-4-Ordner>" --mart "<mart_match.csv>" --ausgabe Spielrechner.html
    python spielrechner/build.py --testdaten --ausgabe Spielrechner_TEST.html   # künstliche, markierte Testdaten

Eingaben: Run-4-Tabellen `koeffizienten.csv` und `erwartung_je_spiel.csv`, dazu `mart_match.csv` (Gegner, SOLL, VIP je Spiel).
Die Ausgabe enthält Clubzahlen je Spiel (aggregiert) und ist vertraulich: nicht öffentlich publizieren (D-047).
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import pandas as pd

HIER = Path(__file__).resolve().parent
sys.path.insert(0, str(HIER.parent))

from fcsg.analysis.anstoss_slot import REFERENZ_SLOT, SLOTS  # noqa: E402

WERKTAGE = ("Montag", "Dienstag", "Mittwoch", "Donnerstag", "Freitag")
ZIELE = [
    {"code": "anwesenheitsquote", "label": "Anwesenheitsquote (IST/SOLL)", "prozent": True},
    {"code": "kf_exkl", "label": "Kundenfranken exkl. MwSt", "prozent": False},
    {"code": "bons_pro_anwesende", "label": "Bons je Public-Anwesendem", "prozent": False},
    {"code": "bon_exkl", "label": "Ø Bon exkl. MwSt", "prozent": False},
]
LESEHILFE = """
<p><b>Wozu?</b> Der Spielrechner zeigt, was ein Heimspiel unter seinen Bedingungen (Saisonniveau, Anstoss, Gegner,
Wetter, Ferien) erwarten lässt – vor dem Spiel für die Planung, nach dem Spiel als Vergleich.</p>
<p><b>Kontext vs. Clubhebel:</b> Anstoss, Gegner, Wetter und Ferien sind für den Club extern und werden herausgerechnet.
Was danach bleibt (über/unter Erwartung), kann an Clubhebeln liegen – Stände, Runner, Zweitmarkt, Kommunikation –
aber auch an Zufall. Abweichungen sind Prüfhinweise, kein entgangener Umsatz.</p>
<p><b>Grenzen:</b> Zusammenhänge aus rund 76 Meisterschaftsspielen ab 2022/23, keine Kausalnachweise. Für die
Vorschau nur vor dem Spiel bekannte Werte verwenden (Wetterprognose). Bons 2023/24 eingeschränkt vergleichbar
(Kassensystemwechsel). Umsatz = Public-Anwesende × Kundenfranken (exkl. MwSt), Catering-Systemumsatz – nicht Cluberlös.</p>
<p><b>Pflege:</b> Neue Saison/Spiele: Spielkontext-Tabelle ergänzen, Rechenkern (run4.py) neu laufen lassen, Datei neu erzeugen.</p>
"""


def daten(run4: Path, mart: Path, testdaten: bool, basis_saison: str | None = None) -> dict:
    k = pd.read_csv(run4 / "koeffizienten.csv")
    e = pd.read_csv(run4 / "erwartung_je_spiel.csv")
    m = pd.read_csv(mart)
    modelle = {}
    for ziel, g in k.groupby("ziel_code"):
        modelle[ziel] = {"transformation": g["transformation"].iloc[0], "rmse": float(g["rmse_lomo_transformiert"].iloc[0]),
                         "terme": {t: float(v) for t, v in zip(g["term"], g["koeffizient"])}}
    terme = k["term"].astype(str)
    saisons = sorted({t[len("C(saison)[T."):-1] for t in terme if t.startswith("C(saison)")} | set(e["saison"]))
    vollsaisons = e.groupby("saison")["match_id"].nunique()
    voll = vollsaisons[vollsaisons >= 15]
    basis = basis_saison or str((voll if len(voll) else vollsaisons).index.max())
    sl = m[(m["wettbewerb"] == "SL") & (m["spielstatus"] == "gespielt")]
    # Mittel nur über erfasste Werte (fehlend ≠ 0); ohne erfasste Werte bleibt das Feld leer (null)
    mittel = {s: {c: (float(g[c].mean()) if g[c].notna().any() else None) for c in ("soll", "ist_vip")}
              for s, g in sl.groupby("saison")}
    e = e.merge(m[["match_id", "gegner_anzeige"]], on="match_id", how="left")
    e = e[e["ziel_code"].isin([z["code"] for z in ZIELE])]
    spiele = [{"datum": pd.Timestamp(r.datum).strftime("%d.%m.%Y"), "saison": r.saison, "gegner": r.gegner_anzeige
               if isinstance(r.gegner_anzeige, str) else "", "anstoss_slot": r.anstoss_slot, "ziel_code": r.ziel_code,
               "beobachtet": float(r.beobachtet), "erwartet": float(r.erwartet),
               "band80_unten": float(r.band80_unten), "band80_oben": float(r.band80_oben)}
              for r in e.sort_values("datum").itertuples()]
    slots = [{"code": "referenz", "label": REFERENZ_SLOT}] + [{"code": c, "label": l} for c, l in SLOTS.items()]
    # Vergleichsspiele je Tagesgruppe und Slot (Modellstichprobe KF) – für den Hinweis bei seltenen Ansetzungen
    code_von = {s["label"]: s["code"] for s in slots}
    kf = e[e["ziel_code"] == "kf_exkl"].merge(m[["match_id", "wochentag"]], on="match_id", how="left")
    kf["gruppe"] = kf["wochentag"].map(lambda t: "Werktag" if t in WERKTAGE else t)
    ansetzungen = {}
    for (g, sl), n in kf.groupby(["gruppe", "anstoss_slot"]).size().items():
        ansetzungen.setdefault(g, {})[code_von[sl]] = int(n)
    return {"meta": {"testdaten": testdaten, "basis_saison": basis,
                     "untertitel": ("TESTDATEN · " if testdaten else "") + f"Kontextmodell Run 4 · Meisterschaft · Basis {basis}",
                     "lesehilfe": LESEHILFE},
            "saisons": saisons, "slots": slots, "ansetzungen": ansetzungen, "ziele": ZIELE, "modelle": modelle, "saison_mittel": mittel,
            "spiele": spiele}


def schreibe(d: dict, ziel: Path) -> None:
    html = (HIER / "vorlage.html").read_text(encoding="utf-8")
    payload = json.dumps(d, ensure_ascii=False, allow_nan=False).replace("</", "<\\/")
    ziel.write_text(html.replace("__DATEN__", payload), encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--run4", type=Path, help="Run-4-Ordner (mit Unterordner Tabellen)")
    ap.add_argument("--mart", type=Path, help="mart_match.csv (Gegner, SOLL, VIP je Spiel)")
    ap.add_argument("--ausgabe", type=Path, required=True)
    ap.add_argument("--basis-saison", default=None)
    ap.add_argument("--testdaten", action="store_true", help="künstliche, markierte Testdaten verwenden")
    a = ap.parse_args()
    if a.testdaten:
        from testdaten import erzeuge
        tab, mart = erzeuge(a.ausgabe.parent / "_testdaten")
    else:
        if not (a.run4 and a.mart):
            ap.error("--run4 und --mart angeben (oder --testdaten)")
        tab, mart = a.run4 / "Tabellen", a.mart
    schreibe(daten(tab, mart, a.testdaten, a.basis_saison), a.ausgabe)
    print(f"Spielrechner geschrieben: {a.ausgabe}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

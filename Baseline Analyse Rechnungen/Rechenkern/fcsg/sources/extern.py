"""Öffentliche Zusatzdaten (Cache in «external/»): Stundenwetter MeteoSchweiz und Super-League-Resultate.

* Wetter zum Anpfiff und im Anreisefenster ersetzt das Tagesmittel der Kontexttabelle nicht, sondern
  ergänzt es (Projektantrag: «Wetter zur Anstosszeit»; Auftrag: Tagesmittel ist eine Grenze).
* Aus den Resultaten werden Tabellenstand, Punkte pro Spiel und Form VOR dem Spieltag berechnet
  (nur Spiele mit Datum strikt vor dem Heimspiel). Damit lassen sich die in der Kontexttabelle
  fehlenden Spiele ergänzen und die vorhandenen Werte gegenprüfen.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from .. import config
from ..log import befund

FCSG = "St. Gallen"


def lade_wetter_stunden() -> pd.DataFrame:
    if not config.WETTER_FILE.exists():
        befund("Extern", "mittel", str(config.WETTER_FILE), "Wetter-Cache fehlt.",
               "Kein Wetter zur Anpfiffzeit; nur Tagesmittel aus der Kontexttabelle.",
               "scripts/externe_daten_aktualisieren.py ausführen.")
        return pd.DataFrame()
    w = pd.read_csv(config.WETTER_FILE, parse_dates=["zeit_ende_utc"])
    w["zeit_ende_lokal"] = (w["zeit_ende_utc"].dt.tz_localize("UTC").dt.tz_convert(config.ZEITZONE)
                            .dt.tz_localize(None))
    return w


def wetter_fuer_spiele(anpfiff: pd.DataFrame, wetter: pd.DataFrame) -> pd.DataFrame:
    """Wetter je Spiel. ``anpfiff`` braucht die Spalten match_id und anpfiff_ts (lokale Zeit).

    Stundenintervalle (Ende = Zeitstempel): Anpfiff-Stunde = Intervall, das den Anpfiff enthält;
    Anreise = Intervalle, die das Fenster 2 h vor Anpfiff berühren; Spiel = 2 h ab Anpfiff.
    """
    if wetter.empty:
        return pd.DataFrame({"match_id": anpfiff["match_id"]})
    w = wetter.set_index("zeit_ende_lokal").sort_index()
    rows = []
    for _, r in anpfiff.dropna(subset=["anpfiff_ts"]).iterrows():
        ko = r["anpfiff_ts"]
        ende_ko = ko.ceil("h")
        anreise = w.loc[(w.index > ko - pd.Timedelta(hours=2)) & (w.index <= ende_ko)]
        spiel = w.loc[(w.index > ko) & (w.index <= ko + pd.Timedelta(hours=2))]
        h = w.loc[[ende_ko]] if ende_ko in w.index else pd.DataFrame()
        rows.append({
            "match_id": r["match_id"],
            "temp_anpfiff_c": h["temp_c"].iloc[0] if len(h) else np.nan,
            "wind_anpfiff_kmh": h["wind_kmh"].iloc[0] if len(h) else np.nan,
            "niederschlag_anreise_mm": anreise["niederschlag_mm"].sum(min_count=1),
            "niederschlag_spiel_mm": spiel["niederschlag_mm"].sum(min_count=1),
            "sonne_anreise_min": anreise["sonne_min"].sum(min_count=1),
            "temp_spiel_mittel_c": spiel["temp_c"].mean(),
        })
    out = pd.DataFrame(rows)
    out["regen_anreise"] = out["niederschlag_anreise_mm"] >= 0.5
    return out


def lade_resultate() -> pd.DataFrame:
    if not config.RESULTATE_FILE.exists():
        befund("Extern", "mittel", str(config.RESULTATE_FILE), "Resultate-Cache fehlt.",
               "Tabellenstand nur aus der Kontexttabelle (25/26 lückenhaft).",
               "scripts/externe_daten_aktualisieren.py ausführen.")
        return pd.DataFrame()
    r = pd.read_csv(config.RESULTATE_FILE, parse_dates=["datum"])
    uk = pd.to_datetime(r["zeit_uk"], format="%H:%M", errors="coerce")
    r["anpfiff_ch"] = (uk + pd.Timedelta(hours=1)).dt.strftime("%H:%M")
    return r


def _punkte(tore_eigen, tore_gegner) -> int:
    return 3 if tore_eigen > tore_gegner else (1 if tore_eigen == tore_gegner else 0)


def tabelle_vor_spielen(resultate: pd.DataFrame) -> pd.DataFrame:
    """Je FCSG-Heimspiel der Super League: Rang, Punkte, Punkte/Spiel und Form (letzte 5) beider Teams.

    Rangfolge: Punkte, Tordifferenz, erzielte Tore (Vereinfachung; ab der Ligatrennung reine
    Punkterangliste). Punkte pro Spiel werden zu Saisonbeginn mit dem Vorjahreswert gestützt.
    """
    if resultate.empty:
        return pd.DataFrame()
    r = resultate.sort_values(["datum", "anpfiff_ch"]).reset_index(drop=True)
    lang = pd.concat([
        pd.DataFrame({"saison": r["saison"], "datum": r["datum"], "team": r["heim"],
                      "tf": r["tore_heim"], "tg": r["tore_gast"]}),
        pd.DataFrame({"saison": r["saison"], "datum": r["datum"], "team": r["gast"],
                      "tf": r["tore_gast"], "tg": r["tore_heim"]}),
    ]).sort_values("datum").reset_index(drop=True)
    lang["pkt"] = [_punkte(a, b) for a, b in zip(lang["tf"], lang["tg"])]
    endstand = lang.groupby(["saison", "team"]).agg(pkt=("pkt", "sum"), sp=("pkt", "size")).reset_index()
    endstand["ppg_saison"] = endstand["pkt"] / endstand["sp"]
    saisons = sorted(lang["saison"].unique())
    vorjahr = {}
    for i, s in enumerate(saisons[1:], start=1):
        prev = endstand[endstand["saison"] == saisons[i - 1]].set_index("team")["ppg_saison"]
        vorjahr[s] = prev

    heim = r[r["heim"] == FCSG]
    rows = []
    for _, sp in heim.iterrows():
        vorher = lang[(lang["saison"] == sp["saison"]) & (lang["datum"] < sp["datum"])]
        tab = vorher.groupby("team").agg(pkt=("pkt", "sum"), sp=("pkt", "size"), tf=("tf", "sum"), tg=("tg", "sum"))
        teams = set(lang.loc[lang["saison"] == sp["saison"], "team"])
        tab = tab.reindex(sorted(teams)).fillna(0)
        tab["td"] = tab["tf"] - tab["tg"]
        tab = tab.sort_values(["pkt", "td", "tf"], ascending=False)
        tab["rang"] = np.arange(1, len(tab) + 1)
        info = {"datum": sp["datum"], "saison": sp["saison"], "gegner": sp["gast"], "anpfiff_resultate": sp["anpfiff_ch"],
                "tore_fcsg": sp["tore_heim"], "tore_gegner": sp["tore_gast"]}
        for wer, team in (("fcsg", FCSG), ("gegner", sp["gast"])):
            t = tab.loc[team]
            prior = vorjahr.get(sp["saison"], pd.Series(dtype=float)).get(team, 1.2)   # Aufsteiger: unterdurchschnittlich
            letzte = vorher[vorher["team"] == team].tail(5)
            info.update({
                f"rang_{wer}": int(t["rang"]) if t["sp"] > 0 else np.nan,
                f"punkte_{wer}": float(t["pkt"]), f"spiele_{wer}": float(t["sp"]),
                f"ppg_{wer}": float(t["pkt"] / t["sp"]) if t["sp"] > 0 else np.nan,
                f"ppg_{wer}_gestuetzt": float((t["pkt"] + 5 * prior) / (t["sp"] + 5)),
                f"form5_{wer}_punkte": float(letzte["pkt"].sum()) if len(letzte) else np.nan,
                f"form5_{wer}_spiele": float(len(letzte)),
            })
        rows.append(info)
    return pd.DataFrame(rows)

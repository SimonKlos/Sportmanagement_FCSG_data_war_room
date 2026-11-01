"""Datenmodell gemäss Auftrag Abschnitt 3: dim_match, Faktentabellen, dim_match_context, mart_match.

Regeln:
* Primärer Join-Schlüssel ist das Spieldatum (nie das Gegner-Label). Pro Datum gibt es höchstens ein
  Pflichtspiel der Herren; andere Events am selben Tag werden über den Wettbewerb ausgeschlossen.
* Zuerst jede Faktentabelle auf Spielebene aggregieren, dann verbinden (kein Rohdaten-Join).
* Nicht zuordenbare Zeilen und Duplikate werden im Unmatched-/Duplikatreport ausgewiesen.
"""
from __future__ import annotations

import re
from collections import Counter
from dataclasses import dataclass, field

import numpy as np
import pandas as pd

from . import config
from .log import befund, logger
from .utils import (anpfiff_slot, anzeige_gegner, gegner_kanonisch, ist_leer, minuten, saison_index, saison_von,
                    wochentag)

ANPFIFF_PRIORITAET = ["resultate", "kontext", "catering", "historie", "ticket_export"]


@dataclass
class Rohdaten:
    historie: pd.DataFrame
    catering: pd.DataFrame
    catering_staende_2122: pd.DataFrame
    entwicklung: pd.DataFrame
    kiesplatz: pd.DataFrame
    artikel: pd.DataFrame
    tickets_export: pd.DataFrame
    tickets_csv: pd.DataFrame
    abos: pd.DataFrame
    ticket_inventar: pd.DataFrame
    ankuenfte: pd.DataFrame
    zutritt_info: pd.DataFrame
    zutritt_frauen: pd.DataFrame
    kontext: pd.DataFrame
    kalender: pd.DataFrame
    wetter: pd.DataFrame
    resultate: pd.DataFrame
    tabelle: pd.DataFrame


@dataclass
class Modell:
    dim_match: pd.DataFrame
    fact_attendance_match: pd.DataFrame
    fact_catering_match: pd.DataFrame
    fact_kiesplatz: pd.DataFrame
    tickets: pd.DataFrame                     # Einzeltickets harmonisiert (ohne Personenbezug), nur Kernspiele
    dim_match_context: pd.DataFrame
    unmatched: pd.DataFrame
    duplikate: pd.DataFrame
    datenstand: pd.Timestamp
    extras: dict = field(default_factory=dict)


# --------------------------------------------------------------------------------------------
# dim_match
# --------------------------------------------------------------------------------------------
def _konsens(kandidaten: dict[str, str | None]) -> tuple[str | None, str, str]:
    werte = {q: v for q, v in kandidaten.items() if v}
    if not werte:
        return None, "", ""
    zaehl = Counter(werte.values())
    top = max(zaehl.values())
    beste = [v for v, c in zaehl.items() if c == top]
    wahl = next(werte[q] for q in ANPFIFF_PRIORITAET if werte.get(q) in beste) if len(beste) > 1 else beste[0]
    quellen = ", ".join(q for q, v in werte.items() if v == wahl)
    konflikt = "; ".join(f"{q}: {v}" for q, v in werte.items() if v != wahl)
    return wahl, quellen, konflikt


def baue_dim_match(r: Rohdaten) -> tuple[pd.DataFrame, pd.Timestamp]:
    h = r.historie
    kern = h[h["wettbewerb"].isin(config.KERN_WETTBEWERBE) & (h["saison"] >= config.BASELINE_AB_SAISON)].copy()
    dup = kern[kern.duplicated("datum", keep=False)]
    if len(dup):
        befund("Datenmodell", "hoch", "Historie", f"{len(dup)} Pflichtspiele mit gleichem Datum.",
               "Datum allein nicht eindeutig.", "Erstes Vorkommen verwendet; manuell prüfen.")
        kern = kern.drop_duplicates("datum")
    datenstand = kern.loc[kern["ist"].notna(), "datum"].max()

    dim = pd.DataFrame({
        "datum": kern["datum"].values, "saison": kern["saison"].values, "wettbewerb": kern["wettbewerb"].values,
        "wettbewerb_text": kern["wettbewerb_text"].values, "spiel_text": kern["spiel_text"].values,
        "historie_zeile": kern["zeile"].values, "spielstatus": "gespielt",
    })
    # Abgesagtes Spiel (nur im Catering erfasst) als eigenes Ereignis aufnehmen, aber nie im Modell
    abg = r.catering[(r.catering["wettbewerb"] == "SL abgesagt") & (r.catering["saison"] >= config.BASELINE_AB_SAISON)]
    for _, a in abg.iterrows():
        dim.loc[len(dim)] = {"datum": a["datum"], "saison": a["saison"], "wettbewerb": "SL",
                             "wettbewerb_text": "Meisterschaft (abgesagt)", "spiel_text": a["spiel"],
                             "historie_zeile": np.nan, "spielstatus": "abgesagt"}
        befund("Datenmodell", "info", f"Catering {a['blatt']} Zeile {a['zeile']} ({a['datum']:%d.%m.%Y})",
               "Spiel 10 Minuten vor Anpfiff abgesagt; Catering-Umsatz und Kiesplatz erfasst, keine Historie- und Zutrittszeile.",
               "Kein reguläres Spiel; Umsatz ohne Spielerlebnis.", "Als eigenes Ereignis (Status «abgesagt») geführt, nie in Modellen.")
    dim = dim.sort_values("datum").reset_index(drop=True)
    dim["historie_zeile"] = dim["historie_zeile"].astype("Int64")
    dim["match_id"] = dim["datum"].dt.strftime("%Y%m%d") + "_" + dim["wettbewerb"] + \
        np.where(dim["spielstatus"] == "abgesagt", "_abgesagt", "")

    # Gegner (nur Anzeige/Kontrolle): Resultate > Kontext > Historie-Text
    gegner_res = r.tabelle.set_index("datum")["gegner"] if not r.tabelle.empty else pd.Series(dtype=str)
    gegner_kon = r.kontext.set_index("datum")["gegner"] if not r.kontext.empty else pd.Series(dtype=str)
    dim["gegner"] = [gegner_res.get(d) or gegner_kon.get(d) or gegner_kanonisch(t)
                     for d, t in zip(dim["datum"], dim["spiel_text"])]
    dim["gegner_anzeige"] = dim["gegner"].map(anzeige_gegner)
    dim["top_gegner"] = dim["gegner"].isin(config.TOP_GEGNER)

    # Anpfiff aus allen Quellen (Mehrheit, bei Gleichstand Priorität)
    kand = {
        "historie": kern.set_index("datum")["anpfiff"],
        "catering": r.catering[r.catering["wettbewerb"].isin(list(config.KERN_WETTBEWERBE) + ["SL abgesagt"])]
                    .drop_duplicates("datum").set_index("datum")["anpfiff"],
        "kontext": r.kontext.set_index("datum")["anpfiff"] if not r.kontext.empty else pd.Series(dtype=str),
        "resultate": r.tabelle.set_index("datum")["anpfiff_resultate"] if not r.tabelle.empty else pd.Series(dtype=str),
        "ticket_export": r.tickets_export[r.tickets_export["ist_fcsg_herren_event"]]
                         .groupby("match_datum")["event_zeit"].agg(lambda s: s.mode().iloc[0]),
    }
    wahl = [_konsens({q: s.get(d) for q, s in kand.items()}) for d in dim["datum"]]
    dim["anpfiff"] = [w[0] for w in wahl]
    dim["anpfiff_quellen"] = [w[1] for w in wahl]
    dim["anpfiff_abweichungen"] = [w[2] for w in wahl]
    for _, row in dim[dim["anpfiff_abweichungen"] != ""].iterrows():
        befund("Datenmodell", "tief", f"{row['datum']:%d.%m.%Y} {row['gegner_anzeige']}",
               f"Anpfiff uneinheitlich – gewählt {row['anpfiff']} ({row['anpfiff_quellen']}); abweichend: {row['anpfiff_abweichungen']}.",
               "Ankunftszeiten relativ zum Anpfiff hängen davon ab.", "Mehrheitswert der Quellen verwendet.")
    dim["anpfiff_ts"] = pd.to_datetime(dim["datum"].dt.strftime("%Y-%m-%d") + " " + dim["anpfiff"].fillna("00:00"))
    dim.loc[dim["anpfiff"].isna(), "anpfiff_ts"] = pd.NaT

    dim["wochentag"] = dim["datum"].map(wochentag)
    dim["wochenende"] = dim["datum"].dt.weekday >= 5
    dim["wochentag_typ"] = np.where(dim["wochenende"], "Wochenende (Sa/So)", "Wochentag (Mo–Fr)")
    dim["anpfiff_slot"] = dim["anpfiff"].map(anpfiff_slot)
    dim["abendspiel"] = dim["anpfiff"].map(minuten) >= 20 * 60
    dim["monat"] = dim["datum"].dt.month
    dim["winter"] = dim["monat"].isin([11, 12, 1, 2])
    dim["saison_idx"] = dim["saison"].map(saison_index)
    dim.loc[(dim["datum"] > datenstand) & (dim["spielstatus"] == "gespielt"), "spielstatus"] = "geplant"
    cols = ["match_id", "datum", "saison", "saison_idx", "wettbewerb", "wettbewerb_text", "spielstatus", "gegner",
            "gegner_anzeige", "top_gegner", "anpfiff", "anpfiff_ts", "anpfiff_quellen", "anpfiff_abweichungen",
            "wochentag", "wochenende", "wochentag_typ", "anpfiff_slot", "abendspiel", "monat", "winter",
            "spiel_text", "historie_zeile"]
    return dim[cols], datenstand


# --------------------------------------------------------------------------------------------
# Faktentabellen
# --------------------------------------------------------------------------------------------
def _match_ids(dim: pd.DataFrame) -> pd.Series:
    return dim[dim["spielstatus"] != "abgesagt"].set_index("datum")["match_id"]


def fact_attendance(r: Rohdaten, dim: pd.DataFrame) -> pd.DataFrame:
    d = dim.dropna(subset=["historie_zeile"])[["match_id", "historie_zeile"]].astype({"historie_zeile": "int64"})
    h = r.historie.merge(d, left_on="zeile", right_on="historie_zeile", how="inner")
    f = h[["match_id", "soll", "ist", "ist_vip", "ist_gaeste", "zweitmarkt", "ausverkauft", "soll_definition",
           "ist_definition", "soll_formel", "ist_formel", "bemerkung", "zeile", "korrektur"]].rename(
        columns={"zeile": "historie_zeile"})
    f["noshow_abs"] = f["soll"] - f["ist"]
    f["noshow_quote"] = 1 - f["ist"] / f["soll"]
    f["anwesenheitsquote"] = f["ist"] / f["soll"]
    f["zweitmarkt_quote"] = f["zweitmarkt"] / f["soll"]
    f["verkaufsquote_naeherung"] = (f["soll"] - f["ist_gaeste"].fillna(0)) / config.KAPAZITAET_HEIM
    bem = f["bemerkung"].fillna("").str.lower()
    f["ist_qualitaet"] = np.select(
        [bem.str.contains("geschätzt|drehkreuze nicht|handscanner"), f["ist_formel"].notna() | bem.str.contains("keine scans")],
        ["IST geschätzt/Scanprobleme", "IST mit Ergänzung (Formel)"], default="IST aus Zählung")
    f["soll_ticketbasiert"] = ~f["soll_definition"].str.contains("Kapazität")
    return f


def fact_catering(r: Rohdaten, dim: pd.DataFrame) -> pd.DataFrame:
    c = r.catering[r.catering["wettbewerb"].isin(list(config.KERN_WETTBEWERBE) + ["SL abgesagt"])].copy()
    ids = _match_ids(dim)
    abg = dim[dim["spielstatus"] == "abgesagt"].set_index("datum")["match_id"]
    c["match_id"] = [abg.get(d) if w == "SL abgesagt" else ids.get(d) for d, w in zip(c["datum"], c["wettbewerb"])]
    keep = ["match_id", "datum", "saison", "wettbewerb", "spiel", "anpfiff", "public_netto", "transaktionen",
            "umsatz_inkl", "umsatz_exkl", "kf_inkl", "kf_exkl", "bons_pro_anwesende", "bon_inkl", "bon_exkl",
            "gaeste_catering", "formel_ist", "formel_abzug_vip", "public_netto_formel", "mwst_faktor_implizit",
            "stand_geschlossen", "mobiler_verkauf_reduziert", "personalmangel", "technische_probleme",
            "operativer_hinweis", "alle_staende_offen", "aktion_gratis_gutschein", "event_plattform",
            "mobil_status", "mobil_sektoren_ja", "mobil_sektoren_nein", "merch_verkauf",
            "bemerkung", "wetter_text", "resultat", "blatt", "zeile", "korrektur"]
    kanal = [k for k in c.columns if k.startswith("kanal_")]
    return c[keep + kanal].reset_index(drop=True)


def fact_kiesplatz(r: Rohdaten, dim: pd.DataFrame) -> pd.DataFrame:
    k = r.kiesplatz.copy()
    ids = _match_ids(dim)
    abg = dim[dim["spielstatus"] == "abgesagt"].set_index("datum")["match_id"]
    k["match_id"] = [abg.get(d) if "abgesagt" in str(e).lower() else ids.get(d) for d, e in zip(k["datum"], k["event"])]
    return k


def tickets_kern(r: Rohdaten, dim: pd.DataFrame) -> pd.DataFrame:
    """Einzeltickets beider Quellen, nur Pflichtspiele der Herren, mit match_id."""
    ids = _match_ids(dim)
    x = r.tickets_export[r.tickets_export["ist_fcsg_herren_event"]].copy()
    x["match_id"] = x["match_datum"].map(ids)
    c = r.tickets_csv[r.tickets_csv["wettbewerb_datei"].isin(config.KERN_WETTBEWERBE)].copy()
    c["match_id"] = c["match_datum"].map(ids)
    t = pd.concat([x, c], ignore_index=True, sort=False)
    return t[t["match_id"].notna()].reset_index(drop=True)


# --------------------------------------------------------------------------------------------
# dim_match_context
# --------------------------------------------------------------------------------------------
def baue_kontext(r: Rohdaten, dim: pd.DataFrame) -> pd.DataFrame:
    from .sources.extern import wetter_fuer_spiele

    ctx = dim[["match_id", "datum", "saison", "wettbewerb", "spielstatus", "gegner", "top_gegner", "anpfiff",
               "anpfiff_ts", "wochentag", "wochenende", "anpfiff_slot", "abendspiel", "monat", "winter"]].copy()
    k = r.kontext.drop_duplicates("datum").set_index("datum") if not r.kontext.empty else pd.DataFrame()
    ctx["in_kontexttabelle"] = ctx["datum"].isin(k.index) if len(k) else False
    for col in ["rang_fcsg_kontext", "punkte_fcsg_kontext", "rang_gegner_kontext", "punkte_gegner_kontext",
                "form_fcsg_punkte_kontext", "form_gegner_punkte_kontext", "free_tv_srf", "temp_tagesmittel",
                "niederschlag_tag_mm", "wind_tag_kmh", "schulferien", "feiertag", "parallelevent",
                "besondere_anlaesse", "tv"]:
        ctx[col] = ctx["datum"].map(k[col]) if len(k) and col in k else pd.NA

    # Tabellenstand/Form vor dem Spiel aus Resultaten (konsistente Methode für alle SL-Spiele)
    if not r.tabelle.empty:
        t = r.tabelle.drop_duplicates("datum").set_index("datum")
        for col in ["rang_fcsg", "punkte_fcsg", "ppg_fcsg", "ppg_fcsg_gestuetzt", "form5_fcsg_punkte",
                    "rang_gegner", "punkte_gegner", "ppg_gegner", "ppg_gegner_gestuetzt", "form5_gegner_punkte",
                    "spiele_fcsg"]:
            ctx[col] = ctx["datum"].map(t[col])
        _vergleich_tabelle(ctx)

    # Kalender (Ferien/Parallelevents/Feiertage) für Spiele ohne Kontextzeile ergänzen
    kal = r.kalender.drop_duplicates("datum").set_index("datum") if not r.kalender.empty else pd.DataFrame()
    for ziel, quelle in (("schulferien", "schulfrei_kalender"), ("parallelevent", "parallelevent_kalender"),
                         ("feiertag", "feiertag_kalender")):
        ctx[f"{ziel}_quelle"] = np.where(ctx[ziel].notna(), "Kontexttabelle", "")
        if len(kal) and quelle in kal:
            fehlt = ctx[ziel].isna()
            ctx.loc[fehlt, ziel] = ctx.loc[fehlt, "datum"].map(kal[quelle])
            ctx.loc[fehlt & ctx[ziel].notna(), f"{ziel}_quelle"] = "Kalender der Kontextdatei"
    # Wetter zur Anpfiffzeit (MeteoSchweiz)
    w = wetter_fuer_spiele(ctx[["match_id", "anpfiff_ts"]], r.wetter)
    ctx = ctx.merge(w, on="match_id", how="left")
    # TV: SRF-Übertragung (Free-TV) – nur aus Kontexttabelle verfügbar
    ctx["free_tv_srf"] = ctx["free_tv_srf"].astype("boolean")
    for c in ("schulferien", "parallelevent", "feiertag"):
        ctx[c] = ctx[c].astype("boolean")
    return ctx


def _vergleich_tabelle(ctx: pd.DataFrame) -> None:
    sub = ctx[(ctx["wettbewerb"] == "SL") & ctx["rang_gegner_kontext"].notna() & ctx["punkte_gegner"].notna()]
    if sub.empty:
        return
    diff = sub[(sub["punkte_gegner_kontext"] - sub["punkte_gegner"]).abs() >= 5]
    for _, row in diff.iterrows():
        befund("Kontext", "mittel", f"Spielkontext-Tabelle {row['datum']:%d.%m.%Y} ({row['gegner']})",
               f"Punktestand Gegner vor dem Spiel: Tabelle {row['punkte_gegner_kontext']:.0f}, aus Resultaten berechnet "
               f"{row['punkte_gegner']:.0f} (FCSG: {row['punkte_fcsg_kontext']:.0f} vs. {row['punkte_fcsg']:.0f}).",
               "Tabellenstand in der Kontexttabelle veraltet.",
               "In Modellen wird der berechnete Stand verwendet; Kontexttabelle nachführen.")
    gleich = (sub["rang_gegner_kontext"] == sub["rang_gegner"]).mean()
    befund("Kontext", "info", "Spielkontext-Tabelle, Tabellenstand vor dem Spiel",
           f"Abgleich mit Rangliste aus Resultaten (n={len(sub)} SL-Spiele): Gegner-Rang in {gleich:.0%} identisch.",
           "Kleinere Abweichungen durch Zeitpunkt (Spiele am selben Tag) und Rangregeln.",
           "Für alle Modelle einheitlich der berechnete Stand (Spiele strikt vor dem Datum).")


# --------------------------------------------------------------------------------------------
# Unmatched- und Duplikatreport
# --------------------------------------------------------------------------------------------
def _grund_catering(w: str) -> str:
    return {"Frauen": "Frauen (ausserhalb Kernscope)", "U21": "U21 (ausserhalb Kernscope)",
            "Nati": "Länderspiel (ausserhalb Kernscope)", "Test": "Testspiel (ausserhalb Kernscope)",
            "Event": "Event ohne Spiel (ausserhalb Kernscope)", "Fremdclub": "Fremdclub (ausserhalb Kernscope)"}.get(
        w, "Pflichtspiel ohne Gegenstück in dim_match – prüfen")


def unmatched_report(r: Rohdaten, dim: pd.DataFrame, cat: pd.DataFrame, kies: pd.DataFrame,
                     tickets: pd.DataFrame) -> pd.DataFrame:
    rows = []
    ab = config.BASELINE_AB_SAISON
    ids = set(dim["datum"])
    # Catering: alle Zeilen ab Baseline, die keinem Kernspiel zugeordnet sind
    c = r.catering[(r.catering["saison"] >= ab)]
    for _, x in c.iterrows():
        if x["wettbewerb"] in config.KERN_WETTBEWERBE and x["datum"] in ids:
            continue
        if x["wettbewerb"] == "SL abgesagt":
            continue
        rows.append({"quelle": "Catering", "ort": f"Blatt {x['blatt']} Zeile {x['zeile']}",
                     "datum": x["datum"], "bezeichnung": x["spiel"], "kategorie": x["wettbewerb"],
                     "grund": _grund_catering(x["wettbewerb"]) if not pd.isna(x["datum"]) else "kein eindeutiges Datum (mehrtägig)"})
    # Kiesplatz
    for _, x in kies[kies["ist_total"] & kies["match_id"].isna()].iterrows():
        fcsg_spiel = bool(re.search(r"st\.?\s*gallen|fcsg", str(x["event"]), re.I)) and "frauen" not in str(x["event"]).lower()
        rows.append({"quelle": "Kiesplatz", "ort": f"{x['blatt']} Zeile {x['zeile']}", "datum": x["datum"],
                     "bezeichnung": x["event"], "kategorie": "Spiel" if fcsg_spiel else "Event",
                     "grund": "FCSG-Spiel ohne Heimspiel an diesem Datum – Datumsfehler prüfen" if fcsg_spiel
                     else "kein Pflichtspiel der Herren (Länderspiel/Event/WEURO)"})
    # Ticket-Exporte: Events ohne Kernspiel
    ex = r.tickets_export.groupby(["datei", "event_label", "match_datum"]).size().rename("tickets").reset_index()
    for _, x in ex.iterrows():
        if x["match_datum"] in ids and ("FC St.Gallen 1879 - " in x["event_label"]) and \
                not any(s in x["event_label"] for s in ("Frauen", "Mitgliedschaft", "KIDS")):
            continue
        rows.append({"quelle": "Einzeltickets Export", "ort": x["datei"], "datum": x["match_datum"],
                     "bezeichnung": f"{x['event_label']} ({x['tickets']} Tickets)", "kategorie": "Event",
                     "grund": "kein Pflichtspiel der Herren (Test/Frauen/Mitgliedschaft/Event) oder Eventdatum ≠ Spieldatum"})
    for _, x in r.ticket_inventar.iterrows():
        if x["ist_abo"] or (x["wettbewerb"] in config.KERN_WETTBEWERBE and x["datei_datum"] in ids):
            continue
        rows.append({"quelle": "Ticket-CSV", "ort": x["datei"], "datum": x["datei_datum"], "bezeichnung": x["datei"],
                     "kategorie": x["wettbewerb"], "grund": "Frauen (ausserhalb Kernscope)" if x["wettbewerb"] == "Frauen" else "prüfen"})
    # Zutritt: Spieltage ohne Kernspiel
    for _, x in r.zutritt_info[~r.zutritt_info["datum"].isin(ids)].iterrows():
        rows.append({"quelle": "Zutritt", "ort": x["lieferung"], "datum": x["datum"], "bezeichnung": x["spieltag_label"],
                     "kategorie": "?", "grund": "prüfen"})
    # Kontext: Zeilen ohne Kernspiel (z.B. geplante Spiele nach Datenstand)
    if not r.kontext.empty:
        for _, x in r.kontext[~r.kontext["datum"].isin(ids)].iterrows():
            rows.append({"quelle": "Kontexttabelle", "ort": f"Übersicht Zeile {x['zeile']}", "datum": x["datum"],
                         "bezeichnung": x["gegner_text"], "kategorie": x["wettbewerb"],
                         "grund": "geplantes Spiel (nach Datenstand)" if not x["resultat_bekannt"] else "prüfen"})
    # Umgekehrt: Kernspiele ohne Daten je Quelle
    gespielt = dim[dim["spielstatus"] == "gespielt"]
    cat_ids = set(cat["match_id"].dropna())
    for _, x in gespielt[~gespielt["match_id"].isin(cat_ids)].iterrows():
        rows.append({"quelle": "Catering", "ort": "-", "datum": x["datum"], "bezeichnung": x["spiel_text"],
                     "kategorie": x["wettbewerb"], "grund": "Kernspiel ohne Catering-Zeile"})
    ktx = set(r.kontext["datum"]) if not r.kontext.empty else set()
    for _, x in gespielt[(gespielt["saison"] >= config.MODELL_AB_SAISON) & ~gespielt["datum"].isin(ktx)].iterrows():
        rows.append({"quelle": "Kontexttabelle", "ort": "-", "datum": x["datum"], "bezeichnung": x["spiel_text"],
                     "kategorie": x["wettbewerb"], "grund": "Kernspiel fehlt in der Kontexttabelle (ergänzt aus Resultaten/Kalender/Wetter)"})
    tick_ids = set(tickets["match_id"].dropna())
    for _, x in gespielt[~gespielt["match_id"].isin(tick_ids)].iterrows():
        rows.append({"quelle": "Einzeltickets", "ort": "-", "datum": x["datum"], "bezeichnung": x["spiel_text"],
                     "kategorie": x["wettbewerb"], "grund": "Kernspiel ohne Einzelticket-Daten (Export abgeschnitten bzw. Datei fehlt)"})
    out = pd.DataFrame(rows)
    out["zu_pruefen"] = out["grund"].str.contains("prüfen", regex=False) | out["grund"].str.startswith("Kernspiel")
    return out.sort_values(["zu_pruefen", "quelle", "datum"], ascending=[False, True, True]).reset_index(drop=True)


def duplikat_report(r: Rohdaten) -> pd.DataFrame:
    rows = []
    c = r.catering[r.catering["wettbewerb"].isin(config.KERN_WETTBEWERBE)]
    for d, g in c.groupby("datum"):
        if len(g) > 1:
            rows.append({"quelle": "Catering", "schluessel": f"{d:%d.%m.%Y}", "anzahl": len(g), "behandlung": "prüfen"})
    for d, g in r.catering[r.catering["saison"] >= config.BASELINE_AB_SAISON].groupby("datum"):
        if len(g) > 1:
            rows.append({"quelle": "Catering (alle Events)", "schluessel": f"{d:%d.%m.%Y}", "anzahl": len(g),
                         "behandlung": "mehrere Events am selben Tag – über Wettbewerb getrennt: " +
                                       ", ".join(g["wettbewerb"].astype(str))})
    k = r.kiesplatz[r.kiesplatz["ist_total"]]
    for d, g in k.groupby("datum"):
        if len(g) > 1:
            rows.append({"quelle": "Kiesplatz", "schluessel": f"{d:%d.%m.%Y}", "anzahl": len(g),
                         "behandlung": "mehrere Abrechnungszeilen am selben Datum – prüfen"})
    z = r.zutritt_info
    rows.append({"quelle": "Zutritt", "schluessel": "Ticket-ID je Spiel",
                 "anzahl": int(z["tickets_mehrfach_gescannt"].sum()),
                 "behandlung": "Mehrfachscans derselben Ticket-ID: nur erster Durchgang gezählt "
                               f"(Anteil {z['tickets_mehrfach_gescannt'].sum() / z['besucher_scans'].sum():.3%})"})
    return pd.DataFrame(rows)


# --------------------------------------------------------------------------------------------
# Gesamtaufbau
# --------------------------------------------------------------------------------------------
def baue_modell(r: Rohdaten) -> Modell:
    dim, datenstand = baue_dim_match(r)
    att = fact_attendance(r, dim)
    cat = fact_catering(r, dim)
    kies = fact_kiesplatz(r, dim)
    tick = tickets_kern(r, dim)
    ctx = baue_kontext(r, dim)
    unm = unmatched_report(r, dim, cat, kies, tick)
    dup = duplikat_report(r)
    logger.info("dim_match: %s Spiele (%s gespielt), Datenstand %s", len(dim), (dim["spielstatus"] == "gespielt").sum(),
                f"{datenstand:%d.%m.%Y}")
    return Modell(dim, att, cat, kies, tick, ctx, unm, dup, datenstand)

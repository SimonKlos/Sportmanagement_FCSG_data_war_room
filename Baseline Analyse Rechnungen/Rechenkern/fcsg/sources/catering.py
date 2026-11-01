"""Catering: Public-Catering-Umsätze je Event, Entwicklung, Kiesplatz-Abrechnungen, Artikelauswertung.

Die Saisonblätter haben je Saison andere Spalten (Payfix, Just Eat, Pick Up, Gutscheine, extern,
Contrailer ...). Die Spalten werden über ihre Überschrift auf kanonische Namen abgebildet; gelesen
wird nur der Bereich der Excel-Tabelle (rechts davon liegt eine Zusammenfassung mit gleichen Titeln).
"""
from __future__ import annotations

import re

import numpy as np
import openpyxl
import pandas as pd
from openpyxl.utils import range_boundaries

from .. import config
from ..log import befund
from ..utils import ist_leer, mwst_satz, text, parse_anpfiff, parse_datum, saison_von, zahl_oder_nan
from . import korrekturen

WETTBEWERB_MAP = {
    "meisterschaft": "SL", "cup": "Cup", "uefa wettbewerbe": "UEFA",
    "uefa wettbewerbe andere clubs": "Fremdclub", "länderspiel": "Nati", "freundschaftsspiel": "Test",
    "meisterschaft frauen": "Frauen", "meisterschaft u21": "U21", "diverse events": "Event",
}

_SPALTEN = [
    (r"^datum$", "datum"), (r"^(kick-off|zeit)$", "anpfiff_text"), (r"^spiel$", "spiel"),
    (r"^wettbewerb$", "wettbewerb_text"), (r"^wetter$", "wetter_text"), (r"^resultat$", "resultat"),
    (r"^bemerkung", "bemerkung"), (r"zuschauer gästesektor", "gaeste_catering"),
    (r"^(anwesende|zuschauerzahlen public netto)$", "public_netto"),
    (r"^anzahl transaktionen", "transaktionen"),
    (r"^umsatz total inkl", "umsatz_inkl"), (r"^umsatz total exkl", "umsatz_exkl"),
    (r"^umsatz public$", "kanal_public_inkl"), (r"^umsatz matchbar$", "kanal_matchbar_inkl"),
    (r"^umsatz stadion inkl", "kanal_stadion_inkl"), (r"^umsatz stadion exkl", "kanal_stadion_exkl"),
    (r"^umsatz matchbar inkl", "kanal_matchbar_inkl"), (r"^umsatz matchbar exkl", "kanal_matchbar_exkl"),
    (r"^umsatz payfix inkl", "kanal_payfix_inkl"), (r"^umsatz payfix exkl", "kanal_payfix_exkl"),
    (r"^umsatz just eat inkl", "kanal_justeat_inkl"), (r"^umsatz just eat exkl", "kanal_justeat_exkl"),
    (r"^umsatz pick ?up inkl", "kanal_pickup_inkl"), (r"^umsatz pick ?up exkl", "kanal_pickup_exkl"),
    (r"^umsatz nicht verbuchter.*inkl", "kanal_gutscheine_inkl"),
    (r"^umsatz nicht verbuchter.*exkl", "kanal_gutscheine_exkl"),
    (r"^umsatz extern inkl", "kanal_extern_inkl"), (r"^umsatz extern.*exkl", "kanal_extern_exkl"),
    (r"^umsatz contrailer inkl", "kanal_contrailer_inkl"), (r"^umsatz contrailer exkl", "kanal_contrailer_exkl"),
    (r"^ku\w*franken.*inkl", "kf_inkl_blatt"), (r"^ku\w*franken.*exkl", "kf_exkl_blatt"),
    (r"^transaktions-durchschnitt.*inkl", "bon_inkl_blatt"), (r"^transaktions-durchschnitt.*exkl", "bon_exkl_blatt"),
]
# Einzelstände im Blatt 2021-2022 (Contrailer/Bierwagen): für den Doppelzählungs-Abgleich mit dem Kiesplatz
_STAND_2122 = r"^(contrailer|bier \d|fanshop bar)"

# Operative Merkmale aus den Catering-Bemerkungen (satzweise geprüft, damit z.B. «Gästesektor geschlossen»
# oder «nach dem Spiel geschlossen» nicht als Standschliessung zählen). Standschliessung, «alle Stände offen» und
# mobiler Verkauf werden in codiere_bemerkung() gesondert behandelt (Listen nach «ausser» bzw. «geschlossen:»).
_OPERATIV = {
    "personalmangel": (r"zu wenig personal|personalmangel", None),
    "technische_probleme": (r"technische probleme|probleme mit (dem |den )?(handheld|terminal|just eat|login)|ausfall|nur twint", None),
    "aktion_gratis_gutschein": (r"kostenlos|gratis|punschgutschein", None),
    # Zusatzangebote/Programm; «Side Event 1: …» allein ist eine Kassenzuteilung und zählt nicht
    "event_plattform": (r"winterzauber|family ?day|kids[- ]?day|raclette|suppe|sittermarsch", None),
    # Verkauf von Fanartikeln über die Catering-Kassen (verzerrt den MwSt-Mix des Umsatzes)
    "merch_verkauf": (r"t-shirt|trikot|fanartikel", None),
}
_STAND_ZU = (r"geschlossen|geschossen|nicht alle stände geöffnet", r"gästesektor|geschlossenem|nach dem spiel|nach der pause")
_ALLE_OFFEN = r"all[eä] stände (?:offen|geöffnet)"
_MOBIL = r"runner|bauchl[aä]d|bierrucks[aä]ck|bierbauchl"
OPERATIVE_HINWEISE = ["stand_geschlossen", "mobiler_verkauf_reduziert", "personalmangel", "technische_probleme"]
MOBIL_STATUS = ("im Einsatz", "eingeschränkt", "nicht im Einsatz", "keine Angabe")


def _saetze(bemerkung) -> list[str]:
    """Teilsätze (Trennung an Zeilenumbruch, «/», «;» und Satzende – nicht nach «inkl.», «exkl.», «ca.»)."""
    return [s.strip() for s in re.split(r"[\n/;]|(?<=[.!])(?<!inkl\.)(?<!exkl\.)(?<!ca\.)\s", text(bemerkung).lower())
            if s.strip()]


def _operativ(bemerkung: str, muster: str, ausnahme: str | None) -> bool:
    for satz in _saetze(bemerkung):
        if re.search(muster, satz) and not (ausnahme and re.search(ausnahme, satz)):
            return True
    return False


def _sektoren(fragment: str) -> set[str]:
    """Sektorbuchstaben B, C, D aus einem Textstück («Runner C und B», «Sektor B, C, D»)."""
    return {s.upper() for s in re.findall(r"\b([bcd])\b", fragment)}


def _ausser_liste(satz: str) -> tuple[list[str], str]:
    """«Alle Stände geöffnet ausser Bierbar A3, Bierbar C und Runner B, C, D» → (["bierbar a3", "bierbar c"], " b, c, d").

    Liefert die geschlossenen Stände und den Textteil nach dem ersten Runner/Bauchladen (dessen Sektoren). Ohne
    «ausser»-Liste: ([], "").
    """
    m = re.search(_ALLE_OFFEN + r"\s+ausser\s+(.+)", satz)
    if not m:
        return [], ""
    teile = re.split(r"\b(?:" + _MOBIL + r")\w*", m.group(1), maxsplit=1)
    staende = [e.strip() for e in re.split(r",|\bund\b", teile[0]) if e.strip()]
    mobil = teile[1] if len(teile) > 1 else ""
    if len(teile) > 1 and not mobil.strip():
        mobil = " "          # Runner ohne Sektorangabe
    return staende, mobil


def mobiler_verkauf(bemerkung) -> dict:
    """Einsatz des mobilen Verkaufs (Bier-Runner, Bauchläden, Bierrucksäcke) laut Catering-Bemerkung.

    Nur ausdrückliche Angaben zählen. «nicht im Einsatz», «keine Bierbauchläden», Runner in «Alle Stände geöffnet
    ausser Runner B, C, D» oder in der Liste «folgende Stände waren geschlossen: …» → nicht im Einsatz (je Sektor);
    «im Einsatz» bzw. «inkl. Bauchläden im Sektor B, C, D» → im Einsatz; «nur einer … im Einsatz» → eingeschränkt.
    Kassenzuteilungen wie «Runner C = Stand C4» sind keine Einsatzangabe.

    Rückgabe: status (im Einsatz | eingeschränkt | nicht im Einsatz | keine Angabe) sowie die Sektoren mit
    bzw. ohne Einsatz («alle», wenn die Bemerkung keinen Sektor nennt).
    """
    t = text(bemerkung).lower()
    ja: set[str] = set()
    nein: set[str] = set()
    teilweise = False
    for m in re.finditer(r"geschlossen:\s*/?\s*([^/\n]+)", t):
        k = re.search(r"(?:runner|bauchl\w*)(.*)", m.group(1))
        if k:
            nein |= _sektoren(k.group(1)) or {"alle"}
    for satz in _saetze(t):
        staende, mobil = _ausser_liste(satz)
        if staende or mobil:
            if mobil:
                nein |= _sektoren(mobil) or {"alle"}
            continue
        if not re.search(_MOBIL, satz):
            continue
        if re.search(r"nicht im einsatz|keine\s+(?:bier)?bauchl", satz):
            nein |= _sektoren(re.split(r"nicht im einsatz", satz)[0]) or {"alle"}
        elif re.search(r"nur einer", satz) and "im einsatz" in satz:
            teilweise = True
        elif "im einsatz" in satz or re.search(r"inkl\.?\s+bauchl", satz):
            ja |= _sektoren(satz) or {"alle"}
    if nein and ("alle" in nein or nein >= {"B", "C", "D"}) and not ja and not teilweise:
        status = "nicht im Einsatz"
    elif nein or teilweise:
        status = "eingeschränkt"
    elif ja:
        status = "im Einsatz"
    else:
        status = "keine Angabe"
    return {"mobil_status": status, "mobil_sektoren_ja": ", ".join(sorted(ja)),
            "mobil_sektoren_nein": ", ".join(sorted(nein))}


def codiere_bemerkung(bemerkung) -> dict:
    """Alle operativen Merkmale einer Catering-Bemerkung (eine Stelle, damit Regeln und Tests übereinstimmen)."""
    out = {flag: _operativ(bemerkung, muster, ausnahme) for flag, (muster, ausnahme) in _OPERATIV.items()}
    saetze = _saetze(bemerkung)
    ausser_staende = [e for s in saetze for e in _ausser_liste(s)[0]]
    out["stand_geschlossen"] = _operativ(bemerkung, *_STAND_ZU) or bool(ausser_staende)
    out["alle_staende_offen"] = any(re.search(_ALLE_OFFEN, s) for s in saetze) and not ausser_staende
    out.update(mobiler_verkauf(bemerkung))
    out["mobiler_verkauf_reduziert"] = out["mobil_status"] in ("eingeschränkt", "nicht im Einsatz")
    return out


def _norm_header(h) -> str:
    t = str(h).replace("\n", " ").lower()
    t = re.sub(r"\s+", " ", t).strip()
    return re.sub(r"(mwst\.?)\d+$", r"\1", t)


def _wettbewerb(wert) -> str:
    t = re.sub(r"\s+", " ", text(wert).lower()).strip()
    if "abgesagt" in t:
        return "SL abgesagt"
    return WETTBEWERB_MAP.get(t, "Andere")


def _tabellenbereich(ws) -> tuple[int, int, int, int]:
    """(min_col, min_row, max_col, max_row) der Haupttabelle des Saisonblatts."""
    refs = []
    for _, ref in ws.tables.items():
        ref = ref if isinstance(ref, str) else ref.ref
        refs.append(range_boundaries(ref))
    if refs:
        return min(refs, key=lambda b: b[0])
    return 1, 3, ws.max_column, ws.max_row


def lade_public_catering() -> tuple[pd.DataFrame, pd.DataFrame]:
    """Liefert (events, staende_2122).

    ``events``: eine Zeile pro Event/Spiel aller Saisonblätter ab 2018/19 mit harmonisierten Spalten.
    ``staende_2122``: Umsätze der Einzelstände (Contrailer/Bier) aus dem Blatt 2021-2022 (lang).
    """
    wb_v = openpyxl.load_workbook(config.CATERING_FILE, data_only=True)
    wb_f = openpyxl.load_workbook(config.CATERING_FILE, data_only=False)
    events, staende = [], []
    for blatt in wb_v.sheetnames:
        if not re.fullmatch(r"\d{4}-\d{4}", blatt):
            continue
        ws_v, ws_f = wb_v[blatt], wb_f[blatt]
        c0, r0, c1, r1 = _tabellenbereich(ws_f)
        header = {c: _norm_header(ws_v.cell(r0, c).value) for c in range(c0, c1 + 1) if ws_v.cell(r0, c).value}
        mapping, stand_cols = {}, {}
        for c, h in header.items():
            for muster, name in _SPALTEN:
                if re.search(muster, h) and name not in mapping.values():
                    mapping[c] = name
                    break
            else:
                if blatt == "2021-2022" and re.search(_STAND_2122, h):
                    stand_cols[c] = h
        for r in range(r0 + 1, r1 + 1):
            werte = {name: ws_v.cell(r, c).value for c, name in mapping.items()}
            if all(ist_leer(v) for v in werte.values()) or (ist_leer(werte.get("datum")) and ist_leer(werte.get("spiel"))):
                continue
            if str(werte.get("datum", "")).strip().lower().startswith(("total", "einnahmen")):
                continue
            werte["public_netto_formel"] = ws_f.cell(r, [c for c, n in mapping.items() if n == "public_netto"][0]).value \
                if "public_netto" in mapping.values() else None
            werte.update({"blatt": blatt, "zeile": r})
            events.append(werte)
            for c, h in stand_cols.items():
                staende.append({"blatt": blatt, "zeile": r, "stand_spalte": h, "wert": ws_v.cell(r, c).value})

    df = pd.DataFrame(events)
    df["datum_text"] = df["datum"].astype(str)
    df["datum"] = df["datum"].map(parse_datum)
    df = korrekturen.anwenden(df, "Catering", {"Datum": "datum"})
    df["saison_blatt"] = df["blatt"].str.replace(r"(\d{4})-\d{2}(\d{2})", r"\1/\2", regex=True)
    # Saison aus dem Blatt (nicht aus dem Datum): 2019/20 dauerte wegen COVID bis August 2020
    df["saison"] = df["saison_blatt"]
    df["anpfiff"] = df["anpfiff_text"].map(parse_anpfiff)
    df["wettbewerb"] = df["wettbewerb_text"].map(_wettbewerb)
    num_cols = [c for c in df.columns if c.startswith(("kanal_", "umsatz_", "kf_", "bon_"))] + \
               ["public_netto", "transaktionen", "gaeste_catering"]
    for c in num_cols:
        if c in df.columns:
            df[c] = df[c].map(zahl_oder_nan)
    if "public_netto_formel" in df.columns:
        df["public_netto_formel"] = df["public_netto_formel"].map(
            lambda f: f if isinstance(f, str) and f.startswith("=") else None)
    ist_abzug = df["public_netto_formel"].map(_formel_ist_abzug)
    df["formel_ist"] = [x[0] for x in ist_abzug]
    df["formel_abzug_vip"] = [x[1] for x in ist_abzug]

    # Kennzahlen neu berechnen (nicht die Blattwerte übernehmen)
    pn = df["public_netto"].where(df["public_netto"] > 0)
    tx = df["transaktionen"].where(df["transaktionen"] > 0)
    df["kf_inkl"] = df["umsatz_inkl"] / pn
    df["kf_exkl"] = df["umsatz_exkl"] / pn
    df["bons_pro_anwesende"] = tx / pn
    df["bon_inkl"] = df["umsatz_inkl"] / tx
    df["bon_exkl"] = df["umsatz_exkl"] / tx
    df["mwst_faktor_implizit"] = df["umsatz_inkl"] / df["umsatz_exkl"]
    df["mwst_faktor_erwartet"] = df["datum"].map(lambda d: 1 + mwst_satz(d) if not pd.isna(d) else np.nan)
    codes = pd.DataFrame([codiere_bemerkung(b) for b in df["bemerkung"]], index=df.index)
    for c in codes.columns:
        df[c] = codes[c]
    df["operativer_hinweis"] = df[OPERATIVE_HINWEISE].any(axis=1)

    st = pd.DataFrame(staende)
    if not st.empty:
        st["wert"] = st["wert"].map(zahl_oder_nan)
        st = st.merge(df[["blatt", "zeile", "datum", "spiel", "wettbewerb"]], on=["blatt", "zeile"], how="left")
    _pruefungen(df)
    return df, st


def _formel_ist_abzug(formel) -> tuple[float, float]:
    """'=16908-707' -> (16908, 707); '=16462-(296+24)' -> (16462, 320)."""
    if not isinstance(formel, str):
        return np.nan, np.nan
    m = re.fullmatch(r"=\s*(\d+)\s*-\s*\(?([\d+\s]+)\)?\s*", formel)
    if not m:
        return np.nan, np.nan
    return float(m.group(1)), float(sum(int(x) for x in re.findall(r"\d+", m.group(2))))


def _pruefungen(df: pd.DataFrame) -> None:
    kern = df[df["wettbewerb"].isin(config.KERN_WETTBEWERBE) & (df["saison"] >= config.BASELINE_AB_SAISON)]
    for _, r in kern[kern["datum"].isna()].iterrows():
        befund("Catering", "hoch", f"Blatt {r['blatt']} Zeile {r['zeile']}",
               f"Datum «{r['datum_text']}» nicht lesbar.", "Spiel nicht zuordenbar.", "Manuell prüfen.")
    # Netto-Logik: bis 2019/20 pauschal inkl./1.077, ab 2020/21 effektive Mischsätze (reduziert + normal)
    alle = df[df["wettbewerb"].isin(config.KERN_WETTBEWERBE) & df["mwst_faktor_implizit"].notna()]
    pauschal = alle[(alle["mwst_faktor_implizit"] - 1.077).abs() < 0.0005].groupby("saison").size()
    if not pauschal.empty:
        befund("Catering", "mittel", "Saisonblätter " + ", ".join(pauschal.index),
               "Umsatz exkl. MwSt wurde pauschal als inkl./1.077 gerechnet; ab 2020/21 enthalten die Netto-Werte "
               "effektive Mischsätze (reduzierter Satz für Take-away und Normalsatz, effektiv ca. 4.5–7.9 %).",
               "Netto-Werte vor 2020/21 sind gegenüber später um rund 2 % zu tief und nicht direkt vergleichbar.",
               "Langfristige Vergleiche (Trend ab 2018/19) auf Basis inkl. MwSt; Netto nur ab 2021/22.")
    misch = kern[kern["saison"] >= "2020/21"]
    for _, r in misch[(misch["mwst_faktor_implizit"] < 1.04) | (misch["mwst_faktor_implizit"] > 1.075)].iterrows():
        befund("Catering", "tief", f"Blatt {r['blatt']} Zeile {r['zeile']} ({r['datum']:%d.%m.%Y})",
               f"Effektiver MwSt-Faktor {r['mwst_faktor_implizit']:.4f} liegt ausserhalb des üblichen Bereichs 1.04–1.075.",
               "Netto-Wert dieses Spiels eventuell mit anderer Steuerlogik erfasst.", "Übernommen; markiert.")


def lade_entwicklung() -> pd.DataFrame:
    """Blatt «Entwicklung»: Saison × Wettbewerb wie vom Caterer zusammengefasst (für Abgleiche).

    Die Saison einer Total-Zeile wird aus der Position (vorangehende Saisonzeilen) bestimmt, weil die
    Beschriftung der letzten Total-Zeile falsch ist («25/26» bei Werten 2026/27).
    """
    ws = openpyxl.load_workbook(config.CATERING_FILE, data_only=True)["Entwicklung"]
    rows, aktuelle_saison = [], None
    for r in range(4, ws.max_row + 1):
        v = [ws.cell(r, c).value for c in range(1, 13)]
        if ist_leer(v[0]):
            continue
        label = str(v[0]).strip()
        if not ist_leer(v[1]):
            aktuelle_saison = f"{str(v[1])[:4]}/{str(v[1])[-2:]}"
        m = re.search(r"(\d{2})/(\d{2})\s*$", label)
        saison_label = f"20{m.group(1)}/{m.group(2)}" if m else None
        rows.append({"zeile": r, "label": label, "saison": aktuelle_saison, "saison_label": saison_label,
                     "events": zahl_oder_nan(v[2]), "anwesende": zahl_oder_nan(v[3]), "umsatz_inkl": zahl_oder_nan(v[4]),
                     "umsatz_exkl": zahl_oder_nan(v[5]), "kf_inkl_blatt": zahl_oder_nan(v[8]),
                     "kf_exkl_blatt": zahl_oder_nan(v[9]), "bon_inkl_blatt": zahl_oder_nan(v[10])})
    df = pd.DataFrame(rows)
    falsch = df[df["saison_label"].notna() & (df["saison_label"] != df["saison"])]
    for _, x in falsch.iterrows():
        befund("Catering", "tief", f"Blatt «Entwicklung» Zeile {x['zeile']}",
               f"Beschriftung «{x['label']}» gehört zu den Werten der Saison {x['saison']}.",
               "Verwechslungsgefahr beim Ablesen der Saisontotale.", "Saison aus der Zeilenposition abgeleitet.")
    return df


def lade_kiesplatz() -> pd.DataFrame:
    """Kiesplatz-Abrechnungen 21/22–26/27, lang: eine Zeile pro Event × Verkaufsstelle (inkl. TOTAL)."""
    rows = []
    for pfad in sorted(config.CATERING_DIR.glob(config.KIESPLATZ_GLOB)):
        m = re.search(r"Saison (\d{2})-(\d{2})", pfad.name)
        saison_datei = f"20{m.group(1)}/{m.group(2)}" if m else None
        blatt = f"Saison {m.group(1)}-{m.group(2)}" if m else pfad.stem
        ws = openpyxl.load_workbook(pfad, data_only=True)["Abrechnung Kiesplatz"]
        h3 = {c: _norm_header(ws.cell(3, c).value) for c in range(1, ws.max_column + 1) if ws.cell(3, c).value}
        col = {name: next((c for c, h in h3.items() if h == name), None)
               for name in ("datum", "kick-off", "beginn pause", "event")}
        gruppen = [(c, str(ws.cell(2, c).value).strip()) for c in range(1, ws.max_column + 1) if ws.cell(2, c).value]
        for i, (start, name) in enumerate(gruppen):
            ende = gruppen[i + 1][0] - 1 if i + 1 < len(gruppen) else ws.max_column
            sub = {h3.get(c, ""): c for c in range(start, ende + 1)}
            red = next((c for h, c in sub.items() if re.fullmatch(r"brutto 2\.\d%", h)), None)
            norm = next((c for h, c in sub.items() if re.fullmatch(r"brutto (7\.7|8\.1)%", h)), None)
            satz_label = next((h for h in sub if re.fullmatch(r"brutto (7\.7|8\.1)%", h)), "")
            for r in range(4, ws.max_row + 1):
                a = ws.cell(r, 1).value
                d = ws.cell(r, col["datum"]).value
                if (isinstance(a, str) and a.strip().lower().startswith("total")) or \
                        (isinstance(d, str) and d.strip().lower().startswith("total")):
                    break
                event = ws.cell(r, col["event"]).value
                if ist_leer(event) and ist_leer(d):
                    continue
                rows.append({
                    "datei": pfad.name, "blatt": blatt, "zeile": r, "saison_datei": saison_datei,
                    "datum_text": str(d), "datum": parse_datum(d),
                    "anpfiff": parse_anpfiff(ws.cell(r, col["kick-off"]).value),
                    "beginn_pause": parse_anpfiff(ws.cell(r, col["beginn pause"]).value),
                    "event": event, "verkaufsstelle": name, "ist_total": name.upper() == "TOTAL",
                    "satz_normal_beschriftung": satz_label,
                    "brutto_reduziert": zahl_oder_nan(ws.cell(r, red).value) if red else np.nan,
                    "brutto_normal": zahl_oder_nan(ws.cell(r, norm).value) if norm else np.nan,
                    "brutto_total": zahl_oder_nan(ws.cell(r, sub.get("total brutto")).value) if sub.get("total brutto") else np.nan,
                    "netto_total": zahl_oder_nan(ws.cell(r, sub.get("total netto")).value) if sub.get("total netto") else np.nan,
                })
    df = pd.DataFrame(rows)
    df = korrekturen.anwenden(df, "Kiesplatz", {"Datum": "datum"})
    df["saison"] = df["saison_datei"].fillna(df["datum"].map(saison_von))
    _pruefe_kiesplatz_mwst(df)
    return df


def _pruefe_kiesplatz_mwst(df: pd.DataFrame) -> None:
    """Prüft, mit welchen MwSt-Divisoren die Netto-Werte gerechnet wurden (Beschriftung vs. Formel)."""
    t = df[df["ist_total"] & (df["brutto_total"] > 0)].copy()
    t["netto_alt"] = t["brutto_reduziert"] * (0.8 / 1.025 + 0.2 / 1.077) + t["brutto_normal"] / 1.077
    t["netto_neu"] = t["brutto_reduziert"] * (0.8 / 1.026 + 0.2 / 1.081) + t["brutto_normal"] / 1.081
    for saison, g in t.groupby("saison_datei"):
        alt = (g["netto_total"] - g["netto_alt"]).abs().mean()
        neu = (g["netto_total"] - g["netto_neu"]).abs().mean()
        beschriftung = g["satz_normal_beschriftung"].iloc[0]
        if "8.1" in beschriftung and alt < neu:
            befund("Kiesplatz", "tief", f"Abrechnung Kiesplatz {saison}",
                   "Netto-Formeln teilen durch 1.025/1.077 (MwSt bis 2023), Spalten sind aber mit 2.6 %/8.1 % beschriftet.",
                   "Netto leicht überschätzt (ca. 0.3–0.4 %); Brutto unberührt.",
                   "Für Vergleiche Brutto verwenden; Formel an Sandro melden.")


def lade_artikel() -> pd.DataFrame:
    """Artikelauswertung Meisterschaft: Gruppe/Artikel × Saison (Menge, Umsatz netto, Anteil)."""
    ws = openpyxl.load_workbook(config.ARTIKEL_FILE, data_only=True)["Artikelauswertung"]
    rows, ebene, saison_cols, spiele = [], None, {}, {}
    for r in range(1, ws.max_row + 1):
        a = ws.cell(r, 1).value
        a_txt = str(a).strip() if not ist_leer(a) else ""
        if a_txt in ("Gruppe", "Artikel"):
            ebene = a_txt
            continue
        heads = {c: str(ws.cell(r, c).value) for c in range(2, ws.max_column + 1)
                 if isinstance(ws.cell(r, c).value, str) and re.match(r"Saison \d{4}/\d{4}", str(ws.cell(r, c).value))}
        if heads:
            saison_cols = {c: f"{h[7:11]}/{h[-2:]}" for c, h in heads.items()}
            continue
        if a_txt == "Anzahl Spiele":
            for c, s in saison_cols.items():
                spiele[s] = zahl_oder_nan(ws.cell(r, c).value)
            continue
        if not a_txt or a_txt in ("Name", "Total") or ebene is None:
            continue
        for c, s in saison_cols.items():
            menge = zahl_oder_nan(ws.cell(r, c).value)
            umsatz = zahl_oder_nan(ws.cell(r, c + 2).value)
            if np.isnan(menge) and np.isnan(umsatz):
                continue
            rows.append({"ebene": ebene, "name": a_txt, "saison": s, "zeile": r, "menge": menge,
                         "menge_pro_spiel_blatt": zahl_oder_nan(ws.cell(r, c + 1).value),
                         "umsatz_netto": umsatz, "umsatz_netto_pro_spiel_blatt": zahl_oder_nan(ws.cell(r, c + 3).value),
                         "anteil_blatt": zahl_oder_nan(ws.cell(r, c + 4).value)})
    df = pd.DataFrame(rows)
    df["spiele"] = df["saison"].map(spiele)
    aktiv = df.groupby("saison")["menge"].transform("sum") > 0
    return _harmonisiere_artikel(df[aktiv].reset_index(drop=True))


# --------------------------------------------------------------------------------------------
# Artikel: MwSt-Klasse und einheitliche Brutto-Basis
# --------------------------------------------------------------------------------------------
# Alkoholische Getränke unterliegen immer dem Normalsatz, Speisen und alkoholfreie Getränke (Take-away) dem
# reduzierten Satz. Die Namensregel reproduziert die Gruppe «Alkoholische Getränke» in allen Saisons frankengenau
# (Test in qa.importtests). «Kafi Lutz» = Kaffee mit Schnaps; «Schüga Pitcher» = Bier; «Punsch» ist laut Erlös je
# Einheit reduziert besteuert (alkoholfrei).
_ALKOHOL = r"\bbier\b|bräu|wein|prosecco|longdrink|cocktail|cider|kafi lutz|pitcher"
_KEIN_ALKOHOL = r"alk\.?-?\s*frei|bretzel"


def artikel_mwst_klasse(name: str, ebene: str = "Artikel") -> str:
    """'normal' (Normalsatz, alkoholisch) oder 'reduziert' (Speisen, alkoholfreie Getränke)."""
    t = text(name).lower()
    if ebene == "Gruppe":
        return "normal" if t.startswith("alkoholische") else "reduziert"
    return "normal" if re.search(_ALKOHOL, t) and not re.search(_KEIN_ALKOHOL, t) else "reduziert"


def lade_artikel_basis() -> dict[str, str]:
    """Basis der Umsatzspalte je Saison laut overrides/artikel_basis.csv (brutto | netto)."""
    if not config.ARTIKEL_BASIS_FILE.exists():
        return {}
    b = pd.read_csv(config.ARTIKEL_BASIS_FILE, sep=";", dtype=str, encoding="utf-8")
    return dict(zip(b["saison"].str.strip(), b["basis"].str.strip().str.lower()))


def _saetze_mwst(saison: str) -> tuple[float, float] | None:
    """(Normalsatz, reduzierter Satz) einer Saison; None, wenn der Satzwechsel 1.1.2024 in die Saison fällt."""
    start = int(saison[:4])
    if start >= 2024:
        return config.MWST_NEU, config.MWST_REDUZIERT_NEU
    if start + 1 <= 2023:
        return config.MWST_ALT, config.MWST_REDUZIERT_ALT
    return None


def _harmonisiere_artikel(df: pd.DataFrame) -> pd.DataFrame:
    """Ergänzt MwSt-Klasse und den Umsatz auf einheitlicher Brutto-Basis (inkl. MwSt).

    Die Spalte «Umsatz Netto» der Artikelauswertung ist nicht über alle Saisons gleich definiert: 2023/24 und
    2024/25 enthalten Bruttowerte (Bier 4dl CHF 6.00 je Einheit; Summe ≈ Payfix inkl.), 2025/26 Nettowerte
    (Bier CHF 5.54 = 5.98 brutto / 1.081; jeder Wert × 1.081 bzw. × 1.026 ergibt wieder einen runden Bruttobetrag).
    Basis je Saison: overrides/artikel_basis.csv. Brutto ist die gemeinsame Basis, weil sie für 2025/26 exakt
    rückrechenbar ist (eine Netto-Basis für 2023/24 bräuchte die Aufteilung vor/nach dem Satzwechsel).
    """
    df = df.copy()
    df["mwst_klasse"] = [artikel_mwst_klasse(n, e) for n, e in zip(df["name"], df["ebene"])]
    basis = lade_artikel_basis()
    df["basis_datei"] = df["saison"].map(lambda s: basis.get(s, "unbekannt"))
    faktor = []
    for s, b, k in zip(df["saison"], df["basis_datei"], df["mwst_klasse"]):
        if b == "brutto":
            faktor.append(1.0)
        elif b == "netto" and _saetze_mwst(s):
            satz_normal, satz_reduziert = _saetze_mwst(s)
            faktor.append(1 + (satz_normal if k == "normal" else satz_reduziert))
        else:
            faktor.append(np.nan)
    df["umsatz_brutto"] = df["umsatz_netto"] * np.array(faktor)
    df["erloes_pro_einheit_brutto"] = df["umsatz_brutto"] / df["menge"].where(df["menge"] > 0)
    for s in sorted(df.loc[df["umsatz_brutto"].isna() & df["umsatz_netto"].notna(), "saison"].unique()):
        befund("Catering", "mittel", f"Artikelauswertung Saison {s}",
               "Basis der Umsatzspalte (brutto/netto) für diese Saison nicht festgelegt oder nicht rückrechenbar.",
               "Saison ohne einheitliche Basis; Sortimentsanteile nicht mit anderen Saisons vergleichbar.",
               "In overrides/artikel_basis.csv ergänzen (Beleg: Erlös je Einheit Bier, Summe vs. Payfix inkl./exkl.).")
    return df

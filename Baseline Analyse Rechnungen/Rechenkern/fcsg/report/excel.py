"""Schreibt alle Ergebnistabellen in eine formatierte Excel-Arbeitsmappe (mit Inhaltsverzeichnis)."""
from __future__ import annotations

import re
from pathlib import Path

import numpy as np
import pandas as pd

PROZENT = re.compile(r"(^|_)(anteil|quote|r2|zks_|abweichung_scans|stabil|verhaeltnis_)|noshow_(quote|einzel|rest|gesamt)"
                     r"|eintrittsquote|uebergabequote|^anteil|_anteil|korrelation|r_kf|abo_anwesenheit|scans_je_platz|wiederbesetzung"
                     r"|abdeckung_pi|^s_(brutto|netto)$|proxy_s_|alkoholanteil_brutto|einzel_anwesenheit|^r_(unten|oben)$|r_annahme")
CHF = re.compile(r"umsatz|chf|^kf_|_kf_|kf_(inkl|exkl)|^bon_|_bon_|preis|brutto|netto(_|$)|erloes|kiesplatz_chf|beobachtet_kf|erwartet_kf")
GANZ = re.compile(r"^(spiele|tickets|abos|zeilen|besucher|soll|ist|ist_vip|ist_gaeste|zweitmarkt|einzel|scans|n|events|menge|anzahl|"
                  r"pflichtspiele|transaktionen|public_netto)(_|$)")


def _bereinigen(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    for c in out.columns:
        s = out[c]
        if isinstance(s.dtype, pd.BooleanDtype):
            out[c] = s.astype(object).where(s.notna(), None)
        elif isinstance(s.dtype, (pd.Int64Dtype, pd.Float64Dtype)):
            out[c] = s.astype(float)
        elif isinstance(s.dtype, pd.CategoricalDtype):
            out[c] = s.astype(str)
        elif pd.api.types.is_datetime64_any_dtype(s):
            if getattr(s.dt, "tz", None) is not None:
                s = s.dt.tz_localize(None)
            zeit = s.dropna()
            if len(zeit) and ((zeit.dt.hour != 0) | (zeit.dt.minute != 0)).any():
                out[c] = s.dt.strftime("%d.%m.%Y %H:%M").where(s.notna(), None)   # mit Uhrzeit als Text
            else:
                out[c] = s
        elif s.dtype == object:
            out[c] = s.map(lambda v: None if v is pd.NA else v)
    return out


def _format_fuer(spalte: str, s: pd.Series, fmt: dict) -> object:
    name = str(spalte).lower()
    if pd.api.types.is_datetime64_any_dtype(s):
        zeit = s.dropna()
        hat_zeit = len(zeit) and ((zeit.dt.hour != 0) | (zeit.dt.minute != 0)).any()
        return fmt["datumzeit"] if hat_zeit else fmt["datum"]
    if not pd.api.types.is_numeric_dtype(s) or pd.api.types.is_bool_dtype(s):
        return fmt["text"]
    if name.startswith(("z_", "p_wert", "ln_", "koeffizient", "beta_", "rmse", "smearing", "elastizitaet")):
        return fmt["dez3"]
    if name.endswith("_pct") or "effekt" in name or name.startswith(("ki95", "ki90")) or "abweichung_von_erwartung" in name:
        return fmt["dez1"]
    if PROZENT.search(name):
        return fmt["prozent"]
    if "min_vor_anpfiff" in name or name.endswith(("_min", "_tage", "_c", "_mm", "_kmh")) or "verweil" in name or "_je_100_" in name:
        return fmt["dez1"]
    if CHF.search(name):
        return fmt["chf"]
    if GANZ.search(name):
        return fmt["ganz"]
    werte = s.dropna()
    if len(werte) and np.all(np.mod(werte, 1) == 0) and werte.abs().max() > 100:
        return fmt["ganz"]
    return fmt["dez3"]


def schreibe_excel(pfad: Path, blaetter: list[tuple[str, pd.DataFrame, str]], titel: str | None = None,
                   untertitel: str | None = None, zusatz_vorne: list | None = None) -> None:
    """Schreibt Tabellen mit Inhaltsverzeichnis. ``zusatz_vorne``: Liste (Blattname, Beschreibung, Funktion(wb, ws, fmt))
    für frei gestaltete Blätter direkt nach dem Inhaltsverzeichnis (z.B. Rechner). Ohne Zusatzargumente unverändert."""
    pfad.parent.mkdir(parents=True, exist_ok=True)
    zusatz_vorne = zusatz_vorne or []
    with pd.ExcelWriter(pfad, engine="xlsxwriter", datetime_format="dd.mm.yyyy", date_format="dd.mm.yyyy") as xw:
        wb = xw.book
        fmt = {
            "kopf": wb.add_format({"bold": True, "bg_color": "#0B6E4F", "font_color": "white", "text_wrap": True,
                                   "valign": "top", "border": 1}),
            "text": wb.add_format({"text_wrap": False, "valign": "top"}),
            "wrap": wb.add_format({"text_wrap": True, "valign": "top"}),
            "prozent": wb.add_format({"num_format": "0.0%"}), "chf": wb.add_format({"num_format": "#,##0.00"}),
            "ganz": wb.add_format({"num_format": "#,##0"}), "dez1": wb.add_format({"num_format": "0.0"}),
            "dez3": wb.add_format({"num_format": "0.000"}), "datum": wb.add_format({"num_format": "dd.mm.yyyy"}),
            "datumzeit": wb.add_format({"num_format": "dd.mm.yyyy hh:mm"}),
            "titel": wb.add_format({"bold": True, "font_size": 14}),
            "link": wb.add_format({"font_color": "#0B6E4F", "underline": 1}),
        }
        # Inhaltsverzeichnis
        inhalt = wb.add_worksheet("00_Inhalt")
        inhalt.write(0, 0, titel or "FCSG «Untapped Business» – Phase 1: Datenverknüpfung & Kontextbereinigung", fmt["titel"])
        inhalt.write(1, 0, untertitel or "Nur Aggregate, keine Personendaten. Lesehilfe: Methodennotiz_Phase1.md im selben Ordner.")
        for j, h in enumerate(["Blatt", "Inhalt", "Zeilen", "Spalten"]):
            inhalt.write(3, j, h, fmt["kopf"])
        i = 4
        for name, text, _ in zusatz_vorne:
            inhalt.write_url(i, 0, f"internal:'{name}'!A1", fmt["link"], name)
            inhalt.write(i, 1, text, fmt["wrap"])
            i += 1
        for name, df, text in blaetter:
            inhalt.write_url(i, 0, f"internal:'{name}'!A1", fmt["link"], name)
            inhalt.write(i, 1, text, fmt["wrap"])
            inhalt.write(i, 2, len(df))
            inhalt.write(i, 3, df.shape[1])
            i += 1
        for name, _, schreiber in zusatz_vorne:
            schreiber(wb, wb.add_worksheet(name), fmt)
        inhalt.set_column(0, 0, 30)
        inhalt.set_column(1, 1, 110)
        inhalt.set_column(2, 3, 9)
        inhalt.freeze_panes(4, 0)

        for name, df, _ in blaetter:
            d = _bereinigen(df)
            d.to_excel(xw, sheet_name=name, index=False, startrow=0)
            ws = xw.sheets[name]
            for j, c in enumerate(d.columns):
                ws.write(0, j, str(c), fmt["kopf"])
                inhalt_laenge = d[c].astype(str).str.len().quantile(0.9) if len(d) else 8
                breite = min(max(len(str(c)) * 0.9, inhalt_laenge, 8), 60)
                f = _format_fuer(c, d[c], fmt)
                ws.set_column(j, j, breite + 1, f)
            ws.set_row(0, 45)
            ws.freeze_panes(1, 0)
            if len(d):
                ws.autofilter(0, 0, len(d), max(len(d.columns) - 1, 0))

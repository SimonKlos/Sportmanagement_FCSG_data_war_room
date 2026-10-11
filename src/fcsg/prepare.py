"""Bereinigung und Export der echten FCSG-Daten nach ``data/clean/<run_id>/``.

Datenmodus ``release_aggregates`` (D-001 c, Entscheid 10.10.2026):

- **Aggregat-Quellen** ohne Personenbezug (Zuschauerhistorie, Public Catering, Kiesplatz, Artikel,
  Spielkontext) werden bereinigt und mit einheitlichen englischen Spaltennamen übernommen.
- **Personenbezogene Quellen** (Einzeltickets-Exporte, Ticket-CSVs, Saisonabos, Zutritte) werden
  ausschliesslich **aggregiert** exportiert. Es werden nur Spalten einer Positivliste geladen;
  Name, Anrede, Geburtstag, Alter, Geschlecht, PLZ, Land, Kunden-Nr., Sitz/Reihe, Seatinfo, TicketData
  werden nie gelesen. Ticket-/Rechnungsschlüssel werden nur intern zum Zählen verwendet und nie ausgegeben.
- Jede Ausgabetabelle wird gegen die Personenbezug-Heuristik geprüft; jede Aggregation auf Summenerhalt.
- **Scope (D-016, 11.10.2026):** Frauen-Daten fallen ganz weg – Frauen-Dateien werden nicht gelesen,
  Frauen-Events aus gemischten Quellen entfernt (``drop_women``).
- **Schulferien (D-017 b):** vor 2026/27 durch recherchierte Werte ersetzt (``apply_school_holidays``).

Fachliche Definitionen (SOLL, Public Netto, Umsatzbasis) werden hier **nicht** festgelegt: Werte werden
so übernommen, wie die Quelle sie liefert; berichtete Kennzahlen tragen den Suffix ``_reported``.
"""

from __future__ import annotations

import datetime as dt
import hashlib
import json
import platform
import re
import secrets
from dataclasses import dataclass, field
from importlib.metadata import version
from pathlib import Path
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd

from fcsg import __version__
from fcsg.inventory import personal_category

ENGINE = "calamine"


class PrivacyError(RuntimeError):
    """Eine Ausgabetabelle enthält eine Spalte mit Personenbezug."""


# ----------------------------------------------------------------------------------------------------
# Hilfsfunktionen (Parsing)
# ----------------------------------------------------------------------------------------------------

def norm_text(s) -> str:
    """Kleinbuchstaben, Umlaute aufgelöst, Mehrfach-Leerzeichen entfernt."""
    t = str(s).lower().replace("ä", "ae").replace("ö", "oe").replace("ü", "ue").replace("ß", "ss")
    return " ".join(t.replace("\n", " ").split())


def slug(s) -> str:
    return re.sub(r"[^a-z0-9]+", "_", norm_text(s)).strip("_")


def parse_chf(value) -> float:
    """``'5,00\\xa0CHF'`` → 5.0; leer/ungültig → NaN."""
    if value is None or (isinstance(value, float) and np.isnan(value)):
        return np.nan
    if isinstance(value, (int, float)):
        return float(value)
    s = str(value).replace("\xa0", " ").replace("CHF", "").replace("'", "").replace("’", "").strip()
    if not s:
        return np.nan
    s = s.replace(".", "").replace(",", ".") if re.search(r",\d{1,2}$", s) else s.replace(",", "")
    try:
        return float(s)
    except ValueError:
        return np.nan


def fmt_time(value) -> str | None:
    """Zeitangaben vereinheitlichen zu ``HH:MM`` (time, '20:30', 19.3 = 19:30)."""
    if value is None or (isinstance(value, float) and np.isnan(value)):
        return None
    if isinstance(value, (dt.time, dt.datetime)):
        return f"{value.hour:02d}:{value.minute:02d}"
    if isinstance(value, (int, float)):
        h = int(value)
        m = int(round((float(value) - h) * 100))
        return f"{h:02d}:{m:02d}" if 0 <= h < 24 and 0 <= m < 60 else None
    m = re.match(r"^\s*(\d{1,2})[:.](\d{2})", str(value))
    return f"{int(m.group(1)):02d}:{m.group(2)}" if m else None


def to_date(value) -> dt.date | None:
    """Datum aus datetime/date/'dd.mm.yyyy'/'yyyy-mm-dd'; sonst None."""
    if isinstance(value, dt.datetime):
        return value.date()
    if isinstance(value, dt.date):
        return value
    if isinstance(value, pd.Timestamp):
        return value.date()
    if isinstance(value, str):
        s = value.strip()
        m = re.match(r"^(\d{1,2})\.(\d{1,2})\.(\d{4})(?:\s|$)", s)
        if m:
            return dt.date(int(m.group(3)), int(m.group(2)), int(m.group(1)))
        m = re.match(r"^(\d{4})-(\d{2})-(\d{2})", s)
        if m:
            return dt.date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
    return None


def to_num(series: pd.Series) -> tuple[pd.Series, int]:
    """Numerisch konvertieren; Rückgabe (Werte, Anzahl nicht-numerischer Nicht-Leerwerte)."""
    num = pd.to_numeric(series, errors="coerce")
    blank = series.isna() | series.astype("string").str.strip().isin(["", "-", "–"])
    return num.astype("float64"), int((num.isna() & ~blank).sum())


RE_FLOAT = r"(-?\d+(?:[.,]\d+)?)"


def parse_temperature(s) -> tuple[float, float, float]:
    """``'19.9°C (Tagesmittel; 17.2–24.0°C)'`` → (19.9, 17.2, 24.0)."""
    if not isinstance(s, str):
        return (np.nan, np.nan, np.nan)
    nums = [float(x.replace(",", ".")) for x in re.findall(RE_FLOAT, s.replace("–", " ").replace("−", "-"))]
    mean = nums[0] if nums else np.nan
    lo, hi = (nums[1], nums[2]) if len(nums) >= 3 else (np.nan, np.nan)
    return (mean, lo, hi)


def parse_first_number(s) -> float:
    if isinstance(s, (int, float)) and not (isinstance(s, float) and np.isnan(s)):
        return float(s)
    if not isinstance(s, str):
        return np.nan
    m = re.search(RE_FLOAT, s)
    return float(m.group(1).replace(",", ".")) if m else np.nan


def parse_table_position(s) -> tuple[float, float]:
    """``'7. Platz, 0 Pkt'`` → (7, 0); '–' oder Hinweistext → (NaN, NaN)."""
    if not isinstance(s, str):
        return (np.nan, np.nan)
    m = re.match(r"^\s*(\d+)\.\s*Platz,\s*(\d+)\s*Pkt", s)
    return (float(m.group(1)), float(m.group(2))) if m else (np.nan, np.nan)


def parse_form(s) -> tuple[float, float]:
    """``'S-U-N'`` → (Anzahl Spiele 3, Punkte 4); sonst NaN."""
    if not isinstance(s, str) or not re.fullmatch(r"[SUN](-[SUN])*", s.strip()):
        return (np.nan, np.nan)
    games = s.strip().split("-")
    return (float(len(games)), float(sum({"S": 3, "U": 1, "N": 0}[g] for g in games)))


def yes_no(s) -> float:
    """'Ja' → 1, 'Nein' → 0, sonst NaN (leer bleibt leer, nicht 'Nein')."""
    if not isinstance(s, str):
        return np.nan
    t = s.strip().lower()
    return 1.0 if t == "ja" else (0.0 if t == "nein" else np.nan)


def reader_sector(reader) -> str | None:
    """Lesername → Sektor: 'A1.2 (62)' → 'A', 'HH-VIP1' → 'HH'."""
    if not isinstance(reader, str):
        return None
    if reader.startswith("HH"):
        return "HH"
    m = re.match(r"^([A-D])\d", reader)
    return m.group(1) if m else "andere"


def season_of(d: dt.date) -> str:
    """Saison Juli–Juni: 2025-08-01 → '2025/26'."""
    start = d.year if d.month >= 7 else d.year - 1
    return f"{start}/{str(start + 1)[2:]}"


def assert_no_personal_columns(df: pd.DataFrame, name: str) -> None:
    """Bricht ab, wenn eine Ausgabespalte nach direktem Personenbezug oder pseudonymer ID aussieht."""
    bad = [c for c in df.columns if personal_category(str(c)) in {"direkt", "pseudonym"}]
    if bad:
        raise PrivacyError(f"[{name}] Ausgabe enthält Spalten mit Personenbezug: {', '.join(bad)}")


# ----------------------------------------------------------------------------------------------------
# Quellen ohne Personenbezug
# ----------------------------------------------------------------------------------------------------

def competition_group(s) -> str:
    t = norm_text(s)
    if "frauen" in t or "awsl" in t:
        return "Frauen"
    if any(k in t for k in ("conference", "europa league", "uefa", "uecl", "uel", "champions")):
        return "UEFA"
    if "cup" in t:
        return "Cup"
    if any(k in t for k in ("super league", "meisterschaft", "abstiegsrunde", "bsl")):
        return "Liga"
    if "test" in t or "freundschaft" in t:
        return "Testspiel"
    return "Andere"


def prepare_context(path: Path) -> pd.DataFrame:
    """Spielkontext-Tabelle des Projektteams (Saison-Tabs, nicht «Übersicht»)."""
    sheets = pd.read_excel(path, sheet_name=None, engine=ENGINE)
    frames = []
    for name, df in sheets.items():
        if not re.fullmatch(r"\d{4}-\d{2}", name):
            continue
        df = df.dropna(subset=["Datum"])
        out = pd.DataFrame({
            "match_date": df["Datum"].map(to_date),
            "season": f"{name[:4]}/{name[5:]}",
            "match_no": df["Nr."],
            "weekday": df["Wochentag"],
            "kickoff": df["Anstosszeit"].map(fmt_time),
            "competition": df["Wettbewerb"],
            "opponent": df["Gegner"],
            "result_post_match": df["Resultat"],
        })
        out["competition_group"] = out["competition"].map(competition_group)

        def split(series, func, names):
            out[names] = pd.DataFrame(series.map(func).tolist(), index=out.index, columns=names)

        split(df["Tabellenstand FCSG (vor Spiel)"], parse_table_position, ["table_rank_fcsg", "table_points_fcsg"])
        split(df["Tabellenstand Gegner (vor Spiel)"], parse_table_position, ["table_rank_opp", "table_points_opp"])
        form_f, form_o = df["Form FCSG (letzte 5 Spiele)"], df["Form Gegner (letzte 5 Spiele)"]
        out["form_fcsg"] = form_f.where(form_f.map(lambda s: not np.isnan(parse_form(s)[0])))
        split(form_f, parse_form, ["form_fcsg_games", "form_fcsg_points"])
        out["form_opp"] = form_o.where(form_o.map(lambda s: not np.isnan(parse_form(s)[0])))
        split(form_o, parse_form, ["form_opp_games", "form_opp_points"])
        out["tv_raw"] = df["TV-Übertragung"]
        out["tv_free_srf"] = df["TV-Übertragung"].map(lambda s: float("srf" in s.lower()) if isinstance(s, str) else np.nan)
        split(df["Temperatur Anstoss (°C)"], parse_temperature, ["temp_day_mean_c", "temp_day_min_c", "temp_day_max_c"])
        out["precip_day_mm"] = df["Niederschlag (mm)"].map(parse_first_number)
        out["wind_day_kmh"] = df["Wind (km/h)"].map(parse_first_number)
        out["school_holiday"] = df["Schulferien Kt. SG"].map(yes_no)
        out["public_holiday_label"] = df["Feiertag Kt. SG"].where(df["Feiertag Kt. SG"].map(lambda s: isinstance(s, str) and s.strip().lower() != "nein"))
        out["public_holiday"] = df["Feiertag Kt. SG"].map(lambda s: np.nan if not isinstance(s, str) else float(s.strip().lower() != "nein"))
        out["parallel_event"] = df["Parallelevents Stadt SG"].map(yes_no)
        out["special_occasion_raw"] = df["Besondere Anlässe"]
        out["remark_raw"] = df["Quelle / Bemerkungen"]
        frames.append(out)
    ctx = pd.concat(frames, ignore_index=True).sort_values("match_date").reset_index(drop=True)
    ctx["weather_basis"] = "Tageswert (nicht Anstosszeit)"
    return ctx


HISTORY_COLUMNS = {
    "Saison": "season", "Wettbewerb": "competition", "Datum": "match_date", "Tag": "weekday",
    "Anpfiff": "kickoff_raw", "Spiel": "match_label", "SOLL": "soll", "IST": "ist", "IST VIP": "ist_vip",
    "IST Gäste": "ist_guests", "Zweitmarkt": "secondary_market", "No-Show": "no_show_rate_reported",
    "No-Show Impact Zweitmarkt": "no_show_impact_secondary_reported",
    "Auslastung, exkl. Gäste": "utilization_excl_guests_reported", "Ausverkauft": "sold_out",
    "Bemerkung": "remark",
}


def prepare_attendance_history(path: Path) -> tuple[pd.DataFrame, dict]:
    """Zuschauerzahlen-Historie (1 Zeile pro Event, alle Wettbewerbe)."""
    raw = pd.read_excel(path, engine=ENGINE)
    missing = [c for c in HISTORY_COLUMNS if c not in raw.columns]
    if missing:
        raise ValueError(f"Historie: Spalten fehlen: {missing}")
    df = raw[list(HISTORY_COLUMNS)].rename(columns=HISTORY_COLUMNS)
    df["match_date"] = df["match_date"].map(to_date)
    n_no_date = int(df["match_date"].isna().sum())
    df = df[df["match_date"].notna()].copy()
    df["kickoff"] = df["kickoff_raw"].map(fmt_time)
    nonnum = {}
    for c in ["soll", "ist", "ist_vip", "ist_guests", "secondary_market", "no_show_rate_reported",
              "no_show_impact_secondary_reported", "utilization_excl_guests_reported", "sold_out"]:
        df[c], nonnum[c] = to_num(df[c])
    df["competition_group"] = df["competition"].map(competition_group)
    return df.reset_index(drop=True), {"rows_without_date": n_no_date, "non_numeric": {k: v for k, v in nonnum.items() if v}}


def _catering_name(header) -> str:
    """Kopfzeile eines Catering-Tabs → einheitlicher Spaltenname."""
    h = norm_text(re.sub(r"(\D)\d+$", r"\1", str(header).strip()))  # Fussnoten-Ziffern am Ende entfernen
    vat = "gross" if "inkl" in h else ("net" if "exkl" in h else "")
    sfx = f"_{vat}" if vat else ""
    rules = [
        (r"^datum$", "match_date"), (r"^(kick-off|zeit)$", "kickoff"), (r"^spiel$", "match_label"),
        (r"^wettbewerb$", "competition"), (r"^wetter$", "weather_text"), (r"^resultat$", "result"),
        (r"^bemerkungen?$", "remark"), (r"zuschauer gaestesektor", "guest_sector_attendance"),
        (r"zuschauerzahlen public netto|^anwesende$", "public_attendance"),
        (r"anzahl transaktionen", "transactions"), (r"ku?n?denfranken|kunenfranken", f"kf{sfx}_reported"),
        (r"transaktions-?\s?durchschnitt", f"avg_receipt{sfx}_reported"), (r"^umsatz total", f"revenue_total{sfx}"),
    ]
    for pattern, name in rules:
        if re.search(pattern, h):
            return name
    base = re.sub(r"\b(inkl|exkl)\b\.?|mwst\.?|\(.*?\)", " ", h)
    prefix = "rev_" if base.strip().startswith("umsatz") else ("fee_" if base.strip().startswith("abgabe") else "x_")
    return prefix + slug(base.replace("umsatz", "").replace("abgabe", "")) + sfx


def prepare_catering(path: Path) -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    """Public-Catering: Saison-Tabs (1 Zeile pro Event) und Tab «Entwicklung» (Saisonsummen)."""
    sheets = pd.read_excel(path, sheet_name=None, header=None, engine=ENGINE)
    frames, report = [], {}
    for name, raw in sheets.items():
        if name == "Entwicklung":
            continue
        header = raw.iloc[2].tolist()
        width = next((i for i, h in enumerate(header) if pd.isna(h)), len(header))  # linker Block bis Leerspalte
        names = [_catering_name(h) for h in header[:width]]
        dup = pd.Series(names).duplicated(keep=False)
        names = [f"{n}_{i}" if d else n for i, (n, d) in enumerate(zip(names, dup))]
        body = raw.iloc[3:, :width].copy()
        body.columns = names
        body["match_date"] = body["match_date"].map(to_date)
        n_skipped = int(body["match_date"].isna().sum() - body.isna().all(axis=1).sum())
        body = body[body["match_date"].notna()].copy()
        nonnum = {}
        for c in body.columns:
            if c.startswith(("rev_", "fee_", "kf_", "avg_receipt", "revenue_total", "x_")) or c in (
                    "public_attendance", "transactions", "guest_sector_attendance"):
                body[c], nonnum[c] = to_num(body[c])
        if "kickoff" in body:
            body["kickoff"] = body["kickoff"].map(fmt_time)
        body.insert(0, "source_tab", name)
        report[name] = {"rows": len(body), "rows_skipped_no_date": n_skipped,
                        "non_numeric_cells": {k: v for k, v in nonnum.items() if v}}
        frames.append(body)
    cat = pd.concat(frames, ignore_index=True)
    label = cat["match_label"].map(norm_text).astype("string")
    comp = cat["competition"].map(norm_text).astype("string")
    is_fcsg = label.str.match(r"^(fcsg|fc st\.? ?gallen)", na=False)
    mentions_fcsg = label.str.contains(r"fcsg|st\.? ?gallen", na=False)  # z. B. «Frauen FCSG vs. …»
    cat["event_class"] = np.select(
        [mentions_fcsg & (label.str.contains("frauen", na=False) | comp.str.contains("frauen", na=False)),
         mentions_fcsg & (label.str.contains(r"u\d\d", na=False) | comp.str.contains(r"u\d\d|nachwuchs", na=False)),
         is_fcsg],
        ["fcsg_frauen", "fcsg_nachwuchs", "fcsg_herren"], default="anderes_event")
    cat["cancelled_flag"] = (comp.str.contains("abgesagt", na=False)
                             | cat.get("remark", pd.Series(index=cat.index, dtype="object")).map(norm_text).str.contains("abgesagt", na=False))
    cat["season"] = cat["match_date"].map(season_of)
    for c in ("kf_gross_reported", "kf_net_reported"):
        if c not in cat:
            cat[c] = np.nan

    dev = sheets["Entwicklung"]
    dev_cols = ["competition_label", "season", "n_events", "attendance", "revenue_total_gross",
                "revenue_total_net", "revenue_per_event_gross", "revenue_per_event_net",
                "kf_gross_avg_reported", "kf_net_avg_reported", "avg_receipt_gross_reported",
                "avg_receipt_net_reported"]
    dev = dev.iloc[3:, :len(dev_cols)].copy()
    dev.columns = dev_cols
    for c in dev_cols[2:]:
        dev[c], _ = to_num(dev[c])
    dev = dev[dev["n_events"].notna()].reset_index(drop=True)
    return cat, dev, report


def prepare_kiesplatz(paths: list[Path]) -> pd.DataFrame:
    """Kiesplatz-Abrechnungen → Langformat (Event × Stand × Kennzahl)."""
    rows = []
    for path in paths:
        season = re.search(r"(\d{2}-\d{2})", path.name).group(1)
        for sheet, raw in pd.read_excel(path, sheet_name=None, header=None, engine=ENGINE).items():
            stands = raw.iloc[1].ffill()
            metrics = raw.iloc[2]
            base = {norm_text(m): i for i, m in enumerate(metrics) if isinstance(m, str)
                    and norm_text(m) in {"monat", "datum", "kick-off", "beginn pause", "event"}}
            metric_cols = [i for i in range(len(metrics)) if i not in base.values() and pd.notna(metrics.iloc[i])]
            for r in range(3, len(raw)):
                d = to_date(raw.iat[r, base["datum"]]) if "datum" in base else None
                if d is None:
                    continue
                for i in metric_cols:
                    m_raw = " ".join(str(metrics.iloc[i]).split())
                    rows.append({
                        "season_file": season, "sheet": sheet, "match_date": d,
                        "kickoff": fmt_time(raw.iat[r, base["kick-off"]]) if "kick-off" in base else None,
                        "event_label": raw.iat[r, base["event"]] if "event" in base else None,
                        "stand": stands.iloc[i], "metric_raw": m_raw, "metric": _kiesplatz_metric(m_raw),
                        "value": parse_first_number(raw.iat[r, i]) if not isinstance(raw.iat[r, i], (int, float))
                        else float(raw.iat[r, i]),
                    })
    return pd.DataFrame(rows)


def _kiesplatz_metric(label: str) -> str:
    t = norm_text(label)
    if t.startswith("total brutto"):
        return "brutto_total"
    if t.startswith("total netto"):
        return "netto_total"
    m = re.match(r"^(brutto|netto) (\d+(?:\.\d+)?)%", t)
    if not m:
        return slug(t)
    kind, rate = m.group(1), m.group(2).replace(".", "_")
    share = "_anteil80" if "anteil 80" in t else ("_anteil20" if "anteil 20" in t else "")
    return f"{kind}_{rate}pct{share}"


def prepare_articles(path: Path) -> pd.DataFrame:
    """Artikelauswertung (Meisterschaft) → Langformat je Abschnitt (Gruppe/Artikel), Name, Saison."""
    raw = pd.read_excel(path, header=None, engine=ENGINE)
    col0 = raw.iloc[:, 0]
    out = []
    header_rows = [i for i, v in col0.items() if v == "Name"]
    n_matches_row = next((i for i, v in col0.items() if v == "Anzahl Spiele"), None)
    for h in header_rows:
        section = next((str(col0.iloc[j]) for j in range(h - 1, -1, -1) if col0.iloc[j] in ("Gruppe", "Artikel")), "?")
        seasons = {c: raw.iat[h - 1, c] for c in range(1, raw.shape[1]) if isinstance(raw.iat[h - 1, c], str)}
        n_matches = {c: raw.iat[n_matches_row, c] for c in seasons} if n_matches_row is not None else {}
        r = h + 2
        while r < len(raw) and pd.notna(col0.iloc[r]) and col0.iloc[r] != "Total":
            for c, season in seasons.items():
                vals = [pd.to_numeric(raw.iat[r, c + k], errors="coerce") for k in range(5)]
                out.append({"section": "group" if section == "Gruppe" else "article", "item_label": col0.iloc[r],
                            "season": season.replace("Saison ", ""), "qty_total": vals[0], "qty_avg_per_match": vals[1],
                            "revenue_net_total": vals[2], "revenue_net_avg_per_match": vals[3],
                            "revenue_share": vals[4], "n_matches_reported": pd.to_numeric(n_matches.get(c), errors="coerce")})
            r += 1
    return pd.DataFrame(out)


# ----------------------------------------------------------------------------------------------------
# Personenbezogene Quellen → nur Aggregate
# ----------------------------------------------------------------------------------------------------

def _parse_ts(series: pd.Series) -> pd.Series:
    if pd.api.types.is_datetime64_any_dtype(series):
        return series
    ts = pd.to_datetime(series, errors="coerce", format="ISO8601")
    if ts.isna().mean() > 0.5:
        ts = pd.to_datetime(series, errors="coerce", dayfirst=True)
    return ts


@dataclass
class AccessResult:
    summary: pd.DataFrame
    sector_minute: pd.DataFrame
    reader: pd.DataFrame
    coding: pd.DataFrame
    checks: list = field(default_factory=list)


ACCESS_SOURCES = [
    # (Dateimuster, Team, Leser-Funktion, Spaltenzuordnung Quelle→Ziel bzw. Index)
    ("ErlaubteZutritteHerren.xlsx", "Herren", {"Datum": "match_date", "Spieltag": "match_label", "TransactionTime": "scan_ts",
                                               "UTId": "_key", "Coding": "coding", "Lesername": "reader", "DisplayMessage": "message"}),
    ("zugangsdaten_herren_alteSaisons.txt", "Herren", {"Matchday": "match_date", "Spieltag": "match_label", "TransactionTime": "scan_ts",
                                                       "Barcode": "_key", "Coding": "coding", "Lesername": "reader", "DisplayMessage": "message"}),
    ("zugangsdaten_herren_inhouse.csv", "Herren", {0: "match_date", 1: "match_label", 2: "scan_ts", 3: "_key", 5: "coding",
                                                   6: "reader", 9: "message"}),
    # zugangsdaten_frauenequipe_alleSpiele.txt wird nicht gelesen (D-016: Frauen-Daten ausserhalb Scope).
]


def _read_access(path: Path, mapping: dict) -> pd.DataFrame:
    cols = list(mapping)
    if path.suffix == ".xlsx":
        df = pd.read_excel(path, engine=ENGINE, usecols=cols)
    elif path.suffix == ".txt":
        df = pd.read_csv(path, sep="\t", usecols=cols, dtype=str, encoding="utf-8")
    else:  # Inhouse-CSV ohne Kopfzeile
        df = pd.read_csv(path, sep=";", header=None, usecols=cols, dtype=str, encoding="utf-8-sig")
    return df.rename(columns=mapping)


def prepare_access(raw_root: Path) -> AccessResult:
    """Zutritte aller Dateien → Aggregate. Ticketschlüssel nur intern für die Anzahl eindeutiger Tickets."""
    frames, checks = [], []
    for pattern, team, mapping in ACCESS_SOURCES:
        for path in sorted(raw_root.rglob(pattern)):
            df = _read_access(path, mapping)
            n_in = len(df)
            df["source_file"] = path.name
            df["team"] = team
            df["scan_ts"] = _parse_ts(df["scan_ts"])
            df["match_date"] = df["match_date"].map(to_date)
            if "reader" not in df:
                df["reader"] = None
            df["sector"] = df["reader"].map(reader_sector)
            df["venue_message"] = df["message"].astype("string").str.replace("Durchgang erlaubt", "", regex=False).str.strip()
            # Schlüssel sofort durch kurzen Hash ersetzen (nur Zählzweck, nie exportiert).
            df["_key"] = df["_key"].astype("string").map(lambda k: hashlib.blake2b(str(k).encode(), digest_size=8).hexdigest()
                                                         if pd.notna(k) else None)
            checks.append({"check_id": f"A-{path.name}", "description": "Zutrittsdatei gelesen", "status": "OK",
                           "detail": f"{n_in} Scans; ohne Zeitstempel: {int(df['scan_ts'].isna().sum())}"})
            frames.append(df.drop(columns=["message"]))
    scans = pd.concat(frames, ignore_index=True)
    n_total = len(scans)
    scans["scan_minute"] = scans["scan_ts"].dt.strftime("%H:%M")
    keys = ["source_file", "team", "match_date"]

    summary = scans.groupby(keys, dropna=False).agg(
        match_label=("match_label", lambda s: s.mode().iat[0] if s.notna().any() else None),
        scans=("scan_ts", "size"),
        n_distinct_tickets=("_key", "nunique"),
        first_scan=("scan_ts", "min"), last_scan=("scan_ts", "max"),
        n_readers=("reader", "nunique"),
        venue_messages=("venue_message", lambda s: " | ".join(sorted(s.dropna().unique()))),
    ).reset_index()
    summary["scans_per_ticket"] = summary["scans"] / summary["n_distinct_tickets"]
    summary["season"] = summary["match_date"].map(lambda d: season_of(d) if d else None)
    for c in ("first_scan", "last_scan"):
        summary[c] = summary[c].dt.strftime("%H:%M:%S")

    sector_minute = scans.groupby(keys + ["sector", "scan_minute"], dropna=False).size().rename("scans").reset_index()
    reader = scans.groupby(keys + ["reader", "sector"], dropna=False).agg(
        scans=("scan_ts", "size"), first_scan=("scan_ts", "min"), last_scan=("scan_ts", "max")).reset_index()
    for c in ("first_scan", "last_scan"):
        reader[c] = reader[c].dt.strftime("%H:%M:%S")
    coding = scans.groupby(keys + ["sector", "coding"], dropna=False).size().rename("scans").reset_index()

    for name, df in (("summary", summary), ("sector_minute", sector_minute), ("reader", reader), ("coding", coding)):
        ok = int(df["scans"].sum()) == n_total
        checks.append({"check_id": f"A-SUM-{name}", "description": f"Summenerhalt Zutritt → {name}",
                       "status": "OK" if ok else "FAIL", "detail": f"{int(df['scans'].sum())} / {n_total}"})
    return AccessResult(summary, sector_minute, reader, coding, checks)


TICKET_CSV_COLUMNS = ["Tribüne", "Block", "Ermäßigung", "Datum", "Uhrzeit", "Filiale", "Versandart", "Summe", "Rechnung"]


def _ticket_file_meta(path: Path) -> dict:
    m = re.match(r"^(\d{8})_(.+)\.csv$", path.name)
    date = None
    if m:
        try:
            date = dt.datetime.strptime(m.group(1), "%Y%m%d").date()
        except ValueError:
            date = None
    folder = path.parent.name
    team = "Frauen" if "frauen" in f"{folder} {path.name}".lower() else "Herren"
    return {"source_file": path.name, "match_date": date, "event_code": m.group(2) if m else path.stem,
            "folder": folder, "team": team, "season_folder": path.parent.parent.name}


def prepare_ticket_csvs(raw_root: Path) -> tuple[dict[str, pd.DataFrame], list]:
    """Ticket-CSVs 25/26–26/27 (Einzeltickets je Spiel) und Saisonabo-Snapshots → Aggregate."""
    singles, abos, checks = [], [], []
    n_women_files = 0
    for path in sorted(raw_root.rglob("Ticketing/20*/**/*.csv")):
        meta = _ticket_file_meta(path)
        if meta["team"] == "Frauen":  # D-016: Frauen-Dateien werden gar nicht erst gelesen
            n_women_files += 1
            continue
        df = pd.read_csv(path, usecols=TICKET_CSV_COLUMNS, dtype=str, encoding="utf-8-sig")
        df = df.rename(columns={"Tribüne": "tribune", "Block": "block", "Ermäßigung": "tarif", "Filiale": "channel",
                                "Versandart": "delivery", "Rechnung": "_purchase"})
        df["price_chf"] = df["Summe"].map(parse_chf)
        df["sale_date"] = df["Datum"].map(to_date)
        df["_purchase"] = df["_purchase"].map(lambda k: hashlib.blake2b(str(k).encode(), digest_size=8).hexdigest()
                                              if pd.notna(k) else None)
        df = df.drop(columns=["Summe", "Datum", "Uhrzeit"])
        for k, v in meta.items():
            df[k] = v
        (abos if "saisonabo" in path.name.lower() else singles).append(df)
    checks.append({"check_id": "D016-ticket_csv", "description": "Frauen-Ticketdateien nicht gelesen (D-016)",
                   "status": "OK", "detail": f"{n_women_files} Dateien übersprungen"})

    out = {}
    if singles:
        s = pd.concat(singles, ignore_index=True)
        n = len(s)
        s["lead_days"] = [(m - d).days if (m and d) else np.nan for m, d in zip(s["match_date"], s["sale_date"])]
        g = ["source_file", "season_folder", "folder", "team", "match_date", "event_code"]
        out["tickets_single_agg"] = s.groupby(g + ["tribune", "block", "tarif", "channel", "delivery"], dropna=False).agg(
            n_tickets=("price_chf", "size"), revenue_chf=("price_chf", "sum"),
            n_price_missing=("price_chf", lambda x: int(x.isna().sum()))).reset_index()
        out["tickets_single_leadtime"] = s.groupby(g + ["tribune", "channel", "lead_days"], dropna=False).agg(
            n_tickets=("price_chf", "size"), revenue_chf=("price_chf", "sum")).reset_index()
        per_purchase = s.groupby(g + ["_purchase"], dropna=False).size().rename("tickets_in_purchase").reset_index()
        per_purchase["tickets_in_purchase"] = per_purchase["tickets_in_purchase"].clip(upper=10)
        out["tickets_single_purchase_size"] = per_purchase.groupby(g + ["tickets_in_purchase"]).size() \
            .rename("n_purchases").reset_index()
        out["tickets_single_purchase_size"]["n_tickets_approx"] = (
            out["tickets_single_purchase_size"]["n_purchases"] * out["tickets_single_purchase_size"]["tickets_in_purchase"])
        for name in ("tickets_single_agg", "tickets_single_leadtime"):
            ok = int(out[name]["n_tickets"].sum()) == n
            checks.append({"check_id": f"T-SUM-{name}", "description": f"Summenerhalt Tickets → {name}",
                           "status": "OK" if ok else "FAIL", "detail": f"{int(out[name]['n_tickets'].sum())} / {n}"})
        checks.append({"check_id": "T-PURCHASE", "description": "Kaufgrössen: Anzahl Käufe aus Rechnungsnummern (nur gezählt)",
                       "status": "OK", "detail": f"{int(out['tickets_single_purchase_size']['n_purchases'].sum())} Käufe; ab 10 Tickets gekappt"})
    if abos:
        a = pd.concat(abos, ignore_index=True)
        a["sale_month"] = a["sale_date"].map(lambda d: d.strftime("%Y-%m") if d else None)
        out["season_ticket_snapshot_agg"] = a.groupby(
            ["source_file", "team", "tribune", "block", "tarif", "channel", "delivery", "sale_month"], dropna=False).agg(
            n_seats=("price_chf", "size"), revenue_chf=("price_chf", "sum")).reset_index()
        ok = int(out["season_ticket_snapshot_agg"]["n_seats"].sum()) == len(a)
        checks.append({"check_id": "T-SUM-abo", "description": "Summenerhalt Saisonabos", "status": "OK" if ok else "FAIL",
                       "detail": f"{len(a)} Abo-Sitze"})
    return out, checks


EINZEL_COLUMNS = {
    "Saison-Bez.": "season_label", "Veranstaltung": "event_id", "Veranstaltungsdatum": "event_date",
    "Veranstaltungszeit": "event_time", "Veranstaltungs-Bez.": "event_label", "Preiskategorie-Bez.": "price_category",
    "Verkaufsmodul-Bez.": "channel", "Warenart-Bez.": "goods_type", "Stornostatus-Bez.": "cancel_status",
    "Verkaufsstatus-Bez.": "sale_status", "Platzgruppen-Bez.": "seat_group", "Verkaufsart-Bez.": "tarif",
    "Bestelldatum": "order_ts", "Versandart-Bez.": "delivery", "Anzahl Waren": "quantity", "Preis": "price_chf",
    "ZKS-Eintrittsdatum": "entry_ts",
}


def prepare_einzeltickets(raw_root: Path) -> tuple[dict[str, pd.DataFrame], list]:
    """Einzeltickets-Exporte 21/22–24/25 (mehrere Tabs à 65 000 Zeilen) → Aggregate ohne Personenfelder."""
    frames, checks = [], []
    for path in sorted(raw_root.rglob("Einzeltickets_*.xlsx")):
        sheets = pd.read_excel(path, sheet_name=None, engine=ENGINE, usecols=list(EINZEL_COLUMNS))
        df = pd.concat(sheets.values(), ignore_index=True).rename(columns=EINZEL_COLUMNS)
        df["source_file"] = path.name
        checks.append({"check_id": f"E-{path.name}", "description": "Einzelticket-Export gelesen (Tabs zusammengeführt)",
                       "status": "OK", "detail": f"{len(df)} Zeilen aus {len(sheets)} Tabs"})
        frames.append(df)
    e = pd.concat(frames, ignore_index=True)
    n = len(e)
    e["event_date"] = e["event_date"].map(to_date)
    e["is_match"] = e["event_label"].astype("string").str.startswith("FC St.Gallen 1879 - ").fillna(False)
    e["opponent"] = e["event_label"].astype("string").str.extract(r"^FC St\.Gallen 1879 - (.+?) \(")[0]
    e["quantity"], _ = to_num(e["quantity"])
    e["price_chf"], _ = to_num(e["price_chf"])
    e["entered"] = e["entry_ts"].notna()
    order_date = pd.to_datetime(e["order_ts"], errors="coerce").dt.date
    e["lead_days"] = [(m - d).days if (m is not None and pd.notna(d)) else np.nan for m, d in zip(e["event_date"], order_date)]
    e["entry_minute"] = pd.to_datetime(e["entry_ts"], errors="coerce").dt.strftime("%H:%M")
    ev = ["source_file", "season_label", "event_date", "event_id", "event_label", "opponent", "is_match"]
    out = {
        "tickets_hist_agg": e.groupby(ev + ["price_category", "channel", "seat_group", "tarif", "delivery", "goods_type",
                                            "cancel_status", "sale_status", "entered"], dropna=False).agg(
            n_rows=("quantity", "size"), n_tickets=("quantity", "sum"), revenue_chf=("price_chf", "sum")).reset_index(),
        "tickets_hist_leadtime": e.groupby(ev + ["channel", "seat_group", "lead_days"], dropna=False).agg(
            n_rows=("quantity", "size"), n_tickets=("quantity", "sum"), n_entered=("entered", "sum")).reset_index(),
        "tickets_hist_entry_minute": e[e["entered"]].groupby(ev + ["entry_minute"], dropna=False).size()
        .rename("n_entries").reset_index(),
    }
    for name in ("tickets_hist_agg", "tickets_hist_leadtime"):
        ok = int(out[name]["n_rows"].sum()) == n
        checks.append({"check_id": f"E-SUM-{name}", "description": f"Summenerhalt Einzeltickets → {name}",
                       "status": "OK" if ok else "FAIL", "detail": f"{int(out[name]['n_rows'].sum())} / {n}"})
    ok = int(out["tickets_hist_entry_minute"]["n_entries"].sum()) == int(e["entered"].sum())
    checks.append({"check_id": "E-SUM-entry", "description": "Summenerhalt Eintritte → Minutenprofil",
                   "status": "OK" if ok else "FAIL", "detail": f"{int(e['entered'].sum())} Eintritte"})
    return out, checks


# ----------------------------------------------------------------------------------------------------
# Scope (D-016) und Schulferien (D-017 b / D-021)
# ----------------------------------------------------------------------------------------------------

WOMEN_PATTERN = r"frauen|awsl"
# Textspalten, an denen ein Frauen-Event erkennbar ist (Wettbewerb, Eventklasse, Spiel-/Eventbezeichnung).
WOMEN_COLUMNS = ("competition_group", "event_class", "competition", "competition_label", "match_label", "event_label",
                 "team")


def drop_women(tables: dict[str, pd.DataFrame]) -> list[dict]:
    """Entfernt Frauen-Events aus allen Tabellen (D-016: Frauen-Daten fallen ganz weg).

    Reine Frauen-Dateien (Zutritt, Ticket-CSVs, Abos) werden schon beim Lesen übersprungen; hier werden
    gemischte Quellen (Historie, Catering, Kiesplatz, Einzeltickets, Kontext) bereinigt. Ein Event gilt als
    Frauen-Event, wenn eine der ``WOMEN_COLUMNS`` «Frauen» oder «AWSL» enthält. Die Tabellen werden an Ort
    und Stelle ersetzt.

    Returns:
        Prüfprotokoll: je Tabelle Anzahl entfernter Zeilen (nur Anzahlen).
    """
    checks = []
    for name, df in tables.items():
        cols = [c for c in WOMEN_COLUMNS if c in df.columns]
        if not cols:
            continue
        mask = pd.Series(False, index=df.index)
        for c in cols:
            mask |= df[c].astype("string").str.contains(WOMEN_PATTERN, case=False, regex=True, na=False)
        if mask.any():
            tables[name] = df[~mask].reset_index(drop=True)
        checks.append({"check_id": f"D016-{name}", "description": f"Frauen-Events entfernt (D-016) → {name}",
                       "status": "OK", "detail": f"{int(mask.sum())} von {len(df)} Zeilen entfernt"})
    return checks


SCHOOL_HOLIDAYS_FILE = Path(__file__).resolve().parents[2] / "config" / "reference" / "school_holidays_stadt_sg.csv"
# D-017 b: Schulferien-Werte des Teams sind nur ab dieser Saison verlässlich recherchiert.
SCHOOL_HOLIDAY_TEAM_FROM = "2026/27"


def load_school_holidays(path: Path = SCHOOL_HOLIDAYS_FILE) -> pd.DataFrame:
    """Lädt die recherchierte Ferientabelle (``config/reference/``) und prüft sie.

    Erwartet je Zeile einen Ferienblock mit ``first_day``/``last_day`` (beide inklusive).

    Raises:
        ValueError: Pflichtspalte fehlt, Ende vor Beginn oder Ferienblöcke überlappen.
    """
    df = pd.read_csv(path, dtype=str)
    missing = {"school_year", "holiday", "first_day", "last_day", "source_id"} - set(df.columns)
    if missing:
        raise ValueError(f"Schulferien-Tabelle: Spalten fehlen: {sorted(missing)}")
    for c in ("first_day", "last_day"):
        df[c] = df[c].map(to_date)
    df = df.sort_values("first_day").reset_index(drop=True)
    if (df["last_day"] < df["first_day"]).any():
        raise ValueError("Schulferien-Tabelle: Ende vor Beginn.")
    if (df["first_day"].iloc[1:].values <= df["last_day"].iloc[:-1].values).any():
        raise ValueError("Schulferien-Tabelle: Ferienblöcke überlappen.")
    return df


def apply_school_holidays(ctx: pd.DataFrame, holidays: pd.DataFrame,
                          team_from: str = SCHOOL_HOLIDAY_TEAM_FROM) -> tuple[pd.DataFrame, dict]:
    """Ersetzt ``school_holiday`` vor ``team_from`` durch den recherchierten Wert (D-017 b).

    - ``school_holiday_team``: Originalwert der Spielkontext-Tabelle (unverändert erhalten).
    - ``school_holiday_research``: 1 = Spieltag liegt in einem Ferienblock, 0 = nicht, leer = Datum ausserhalb
      der recherchierten Abdeckung (nie automatisch 0).
    - ``school_holiday_period``: Name des Ferienblocks.
    - ``school_holiday``: ab ``team_from`` Teamwert, davor Recherche.
    - ``school_holiday_source``: ``team`` bzw. ``agent_recherche_2026-10-11`` (Anmerkung, wer den Wert gesetzt hat).

    Returns:
        (Kontexttabelle, Kennzahlen zum Abgleich Team vs. Recherche)
    """
    ctx = ctx.copy()
    lo, hi = holidays["first_day"].min(), holidays["last_day"].max()

    def lookup(d):
        if d is None or not (lo <= d <= hi):
            return (np.nan, None)
        hit = holidays[(holidays["first_day"] <= d) & (holidays["last_day"] >= d)]
        return (1.0, hit["holiday"].iat[0]) if len(hit) else (0.0, None)

    found = ctx["match_date"].map(lookup)
    ctx["school_holiday_team"] = ctx["school_holiday"]
    ctx["school_holiday_research"] = found.map(lambda t: t[0]).astype("float64")
    ctx["school_holiday_period"] = found.map(lambda t: t[1])
    use_team = ctx["season"] >= team_from
    ctx["school_holiday"] = ctx["school_holiday_team"].where(use_team, ctx["school_holiday_research"])
    ctx["school_holiday_source"] = np.where(use_team, "team", "agent_recherche_2026-10-11")

    both = ctx["school_holiday_team"].notna() & ctx["school_holiday_research"].notna()
    differs = both & (ctx["school_holiday_team"] != ctx["school_holiday_research"])
    stats = {
        "replaced": int((~use_team).sum()),
        "changed": int((differs & ~use_team).sum()),
        "team_period_checked": int((both & use_team).sum()),
        "team_period_differs": int((differs & use_team).sum()),
        "outside_coverage": int(ctx["school_holiday_research"].isna().sum()),
    }
    return ctx, stats


# ----------------------------------------------------------------------------------------------------
# Abdeckung und Lauf
# ----------------------------------------------------------------------------------------------------

def build_match_coverage(t: dict[str, pd.DataFrame], since: dt.date = dt.date(2021, 7, 1)) -> pd.DataFrame:
    """Ein Datum pro Zeile mit Kennzeichen, welche Quelle dieses Datum enthält (Herren-Fokus)."""
    hist = t["attendance_history"]
    hist = hist[hist["competition_group"] != "Frauen"]
    cat = t["catering_match"]
    single = t.get("tickets_single_agg", pd.DataFrame(columns=["team", "match_date", "n_tickets"]))
    parts = {
        "context": t["context_match"].groupby("match_date")["competition"].first(),
        "history": hist.groupby("match_date")["competition"].first(),
        "catering": cat[cat["event_class"] == "fcsg_herren"].groupby("match_date")["revenue_total_gross"].sum(min_count=1),
        "access_scans": t["access_match_summary"][t["access_match_summary"]["team"] == "Herren"]
        .groupby("match_date")["scans"].sum(),
        "ticket_csv": single[single["team"] == "Herren"].groupby("match_date")["n_tickets"].sum(),
        "einzeltickets": t["tickets_hist_agg"][t["tickets_hist_agg"]["is_match"]].groupby("event_date")["n_tickets"].sum(),
    }
    dates = sorted({d for s in parts.values() for d in s.index if d is not None and d >= since})
    cov = pd.DataFrame({"match_date": dates})
    for name, s in parts.items():
        cov[name] = cov["match_date"].map(s)
        cov[f"has_{name}"] = cov[name].notna()
    cov["season"] = cov["match_date"].map(season_of)
    cov["n_sources"] = cov[[c for c in cov.columns if c.startswith("has_")]].sum(axis=1)
    # Abgleich Zutritt vs. IST (Historie): grobe Vollständigkeitsprüfung der Scans je Spiel.
    ist = hist.groupby("match_date")["ist"].sum(min_count=1)
    cov["history_ist"] = cov["match_date"].map(ist)
    cov["scans_vs_ist_rate"] = cov["access_scans"] / cov["history_ist"] - 1
    cov["access_complete"] = np.where(cov["scans_vs_ist_rate"].isna(), np.nan,
                                      (cov["scans_vs_ist_rate"].abs() <= 0.05).astype(float))
    return cov


def _find(raw_root: Path, pattern: str) -> list[Path]:
    return sorted(raw_root.rglob(pattern))


def _sha16(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        while chunk := fh.read(8 << 20):
            h.update(chunk)
    return h.hexdigest()[:16]


def run_prepare(raw_root: Path, context_file: Path, clean_root: Path, tz: str = "Europe/Zurich", progress=print) -> Path:
    """Gesamtlauf: liest Rohdaten, schreibt bereinigte Tabellen + Manifest nach ``clean_root/<run_id>/``."""
    run_id = f"{dt.datetime.now(ZoneInfo(tz)):%Y%m%dT%H%M%S}_clean_{secrets.token_hex(2)}"
    out_dir = clean_root / run_id
    tables: dict[str, pd.DataFrame] = {}
    checks: list[dict] = []
    reports: dict = {}

    progress("Spielkontext …")
    tables["context_match"], hol = apply_school_holidays(prepare_context(context_file), load_school_holidays())
    checks.append({"check_id": "K-SCHOOL-HOLIDAY", "description": "Schulferien vor 2026/27 durch Recherche ersetzt (D-017 b)",
                   "status": "OK", "detail": f"{hol['replaced']} Spiele ersetzt, davon {hol['changed']} geändert; "
                                             f"ohne Abdeckung: {hol['outside_coverage']}"})
    checks.append({"check_id": "K-SCHOOL-HOLIDAY-XCHECK", "description": "Gegenprobe Teamwerte ab 2026/27 vs. Recherche",
                   "status": "OK" if hol["team_period_differs"] == 0 else "WARN",
                   "detail": f"{hol['team_period_checked']} geprüft, {hol['team_period_differs']} abweichend"})
    progress("Zuschauerhistorie …")
    tables["attendance_history"], reports["attendance_history"] = prepare_attendance_history(
        _find(raw_root, "Ticketing-Zuschauerzahlen-Historie.xlsx")[0])
    progress("Public Catering …")
    tables["catering_match"], tables["catering_season_summary"], reports["catering"] = prepare_catering(
        _find(raw_root, "Umsatz Public Catering*.xlsx")[0])
    progress("Kiesplatz …")
    tables["kiesplatz_event_stand"] = prepare_kiesplatz(_find(raw_root, "Abrechnung Kiesplatz*.xlsx"))
    progress("Artikelauswertung …")
    tables["article_season"] = prepare_articles(_find(raw_root, "Artikelauswertung*.xlsx")[0])
    progress("Zutritte (aggregiert) …")
    acc = prepare_access(raw_root)
    tables.update({"access_match_summary": acc.summary, "access_sector_minute": acc.sector_minute,
                   "access_reader": acc.reader, "access_coding": acc.coding})
    checks += acc.checks
    progress("Ticket-CSVs und Abos (aggregiert) …")
    t_out, t_checks = prepare_ticket_csvs(raw_root)
    tables.update(t_out)
    checks += t_checks
    progress("Einzeltickets-Exporte (aggregiert) …")
    e_out, e_checks = prepare_einzeltickets(raw_root)
    tables.update(e_out)
    checks += e_checks
    progress("Frauen-Events entfernen (D-016) …")
    checks += drop_women(tables)
    progress("Abdeckungsmatrix …")
    tables["match_coverage"] = build_match_coverage(tables)

    for name, df in tables.items():  # erst alle prüfen, dann schreiben (kein Teil-Export)
        assert_no_personal_columns(df, name)
    out_dir.mkdir(parents=True, exist_ok=False)
    outputs = {}
    for name, df in tables.items():
        path = out_dir / f"{name}.csv"
        df.to_csv(path, index=False, encoding="utf-8", lineterminator="\n")
        outputs[name] = {"rows": len(df), "columns": list(df.columns)}
    checks.append({"check_id": "P-01", "description": "Keine Ausgabespalte mit Personenbezug (Heuristik)",
                   "status": "OK", "detail": f"{len(tables)} Tabellen geprüft"})

    inputs = [{"file": p.relative_to(raw_root).as_posix(), "sha256_16": _sha16(p), "bytes": p.stat().st_size}
              for p in sorted(raw_root.rglob("*")) if p.is_file() and p.name != ".DS_Store"]
    inputs.append({"file": f"projekt/{context_file.name}", "sha256_16": _sha16(context_file), "bytes": context_file.stat().st_size})
    inputs.append({"file": f"projekt/config/reference/{SCHOOL_HOLIDAYS_FILE.name}", "sha256_16": _sha16(SCHOOL_HOLIDAYS_FILE),
                   "bytes": SCHOOL_HOLIDAYS_FILE.stat().st_size})
    manifest = {
        "run_id": run_id, "created_at": dt.datetime.now(ZoneInfo(tz)).isoformat(timespec="seconds"),
        "data_mode": "release_aggregates", "code_version": __version__, "python": platform.python_version(),
        "packages": {p: version(p) for p in ("pandas", "numpy", "openpyxl", "python-calamine")},
        "inputs": inputs, "outputs": outputs, "checks": checks, "source_reports": reports,
    }
    (out_dir / "manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False, default=str), encoding="utf-8")
    pd.DataFrame(checks).to_csv(out_dir / "quality_checks.csv", index=False, encoding="utf-8")
    (clean_root / "LATEST").write_text(run_id, encoding="utf-8")
    return out_dir

"""Strukturinventar der Rohdateien – Datenmodus «structure_only» (D-001, Option b).

Liest Excel-, CSV- und Textdateien **lokal** und gibt ausschliesslich Strukturinformationen aus:
Dateiname, Tabs inkl. Sichtbarkeit, erkannte Kopfzeile, Zeilen-/Spaltenzahl, Spaltennamen,
Datentypverteilung, Missing-Anteil, Datumsbereich und Anzahl unterschiedlicher Tage (nur Datumsspalten)
sowie Hinweise (Summenzeilen, Formeln ohne gespeicherten Wert, Kommentare, externe Verknüpfungen).

Schutzregeln (damit keine Rohwerte in Berichte oder den Agentenkontext gelangen):

- Zellinhalte werden nie ausgegeben, nur Zählwerte und Typen.
- Spalten mit direktem Personenbezug (Name, Adresse, PLZ, Geburtsdatum, E-Mail, Telefon …) erscheinen
  nur mit Spaltenname und Kategorie; ihre Statistik wird unterdrückt.
- Datumsbereiche mit Werten vor 2000 werden unterdrückt (mögliches Geburtsdatum).
- Kopfzellen, die wie Daten aussehen (Zahl, Datum, E-Mail, lange Ziffernfolge), werden maskiert, falls
  die Kopfzeilenerkennung eine Datenzeile erwischt.
- Inhaltsprüfung: Textspalten mit E-Mail-artigen oder telefonartigen Werten werden markiert (nur Anzahl).

Grenze: Personennamen in unauffällig benannten Textspalten sind inhaltlich nicht sicher erkennbar.
Deshalb wird später mit einer Positivliste (Allowlist) gearbeitet, nicht mit einer Sperrliste.
"""

from __future__ import annotations

import codecs
import csv
import datetime as dt
import hashlib
import re
import time
import zipfile
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from xml.etree import ElementTree as ET

import pandas as pd
from openpyxl import load_workbook

HEADER_SCAN_ROWS = 30
MAX_DISTINCT_DATES = 20000
IGNORED_FILES = {".ds_store", "thumbs.db", "desktop.ini"}
TABULAR_SUFFIXES = {".xlsx", ".xlsm", ".csv", ".txt", ".tsv"}

# --- Klassifikation einzelner Werte -------------------------------------------------------------

RE_EMAIL = re.compile(r"[^@\s]+@[^@\s]+\.[A-Za-z]{2,}")
RE_DATE_DE = re.compile(r"^(\d{1,2})\.(\d{1,2})\.(\d{4}|\d{2})(?:[ T]\d{1,2}:\d{2}(?::\d{2})?)?$")
RE_DATE_ISO = re.compile(r"^(\d{4})-(\d{2})-(\d{2})(?:[ T]\d{1,2}:\d{2}(?::\d{2}(?:\.\d+)?)?.*)?$")
RE_TIME = re.compile(r"^\d{1,2}:\d{2}(?::\d{2})?$")
RE_NUMBER = re.compile(r"^[-+]?(?:\d{1,3}(?:['’ ]\d{3})+|\d+)(?:[.,]\d+)?%?$")
RE_LONG_DIGITS = re.compile(r"\d[\d /+-]{8,}\d")
RE_TOTAL_ROW = re.compile(r"^\s*(total|totale?|summe|gesamt\w*|durchschnitt|schnitt|ø|mittelwert|average|sum)\b", re.I)


def classify(value) -> tuple[str, dt.date | None]:
    """Gibt (Typ, Datum oder None) für einen Zellwert zurück. Typ ``null`` = fehlend."""
    if value is None:
        return "null", None
    if isinstance(value, bool):
        return "bool", None
    if isinstance(value, (int, float)):
        if isinstance(value, float) and value != value:  # NaN
            return "null", None
        return "zahl", None
    if isinstance(value, dt.datetime):
        kind = "datum" if value.time() == dt.time(0) else "datum_zeit"
        return kind, value.date()
    if isinstance(value, dt.date):
        return "datum", value
    if isinstance(value, dt.time):
        return "zeit", None
    if isinstance(value, dt.timedelta):
        return "dauer", None
    s = str(value).strip()
    if not s:
        return "null", None
    m = RE_DATE_DE.match(s)
    if m:
        d, mth, y = int(m.group(1)), int(m.group(2)), int(m.group(3))
        y = y + 2000 if y < 100 else y
        try:
            return "datum_text", dt.date(y, mth, d)
        except ValueError:
            return "text", None
    m = RE_DATE_ISO.match(s)
    if m:
        try:
            return "datum_text", dt.date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
        except ValueError:
            return "text", None
    if RE_TIME.match(s):
        return "zeit_text", None
    if RE_NUMBER.match(s):
        return "zahl_text", None
    return "text", None


# --- Personenbezug anhand des Spaltennamens ---------------------------------------------------------

DIRECT_SUBSTR = (
    "vorname", "nachname", "firstname", "lastname", "surname", "familienname", "geburt", "birth", "gebdat",
    "strasse", "street", "adresse", "address", "postleitzahl", "wohnort", "email", "emailadresse", "telefon",
    "phone", "handy", "mobilnummer", "natel", "iban", "ausweis", "passport", "anrede", "geschlecht", "gender",
    "karteninhaber", "inhaber", "kaeufer", "besteller", "kundenname", "personenname", "postfach",
)
DIRECT_TOKENS = {"name", "plz", "zip", "ort", "city", "mail", "tel", "mobile", "mobil", "alter", "age",
                 "jahrgang", "geb", "titel"}
PSEUDO_SUBSTR = (
    "kundennr", "kundennummer", "kundenid", "customer", "personid", "personennr", "utid", "barcode",
    "ticketnr", "ticketnummer", "ticketid", "kartennr", "kartennummer", "chipnr", "rfid", "mitglied",
    "member", "bestellnr", "bestellnummer", "orderid", "ordernr", "rechnungsnr", "rechnungsnummer",
    "rechnungsid", "invoice", "transaktionsid", "abonr", "abonummer", "userid", "benutzer", "login",
    "kontonr", "kontonummer",
)
PSEUDO_TOKENS = {"uid", "kunde", "kunden", "person", "user", "order", "rechnung"}
QUASI_SUBSTR = ("sitz", "reihe", "seat", "platznr", "nationalitaet", "sprache", "language", "country")
QUASI_TOKENS = {"platz", "land", "staat"}
# «Name» neben diesen Wörtern bezeichnet Dinge, nicht Personen (z. B. «Artikel Name», «Leser Name»).
NON_PERSON_NAME_CONTEXT = {"artikel", "produkt", "article", "product", "leser", "reader", "stand", "sektor",
                           "event", "spiel", "gegner", "team", "verkaufsstelle", "kategorie", "gruppe", "tarif",
                           "kanal", "datei", "file", "liga", "wettbewerb", "tor", "gate", "block", "tribuene",
                           "sheet", "tab", "saison"}


def _norm(text: str) -> tuple[str, list[str]]:
    t = text.lower().replace("ä", "ae").replace("ö", "oe").replace("ü", "ue").replace("ß", "ss")
    tokens = re.sub(r"[^a-z0-9]+", " ", t).split()
    return "".join(tokens), tokens


def personal_category(column_name: str) -> str:
    """Kategorie des Personenbezugs nach Spaltenname: ``direkt``, ``pseudonym``, ``quasi`` oder ``""``.

    Heuristik; Fehlalarme sind gewollt (Mensch prüft), Fehlende werden durch die Allowlist abgefangen.
    """
    joined, tokens = _norm(column_name)
    direct_tokens = DIRECT_TOKENS & set(tokens)
    if direct_tokens == {"name"} and NON_PERSON_NAME_CONTEXT & set(tokens):
        direct_tokens = set()
    if any(s in joined for s in DIRECT_SUBSTR) or direct_tokens:
        return "direkt"
    if any(s in joined for s in PSEUDO_SUBSTR) or PSEUDO_TOKENS & set(tokens):
        return "pseudonym"
    if any(s in joined for s in QUASI_SUBSTR) or QUASI_TOKENS & set(tokens):
        return "quasi"
    return ""


# --- Spaltenstatistik --------------------------------------------------------------------------------

@dataclass
class ColumnStats:
    """Akkumuliert Zählwerte einer Spalte, ohne Werte zu speichern (ausser Datumsmenge, nie ausgegeben)."""

    n_rows: int = 0
    types: Counter = field(default_factory=Counter)
    date_min: dt.date | None = None
    date_max: dt.date | None = None
    dates: set = field(default_factory=set)
    n_email: int = 0
    n_long_digits: int = 0

    def add(self, value) -> None:
        self.n_rows += 1
        kind, date = classify(value)
        self.types[kind] += 1
        if date is not None:
            self.date_min = date if self.date_min is None or date < self.date_min else self.date_min
            self.date_max = date if self.date_max is None or date > self.date_max else self.date_max
            if len(self.dates) < MAX_DISTINCT_DATES:
                self.dates.add(date)
        elif kind == "text":
            s = str(value)
            if RE_EMAIL.search(s):
                self.n_email += 1
            elif RE_LONG_DIGITS.search(s):
                self.n_long_digits += 1

    def profile(self, category: str) -> dict:
        """Ausgabefähiges Profil; bei direktem Personenbezug ohne Statistik."""
        if category == "direkt":
            return {"dominant_type": "", "type_mix": "", "missing_share": None, "n_nonnull": None,
                    "date_min": "", "date_max": "", "n_distinct_dates": None,
                    "content_flags": "Statistik unterdrückt (Personenbezug)"}
        n_null = self.types.get("null", 0)
        nonnull = {k: v for k, v in self.types.items() if k != "null"}
        n_nonnull = sum(nonnull.values())
        dominant = max(nonnull, key=nonnull.get) if nonnull else "leer"
        mix = " | ".join(f"{k} {v / n_nonnull:.0%}" for k, v in sorted(nonnull.items(), key=lambda kv: -kv[1]))
        flags = []
        if self.n_email:
            flags.append(f"E-Mail-artige Werte: {self.n_email}")
        if self.n_long_digits:
            flags.append(f"telefon-/ID-artige Ziffernfolgen: {self.n_long_digits}")
        show_dates = category != "pseudonym" and self.date_min is not None
        if show_dates and self.date_min.year < 2000:
            flags.append("Datumswerte vor 2000 – Bereich unterdrückt (mögliches Geburtsdatum)")
            show_dates = False
        return {
            "dominant_type": dominant,
            "type_mix": mix if len(nonnull) > 1 else "",
            "missing_share": round(n_null / self.n_rows, 4) if self.n_rows else None,
            "n_nonnull": n_nonnull,
            "date_min": self.date_min.isoformat() if show_dates else "",
            "date_max": self.date_max.isoformat() if show_dates else "",
            "n_distinct_dates": len(self.dates) if show_dates else None,
            "content_flags": "; ".join(flags),
        }


# --- Tabellenprofil (gemeinsam für Excel-Tabs und Textdateien) -----------------------------------------

def _header_score(row: list) -> int:
    return sum(1 for v in row if isinstance(v, str) and classify(v)[0] == "text" and len(v.strip()) <= 80)


def _header_label(value, idx: int) -> str:
    """Spaltenname aus einer Kopfzelle; Zellen, die wie Daten aussehen, werden maskiert."""
    if value is None or (isinstance(value, str) and not value.strip()):
        return f"<leer_{idx}>"
    kind, _ = classify(value)
    s = " ".join(str(value).split())
    if kind != "text" or RE_EMAIL.search(s) or RE_LONG_DIGITS.search(s):
        return f"<maskiert_{idx}:{kind}>"
    return s if len(s) <= 80 else s[:80] + "…"


def profile_rows(rows) -> tuple[dict, list[dict]]:
    """Profiliert eine Tabelle aus einem Zeilen-Iterator (Listen von Zellwerten).

    Returns:
        ``(sheet_info, column_profiles)``; enthält nur Strukturangaben.
    """
    rows = iter(rows)
    head = []
    for _ in range(HEADER_SCAN_ROWS):
        try:
            head.append(list(next(rows)))
        except StopIteration:
            break

    scores = [_header_score(r) for r in head]
    best = max(scores, default=0)
    header_idx = scores.index(best) if best >= 2 else None
    header = head[header_idx] if header_idx is not None else []
    notes = []
    if header_idx is None:
        notes.append("keine Kopfzeile erkannt")
    elif header_idx > 0 and scores[header_idx - 1] >= 2:
        notes.append("mögliche mehrzeilige Kopfzeile")

    stats: list[ColumnStats] = []
    n_data = n_internal_empty = pending_empty = n_total_rows = 0
    total_rows_at: list[int] = []
    first_data_row = (header_idx + 1) if header_idx is not None else 0

    def consume(row: list, row_no: int) -> None:
        nonlocal n_data, n_internal_empty, pending_empty, n_total_rows
        if all(v is None or (isinstance(v, str) and not v.strip()) for v in row):
            pending_empty += 1
            return
        if n_data:
            n_internal_empty += pending_empty
        pending_empty = 0
        n_data += 1
        if any(isinstance(v, str) and RE_TOTAL_ROW.match(v) for v in row[:3]):
            n_total_rows += 1
            if len(total_rows_at) < 10:
                total_rows_at.append(row_no)
        while len(stats) < len(row):
            stats.append(ColumnStats(n_rows=n_data - 1, types=Counter({"null": n_data - 1})))
        for i, s in enumerate(stats):
            s.add(row[i] if i < len(row) else None)

    excel_row = 0
    for excel_row, row in enumerate(head[first_data_row:], start=first_data_row + 1):
        consume(row, excel_row)
    for excel_row, row in enumerate(rows, start=len(head) + 1):
        consume(list(row), excel_row)

    # Spalten ganz rechts, die weder Kopf noch Werte haben, nicht ausweisen.
    header_width = max((i + 1 for i, v in enumerate(header) if v is not None and str(v).strip()), default=0)
    while len(stats) > header_width and stats[-1].types.get("null", 0) == stats[-1].n_rows:
        stats.pop()
    header = header[:max(header_width, len(stats))]
    while len(stats) < len(header):
        stats.append(ColumnStats(n_rows=n_data, types=Counter({"null": n_data})))

    labels = [_header_label(header[i] if i < len(header) else None, i + 1) for i in range(len(stats))]
    dupes = [k for k, v in Counter(labels).items() if v > 1 and not k.startswith("<")]
    if dupes:
        notes.append(f"doppelte Spaltennamen: {len(dupes)}")

    columns = []
    for i, (label, s) in enumerate(zip(labels, stats), start=1):
        category = personal_category(label) if not label.startswith("<") else ""
        if not category and (s.n_email or s.n_long_digits):
            category = "inhalt_auffaellig"
        columns.append({"col": i, "column_name": label, "personal_category": category, **s.profile(category)})

    info = {
        "header_row": header_idx + 1 if header_idx is not None else None,
        "n_data_rows": n_data,
        "n_columns": len(stats),
        "internal_empty_rows": n_internal_empty,
        "total_row_candidates": n_total_rows,
        "total_rows_at": ", ".join(map(str, total_rows_at)),
        "notes": "; ".join(notes),
    }
    return info, columns


# --- Excel-spezifisch ---------------------------------------------------------------------------------

NS_MAIN = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"
NS_REL = "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}"
NS_PKG_REL = "{http://schemas.openxmlformats.org/package/2006/relationships}"
RE_FORMULA_OPEN = re.compile(rb"<f[ >/]")
# Formel ohne gespeicherten Wert: kein <v> oder leeres <v/> / <v></v> nach der Formel.
RE_FORMULA_NO_CACHE = re.compile(rb"(?:<f[^>]*/>|</f>)\s*(?:<v\s*/>|<v>\s*</v>)?\s*</c>")


def _count_formulas(zf: zipfile.ZipFile, member: str) -> tuple[int, int]:
    """Zählt Formelzellen und Formeln ohne gespeicherten Wert im Sheet-XML (Stream, ohne Inhalte)."""
    n_f = n_nocache = 0
    carry = b""
    with zf.open(member) as fh:
        while True:
            chunk = fh.read(4 << 20)
            if not chunk:
                break
            buf = carry + chunk
            cut = buf.rfind(b"</c>")
            cut = cut + 4 if cut >= 0 else 0
            part, carry = buf[:cut], buf[cut:]
            n_f += len(RE_FORMULA_OPEN.findall(part))
            n_nocache += len(RE_FORMULA_NO_CACHE.findall(part))
    n_f += len(RE_FORMULA_OPEN.findall(carry))
    n_nocache += len(RE_FORMULA_NO_CACHE.findall(carry))
    return n_f, n_nocache


def excel_package_info(path: Path) -> tuple[dict, dict[str, dict]]:
    """Paketebene: Tab-Sichtbarkeit, Formeln, Kommentare, externe Links, Pivots, Autor-Metadaten."""
    with zipfile.ZipFile(path) as zf:
        names = zf.namelist()
        wb_xml = ET.fromstring(zf.read("xl/workbook.xml"))
        rels_xml = ET.fromstring(zf.read("xl/_rels/workbook.xml.rels"))
        targets = {r.get("Id"): r.get("Target") for r in rels_xml.iter(f"{NS_PKG_REL}Relationship")}
        sheets = {}
        for sh in wb_xml.iter(f"{NS_MAIN}sheet"):
            target = targets.get(sh.get(f"{NS_REL}id"), "")
            member = target.lstrip("/") if target.startswith("/") else f"xl/{target}"
            n_f, n_nocache = _count_formulas(zf, member) if member in names else (0, 0)
            sheets[sh.get("name")] = {"state": sh.get("state", "visible"), "n_formulas": n_f,
                                      "formulas_without_cached_value": n_nocache}
        has_author = False
        if "docProps/core.xml" in names:
            core = zf.read("docProps/core.xml").decode("utf-8", "ignore")
            has_author = bool(re.search(r"<dc:creator>[^<]+</dc:creator>|<cp:lastModifiedBy>[^<]+<", core))
        pkg = {
            "n_sheets": len(sheets),
            "n_hidden_sheets": sum(s["state"] != "visible" for s in sheets.values()),
            "comment_parts": sum(1 for n in names if re.match(r"xl/(comments\d*|threadedComments/)", n)),
            "external_links": sum(1 for n in names if n.startswith("xl/externalLinks/") and n.endswith(".xml")),
            "pivot_tables": sum(1 for n in names if n.startswith("xl/pivotTables/") and n.endswith(".xml")),
            "author_metadata": "ja" if has_author else "nein",
        }
    return pkg, sheets


def profile_excel(path: Path) -> tuple[dict, list[dict], list[dict]]:
    pkg, sheet_meta = excel_package_info(path)
    wb = load_workbook(path, read_only=True, data_only=True)
    sheet_rows, col_rows = [], []
    try:
        for ws in wb.worksheets:
            info, cols = profile_rows(ws.iter_rows(values_only=True))
            meta = sheet_meta.get(ws.title, {})
            sheet_rows.append({"sheet": ws.title, "state": meta.get("state", ""), **info,
                               "n_formulas": meta.get("n_formulas"),
                               "formulas_without_cached_value": meta.get("formulas_without_cached_value")})
            col_rows += [{"sheet": ws.title, **c} for c in cols]
    finally:
        wb.close()
    return pkg, sheet_rows, col_rows


# --- Text/CSV -------------------------------------------------------------------------------------------

def detect_encoding(path: Path) -> str:
    """UTF-8 (mit/ohne BOM), sonst cp1252. Prüft die ganze Datei inkrementell."""
    with path.open("rb") as fh:
        start = fh.read(3)
    enc = "utf-8-sig" if start == b"\xef\xbb\xbf" else "utf-8"
    decoder = codecs.getincrementaldecoder("utf-8")()
    try:
        with path.open("rb") as fh:
            while chunk := fh.read(8 << 20):
                decoder.decode(chunk)
            decoder.decode(b"", final=True)
        return enc
    except UnicodeDecodeError:
        return "cp1252"


def detect_delimiter(sample: str) -> str | None:
    lines = [ln for ln in sample.splitlines()[:50] if ln.strip()]
    best, best_score = None, 0
    for d in (";", ",", "\t", "|"):
        counts = [ln.count(d) for ln in lines]
        if not counts or max(counts) == 0:
            continue
        mode = Counter(counts).most_common(1)[0]
        score = mode[0] * mode[1]  # konsistente Spaltenzahl über viele Zeilen
        if mode[0] > 0 and score > best_score:
            best, best_score = d, score
    return best


def profile_text(path: Path) -> tuple[dict, list[dict], list[dict]]:
    encoding = detect_encoding(path)
    with path.open(encoding=encoding, newline="") as fh:
        sample = fh.read(256 << 10)
    delimiter = detect_delimiter(sample)
    pkg = {"encoding": encoding, "delimiter": {"\t": "TAB"}.get(delimiter, delimiter) if delimiter else "",
           "n_sheets": 1}
    if delimiter is None:
        with path.open(encoding=encoding, newline="") as fh:
            n_lines = sum(1 for _ in fh)
        info = {"sheet": "(Text)", "state": "", "header_row": None, "n_data_rows": n_lines, "n_columns": 0,
                "notes": "kein Trennzeichen erkannt – nicht als Tabelle gelesen"}
        return pkg, [info], []
    with path.open(encoding=encoding, newline="") as fh:
        reader = csv.reader(fh, delimiter=delimiter)
        info, cols = profile_rows(reader)
    return pkg, [{"sheet": "(Datei)", "state": "", **info}], [{"sheet": "(Datei)", **c} for c in cols]


# --- Gesamtinventar -------------------------------------------------------------------------------------

def _sha256_16(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        while chunk := fh.read(8 << 20):
            h.update(chunk)
    return h.hexdigest()[:16]


@dataclass
class Inventory:
    files: pd.DataFrame
    sheets: pd.DataFrame
    columns: pd.DataFrame


def build_inventory(roots: list[tuple[str, Path]], progress=None) -> Inventory:
    """Erstellt das Strukturinventar.

    Args:
        roots: Liste ``(label, pfad)``; Pfad ist ein Ordner (rekursiv) oder eine einzelne Datei.
        progress: optionale Funktion ``(text) -> None`` für Fortschrittsmeldungen (nur Dateinamen).
    """
    file_rows, sheet_rows, col_rows = [], [], []
    for label, root in roots:
        paths = sorted(p for p in root.rglob("*") if p.is_file()) if root.is_dir() else [root]
        for path in paths:
            rel = f"{label}/{path.relative_to(root).as_posix()}" if root.is_dir() else f"{label}/{path.name}"
            base = {"file": rel, "format": path.suffix.lower().lstrip("."),
                    "size_mb": round(path.stat().st_size / 2**20, 2)}
            if path.name.lower() in IGNORED_FILES:
                file_rows.append({**base, "status": "ignoriert (Systemdatei)"})
                continue
            if path.suffix.lower() not in TABULAR_SUFFIXES:
                file_rows.append({**base, "status": "nicht gelesen (Format nicht unterstützt)"})
                continue
            t0 = time.perf_counter()
            try:
                if path.suffix.lower() in {".xlsx", ".xlsm"}:
                    pkg, sheets, cols = profile_excel(path)
                else:
                    pkg, sheets, cols = profile_text(path)
                status = "gelesen"
            except Exception as exc:  # Struktur-Inventar soll weiterlaufen; Meldung ohne Inhalte
                pkg, sheets, cols, status = {}, [], [], f"Fehler: {type(exc).__name__}"
            secs = round(time.perf_counter() - t0, 1)
            file_rows.append({**base, "sha256_16": _sha256_16(path), "status": status, "seconds": secs, **pkg})
            sheet_rows += [{"file": rel, **s} for s in sheets]
            col_rows += [{"file": rel, **c} for c in cols]
            if progress:
                progress(f"{status:8s} {secs:6.1f}s  {rel}")
    return Inventory(pd.DataFrame(file_rows), pd.DataFrame(sheet_rows), pd.DataFrame(col_rows))


def schema_groups(columns: pd.DataFrame) -> pd.DataFrame:
    """Fasst Tabellen mit identischer Spaltenliste zusammen (z. B. 27 gleich gebaute Ticket-CSVs)."""
    if columns.empty:
        return pd.DataFrame(columns=["schema_id", "n_tables", "tables", "column_names"])
    sig = columns.groupby(["file", "sheet"])["column_name"].apply(lambda s: " | ".join(s)).reset_index()
    out = []
    for i, (cols, g) in enumerate(sig.groupby("column_name", sort=False), start=1):
        out.append({"schema_id": f"S{i:02d}", "n_tables": len(g),
                    "tables": "; ".join(f"{f} [{s}]" for f, s in zip(g["file"], g["sheet"])),
                    "column_names": cols})
    return pd.DataFrame(out).sort_values("n_tables", ascending=False)


def write_inventory(inv: Inventory, out_dir: Path) -> dict[str, Path]:
    """Schreibt ``source_inventory.xlsx`` und ``source_inventory.md`` (nur Struktur)."""
    out_dir.mkdir(parents=True, exist_ok=True)
    groups = schema_groups(inv.columns)
    personal = inv.columns[inv.columns["personal_category"] != ""] if not inv.columns.empty else inv.columns
    xlsx = out_dir / "source_inventory.xlsx"
    with pd.ExcelWriter(xlsx, engine="openpyxl") as w:
        pd.DataFrame({"Hinweis": [
            "Strukturinventar (Datenmodus structure_only). Enthält KEINE Zellinhalte.",
            "Personenbezogene Spalten: nur Name und Kategorie; Statistik unterdrückt (Kategorie 'direkt').",
        ]}).to_excel(w, sheet_name="Start", index=False)
        inv.files.to_excel(w, sheet_name="Dateien", index=False)
        inv.sheets.to_excel(w, sheet_name="Tabs", index=False)
        inv.columns.to_excel(w, sheet_name="Spalten", index=False)
        groups.to_excel(w, sheet_name="Schema-Gruppen", index=False)
        personal.to_excel(w, sheet_name="Personenbezug", index=False)
        w.book.properties.creator = "fcsg-analysis"

    md = out_dir / "source_inventory.md"
    md.write_text(render_markdown(inv, groups), encoding="utf-8")
    return {"xlsx": xlsx, "md": md}


def _fmt(v) -> str:
    if v is None or (isinstance(v, float) and v != v):
        return ""
    return str(v).replace("|", "\\|").replace("\n", " ")


def md_table(df: pd.DataFrame) -> str:
    """Markdown-Tabelle ohne Zusatzpaket."""
    if df.empty:
        return "–"
    lines = ["| " + " | ".join(map(str, df.columns)) + " |", "|" + "---|" * len(df.columns)]
    lines += ["| " + " | ".join(_fmt(v) for v in row) + " |" for row in df.itertuples(index=False)]
    return "\n".join(lines)


def render_markdown(inv: Inventory, groups: pd.DataFrame) -> str:
    """Kompakter Lesebericht: Dateien, Tabs, und Spalten je Schema-Gruppe (keine Zellinhalte)."""
    out = ["# Strukturinventar (structure_only – keine Zellinhalte)", ""]
    out.append("## Dateien")
    fcols = [c for c in ("file", "size_mb", "status", "seconds", "n_sheets", "n_hidden_sheets", "encoding",
                         "delimiter", "comment_parts", "external_links", "pivot_tables", "author_metadata")
             if c in inv.files.columns]
    out.append(md_table(inv.files[fcols]) if not inv.files.empty else "–")
    out += ["", "## Tabs"]
    if not inv.sheets.empty:
        scols = [c for c in ("file", "sheet", "state", "header_row", "n_data_rows", "n_columns",
                             "internal_empty_rows", "total_row_candidates", "n_formulas",
                             "formulas_without_cached_value", "notes") if c in inv.sheets.columns]
        out.append(md_table(inv.sheets[scols]))
    out += ["", "## Spalten je Schema-Gruppe"]
    for _, g in groups.iterrows():
        first_file, first_sheet = g["tables"].split("; ")[0].rsplit(" [", 1)
        first_sheet = first_sheet.rstrip("]")
        cols = inv.columns[(inv.columns["file"] == first_file) & (inv.columns["sheet"] == first_sheet)]
        out += ["", f"### {g['schema_id']} – {g['n_tables']} Tabelle(n)", "", f"Tabellen: {g['tables']}", ""]
        show = cols[["col", "column_name", "personal_category", "dominant_type", "type_mix", "missing_share",
                     "date_min", "date_max", "n_distinct_dates", "content_flags"]]
        out.append(md_table(show))
        if g["n_tables"] > 1:
            out.append("\n(Statistik der ersten Tabelle; alle Tabellen der Gruppe im Excel-Blatt «Spalten».)")
    return "\n".join(out) + "\n"

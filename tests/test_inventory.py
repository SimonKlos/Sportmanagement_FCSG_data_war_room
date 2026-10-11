"""Strukturinventar: erkennt Struktur korrekt und gibt KEINE Zellinhalte aus.

Alle Dateien werden hier künstlich erzeugt. Die «SENTINEL»-Werte simulieren Personendaten und dürfen
in keinem Output (Markdown, Excel, Konsole) erscheinen.
"""

import datetime as dt

import pytest
from openpyxl import Workbook, load_workbook

from fcsg.cli import main
from fcsg.inventory import build_inventory, classify, personal_category, write_inventory

SENTINELS = ["SENTINEL", "sentinel", "9471", "1950", "555 12 34", "Geheimweg"]


@pytest.fixture
def raw_dir(tmp_path):
    raw = tmp_path / "raw" / "2099-01-01_Test"
    raw.mkdir(parents=True)

    wb = Workbook()
    ws = wb.active
    ws.title = "Saison FX1"
    ws.append(["Umsatzbericht Testsaison"])
    ws.append([])
    ws.append(["Spieldatum", "Gegner", "Umsatz CHF", "Bons"])
    for i, day in enumerate([1, 8, 15, 22]):
        ws.append([dt.datetime(2099, 8, day), f"Testgegner {i}", 1000 + i, 90 + i])
    ws.append(["Total", None, "=SUM(C4:C7)", None])
    hidden = wb.create_sheet("Inhaber")
    hidden.sheet_state = "hidden"
    hidden.append(["Vorname", "Nachname", "PLZ", "Geburtsdatum", "Info", "Block", "Strasse"])
    for _ in range(3):
        hidden.append(["SENTINELVORNAME", "SENTINELNACHNAME", "9471", dt.datetime(1950, 3, 17),
                       "sentinel.person@example.invalid", "B12", "Geheimweg 1"])
    wb.save(raw / "Umsatz.xlsx")

    (raw / "tickets.csv").write_bytes(
        "Datum;Tarif;Preis;Telefonnr;Notiz\n"
        "01.08.2099;Erwachsene;25.00;+41 79 555 12 34;Zürich\n"
        "02.08.2099;Kinder;10.00;+41 79 555 12 34;+41 79 555 12 34\n".encode("cp1252")
    )
    (raw / "zutritt.txt").write_text(
        "TransactionTime\tLesername\tUTId\n2099-08-01 18:01:00\tA1.1\tX1\n2099-08-01 18:02:00\tA1.2\tX2\n",
        encoding="utf-8",
    )
    (raw / ".DS_Store").write_bytes(b"\x00\x01")
    return tmp_path / "raw"


def _all_output_text(paths, stdout=""):
    text = paths["md"].read_text(encoding="utf-8") + stdout
    wb = load_workbook(paths["xlsx"])
    for ws in wb.worksheets:
        for row in ws.iter_rows(values_only=True):
            text += " ".join("" if v is None else str(v) for v in row) + "\n"
    return text


def test_no_cell_values_leak(raw_dir, tmp_path):
    inv = build_inventory([("raw", raw_dir)])
    text = _all_output_text(write_inventory(inv, tmp_path / "out"))
    for s in SENTINELS:
        assert s not in text, f"Wert '{s}' im Output gefunden"


def test_structure_is_detected(raw_dir):
    inv = build_inventory([("raw", raw_dir)])
    files = inv.files.set_index("file")
    xlsx = files.loc["raw/2099-01-01_Test/Umsatz.xlsx"]
    assert xlsx["n_hidden_sheets"] == 1
    assert files.loc["raw/2099-01-01_Test/.DS_Store", "status"].startswith("ignoriert")
    assert files.loc["raw/2099-01-01_Test/tickets.csv", "encoding"] == "cp1252"
    assert files.loc["raw/2099-01-01_Test/tickets.csv", "delimiter"] == ";"
    assert files.loc["raw/2099-01-01_Test/zutritt.txt", "delimiter"] == "TAB"

    sheets = inv.sheets.set_index(["file", "sheet"])
    s = sheets.loc[("raw/2099-01-01_Test/Umsatz.xlsx", "Saison FX1")]
    assert s["header_row"] == 3 and s["n_data_rows"] == 5 and s["total_row_candidates"] == 1
    assert s["n_formulas"] == 1 and s["formulas_without_cached_value"] == 1
    assert sheets.loc[("raw/2099-01-01_Test/Umsatz.xlsx", "Inhaber"), "state"] == "hidden"

    cols = inv.columns.set_index(["file", "sheet", "column_name"])
    d = cols.loc[("raw/2099-01-01_Test/Umsatz.xlsx", "Saison FX1", "Spieldatum")]
    assert d["date_min"] == "2099-08-01" and d["date_max"] == "2099-08-22" and d["n_distinct_dates"] == 4


def test_personal_columns_flagged_and_suppressed(raw_dir):
    inv = build_inventory([("raw", raw_dir)])
    cols = inv.columns.set_index(["sheet", "column_name"])
    for name in ("Vorname", "Nachname", "PLZ", "Geburtsdatum", "Strasse"):
        row = cols.loc[("Inhaber", name)]
        assert row["personal_category"] == "direkt"
        assert row["content_flags"].startswith("Statistik unterdrückt") and row["date_min"] == ""
    assert cols.loc[("Inhaber", "Info"), "personal_category"] == "inhalt_auffaellig"
    assert cols.loc[("Inhaber", "Block"), "personal_category"] == ""
    assert cols.loc[("(Datei)", "Telefonnr"), "personal_category"] == "direkt"
    assert cols.loc[("(Datei)", "Notiz"), "personal_category"] == "inhalt_auffaellig"
    assert cols.loc[("(Datei)", "UTId"), "personal_category"] == "pseudonym"


def test_birthdate_like_ranges_are_suppressed(tmp_path):
    raw = tmp_path / "raw"
    raw.mkdir()
    (raw / "x.csv").write_text("Datum Kauf;Wert\n17.03.1950;1\n18.03.1951;2\n", encoding="utf-8")
    inv = build_inventory([("raw", raw)])
    row = inv.columns.set_index("column_name").loc["Datum Kauf"]
    assert row["date_min"] == "" and "vor 2000" in row["content_flags"]


@pytest.mark.parametrize("name,expected", [
    ("Lesername", ""), ("Artikel Name", ""), ("Name", "direkt"), ("Sortiment", ""), ("Ort", "direkt"),
    ("Abrechnung Kiesplatz", ""), ("Rechnungsnummer", "pseudonym"), ("Kundenfranken", ""),
    ("Seatinfo", "quasi"), ("Reihe", "quasi"), ("E-Mail", "direkt"), ("Geb.-Datum", "direkt"),
])
def test_personal_category_heuristic(name, expected):
    assert personal_category(name) == expected


def test_classify_swiss_formats():
    assert classify("1'234.50")[0] == "zahl_text"
    assert classify("31.12.2099")[1] == dt.date(2099, 12, 31)
    assert classify("18:30")[0] == "zeit_text"


def test_cli_inventory_raw_requires_structure_mode(raw_dir, tmp_path, capsys):
    cfg = tmp_path / "cfg.yaml"
    cfg.write_text(f"data_mode: structure_only\ninput_dir: '{raw_dir.as_posix()}'\n"
                   f"output_dir: '{(tmp_path / 'o').as_posix()}'\n", encoding="utf-8")
    assert main(["inventory-raw", "--config", str(cfg)]) == 0
    out = capsys.readouterr().out
    assert "Personenbezug-Kandidaten" in out
    for s in SENTINELS:
        assert s not in out
    # Derselbe Modus darf keinen Analyse-Lauf starten.
    assert main(["run", "--config", str(cfg)]) == 2

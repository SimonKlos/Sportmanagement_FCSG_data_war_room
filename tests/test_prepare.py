"""Bereinigungslogik (fcsg.prepare) mit künstlichen Daten: Parser, Mapping, Aggregation, Datenschutz."""

import datetime as dt

import numpy as np
import pandas as pd
import pytest

from fcsg.prepare import (
    PrivacyError, _catering_name, _kiesplatz_metric, apply_school_holidays, assert_no_personal_columns,
    competition_group, drop_women, fmt_time, load_school_holidays, parse_chf, parse_form, prepare_access, prepare_ticket_csvs, reader_sector, season_of, to_date, yes_no,
)


def test_parsers():
    assert parse_chf("5,00\xa0CHF") == 5.0 and parse_chf("1'234,50 CHF") == 1234.5 and np.isnan(parse_chf("\xa0"))
    assert fmt_time(19.3) == "19:30" and fmt_time("9:05") == "09:05" and fmt_time(dt.time(14, 15)) == "14:15"
    assert parse_form("S-U-N") == (3.0, 4.0) and np.isnan(parse_form("–")[0])
    assert yes_no("Ja") == 1.0 and yes_no("Nein") == 0.0 and np.isnan(yes_no(None))  # leer bleibt leer
    assert to_date("13.10.2025") == dt.date(2025, 10, 13) and to_date("2022-07-23 17:10:42") == dt.date(2022, 7, 23)
    assert to_date("Total") is None
    assert season_of(dt.date(2025, 8, 1)) == "2025/26" and season_of(dt.date(2026, 3, 1)) == "2025/26"
    assert reader_sector("A1.2 (62)") == "A" and reader_sector("HH-VIP1") == "HH"


@pytest.mark.parametrize("header,expected", [
    ("Zuschauerzahlen Public Netto", "public_attendance"), ("Anwesende", "public_attendance"),
    ("Umsatz Total \ninkl. Mwst", "revenue_total_gross"), ("Umsatz Total exkl. Mwst.", "revenue_total_net"),
    ("Kunenfranken inkl. Mwst.", "kf_gross_reported"), ("Kundenfranken exkl. MwSt.", "kf_net_reported"),
    ("Transaktions-durchschnitt exkl. MwSt.", "avg_receipt_net_reported"),
    ("Umsatz Payfix inkl. MwSt.", "rev_payfix_gross"), ("Umsatz Extern MwSt. exkl.", "rev_extern_net"),
    ("Umsatz Just Eat exkl. MwSt.3", "rev_just_eat_net"), ("Kick-Off", "kickoff"), ("Zeit", "kickoff"),
])
def test_catering_header_mapping(header, expected):
    assert _catering_name(header) == expected


def test_kiesplatz_metric_names():
    assert _kiesplatz_metric("Total Brutto") == "brutto_total"
    assert _kiesplatz_metric("Netto 2.6% Anteil 80%") == "netto_2_6pct_anteil80"
    assert _kiesplatz_metric("Brutto 7.7%") == "brutto_7_7pct"


def test_competition_group():
    assert competition_group("Super League (3. Spieltag)") == "Liga"
    assert competition_group("Conference League Quali. (2. Runde)") == "UEFA"
    assert competition_group("Schweizer Cup (Achtelfinal)") == "Cup"
    assert competition_group("Meisterschaft Frauen") == "Frauen"


def test_privacy_guard():
    assert_no_personal_columns(pd.DataFrame(columns=["match_date", "n_tickets", "tribune", "seat_group"]), "ok")
    for bad in ("Kundenname", "Postleitzahl", "Geburtstag", "UTId", "Barcode", "name"):
        with pytest.raises(PrivacyError):
            assert_no_personal_columns(pd.DataFrame(columns=["match_date", bad]), "x")


@pytest.fixture
def raw_root(tmp_path):
    """Künstliche Rohdaten-Struktur (KEINE Clubdaten)."""
    root = tmp_path / "raw" / "2099_Test"
    (root / "Zutritt").mkdir(parents=True)
    (root / "Ticketing" / "2099-00" / "MS_Herren").mkdir(parents=True)
    (root / "Zutritt" / "zugangsdaten_herren_alteSaisons.txt").write_text(
        "Matchday\tSpieltag\tTransactionTime\tBarcode\tTicketData\tCoding\tLesername\tSeatinfo\tErrorcode\tDisplayMessage\n"
        "2099-08-01\tBSL: TEST\t2099-08-01 17:10:00.000\tK1\tGEHEIM\t270\tA1.1\tS1\t0\tDurchgang erlaubt Willkommen\n"
        "2099-08-01\tBSL: TEST\t2099-08-01 17:10:30.000\tK1\tGEHEIM\t270\tA1.1\tS1\t0\tDurchgang erlaubt Willkommen\n"
        "2099-08-01\tBSL: TEST\t2099-08-01 17:55:00.000\tK2\tGEHEIM\t257\tHH-VIP1\tS2\t0\tDurchgang erlaubt Willkommen\n",
        encoding="utf-8")
    header = "Tribüne,Block,Reihe,Sitz,Ermäßigung,Ticketnummer,Barcode,Datum,Uhrzeit,KundenNr,Filiale,Interne Nummer,Rechnung,Versandart,Zusatzfeld,Summe\n"
    rows = [
        "D | Test,D1,1,1,D1 Vollpreis,T1,B1,25.07.2099,10:00,KUNDE1,Onlineshop,1,R1,Digital,,\"25,00\xa0CHF\"",
        "D | Test,D1,1,2,D1 Vollpreis,T2,B2,25.07.2099,10:00,KUNDE1,Onlineshop,2,R1,Digital,,\"25,00\xa0CHF\"",
        "C | Test,C1,2,1,C1 U16,T3,B3,31.07.2099,18:00,KUNDE2,Kasse,3,R2,Post,,\"10,00\xa0CHF\"",
    ]
    (root / "Ticketing" / "2099-00" / "MS_Herren" / "20990801_MS1_TST.csv").write_text(header + "\n".join(rows) + "\n",
                                                                                         encoding="utf-8-sig")
    return tmp_path / "raw"


def test_access_aggregation(raw_root):
    res = prepare_access(raw_root)
    s = res.summary.iloc[0]
    assert s["scans"] == 3 and s["n_distinct_tickets"] == 2 and s["scans_per_ticket"] == 1.5
    assert set(res.sector_minute["sector"]) == {"A", "HH"}
    assert all(c["status"] == "OK" for c in res.checks)
    for df in (res.summary, res.sector_minute, res.reader, res.coding):
        assert "_key" not in df.columns
        assert not df.astype(str).apply(lambda c: c.str.contains("K1|K2|GEHEIM|S1")).any().any()


def test_ticket_csv_aggregation(raw_root):
    out, checks = prepare_ticket_csvs(raw_root)
    agg = out["tickets_single_agg"]
    assert agg["n_tickets"].sum() == 3 and agg["revenue_chf"].sum() == 60.0
    assert set(agg["match_date"]) == {dt.date(2099, 8, 1)}
    lead = out["tickets_single_leadtime"].set_index("lead_days")["n_tickets"]
    assert lead.loc[7] == 2 and lead.loc[1] == 1
    size = out["tickets_single_purchase_size"].set_index("tickets_in_purchase")["n_purchases"]
    assert size.loc[2] == 1 and size.loc[1] == 1
    assert all(c["status"] == "OK" for c in checks)
    text = " ".join(df.astype(str).to_string() for df in out.values())
    for secret in ("KUNDE1", "R1", "T1", "B1"):
        assert secret not in text.split()  # keine IDs als Werte
    for df in out.values():
        assert not {"KundenNr", "Rechnung", "Ticketnummer", "Barcode", "Reihe", "Sitz", "_purchase"} & set(df.columns)


def test_ticket_csv_skips_women_files(raw_root):
    women = raw_root / "2099_Test" / "Ticketing" / "2099-00" / "MS_Frauen"
    women.mkdir(parents=True)
    src = raw_root / "2099_Test" / "Ticketing" / "2099-00" / "MS_Herren" / "20990801_MS1_TST.csv"
    (women / "20990802_FR1_TST.csv").write_bytes(src.read_bytes())
    out, checks = prepare_ticket_csvs(raw_root)
    assert out["tickets_single_agg"]["n_tickets"].sum() == 3  # nur Herren-Datei
    assert set(out["tickets_single_agg"]["team"]) == {"Herren"}
    assert next(c for c in checks if c["check_id"] == "D016-ticket_csv")["detail"].startswith("1 ")


def test_drop_women():
    """D-016: Frauen-Events werden aus allen Tabellen entfernt, andere Events bleiben."""
    tables = {
        "catering_match": pd.DataFrame({"event_class": ["fcsg_herren", "fcsg_frauen", "anderes_event"],
                                        "match_label": ["FCSG vs. Test", "Frauen FCSG vs. Test", "Konzert"]}),
        "attendance_history": pd.DataFrame({"competition_group": ["Liga", "Frauen"], "competition": ["Super League", "AWSL"]}),
        "article_season": pd.DataFrame({"item_label": ["Bier"]}),  # ohne Scope-Spalte: unverändert
    }
    checks = drop_women(tables)
    assert list(tables["catering_match"]["event_class"]) == ["fcsg_herren", "anderes_event"]
    assert list(tables["attendance_history"]["competition_group"]) == ["Liga"]
    assert len(tables["article_season"]) == 1
    assert {c["check_id"] for c in checks} == {"D016-catering_match", "D016-attendance_history"}


def _holidays(tmp_path, rows):
    p = tmp_path / "holidays.csv"
    p.write_text("school_year,holiday,first_day,last_day,source_id\n" + "\n".join(rows) + "\n", encoding="utf-8")
    return load_school_holidays(p)


def test_apply_school_holidays(tmp_path):
    """D-017 b: vor 2099/00 Recherche statt Teamwert; ausserhalb der Abdeckung leer, nicht 0."""
    hol = _holidays(tmp_path, ["2098/99,Herbstferien,2098-10-03,2098-10-18,T", "2099/00,Herbstferien,2099-10-02,2099-10-17,T"])
    ctx = pd.DataFrame({
        "match_date": [dt.date(2098, 10, 3), dt.date(2098, 10, 19), dt.date(2099, 10, 10), dt.date(2099, 10, 1),
                       dt.date(2097, 5, 1)],
        "season": ["2098/99", "2098/99", "2099/00", "2099/00", "2096/97"],
        "school_holiday": [0.0, 1.0, 1.0, 1.0, 1.0],
    })
    out, stats = apply_school_holidays(ctx, hol, team_from="2099/00")
    assert out["school_holiday"].tolist()[:4] == [1.0, 0.0, 1.0, 1.0]  # Grenztage inklusive; ab 2099/00 Teamwert
    assert np.isnan(out["school_holiday"].iat[4])  # vor der Abdeckung: fehlend
    assert out["school_holiday_team"].tolist() == ctx["school_holiday"].tolist()  # Original bleibt erhalten
    assert out["school_holiday_source"].tolist() == ["agent_recherche_2026-10-11"] * 2 + ["team"] * 2 + \
        ["agent_recherche_2026-10-11"]
    assert out["school_holiday_period"].iat[0] == "Herbstferien"
    assert stats == {"replaced": 3, "changed": 2, "team_period_checked": 2, "team_period_differs": 1,
                     "outside_coverage": 1}


def test_school_holiday_table_validation(tmp_path):
    with pytest.raises(ValueError, match="überlappen"):
        _holidays(tmp_path, ["a,x,2099-01-01,2099-01-10,T", "a,y,2099-01-10,2099-01-20,T"])
    with pytest.raises(ValueError, match="Ende vor Beginn"):
        _holidays(tmp_path, ["a,x,2099-01-10,2099-01-01,T"])


def test_school_holiday_reference_file():
    """Versionierte Referenz (öffentliche Daten) ist lückenlos ladbar; Stichproben gegen die Quellen."""
    hol = load_school_holidays()
    by_day = lambda d: hol[(hol.first_day <= d) & (hol.last_day >= d)]["holiday"].tolist()
    assert by_day(dt.date(2023, 10, 7)) == ["Herbstferien"]  # Open Data 30.09.–23.10.2023 (exkl.)
    assert by_day(dt.date(2024, 8, 11)) == ["Sommerferien"] and by_day(dt.date(2024, 8, 12)) == []  # Schulbeginn
    assert by_day(dt.date(2026, 9, 26)) == ["Herbstferien"]  # Ferienplan: So 27.09.2026 → Samstag davor
    assert set(hol["source_id"]) == {"OD", "FP25", "FP26"}

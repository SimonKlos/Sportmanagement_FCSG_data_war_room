"""Spielkontext-Tabelle Version 5 (D-034): Einlesen mit künstlicher Arbeitsmappe (keine Clubdaten, Jahr 2099)."""
import openpyxl
import pandas as pd
import pytest

from fcsg import config
from fcsg.sources import kontext

KOPF = list(kontext._SPALTEN)


def _mappe(tmp_path, zeilen, kopf=KOPF):
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Übersicht"
    ws.append(kopf)
    for z in zeilen:
        ws.append([z.get(h) for h in kopf])
    p = tmp_path / "kontext_v5.xlsx"
    wb.save(p)
    return p


def test_v5_wird_gelesen(tmp_path, monkeypatch):
    p = _mappe(tmp_path, [
        {"Datum": "2099-08-01", "Wochentag": "Samstag", "Anstoss (Lokalzeit)": "18:00", "Wettbewerb": "Super League",
         "Gegner": "FC Basel", "Gegner-Kategorie": "Topspiel", "Resultat (FCSG : Gegner)": "2:1",
         "Platzierung FCSG vor Spiel": 4, "Punkte FCSG vor Spiel": 12, "Platzierung Gegner vor Spiel": 1,
         "Punkte Gegner vor Spiel": 15, "Form FCSG (letzte 5 SL-Spiele)": "S-U-N", "TV-Übertragung": "Blue Sport",
         "Free-TV (SRF)": "Nein", "Temperatur Anstossstunde (°C)": 21.5,
         "Niederschlag 1 h vor bis 2 h nach Anstoss (mm)": 0.6, "Schulferien Stadt SG": "Ja",
         "Feiertag Kt. SG": "Nein", "Parallelevent Stadt SG": "Nein", "Covid-Massnahmen": "Nein"},
        {"Datum": "2099-09-01", "Anstoss (Lokalzeit)": "20:30", "Wettbewerb": "Schweizer Cup", "Gegner": "FC Zürich",
         "Schulferien Stadt SG": "n/a", "Free-TV (SRF)": "Ja"},
    ])
    monkeypatch.setattr(config, "KONTEXT_FILE", p)
    df = kontext.lade_kontext()
    a, b = df.iloc[0], df.iloc[1]
    assert a["rang_fcsg_kontext"] == 4 and a["punkte_gegner_kontext"] == 15 and a["form_fcsg_punkte_kontext"] == 4
    assert a["temp_tagesmittel"] == 21.5 and a["schulferien"] is True and a["resultat_bekannt"]
    assert b["wettbewerb"] == "Cup" and bool(b["free_tv_srf"]) and not b["resultat_bekannt"]
    assert pd.isna(b["schulferien"]) and pd.isna(b["rang_gegner_kontext"])  # «n/a»/leer bleibt fehlend


def test_alte_version_bricht_ab(tmp_path, monkeypatch):
    alt = ["Datum", "Wochentag", "Anstosszeit", "Wettbewerb", "Gegner", "Resultat"]
    monkeypatch.setattr(config, "KONTEXT_FILE", _mappe(tmp_path, [{"Datum": "2099-08-01"}], kopf=alt))
    with pytest.raises(ValueError, match="Version 5"):
        kontext.lade_kontext()

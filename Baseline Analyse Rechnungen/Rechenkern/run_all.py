"""Auswertung «Untapped Business» FC St.Gallen 1879 – ein Aufruf erzeugt Phase 1 und die Ideen-Grundlage.

    python run_all.py                 # Standard: «2. Modellierung/Ergebnisse_Phase1» und «…/Ergebnisse_Ideen_Grundlage»
    python run_all.py --ohne-grafiken # schneller, ohne PNG-Grafiken
    python run_all.py --ausgabe PFAD  # anderer Zielordner für Phase 1
    python run_all.py --ohne-ideen    # nur Phase 1, ohne Ideen-Grundlage
    python run_all.py --ideen-ausgabe PFAD           # anderer Zielordner für die Ideen-Grundlage
    python run_all.py --daten PFAD --kontext DATEI   # Rohdaten/Kontexttabelle liegen an einem anderen Ort

Rohdaten werden nur gelesen. Ausgegeben werden ausschliesslich Aggregate (keine Personen- oder ID-Felder).
Exit-Code: 0 = alles bestanden, 1 = Eingaben fehlen, 2 = Phase-1-Importtest nicht bestanden,
3 = Ideen-Grundlage: Qualitätsprüfung nicht bestanden oder Abbruch (Phase 1 ist dann trotzdem vollständig geschrieben).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import sys
import time
from importlib import metadata
from pathlib import Path

import pandas as pd

sys.dont_write_bytecode = True          # keine __pycache__-Ordner im synchronisierten Projektordner
sys.path.insert(0, str(Path(__file__).resolve().parent))

from fcsg import __version__, config, qa  # noqa: E402
from fcsg.analysis import arrival, attendance, baseline, catering, models, reto  # noqa: E402
from fcsg.datamodel import baue_modell  # noqa: E402
from fcsg.log import befunde_tabelle, logger, setup_logging  # noqa: E402
from fcsg.mart import baue_mart  # noqa: E402
from fcsg.pipeline import lade_rohdaten  # noqa: E402
from fcsg.report import excel, grafiken, inhalte, methodennotiz  # noqa: E402
from fcsg.sources import korrekturen  # noqa: E402

# (Schlüssel, Blattname, Beschreibung) – Reihenfolge = Reihenfolge in der Arbeitsmappe
BLAETTER = [
    ("aenderungsprotokoll", "00_Aenderungsprotokoll", "Änderungen gegenüber v1.0.1 (Bemerkungs-Codierung, Brutto/Netto der Artikelauswertung) mit Vorher/Nachher."),
    ("reto_abgleich", "01_Reto_Abgleich", "Retos Zahlen reproduziert bzw. Abweichung erklärt (Deliverable B)."),
    ("datenqualitaet", "02_Datenqualitaet", "Alle Befunde mit Ort, Auswirkung und Behandlung (hoch → info)."),
    ("importtests", "03_Importtests", "Automatisierte Prüfungen: Eindeutigkeit, Join-Kardinalität, Identitäten, Summenabgleich, Datenschutz."),
    ("quelleninventar", "04_Quelleninventar", "Gelieferte und NICHT gelieferte Quellen (u.a. Merchandise)."),
    ("abdeckung", "05_Abdeckung", "Abdeckungsmatrix: Pflichtspiele je Saison und Modul (Abdeckung statt fiktivem Gesamtdatensatz)."),
    ("gemeinsame_stichproben", "06_Gemeinsame_Stichproben", "Tatsächliche gemeinsame Stichprobe je Analysekombination."),
    ("unmatched", "07_Unmatched", "Unmatched-Report: nicht zuordenbare Zeilen je Quelle mit Grund (Pflichtoutput)."),
    ("duplikate", "08_Duplikate", "Duplikatreport (mehrere Events pro Datum, Mehrfachscans)."),
    ("korrekturen", "09_Korrekturen", "Belegte manuelle Korrekturen (overrides/korrekturen.csv)."),
    ("datenwoerterbuch", "10_Datenwoerterbuch", "Spaltenwörterbuch der Kerntabellen."),
    ("mart_match", "A1_mart_match", "Ein Heimspiel pro Zeile: Zielgrössen, Kontext, Diagnose und Verfügbarkeitsflags."),
    ("dim_match", "A2_dim_match", "Spielkalender mit stabiler match_id, Anpfiff (Mehrheit der Quellen) und Status."),
    ("dim_match_context", "A3_dim_match_context", "Kontextvariablen je Spiel mit Quelle (Kontexttabelle, Resultate, MeteoSchweiz, Kalender)."),
    ("spiel_kpi", "A4_Spiel_KPI", "Spiel-KPI-Tabelle (Paket A) inkl. Prüfspalten und Ausreisser-Flags."),
    ("saison_kpi", "A5_Saison_KPI", "Saisonwerte als Summe/Summe je Wettbewerb (ungewichtet nur zum Vergleich)."),
    ("catering_trend", "A6_Catering_Trend", "Langfristiger KF-Trend ab 2018/19 (inkl. MwSt)."),
    ("scan_ist", "A7_Scan_IST", "Abgleich Drehkreuz-Scans vs. IST je Spiel mit Erklärung."),
    ("entwicklung_abgleich", "A8_Entwicklung_Abgleich", "Gegenprobe eigene Saisonsummen vs. Blatt «Entwicklung»."),
    ("noshow_kontext", "B1_NoShow_Kontext", "No-Show nach Kontextmerkmal (deskriptiv, saisonbereinigt)."),
    ("tickettyp_noshow", "B2_Tickettyp_NoShow", "Näherung No-Show Einzeltickets vs. Rest (≈Abos), 21/22 und 22/23."),
    ("tickettyp_je_spiel", "B3_Tickettyp_je_Spiel", "Ticket-Typ-Näherung je Spiel."),
    ("eintritt_segmente", "B4_Eintritt_Segmente", "Eintrittsquote Einzeltickets nach Kanal, Tarif, Tribüne, Vorlauf, Bestellgrösse."),
    ("absatz_je_spiel", "B5_Absatz_je_Spiel", "Einzelticket-Vorlauf je Spiel (t50/t80/t95, Spieltagsanteil)."),
    ("absatzkurven", "B6_Absatzkurven", "Kumulierte Einzelticket-Absatzkurven je Spiel (0–60 Tage vor Spiel)."),
    ("absatz_segmente", "B7_Absatz_Segmente", "Vorlauf nach Tribüne, Tarif und Kanal."),
    ("absatz_ausverkauft", "B8_Absatz_Ausverkauft", "Vorlauf ausverkaufter vs. nicht ausverkaufter Spiele."),
    ("bestellgroesse", "B9_Bestellgroesse", "Tickets pro Bestellung je Saison."),
    ("abo_snapshot", "B10_Abo_Snapshot", "Saisonabos 2026/27 nach Tribüne, Tarif, Kanal und Abo-Form."),
    ("soll_zerlegung", "B11_SOLL_Zerlegung", "SOLL-Formeln 2025/26 zerlegt (Einzeltickets je Verkaufsstelle + Abo-Bestand)."),
    ("kf_zerlegung", "C1_KF_Zerlegung", "Varianzzerlegung ln KF = ln Bons/Anwesende + ln Ø Bon."),
    ("kf_korrelationen", "C2_KF_Korrelationen", "Korrelationen KF mit Ø Bon und Bons/Anwesende (Retos Werte)."),
    ("kf_je_spiel", "C3_KF_je_Spiel", "KF-Komponenten je Spiel (ab 2023/24)."),
    ("zahlungswege", "C4_Zahlungswege", "Umsatz nach Zahlungsweg je Saison."),
    ("artikel_gruppen", "C5_Artikel_Gruppen", "Sortimentsmix je Saison (Gruppen), Anteile auf einheitlicher Brutto-Basis (Datei: 23/24–24/25 brutto, 25/26 netto)."),
    ("artikel_top15", "C6_Artikel_Top15", "Top-15-Artikel je Saison inkl. Erlös je Einheit (brutto, einheitliche Basis)."),
    ("artikel_abgleich", "C7_Artikel_Abgleich", "Artikelsumme (brutto) vs. Payfix und Catering inkl. MwSt; MwSt-Klassen vs. Gruppe Alkohol."),
    ("kiesplatz_je_spiel", "C8_Kiesplatz_je_Spiel", "Kiesplatz je Spiel (Teilmenge des Catering-Totals)."),
    ("kiesplatz_staende", "C9_Kiesplatz_Staende", "Kiesplatz je Verkaufsstelle und Saison."),
    ("kiesplatz_doppelzaehlung", "C10_Kiesplatz_Doppelz", "Doppelzählungsprüfung Kiesplatz vs. Catering-Standspalten 2021/22."),
    ("elastizitaet", "C11_Elastizitaet", "Elastizität Umsatz ~ Public-Anwesende (Association)."),
    ("operative_hinweise", "C12_Operative_Hinweise", "Operative Hinweise aus Catering-Bemerkungen je Saison."),
    ("ankunft_je_spiel", "D1_Ankunft_je_Spiel", "Ankunftskennzahlen je Spiel (vollständige Zutrittslieferungen)."),
    ("ankunft_je_sektor", "D2_Ankunft_je_Sektor", "Ankunft je Spiel und Eingang (Sektor = Lesername)."),
    ("ankunftskurve_sektor", "D3_Kurve_Sektor", "Mittlere Ankunftskurve je Eingang."),
    ("ankunftskurve_anstosszeit", "D4_Kurve_Anstoss", "Mittlere Ankunftskurve je Anstosszeit."),
    ("leserabdeckung", "D5_Leserabdeckung", "Aktive Drehkreuz-Leser je Saison."),
    ("ankunft_konsum", "D6_Ankunft_Konsum", "Zusammenhang Frühankunft und Konsum (aggregierte Spiele, keine Kausalität)."),
    ("ankunft_reto", "D7_Ankunft_Reto", "Ankunftskennzahlen in Retos Stichprobe und gesamt."),
    ("einlass_je_eingang", "D8_Einlass_je_Eingang", "Geschätzte Toröffnung je Eingang (1 %-Punkt) und Konsumfenster."),
    ("toroeffnung_did", "D9_Toroeffnung_DiD", "Natürliches Experiment: Sektor D öffnet ab 02.04.2023 früher (Differenz-in-Differenzen)."),
    ("toroeffnung_konsum", "D10_Toroeffnung_Konsum", "KF-Abweichung 2022/23 vor/nach der Umstellung (nicht belastbar, n klein)."),
    ("toroeffnung_verlauf", "D11_Toroeffnung_Verlauf", "Einlass und Ankunft je Spiel für Sektoren A, C, D."),
    ("kontext_effekt_matrix", "K1_Kontext_Effekt_Matrix", "Kontext-Effekt-Matrix je Zielgrösse (Deliverable C)."),
    ("modellguete", "K2_Modellguete", "Modellgüte: R², Leave-one-season-out vs. Saisonmittel, Smearing."),
    ("sensitivitaet", "K3_Sensitivitaet", "Koeffizienten unter Scope-, Variablen- und Ausreisser-Varianten."),
    ("loso_folds", "K4_LOSO_Folds", "Validierung je ausgelassener Saison."),
    ("variablen_einordnung", "K5_Variablen_Einordnung", "Einordnung extern / teilweise beeinflussbar / Clubhebel."),
    ("diagnosekarte", "K6_Diagnosekarte", "Diagnosekarte je Spiel (Deliverable D) – Referenzlücken, keine Potenzialsumme."),
    ("diagnose_muster", "K7_Diagnose_Muster", "Wiederkehrende Abweichungen nach operativen Merkmalen."),
    ("klaerungsfragen", "E1_Klaerungsfragen", "Konkrete Klärungsfragen an Sandro/FCSG mit Evidenz (Deliverable E)."),
    ("phase2_kandidaten", "E2_Phase2_Kandidaten", "Prüfkandidaten für Phase 2 (nicht quantifiziert)."),
    ("grafiken", "E3_Grafiken", "Verzeichnis der Grafiken mit Kernaussage."),
]
CSV_EXPORT = ["mart_match", "kontext_effekt_matrix", "modellguete", "diagnosekarte", "saison_kpi", "reto_abgleich",
              "datenqualitaet", "abdeckung", "klaerungsfragen", "phase2_kandidaten"]


def _md5(pfad: Path) -> str:
    h = hashlib.md5()
    with open(pfad, "rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def _laufinfo(datenstand, dauer: float) -> dict:
    # followlinks: Datenordner darf aus Verknüpfungen bestehen (z.B. «Zutritt» → «Zutritte» der Lieferung)
    eingaben = sorted(Path(w) / f for w, _, dateien in os.walk(config.DATA_DIR, followlinks=True)
                      for f in dateien if not f.startswith("."))
    eingaben += [config.KONTEXT_FILE, config.WETTER_FILE, config.RESULTATE_FILE, config.OVERRIDES_FILE]
    pakete = {}
    for p in ("pandas", "numpy", "openpyxl", "python-calamine", "statsmodels", "matplotlib", "xlsxwriter"):
        try:
            pakete[p] = metadata.version(p)
        except metadata.PackageNotFoundError:
            pakete[p] = "nicht installiert"
    return {
        "zeitpunkt": time.strftime("%Y-%m-%d %H:%M:%S"), "version_auswertung": __version__,
        "datenstand_letztes_spiel_mit_ist": f"{datenstand:%d.%m.%Y}", "laufzeit_sekunden": round(dauer, 1),
        "python": platform.python_version(), "pakete": pakete,
        "eingabedateien": [{"datei": str(p.relative_to(config.PROJECT_ROOT)) if p.is_relative_to(config.PROJECT_ROOT) else p.name,
                            "bytes": p.stat().st_size, "md5": _md5(p)} for p in eingaben if p.exists()],
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--ausgabe", type=Path, default=None, help="Zielordner (Standard: 2. Modellierung/Ergebnisse_Phase1)")
    ap.add_argument("--ohne-grafiken", action="store_true", help="PNG-Grafiken nicht erzeugen")
    ap.add_argument("--daten", type=Path, default=None, help="Ordner «1. Daten FCSG» (Standard: im Projektordner)")
    ap.add_argument("--kontext", type=Path, default=None,
                    help="Spielkontext-Tabelle (Standard: 2. Modellierung/Spielkontext_Tabelle_FCSG_3.xlsx)")
    ap.add_argument("--ohne-ideen", action="store_true", help="Ideen-Grundlage nicht erzeugen (nur Phase 1)")
    ap.add_argument("--ideen-ausgabe", type=Path, default=None,
                    help="Zielordner der Ideen-Grundlage (Standard: 2. Modellierung/Ergebnisse_Ideen_Grundlage)")
    args = ap.parse_args()
    setup_logging()
    config.setze_datenpfade(args.daten, args.kontext)
    ziel = args.ausgabe or config.OUTPUT_DIR
    fehlend = config.fehlende_pflichteingaben()
    if fehlend:
        for eintrag in fehlend:
            logger.error("Nicht gefunden – %s", eintrag)
        logger.error('Pfade angeben: python run_all.py --daten "<Ordner 1. Daten FCSG>" '
                     '--kontext "<Spielkontext_Tabelle_FCSG_3.xlsx>" (siehe README, Abschnitt 1)')
        return 1
    t0 = time.time()

    r = lade_rohdaten()
    m = baue_modell(r)
    res: dict = {}
    res.update(baseline.baseline(r, m))
    k = res["spiel_kpi"]
    res.update(attendance.anwesenheit(r, m, k))
    res.update(catering.catering(r, m, k))
    res.update(arrival.ankunft(r, m, k, res["scan_ist"]))
    d = models.modell_daten(k, m.dim_match_context, res["ankunft_je_spiel"])
    res["modell_daten"] = d               # Eingabe der Ideen-Stufe (gleiche Modellstichprobe), kein Ausgabeblatt
    res.update(models.kontextmodelle(d))
    res.update(models.diagnosekarte(res["diagnosekarte_lang"], d, m.fact_attendance_match, m.fact_catering_match))
    res.update(arrival.toroeffnung_experiment(res["ankunft_je_sektor"], k, res["diagnosekarte_lang"]))
    res["mart_match"] = baue_mart(m, res)
    res["dim_match"] = m.dim_match
    res["dim_match_context"] = m.dim_match_context
    res["unmatched"] = m.unmatched
    res["duplikate"] = m.duplikate
    res["korrekturen"] = korrekturen.lade_korrekturen()
    res["abdeckung"] = qa.abdeckung(res["mart_match"])
    res["gemeinsame_stichproben"] = qa.gemeinsame_stichproben(res["mart_match"])
    res["quelleninventar"] = qa.quelleninventar(r)
    inv = r.ticket_inventar
    roh_info = {"csv_herren_spiele": int((~inv["ist_abo"] & (inv["wettbewerb"] != "Frauen")).sum()),
                "csv_frauen": int((~inv["ist_abo"] & (inv["wettbewerb"] == "Frauen")).sum()),
                "abos_herren": int((r.abos["team"] == "Herren").sum()),
                "scans_erlaubt": int(r.zutritt_info.loc[r.zutritt_info["lieferung"] == config.ZUTRITT_ERLAUBT_FILE.name, "scans_roh"].sum()),
                "kontext_zeilen": len(r.kontext), "kontext_gespielt": int(r.kontext["resultat_bekannt"].sum())}
    res["reto_abgleich"] = reto.reto_abgleich(res, roh_info)
    res["klaerungsfragen"] = inhalte.klaerungsfragen(res)
    res["phase2_kandidaten"] = inhalte.phase2_kandidaten(res)

    ziel.mkdir(parents=True, exist_ok=True)
    if args.ohne_grafiken:
        res["grafiken"] = pd.DataFrame(columns=["datei", "titel", "aussage"])
    else:
        res["grafiken"] = grafiken.erstelle_grafiken(res, ziel / "Abbildungen")

    res["datenwoerterbuch"] = inhalte.datenwoerterbuch(
        {n: res[n] for n in ("mart_match", "dim_match", "dim_match_context", "kontext_effekt_matrix", "diagnosekarte")})
    ausgaben = {key: res[key] for key, _, _ in BLAETTER if key in res and key not in ("importtests", "datenqualitaet")}
    res["importtests"] = qa.importtests(r, m, res, ausgaben)
    res["aenderungsprotokoll"] = inhalte.aenderungsprotokoll(res)
    res["datenqualitaet"] = befunde_tabelle()

    blaetter = [(name, res[key], text) for key, name, text in BLAETTER if key in res]
    excel.schreibe_excel(ziel / "FCSG_Phase1_Ergebnisse.xlsx", blaetter)
    (ziel / "Tabellen").mkdir(exist_ok=True)
    for key in CSV_EXPORT:
        res[key].to_csv(ziel / "Tabellen" / f"{key}.csv", index=False, encoding="utf-8-sig")
    info = _laufinfo(m.datenstand, time.time() - t0)
    (ziel / "Laufprotokoll.json").write_text(json.dumps(info, indent=2, ensure_ascii=False), encoding="utf-8")
    methodennotiz.schreibe(ziel / "Methodennotiz_Phase1.md", res, info)

    tests = res["importtests"]
    logger.info("Importtests: %s von %s bestanden", int(tests["bestanden"].sum()), len(tests))
    for _, t in tests[~tests["bestanden"]].iterrows():
        logger.warning("Test NICHT bestanden: %s – %s", t["test"], t["detail"])
    logger.info("Befunde: %s (davon hoch: %s)", len(res["datenqualitaet"]),
                int((res["datenqualitaet"]["schweregrad"] == "hoch").sum()))
    logger.info("Phase 1 fertig in %.0f s. Ergebnisse: %s", time.time() - t0, ziel)

    ideen_ok = True
    if not args.ohne_ideen:
        ideen_ok = _ideen_grundlage(r, m, res, args.ideen_ausgabe or config.IDEEN_DIR, mit_grafiken=not args.ohne_grafiken)
    logger.info("Fertig in %.0f s.", time.time() - t0)
    if not tests["bestanden"].all():
        return 2
    return 0 if ideen_ok else 3


def _ideen_grundlage(r, m, res: dict, ziel: Path, mit_grafiken: bool) -> bool:
    """Ideen-Grundlage auf den fertigen Phase-1-Objekten; ein Fehler hier lässt die geschriebene Phase 1 unberührt."""
    from fcsg.ideen import stufe
    try:
        qa_ideen = stufe.erstelle(r, m, res, ziel, mit_grafiken=mit_grafiken)["qa"]
    except Exception:
        logger.exception("Ideen-Grundlage abgebrochen – Phase 1 ist vollständig geschrieben")
        return False
    for _, t in qa_ideen[~qa_ideen["bestanden"]].iterrows():
        logger.warning("Ideen-Prüfung NICHT bestanden: %s – %s", t["test"], t["detail"])
    return bool(qa_ideen["bestanden"].all())


if __name__ == "__main__":
    sys.exit(main())

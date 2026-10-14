"""Excel der Ideen-Grundlage: alle Tabellen, Hebel-Rechner mit echten Formeln, Szenarien-Blatt und Ideen-Steckbrief.

Die Formeln des Hebel-Rechners bilden ``basis.hebel_szenario()`` exakt nach (gleiche Definition in Python und Excel);
``pruefe_formeln()`` rechnet sie mit einem kleinen Auswerter nach und vergleicht mit Python (Test in qa/pytest).
"""
from __future__ import annotations

import re
from pathlib import Path

import numpy as np
import pandas as pd

from ...report.excel import schreibe_excel
from .. import basis

BLAETTER = [
    ("kernbefunde", "01_Kernbefunde", "Die 12 wichtigsten Befunde mit Zahl und Fundstelle."),
    ("chancenfelder", "02_Chancenfelder", "9 Chancenfelder: Befund, Evidenz, Steuerbarkeit, Hebel-Arithmetik, Leitplanken, Datenlücke, Leitfragen, Pilot."),
    ("reto_ideen_check", "03_Reto_Ideen_Check", "Retos 12 Ideen gegen die Daten geprüft (Datenlage, Vortest, korrigierte Rechenbasis, Einschätzung)."),
    ("datenanfragen", "04_Datenanfragen", "Datenanfragen an Sandro/FCSG, die Chancenfelder freischalten."),
    ("faustwerte", "R1_Faustwerte", "Hebel-Arithmetik je Hebel (isoliert, nicht addieren) für 2025/26 und Ø 23/24–25/26."),
    ("reto_faustwerte", "R2_Reto_Faustwerte", "Retos Faustwerte (18'000 Anwesende) gegenüber den Daten 2025/26."),
    ("basis_saison", "R3_Basis_Saison", "Saisonbasis Meisterschaft: Summen und Mittelwerte je Spiel (Summe/Summe)."),
    ("noshow_kosten", "R4_NoShow_Kosten", "Leere Plätze nach ausverkauft/nicht ausverkauft; Konsum-Referenz je leerem Platz."),
    ("leere_plaetze_saison", "N1_Leere_Plaetze_Saison", "Leere, vergebene Plätze je Saison (SOLL − IST)."),
    ("leere_plaetze_kontext", "N2_Leere_Plaetze_Kontext", "Leere Plätze nach Kontext (Wochentag, Anstosszeit, Winter, Gegner, Temperatur, Monat)."),
    ("zweitmarkt_saison", "N3_Zweitmarkt_Saison", "Zweitmarkt je Saison: Wiederbesetzung, Anteile je Tribüne, Spiele ohne Zweitmarkt in D."),
    ("zweitmarkt_je_spiel", "N4_Zweitmarkt_je_Spiel", "Zweitmarkt und leere Plätze je Meisterschaftsspiel (25/26–26/27)."),
    ("zweitmarkt_vorlauf", "N5_Zweitmarkt_Vorlauf", "Wann wird weiterverkauft (Tage vor dem Spiel)?"),
    ("zweitmarkt_preis", "N6_Zweitmarkt_Preis", "Preis Zweitmarkt vs. gleicher Tarif im selben Spiel (Gebühr)."),
    ("tribuene_2627", "N7_Tribuene_2627", "Nutzung vergebener Plätze und Abo-Anwesenheit je Tribüne (Näherung, 4 Spiele 26/27)."),
    ("tribuene_2627_je_spiel", "N8_Tribuene_2627_je_Spiel", "Tribünen 26/27 je Spiel inkl. UEFA-Kalibrierung."),
    ("einzel_noshow_segmente", "N9_Einzel_NoShow_Segmente", "No-Show der Einzeltickets nach Kanal × Preis × Bestellgrösse (ZKS 21/22–22/23, Bootstrap-KI)."),
    ("absatz_merkmale", "A1_Absatz_Merkmale", "Einzelticket-Merkmale je Spiel (Volumen, Spätkaufanteil, T-7)."),
    ("spieltypen", "A2_Spieltypen", "Regelbasierte Spieltypen mit No-Show, KF und Kontextanteilen."),
    ("spieltypen_tests", "A3_Spieltypen_Tests", "Permutationstests: Typ vs. Gegnerstärke, Top-Gegner, Abend, Winter, No-Show."),
    ("spieltypen_robustheit", "A4_Spieltypen_Robustheit", "Ward-Clustering als Robustheitsprüfung (Silhouette, Bootstrap-Jaccard)."),
    ("spieltypen_zuordnung", "A5_Spieltypen_Zuordnung", "Spieltyp je Spiel."),
    ("fruehindikator", "A6_Fruehindikator", "Frühindikator T-7: Rolling-Origin-Fehler gegen Kontextmodell und Saisonmittel."),
    ("fruehindikator_vorhersagen", "A7_Fruehindikator_Vorhersagen", "Vorhersagen je Spiel mit 80 %-Band (nur frühere Spiele im Training)."),
    ("fruehindikator_korrelation", "A8_Fruehindikator_Korrelation", "Korrelation T-7-Verkäufe mit IST und No-Show je Saison."),
    ("preis_einzel_tribuene", "A9_Preis_Einzel_Tribuene", "Einzelticket-Preise und -Erlöse je Tribüne (deskriptiv, kein Preishebel)."),
    ("preis_abo_tribuene", "A10_Preis_Abo_Tribuene", "Abo-Erlöse 26/27 je Tribüne ohne Hospitality."),
    ("erloes_einzel_saison", "A11_Erloes_Einzel_Saison", "Einzelticket-Erlöse je Saison (Meisterschaft)."),
    ("verweilzeit_eingang", "Z1_Verweilzeit_Eingang", "Verweilminuten vor Anpfiff je Eingang."),
    ("verweilzeit_kontext", "Z2_Verweilzeit_Kontext", "Verweilminuten nach Anstosszeit, Wochentag, Temperatur."),
    ("verweilzeit_je_spiel_eingang", "Z3_Verweilzeit_je_Spiel", "Verweilminuten je Spiel und Eingang."),
    ("einlass_spitzen", "Z4_Einlass_Spitzen", "Einlass-Spitzen je Eingang und Leser vs. Leser-Kapazität."),
    ("einlass_spitzen_je_spiel", "Z5_Einlass_je_Spiel", "Einlass-Spitzen je Spiel."),
    ("toroeffnung_beleg", "Z6_Toroeffnung_Beleg", "Toröffnungs-Experiment Sektor D (aus Phase 1)."),
    ("kf_entwicklung", "K1_KF_Entwicklung", "KF-Entwicklung zerlegt in Kauffrequenz × Ø Bon."),
    ("warenkorb_gruppen", "K2_Warenkorb_Gruppen", "Sortimentsgruppen je Saison (brutto) und Einheiten je 100 Anwesende."),
    ("warenkorb_artikel", "K3_Warenkorb_Artikel", "Top-Artikel: Einheiten je 100 Anwesende je Saison."),
    ("warenkorb_je_bon", "K4_Warenkorb_je_Bon", "Einheiten je Bon und je Anwesendem."),
    ("preis_menge", "K5_Preis_Menge", "Fisher-Zerlegung: Erlös je Einheit × Einheiten je Anwesendem × Sortimentswechsel."),
    ("alkohol_validierung", "K6_Alkohol_Validierung", "Validierung des Alkohol-Proxys (Artikelauswertung, Kiesplatz)."),
    ("alkohol_je_spiel", "K7_Alkohol_je_Spiel", "Alkoholanteil (Normalsatz-Proxy) und KF-Teile je Spiel."),
    ("alkohol_effekt_matrix", "K8_Alkohol_Effekt_Matrix", "Kontexteffekte auf Alkoholanteil, KF Alkohol und KF Food & alkoholfrei."),
    ("alkohol_modellguete", "K9_Alkohol_Modellguete", "Modellgüte der Alkohol-Modelle (R², Leave-one-season-out)."),
    ("durchsatz_knick", "K10_Durchsatz_Knick", "Test auf Durchsatz-Knick bei hoher Auslastung (Wild-Bootstrap)."),
    ("mobiler_verkauf_effekt", "K11_Mobiler_Verkauf_Effekt", "KF/Bons/Ø Bon vs. Kontexterwartung nach mobilem Verkauf (inkl. MDE)."),
    ("mobiler_verkauf_codierung", "K12_Mobiler_Verkauf_Codierung", "Codierung mobiler Verkauf je Saison (aus Bemerkungen)."),
    ("zahlungswege_ideen", "K13_Zahlungswege_Ideen", "Zahlungswege und digitale Kanäle je Saison."),
    ("kiesplatz_wetter", "K14_Kiesplatz_Wetter", "Kiesplatz und Stadion nach Temperatur, Regen, Abend (Substitutionstest)."),
    ("kiesplatz_je_spiel_ideen", "K15_Kiesplatz_je_Spiel", "Kiesplatz je Spiel (Teilmenge des Catering-Totals)."),
    ("phi_evidenz", "K16_Phi_Evidenz", "Evidenz zu φ: Elastizität und Promo-Anteil."),
    ("reto_gaeste_test", "K17_Reto_Gaeste_Test", "Idee 1: KF und Gästeanteil im Nenner."),
    ("ausreisser_zaehlung", "D1_Ausreisser_Zaehlung", "Spiele ausserhalb des 80 %-Bands vs. Zufallserwartung."),
    ("ausreisser_positiv", "D2_Ausreisser_Positiv", "Positive Ausreisser mit Merkmalen."),
    ("ausreisser_merkmale", "D3_Ausreisser_Merkmale", "Merkmalsvergleich positive Ausreisser vs. übrige."),
    ("randfelder_kategorien", "F1_Randfelder_Kategorien", "Catering nach Anlass-Kategorie (inkl. Frauen, Länderspiele, Events)."),
    ("randfelder_frauen", "F2_Randfelder_Frauen", "Frauen-Spiele: Ort, Familyday, Promo, No-Show, KF."),
    ("grafiken_ideen", "G1_Grafiken", "Verzeichnis der Grafiken mit Kernaussage und Datenblatt."),
    ("qa_ideen", "Q1_Qualitaetspruefung", "Automatisierte Prüfungen der Ideen-Grundlage."),
]

GELB = "#FFF4C2"
BASIS_ZEILEN = [  # (Schlüssel, Bezeichnung, Einheit, Zahlformat)
    ("spiele", "Spiele je Saison", "Spiele", "0.0"),
    ("soll_mittel", "Ø SOLL je Spiel (vergebene Plätze)", "Plätze", "#,##0"),
    ("public_netto_mittel", "Ø Public-Anwesende je Spiel (KF-Nenner)", "Personen", "#,##0"),
    ("umsatz_exkl_mittel", "Ø Catering-Umsatz exkl. MwSt je Spiel", "CHF", "#,##0"),
    ("bons_mittel", "Ø Bons (Transaktionen) je Spiel", "Bons", "#,##0"),
    ("kf_exkl", "Kundenfranken exkl. MwSt", "CHF", "0.00"),
    ("bon_exkl", "Ø Bon exkl. MwSt", "CHF", "0.00"),
    ("bons_pro_anwesende", "Bons je Public-Anwesendem", "Bons", "0.000"),
    ("noshow_quote", "No-Show-Quote (1 − IST/SOLL)", "%", "0.0%"),
]
B0 = 6  # erste Zeile der Basiswerte (Excel-Zeile 7)


def _zelle(zeile: int, spalte: int) -> str:
    return f"{chr(ord('A') + spalte)}{zeile + 1}"


def _basis_ref(schluessel: str) -> str:
    i = [k for k, *_ in BASIS_ZEILEN].index(schluessel)
    return f"$D${B0 + i + 1}"


HEBEL_FORMELN = {  # Formeln in Abhängigkeit der Eingabezellen: {V} Veränderung, {P} φ, {A} Anteil Spiele
    "noshow_pp": ("={V}/100*" + _basis_ref("soll_mittel"), "={M}*" + _basis_ref("kf_exkl") + "*{P}"),
    "zusatz_anwesende": ("={V}", "={V}*" + _basis_ref("kf_exkl") + "*{P}"),
    "bons_pro_anwesende": ("={V}*" + _basis_ref("public_netto_mittel"), "={M}*" + _basis_ref("bon_exkl")),
    "frequenz_pct": (None, "={V}/100*" + _basis_ref("umsatz_exkl_mittel")),
    "bon_chf": (None, "={V}*" + _basis_ref("bons_mittel")),
    "kf_chf": (None, "={V}*" + _basis_ref("public_netto_mittel")),
}


def _rechner(e: dict):
    b = e["basis_saison"].set_index("basis")
    r26, mittel = b.loc[basis.REFERENZ_SAISON], b.loc[basis.MITTEL_LABEL]

    def schreiber(wb, ws, fmt):
        f_titel = wb.add_format({"bold": True, "font_size": 14})
        f_h = wb.add_format({"bold": True, "bg_color": "#0B6E4F", "font_color": "white", "text_wrap": True, "valign": "top", "border": 1})
        f_txt = wb.add_format({"text_wrap": True, "valign": "top"})
        f_hinweis = wb.add_format({"text_wrap": True, "valign": "top", "italic": True, "font_color": "#52514e"})
        f_in = {nf: wb.add_format({"num_format": nf, "bg_color": GELB, "border": 1}) for nf in ("0.0", "#,##0", "0.00", "0.000", "0.0%", "0%")}
        f_zahl = {nf: wb.add_format({"num_format": nf}) for nf in ("0.0", "#,##0", "0.00", "0.000", "0.0%", "#,##0.0")}
        f_chf = wb.add_format({"num_format": "#,##0", "bold": True})
        ws.set_column(0, 0, 44)
        ws.set_column(1, 3, 16)
        ws.set_column(4, 7, 16)
        ws.set_column(8, 8, 60)
        ws.write(0, 0, "Hebel-Rechner – isolierte Umsatzwirkung je Hebel (Catering-Umsatz exkl. MwSt)", f_titel)
        ws.write(1, 0, "Gelbe Zellen sind Eingaben. Ergebnisse sind Rechenbeispiele (Caterer-Umsatz, nicht Club-Ertrag) – kein Potenzial. "
                       "Hebel überlappen (KF = Bons je Anwesendem × Ø Bon) und dürfen NICHT addiert werden.", f_hinweis)
        ws.write(3, 0, "1. Basiswerte (Meisterschaft)", wb.add_format({"bold": True, "font_size": 12}))
        ws.write(4, 0, "Für eine andere Basis die Werte aus Spalte C in die gelbe Spalte D übernehmen oder eigene Annahmen eintragen.", f_hinweis)
        for j, h in enumerate(["Kennzahl", f"Saison {basis.REFERENZ_SAISON}", basis.MITTEL_LABEL, "verwendete Basis", "Einheit"]):
            ws.write(B0 - 1, j, h, f_h)
        for i, (k, label, einheit, nf) in enumerate(BASIS_ZEILEN):
            z_ = B0 + i
            ws.write(z_, 0, label, f_txt)
            ws.write_number(z_, 1, float(r26[k]), f_zahl.get(nf, f_zahl["0.00"]))
            ws.write_number(z_, 2, float(mittel[k]), f_zahl.get(nf, f_zahl["0.00"]))
            ws.write_formula(z_, 3, f"=B{z_ + 1}", f_in[nf], float(r26[k]))
            ws.write(z_, 4, einheit)
            wb.define_name(f"Basis_{k}", f"=Hebel_Rechner!$D${z_ + 1}")

        h0 = B0 + len(BASIS_ZEILEN) + 3
        ws.write(h0 - 2, 0, "2. Hebel (isoliert, je Zeile eine Annahme)", wb.add_format({"bold": True, "font_size": 12}))
        for j, h in enumerate(["Hebel", "Veränderung", "φ (Konsum Zusatzbesucher)", "Anteil der Spiele", "Zusatzmenge je Spiel",
                               "CHF je Spiel", "CHF je Saison", "Einheit der Veränderung", "Formel"]):
            ws.write(h0 - 1, j, h, f_h)
        ws.data_validation(h0, 2, h0 + len(basis.HEBEL) - 1, 2, {"validate": "decimal", "criteria": "between", "minimum": 0,
                                                                 "maximum": 1.5, "input_message": "φ zwischen 0 und 1.5"})
        ws.data_validation(h0, 3, h0 + len(basis.HEBEL) - 1, 3, {"validate": "decimal", "criteria": "between", "minimum": 0, "maximum": 1})
        bz = basis.basis_zeile(e["basis_saison"], basis.REFERENZ_SAISON)
        for i, (code, (titel, einheit, formel)) in enumerate(basis.HEBEL.items()):
            z_ = h0 + i
            v = basis.STANDARD_VERAENDERUNG[code]
            phi = 1.0
            py = basis.hebel_szenario(bz, code, v, phi=phi)
            ws.write(z_, 0, titel, f_txt)
            ws.write_number(z_, 1, v, f_in["0.00"])
            if code in basis.MIT_PHI:
                ws.write_number(z_, 2, phi, f_in["0.00"])
            else:
                ws.write(z_, 2, "–")
            ws.write_number(z_, 3, 1.0, f_in["0%"])
            V, P, A, M = f"$B${z_ + 1}", f"$C${z_ + 1}", f"$D${z_ + 1}", f"$E${z_ + 1}"
            f_menge, f_chf_spiel = HEBEL_FORMELN[code]
            if f_menge:
                ws.write_formula(z_, 4, f_menge.format(V=V, P=P, A=A, M=M), f_zahl["#,##0.0"], float(py["zusatz_menge_je_spiel"]))
            else:
                ws.write(z_, 4, "–")
            ws.write_formula(z_, 5, f_chf_spiel.format(V=V, P=P, A=A, M=M), f_zahl["#,##0"], float(py["chf_pro_spiel"]))
            ws.write_formula(z_, 6, f"=F{z_ + 1}*{_basis_ref('spiele')}*{A}", f_chf, float(py["chf_pro_saison"]))
            ws.write(z_, 7, einheit, f_txt)
            ws.write(z_, 8, formel, f_txt)
        ws.write(h0 + len(basis.HEBEL) + 1, 0, "Keine Totalzeile: Die Hebel überlappen und sind Rechenbausteine für Phase 2, keine Potenzialsumme.",
                 f_hinweis)

        r0 = h0 + len(basis.HEBEL) + 4
        ws.write(r0 - 1, 0, "3. Retos Faustwerte (Annahme 18'000 Anwesende) gegenüber den Daten 2025/26",
                 wb.add_format({"bold": True, "font_size": 12}))
        for j, h in enumerate(["Kennzahl", "Retos Annahme", "Daten 2025/26", "Faktor Daten/Reto"]):
            ws.write(r0, j, h, f_h)
        for i, (_, rr) in enumerate(e["reto_faustwerte"].iterrows(), start=1):
            ws.write(r0 + i, 0, rr["kennzahl"], f_txt)
            ws.write_number(r0 + i, 1, float(rr["reto_annahme"]), f_zahl["#,##0"])
            ws.write_number(r0 + i, 2, float(rr["daten_2025_26"]), f_zahl["#,##0"])
            ws.write_number(r0 + i, 3, float(rr["faktor_daten_zu_reto"]), f_zahl["0.000"])
        ws.freeze_panes(1, 0)
    return schreiber


def _szenarien(e: dict):
    codes = list(basis.HEBEL)

    def schreiber(wb, ws, fmt):
        f_h = wb.add_format({"bold": True, "bg_color": "#0B6E4F", "font_color": "white", "text_wrap": True, "valign": "top", "border": 1})
        f_in = wb.add_format({"bg_color": GELB, "border": 1, "text_wrap": True, "valign": "top"})
        f_in_z = wb.add_format({"bg_color": GELB, "border": 1, "num_format": "0.00"})
        f_in_p = wb.add_format({"bg_color": GELB, "border": 1, "num_format": "0%"})
        f_chf = wb.add_format({"num_format": "#,##0", "bold": True})
        f_hinweis = wb.add_format({"text_wrap": True, "italic": True, "font_color": "#52514e"})
        ws.write(0, 0, "Szenarien für eigene Ideen – eine Zeile je Idee (rechnet mit den Basiswerten des Hebel-Rechners)",
                 wb.add_format({"bold": True, "font_size": 14}))
        ws.write(1, 0, "Hebel aus der Liste wählen, Veränderung, φ (nur Anwesenheitshebel) und Anteil der betroffenen Spiele eintragen. "
                       "Annahmen in Spalte H begründen. Ergebnis = isolierter Rechenwert (Phase-2-Annahme), keine Summenbildung über Ideen.",
                 f_hinweis)
        kopf = ["Idee", "Chancenfeld (Nr.)", "Hebel", "Veränderung", "φ", "Anteil Spiele", "CHF je Saison (exkl. MwSt)",
                "Begründung der Annahmen / Quelle"]
        for j, h in enumerate(kopf):
            ws.write(3, j, h, f_h)
        ws.set_column(0, 0, 36)
        ws.set_column(1, 1, 12)
        ws.set_column(2, 2, 34)
        ws.set_column(3, 5, 13)
        ws.set_column(6, 6, 18)
        ws.set_column(7, 7, 60)
        liste = "=" + "Hebel_Rechner!$A$" + str(B0 + len(BASIS_ZEILEN) + 4) + ":$A$" + str(B0 + len(BASIS_ZEILEN) + 3 + len(codes))
        bz = basis.basis_zeile(e["basis_saison"], basis.REFERENZ_SAISON)
        beispiele = [("Beispiel – überschreiben: Abo-Plätze in D besser freigeben", 1, codes[0], 0.5, 0.8, 1.0,
                      "Beispielannahme: −0.5 Pp. No-Show über alle Spiele; φ 0.8 (Zusatzbesucher konsumieren etwas weniger)."),
                     ("Beispiel – überschreiben: zusätzliche Kaufmomente durch Runner", 4, codes[3], 2.0, None, 1.0,
                      "Beispielannahme: +2 % Kauffrequenz; Wirkung im Pilot messen (Chancenfeld 4).")]
        for i in range(15):
            z_ = 4 + i
            ws.data_validation(z_, 2, z_, 2, {"validate": "list", "source": liste})
            ws.data_validation(z_, 4, z_, 4, {"validate": "decimal", "criteria": "between", "minimum": 0, "maximum": 1.5})
            if i < len(beispiele):
                titel, cf, code, v, phi, anteil, begr = beispiele[i]
                py = basis.hebel_szenario(bz, code, v, phi=phi if phi is not None else 1.0, anteil_spiele=anteil)["chf_pro_saison"]
                ws.write(z_, 0, titel, f_in)
                ws.write_number(z_, 1, cf, f_in_z)
                ws.write(z_, 2, basis.HEBEL[code][0], f_in)
                ws.write_number(z_, 3, v, f_in_z)
                if phi is not None:
                    ws.write_number(z_, 4, phi, f_in_z)
                else:
                    ws.write(z_, 4, "", f_in_z)
                ws.write_number(z_, 5, anteil, f_in_p)
                ws.write(z_, 7, begr, f_in)
            else:
                py = None
                for j in (0, 1, 2, 3, 4, 7):
                    ws.write_blank(z_, j, None, f_in)
                ws.write_blank(z_, 5, None, f_in_p)
            # CHF je Saison: CHF je Spiel des gewählten Hebels mit eigener Veränderung/φ, × Spiele × Anteil
            idx = f"MATCH(C{z_ + 1},{liste[1:]},0)"
            menge_np = f"D{z_ + 1}/100*Hebel_Rechner!{_basis_ref('soll_mittel')}"
            phi = f"IF(E{z_ + 1}=\"\",1,E{z_ + 1})"
            je_spiel = (f"CHOOSE({idx},{menge_np}*Hebel_Rechner!{_basis_ref('kf_exkl')}*{phi},"
                        f"D{z_ + 1}*Hebel_Rechner!{_basis_ref('kf_exkl')}*{phi},"
                        f"D{z_ + 1}*Hebel_Rechner!{_basis_ref('public_netto_mittel')}*Hebel_Rechner!{_basis_ref('bon_exkl')},"
                        f"D{z_ + 1}/100*Hebel_Rechner!{_basis_ref('umsatz_exkl_mittel')},"
                        f"D{z_ + 1}*Hebel_Rechner!{_basis_ref('bons_mittel')},"
                        f"D{z_ + 1}*Hebel_Rechner!{_basis_ref('public_netto_mittel')})")
            formel = f"=IF(C{z_ + 1}=\"\",\"\",{je_spiel}*Hebel_Rechner!{_basis_ref('spiele')}*IF(F{z_ + 1}=\"\",1,F{z_ + 1}))"
            if py is not None:
                ws.write_formula(z_, 6, formel, f_chf, float(py))
            else:
                ws.write_formula(z_, 6, formel, f_chf, "")
        ws.freeze_panes(4, 1)
    return schreiber


STECKBRIEF = [
    ("Titel der Idee", "Kurz und konkret."),
    ("Chancenfeld (Nr.)", "Auf welchem Befund baut die Idee auf? (Blatt 02_Chancenfelder)"),
    ("Befund aus den Daten (mit Zahl)", "Welche Zahl macht das Problem sichtbar? Fundstelle angeben."),
    ("Wirkungskette im Treiberbaum", "Welcher Treiber bewegt sich? Anwesende × Bons je Anwesendem × Ø Bon – und warum?"),
    ("Zielgrösse (KPI) und Messung", "Woran sehen wir den Erfolg je Spiel? (z.B. Scans je Platz, Bons je Anwesendem, KF vs. Erwartung)"),
    ("Clubhebel", "Was genau ändert der Club? (Prozess, Angebot, Ablauf – keine Preisänderung)"),
    ("Rechenbeispiel", "Zeile im Blatt Szenarien (Hebel, Veränderung, φ, Anteil Spiele) – isoliert, keine Summe."),
    ("Annahmen und Begründung", "Woher kommen Veränderung und φ? Quelle/Analogie nennen; Bandbreite statt Punktwert."),
    ("Leitplanken-Check", "Dynamic Pricing? Personensegmentierung? Kapazität/Ausbau? Hospitality? Alkohol/Jugendschutz?"),
    ("Umsatz ≠ DB", "Welche Kosten entstehen (Personal, Ware)? Wer erhält den Umsatz (Caterer/Club)?"),
    ("Datenbedarf", "Welche Daten fehlen noch? (Blatt 04_Datenanfragen)"),
    ("Pilot und Vergleich", "Welche Spiele/Sektoren mit, welche ohne Massnahme? Wie lange? (vgl. Toröffnung D)"),
    ("Risiken und Nebenwirkungen", "Wartezeit, Stimmung, Sicherheit, Marge, Akzeptanz bei Fans."),
    ("Nächster Schritt / verantwortlich", ""),
]


def _steckbrief(wb, ws, fmt):
    f_h = wb.add_format({"bold": True, "bg_color": "#0B6E4F", "font_color": "white", "text_wrap": True, "valign": "top", "border": 1})
    f_feld = wb.add_format({"bold": True, "text_wrap": True, "valign": "top", "border": 1})
    f_frage = wb.add_format({"text_wrap": True, "valign": "top", "italic": True, "font_color": "#52514e", "border": 1})
    f_in = wb.add_format({"bg_color": GELB, "text_wrap": True, "valign": "top", "border": 1})
    ws.write(0, 0, "Ideen-Steckbrief (Vorlage) – je Spalte eine Idee", wb.add_format({"bold": True, "font_size": 14}))
    for j, h in enumerate(["Feld", "Leitfrage", "Idee 1", "Idee 2", "Idee 3"]):
        ws.write(2, j, h, f_h)
    ws.set_column(0, 0, 30)
    ws.set_column(1, 1, 52)
    ws.set_column(2, 4, 42)
    for i, (feld, frage) in enumerate(STECKBRIEF, start=3):
        ws.write(i, 0, feld, f_feld)
        ws.write(i, 1, frage, f_frage)
        for j in (2, 3, 4):
            ws.write_blank(i, j, None, f_in)
        ws.set_row(i, 48)
    ws.freeze_panes(3, 2)


def schreibe(pfad: Path, e: dict, kz: dict) -> None:
    blaetter = [(name, e[key], text) for key, name, text in BLAETTER if key in e and isinstance(e[key], pd.DataFrame)]
    zusatz = [("Hebel_Rechner", "Rechner mit echten Formeln: Basiswerte, isolierte Hebel (gelb = Eingabe), Retos Faustwerte im Vergleich.",
               _rechner(e)),
              ("Szenarien", "Eine Zeile je Idee: Hebel wählen, Annahmen eintragen, CHF je Saison wird berechnet (isoliert).", _szenarien(e)),
              ("Ideen_Steckbrief", "Vorlage für Simon & Reto: Befund, Wirkungskette, Rechenbeispiel, Leitplanken, Pilot, Risiken.", _steckbrief)]
    schreibe_excel(pfad, blaetter, titel="FCSG «Untapped Business» – Ideen-Grundlage für Simon & Reto",
                   untertitel="Nur Aggregate, keine Personendaten. Lesehilfe: Ideen_Grundlage_FCSG.html (bzw. .pdf) im selben Ordner.",
                   zusatz_vorne=zusatz)


# --------------------------------------------------------------------------------------------
# Formelprüfung: Hebel-Rechner mit Mini-Auswerter nachrechnen
# --------------------------------------------------------------------------------------------
def _auswerten(formel: str, werte: dict[str, float]) -> float:
    ausdruck = formel.lstrip("=")
    ausdruck = re.sub(r"\$?([A-Z])\$?(\d+)", lambda m_: f"_{m_.group(1)}{m_.group(2)}", ausdruck)
    if not re.fullmatch(r"[\w\s\.\*/\+\-\(\)]+", ausdruck):
        raise ValueError(f"Nicht unterstützte Formel: {formel}")
    return float(eval(ausdruck, {"__builtins__": {}}, {f"_{k}": v for k, v in werte.items()}))  # noqa: S307 – nur Zellbezüge und + − × ÷


def pruefe_formeln(pfad: Path, e: dict) -> pd.DataFrame:
    """Rechnet die Formeln im Blatt Hebel_Rechner nach (mit Python-Basiswerten) und vergleicht mit hebel_szenario()."""
    import openpyxl
    ws = openpyxl.load_workbook(pfad, data_only=False)["Hebel_Rechner"]
    werte: dict[str, float] = {}
    for row in ws.iter_rows():
        for c in row:
            if isinstance(c.value, (int, float)) and not isinstance(c.value, bool):
                werte[c.coordinate] = float(c.value)
    # Formeln iterativ auswerten (Basis → Menge → CHF je Spiel → CHF je Saison)
    formeln = {c.coordinate: c.value for row in ws.iter_rows() for c in row if isinstance(c.value, str) and c.value.startswith("=")}
    for _ in range(5):
        for zelle, f in formeln.items():
            try:
                werte[zelle] = _auswerten(f, werte)
            except (KeyError, NameError, ValueError, ZeroDivisionError):
                continue
    bz = basis.basis_zeile(e["basis_saison"], basis.REFERENZ_SAISON)
    h0 = B0 + len(BASIS_ZEILEN) + 3
    rows = []
    for i, code in enumerate(basis.HEBEL):
        z_ = h0 + i + 1
        py = basis.hebel_szenario(bz, code, phi=1.0)["chf_pro_saison"]
        xl = werte.get(f"G{z_}", np.nan)
        rows.append({"hebel": code, "python_chf_saison": py, "excel_chf_saison": xl,
                     "gleich": bool(np.isclose(py, xl, rtol=1e-9))})
    return pd.DataFrame(rows)

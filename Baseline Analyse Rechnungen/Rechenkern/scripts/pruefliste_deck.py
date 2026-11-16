"""Zahlen-Prüfliste für das Präsentationsdeck: jede Zahl gegen Deck-PDF und Quelle prüfen.

Prüft zwei Dinge je Zahl:
1. Deck: Steht die Zahl (in der angegebenen Schreibweise) im Text des Deck-PDFs?
2. Quelle: Gibt es in der angegebenen Quelldatei (CSV, Excel-Blatt oder Markdown) einen Wert, der auf die
   gezeigten Nachkommastellen gerundet gleich ist? Prozentwerte werden auch als Anteil (×100) gesucht,
   das Vorzeichen wird ignoriert (Darstellung «−» vs. negative Zahl, KI-Grenzen).
Abgeleitete Zahlen (z.B. 0.93 = 243'989 / 261'924) werden nachgerechnet.

Nur aggregierte Ergebnistabellen werden gelesen, keine Rohdaten.

    python scripts/pruefliste_deck.py <Deck.pdf> <Ausgabe.md>
"""
import re
import sys
from pathlib import Path

import pandas as pd
from pypdf import PdfReader

BASIS = Path(__file__).resolve().parents[2]          # Baseline Analyse Rechnungen
R4 = BASIS / "run4_komplett_2026-11-05"
QUELLEN = {
    "SK": R4 / "kern_phase1/Tabellen/saison_kpi.csv",
    "AB": R4 / "kern_phase1/Tabellen/abdeckung.csv",
    "KM": R4 / "kern_phase1/Tabellen/kontext_effekt_matrix.csv",
    "MG": R4 / "kern_phase1/Tabellen/modellguete.csv",
    "DK": R4 / "kern_phase1/Tabellen/diagnosekarte.csv",
    "README4": R4 / "README.md",
    "MN": R4 / "kern_phase1/Methodennotiz_Phase1.md",
    "IGmd": R4 / "ideen_grundlage/Ideen_Grundlage_FCSG.md",
    "V": BASIS / "run4_anstoss-slot_2026-11-02/Tabellen/effekte.csv",
    "B_ns": BASIS / "barcode_abgleich_2026-11-13/nicht_scan_quote_einzeltickets_je_saison.csv",
    "B_abo": BASIS / "barcode_abgleich_2026-11-13/abo_noshow_naeherung_je_saison.csv",
    "B_val": BASIS / "barcode_abgleich_2026-11-13/validierung_zks_barcode.csv",
    "B_seg": BASIS / "barcode_abgleich_2026-11-13/noshow_segmente_je_saison.csv",
    "B_ab": BASIS / "barcode_abgleich_2026-11-13/abdeckung_je_saison.csv",
}
IG = R4 / "ideen_grundlage/Ideen_Grundlage_FCSG.xlsx"
PE = R4 / "kern_phase1/FCSG_Phase1_Ergebnisse.xlsx"
ZAHL = re.compile(r"[−-]?\d[\d']*(?:\.\d+)?")


def zahlen_aus_text(t: str) -> list[float]:
    return [float(z.replace("−", "-").replace("'", "")) for z in ZAHL.findall(t)]


_cache: dict = {}


def werte(quelle: str) -> list[float]:
    """Alle Zahlen einer Quelle (CSV-Zellen, Excel-Blatt 'IG:Blatt'/'PE:Blatt', Markdown-Text)."""
    if quelle in _cache:
        return _cache[quelle]
    if ":" in quelle:
        datei, blatt = quelle.split(":", 1)
        df = pd.read_excel(IG if datei == "IG" else PE, sheet_name=blatt, engine="calamine", header=None)
    else:
        p = QUELLEN[quelle]
        if p.suffix == ".md":
            _cache[quelle] = zahlen_aus_text(p.read_text(encoding="utf-8"))
            return _cache[quelle]
        df = pd.read_csv(p, header=None, dtype=str)
    out = []
    for v in df.to_numpy().ravel():
        if isinstance(v, (int, float)) and not pd.isna(v):
            out.append(float(v))
        elif isinstance(v, str):
            out.extend(zahlen_aus_text(v))
    _cache[quelle] = out
    return out


def in_quelle(wert: float, dez: int, quellen: list[str]) -> str | None:
    for q in quellen:
        for v in werte(q):
            for k in (v, v * 100):
                if abs(round(abs(k), dez) - abs(wert)) < 10 ** -(dez + 3):
                    return q
    return None


# (Folie, Aussage, Schreibweise im Deck, Wert, Nachkommastellen, Quellen) – Quellen: Kürzel aus QUELLEN oder 'IG:/PE:Blatt'
P = [
    (3, "−1 Pp. No-Show, Rechenbaustein tief/hoch", "29k–49k", None, 0, []),
    (5, "Herren-Pflichtspiele verknüpft", "108", 108, 0, ["AB"]),
    (5, "No-Show Meisterschaft 2025/26", "18.1 %", 18.1, 1, ["SK"]),
    (5, "nicht genutzte Plätze 2025/26", "60'942", 60942, 0, ["IG:N1_Leere_Plaetze_Saison"]),
    (5, "KF exkl. MwSt. 2025/26", "14.51", 14.51, 2, ["SK"]),
    (5, "KF Sonntagnachmittag", "−15.7 %", -15.7, 1, ["KM"]),
    (5, "KF Werktagabend", "−9.4 %", -9.4, 1, ["KM"]),
    (5, "erklärte KF-Schwankung innerhalb Saison", "82 %", 82, 0, ["MG"]),
    (6, "Einzelticket-Vorlauf vollständig", "97", 97, 0, ["AB"]),
    (6, "Ankunft vollständig", "71", 71, 0, ["AB"]),
    (6, "Bons", "70", 70, 0, ["AB"]),
    (6, "Eintritt je Einzelticket (ZKS)", "35", 35, 0, ["AB"]),
    (6, "Kontextmodell und Diagnose", "76", 76, 0, ["AB"]),
    (7, "Public-Catering-Umsatz exkl. MwSt. 2025/26", "3.80 Mio.", 3799455, 0, ["SK", "IG:R3_Basis_Saison"]),
    (7, "Public-Anwesende 2025/26", "261'924", 261924, 0, ["SK", "IG:R3_Basis_Saison"]),
    (7, "Ø Public-Anwesende je Spiel", "13'785", 13785, 0, ["IG:R3_Basis_Saison", "IGmd"]),
    (7, "Bons je Anwesendem", "0.932", 0.932, 3, ["SK", "IG:R3_Basis_Saison"]),
    (7, "Ø Bon exkl. MwSt.", "15.57", 15.57, 2, ["SK", "IG:R3_Basis_Saison"]),
    (8, "Fehlerreduktion KF, ausgelassene Saison", "−53 %", 53, 0, ["MG"]),
    (8, "Erklärungsquote bei vertauschten Anstosszeiten (Median)", "27 %", 27, 0, ["README4"]),
    (9, "Ø IST 2021/22", "12'042", 12042, 0, ["SK"]),
    (9, "Ø IST 2022/23", "14'558", 14558, 0, ["SK"]),
    (9, "Ø IST 2023/24", "14'829", 14829, 0, ["SK"]),
    (9, "Ø IST 2024/25", "14'635", 14635, 0, ["SK"]),
    (9, "Ø IST 2025/26", "14'510", 14510, 0, ["SK"]),
    (9, "No-Show 2021/22", "22.4 %", 22.4, 1, ["SK"]),
    (9, "No-Show 2022/23", "17.2 %", 17.2, 1, ["SK"]),
    (9, "No-Show 2023/24", "16.5 %", 16.5, 1, ["SK"]),
    (9, "No-Show 2024/25", "19.0 %", 19.0, 1, ["SK"]),
    (9, "KF inkl. 2021/22", "13.68", 13.68, 2, ["SK"]),
    (9, "KF inkl. 2022/23", "13.32", 13.32, 2, ["SK"]),
    (9, "KF inkl. 2023/24", "14.81", 14.81, 2, ["SK"]),
    (9, "KF inkl. 2024/25", "14.48", 14.48, 2, ["SK"]),
    (9, "KF inkl. 2025/26", "15.27", 15.27, 2, ["SK"]),
    (9, "Ø nicht genutzte Plätze je Spiel", "3'207", 3207, 0, ["IG:N1_Leere_Plaetze_Saison"]),
    (9, "Catering-Umsatz inkl. MwSt. 2025/26", "4.00 Mio.", 4.00, 2, ["SK"]),
    (10, "Anwesenheit Sonntagnachmittag", "+3.7 Pp.", 3.7, 1, ["KM"]),
    (10, "Anwesenheit Werktagabend", "−7.4 Pp.", -7.4, 1, ["KM"]),
    (10, "Anwesenheit Samstag ab 20 Uhr", "−0.4 Pp.", -0.4, 1, ["KM"]),
    (10, "Anwesenheit je +5 °C", "+1.3 Pp.", 1.3, 1, ["KM"]),
    (10, "Anwesenheit Top-Gegner", "+3.4 Pp.", 3.4, 1, ["KM"]),
    (10, "KF Samstag ab 20 Uhr", "−3.6 %", -3.6, 1, ["KM"]),
    (10, "KF je +5 °C", "+2.8 %", 2.8, 1, ["KM"]),
    (10, "KF Top-Gegner", "+0.1 %", 0.1, 1, ["KM"]),
    (10, "KI KF Sonntagnachmittag unten", "−17.9", -17.9, 1, ["KM"]),
    (10, "KI KF Sonntagnachmittag oben", "−13.3", -13.3, 1, ["KM"]),
    (11, "KF-Ausreisser unter Erwartung", "8", 8, 0, ["IG:D1_Ausreisser_Zaehlung"]),
    (11, "KF-Ausreisser über Erwartung", "6", 6, 0, ["IG:D1_Ausreisser_Zaehlung"]),
    (11, "Zufallserwartung je Seite", "7.6", 7.6, 1, ["IG:D1_Ausreisser_Zaehlung"]),
    (11, "Yverdon beobachtet", "11.88", 11.88, 2, ["DK"]),
    (11, "Yverdon erwartet", "12.70", 12.70, 2, ["DK"]),
    (11, "Luzern beobachtet", "11.24", 11.24, 2, ["DK"]),
    (11, "Luzern erwartet", "12.65", 12.65, 2, ["DK"]),
    (11, "GC beobachtet", "15.97", 15.97, 2, ["DK"]),
    (11, "GC erwartet", "15.02", 15.02, 2, ["DK"]),
    (12, "Toröffnung D: Ankunft", "+22.6 min", 22.6, 1, ["PE:D9_Toroeffnung_DiD"]),
    (15, "+CHF 1 KF", "261'924", 261924, 0, ["IG:R1_Faustwerte"]),
    (15, "+CHF 1 Ø Bon", "243'989", 243989, 0, ["IG:R1_Faustwerte"]),
    (15, "+1 % Bonsrate", "37'995", 37995, 0, ["IG:R1_Faustwerte"]),
    (15, "−1 Pp. No-Show, φ 0.6", "29'299", 29299, 0, ["IG:R1_Faustwerte"]),
    (15, "−1 Pp. No-Show, φ 0.8", "39'066", 39066, 0, ["IG:R1_Faustwerte"]),
    (15, "−1 Pp. No-Show, φ 1.0", "48'832", 48832, 0, ["IG:R1_Faustwerte"]),
    (15, "Elastizität", "1.01", 1.01, 2, ["PE:C11_Elastizitaet", "IG:K16_Phi_Evidenz", "IGmd", "MN"]),
    (16, "Weiterverkäufe Zweitmarkt", "5'716", 5716, 0, ["IG:N3_Zweitmarkt_Saison"]),
    (16, "Weiterverkäufe in den letzten 2 Tagen", "70 %", 70, 0, ["IG:N5_Zweitmarkt_Vorlauf", "IGmd"]),
    (16, "Weiterverkäufe am Spieltag", "36 %", 36, 0, ["IG:N5_Zweitmarkt_Vorlauf", "IGmd"]),
    (16, "Tickets Vorlauf-Basis", "7'607", 7607, 0, ["IG:N5_Zweitmarkt_Vorlauf", "IGmd"]),
    (16, "Käufergebühr Zweitmarkt", "10.8 %", 10.8, 1, ["IG:N6_Zweitmarkt_Preis", "IGmd"]),
    (16, "Einzeltickets nicht gescannt 22/23", "9.6 %", 9.6, 1, ["B_ns"]),
    (16, "Einzeltickets nicht gescannt 23/24", "11.5 %", 11.5, 1, ["B_ns"]),
    (16, "Einzeltickets nicht gescannt 25/26", "6.9 %", 6.9, 1, ["B_ns"]),
    (16, "Einzeltickets nicht gescannt 26/27", "5.7 %", 5.7, 1, ["B_ns"]),
    (16, "Public-Abos nicht genutzt 22/23", "27.4 %", 27.4, 1, ["B_abo"]),
    (16, "Public-Abos nicht genutzt 23/24", "28.1 %", 28.1, 1, ["B_abo"]),
    (16, "Public-Abos nicht genutzt 25/26", "28.8 %", 28.8, 1, ["B_abo"]),
    (16, "Public-Abos nicht genutzt 26/27", "26.2 %", 26.2, 1, ["B_abo"]),
    (16, "Validierung ZKS × Barcode", "99.2 %", 99.2, 1, ["B_val"]),
    (16, "No-Show ausverkaufte Spiele", "14.0", 14.0, 1, ["PE:B1_NoShow_Kontext", "MN"]),
    (16, "No-Show übrige Spiele", "20.8", 20.8, 1, ["PE:B1_NoShow_Kontext", "MN"]),
    (17, "Online-Shop 2–4 Tickets 2025/26", "5.1 %", 5.1, 1, ["B_seg"]),
    (17, "Inhouse ab 10 ohne Gästesektor 2025/26", "15.0 %", 15.0, 1, ["B_seg"]),
    (17, "Gratis-Tickets 2025/26", "19.4 %", 19.4, 1, ["B_seg"]),
    (17, "Anteil Gratis an No-Shows 2025/26 (≈ 1/3)", "1/3", 32.7, 1, ["B_seg"]),
    (17, "Anteil Grossbestellungen an No-Shows 2025/26", "11 %", 10.7, 1, ["B_seg"]),
    (18, "Verweilzeit Eingang C", "27.4 min", 27.4, 1, ["IG:Z1_Verweilzeit_Eingang", "IGmd"]),
    (18, "letzte 15 min Eingang C", "23.1 %", 23.1, 1, ["IG:Z1_Verweilzeit_Eingang", "IGmd"]),
    (18, "KI Toröffnung unten", "19.0", 19.0, 1, ["PE:D9_Toroeffnung_DiD"]),
    (18, "KI Toröffnung oben", "26.1", 26.1, 1, ["PE:D9_Toroeffnung_DiD"]),
    (18, "Runner nicht im Einsatz", "−1.1 %", -1.1, 1, ["IG:K11_Mobiler_Verkauf_Effekt"]),
    (18, "Runner im Einsatz", "−0.2 %", -0.2, 1, ["IG:K11_Mobiler_Verkauf_Effekt"]),
    (18, "Differenz Runner", "−0.8 %", -0.8, 1, ["IG:K11_Mobiler_Verkauf_Effekt"]),
    (18, "Nachweisgrenze", "4.6 %", 4.6, 1, ["IG:K11_Mobiler_Verkauf_Effekt", "IGmd"]),
    (19, "KF Alkohol Samstag ab 20 Uhr", "+6.4 %", 6.4, 1, ["IG:K8_Alkohol_Effekt_Matrix"]),
    (19, "KF Food Samstag ab 20 Uhr", "−14.9 %", -14.9, 1, ["IG:K8_Alkohol_Effekt_Matrix"]),
    (19, "KF Alkohol Sonntagnachmittag", "−26.4 %", -26.4, 1, ["IG:K8_Alkohol_Effekt_Matrix"]),
    (19, "KF Food Sonntagnachmittag", "−5.2 %", -5.2, 1, ["IG:K8_Alkohol_Effekt_Matrix"]),
    (19, "KF Alkohol Werktagabend", "−12.0 %", -12.0, 1, ["IG:K8_Alkohol_Effekt_Matrix"]),
    (19, "KF Food Werktagabend", "−9.8 %", -9.8, 1, ["IG:K8_Alkohol_Effekt_Matrix"]),
    (19, "Alkoholanteil 2023/24", "53.5 %", 53.5, 1, ["IG:K2_Warenkorb_Gruppen", "IGmd"]),
    (19, "Alkoholanteil 2025/26", "49.9 %", 49.9, 1, ["IG:K2_Warenkorb_Gruppen", "IGmd"]),
    (19, "KF Kiesplatz je +5 °C", "+8.1 %", 8.1, 1, ["IG:K14_Kiesplatz_Wetter"]),
    (19, "KF Stadion je +5 °C", "+2.3 %", 2.3, 1, ["IG:K14_Kiesplatz_Wetter"]),
    (19, "Regen bei Anreise Kiesplatz", "−16.8 %", -16.8, 1, ["IG:K14_Kiesplatz_Wetter", "IGmd"]),
    (20, "MAE nur Kontext", "1'120", 1120, 0, ["IG:A6_Fruehindikator"]),
    (20, "MAE mit T−7", "849", 849, 0, ["IG:A6_Fruehindikator"]),
    (20, "Prognosefehler-Reduktion", "−24.2 %", -24.2, 1, ["IG:A6_Fruehindikator", "IGmd"]),
    (20, "im 80 %-Band", "84.1 %", 84.1, 1, ["IG:A6_Fruehindikator", "IGmd"]),
    (20, "KF Testspiele inkl. MwSt.", "14.01", 14.01, 2, ["IG:F1_Randfelder_Kategorien", "IGmd"]),
    (20, "KF Herren-Meisterschaft inkl. MwSt.", "14.61", 14.61, 2, ["IG:F1_Randfelder_Kategorien", "IGmd"]),
    (28, "Catering-Umsatz exkl. MwSt. Meisterschaft", "3'799'455", 3799455, 0, ["IG:R3_Basis_Saison"]),
    (28, "Public-Anwesende alle Pflichtspiele", "277'145", 277145, 0, ["SK", "IG:R3_Basis_Saison"]),
    (28, "Catering-Umsatz alle Pflichtspiele", "4'022'508", 4022508, 0, ["SK", "IG:R3_Basis_Saison"]),
    (30, "Ø Bon Sonntagnachmittag mit 2023/24", "−8.3 %", -8.3, 1, ["KM"]),
    (30, "Ø Bon Sonntagnachmittag ohne 2023/24", "−8.5 %", -8.5, 1, ["V"]),
    (31, "R² Anwesenheitsquote", "62 %", 62, 0, ["MG"]),
    (31, "R² Bons je Anwesendem", "50 %", 50, 0, ["MG"]),
    (31, "R² Ø Bon", "71 %", 71, 0, ["MG"]),
    (31, "LOSO Anwesenheitsquote", "29 %", 29, 0, ["MG"]),
    (31, "LOSO Bons", "18 %", 18, 0, ["MG"]),
    (31, "LOSO Ø Bon", "39 %", 39, 0, ["MG"]),
    (31, "Slot allein", "64 %", 64, 0, ["README4", "MN"]),
    (31, "Permutation maximal", "41 %", 41, 0, ["README4", "MN"]),
    (33, "KF exkl. 2026/27 Meisterschaft", "15.86", 15.86, 2, ["SK"]),
    (33, "No-Show 2026/27 Meisterschaft", "14.9 %", 14.9, 1, ["SK"]),
    (33, "KF exkl. 2026/27 alle Pflichtspiele", "16.90", 16.90, 2, ["SK", "IGmd", "MN"]),
    (33, "No-Show 2026/27 alle Pflichtspiele", "11.2 %", 11.2, 1, ["SK", "IGmd", "MN"]),
    (34, "Bons je Anw. Sonntagnachmittag", "−8.2", -8.2, 1, ["KM"]),
    (34, "Ø Bon Werktagabend", "−9.5", -9.5, 1, ["KM"]),
    (34, "Ø Bon je +5 °C", "+1.9", 1.9, 1, ["KM"]),
    (34, "Bons Regen bei Anreise", "−4.3", -4.3, 1, ["KM"]),
    (34, "Anwesenheit Schulferien", "−2.6", -2.6, 1, ["KM"]),
    (34, "Ankunft ≥ 45 min Top-Gegner", "+3.3", 3.3, 1, ["KM"]),
    (38, "Inhouse ab 10 ohne Gästesektor, Tickets 2025/26", "6'209", 6209, 0, ["B_seg"]),
    (39, "Ø Abos Sektor D", "3'614", 3614, 0, ["IG:N7_Tribuene_2627", "IGmd", "MN"]),
    (39, "Ø Abo-Preis D", "CHF 304", 304, 0, ["IG:A10_Preis_Abo_Tribuene", "IG:N7_Tribuene_2627", "IGmd"]),
]

# abgeleitete Zahlen: (Folie, Aussage, Schreibweise, berechnet, Rechenweg)
r1 = dict(kf=261924, bon=243989, rate=37995)
seg = pd.read_csv(QUELLEN["B_seg"])
abo = pd.read_csv(QUELLEN["B_abo"])
ns = pd.read_csv(QUELLEN["B_ns"])
ns_sl = ns[ns["wettbewerb"] == "Nur Super League"].set_index("saison")["nicht_scan_quote"]
gratis_anteil = seg[seg["segment"].str.startswith("Gratis")]["anteil_an_allen_noshows"]
gross_anteil = seg[seg["segment"].str.contains("davon ohne Gästesektor")]["anteil_an_allen_noshows"]
diffs = (abo.set_index("saison")["abo_noshow_quote"] - ns_sl).dropna()
ab = pd.read_csv(QUELLEN["B_ab"])
ABGELEITET = [
    (3, "−1 Pp. No-Show ≈ CHF 29k–49k", "29k–49k", "29'299 / 48'832 → 29k–49k", "R1_Faustwerte, gerundet"),
    (6, "Eintritt über Barcode-Abgleich (Spiele)", "59", int(ab["abgleichbar"].sum()), "Summe abgleichbar in abdeckung_je_saison"),
    (6, "Spiele nicht im Kontextmodell", "32", 108 - 76, "108 − 76 = 18 + 9 + 3 + 2"),
    (12, "Abo-No-Show je Saison", "26–29 %", f"{abo['abo_noshow_quote'].min()*100:.1f}–{abo['abo_noshow_quote'].max()*100:.1f} %", "Min/Max abo_noshow_quote"),
    (12, "Einzeltickets nicht gescannt je Saison", "6–12 %", f"{ns_sl.min()*100:.1f}–{ns_sl.max()*100:.1f} %", "Min/Max SL nicht_scan_quote"),
    (15, "Ø Bon in KF-Franken", "≈ KF +0.93", f"{r1['bon']/r1['kf']:.3f}", "243'989 / 261'924"),
    (15, "Bonsrate in KF-Franken", "≈ KF +0.15", f"{r1['rate']/r1['kf']:.3f}", "37'995 / 261'924"),
    (17, "Gratis-Anteil an No-Shows je Saison", "21–36 %", f"{gratis_anteil.min()*100:.1f}–{gratis_anteil.max()*100:.1f} %", "Min/Max über 2021/22–2026/27"),
    (17, "Grossbestellungen ohne Gäste je Saison", "7–22 %", f"{gross_anteil.min()*100:.1f}–{gross_anteil.max()*100:.1f} %", "Min/Max über 2021/22–2026/27"),
    (39, "Gegenprobe Nutzungsdifferenz Abo − Einzel", "17–22 Pp.", f"{diffs.min()*100:.1f}–{diffs.max()*100:.1f} Pp.", "Abo-No-Show − Nicht-Scan-Quote je Saison"),
    (39, "Rechenweg M3 je 100 Abos", "CHF 2'800–7'100", f"{17*19*14.51*0.6:,.0f}–{25.8*19*14.51*1.0:,.0f}".replace(",", "'"),
     "17 × 19 × 14.51 × 0.6 bis 25.8 × 19 × 14.51 × 1.0 (17–26 gerundet)"),
]


def main(deck: Path, ziel: Path) -> None:
    text = " ".join(p.extract_text() or "" for p in PdfReader(deck).pages)
    norm = lambda s: re.sub(r"\s+", "", s.replace("−", "-").replace("’", "'"))  # noqa: E731
    deck_n = norm(text)
    zeilen, fehler = [], 0
    for folie, aussage, schreib, wert, dez, quellen in P:
        im_deck = norm(schreib) in deck_n
        if wert is None:
            continue
        treffer = in_quelle(wert, dez, quellen)
        ok = im_deck and treffer is not None
        fehler += not ok
        zeilen.append(f"| {folie} | {aussage} | {schreib} | {treffer or ', '.join(quellen)} | "
                      f"{'✓' if im_deck else '✗'} | {'✓' if treffer else '✗ prüfen'} |")
    abg = []
    for folie, aussage, schreib, berechnet, weg in ABGELEITET:
        im_deck = norm(schreib) in deck_n
        abg.append(f"| {folie} | {aussage} | {schreib} | {berechnet} | {weg} | {'✓' if im_deck else '✗'} |")
    md = [f"# Zahlen-Prüfliste Deck «{deck.stem}»", "",
          "Erzeugt mit `Rechenkern/scripts/pruefliste_deck.py`. «Deck ✓» = Zahl steht so im PDF; «Quelle ✓» = gerundet gleicher Wert in der Quelle.",
          "Quellenkürzel: SK saison_kpi · AB abdeckung · KM kontext_effekt_matrix · MG modellguete · DK diagnosekarte (alle Run 4, kern_phase1/Tabellen) ·",
          "IG:Blatt = Ideen_Grundlage_FCSG.xlsx · PE:Blatt = FCSG_Phase1_Ergebnisse.xlsx · README4 = Run-4-README · MN = Methodennotiz · IGmd = Ideen_Grundlage_FCSG.md ·",
          "V = run4_anstoss-slot effekte.csv · B_* = barcode_abgleich_2026-11-13 (ns Nicht-Scan, abo Abo-No-Show, val Validierung, seg Segmente, ab Abdeckung).", "",
          f"**Ergebnis:** {len(zeilen)} direkte Zahlen geprüft, davon {fehler} mit Befund (✗).", "",
          "## Direkte Zahlen", "", "| Folie | Aussage | Deck | Quelle | Deck ✓ | Quelle ✓ |", "|---|---|---|---|---|---|",
          *zeilen, "", "## Abgeleitete Zahlen (nachgerechnet)", "",
          "| Folie | Aussage | Deck | nachgerechnet | Rechenweg | Deck ✓ |", "|---|---|---|---|---|---|", *abg, "",
          "**Nicht geprüft (externe Quelle):** Referenzwerte laut Projektantrag (~17 %, CHF 14.50, S. 3), Research-Beispiele (S. 22, Research-Dossier mit Links)."]
    ziel.write_text("\n".join(md) + "\n", encoding="utf-8")
    print(f"{len(zeilen)} direkte Zahlen, {fehler} Befunde; geschrieben: {ziel.name}")
    for z in zeilen:
        if "✗" in z:
            print(z)
    for z in abg:
        print(z)


if __name__ == "__main__":
    main(Path(sys.argv[1]), Path(sys.argv[2]))

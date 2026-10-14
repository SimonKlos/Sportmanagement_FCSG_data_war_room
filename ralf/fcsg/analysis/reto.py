"""Abgleich mit Retos Sichtung («FCSG Datenquellen & Treiberbaum», Stand 08.10.2026).

Auftrag Deliverable B: «Zahlen aus Retos Sichtung reproduzieren oder Abweichungen erklären, nicht als
Soll-Ergebnis übernehmen.»
"""
from __future__ import annotations

import pandas as pd


def _f(x, fmt="{:.1%}") -> str:
    try:
        out = fmt.format(x)
    except (TypeError, ValueError):
        return "–"
    return out.replace("%", " %") if "%" in fmt else out


def reto_abgleich(res: dict[str, pd.DataFrame], roh_info: dict) -> pd.DataFrame:
    s = res["saison_kpi"]
    sl = s[s["wettbewerbe"] == "SL"].set_index("saison")
    mitte = sl.loc[[x for x in ("2022/23", "2023/24", "2024/25", "2025/26") if x in sl.index]]
    typ = res["tickettyp_noshow"]
    typ = typ[typ["scope"] == "alle validen Spiele"].set_index("saison")
    seg = res["eintritt_segmente"]
    seg = seg[seg["merkmal"] == "Verkaufsmodul (Rohwert)"].set_index("auspraegung")["eintrittsquote"]
    scan = res["scan_ist"]
    scan27 = scan[(scan["saison"] >= "2025/26")]
    ank = res["ankunft_reto"].iloc[0]
    korr = res["kf_korrelationen"].iloc[0]
    k = res["spiel_kpi"]
    reto_bon = k[(k["saison"] >= "2025/26") & k["wettbewerb"].isin(["SL", "Cup", "UEFA"]) &
                 (k["spielstatus"] == "gespielt") & k["transaktionen"].notna()]
    art = res["artikel_gruppen"].set_index(["saison", "name"])["anteil"]
    el = res["elastizitaet"].set_index("variante")["elastizitaet"]
    elki = res["elastizitaet"].set_index("variante")

    def a(s_, n):
        return art.get((s_, n))

    zeilen = [
        ("Ticketing", "Ø IST 22/23–25/26 rund 14.5k–14.8k (Meisterschaft)",
         f"{mitte['ist_mittel'].min():,.0f}–{mitte['ist_mittel'].max():,.0f}".replace(",", "'"), "bestätigt",
         "Saisonmittel der Meisterschafts-Heimspiele (Historie)."),
        ("Ticketing", "Ø SOLL 17.6k–18.1k",
         f"{mitte['soll_mittel'].min():,.0f}–{mitte['soll_mittel'].max():,.0f}".replace(",", "'"), "bestätigt",
         "SOLL ist teils Ticketsumme, teils Kapazitätswert (ausverkaufte Spiele) – siehe soll_definition."),
        ("Ticketing", "No-Show 16 %–19 %",
         f"{_f(mitte['noshow_quote'].min())}–{_f(mitte['noshow_quote'].max())}", "bestätigt",
         "Gewichtet (1 − ΣIST/ΣSOLL). 2021/22 (COVID-Zertifikatspflicht): " + _f(sl.loc['2021/22', 'noshow_quote'])
         if "2021/22" in sl.index else "Gewichtet (1 − ΣIST/ΣSOLL)."),
        ("Ticketing", "Abo-Anteil (SOLL − Einzeltickets) 21/22 und 22/23 rund 63–65 % von SOLL",
         f"21/22: {_f(typ.loc['2021/22', 'anteil_rest_am_soll'])}, 22/23: {_f(typ.loc['2022/23', 'anteil_rest_am_soll'])}",
         "bestätigt mit Präzisierung",
         "Rest enthält neben Abos auch VIP, Gäste und Freikarten; bei Kapazitäts-SOLL überschätzt. 22/23 eher 60 %."),
        ("Ticketing", "No-Show Einzeltickets ca. 9–12 %, Abos ca. 20–29 % (21/22, 22/23)",
         f"Einzel: {_f(typ.loc['2021/22', 'noshow_einzel'])} / {_f(typ.loc['2022/23', 'noshow_einzel'])}; "
         f"Rest (≈Abos): {_f(typ.loc['2021/22', 'noshow_rest_naeherung'])} / {_f(typ.loc['2022/23', 'noshow_rest_naeherung'])}",
         "bestätigt", "Nur valide ZKS-Spiele (ohne 02.04. und 16.04.2023 mit Scanproblemen)."),
        ("Ticketing", "Eintrittsquote Webshop und Connect Online ca. 90–95 %, Inhouse ca. 71–74 %",
         f"Webshop {_f(seg.get('Webshop'))}, Connect {_f(seg.get('Connect Online'))}, Inhouse {_f(seg.get('Inhouse'))}, "
         f"Websales Client {_f(seg.get('Websales Client'))}", "bestätigt mit Präzisierung",
         "Über beide Saisons gepoolt Inhouse 75 %. Inhouse enthält viele Gratis-/Promotickets (tiefere Eintrittsquote)."),
        ("Zutritt", "Scans im Schnitt 0.4 % unter IST (meist < 1 %)",
         f"{_f(scan27['abweichung_scans_ist'].mean(), '{:+.2%}')} (n={len(scan27)}); ältere Saisons (vollständige Lieferungen) "
         f"{_f(scan[(scan['saison'] < '2025/26') & scan['zutritt_vollstaendig']]['abweichung_scans_ist'].mean(), '{:+.1%}')}",
         "bestätigt", "Ab 25/26 ist IST praktisch die Scanzahl; 22/23–24/25 liegt IST 1–3 % über den Scans."),
        ("Zutritt", "Median Ankunft rund 37 min vor Anpfiff, 41 % ≥ 45 min, 17 % in den letzten 15 min",
         f"{ank['median_min_vor_anpfiff_mittel']:.1f} min; {_f(ank['anteil_ab_45_min_mittel'])}; "
         f"{_f(ank['anteil_letzte_15_min_inkl_nach_anpfiff_mittel'])} (inkl. nach Anpfiff)", "bestätigt",
         "Voraussetzung: Anpfiff 17.05.2026 korrigiert (Historie 14:00 statt 16:30). 71 statt 27 Spiele verfügbar."),
        ("Zutritt", "Ältere Saisons folgen", "22/23, 23/24 und 2. Hälfte 24/25 bereits geliefert", "erweitert",
         "zugangsdaten_herren_inhouse.csv und _alteSaisons.txt; Juli–Dez. 2024 nur Bruchstücke (5–22 Scans/Spiel)."),
        ("Catering", "Umsatz inkl. MwSt 21/22 rund 2.8 Mio., 25/26 rund 4.0 Mio. (Meisterschaft)",
         f"{sl.loc['2021/22', 'umsatz_inkl'] / 1e6:.2f} Mio. → {sl.loc['2025/26', 'umsatz_inkl'] / 1e6:.2f} Mio.", "bestätigt", ""),
        ("Catering", "KF inkl. MwSt 13.68 → 15.27 (Summe/Summe)",
         f"{sl.loc['2021/22', 'kf_inkl']:.2f} → {sl.loc['2025/26', 'kf_inkl']:.2f}", "bestätigt",
         "Exkl. MwSt alle Pflichtspiele 25/26: " + _f(s[(s['wettbewerbe'] == 'SL+Cup+UEFA') & (s['saison'] == '2025/26')]['kf_exkl'].iloc[0], "{:.2f}")
         + " = Antragswert CHF 14.50."),
        ("Catering", "Bons je Anwesendem rund 0.95, Ø Bon rund 16.70 (25/26 + 26/27 inkl. Cup/Europa)",
         f"{korr['bons_pro_anwesende_gewichtet']:.3f}; Ø Bon inkl. MwSt gewichtet {korr['bon_inkl_gewichtet']:.2f}, "
         f"ungewichtet {reto_bon['bon_inkl'].mean():.2f} (n={len(reto_bon)})",
         "bestätigt mit Präzisierung", "Retos 16.70 entspricht dem ungewichteten Mittel der Spiel-Bons; Summe/Summe ergibt einen "
         "etwas höheren Wert (Auftrag: Saisonwerte als Summe/Summe)."),
        ("Catering", "r(KF, Ø Bon) = 0.87; r(KF, Bons je Anwesendem) = 0.75",
         f"{korr['r_kf_bon']:.2f}; {korr['r_kf_bons_pro_anwesende']:.2f}", "bestätigt",
         "Algebraisch verknüpft (KF = Bons/Anw × Ø Bon) – kein unabhängiger Kausalnachweis. Saisonbereinigt erklären "
         "Ø Bon rund 50 % und Bons/Anwesende rund 39 % der KF-Streuung."),
        ("Catering", "Alkoholanteil 25/26 rund 49 % (23/24: 54 %), Food 33 %, alkoholfrei 15 %",
         f"{_f(a('2025/26', 'Alkoholische Getränke'), '{:.1%}')} (23/24: {_f(a('2023/24', 'Alkoholische Getränke'), '{:.1%}')}); "
         f"Food {_f(a('2025/26', 'Food'), '{:.1%}')}; alkoholfrei {_f(a('2025/26', 'Alk.-freie Getränke'), '{:.1%}')}",
         "bestätigt mit Präzisierung", "Saisonsummen Meisterschaft (Artikelauswertung), einheitlich brutto: Die Datei liefert 23/24 "
         "und 24/25 Bruttowerte, 25/26 Nettowerte. Retos 49 % vs. 54 % vergleicht Netto (25/26) mit Brutto (23/24); auf "
         "gleicher Basis sinkt der Alkoholanteil weniger stark."),
        ("Catering", "Elastizität Umsatz ~ Zuschauer rund 1.14 (22 Spiele, Modell)",
         f"25/26+26/27: {el.iloc[0]:.2f} [{elki.iloc[0]['ki95_unten']:.2f}–{elki.iloc[0]['ki95_oben']:.2f}]; "
         f"21/22–26/27 mit Saison-Effekten: {el.iloc[1]:.2f} [{elki.iloc[1]['ki95_unten']:.2f}–{elki.iloc[1]['ki95_oben']:.2f}]",
         "präzisiert", "Auf der kleinen Stichprobe > 1, auf 96 Spielen ≈ 1: Mehr Zuschauer bringen proportional mehr Umsatz "
                      "(KF bleibt etwa gleich) – kein belastbarer Skaleneffekt."),
        ("Datenbasis", "27 Ticket-CSVs, rund 13'000 Abos, rund 394'000 Scans in 27 Spielen, rund 90 Kontextspiele",
         f"{roh_info['csv_herren_spiele']} Herren-Spiel-CSVs (+{roh_info['csv_frauen']} Frauen, 2 Abo-Dateien); "
         f"{roh_info['abos_herren']:_} Abos; {roh_info['scans_erlaubt']:_} Scans; {roh_info['kontext_zeilen']} Kontextzeilen "
         f"({roh_info['kontext_gespielt']} gespielt)".replace("_", "'"), "bestätigt",
         "In der Kontexttabelle fehlen 6 Meisterschaftsspiele 25/26 (11.02.–06.04.2026); ergänzt aus öffentlichen Quellen."),
    ]
    return pd.DataFrame(zeilen, columns=["bereich", "aussage_reto", "reproduziert", "status", "erklaerung"])

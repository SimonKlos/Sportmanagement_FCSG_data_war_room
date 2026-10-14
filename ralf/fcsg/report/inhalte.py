"""Klärungsfragen, Prüfkandidaten Phase 2 und Datenwörterbuch (Deliverable E und A).

Die Texte enthalten die aktuell berechneten Zahlen, damit sie nach einer Datenlieferung automatisch
nachgeführt werden. Prüfkandidaten sind KEINE quantifizierten Massnahmen (Phase 2, Auftrag 12).
"""
from __future__ import annotations

import pandas as pd


def _pct(x, d=0) -> str:
    return "–" if pd.isna(x) else f"{x * 100:.{d}f} %"


def klaerungsfragen(res: dict[str, pd.DataFrame]) -> pd.DataFrame:
    k = res["spiel_kpi"]
    kern = k[k["spielstatus"] == "gespielt"]
    kap = (kern["soll_definition"].str.contains("Kapazität")).sum()
    sz = res["soll_zerlegung"]
    abo = f"{sz['abo_bestand_implizit'].min():,.0f}–{sz['abo_bestand_implizit'].max():,.0f}".replace(",", "'") if len(sz) else "–"
    pn = kern.dropna(subset=["public_netto_minus_ist_minus_vip"])
    pn25 = pn[pn["saison"] == "2025/26"]["public_netto_minus_ist_minus_vip"].mean()
    scan = res["scan_ist"]
    lueck = scan[~scan["zutritt_vollstaendig"]]
    art = res["artikel_alle"]
    bier = art[art["name"] == "Bier 4dl."].set_index("saison")
    bier_txt = ", ".join(f"{s_}: {v:.2f}" for s_, v in (bier["umsatz_laut_datei"] / bier["menge"]).items()) if len(bier) else "–"
    seg = res["eintritt_segmente"].set_index(["merkmal", "auspraegung"])["eintrittsquote"]
    gratis = _pct(seg.get(("Tarifgruppe", "Gratis/Promo")))
    einlass = res["ankunft_je_spiel"]["einlass_1pct_min_vor_anpfiff"].median()
    ohne_tickets = int((~kern["einzeltickets_vollstaendig"].astype(bool) & kern["wettbewerb"].isin(["SL", "Cup", "UEFA"])).sum())
    rows = [
        ("Startblocker", "Ticketing", "Was umfasst SOLL genau, und weshalb wird SOLL bei ausverkauften Spielen als Kapazitätswert gesetzt?",
         f"{kap} von {len(kern)} Pflichtspielen haben ein Kapazitäts-SOLL (z.B. =20036−1930+Gäste). Ticketbasiertes SOLL 25/26 = "
         f"Einzeltickets je Verkaufsstelle + 2 Abo-Komponenten ({abo}) − Zweitmarkt. Kapazitätskonstanten wechseln "
         "(19'200, 20'029, 20'036, 20'088, 20'144).",
         "No-Show bei ausverkauften Spielen ist nicht ticketbasiert; Vergleich über Spiele verzerrt."),
        ("Startblocker", "Ticketing", "Wie werden Zweitmarkt, Freikarten, Personal und Abo-Sitze im SOLL gezählt?",
         "SOLL-Formeln ziehen den Zweitmarkt ab (Doppelzählung vermeiden); Gratis-/Promotickets sind im SOLL enthalten "
         f"(Eintrittsquote Gratis/Promo nur {gratis}).", "Definition der Anwesenheitsquote."),
        ("Startblocker", "Catering", "Welche VIP-Zahl wird für «Public Netto» (Nenner des Kundenfrankens) von IST abgezogen?",
         f"Formeln «=IST − x»: x liegt 25/26 im Mittel {abs(pn25):.0f} Personen über «IST VIP» der Historie, 26/27 identisch.",
         "Nenner des KF über die Saisons nicht exakt gleich definiert (Effekt < 1 %)."),
        ("Startblocker", "Catering", "Gilt CHF 14.50 als KF exkl. MwSt, Summe/Summe aller Pflichtspiele 2025/26 (wir rechnen 14.51)?",
         "Blatt «Entwicklung»: 14.51 exkl. MwSt (gewichtet) für MS+Cup 25/26; die Meisterschaftszeilen sind ungewichtete Mittel.",
         "Vergleichsbasis aller KF-Aussagen."),
        ("Startblocker", "Catering", "Sind die Bons (Transaktionen) über alle Zahlungswege vollständig und über die Saisons vergleichbar?",
         "Transaktionen ab 23/24 als Formelsummen (z.B. =14781+153+286); vor 23/24 keine Transaktionen.",
         "Zerlegung KF = Bons/Anwesende × Ø Bon."),
        ("Startblocker", "Catering", "Ist der Kiesplatz im Public-Catering-Total enthalten (auch nach 21/22)? Was bedeuten 80/20 und die Sätze 2.6/8.1 %?",
         "21/22: Contrailer-/Bier-Stände sind frankengenau in der Catering-Datei enthalten. 80/20 = vermutlich MwSt-Aufteilung "
         "Take-away/vor Ort; Netto-Formeln 24/25–25/26 teilen noch durch 1.025/1.077.", "Doppelzählung vermeiden."),
        ("Startblocker", "Daten", "Bitte Datumsfehler bestätigen bzw. in den Quelldateien korrigieren.",
         "Historie 24.08.2024→24.09.2024; Anpfiff 17.05.2026 14:00→16:30; Catering 16.07.2022→23.07.2022; "
         "Kiesplatz 14.07.2022→23.07.2022 und 23.01.2023→22.01.2023; Ticket-CSV 20260126→25.01.2026.",
         "Joins laufen ausschliesslich über das Datum."),
        ("Startblocker", "Datenschutz", "Welche Personenfelder müssen gelöscht werden; ist technische Deduplizierung über UTId/Barcode zulässig?",
         "Einzelticket-Exporte 21/22–24/25 enthalten Namen, Geburtstag, PLZ, Geschlecht (Widerspruch zum Projektantrag). "
         "Sie werden beim Einlesen verworfen; UTId nur zur Deduplizierung.", "NDA/Datenraum."),
        ("Erweiterung", "Zutritt", "Können die Zutritte Juli–Dezember 2024 und das Spiel vom 23.07.2022 nachgeliefert werden?",
         f"{len(lueck)} Spieltage mit unvollständiger Lieferung (z.B. 2. Hälfte 2024 nur 5–22 Scans je Spiel).",
         "Mehr Spiele für Ankunftsanalysen."),
        ("Erweiterung", "Zutritt", "Bitte Toröffnungszeiten je Tor bestätigen und die Bedeutung der Seatinfo-Codes und Reserveleser erklären.",
         "Aus den Scans: Hospitality ≈ 120 min, Fankurve D ≈ 90 min (seit 02.04.2023, vorher 60), Tribünen A/B/C und Gäste ≈ 60 min "
         f"vor Anpfiff (gesamt 1 %-Punkt im Median {einlass:.0f} min). Seatinfo vor 25/26 als «Sektor D2», danach Codes 1–77.",
         "Toröffnung ist ein Clubhebel mit messbarer Wirkung auf die Ankunft."),
        ("Erweiterung", "Ticketing", "Export 2024/25 nach 09.12.2024 und Ticket-CSV Cup-Viertelfinal 04.02.2026 nachliefern?",
         f"{ohne_tickets} Pflichtspiele ohne vollständige Einzelticket-Daten.", "Absatzkurven und Vorlauf."),
        ("Erweiterung", "Ticketing", "Gibt es Stornos/Rückgaben, einen historischen Verkaufsstand je Tag und die verfügbare Kapazität je Sektor?",
         "Exporte enthalten nur den Endbestand (keine Stornos sichtbar). Ohne Kapazität je Tag kein Ausverkaufszeitpunkt.",
         "Projektziel 3 «Absatzverlauf lesen»."),
        ("Erweiterung", "Ticketing", "Aggregierte Abo-Bestände und Abo-Besuchsquoten je Spiel 21/22–25/26?",
         "Abo-No-Show heute nur als Näherung (Rest = SOLL − Einzeltickets) für 21/22 und 22/23.", "Grösster No-Show-Block."),
        ("Erweiterung", "Catering", "Catering-Umsätze je Viertelstunde und Verkaufsstelle sowie Stand→Sektor-Mapping?",
         "Heute nur Spieltotale; Kiesplatz als einzige Standebene.", "Timing des Konsums, Durchsatz, Ort."),
        ("Erweiterung", "Catering", "Bitte bestätigen: Enthält die Spalte «Umsatz Netto» der Artikelauswertung 2023/24 und 2024/25 "
         "Bruttowerte (inkl. MwSt) und 2025/26 Nettowerte? Welche Basis gilt für künftige Lieferungen?",
         f"Bier 4dl, Umsatz laut Datei je Einheit (CHF): {bier_txt} – also 6.00 brutto, 2025/26 6.00 / 1.081. Alle 2025/26-Werte × 1.081 "
         "(Alkohol) bzw. × 1.026 (übrige) ergeben runde Bruttobeträge. Bis v1.0.1 wurden die Saisons ungleich verglichen; seit v1.1.0 "
         "einheitlich brutto (overrides/artikel_basis.csv).", "Sortimentsanteile und Erlös je Einheit über Saisons."),
        ("Erweiterung", "Merchandise", "Merchandise-Umsätze je Kanal (Stadionshop, Online, City) und Tag?",
         "Nicht geliefert; Merchandise ist in Phase 1 keine Voraussetzung.", "Projektantrag Paket 3."),
        ("Erweiterung", "Deckungsbeitrag", "Beteiligungsmodell des Clubs am Catering-Umsatz und Einstandspreise je Artikelkategorie?",
         "Steuerungsgrösse laut Antrag ist der DB pro Anwesendem; Phase 1 bleibt beim Umsatz.", "Umsatz ≠ Ertrag."),
    ]
    return pd.DataFrame(rows, columns=["prioritaet", "bereich", "frage", "evidenz_aus_den_daten", "wofuer_wichtig"])


def aenderungsprotokoll(res: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """Änderungen v1.0.1 → v1.1.0 (13.10.2026). «Vorher» = Werte der übergebenen Version 1.0.1 (fest), «nachher» = aktueller Lauf."""
    k = res["spiel_kpi"]
    kern = k[k["spielstatus"] == "gespielt"]

    def anzahl(flag):
        return int(kern[flag].fillna(False).astype(bool).sum())

    art = res["artikel_gruppen"].set_index(["saison", "name"])["anteil"]
    alk = (f"{_pct(art.get(('2023/24', 'Alkoholische Getränke')), 1)} (23/24) → "
           f"{_pct(art.get(('2025/26', 'Alkoholische Getränke')), 1)} (25/26), beide brutto")
    mu = res["diagnose_muster"]
    runner = mu[(mu["zielgroesse"] == "Kundenfranken exkl. MwSt") & mu["merkmal"].str.startswith("Runner") & (mu["auspraegung"] == "ja")]
    runner_txt = (f"n={int(runner['spiele'].iloc[0])}, KF {runner['mittlere_abweichung_von_erwartung_pct'].iloc[0]:+.1f} % "
                  f"(KI90 {runner['ki90_unten'].iloc[0]:+.1f} bis {runner['ki90_oben'].iloc[0]:+.1f})").replace("-", "−") if len(runner) else "–"
    tests = res.get("importtests")
    n_tests = f"{int(tests['bestanden'].sum())} von {len(tests)} bestanden" if tests is not None else "siehe 03_Importtests"
    rows = [
        ("Bemerkungs-Codierung: mobiler Verkauf",
         "«Alle Stände geöffnet ausser Runner B, C, D», Runner in «folgende Stände waren geschlossen: …» und «nur einer … im Einsatz» "
         "wurden als «Runner im Einsatz» gelesen. Neu zählen nur ausdrückliche Angaben je Sektor (Funktion mobiler_verkauf; "
         "Kassenzuteilungen wie «Runner C = Stand C4» sind keine Einsatzangabe).",
         "13 Pflichtspiele mit «Runner/Bauchläden nicht im Einsatz»",
         f"{anzahl('mobiler_verkauf_reduziert')} Pflichtspiele «ganz oder teilweise nicht im Einsatz»", "A1, A4, C12, K6, K7, E2"),
        ("Bemerkungs-Codierung: Plattform-Event",
         "«Side Event 1: BBQ S1» ist eine Kassenzuteilung und wurde als Plattform-Event gezählt, ebenso «mit Glühwein». Neu zählen "
         "nur Programm/Zusatzangebote (Winterzauber, Family/Kids Day, Raclette, Suppe, Sittermarsch); die Espen Kids Days "
         "16.04.2023 und 02.09.2023 werden neu erkannt.",
         "18 Pflichtspiele", f"{anzahl('event_plattform')} Pflichtspiele", "A1, A4, C12, K6, K7"),
        ("Bemerkungs-Codierung: Stände geschlossen",
         "«Alle Stände offen ausser Bier S2» (12.12.2024) und «… ausser Bierbar A3, Bierbar C …» (27.08.2026) gelten neu als "
         "geschlossene Stände; die Schreibweise «Allä Stände offen» wird erkannt.",
         "15 Pflichtspiele", f"{anzahl('stand_geschlossen')} Pflichtspiele", "A4, C12, K6"),
        ("Folge: wiederkehrende Muster (K7)",
         "Mit korrekter Codierung liegen Spiele ohne (vollständigen) mobilen Verkauf beim KF unter der Kontexterwartung; "
         "19.02.2023 (FC Luzern) gilt neu als «möglicher Clubhebel» statt «ungeklärt».",
         "n=9, KF −2.4 % (KI90 −6.5 bis +1.8)", runner_txt, "K6, K7, E2, Methodennotiz §10"),
        ("Artikelauswertung brutto/netto",
         "Die Spalte «Umsatz Netto» enthält 2023/24–2024/25 Bruttowerte, 2025/26 Nettowerte (Bier 4dl je Einheit 6.00 → 5.96 → "
         "5.54, × 1.081 = 5.98 brutto). Neu einheitlich brutto (overrides/artikel_basis.csv; MwSt-Klasse je Artikel, 2025/26 × 1.081 "
         "bzw. × 1.026). Die Klärungsfrage «Bier −7.1 %» entfällt (kein Preiseffekt, sondern Basiswechsel).",
         "Alkoholanteil 53.5 % (23/24) → 48.6 % (25/26); Bier je Einheit −7.1 %",
         f"Alkoholanteil {alk}; Bier je Einheit stabil (CHF 5.96–6.00 brutto)", "C5, C6, C7, 01, E1, Abb. 10, Methodennotiz §7"),
        ("Importtests",
         "Test «Artikelsumme vs. Catering exkl. ±3 %» bestand nur zufällig (Brutto gegen Netto). Ersetzt durch «Artikelsumme brutto "
         "vs. Payfix inkl. ±3 %»; neu «Normalsatz-Artikel = Gruppe Alkohol» und «Erlös je Einheit zwischen Saisons stabil».",
         "17 von 17 bestanden", n_tests, "03_Importtests"),
    ]
    out = pd.DataFrame(rows, columns=["bereich", "aenderung", "vorher_v1_0_1", "nachher_v1_1_0", "betroffene_blaetter"])
    out.insert(0, "version", "1.1.0 (13.10.2026)")
    out["unveraendert"] = ("Datenmodell, KPI, Kontextmodelle (Effekt-Matrix, Modellgüte), Erwartungswerte der Diagnosekarte, "
                           "Ankunft, Absatz – die korrigierten Merkmale sind keine Modellvariablen.")
    return out


def phase2_kandidaten(res: dict[str, pd.DataFrame]) -> pd.DataFrame:
    seg = res["eintritt_segmente"].set_index(["merkmal", "auspraegung"])["noshow_quote"]
    mx = res["kontext_effekt_matrix"].set_index(["zielgroesse", "variable"])
    sek = res["ankunft_je_sektor"].dropna(subset=["median_min_vor_anpfiff"]).groupby("sektor")["median_min_vor_anpfiff"].median()
    ab = res["absatz_ausverkauft"].set_index("ausverkauft")
    mu = res["diagnose_muster"]
    ein = res["einlass_je_eingang"].set_index("sektor")["einlass_1pct_median"]
    did = res["toroeffnung_did"].set_index("zielgroesse")
    did_m, did_a = did.loc["Median Ankunft, min vor Anpfiff"], did.loc["Anteil Ankunft ≥ 60 min vor Anpfiff"]
    st = mu[(mu["merkmal"].str.startswith("Operativer Hinweis")) & (mu["auspraegung"] == "ja")].set_index("zielgroesse")

    def e(z, v):
        try:
            r = mx.loc[(z, v)]
            return f"{r['effekt']:+.1f} {'%' if r['einheit_effekt'] == '%' else 'Pp.'} ({r['beurteilung']})"
        except KeyError:
            return "–"

    def g(m, a):
        return _pct(seg.get((m, a)))

    rows = [
        ("No-Show bei Gross- und Gratisbestellungen", "Zweitmarkt/Kommunikation (Clubhebel)",
         f"No-Show Einzeltickets 21/22–22/23: Bestellungen ab 10 Tickets {g('Tickets pro Bestellung', '10+')}, "
         f"Gratis/Promo {g('Tarifgruppe', 'Gratis/Promo')}, Inhouse {g('Verkaufskanal', 'Inhouse (Geschäftsstelle/Kasse)')} "
         f"vs. Online-Shop {g('Verkaufskanal', 'Online-Shop')}.",
         "Aktuelle Eintrittsdaten je Einzelticket (ZKS) ab 23/24; Zweitmarkt-Nutzung je Segment."),
        ("Abendspiele: weniger Anwesende, mehr Konsum", "Programm/Angebot (Clubhebel); Anstosszeit selbst = Liga",
         f"Anwesenheitsquote {e('Anwesenheitsquote (IST/SOLL)', 'Abendspiel (Anpfiff ab 20 Uhr)')}; "
         f"KF {e('Kundenfranken exkl. MwSt', 'Abendspiel (Anpfiff ab 20 Uhr)')}, getragen von Bons/Anwesende.",
         "Viertelstunden-Umsätze, um den Mehrkonsum zeitlich zu verorten."),
        ("Werktagsspiele: tieferer Ø Bon", "Angebot für späte Ankünfte (Clubhebel)",
         f"Ø Bon {e('Ø Bon exkl. MwSt', 'Werktag (Mo–Fr) statt Wochenende')}; KF {e('Kundenfranken exkl. MwSt', 'Werktag (Mo–Fr) statt Wochenende')}.",
         "Zeitdaten Catering; Ankunft nach Eingang an Werktagen."),
        ("Frühere Toröffnung Tribünen A/B/C", "Toröffnung/Programm (Clubhebel)",
         "Einlass-Beginn heute: " + ", ".join(f"{s_} {v:.0f} min" for s_, v in ein.items()) + " vor Anpfiff. Natürliches Experiment "
         f"Sektor D (ab 02.04.2023 90 statt 60 min): Ankunft {did_m['did_effekt']:+.1f} min (95 %-KI {did_m['ki95_unten']:.0f} bis "
         f"{did_m['ki95_oben']:.0f}), Anteil ≥ 60 min {did_a['did_effekt'] * 100:+.0f} Pp. gegenüber A/B/C. Median Ankunft je Eingang: "
         + ", ".join(f"{s_} {v:.0f} min" for s_, v in sek.sort_values(ascending=False).items()) + ".",
         "Pilot mit früherer Öffnung einzelner Tore + Standumsätze je Viertelstunde und Stand→Sektor-Mapping (Konsumwirkung messen)."),
        ("Kälte und Wintersortiment", "Sortiment (Clubhebel); Wetter = extern",
         f"KF {e('Kundenfranken exkl. MwSt', 'Temperatur bei Anpfiff')} je +5 °C; Ø Bon {e('Ø Bon exkl. MwSt', 'Temperatur bei Anpfiff')}.",
         "Artikel je Spiel (heute nur Saisonsummen)."),
        ("Operative Engpässe (Stände zu, Runner/Personal fehlt, Technik)", "Standbesetzung/Personal/Payment (Clubhebel)",
         "Spiele mit dokumentiertem operativem Hinweis: Ø Bon " +
         (f"{st.loc['Ø Bon exkl. MwSt', 'mittlere_abweichung_von_erwartung_pct']:+.1f} %" if 'Ø Bon exkl. MwSt' in st.index else "–") +
         ", KF " + (f"{st.loc['Kundenfranken exkl. MwSt', 'mittlere_abweichung_von_erwartung_pct']:+.1f} %"
                     if 'Kundenfranken exkl. MwSt' in st.index else "–") +
         " gegenüber Erwartung (nicht belastbar); Schliessungen folgen oft tiefer Nachfrage (umgekehrte Kausalität möglich).",
         "Standöffnungen je Spiel strukturiert erfassen; Viertelstunden-Umsätze."),
        ("Ausverkaufte Spiele: früher Einzelticket-Absatz", "Abo-/Zweitmarktprozess (Clubhebel); kein Dynamic Pricing",
         f"Halbe Einzelticket-Menge verkauft {ab.loc[True, 't50_median']:.0f} Tage vor ausverkauften Spielen vs. "
         f"{ab.loc[False, 't50_median']:.0f} Tage sonst; Anteil Spieltagsverkauf {_pct(ab.loc[True, 'anteil_spieltag_median'])} vs. "
         f"{_pct(ab.loc[False, 'anteil_spieltag_median'])}.",
         "Verfügbare Kapazität und Verkaufsstand je Tag (Projektantrag Paket 2)."),
    ]
    out = pd.DataFrame(rows, columns=["pruefkandidat", "hebeltyp", "befund_phase_1", "benoetigte_daten_phase_2"])
    out["leitplanken"] = "Kein Dynamic Pricing, Kapazität fix, keine Personensegmentierung; Umsatzwirkung erst in Phase 2 quantifizieren."
    return out


BESCHREIBUNG = {
    "match_id": "Stabiler Spielschlüssel: Datum (JJJJMMTT) + Wettbewerb (SL/Cup/UEFA)",
    "datum": "Spieldatum (lokal)", "saison": "Saison (Wechsel 1. Juli; COVID-Saison 2019/20 gemäss Quelle)",
    "wettbewerb": "SL = Super League (inkl. Meisterschafts-/Abstiegsrunde), Cup, UEFA",
    "spielstatus": "gespielt | abgesagt | geplant (nach Datenstand)", "gegner": "Gegner (kanonischer Name, nur Anzeige/Kontrolle)",
    "gegner_anzeige": "Gegner (Anzeigename)", "top_gegner": "Gegner FC Basel, BSC Young Boys oder FC Zürich (vorab festgelegt)",
    "anpfiff": "Anpfiffzeit (Mehrheit aus Historie, Catering, Kontext, Resultate, Ticket-Export)",
    "anpfiff_quellen": "Quellen, die den gewählten Anpfiff nennen", "anpfiff_abweichungen": "Abweichende Quellenwerte",
    "wochentag": "Wochentag", "wochenende": "Samstag/Sonntag", "anpfiff_slot": "Nachmittag (<17), Vorabend (17–19), Abend (≥20)",
    "abendspiel": "Anpfiff ab 20 Uhr", "winter": "Monate November–Februar",
    "soll": "SOLL laut Historie (verkauft/ausgegeben; bei ausverkauften Spielen teils Kapazitätswert)",
    "ist": "IST laut Historie (anwesend, Drehkreuz-Zählung inkl. VIP und Gäste)", "ist_vip": "IST VIP (Hospitality)",
    "ist_gaeste": "IST Gästesektor", "zweitmarkt": "Über den Zweitmarkt weiterverkaufte Tickets",
    "noshow_quote": "1 − IST/SOLL", "anwesenheitsquote": "IST/SOLL", "noshow_abs": "SOLL − IST",
    "ausverkauft": "Ausverkauft-Flag ODER Bemerkung «ausverkauft» in der Historie",
    "soll_definition": "Herkunft des SOLL-Werts (Formel Ticketkomponenten, Kapazitätsformel, Fixwert …)",
    "ist_qualitaet": "IST aus Zählung | mit Ergänzung | geschätzt/Scanprobleme",
    "soll_ticketbasiert": "SOLL ist kein Kapazitätswert", "public_netto": "Public-Anwesende laut Caterer (≈ IST − VIP); Nenner KF",
    "transaktionen": "Anzahl Catering-Transaktionen (Bons), ab 2023/24", "umsatz_inkl": "Public-Catering-Umsatz inkl. MwSt (CHF)",
    "umsatz_exkl": "Public-Catering-Umsatz exkl. MwSt (CHF; ab 20/21 effektive Mischsätze)",
    "kf_inkl": "Kundenfranken inkl. MwSt = Umsatz inkl. / Public Netto", "kf_exkl": "Kundenfranken exkl. MwSt = Umsatz exkl. / Public Netto",
    "bons_pro_anwesende": "Transaktionen / Public Netto (≠ Kaufquote)", "bon_inkl": "Ø Bon inkl. MwSt = Umsatz / Transaktionen",
    "bon_exkl": "Ø Bon exkl. MwSt", "besucher_scans": "Eindeutige Tickets mit erlaubtem Durchgang (erster Scan je Ticket)",
    "abweichung_scans_ist": "Scans / IST − 1", "einzeltickets": "Anzahl Einzeltickets (Export bzw. CSV)",
    "einzeltickets_vollstaendig": "Einzelticket-Daten decken den Verkauf bis zum Spieltag ab",
    "in_kontexttabelle": "Spiel ist in der Spielkontext-Tabelle der Gruppe erfasst",
    "rang_gegner": "Tabellenrang Gegner vor dem Spiel (berechnet aus Resultaten, Spiele strikt vor dem Datum)",
    "ppg_gegner_gestuetzt": "Punkte/Spiel Gegner vor dem Spiel, mit Vorjahreswert gestützt (5 Spiele Gewicht)",
    "temp_anpfiff_c": "Temperatur in der Anpfiff-Stunde (MeteoSchweiz STG, °C)",
    "niederschlag_anreise_mm": "Niederschlag in den Stunden, die die 2 h vor Anpfiff berühren (mm)",
    "regen_anreise": "Niederschlag Anreise ≥ 0.5 mm", "schulferien": "Schulferien Stadt St.Gallen (Kontexttabelle bzw. deren Kalender)",
    "free_tv_srf": "Übertragung im Free-TV (SRF) laut Kontexttabelle",
    "median_min_vor_anpfiff": "Median der Ankunft (Minuten vor Anpfiff, erster Scan je Ticket)",
    "anteil_ab_45_min": "Anteil Besucher mit Ankunft ≥ 45 min vor Anpfiff",
    "anteil_letzte_15_min_inkl_nach_anpfiff": "Anteil Ankunft < 15 min vor Anpfiff inkl. nach Anpfiff",
    "anteil_am_spieltag": "Anteil Einzeltickets, die am Spieltag verkauft wurden", "t50_tage": "Tage vor Spiel, an denen 50 % der Einzeltickets verkauft waren",
    "eintrittsquote_einzel": "Anteil Einzeltickets mit Eintritt (ZKS) – nur 21/22 und 22/23 belastbar",
    "zks_valide": "Eintrittsdaten je Einzelticket für dieses Spiel valide",
    "erwartet_kf_exkl": "Erwarteter KF unter Kontext (Leave-one-match-out)", "z_wert_kf_exkl": "Standardisierte Abweichung beobachtet vs. erwartet",
    "referenzluecke_konsum_chf": "(erwarteter KF − beobachteter KF) × Public Netto; modellbasiert, KEIN realisierbarer Mehrumsatz",
    "erwartet_anwesenheitsquote": "Erwartete Anwesenheitsquote unter Kontext", "z_wert_anwesenheitsquote": "Standardisierte Abweichung Anwesenheit",
    "einordnung_konsum": "Kontextassoziation, ungeklärte Abweichung oder möglicher Clubhebel (Konsum)",
    "einordnung_anwesenheit": "Einordnung der Anwesenheitsabweichung", "mechanismen": "Mögliche Mechanismen aus Bemerkungen und Teilmodellen",
    "fehlende_anwesende_ref": "(erwartete − beobachtete Quote) × SOLL; nur bei ticketbasiertem SOLL",
    "chf_szenario_phi_0_6": "Szenario: fehlende Anwesende × 0.6 × KF (expliziter Annahmewert φ = 0.6)",
    "kernscope": "Pflichtspiel der Herren (SL/Cup/UEFA), gespielt",
    "hat_anwesenheit": "SOLL und IST vorhanden", "hat_catering_umsatz": "Catering-Umsatz und Public Netto vorhanden",
    "hat_bons": "Transaktionen vorhanden", "hat_zutritt_vollstaendig": "Zutrittslieferung vollständig (Scans ≥ 90 % IST)",
    "hat_einzeltickets_vollstaendig": "Einzelticket-Daten vollständig", "hat_eintritt_zks_valide": "Eintritt je Einzelticket valide",
    "hat_kontext_gruppe": "In Kontexttabelle der Gruppe", "im_kontextmodell": "Teil der Kontextmodelle (Hauptstichprobe)",
    "effekt": "Effekt der Variablen (log-Ziele: %, Quoten: Prozentpunkte am Mittelwert)",
    "ki95_unten": "95 %-Konfidenzintervall unten (robuste HC3-Standardfehler)", "ki95_oben": "95 %-Konfidenzintervall oben",
    "vorzeichen_stabil_loso": "Anteil Leave-one-season-out-Schätzungen mit gleichem Vorzeichen",
    "vorzeichen_stabil_sensitivitaet": "Anteil Sensitivitätsvarianten mit gleichem Vorzeichen",
    "beurteilung": "belastbar | Hinweis (Richtung stabil, Grösse unsicher) | nicht belastbar schätzbar",
}


_DATENTYP = {"string": "Text", "floating": "Zahl", "mixed-integer-float": "Zahl", "integer": "Ganzzahl",
             "boolean": "ja/nein", "datetime64": "Datum/Zeit", "datetime": "Datum/Zeit", "date": "Datum", "empty": "leer"}


def _datentyp(s: pd.Series) -> str:
    """Lesbarer Typ, unabhängig von der pandas-Version (pandas 2 und 3 benennen Text- und Datumsspalten verschieden)."""
    return _DATENTYP.get(pd.api.types.infer_dtype(s, skipna=True), "gemischt")


def datenwoerterbuch(tabellen: dict[str, pd.DataFrame]) -> pd.DataFrame:
    rows = []
    for name, df in tabellen.items():
        for c in df.columns:
            rows.append({"tabelle": name, "spalte": c, "beschreibung": BESCHREIBUNG.get(c, ""),
                         "datentyp": _datentyp(df[c]), "fehlend": int(df[c].isna().sum()), "zeilen": len(df)})
    return pd.DataFrame(rows)

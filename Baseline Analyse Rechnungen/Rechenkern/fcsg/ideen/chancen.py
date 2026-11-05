"""Chancenfelder, Kernbefunde und Datenanfragen – die Brücke von den Daten zur Ideenfindung (Simon & Reto).

Jedes Chancenfeld nennt Befund, Evidenz, Hebel-Arithmetik (isoliert, nicht addierbar), Steuerbarkeit, Leitplanken,
Datenlücke, Leitfragen («Wie könnten wir …?») und wie ein Pilot messbar wäre. Es enthält bewusst KEINE fertigen Ideen und
KEINE Potenzialsumme. Rangfolgen sind ordinal (Evidenz, Steuerbarkeit, Reichweite, Datenreife).
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field

import pandas as pd

from .fmt import chf_k, dez, p, pct, pp, z

LEITPLANKEN_SCHLUESSEL = ("Dynamic Pricing", "Personensegmentierung", "Kapazität/Ausbau", "Hospitality", "Umsatz ≠ DB")


@dataclass
class Chancenfeld:
    nr: int
    titel: str
    treiber: str
    kernzahl: str
    befund: list[str]
    evidenz: str
    evidenz_begruendung: str
    steuerbarkeit: str
    clubhebel: str
    reichweite: str
    datenreife: str
    hebel_arithmetik: str
    leitplanken: dict[str, str]
    datenluecke: str
    leitfragen: list[str]
    pilot_messung: str
    grafik: str
    quellen: str
    warnhinweis: str = ""
    extras: dict = field(default_factory=dict)


def _lp(**abweichend) -> dict[str, str]:
    basis = {"Dynamic Pricing": "nicht betroffen (keine Preisänderung)",
             "Personensegmentierung": "nur Sektor/Spiel/Tarif, aggregiert",
             "Kapazität/Ausbau": "nicht betroffen", "Hospitality": "nicht betroffen",
             "Umsatz ≠ DB": "CHF = Caterer-Umsatz; Club-Anteil und Kosten unbekannt"}
    basis.update(abweichend)
    return basis


def chancenfelder(kz: dict) -> list[Chancenfeld]:
    np_arith = (f"1 Pp. weniger No-Show = {z(kz['fw_noshow_anw_spiel'])} zusätzliche Anwesende je Spiel ≈ "
                f"{chf_k(kz['fw_noshow_pp_6'])} / {chf_k(kz['fw_noshow_pp_8'])} / {chf_k(kz['fw_noshow_pp_10'])} Catering-Umsatz je Saison "
                "(φ = 0.6 / 0.8 / 1.0; exkl. MwSt).")
    felder = [
        Chancenfeld(
            1, "Leere bezahlte Plätze aktivieren", "Anwesenheitsquote (Abo-Plätze)",
            f"{z(kz['b_noshow_summe'])} leere, vergebene Plätze (verkauft oder ausgegeben) in der Saison 2025/26 – der Zweitmarkt besetzt "
            f"nur {p(kz['zm_wb_2526'])} davon neu.",
            [f"No-Show 2025/26: {p(kz['b_noshow_quote'], 1)} des SOLL (Ø {z(kz['b_noshow_summe'] / kz['b_spiele'])} Plätze je Spiel). "
             f"Nicht ausverkaufte Spiele {p(kz['ns_offen'])}, ausverkaufte {p(kz['ns_ausv'])}.",
             f"Einzeltickets werden zu rund {p(kz['seg_zks_anwesenheit'])}–{p(kz['tr_C_einzel_uefa'])} genutzt. Die leeren Plätze sind vor allem "
             f"Abo-Plätze: Abo-Anwesenheit 2026/27 (Näherung, 4 Spiele) Fankurve D {p(kz['tr_D_abo_lo'])}–{p(kz['tr_D_abo_hi'])}, "
             f"Osttribüne B {p(kz['tr_B_abo_lo'])}–{p(kz['tr_B_abo_hi'])}, Tribüne C {p(kz['tr_C_abo_lo'])}–{p(kz['tr_C_abo_hi'])}.",
             f"In D bleiben je Spiel rund {z(kz['tr_D_leer_spiel'])} vergebene Plätze leer, in C {z(kz['tr_C_leer_spiel'])}, in B "
             f"{z(kz['tr_B_leer_spiel'])}. In D gab es 2025/26 in {kz['zm_d_ohne']} von 19 Spielen keinen einzigen Zweitmarkt-Verkauf.",
             f"Zweitmarkt 2025/26: {z(kz['zm_2526'])} Weiterverkäufe; {p(kz['zm_letzte2'])} davon in den letzten 2 Tagen, "
             f"{p(kz['zm_spieltag'])} am Spieltag. Käufer zahlen {z(kz['zm_aufpreis'], 1)} % Gebühr.",
             f"Kontext: No-Show an Werktagen {p(kz['ns_werktag'])} (Wochenende {p(kz['ns_wochenende'])}), abends {p(kz['ns_abend'])} "
             f"(nachmittags {p(kz['ns_nachmittag'])}), im Winter {p(kz['ns_winter'])}."],
            "stark", "Umfang und Zweitmarkt aus Vollerhebung; Tribünenwerte = Näherung aus 4 Sommerspielen 2026/27 (UEFA-Spiele bestätigen die Methode).",
            "hoch", "Zweitmarkt-Prozess (Freigabe, Sichtbarkeit, Zeitpunkt), generische Kommunikation an alle Abo-Inhaber eines Sektors",
            "alle Spiele (v.a. Winter, Werktag, Abend)", "heute nutzbar; Abo-Besuche je Spiel würden die Näherung ersetzen",
            np_arith + " Wichtig: Aktivieren (Inhaber kommt) wirkt in jedem Spiel; Weiterverkaufen bringt nur dann zusätzliche "
            "Besucher, wenn die Nachfrage die freien Plätze übersteigt (ausverkaufte Spiele/Sektoren).",
            _lp(**{"Dynamic Pricing": "Zweitmarkt-Preis = Originalpreis + Gebühr – unverändert lassen",
                   "Personensegmentierung": "keine individuelle Ansprache nach Nutzungsverhalten; nur generisch je Sektor/Spiel"}),
            "Abo-Anwesenheit je Spiel und Sektor (aggregiert, alle Saisons); angebotene vs. verkaufte Zweitmarkt-Plätze; wer den "
            "Zweitmarkt-Erlös erhält; Kapazität je Sektor.",
            ["Wie könnten wir es Abo-Inhabern so einfach machen, ihren Platz freizugeben, dass es sich auch 1–2 Tage vor dem Spiel noch lohnt?",
             "Wie könnten wir in der Fankurve D – tiefste Abo-Anwesenheit, kaum Zweitmarkt – freie Plätze sichtbar und nutzbar machen?",
             "Was müsste sich ändern, damit Abo-Inhaber bei Winter-, Werktags- und Abendspielen kommen oder ihren Platz weitergeben?",
             "Wie könnten wir bei ausverkauften Spielen, wo Nachfrage die Plätze übersteigt, die Wiederbesetzung erhöhen?"],
            "Pilot in einem Sektor (z.B. D), Vergleichssektor ohne Massnahme; Messgrösse = Scans je vergebenem Platz und Zweitmarkt-"
            "Verkäufe je Spiel, Vorher/Nachher wie beim Toröffnungs-Experiment (Differenz-in-Differenzen).",
            "abb_i02_leere_plaetze_zweitmarkt.png", "Blätter Leere_Plaetze*, Zweitmarkt*, Tribuene_2627*"),
        Chancenfeld(
            2, "Gruppen- und Gratistickets, die nicht genutzt werden", "Anwesenheitsquote (Einzeltickets)",
            f"{p(kz['seg_inhouse10_anteil'])} aller No-Shows bei Einzeltickets stammen aus Inhouse-Bestellungen ab 10 Tickets.",
            [f"Gültige Eintrittsdaten 2021/22–2022/23: Inhouse-Grossbestellungen bezahlt {p(kz['seg_inhouse10_quote_bez'])} No-Show, "
             f"gratis {p(kz['seg_inhouse10_quote_gratis'])}; Online-Shop mit 2–4 Tickets nur {p(kz['seg_online24_quote'], 1)}.",
             f"Je Spiel rund {z(kz['seg_inhouse10_tickets_spiel'])} Tickets aus solchen Bestellungen, davon rund "
             f"{z(kz['seg_inhouse10_noshows_spiel'])} leer.",
             f"Gratis-/Promotickets haben generell tiefere Nutzung ({p(kz['tarif_gratis'])} statt {p(kz['tarif_voll'])} bei Vollpreis)."],
            "mittel", "Klare Muster, aber nur für 2021/22–2022/23 messbar (Eintritt je Ticket danach nicht erfasst); 21/22 COVID-geprägt.",
            "hoch", "Vergabe und Bestätigung von Gruppen-/Gratiskontingenten, Rückgabe ungenutzter Tickets",
            "alle Spiele mit Gruppenkontingenten", "Prüfung mit aktuellen Eintrittsdaten je Bestellkanal nötig",
            np_arith,
            _lp(**{"Personensegmentierung": "nur Bestellkanal/Bestellgrösse aggregiert; keine Besteller-Namen",
                   "Dynamic Pricing": "Gratis-/Promotickets sind kein Preishebel"}),
            "Eintritt je Ticket ab 2023/24 (ZKS) aggregiert nach Kanal und Bestellgrösse; Art der Grossbesteller (Schulen, Vereine, "
            "Sponsoren – aggregiert).",
            ["Wie könnten wir sicherstellen, dass Gruppen- und Gratistickets auch genutzt werden?",
             "Wie könnten nicht benötigte Tickets aus Grosskontingenten rechtzeitig zurückfliessen?",
             "Wie könnten Gruppen ein Erlebnis vor dem Anpfiff bekommen, das sie früh ins Stadion holt?"],
            "Eintrittsquote der Grossbestellungen je Spiel (ZKS) vor/nach einer Prozessänderung, Vergleich mit Online-Bestellungen.",
            "abb_i04_noshow_segmente.png", "Blatt Einzel_NoShow_Segmente"),
        Chancenfeld(
            3, "Das Zeitfenster vor dem Anpfiff", "Ankunft (Konsumfenster)",
            f"Tribüne C: im Schnitt {z(kz['vw_C'])} min vor Anpfiff im Stadion – {p(kz['vw_C_l15'])} kommen in den letzten 15 Minuten "
            f"(≈ {z(kz['vw_C_l15_personen'])} Personen je Spiel).",
            [f"Verweilzeit vor Anpfiff: Fankurve D {z(kz['vw_D'])} min, Tribünen A {z(kz['vw_A'])}, B {z(kz['vw_B'])}, C {z(kz['vw_C'])} min.",
             f"Bei ähnlicher Besucherzahl verbringen D-Fans {z(kz['vw_D_minuten'])} Besucher-Minuten je Spiel vor Anpfiff im Stadion, "
             f"C-Fans {z(kz['vw_C_minuten'])}.",
             f"Die Toröffnung wirkt: Seit D 30 min früher öffnet, kommen D-Fans {z(kz['tor_did'], 1)} min früher "
             f"(95 %-KI {z(kz['tor_did_lo'], 0)}–{z(kz['tor_did_hi'], 0)}).",
             f"Der Einlass ist kaum der Engpass: Die Spitzen in A/B/C erreichen {p(kz['einlass_ABC_min'])}–{p(kz['einlass_ABC_max'])} der "
             f"Leser-Kapazität, nur der Einlassbeginn in D {p(kz['einlass_D'])}. Spätes Kommen ist Verhalten, nicht Stau.",
             f"An Werktagen kommen Fans später ({pct(kz['vw_werktag_abw'], 1).replace(' %', ' min')} gegenüber dem Saisonmittel, "
             f"{p(kz['vw_werktag_l15'])} statt {p(kz['vw_wochenende_l15'])} in den letzten 15 min)."],
            "mittel", "Ankunft und Toröffnungs-Wirkung belegt; ob frühere Ankunft mehr Konsum bringt, ist ohne Kassen-Zeitstempel offen "
            "(auf Spielebene kein belastbarer Zusammenhang).",
            "hoch", "Toröffnungszeiten je Tor, Programm und Angebote vor Anpfiff (nicht-preislich)",
            "alle Spiele; grösster Hebel bei C (≈ 4'700 Besucher)", "Konsumwirkung erst mit Payfix-Daten je Kasse/Viertelstunde messbar",
            f"Isoliert: +1 % Kauffrequenz ≈ {chf_k(kz['fw_frequenz_pct_10'])} je Saison; +CHF 1 Ø Bon ≈ {chf_k(kz['fw_bon_chf_10'])}. "
            "Wie viel Zusatzkonsum frühere Ankunft bringt, ist eine Phase-2-Annahme.",
            _lp(**{"Dynamic Pricing": "keine Rabatte nach Uhrzeit (Preisaktion – ausgeschlossen)"}),
            "Payfix-Umsatz je Kasse und Viertelstunde (Kassen sind laut Bemerkungen Ständen/Runnern zugeordnet), Stand→Sektor-Zuordnung, "
            "Toröffnungszeiten je Tor (Bestätigung).",
            ["Wie könnten wir Besucher der Tribüne C 15 Minuten früher ins Stadion holen?",
             "Was erleben Fans in A, B und C zwischen Toröffnung und Anpfiff – und was fehlt ihnen?",
             "Wie könnten wir die letzten 15 Minuten, in denen ein Viertel von C ankommt, für schnelle Käufe nutzen?",
             "Was bräuchte ein Fan, der an einem Werktag direkt von der Arbeit kommt?"],
            "Frühere Toröffnung in C an 3 Spielen, A/B als Vergleich (Differenz-in-Differenzen wie Sektor D); Konsumwirkung mit "
            "Payfix-Viertelstunden je Kasse.",
            "abb_i07_verweilzeit.png", "Blätter Verweilzeit*, Einlass_Spitzen, Toroeffnung_Beleg"),
        Chancenfeld(
            4, "Mehr Kaufmomente: die Kauffrequenz", "Bons je Anwesendem",
            f"Der KF stieg 2023/24→2025/26 um {pct(kz['kf_entw_kf'])} – getragen von {pct(kz['kf_entw_freq'])} Kaufhäufigkeit, "
            f"bei {pct(kz['kf_entw_bon'])} kleinerem Bon.",
            [f"Preise je Einheit blieben praktisch gleich (Preisindex {pct(kz['pm_preis'], 1)}); Einheiten je Bon sanken von "
             f"{dez(kz['einh_bon_2324'])} auf {dez(kz['einh_bon_2526'])}, Einheiten je Anwesendem stiegen von {dez(kz['einh_anw_2324'])} "
             f"auf {dez(kz['einh_anw_2526'])}: Fans kaufen öfter, aber kleinere Warenkörbe.",
             f"Spiele ohne (vollständigen) mobilen Verkauf (Runner/Bauchläden, n={int(kz['mob_n_nein'])}) liegen beim KF {pct(kz['mob_nein'])} "
             f"unter der Kontexterwartung, Spiele mit ausdrücklichem Einsatz (n={int(kz['mob_n_ja'])}) {pct(kz['mob_ja'])} darüber "
             f"(Differenz {pct(kz['mob_diff'])}, KI90 {pct(kz['mob_diff_lo'])} bis {pct(kz['mob_diff_hi'])}).",
             f"Bei vollem Haus ist kein Engpass messbar (kein «Knick», alle p ≥ {dez(kz['knick_p_roh_min'], 2)}); die Bons wachsen mit Elastizität "
             f"{dez(kz['knick_elast_bons'])} – mehr Zuschauer kaufen eher grössere Bons als mehr Bons.",
             f"Digitale Kanäle sind klein: Just Eat {p(kz['zw_justeat'], 1)} (25/26), Pick Up {p(kz['zw_pickup'], 1)} (26/27)."],
            "mittel", "Frequenz-Trend aus Vollerhebung; Effekt des mobilen Verkaufs an der Nachweisgrenze (MDE "
            f"{z(kz['mob_mde'], 1)} %), Codierung nur aus Bemerkungen.",
            "hoch", "Einsatz von Runnern/Bauchläden je Sektor, Standbesetzung, Kassen/Payment, Pick-up",
            "alle Spiele", "heute nutzbar; Kassen-/Viertelstundendaten und Personalstunden würden den Effekt sauber messen",
            f"+1 % Kauffrequenz ≈ {chf_k(kz['fw_frequenz_pct_10'])} je Saison; +0.1 Bons je Anwesendem ≈ "
            f"{chf_k(kz['fw_bons_pro_anwesende_10'])} je Saison (isoliert, exkl. MwSt).",
            _lp(**{"Umsatz ≠ DB": "Personal-/Gerätekosten des mobilen Verkaufs fehlen (Phase 2: DB-Sicht)"}),
            "Payfix je Kasse/Viertelstunde, Runner-Einsatz strukturiert je Spiel/Sektor, Personalstunden.",
            ["Wie könnten wir in jedem Sektor zusätzliche Kaufmomente schaffen – auch bei Kälte und an Werktagen?",
             "Wie könnten digitale Kanäle echte Zusatzkäufe auslösen statt nur Käufe zu verlagern?",
             "Wo gehen heute Kaufmomente verloren (Pause, Platz verlassen ungern, letzte 15 Minuten)?"],
            "Mobiler Verkauf je Spiel und Sektor nach festem Plan abwechselnd einsetzen (Randomisierung); Messgrösse = Bons je Anwesendem "
            "gegenüber Kontexterwartung.",
            "abb_i09_kf_entwicklung.png", "Blätter KF_Entwicklung, Preis_Menge, Mobiler_Verkauf*, Durchsatz_Knick"),
        Chancenfeld(
            5, "Warenkorb und Sortiment nach Spieltyp", "Ø Bon und Sortimentsmix",
            f"Die Anstosszeit verschiebt den Warenkorb: Samstag ab 20 Uhr KF Alkohol {pct(kz['alk_sa20_kf'], 0)}, KF Food & alkoholfrei "
            f"{pct(kz['food_sa20_kf'], 0)} gegenüber Samstag 17–19.59 Uhr bei gleichem Kontext.",
            [f"Neuer Spiel-Indikator: Alkoholanteil je Spiel aus dem MwSt-Mix der Kassen (validiert: ≤ {dez(kz['alk_val_maxdiff'], 1)} Pp. "
             f"Abweichung zur Artikelauswertung, r = {dez(kz['alk_val_r'])} mit dem Kiesplatz).",
             f"Je gegenüber Samstag 17–19.59 Uhr: Sonntagnachmittag KF Alkohol {pct(kz['alk_nachm_kf'], 0)}, Food & alkoholfrei "
             f"{pct(kz['food_nachm_kf'], 0)}; Werktagabend Alkohol {pct(kz['alk_wt_kf'], 0)}, Food & alkoholfrei {pct(kz['food_wt_kf'], 0)}; "
             f"Alkoholanteil am Umsatz Samstag ab 20 Uhr {pp(kz['alk_sa20_pp'])}.",
             f"+5 °C: KF Food & alkoholfrei {pct(kz['food_temp_kf'])}; Top-Gegner: Food & alkoholfrei {pct(kz['food_top_kf'])}.",
             f"Alkoholanteil am Umsatz sinkt ({p(kz['alk_2324'], 1)} → {p(kz['alk_2526'], 1)}, 23/24→25/26, einheitlich brutto); Food "
             f"{p(kz['food_2526'])}, alkoholfrei {p(kz['afrei_2526'])}.",
             f"Warenkorb je 100 Anwesende (25/26): {z(kz['wk_bier_total'])} Bier, {z(kz['wk_soft'])} Süssgetränke, {z(kz['wk_bratwurst'])} "
             f"Bratwürste, {z(kz['wk_nuggets'])} Nugget-Boxen, {z(kz['wk_mineral'])} Mineral, {z(kz['wk_punsch'])} Punsch.",
             f"An Werktagabenden liegt der Ø Bon bei {pct(kz['ktx_wt_bon'])} gegenüber Samstag 17–19.59 Uhr (Phase 1, {kz['ktx_wt_bon_urteil']})."],
            "stark", "Proxy doppelt validiert; Effekte nach Phase-1-Regel belastbar (Intervall ohne 0, stabil über Saisons und Varianten).",
            "hoch", "Sortiment und Angebot je Spieltyp (ohne Preisänderung), Platzierung, Bundles aus bestehenden Preisen",
            "Samstagsspiele ab 20 Uhr, Sonntagnachmittage, Werktagabende, Kälte", "heute nutzbar; Artikel je Spiel würden die Proxy-Ebene ergänzen",
            f"+CHF 1 Ø Bon ≈ {chf_k(kz['fw_bon_chf_10'])} je Saison; +CHF 1 KF ≈ {chf_k(kz['fw_kf_chf_10'])} je Saison (isoliert).",
            _lp(**{"Dynamic Pricing": "Preise fix vor Saison – Sortiment/Angebot statt Preis",
                   "Umsatz ≠ DB": "Margen je Kategorie unbekannt (Food vs. Getränke!)",
                   "Personensegmentierung": "Spieltyp-Ebene, keine Personen"}),
            "Artikel je Spiel (statt Saison), Einstandspreise/Marge je Kategorie, Beteiligungsmodell des Clubs.",
            ["Wie könnten wir bei Samstagsspielen ab 20 Uhr den Food-Umsatz zurückholen, wenn Fans offenbar vorher essen?",
             "Was fehlt am Sonntagnachmittag, damit Fans ähnlich konsumieren wie an einem Samstag um 18 Uhr?",
             "Wie könnten wir den Trend zu Food und alkoholfreien Getränken in grössere Warenkörbe übersetzen?",
             "Was bräuchte ein Werktags-Fan, der spät und hungrig direkt von der Arbeit kommt?",
             "Welche Angebote passen zu kalten Spielen, an denen Food & alkoholfrei weniger läuft?"],
            "Angebotstest an Samstagsspielen ab 20 Uhr bzw. Sonntagnachmittagen (z.B. 3 Spiele mit, 3 ohne); Messgrössen = KF Food & alkoholfrei (Proxy) und Ø Bon gegenüber "
            "Kontexterwartung.",
            "abb_i13_alkohol_kontext.png", "Blätter Alkohol_*, Warenkorb_*, Preis_Menge",
            warnhinweis="Weiche Leitplanke: Ideen, die Alkoholkonsum steigern, brauchen Jugendschutz-, Sicherheits- und Bewilligungs-Check."),
        Chancenfeld(
            6, "Spieltage planbar machen (Frühindikator)", "Planung (Personal, Ware, Kommunikation)",
            f"Verkaufte Einzeltickets 7 Tage vor dem Spiel senken den Prognosefehler der Anwesenden um {z(kz['fi_verb'], 0)} %.",
            [f"Rolling-Origin-Test ({int(kz['fi_n'])} Spiele): mittlerer Fehler {z(kz['fi_mae_ktx'])} Anwesende (nur Kontext) → "
             f"{z(kz['fi_mae_t7'])} (mit T-7). Das 80 %-Band trifft in {p(kz['fi_abdeckung'])} der Spiele.",
             f"Innerhalb der Saison korrelieren T-7-Verkäufe und Anwesende mit r = {dez(kz['fi_r_min'])}–{dez(kz['fi_r_max'])}. "
             "Die No-Show-Quote selbst wird nicht besser vorhersagbar.",
             f"Spieltyp «Spontanpublikum» (spät, wenig; {z(kz['typ_spontan_n'])} Spiele, {p(kz['typ_spontan_abend'])} Abendspiele): "
             f"{p(kz['typ_spontan_ns'], 1)} No-Show gegenüber {p(kz['typ_frueh_ns'], 1)} bei früher, starker Nachfrage – unabhängig "
             "von der Gegnerstärke."],
            "stark", "Retrospektiv mit Rolling Origin getestet (keine Informationen aus der Zukunft); kalibriertes Band.",
            "mittel", "Personal-, Waren- und Kommunikationsplanung (Prognose ist Werkzeug, nicht Massnahme)",
            "alle Spiele", "heute nutzbar (Einzelticket-Export); mit Verkaufsstand inkl. Abos noch besser",
            "Planungsnutzen ohne Kostendaten nicht bezifferbar (Out-of-Stock ist belegt, z.B. 24.10.2024 «zu wenig Bürli»).",
            _lp(**{"Dynamic Pricing": "Spieltypen sind KEIN Input für Preise"}),
            "Verkaufsstand je Tag inkl. Abos, Kosten (Personal, Ware), Out-of-Stock-Log.",
            ["Wie könnten wir die T-7-Prognose für Personal- und Warenplanung nutzen?",
             "Was machen wir bei einem «Spontanpublikum»-Spiel anders (Kommunikation, Angebot, Zweitmarkt)?",
             "Welche Entscheide könnten wir 7 Tage vorher treffen, die heute zu spät fallen?"],
            "Prognose vor den nächsten Heimspielen festhalten und Treffer messen (Band-Trefferquote, Fehler).",
            "abb_i06_fruehindikator.png", "Blätter Fruehindikator*, Spieltypen*"),
        Chancenfeld(
            7, "Wetter und Kiesplatz", "Kontext × Ort (Kiesplatz)",
            f"+5 °C bringen dem Kiesplatz {pct(kz['kies_temp'], 0)} Umsatz je Anwesendem – deutlich mehr als im Stadion ({pct(kz['stadion_temp'])}).",
            [f"Kiesplatz = im Median {p(kz['kies_anteil_median'])} des Catering-Umsatzes je Spiel (im Total enthalten, nie addieren).",
             f"Anstoss: Kiesplatz je Anwesendem am Sonntagnachmittag {pct(kz['kies_nachm'], 0)}, am Werktagabend {pct(kz['kies_wt'], 0)} "
             "gegenüber Samstag 17–19.59 Uhr.",
             f"Kein «Switching»: Kiesplatz und Stadion schwanken gemeinsam (Residuen r = {dez(kz['kies_r_resid'])}). Schlechtes Wetter kostet "
             "draussen Umsatz, ohne dass er drinnen zurückkommt.",
             f"Im ganzen Stadion: +5 °C → KF {pct(kz['ktx_temp_kf'])}, Anwesenheit {pp(kz['ktx_temp_anw'])} (Phase 1)."],
            "stark", "Effekte mit Saison- und Kontextkontrolle, 85 Spiele; Wetter extern (Stationsdaten St. Gallen).",
            "mittel", "Angebot, Öffnungszeiten und kleiner Wetterschutz auf dem Kiesplatz (kein Ausbau); Wetter selbst extern",
            "Spiele mit Kälte/Regen (Winter ≈ 1/3)", "heute nutzbar; Kiesplatz-Besucherzahl fehlt",
            "Wetter ist nicht steuerbar – Hebel nur über Reaktion (Angebot/Öffnung) bei schlechtem Wetter.",
            _lp(**{"Kapazität/Ausbau": "kein Ausbau – nur temporäre Massnahmen"}),
            "Kiesplatz-Besucher/Öffnungszeiten je Spiel, Kassen-Zeitstempel.",
            ["Wie könnte der Kiesplatz auch bei Kälte oder Regen ein Treffpunkt vor dem Spiel bleiben?",
             "Wie könnten wir warme Spätsommer- und Frühlingsabende besser nutzen?",
             "Wie könnte der Kiesplatz Fans früher anziehen (Verbindung zu Chancenfeld 3)?"],
            "Wetterabhängiges Angebot an kalten Spielen gegen kalte Vergleichsspiele (Kiesplatz-Umsatz je Anwesendem vs. Erwartung).",
            "abb_i15_kiesplatz_wetter.png", "Blatt Kiesplatz_Wetter"),
        Chancenfeld(
            8, "Erfolgsmuster wiederholen", "Diagnose (positive Ausreisser)",
            f"{kz['aus_kf_samstag']} von {kz['aus_kf_n']} Spielen mit KF über der Erwartung waren Samstagsspiele "
            f"({kz['aus_kf_samstag18']} davon um 18:00).",
            [f"Über dem 80 %-Band: {int(kz['aus_kf_ueber'])} Spiele, zufällig erwartet {z(kz['aus_kf_erw'], 1)}.",
             "Viele davon ausverkauft, mobiler Verkauf häufiger ausdrücklich im Einsatz.",
             f"Anwesenheit über Erwartung: {kz['aus_anw_montag']} von {kz['aus_anw_n']} Spielen an Montagen – meist Feiertage (Ostermontag); "
             "Feiertage sind kein Modellmerkmal.",
             f"Mehr Gästefans gehen mit einem höheren KF einher: {pct(kz['gaeste_eff'])} je +5 Pp. Gästeanteil (mit Top-Gegner-Kontrolle "
             f"{pct(kz['gaeste_eff2'])}) – der Gästesektor ist eher Umsatzquelle als «Verdünner» des KF."],
            "schwach", "Muster in kleinen Fallzahlen; Hinweise für Hypothesen, keine Belege.",
            "mittel", "Abläufe und Angebot an Spieltagen; Anstosszeiten bestimmt die Liga",
            "Teil der Spiele", "heute nutzbar",
            "Kein eigener Hebel – Lernquelle für die anderen Felder.",
            _lp(),
            "Strukturierte Spieltags-Protokolle (welche Stände, Runner, Aktionen) statt Freitext-Bemerkungen.",
            ["Was machen wir an guten Samstagabenden anders – und lässt es sich auf andere Spiele übertragen?",
             "Welche Abläufe (Runner, Stände, Kiesplatz) waren bei den besten Spielen aktiv?",
             "Wie könnten Feiertage gezielt als Fussball-Familientage genutzt werden?",
             "Wie könnten wir Gästefans (Sektor B4) so bedienen, dass ihr Konsum nicht an Wartezeiten scheitert?"],
            "Spieltags-Checkliste je Spiel erfassen und Abweichungen von der Erwartung danach auswerten.",
            "abb_i16_ausreisser.png", "Blätter Ausreisser_*"),
        Chancenfeld(
            9, "Das Stadion an weiteren Anlässen", "Randfeld (ausserhalb Kernscope)",
            f"Testspiele ({z(kz['rf_test_anlaesse'])} Anlässe seit 2022/23): KF CHF {dez(kz['rf_kf_test'])} inkl. MwSt gegenüber "
            f"CHF {dez(kz['rf_kf_herren_sl'])} in der Herren-Meisterschaft.",
            [f"U21-Spiele: KF CHF {dez(kz['rf_kf_u21'])} inkl. MwSt (wenige Anlässe).",
             f"Events ohne Spiel tragen {p(kz['rf_event_anteil_min'])}–{p(kz['rf_event_anteil_max'])} zum Catering-Umsatz bei "
             "(KF dort wenig aussagekräftig, Zuschauerzahl oft geschätzt).",
             "Frauen-Spiele und Länderspiele sind gemäss Teamentscheid ausgeklammert (D-016/D-036)."],
            "schwach", "Explorativ, kleine Fallzahlen, ausserhalb des Phase-1-Kernscopes.",
            "hoch", "Catering-Angebot und Standbesetzung an Test- und Eventtagen",
            "einzelne Anlässe", "heute nutzbar (Aggregate)",
            "Klein gegenüber Herren-Pflichtspielen.",
            _lp(**{"Personensegmentierung": "nur Anlass-Ebene"}),
            "Verlässliche Zuschauerzahlen bei Events; Ziel des Clubs für Nicht-Pflichtspiel-Tage.",
            ["Welche Catering-Formate passen zu Testspielen und Events im Berit Sitterstadion?",
             "Lohnt sich an kleinen Anlässen ein reduziertes Standangebot?"],
            "Format-Varianten an Test-/Eventtagen vergleichen (KF, Bons je Anwesendem).",
            "abb_i17_randfelder.png", "Blatt F1_Randfelder_Kategorien"),
    ]
    return felder


def als_tabelle(felder: list[Chancenfeld]) -> pd.DataFrame:
    rows = []
    for f in felder:
        d = asdict(f)
        rows.append({"nr": d["nr"], "chancenfeld": d["titel"], "treiber": d["treiber"], "kernzahl": d["kernzahl"],
                     "befund": " | ".join(d["befund"]), "evidenz": d["evidenz"], "evidenz_begruendung": d["evidenz_begruendung"],
                     "steuerbarkeit": d["steuerbarkeit"], "clubhebel": d["clubhebel"], "reichweite": d["reichweite"],
                     "datenreife": d["datenreife"], "hebel_arithmetik": d["hebel_arithmetik"],
                     **{f"leitplanke_{k}": v for k, v in d["leitplanken"].items()}, "datenluecke": d["datenluecke"],
                     "leitfragen": " | ".join(d["leitfragen"]), "pilot_messung": d["pilot_messung"], "warnhinweis": d["warnhinweis"],
                     "quellen": d["quellen"]})
    out = pd.DataFrame(rows)
    out["lesart"] = ("Ordinale Einordnung (keine Punkte, keine Summe). Hebel-Arithmetik = isolierter Rechenwert je Einheit; "
                     "Hebel überlappen und werden nicht addiert.")
    return out


def reto_zu_hoch(kz: dict) -> str:
    """Spanne, um die Retos Hebelwerte über den Daten liegen (KF-Hebel und No-Show-Hebel bei φ = 1), z.B. «23–31 %»."""
    werte = sorted(1 / kz[f] - 1 for f in ("reto_faktor_kf", "reto_faktor_noshow"))
    return f"{werte[0] * 100:.0f}–{p(werte[1])}"


def kernbefunde(kz: dict) -> pd.DataFrame:
    rows = [
        ("Rechengrundlage", f"Retos Faustwerte sind {reto_zu_hoch(kz)} zu hoch",
         f"Es sind {z(kz['b_public_netto_mittel'])} Public-Anwesende je Spiel, nicht 18'000: +CHF 1 KF = {chf_k(kz['fw_kf_chf_10'])} "
         f"je Saison (nicht 342k), 1 Pp. No-Show = {chf_k(kz['fw_noshow_pp_6'])}–{chf_k(kz['fw_noshow_pp_10'])} (nicht 60k).",
         "Blatt Faustwerte"),
        ("Leere Plätze", f"{z(kz['b_noshow_summe'])} leere, vergebene Plätze pro Saison (2025/26)",
         f"Der Zweitmarkt besetzt nur {p(kz['zm_wb_2526'])} davon neu; {p(kz['zm_letzte2'])} der Weiterverkäufe fallen in die letzten 2 Tage.",
         "Blätter Leere_Plaetze_Saison, Zweitmarkt_Saison"),
        ("Fankurve D", f"Tiefste Abo-Anwesenheit: {p(kz['tr_D_abo_lo'])}–{p(kz['tr_D_abo_hi'])}",
         f"D (Näherung 2026/27) gegenüber C {p(kz['tr_C_abo_lo'])}–{p(kz['tr_C_abo_hi'])}; 2025/26 in {kz['zm_d_ohne']} Spielen kein Zweitmarkt in D.",
         "Blatt Tribuene_2627"),
        ("Gruppentickets", f"{p(kz['seg_inhouse10_anteil'])} der Einzelticket-No-Shows aus Inhouse-Grossbestellungen",
         f"No-Show {p(kz['seg_inhouse10_quote_bez'])} (bezahlt) bzw. {p(kz['seg_inhouse10_quote_gratis'])} (gratis) gegenüber "
         f"{p(kz['seg_online24_quote'], 1)} bei Online-Bestellungen mit 2–4 Tickets (21/22–22/23).", "Blatt Einzel_NoShow_Segmente"),
        ("Zeitfenster", f"Tribüne C ist nur {z(kz['vw_C'])} min vor Anpfiff im Stadion",
         f"{p(kz['vw_C_l15'])} kommen in den letzten 15 Minuten; die Toröffnung verschob in D die Ankunft um {z(kz['tor_did'], 0)} min.",
         "Blätter Verweilzeit_Eingang, Toroeffnung_Beleg"),
        ("Kundenfranken", f"KF-Wachstum kommt aus der Kaufhäufigkeit ({pct(kz['kf_entw_freq'], 0)}), nicht aus Preisen",
         f"23/24→25/26: KF {pct(kz['kf_entw_kf'])}, Ø Bon {pct(kz['kf_entw_bon'])}, Preis je Einheit {pct(kz['pm_preis'], 1)}.",
         "Blätter KF_Entwicklung, Preis_Menge"),
        ("Anstosszeit", f"Samstag 17–19.59 Uhr ist der stärkste Konsumtermin: KF Sonntagnachmittag {pct(kz['ktx_nachm_kf'], 0)}, "
         f"Werktagabend {pct(kz['ktx_wt_kf'], 0)}, Samstag ab 20 Uhr {pct(kz['ktx_sa20_kf'], 0)}",
         f"Bei gleichem Kontext; Samstag ab 20 Uhr kippt der Warenkorb zum Getränk (Alkohol-KF {pct(kz['alk_sa20_kf'], 0)}, Food "
         f"{pct(kz['food_sa20_kf'], 0)}; validierter Spiel-Indikator aus dem MwSt-Mix der Kassen). Anstosszeit = Liga/TV (extern).",
         "Blätter K1 (Phase 1), Alkohol_Effekt_Matrix"),
        ("Sortiment", f"Alkoholanteil sinkt: {p(kz['alk_2324'], 1)} → {p(kz['alk_2526'], 1)}",
         f"Einheitlich brutto gerechnet (Phase-1-Korrektur); Food {p(kz['food_2526'])}, alkoholfrei {p(kz['afrei_2526'])} am Umsatz 25/26.",
         "Blätter Warenkorb_Gruppen, C5"),
        ("Mobiler Verkauf", f"Ohne Runner/Bauchläden KF {pct(kz['mob_nein'])} unter Erwartung",
         f"Mit ausdrücklichem Einsatz {pct(kz['mob_ja'])}; Differenz {pct(kz['mob_diff'])} (KI90 {pct(kz['mob_diff_lo'])} bis "
         f"{pct(kz['mob_diff_hi'])}) – an der Nachweisgrenze.", "Blatt Mobiler_Verkauf_Effekt"),
        ("Planung", f"Frühindikator T-7 senkt den Prognosefehler um {z(kz['fi_verb'], 0)} %",
         f"Spieltyp «Spontanpublikum» hat {p(kz['typ_spontan_ns'], 1)} No-Show (früh/stark: {p(kz['typ_frueh_ns'], 1)}).",
         "Blätter Fruehindikator, Spieltypen"),
        ("Wetter", f"Kiesplatz {pct(kz['kies_temp'], 0)} je +5 °C, Stadion {pct(kz['stadion_temp'])}",
         "Keine Verlagerung zwischen Kiesplatz und Stadion – schlechtes Wetter kostet draussen, ohne dass es drinnen zurückkommt.",
         "Blatt Kiesplatz_Wetter"),
        ("Erfolgsmuster", f"{kz['aus_kf_samstag']} von {kz['aus_kf_n']} KF-Spitzenspielen an Samstagen",
         f"{kz['aus_kf_samstag18']} davon um 18:00; Feiertagsmontage über der Anwesenheitserwartung.", "Blätter Ausreisser_*"),
    ]
    return pd.DataFrame(rows, columns=["thema", "befund", "detail", "fundstelle"])


def datenanfragen(kz: dict) -> pd.DataFrame:
    rows = [
        (1, "Payfix-Umsatz je Kasse und Viertelstunde (Meisterschaft 23/24–26/27) + Zuordnung Kasse→Stand→Sektor",
         "Konsumwirkung früherer Ankunft, Pausen-Peak, Wirkung des mobilen Verkaufs je Sektor", "3, 4, 5",
         "Laut Bemerkungen sind Kassen Ständen/Runnern zugeordnet («Runner C = Stand C4», «Kasse 10: Aqua D4») – die Daten existieren vermutlich."),
        (2, "Abo-Anwesenheit je Spiel und Sektor (aggregiert) für 21/22–26/27",
         "Abo-No-Show je Tribüne über alle Saisons statt 4-Spiele-Näherung", "1", "Nur Zählungen, keine Abo-IDs."),
        (3, "Zweitmarkt: angebotene vs. verkaufte Plätze je Spiel/Sektor; wer erhält den Zweitmarkt-Erlös?",
         "Engpass Angebot oder Nachfrage? Ökonomie des Zweitmarkts", "1", ""),
        (4, "Eintritt je Ticket (ZKS) 23/24–26/27 aggregiert nach Kanal, Tarif, Bestellgrösse",
         "Aktueller Stand der Gruppen-/Gratisticket-Nutzung", "2", "Aggregiert, ohne Personendaten."),
        (5, "Artikelauswertung je Spiel (statt Saison) und Einstandspreise/Marge je Kategorie; Beteiligungsmodell",
         "Sortimentswirkung je Spieltyp, Umsatz → DB", "4, 5, 6", "Basis der Artikelspalte bestätigen (brutto/netto)."),
        (6, "Kapazität je Sektor inkl. Sperrungen; Verkaufsstand je Tag inkl. Abos", "Verkaufsquote, echte Ausverkaufskurven", "1, 6", ""),
        (7, "Strukturierte Spieltags-Protokolle (Stände offen, Runner je Sektor, Aktionen, Öffnungszeiten Kiesplatz)",
         "Saubere Messung operativer Hebel statt Freitext-Bemerkungen", "4, 7, 8", ""),
    ]
    return pd.DataFrame(rows, columns=["prioritaet", "datenanfrage", "schaltet_frei", "chancenfelder", "hinweis"])

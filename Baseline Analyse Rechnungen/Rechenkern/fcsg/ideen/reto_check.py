"""Daten-Check der 12 Ideen aus Retos Ideenpapier («Ideenphase Kundenfranken / DB pro Anwesendem», 05.10.2026).

Je Idee: Datenlage heute, Ergebnis eines Vortests mit den echten Daten, korrigierte Rechenbasis, Leitplanken und eine
Einschätzung aus Datensicht. Die Auswahl der Ideen bleibt bei der Gruppe (Simon/Reto).
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import statsmodels.formula.api as smf

from .. import config
from .fmt import chf_k, dez, ki, p, pct, z

ZEIT = " + ".join(config.SLOTS)      # Anstoss-Slot statt Werktag + Abendspiel (ab Run 4, D-048)


def gaeste_test(res: dict) -> pd.DataFrame:
    """Idee 1: Hängt der KF vom Anteil der Gästefans im Nenner (Public Netto) ab?"""
    d = res["modell_daten"]
    x = d[d["hauptstichprobe"] & d["ist_gaeste"].notna() & d["temp_anpfiff_c"].notna() & d["public_netto"].gt(0)].dropna(
        subset=list(config.SLOTS)).copy()
    x["gaeste_anteil"] = x["ist_gaeste"] / x["public_netto"] * 100
    x["log_kf"] = np.log(x["kf_exkl"])
    rows = []
    for name, formel in [("ohne Top-Gegner-Kontrolle", f"log_kf ~ gaeste_anteil + C(saison) + {ZEIT} + temp_anpfiff_c"),
                         ("mit Top-Gegner-Kontrolle", f"log_kf ~ gaeste_anteil + C(saison) + {ZEIT} + temp_anpfiff_c + top_gegner")]:
        fit = smf.ols(formel, data=x.astype({"top_gegner": float})).fit(cov_type="HC3")
        b, se = fit.params["gaeste_anteil"] * 5, fit.bse["gaeste_anteil"] * 5
        rows.append({"spezifikation": name, "spiele": int(fit.nobs), "gaeste_anteil_mittel": x["gaeste_anteil"].mean(),
                     "effekt_pct_je_5pp": (np.exp(b) - 1) * 100, "ki95_unten": (np.exp(b - 1.96 * se) - 1) * 100,
                     "ki95_oben": (np.exp(b + 1.96 * se) - 1) * 100, "p_wert": float(fit.pvalues["gaeste_anteil"])})
    out = pd.DataFrame(rows)
    out["lesart"] = ("Effekt auf den KF, wenn der Gästeanteil am Nenner um 5 Pp. steigt (Meisterschaft ab 22/23). VIP sind im "
                     "Nenner bereits abgezogen (Public Netto = IST − VIP).")
    return out


def tabelle(kz: dict) -> pd.DataFrame:
    fw_np = f"{chf_k(kz['fw_noshow_pp_6'])}–{chf_k(kz['fw_noshow_pp_10'])} je Pp. und Saison (φ 0.6–1.0)"
    rows = [
        (1, "Kennzahlen-Fundament «bereinigter KF»", "Streuung des KF kommt teils aus dem Nenner (VIP, Gäste, Promo).",
         "vorhanden",
         f"VIP sind im Nenner schon abgezogen (Public Netto = IST − VIP). Gästefans machen Ø {z(kz['gaeste_anteil_mittel'], 1)} % des Nenners "
         f"aus; +5 Pp. Gäste gehen mit einem HÖHEREN KF einher ({pct(kz['gaeste_eff'])}, KI95 {ki(kz['gaeste_lo'], kz['gaeste_hi'], 1, ' %')}; "
         f"mit Top-Gegner-Kontrolle {pct(kz['gaeste_eff2'])}; {int(kz['gaeste_n'])} Spiele) – Gäste drücken den KF also nicht. "
         "Definitionen, Summe/Summe und MwSt-Basis sind in Phase 1 festgelegt.",
         "kein eigener CHF-Hebel", "ok", "erledigt – als Fundament nutzen; Gästesektor als Umsatzquelle prüfen",
         "Phase 1, Abschnitt 4; Blatt Reto_Gaeste_Test"),
        (2, "Spieltypen aus der Verkaufskurve", "Spieltyp erklärt No-Show/KF besser als Einzelvariablen; Typ ist früh erkennbar.",
         "vorhanden (Einzeltickets 21/22–24/25 teilweise, 25/26–26/27 vollständig; ohne Abos)",
         f"Fünf regelbasierte Typen (69 Spiele): «Spontanpublikum» {p(kz['typ_spontan_ns'], 1)} No-Show vs. «starke, frühe Nachfrage» "
         f"{p(kz['typ_frueh_ns'], 1)} (p = {dez(kz['typ_p_noshow'], 3)}); Typ hängt NICHT an der Gegnerstärke (p = {dez(kz['typ_p_gegner'], 2)}). "
         "Freies Clustering nur mit 2 Gruppen stabil.",
         "über No-Show-Hebel: " + fw_np, "ok – Typen kein Preis-Input", "weiterverfolgen (vereinfacht, regelbasiert)",
         "Blätter Spieltypen*, Abb. Spieltypen"),
        (3, "No-Show-Frühwarnung mit Zweitmarkt", "Kontext + Verkaufsstand erklären No-Show; Zweitmarkt absorbiert No-Show.",
         "vorhanden",
         f"Einzeltickets bis T-7 senken den Prognosefehler der Anwesenden um {z(kz['fi_verb'], 0)} % (MAE {z(kz['fi_mae_ktx'])} → "
         f"{z(kz['fi_mae_t7'])}; 80 %-Band deckt {p(kz['fi_abdeckung'])} ab). Die No-Show-Quote selbst wird nicht besser vorhergesagt "
         f"({pct(kz['fi_ns_verb'], 0)}). Zweitmarkt 25/26: {z(kz['zm_2526'])} Weiterverkäufe = {p(kz['zm_wb_2526'], 1)} der Abwesenheiten.",
         fw_np, "ok, solange Kommunikation generisch je Sektor", "weiterverfolgen (Planung + Zweitmarkt-Hebel)",
         "Blätter Fruehindikator*, Zweitmarkt*"),
        (4, "Grenz-Anwesender φ", "Zusätzliche Anwesende konsumieren unterdurchschnittlich (φ < 1).", "vorhanden",
         f"Elastizität Umsatz ~ Anwesende {dez(kz['phi'])} (KI95 {dez(kz['phi_lo'])}–{dez(kz['phi_hi'])}); Promo-Anteil ohne messbaren "
         f"KF-Effekt ({pct(kz['promo_eff'])} je +5 Pp.). Kein Beleg für φ < 1 – aber auch kein Kausalnachweis.",
         "Basis φ = 1, Sensitivität 0.6/0.8", "ok", "erledigt – φ-Szenarien im Hebel-Rechner", "Blatt Phi_Evidenz"),
        (5, "Durchsatz-Knick und Standöffnung", "Ab hoher Auslastung sinkt die Kauffrequenz; geschlossene Stände kosten Umsatz.",
         "teilweise (keine Viertelstunden-/Standdaten)",
         f"Kein Knick nachweisbar (alle p ≥ {dez(kz['knick_p_roh_min'], 2)}, drei Knotenpunkte). Ohne (vollständigen) mobilen Verkauf liegt der KF "
         f"{pct(kz['mob_nein'])} unter, mit {pct(kz['mob_ja'])} über der Erwartung (Differenz {pct(kz['mob_diff'])}, KI90 "
         f"{ki(kz['mob_diff_lo'], kz['mob_diff_hi'], 1, ' %')}) – an der Nachweisgrenze (MDE {z(kz['mob_mde'], 1)} %).",
         f"+1 % Frequenz ≈ {chf_k(kz['fw_frequenz_pct_10'])}/Saison", "ok (Wartezeit = Zufriedenheit)",
         "umformulieren: «mobiler Verkauf/Standbesetzung» statt Knick; Pilot", "Blätter Durchsatz_Knick, Mobiler_Verkauf*"),
        (6, "Wetter-Switching Stadion/Kiesplatz", "Regen/Kälte verschieben Konsum vom Kiesplatz ins Stadion.", "vorhanden",
         f"Kein Switching: Kiesplatz und Stadion schwanken gemeinsam (Residuen r = {dez(kz['kies_r_resid'])}). Der Kiesplatz reagiert "
         f"stärker auf Wärme ({pct(kz['kies_temp'])} je +5 °C, Stadion {pct(kz['stadion_temp'])}) und auf den Anstoss (Sonntagnachmittag {pct(kz['kies_nachm'])}, Werktagabend {pct(kz['kies_wt'])} vs. Samstag 17–19.59 Uhr).",
         "keine CHF-Hebelzahl (Wetter extern)", "ok (kein Stadionausbau)", "umformulieren: Wetter-/Kiesplatz-Playbook",
         "Blatt Kiesplatz_Wetter"),
        (7, "KF-Zerlegung Frequenz × Bon (inkl. Pick Up)", "Streuung kommt v.a. aus der Frequenz.", "vorhanden",
         f"Innerhalb der Saison: Ø Bon {p(kz['kfz_bon'])}, Frequenz {p(kz['kfz_freq'])} der KF-Streuung (Phase 1). Entwicklung 23/24→25/26: KF {pct(kz['kf_entw_kf'])} = "
         f"Frequenz {pct(kz['kf_entw_freq'])} × Bon {pct(kz['kf_entw_bon'])}; Preise je Einheit {pct(kz['pm_preis'])}. Pick Up 26/27: "
         f"{p(kz['zw_pickup'], 1)} des Umsatzes.",
         f"+1 % Frequenz ≈ {chf_k(kz['fw_frequenz_pct_10'])}; +CHF 1 Ø Bon ≈ {chf_k(kz['fw_bon_chf_10'])}", "ok",
         "erledigt – Ergebnis nutzen (Frequenz trägt das Wachstum)", "Blätter KF_Entwicklung, Preis_Menge"),
        (8, "Newsvendor-Einsatzplanung", "Planung auf den Durchschnitt erzeugt Out-of-Stock/Verderb.", "fehlt (Kosten, Out-of-Stock)",
         f"Prognose-Baustein vorhanden (T-7, Band deckt {p(kz['fi_abdeckung'])}); Kosten- und Bestandsdaten fehlen. Bemerkungen belegen "
         "Out-of-Stock (z.B. «zu wenig Bürli, Schüblig und Burger», 24.10.2024).",
         "ohne Kosten nicht bezifferbar", "ok", "zurückstellen bis Kostendaten", "Blatt Fruehindikator_Vorhersagen"),
        (9, "Freikonsum-Audit (Gutscheine)", "Freikonsum bindet Durchsatz ohne Erlös.", "vorhanden (Umsatz, keine Mengen)",
         f"Gutscheine/nicht verbucht = {p(kz['zw_gutschein'], 1)} des Umsatzes 25/26 (Retos Abbruchschwelle 0.5 %). Klein, aber "
         "Aktionen sind dokumentiert (Punschgutscheine, Gratisbier).",
         f"1 % Freikonsum ≈ {chf_k(kz['fw_frequenz_pct_10'])} Umsatzäquivalent", "ok", "kleiner Hebel – nur Randnotiz",
         "Blatt Zahlungswege_Ideen"),
        (10, "Tarif-Gesamtwert", "Rangfolge der Tarife nach Gesamtwert ≠ nach Ticketerlös.", "teilweise (Konsum je Tarif fehlt)",
         f"Anwesenheit je Tarif 21/22–22/23: Vollpreis {p(kz['tarif_voll'])}, ermässigt {p(kz['tarif_erm'])}, Gratis/Promo "
         f"{p(kz['tarif_gratis'])}. 10 Pp. Unterschied × KF "
         f"{dez(kz['b_kf_exkl'])} ≈ CHF {dez(0.1 * kz['b_kf_exkl'])} je Ticket – klein gegenüber Preisunterschieden.",
         "zu klein, um Rangfolgen zu kippen", "Achtung: nicht als versteckte Preisdifferenzierung lesen",
         "nicht bauen (bestätigt Retos Einschätzung)", "Phase 1 Blatt B4"),
        (11, "Ankunftskurve und Pausen-Peak", "Früh Ankommende konsumieren mehr; Pausen-Peak begrenzt den Umsatz.",
         "teilweise (Zutritt ja, Catering-Zeitdaten nein)",
         f"Ankunft umfassend ausgewertet: C {z(kz['vw_C'])} min Verweilzeit, {p(kz['vw_C_l15'])} in den letzten 15 min; Toröffnung D "
         f"{z(kz['tor_did'], 0)} min früher. Konsum je Zeitfenster fehlt – Payfix-Daten je Kasse/Viertelstunde existieren "
         "laut Bemerkungen (Kassenzuteilung je Stand/Runner).",
         "nach Datenlieferung", "ok (nur nicht-preisliche Anreize)", "Teil 1 erledigt – Datenanfrage für Teil 2",
         "Blätter Verweilzeit*, Einlass_Spitzen"),
        (12, "Merchandise-Konversion", "Merch hat Gelegenheitsfenster nach Kontext.", "fehlt (keine Merch-Daten)",
         "Keine Merchandise-Daten geliefert. Hinweis: Fanartikel wurden an zwei Spielen 2025/26 über Catering-Kassen verkauft "
         "(«Cup T-Shirt Verkauf»).", "keine Basis", "ok (nur Stadion-Shop aggregiert)", "nicht möglich ohne Lieferung",
         "Phase 1 Quelleninventar"),
    ]
    return pd.DataFrame(rows, columns=["nr", "idee_reto", "hypothese", "datenlage_heute", "vortest_mit_daten",
                                       "korrigierte_rechenbasis", "leitplanken", "einschaetzung_datensicht", "fundstelle"])

"""Ideen-Stufe: alle Analysen rechnen, Kennzahlen bündeln, Chancenfelder/Reto-Check ableiten und Ausgaben schreiben.

Die Phase-1-Objekte (r, m, res) werden nur gelesen; ein Fingerabdruck-Test (qa_ideen) stellt sicher, dass sie nach der
Ideen-Stufe unverändert sind.
"""
from __future__ import annotations

import time
from pathlib import Path

import numpy as np
import pandas as pd

from ..log import logger
from . import absatz, ausreisser, basis, chancen, konsum, noshow, randfelder, reto_check, zeitfenster


def berechne(r, m, res: dict) -> dict[str, pd.DataFrame]:
    t0 = time.time()
    e: dict[str, pd.DataFrame] = {}
    e.update(basis.rechne(res))
    e.update(noshow.rechne(r, m, res))
    e.update(absatz.rechne(r, m, res))
    e.update(zeitfenster.rechne(r, m, res))
    e.update(konsum.rechne(r, m, res, e["basis_saison"], e["absatz_merkmale"]))
    e.update(ausreisser.ausreisser(res, m.dim_match_context, m, e["alkohol_je_spiel"], e["spieltypen_zuordnung"]))
    e.update(randfelder.rechne(r))
    e["reto_gaeste_test"] = reto_check.gaeste_test(res)
    logger.info("Ideen-Grundlage: %s Tabellen berechnet (%.0f s)", len(e), time.time() - t0)
    return e


# --------------------------------------------------------------------------------------------
# Kennzahlen für Texte (eine Stelle, damit Dossier, Excel und Markdown dieselben Werte nennen)
# --------------------------------------------------------------------------------------------
def _zeile(df: pd.DataFrame, **bed) -> pd.Series:
    x = df
    for k_, v in bed.items():
        x = x[x[k_] == v]
    return x.iloc[0] if len(x) else pd.Series(dtype=object)


def kennzahlen(e: dict[str, pd.DataFrame], res: dict) -> dict:
    kz: dict = {}
    b = e["basis_saison"].set_index("basis")
    r26 = b.loc[basis.REFERENZ_SAISON]
    kz.update({f"b_{k_}": r26[k_] for k_ in ("spiele", "soll_mittel", "ist_mittel", "public_netto_mittel", "public_netto_summe",
                                              "umsatz_exkl", "umsatz_inkl", "kf_exkl", "kf_inkl", "bons_pro_anwesende", "bon_exkl",
                                              "noshow_quote", "noshow_summe", "noshow_summe_ticketbasiert", "bons_mittel")})
    fw = e["faustwerte"]
    fw26 = fw[fw["basis"] == basis.REFERENZ_SAISON]
    for code in basis.HEBEL:
        for phi in (0.6, 0.8, 1.0):
            z = fw26[(fw26["hebel_code"] == code) & ((fw26["phi"] == phi) | fw26["phi"].isna())]
            if len(z):
                kz[f"fw_{code}_{int(phi * 10)}"] = z["chf_pro_saison"].iloc[0]
                kz[f"fw_{code}_{int(phi * 10)}_spiel"] = z["chf_pro_spiel"].iloc[0]
    kz["fw_noshow_anw_spiel"] = fw26.loc[fw26["hebel_code"] == "noshow_pp", "zusatz_menge_je_spiel"].iloc[0]
    rv = e["reto_faustwerte"].set_index("kennzahl")
    kz["reto_faktor_anw"] = rv.iloc[0]["faktor_daten_zu_reto"]
    kz["reto_faktor_kf"] = rv.loc["+CHF 1 Kundenfranken je Saison (CHF)", "faktor_daten_zu_reto"]
    kz["reto_faktor_noshow"] = rv.loc["1 Pp. No-Show: CHF je Saison (φ = 1)", "faktor_daten_zu_reto"]
    nk = e["noshow_kosten"]
    nk26 = nk[nk["basis"] == basis.REFERENZ_SAISON].set_index("spieltyp")
    kz["leer_ausv"], kz["leer_offen"] = nk26.loc["ausverkauft", "leere_bezahlte_plaetze_je_saison"], nk26.loc["nicht ausverkauft", "leere_bezahlte_plaetze_je_saison"]
    kz["ns_ausv"], kz["ns_offen"] = nk26.loc["ausverkauft", "noshow_quote"], nk26.loc["nicht ausverkauft", "noshow_quote"]
    kz["spiele_ausv"], kz["spiele_offen"] = nk26.loc["ausverkauft", "spiele_je_saison"], nk26.loc["nicht ausverkauft", "spiele_je_saison"]

    zm = e["zweitmarkt_saison"].set_index("saison")
    kz["zm_2526"], kz["zm_wb_2526"] = zm.loc["2025/26", "zweitmarkt"], zm.loc["2025/26", "wiederbesetzung_untergrenze"]
    kz["zm_wb_2627"] = zm.loc["2026/27", "wiederbesetzung_untergrenze"] if "2026/27" in zm.index else np.nan
    kz["zm_d_ohne"] = int(zm.loc["2025/26", "spiele_ohne_zweitmarkt_D"])
    for tr in "ABCD":
        kz[f"zm_anteil_{tr}"] = zm.loc["2025/26", f"anteil_tribuene_{tr}"]
    zv = e["zweitmarkt_vorlauf"].iloc[0]
    kz["zm_letzte2"], kz["zm_spieltag"] = zv["anteil_letzte_2_tage"], zv["anteil_am_spieltag"]
    zp = e["zweitmarkt_preis"]
    kz["zm_aufpreis"] = float(np.average(zp["aufpreis_pct"], weights=zp["zweitmarkt_tickets"])) if len(zp) else np.nan

    t = e["tribuene_2627"].set_index("tribuene")
    for tr in ("B", "C", "D"):
        kz[f"tr_{tr}_quote"] = t.loc[tr, "scans_je_platz"]
        kz[f"tr_{tr}_abo_lo"] = min(t.loc[tr, "abo_anwesenheit_bei_r_unten"], t.loc[tr, "abo_anwesenheit_bei_r_oben"])
        kz[f"tr_{tr}_abo_hi"] = max(t.loc[tr, "abo_anwesenheit_bei_r_unten"], t.loc[tr, "abo_anwesenheit_bei_r_oben"])
        kz[f"tr_{tr}_leer_spiel"] = t.loc[tr, "leere_plaetze_je_spiel"]
        kz[f"tr_{tr}_einzel_uefa"] = t.loc[tr, "einzel_anwesenheit_uefa"]

    seg = e["einzel_noshow_segmente"]
    inhouse10 = seg[(seg["kanal"] == "Inhouse") & (seg["tickets_pro_bestellung"] == "10+")]
    kz["seg_inhouse10_anteil"] = inhouse10["anteil_an_allen_noshows"].sum()
    kz["seg_inhouse10_quote_bez"] = _zeile(inhouse10, preis="bezahlt").get("noshow_quote", np.nan)
    kz["seg_inhouse10_quote_gratis"] = _zeile(inhouse10, preis="gratis").get("noshow_quote", np.nan)
    kz["seg_inhouse10_tickets_spiel"] = inhouse10["tickets"].sum() / inhouse10["spiele"].max()
    kz["seg_inhouse10_noshows_spiel"] = inhouse10["noshows"].sum() / inhouse10["spiele"].max()
    kz["seg_online24_quote"] = _zeile(seg, kanal="Online-Shop", preis="bezahlt", tickets_pro_bestellung="2–4").get("noshow_quote", np.nan)
    kz["seg_zks_anwesenheit"] = noshow.einzelticket_anwesenheit_zks(res)

    lk = e["leere_plaetze_kontext"].set_index(["merkmal", "auspraegung"])["noshow_quote"]
    for key, idx in {"ns_werktag": ("Wochentag", "Wochentag (Mo–Fr)"), "ns_wochenende": ("Wochentag", "Wochenende (Sa/So)"),
                     "ns_abend": ("Anstosszeit", "Abend (ab 20 Uhr)"), "ns_nachmittag": ("Anstosszeit", "Nachmittag (<17 Uhr)"),
                     "ns_winter": ("Winter (Nov–Feb)", "ja"), "ns_nichtwinter": ("Winter (Nov–Feb)", "nein")}.items():
        kz[key] = lk.get(idx, np.nan)

    st = e["spieltypen"].set_index("spieltyp")
    kz["typ_spontan_ns"] = st.loc[absatz.TYPEN[(False, True)], "noshow_quote"] if absatz.TYPEN[(False, True)] in st.index else np.nan
    kz["typ_spontan_n"] = st.loc[absatz.TYPEN[(False, True)], "spiele"] if absatz.TYPEN[(False, True)] in st.index else np.nan
    kz["typ_spontan_abend"] = st.loc[absatz.TYPEN[(False, True)], "anteil_abendspiel"] if absatz.TYPEN[(False, True)] in st.index else np.nan
    kz["typ_frueh_ns"] = st.loc[absatz.TYPEN[(True, False)], "noshow_quote"] if absatz.TYPEN[(True, False)] in st.index else np.nan
    tt = e["spieltypen_tests"].set_index("test")["p_wert"]
    kz["typ_p_gegner"] = tt.iloc[0]
    kz["typ_p_noshow"] = tt.iloc[-1]
    fi = _zeile(e["fruehindikator"], zielgroesse="IST (Anwesende)", testspiele="alle Testspiele")
    kz["fi_mae_ktx"], kz["fi_mae_t7"], kz["fi_verb"] = fi["mae_kontext"], fi["mae_kontext_plus_t7"], fi["verbesserung_gegen_kontext_pct"]
    kz["fi_abdeckung"], kz["fi_n"] = fi["abdeckung_pi80"], fi["n"]
    fn = _zeile(e["fruehindikator"], zielgroesse="No-Show-Quote (nur ticketbasiertes SOLL)", testspiele="alle Testspiele")
    kz["fi_ns_verb"] = fn.get("verbesserung_gegen_kontext_pct", np.nan)
    fk = e["fruehindikator_korrelation"]
    kz["fi_r_min"], kz["fi_r_max"] = fk["r_t7_ist"].min(), fk["r_t7_ist"].max()

    pe = e["erloes_einzel_saison"].set_index("saison")
    kz["erloes_einzel_2526"] = pe.loc["2025/26", "erloes_einzel_chf"] if "2025/26" in pe.index else np.nan
    pa = e["preis_abo_tribuene"]
    kz["erloes_abo_2627"] = pa["erloes_chf"].sum()

    v = e["verweilzeit_eingang"].set_index("sektor")
    for s_, key in (("A", "A"), ("B", "B"), ("C", "C"), ("D", "D")):
        kz[f"vw_{key}"] = v.loc[s_, "verweil_mittel"]
        kz[f"vw_{key}_l15"] = v.loc[s_, "anteil_letzte_15_min"]
        kz[f"vw_{key}_besucher"] = v.loc[s_, "besucher_je_spiel"]
        kz[f"vw_{key}_minuten"] = v.loc[s_, "besucher_minuten_je_spiel"]
    kz["vw_C_l15_personen"] = v.loc["C", "besucher_letzte_15_min_je_spiel"]
    vk = e["verweilzeit_kontext"].set_index(["merkmal", "auspraegung"])
    kz["vw_werktag_abw"] = vk.loc[("Wochentag", "Wochentag (Mo–Fr)"), "abweichung_vom_saisonmittel_min"]
    kz["vw_werktag_l15"] = vk.loc[("Wochentag", "Wochentag (Mo–Fr)"), "anteil_letzte_15_min"]
    kz["vw_wochenende_l15"] = vk.loc[("Wochentag", "Wochenende (Sa/So)"), "anteil_letzte_15_min"]
    es = e["einlass_spitzen"].set_index("sektor")
    kz["einlass_C"], kz["einlass_D"] = es.loc["C", "auslastung_spitze"], es.loc["D", "auslastung_spitze"]
    kz["einlass_ABC_max"] = es.loc[["A", "B", "C"], "auslastung_spitze"].max()
    kz["einlass_ABC_min"] = es.loc[["A", "B", "C"], "auslastung_spitze"].min()
    did = e["toroeffnung_beleg"].set_index("zielgroesse")
    kz["tor_did"] = did.loc["Median Ankunft, min vor Anpfiff", "did_effekt"]
    kz["tor_did_lo"], kz["tor_did_hi"] = did.loc["Median Ankunft, min vor Anpfiff", "ki95_unten"], did.loc["Median Ankunft, min vor Anpfiff", "ki95_oben"]

    ke = e["kf_entwicklung"]
    ges = ke[ke["saison"].str.contains("→")].iloc[0]
    kz["kf_entw_kf"], kz["kf_entw_freq"], kz["kf_entw_bon"] = ges["veraenderung_kf_pct"], ges["veraenderung_frequenz_pct"], ges["veraenderung_bon_pct"]
    jb = e["warenkorb_je_bon"].set_index("saison")
    kz["einh_bon_2324"], kz["einh_bon_2526"] = jb.loc["2023/24", "einheiten_je_bon"], jb.loc["2025/26", "einheiten_je_bon"]
    kz["einh_anw_2324"], kz["einh_anw_2526"] = jb.loc["2023/24", "einheiten_je_anwesenden"], jb.loc["2025/26", "einheiten_je_anwesenden"]
    pm = e["preis_menge"]
    lang = pm[(pm["von"] == "2023/24") & (pm["bis"] == "2025/26")].iloc[0]
    kz["pm_preis"], kz["pm_menge"], kz["pm_sortiment"] = lang["preisindex_fisher_pct"], lang["mengenindex_fisher_pct"], lang["sortimentswechsel_pct"]
    wk = e["warenkorb_artikel"].set_index("name")
    for name, key in (("Bier 4dl.", "bier"), ("Klosterbräu 4dl.", "kloster"), ("Bratwurst", "bratwurst"), ("Süssgetränk 4dl", "soft"),
                      ("Poulet-Nugget Box", "nuggets"), ("Mineral 4dl", "mineral"), ("Punsch 2dl", "punsch")):
        kz[f"wk_{key}"] = wk.loc[name, "2025/26"] if name in wk.index and "2025/26" in wk.columns else np.nan
    kz["wk_bier_total"] = np.nansum([kz["wk_bier"], kz["wk_kloster"]])
    ag = res["artikel_gruppen"].set_index(["saison", "name"])["anteil"]
    kz["alk_2324"], kz["alk_2526"] = ag.get(("2023/24", "Alkoholische Getränke")), ag.get(("2025/26", "Alkoholische Getränke"))
    kz["food_2526"], kz["afrei_2526"] = ag.get(("2025/26", "Food")), ag.get(("2025/26", "Alk.-freie Getränke"))
    av = e["alkohol_validierung"]
    kz["alk_val_maxdiff"] = av["differenz_pp"].abs().max()
    kz["alk_val_r"] = av["r_innerhalb_saison_mit_kiesplatz"].iloc[0]
    am = e["alkohol_effekt_matrix"].set_index(["zielgroesse", "variable"])
    abend, werktag, temp, top = ("Abendspiel (Anpfiff ab 20 Uhr)", "Werktag (Mo–Fr) statt Wochenende", "Temperatur bei Anpfiff",
                                 "Top-Gegner (FCB, YB, FCZ)")
    for key, (ziel, var) in {"alk_abend_pp": ("Alkoholanteil am Umsatz (Normalsatz-Proxy)", abend),
                             "alk_abend_kf": ("KF Alkohol (exkl. MwSt)", abend), "food_abend_kf": ("KF Food & alkoholfrei (exkl. MwSt)", abend),
                             "alk_werktag_kf": ("KF Alkohol (exkl. MwSt)", werktag), "food_temp_kf": ("KF Food & alkoholfrei (exkl. MwSt)", temp),
                             "food_top_kf": ("KF Food & alkoholfrei (exkl. MwSt)", top)}.items():
        kz[key] = am.loc[(ziel, var), "effekt"] if (ziel, var) in am.index else np.nan
        kz[key + "_urteil"] = am.loc[(ziel, var), "beurteilung"] if (ziel, var) in am.index else ""
    dk = e["durchsatz_knick"]
    kz["knick_p_min"] = dk["p_bonferroni_3_knoten"].min()
    kz["knick_p_roh_min"] = dk["p_wild_bootstrap"].min()
    kz["knick_elast_bons"] = dk.loc[dk["zielgroesse"].str.startswith("Bons"), "elastizitaet_unter_knoten"].median()
    mv = e["mobiler_verkauf_effekt"]
    mvk = mv[mv["zielgroesse"] == "Kundenfranken exkl. MwSt"].set_index("gruppe")
    kz["mob_nein"] = mvk.loc["ganz/teilweise nicht im Einsatz", "abweichung_von_erwartung_pct"]
    kz["mob_ja"] = mvk.loc["im Einsatz", "abweichung_von_erwartung_pct"]
    kz["mob_diff"] = mvk.loc["Differenz (nicht im Einsatz − im Einsatz)", "abweichung_von_erwartung_pct"]
    kz["mob_diff_lo"] = mvk.loc["Differenz (nicht im Einsatz − im Einsatz)", "ki90_unten"]
    kz["mob_diff_hi"] = mvk.loc["Differenz (nicht im Einsatz − im Einsatz)", "ki90_oben"]
    kz["mob_mde"] = mvk.loc["Differenz (nicht im Einsatz − im Einsatz)", "mde_80pct_power_pct"]
    kz["mob_n_nein"], kz["mob_n_ja"] = mvk.loc["ganz/teilweise nicht im Einsatz", "spiele"], mvk.loc["im Einsatz", "spiele"]
    zw = e["zahlungswege_ideen"]
    zw26 = zw[zw["saison"] == "2025/26"].set_index("kanal")["anteil"]
    kz["zw_justeat"], kz["zw_gutschein"], kz["zw_extern"] = zw26.get("Just Eat (App)"), zw26.get("Gutscheine/nicht verbucht"), zw26.get("Extern (Partner-Stände)")
    zw27 = zw[zw["saison"] == "2026/27"].set_index("kanal")["anteil"]
    kz["zw_pickup"] = zw27.get("Pick Up (App)", np.nan)
    kw = e["kiesplatz_wetter"].set_index(["zielgroesse", "variable"])["effekt"]
    kz["kies_temp"] = kw.get(("Kiesplatz CHF je Anwesendem (brutto)", "+5 °C"))
    kz["kies_abend"] = kw.get(("Kiesplatz CHF je Anwesendem (brutto)", "Abendspiel"))
    kz["stadion_temp"] = kw.get(("Stadion (ohne Kiesplatz) CHF je Anwesendem", "+5 °C"))
    kz["kies_r_resid"] = e["kiesplatz_wetter"]["residuen_korrelation_kies_stadion"].iloc[0]
    kj = e["kiesplatz_je_spiel_ideen"]
    kz["kies_anteil_median"] = kj["anteil_kies"].median()
    ph = e["phi_evidenz"]
    el = ph[ph["variante"] == "SL 21/22–26/27 mit Saison-Effekten"].iloc[0]
    kz["phi"], kz["phi_lo"], kz["phi_hi"] = el["elastizitaet"], el["ki95_unten"], el["ki95_oben"]
    pr = ph[ph["art"].str.startswith("KF und Anteil Gratis")].iloc[0]
    kz["promo_eff"], kz["promo_lo"], kz["promo_hi"] = pr["effekt_pct"], pr["ki95_unten"], pr["ki95_oben"]

    az = e["ausreisser_zaehlung"].set_index(["zielgroesse", "lage"])
    kz["aus_kf_ueber"] = az.loc[("Kundenfranken exkl. MwSt", "über Erwartung"), "spiele_beobachtet"]
    kz["aus_kf_erw"] = az.loc[("Kundenfranken exkl. MwSt", "über Erwartung"), "spiele_erwartet_zufall"]
    ap = e["ausreisser_positiv"]
    apk = ap[ap["zielgroesse"] == "Kundenfranken exkl. MwSt"]
    kz["aus_kf_samstag"] = int((apk["wochentag"] == "Samstag").sum())
    kz["aus_kf_samstag18"] = int(((apk["wochentag"] == "Samstag") & (apk["anpfiff"] == "18:00")).sum())
    kz["aus_kf_n"] = len(apk)
    apa = ap[ap["zielgroesse"] == "Anwesenheitsquote (IST/SOLL)"]
    kz["aus_anw_montag"] = int((apa["wochentag"] == "Montag").sum())
    kz["aus_anw_n"] = len(apa)

    # Randfelder ohne Frauen und Länderspiele (D-016/D-036)
    rk = e["randfelder_kategorien"]

    def _kf(kat):
        g = rk[rk["kategorie"] == kat]
        return (g["umsatz_inkl"].sum() / g["public_anwesende"].sum()) if len(g) and g["public_anwesende"].sum() > 0 else np.nan

    kz["rf_kf_herren_sl"] = _kf("Herren Meisterschaft")
    kz["rf_kf_test"] = _kf("Testspiele")
    kz["rf_kf_u21"] = _kf("U21")
    ev = rk[rk["kategorie"] == "Events ohne Spiel"]["anteil_am_catering_umsatz"]
    kz["rf_event_anteil_min"], kz["rf_event_anteil_max"] = ev.min(), ev.max()
    kz["rf_test_anlaesse"] = int(rk.loc[rk["kategorie"] == "Testspiele", "anlaesse"].sum())

    mx = res["kontext_effekt_matrix"].set_index(["zielgroesse", "variable"])["effekt"]
    kz["ktx_abend_anw"] = mx.get(("Anwesenheitsquote (IST/SOLL)", abend))
    kz["ktx_abend_kf"] = mx.get(("Kundenfranken exkl. MwSt", abend))
    kz["ktx_temp_kf"] = mx.get(("Kundenfranken exkl. MwSt", temp))
    kz["ktx_temp_anw"] = mx.get(("Anwesenheitsquote (IST/SOLL)", temp))
    kz["ktx_top_anw"] = mx.get(("Anwesenheitsquote (IST/SOLL)", top))
    kz["ktx_werktag_bon"] = mx.get(("Ø Bon exkl. MwSt", werktag))
    seg_t = res["eintritt_segmente"].set_index(["merkmal", "auspraegung"])["eintrittsquote"]
    kz["tarif_voll"] = seg_t.get(("Tarifgruppe", "Vollpreis"))
    kz["tarif_erm"] = seg_t.get(("Tarifgruppe", "Ermässigt"))
    kz["tarif_gratis"] = seg_t.get(("Tarifgruppe", "Gratis/Promo"))
    zr = res["kf_zerlegung"]
    zr = zr[(zr["scope"] == "SL ab 2023/24") & (zr["variante"] == "Streuung innerhalb der Saison")].iloc[0]
    kz["kfz_bon"], kz["kfz_freq"] = zr["anteil_bon"], zr["anteil_bons_pro_anwesende"]
    gt = e["reto_gaeste_test"].iloc[0]
    kz["gaeste_eff"], kz["gaeste_lo"], kz["gaeste_hi"] = gt["effekt_pct_je_5pp"], gt["ki95_unten"], gt["ki95_oben"]
    gt2 = e["reto_gaeste_test"].iloc[1]
    kz["gaeste_eff2"], kz["gaeste_lo2"], kz["gaeste_hi2"] = gt2["effekt_pct_je_5pp"], gt2["ki95_unten"], gt2["ki95_oben"]
    kz["gaeste_n"] = gt["spiele"]
    kz["gaeste_anteil_mittel"] = gt["gaeste_anteil_mittel"]
    return kz


def erstelle(r, m, res: dict, ziel: Path, mit_grafiken: bool = True, pdf: bool = True) -> dict:
    """Rechnet die Ideen-Grundlage und schreibt HTML, PDF (falls Chrome/Edge vorhanden), Excel, Markdown und Grafiken."""
    from . import qa_ideen
    from .bericht import excel_rechner, grafiken, html, notion

    fingerprint_vorher = qa_ideen.fingerabdruck(res)
    e = berechne(r, m, res)
    kz = kennzahlen(e, res)
    kz["datenstand"] = f"{m.datenstand:%d.%m.%Y}"
    e["phase1_aenderungen"] = res.get("aenderungsprotokoll")
    felder = chancen.chancenfelder(kz)
    e["chancenfelder"] = chancen.als_tabelle(felder)
    e["kernbefunde"] = chancen.kernbefunde(kz)
    e["reto_ideen_check"] = reto_check.tabelle(kz)
    e["datenanfragen"] = chancen.datenanfragen(kz)
    ziel.mkdir(parents=True, exist_ok=True)
    abb = grafiken.erstelle(e, kz, res, ziel / "Abbildungen") if mit_grafiken else pd.DataFrame(columns=["datei", "titel", "aussage"])
    e["grafiken_ideen"] = abb
    qa = qa_ideen.pruefe(e, felder, res, fingerprint_vorher)
    xlsx = ziel / "Ideen_Grundlage_FCSG.xlsx"
    e["qa_ideen"] = qa
    excel_rechner.schreibe(xlsx, e, kz)
    formeln = excel_rechner.pruefe_formeln(xlsx, e)
    qa = pd.concat([qa, pd.DataFrame([{"test": "Hebel-Rechner: Excel-Formeln = Python (hebel_szenario) für alle Hebel",
                                        "bestanden": bool(formeln["gleich"].all()),
                                        "detail": f"{int(formeln['gleich'].sum())} von {len(formeln)} Hebeln gleich"}])], ignore_index=True)
    # Zweimal schreiben: der erste Durchgang liefert die Dateiprüfungen (HTML offline, Markdown), der zweite schreibt
    # Excel, HTML und Markdown mit der vollständigen QA-Tabelle; die Dateiprüfungen laufen auf den endgültigen Dateien.
    for _ in range(2):
        e["qa_ideen"] = qa
        excel_rechner.schreibe(xlsx, e, kz)
        seite = html.schreibe(ziel / "Ideen_Grundlage_FCSG.html", e, kz, felder, ziel / "Abbildungen")
        md = notion.schreibe(ziel / "Ideen_Grundlage_FCSG.md", e, kz, felder)
        dateien = qa_ideen.pruefe_dateien(seite, md)
        qa = pd.concat([qa[~qa["test"].isin(dateien["test"])], dateien], ignore_index=True)
    pdf_pfad = html.als_pdf(seite, ziel / "Ideen_Grundlage_FCSG.pdf") if pdf else None
    qa.to_csv(ziel / "QA_Ideen_Grundlage.csv", index=False, encoding="utf-8-sig")
    logger.info("Ideen-Grundlage geschrieben: %s (QA: %s von %s bestanden%s)", ziel, int(qa["bestanden"].sum()), len(qa),
                "; PDF erstellt" if pdf_pfad else "; kein PDF (Chrome/Edge nicht gefunden)")
    return {"qa": qa, "pdf": pdf_pfad, "tabellen": len(e), "kennzahlen": kz, "ergebnisse": e, "chancenfelder": felder}

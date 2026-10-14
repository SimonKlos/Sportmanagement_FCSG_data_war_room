"""mart_match: ein Heimspiel pro Zeile, Inputverfügbarkeit und Zielgrössen explizit markiert (Auftrag 3)."""
from __future__ import annotations

import pandas as pd

from . import config
from .datamodel import Modell
from .utils import als_bool


def baue_mart(m: Modell, res: dict[str, pd.DataFrame]) -> pd.DataFrame:
    k = res["spiel_kpi"]
    ctx = m.dim_match_context
    ank = res["ankunft_je_spiel"]
    ab = res["absatz_je_spiel"]
    zks = res["zks_spiele"]
    karte = res["diagnosekarte"]

    cols_k = ["match_id", "datum", "saison", "wettbewerb", "spielstatus", "gegner_anzeige", "top_gegner", "anpfiff",
              "wochentag", "anpfiff_slot", "soll", "ist", "ist_vip", "ist_gaeste", "zweitmarkt", "noshow_quote",
              "anwesenheitsquote", "ausverkauft", "soll_definition", "ist_qualitaet", "public_netto", "transaktionen",
              "umsatz_inkl", "umsatz_exkl", "kf_inkl", "kf_exkl", "bons_pro_anwesende", "bon_exkl", "besucher_scans",
              "abweichung_scans_ist", "einzeltickets", "einzeltickets_vollstaendig"]
    mart = k[cols_k].copy()
    mart = mart.merge(ctx[["match_id", "in_kontexttabelle", "rang_gegner", "ppg_gegner_gestuetzt", "temp_anpfiff_c",
                           "niederschlag_anreise_mm", "regen_anreise", "schulferien", "free_tv_srf"]], on="match_id", how="left")
    mart = mart.merge(ank[["match_id", "median_min_vor_anpfiff", "anteil_ab_45_min",
                           "anteil_letzte_15_min_inkl_nach_anpfiff"]], on="match_id", how="left")
    mart = mart.merge(ab[["match_id", "anteil_am_spieltag", "t50_tage"]], on="match_id", how="left")
    mart = mart.merge(zks[["match_id", "eintrittsquote_einzel", "zks_valide"]], on="match_id", how="left")
    kcols = [c for c in ["match_id", "erwartet_kf_exkl", "z_wert_kf_exkl", "referenzluecke_konsum_chf",
                         "erwartet_anwesenheitsquote", "z_wert_anwesenheitsquote", "einordnung_konsum",
                         "einordnung_anwesenheit", "mechanismen"] if c in karte.columns]
    mart = mart.merge(karte[kcols], on="match_id", how="left")

    # Verfügbarkeit je Modul (Abdeckung statt fiktivem Gesamtdatensatz)
    mart["hat_anwesenheit"] = mart["soll"].notna() & mart["ist"].notna()
    mart["hat_catering_umsatz"] = mart["umsatz_inkl"].notna() & mart["public_netto"].notna()
    mart["hat_bons"] = mart["transaktionen"].notna()
    mart["hat_zutritt_vollstaendig"] = mart["median_min_vor_anpfiff"].notna()
    mart["hat_einzeltickets_vollstaendig"] = als_bool(mart["einzeltickets_vollstaendig"])
    mart["hat_eintritt_zks_valide"] = als_bool(mart["zks_valide"])
    mart["hat_kontext_gruppe"] = als_bool(mart["in_kontexttabelle"])
    mart["im_kontextmodell"] = mart["erwartet_kf_exkl"].notna() | mart["erwartet_anwesenheitsquote"].notna()
    mart["kernscope"] = mart["wettbewerb"].isin(config.KERN_WETTBEWERBE) & (mart["spielstatus"] == "gespielt")
    return mart.sort_values("datum").reset_index(drop=True)

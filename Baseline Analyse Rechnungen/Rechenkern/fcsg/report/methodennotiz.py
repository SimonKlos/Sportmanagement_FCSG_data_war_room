"""Methodennotiz (Markdown, Notion-tauglich) – alle Zahlen werden aus den aktuellen Ergebnissen eingesetzt."""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from .. import config


def _z(x, d=0, tausender=True) -> str:
    if x is None or (isinstance(x, float) and np.isnan(x)):
        return "–"
    s = f"{x:,.{d}f}" if tausender else f"{x:.{d}f}"
    return s.replace(",", "'")


def _p(x, d=1) -> str:
    return "–" if x is None or pd.isna(x) else f"{x * 100:.{d}f} %"


def _tab(df: pd.DataFrame, spalten: dict[str, tuple[str, str]]) -> str:
    """Kleine Markdown-Tabelle. spalten: Spalte -> (Überschrift, Format: text|z0|z2|p1|d1)."""
    kopf = "| " + " | ".join(h for h, _ in spalten.values()) + " |"
    trenn = "|" + "|".join("---" for _ in spalten) + "|"
    zeilen = []
    for _, r in df.iterrows():
        werte = []
        for c, (_, f) in spalten.items():
            v = r.get(c)
            if f == "z0":
                werte.append(_z(v, 0))
            elif f == "z2":
                werte.append(_z(v, 2))
            elif f == "p1":
                werte.append(_p(v, 1))
            elif f == "d1":
                werte.append("–" if pd.isna(v) else f"{v:+.1f}")
            else:
                werte.append("" if v is None or (isinstance(v, float) and np.isnan(v)) else str(v).replace("\n", " ").replace("|", "/"))
        zeilen.append("| " + " | ".join(werte) + " |")
    return "\n".join([kopf, trenn, *zeilen])


def schreibe(pfad: Path, res: dict[str, pd.DataFrame], info: dict) -> None:
    pfad.write_text(text(res, info), encoding="utf-8")


def text(res: dict[str, pd.DataFrame], info: dict) -> str:
    s = res["saison_kpi"]
    sl = s[s["wettbewerbe"] == "SL"].set_index("saison")
    alle = s[s["wettbewerbe"] == "SL+Cup+UEFA"].set_index("saison")
    mart = res["mart_match"]
    kern = mart[mart["kernscope"]]
    ab = res["abdeckung"]
    gs = res["gemeinsame_stichproben"]
    korr = res["korrekturen"]
    dq = res["datenqualitaet"]
    tests = res["importtests"]
    mx = res["kontext_effekt_matrix"]
    mg = res["modellguete"]
    karte = res["diagnosekarte"]
    muster = res["diagnose_muster"]
    typ = res["tickettyp_noshow"]
    typ = typ[typ["scope"] == "alle validen Spiele"].set_index("saison")
    seg = res["eintritt_segmente"].set_index(["merkmal", "auspraegung"])
    abs_a = res["absatz_ausverkauft"].set_index("ausverkauft")
    sz = res["soll_zerlegung"]
    abo = res["abo_snapshot"]
    abo_h = abo[(abo["team"] == "Herren") & (abo["merkmal"] == "Tribüne")]
    zer = res["kf_zerlegung"]
    zer_in = zer[(zer["scope"] == "SL ab 2023/24") & (zer["variante"] == "Streuung innerhalb der Saison")].iloc[0]
    korrel = res["kf_korrelationen"].iloc[0]
    zw = res["zahlungswege"]
    zw26 = zw[zw["saison"] == "2025/26"].set_index("zahlungsweg")["anteil"]
    art = res["artikel_gruppen"].set_index(["saison", "name"])["anteil"]
    kies = res["kiesplatz_je_spiel"]
    kies_med = kies.groupby("saison")["anteil_am_catering_total"].median()
    dz = res["kiesplatz_doppelzaehlung"]
    el = res["elastizitaet"]
    an = res["ankunft_je_spiel"]
    an_reto = res["ankunft_reto"]
    sek = res["ankunft_je_sektor"].dropna(subset=["median_min_vor_anpfiff"]).groupby("sektor")["median_min_vor_anpfiff"].median()
    ak = res["ankunft_konsum"]
    reto_t = res["reto_abgleich"]
    kf_frage = res["klaerungsfragen"]
    p2 = res["phase2_kandidaten"]
    unm = res["unmatched"]
    noshow_k = res["noshow_kontext"].set_index(["merkmal", "auspraegung"])

    def sv(saison, col, df=sl):
        return df.loc[saison, col] if saison in df.index else np.nan

    hoch = dq[dq["schweregrad"] == "hoch"]
    belastbar = mx[mx["beurteilung"] == "belastbar"]
    status_kf = karte["status_kf_exkl"].value_counts() if "status_kf_exkl" in karte else pd.Series(dtype=int)
    auffaellig = karte[karte.get("status_kf_exkl", pd.Series(index=karte.index)).isin(["unter Erwartung", "über Erwartung"])]

    T = []
    a = T.append
    a("# Methodennotiz Phase 1 – Datenverknüpfung & Kontextbereinigung")
    a(f"*FCSG «Untapped Business» · Auswertung v{info['version_auswertung']} · erstellt {info['zeitpunkt']} · "
      f"Datenstand: letztes Spiel mit IST {info['datenstand_letztes_spiel_mit_ist']}*\n")
    a("> Umsetzung des «Arbeitsauftrags Modellierung» (Pakete A–E) auf Basis von Retos Datenquellen-Übersicht. "
      "Alle Zahlen stammen aus den Projektdateien und werden beim Lauf von `run_all.py` neu berechnet. "
      "Ausgegeben werden nur Aggregate; Personenfelder werden beim Einlesen verworfen.\n")

    # ---------------------------------------------------------------- Kurzfassung
    a("## 0. Kurzfassung (das Wichtigste in 11 Punkten)\n")
    a(f"1. **Datenbasis:** {len(kern)} gespielte Pflichtspiele der Herren 2021/22–2026/27 sind über das Datum verknüpft "
      f"(Historie, Catering, Tickets, Zutritt, Kontext). {len(korr)} Datums-/Anpfiffehler in den Quellen wurden belegt korrigiert "
      f"(Joins laufen nur über das Datum).")
    a(f"2. **Retos Zahlen sind reproduziert** ({(reto_t['status'].str.startswith('bestätigt')).sum()} von {len(reto_t)} Aussagen bestätigt, "
      f"Rest präzisiert/erweitert). Wichtigste Präzisierung: Die Umsatz-Zuschauer-Elastizität liegt auf {el.iloc[1]['spiele']} Spielen "
      f"bei {el.iloc[1]['elastizitaet']:.2f} (95 %-KI {el.iloc[1]['ki95_unten']:.2f}–{el.iloc[1]['ki95_oben']:.2f}) statt 1.14 – "
      "mehr Zuschauer bringen proportional mehr Umsatz, kein Skaleneffekt.")
    a(f"3. **Ältere Zutrittsdaten sind bereits geliefert:** {len(an)} Spiele mit vollständiger Ankunftskurve statt 27 "
      f"(22/23, 23/24, 2025er-Teil 24/25, 25/26, 26/27).")
    a(f"4. **Kundenfranken:** {sv('2025/26', 'kf_exkl', alle):.2f} CHF exkl. MwSt (alle Pflichtspiele 25/26, Summe/Summe) = Antragswert 14.50. "
      f"Meisterschaft inkl. MwSt: {sv('2021/22', 'kf_inkl'):.2f} (21/22) → {sv('2025/26', 'kf_inkl'):.2f} (25/26).")
    a(f"5. **KF-Treiber:** Innerhalb einer Saison erklärt der Ø Bon {_p(zer_in['anteil_bon'], 0)} und die Bons je Anwesendem "
      f"{_p(zer_in['anteil_bons_pro_anwesende'], 0)} der KF-Streuung – beide Hebel (Frequenz und Warenkorb) zählen.")
    top = ", ".join(f"{r['variable']} → {r['zielgroesse'].split(' (')[0]} {r['effekt']:+.1f} {'%' if r['einheit_effekt'] == '%' else 'Pp.'}"
                    for _, r in belastbar.head(8).iterrows())
    a(f"6. **Kontext wirkt messbar** ({len(belastbar)} belastbare Effekte): {top}.")
    a(f"7. **Kontext erklärt** {_p(mg.set_index('zielgroesse').loc['Anwesenheitsquote (IST/SOLL)', 'r2_kontext_innerhalb_saison'], 0)} "
      f"der saisonbereinigten Streuung der Anwesenheitsquote und {_p(mg.set_index('zielgroesse').loc['Kundenfranken exkl. MwSt', 'r2_kontext_innerhalb_saison'], 0)} "
      "beim Kundenfranken; out-of-sample (Leave-one-season-out) besser als das Saisonmittel.")
    a(f"8. **No-Show steckt im «Rest» (≈ Abos):** Einzeltickets {_p(typ['noshow_einzel'].mean(), 0)}, Rest {_p(typ['noshow_rest_naeherung'].min(), 0)}–"
      f"{_p(typ['noshow_rest_naeherung'].max(), 0)} (21/22–22/23). Bei Einzeltickets fallen Grossbestellungen ab 10 Tickets "
      f"({_p(seg.loc[('Tickets pro Bestellung', '10+'), 'noshow_quote'], 0)}), Gratis/Promo ({_p(seg.loc[('Tarifgruppe', 'Gratis/Promo'), 'noshow_quote'], 0)}) "
      f"und Inhouse-Verkäufe ({_p(seg.loc[('Verkaufskanal', 'Inhouse (Geschäftsstelle/Kasse)'), 'noshow_quote'], 0)}) auf.")
    ein0 = res["einlass_je_eingang"].set_index("sektor")["einlass_1pct_median"]
    dm0 = res["toroeffnung_did"].set_index("zielgroesse").loc["Median Ankunft, min vor Anpfiff"]
    a(f"9. **Toröffnung ist ein messbarer Hebel:** Tribünen A/B/C öffnen rund {ein0.get('C', float('nan')):.0f} min, die Fankurve "
      f"{ein0.get('D', float('nan')):.0f} min, Hospitality {ein0.get('HH (Hospitality)', float('nan')):.0f} min vor Anpfiff. Seit Sektor D "
      f"30 min früher öffnet (02.04.2023), kommen D-Fans {dm0['did_effekt']:.0f} min früher (95 %-KI {dm0['ki95_unten']:.0f}–"
      f"{dm0['ki95_oben']:.0f}) – die Konsumwirkung ist noch offen (Phase 2).")
    a(f"10. **Kiesplatz ist im Catering-Total enthalten** (21/22 frankengenau belegt) – nie addieren. Anteil je Spiel im Median "
      f"{_p(kies_med.min(), 0)}–{_p(kies_med.max(), 0)}.")
    a(f"11. **Diagnosekarte:** {int(status_kf.get('unter Erwartung', 0))} Spiele liegen beim KF unter, {int(status_kf.get('über Erwartung', 0))} über dem "
      "80 %-Erwartungsband. Das sind Prüfkandidaten für Phase 2, kein realisierbares Potenzial (keine Summenbildung).\n")

    # ---------------------------------------------------------------- Änderungen
    if "aenderungsprotokoll" in res:
        a("## Änderungen in Version 1.1.0 (gegenüber der Übergabe v1.0.1)\n")
        a("Bei der vertieften Analyse für die Ideen-Grundlage wurden zwei Codier- bzw. Basisfehler gefunden und korrigiert. "
          "Kontextmodelle, KPI und Erwartungswerte sind davon nicht betroffen (die Merkmale sind keine Modellvariablen).\n")
        a(_tab(res["aenderungsprotokoll"], {"bereich": ("Bereich", "text"), "aenderung": ("Änderung", "text"),
                                            "vorher_v1_0_1": ("vorher (v1.0.1)", "text"), "nachher_v1_1_0": ("nachher (v1.1.0)", "text")}) + "\n")

    # ---------------------------------------------------------------- 1 Auftrag
    a("## 1. Auftrag, Scope und Leitplanken\n")
    a("- **Phase 1 (dieser Auftrag):** Quellen validieren, je Heimspiel eine konsistente Baseline, Anwesenheit/No-Show und Catering "
      "beschreiben, KF in Bons je Anwesendem × Ø Bon zerlegen, Ankunft und Ticketvorlauf als eigene Module, kontextbereinigte "
      "Abweichungen mit Unsicherheit zeigen.")
    a("- **Leitplanken:** Kapazität fix, kein Dynamic Pricing, kein Stadionausbau, keine Hospitality; keine Personensegmentierung; "
      "Umsatz (nicht DB) als Fokus; Massnahmenquantifizierung erst Phase 2.")
    a(f"- **Kernstichprobe:** Pflichtspiele der Herren im Berit Sitterstadion (Super League inkl. Meisterschafts-/Abstiegsrunde, Schweizer Cup, UEFA). "
      f"Baseline ab {config.BASELINE_AB_SAISON}, Kontextmodelle Meisterschaft ab {config.MODELL_AB_SAISON} (Kontexttabelle; 21/22 COVID-geprägt). "
      "Frauen, Länderspiele, Testspiele und Events sind dokumentiert ausgeschlossen (Unmatched-Report).\n")

    # ---------------------------------------------------------------- 2 Daten
    a("## 2. Datenbasis und Abdeckung\n")
    a("Abdeckung je Saison (Pflichtspiele mit Daten je Modul):\n")
    spalten = {"saison": ("Saison", "text"), "wettbewerb": ("Wettbewerb", "text"), "pflichtspiele": ("Spiele", "z0")}
    for c in ab.columns[3:]:
        spalten[c] = (c, "z0")
    a(_tab(ab, spalten) + "\n")
    a("Gemeinsame Stichproben (Meisterschaft ab 22/23):\n")
    a(_tab(gs, {"kombination": ("Kombination", "text"), "spiele": ("Spiele", "z0"), "saisons": ("Saisons", "text")}) + "\n")
    a("**Nicht geliefert** (und daher nicht ausgewertet): Merchandise (Paket E), Catering je Viertelstunde und Verkaufsstelle "
      "inkl. Stand→Sektor-Mapping, Deckungsbeiträge/Einstandspreise, Kapazität je Sektor mit Sperrungen und Verkaufsstand je Tag, "
      "Abo-Besuche je Spiel. Einzelticket-Export 2024/25 endet am 09.12.2024; Zutritte Juli–Dezember 2024 nur bruchstückhaft.\n")

    # ---------------------------------------------------------------- 3 Datenmodell
    a("## 3. Datenmodell und Verknüpfung\n")
    a("| Tabelle | Granularität | Inhalt |\n|---|---|---|")
    for t, g, i in [("dim_match", "Heimspiel", "match_id = Datum + Wettbewerb, Anpfiff (Mehrheit aus 5 Quellen), Status"),
                    ("fact_attendance_match", "Heimspiel", "SOLL, IST, VIP, Gäste, Zweitmarkt, SOLL-/IST-Definition"),
                    ("fact_ticket_single", "Einzelticket → aggregiert", "Kanal, Tarif, Tribüne, Vorlauf, Eintritt (ZKS), Bestellgrösse"),
                    ("snapshot_season_ticket", "Abo-Sitz (Stichtag 30.09.2026)", "Tribüne, Tarif, Kanal, Abo-Form, Preis"),
                    ("fact_access", "erster Scan je Ticket → aggregiert", "Ankunft relativ zum Anpfiff, Eingang, Leser"),
                    ("fact_catering_match", "Heimspiel", "Public Netto, Bons, Umsatz inkl./exkl., Zahlungswege, Bemerkungen"),
                    ("fact_kiesplatz", "Event × Verkaufsstelle", "Brutto/Netto (Teilmenge des Catering-Totals)"),
                    ("fact_article_season", "Artikel × Saison", "Menge, Umsatz laut Datei (23/24–24/25 brutto, 25/26 netto) und harmonisiert brutto (nur Saisonsummen)"),
                    ("dim_match_context", "Heimspiel", "Kontextvariablen mit Quelle und Fehlstatus"),
                    ("mart_match", "Heimspiel", "Zielgrössen, Kontext, Diagnose, Verfügbarkeitsflags")]:
        a(f"| `{t}` | {g} | {i} |")
    a("\n**Regeln:** Join ausschliesslich über das Datum (nie über das Gegner-Label); zuerst jede Quelle auf Spielebene aggregieren, "
      "dann verbinden (kein Rohdaten-Join Ticket × Scan × Catering). Pseudonyme IDs (Barcode/UTId) nur technisch zur "
      "Deduplizierung, danach verworfen.\n")
    a("**Belegte Korrekturen** (greifen nur, solange der Altwert noch in der Quelle steht):\n")
    a(_tab(korr, {"quelle": ("Quelle", "text"), "blatt": ("Blatt/Datei", "text"), "zeile": ("Zeile", "text"),
                  "feld": ("Feld", "text"), "alt": ("alt", "text"), "neu": ("neu", "text")}) + "\n")
    zu = unm[unm["zu_pruefen"]]
    a(f"Unmatched-Report: {len(unm)} Zeilen ohne Kernspiel, davon {len(zu)} zu prüfen (v.a. Kernspiele ohne Ticket-/Kontextdaten); "
      "der Rest sind Events, Frauen-, Länder- und Testspiele.\n")

    # ---------------------------------------------------------------- 4 KPI
    a("## 4. KPI-Definitionen\n")
    a("```\nAnwesenheitsquote = IST / SOLL            No-Show-Quote = 1 − IST / SOLL      No-Show absolut = SOLL − IST\n"
      "Kundenfranken (KF) = Umsatz / Public Netto = (Bons / Public Netto) × (Umsatz / Bons)\nØ Bon = Umsatz / Bons\n"
      "Saisonwerte immer Summe/Summe (z.B. KF = Σ Umsatz / Σ Public Netto)\n```\n")
    a("- **SOLL** ist je nach Spiel unterschiedlich definiert: Summe der Ticketkomponenten (Einzeltickets je Verkaufsstelle + "
      f"zwei Abo-Komponenten − Zweitmarkt; Abo-Bestand 25/26 implizit {_z(sz['abo_bestand_implizit'].min())}–{_z(sz['abo_bestand_implizit'].max())}) "
      f"oder bei ausverkauften Spielen ein Kapazitätswert (z.B. 20'036 − 1'930 + Gäste). {int(kern['soll_definition'].str.contains('Kapazität').sum())} "
      "Pflichtspiele haben ein Kapazitäts-SOLL; dort ist die No-Show-Quote nicht ticketbasiert (Flag `soll_definition`).")
    a("- **Public Netto** (KF-Nenner) = IST minus eine VIP-Zahl; 2025/26 liegt der Abzug im Mittel rund 90 Personen über «IST VIP» "
      "der Historie, 2026/27 ist er identisch (Effekt auf den KF < 1 %).")
    a("- **MwSt:** Netto vor 2020/21 pauschal inkl./1.077, danach effektive Mischsätze (Take-away reduziert) → langfristige "
      "Vergleiche inkl. MwSt, Modelle exkl. MwSt mit Saison-Effekten. Die CHF 14.50 des Antrags = KF exkl. MwSt aller Pflichtspiele 25/26.")
    a("- **Bons je Anwesendem ≠ Kaufquote:** Eine Person kann mehrfach kaufen, eine Gruppe auf einem Bon.\n")

    # ---------------------------------------------------------------- 5 Paket A
    a("## 5. Paket A – Baseline und Qualitätsprüfung\n")
    sl_t = sl.reset_index()
    a(_tab(sl_t, {"saison": ("Saison", "text"), "spiele": ("Spiele", "z0"), "ist_mittel": ("Ø IST", "z0"),
                  "soll_mittel": ("Ø SOLL", "z0"), "noshow_quote": ("No-Show", "p1"), "kf_inkl": ("KF inkl.", "z2"),
                  "kf_exkl": ("KF exkl.", "z2"), "bons_pro_anwesende": ("Bons/Anw.", "z2"), "bon_exkl": ("Ø Bon exkl.", "z2"),
                  "umsatz_inkl": ("Umsatz inkl. CHF", "z0")}) + "\n")
    a("*Meisterschaft; 2026/27 erst 4 Spiele (Sommer/Frühherbst) – nicht ungewichtet mit Vollsaisons vergleichen.*\n")
    si = res["scan_ist"]
    a(f"**Scan-IST-Abgleich:** {int(si['zutritt_vollstaendig'].sum())} von {len(si)} Spieltagen mit vollständiger Lieferung. "
      f"Ab 2025/26 weichen die Scans im Mittel {si[si['saison'] >= '2025/26']['abweichung_scans_ist'].mean() * 100:+.2f} % vom IST ab "
      "(IST ≈ Scanzahl), davor liegt IST um 1–3 % über den Scans (manuelle Zählungen). Grosse Lücken sind erklärt "
      "(Drehkreuz-/Handscannerprobleme laut Historie, unvollständige Lieferung).\n")

    # ---------------------------------------------------------------- 6 Paket B
    a("## 6. Paket B – Anwesenheit und Absatz\n")

    def nk(m, aus):
        try:
            return noshow_k.loc[(m, aus)]
        except KeyError:
            return None

    rows = []
    for m_, aus in [("Wochentag", "Wochenende (Sa/So)"), ("Wochentag", "Wochentag (Mo–Fr)"),
                    ("Anstosszeit", "Nachmittag (<17 Uhr)"), ("Anstosszeit", "Abend (ab 20 Uhr)"),
                    ("Winter (Nov–Feb)", "True"), ("Top-Gegner (FCB/YB/FCZ)", "True"), ("Ausverkauft", "True"),
                    ("Ausverkauft", "False")]:
        x = nk(m_, aus)
        if x is not None:
            rows.append({"merkmal": m_, "auspraegung": aus.replace("True", "ja").replace("False", "nein"), "spiele": x["spiele"],
                         "noshow": x["noshow_gewichtet"], "abw": x["abweichung_vom_saisonmittel_pp"]})
    a("No-Show nach Kontext (deskriptiv; Merkmale überlagern sich – Effekte siehe Kontext-Effekt-Matrix):\n")
    a(_tab(pd.DataFrame(rows), {"merkmal": ("Merkmal", "text"), "auspraegung": ("Ausprägung", "text"), "spiele": ("Spiele", "z0"),
                                "noshow": ("No-Show", "p1"), "abw": ("Abw. vom Saisonmittel (Pp.)", "d1")}) + "\n")
    a("**Ticket-Typ-Näherung (nur 21/22 und 22/23 mit validem Eintritt je Einzelticket):**\n")
    a(_tab(typ.reset_index(), {"saison": ("Saison", "text"), "spiele": ("Spiele", "z0"), "anteil_rest_am_soll": ("Rest (≈Abos) am SOLL", "p1"),
                               "noshow_einzel": ("No-Show Einzel", "p1"), "noshow_rest_naeherung": ("No-Show Rest", "p1")}) + "\n")
    a("*Rest = SOLL − Einzeltickets enthält Abos, VIP, Gäste und Freikarten; bei Kapazitäts-SOLL überschätzt. Nur als gekennzeichnete Näherung.*\n")
    rows = []
    for m_, aus in [("Tickets pro Bestellung", "1"), ("Tickets pro Bestellung", "2"), ("Tickets pro Bestellung", "3–4"),
                    ("Tickets pro Bestellung", "5–9"), ("Tickets pro Bestellung", "10+"), ("Tarifgruppe", "Vollpreis"),
                    ("Tarifgruppe", "Ermässigt"), ("Tarifgruppe", "Gratis/Promo"), ("Tarifgruppe", "Sponsor/Dritte"),
                    ("Verkaufskanal", "Online-Shop"), ("Verkaufskanal", "Inhouse (Geschäftsstelle/Kasse)"),
                    ("Verkaufskanal", "Partner online (Connect/TDL)"), ("Kaufzeitpunkt vor Spiel", "Spieltag"),
                    ("Kaufzeitpunkt vor Spiel", "über 30 Tage")]:
        if (m_, aus) in seg.index:
            x = seg.loc[(m_, aus)]
            rows.append({"merkmal": m_, "auspraegung": aus, "tickets": x["tickets"], "noshow": x["noshow_quote"]})
    a("No-Show der Einzeltickets nach Segment (Spiele 21/22–22/23 mit validem ZKS-Eintritt):\n")
    a(_tab(pd.DataFrame(rows), {"merkmal": ("Merkmal", "text"), "auspraegung": ("Ausprägung", "text"),
                                "tickets": ("Tickets", "z0"), "noshow": ("No-Show", "p1")}) + "\n")
    a(f"**Einzelticket-Vorlauf:** Bei ausverkauften Meisterschaftsspielen ist die Hälfte der Einzeltickets "
      f"{abs_a.loc[True, 't50_median']:.0f} Tage vor dem Spiel verkauft (sonst {abs_a.loc[False, 't50_median']:.0f} Tage); "
      f"der Spieltagsanteil liegt bei {_p(abs_a.loc[True, 'anteil_spieltag_median'], 0)} vs. {_p(abs_a.loc[False, 'anteil_spieltag_median'], 0)}. "
      "Die Kurven zeigen nur Einzeltickets (ohne Abos) und den Endbestand nach allfälligen Stornos – keine Stadion-Ausverkaufskurve.\n")
    a("**Saisonabos 2026/27 (Herren, 13'052 Sitze):** " + ", ".join(
        f"Tribüne {r['auspraegung']} {_z(r['abos'])} ({_p(r['anteil'], 0)})" for _, r in abo_h.iterrows()) + ".\n")

    # ---------------------------------------------------------------- 7 Paket C
    a("## 7. Paket C – Catering\n")
    a(f"- **KF-Zerlegung (Meisterschaft ab 23/24, n={int(zer_in['spiele'])}):** saisonbereinigt Ø Bon {_p(zer_in['anteil_bon'], 0)}, "
      f"Bons je Anwesendem {_p(zer_in['anteil_bons_pro_anwesende'], 0)}, Kovarianz {_p(zer_in['anteil_kovarianz'], 0)} der Varianz von ln KF.")
    a(f"- **Retos Korrelationen** (25/26 + 26/27, n={int(korrel['spiele'])}): r(KF, Ø Bon) = {korrel['r_kf_bon']:.2f}, "
      f"r(KF, Bons/Anw.) = {korrel['r_kf_bons_pro_anwesende']:.2f} – algebraisch verknüpft, kein Kausalnachweis.")
    a("- **Zahlungswege 25/26:** " + ", ".join(f"{k_} {_p(v, 1)}" for k_, v in zw26.items()) + ".")
    a(f"- **Sortiment (Meisterschaft, Umsatzanteile brutto):** Alkohol {_p(art.get(('2023/24', 'Alkoholische Getränke')), 1)} (23/24) → "
      f"{_p(art.get(('2025/26', 'Alkoholische Getränke')), 1)} (25/26); Food {_p(art.get(('2025/26', 'Food')), 0)}, "
      f"alkoholfrei {_p(art.get(('2025/26', 'Alk.-freie Getränke')), 0)}. Die Artikelauswertung liefert 23/24–24/25 brutto, 25/26 netto; "
      "verglichen wird einheitlich brutto (overrides/artikel_basis.csv). Artikelwerte nur als Saisonsummen – nie pro Spiel in Modelle.")
    ohne_bbq = dz[(dz["verkaufsstelle_kiesplatz"] != "BBQ1 Kiesplatz") & (dz["brutto_kiesplatz"] > 0)]
    bbq = dz[dz["verkaufsstelle_kiesplatz"] == "BBQ1 Kiesplatz"]
    a(f"- **Kiesplatz:** Für Getränke-/Pommes-Contrailer, Fanshop Bar und Bier S2 sind {int(ohne_bbq['identisch'].sum())} von "
      f"{len(ohne_bbq)} Spiel-Stand-Werten 21/22 frankengenau identisch mit den Standspalten der Catering-Datei; «BBQ1 Kiesplatz» "
      f"liegt in {int((bbq['brutto_kiesplatz'] <= bbq['wert_catering']).sum())} von {len(bbq)} Fällen unter «Contrailer BBQ 1» "
      "(Teilmenge, Rest auf der Plattform) → Kiesplatz ist im Catering-Total enthalten und wird nie addiert.")
    a("- **Elastizität Umsatz ~ Public-Anwesende:** " + "; ".join(
        f"{r['variante']}: {r['elastizitaet']:.2f} [{r['ki95_unten']:.2f}–{r['ki95_oben']:.2f}], n={r['spiele']}" for _, r in el.iterrows())
      + ". Zusammenhang, keine Kausalität.\n")

    # ---------------------------------------------------------------- 8 Paket D
    a("## 8. Paket D – Ankunft\n")
    r0, r1 = an_reto.iloc[0], an_reto.iloc[1]
    a(f"- **Retos Stichprobe (25/26 + 26/27, n={r0['spiele']}):** Median {r0['median_min_vor_anpfiff_mittel']:.1f} min vor Anpfiff, "
      f"{_p(r0['anteil_ab_45_min_mittel'], 0)} ≥ 45 min, {_p(r0['anteil_letzte_15_min_inkl_nach_anpfiff_mittel'], 0)} in den letzten 15 min "
      f"(inkl. nach Anpfiff). **Alle vollständigen Spiele (n={r1['spiele']}):** {r1['median_min_vor_anpfiff_mittel']:.1f} min, "
      f"{_p(r1['anteil_ab_45_min_mittel'], 0)}, {_p(r1['anteil_letzte_15_min_inkl_nach_anpfiff_mittel'], 0)}.")
    a("- **Nach Eingang (Median der Spielmediane):** " + ", ".join(f"{k_} {v:.0f} min" for k_, v in sek.sort_values(ascending=False).items())
      + ". Sektor = physischer Eingang (Lesername); Seatinfo ist nicht eindeutig und wird nicht verwendet.")
    a(f"- **Einlass:** 1 % der Besucher ist im Median {an['einlass_1pct_min_vor_anpfiff'].median():.0f} min vor Anpfiff im Stadion "
      f"(Toröffnung laut Daten); Mehrfachscans derselben Ticket-ID sind selten "
      f"({si['tickets_mehrfach_gescannt'].sum() / si['besucher_scans'].sum() * 100:.3f} %) – Wiedereintritt praktisch nicht vorhanden.")
    ein = res["einlass_je_eingang"].set_index("sektor")["einlass_1pct_median"]
    did = res["toroeffnung_did"].set_index("zielgroesse")
    tk = res["toroeffnung_konsum"]
    a("- **Toröffnung je Eingang (aus Scans):** Einlass-Beginn (1 %-Punkt) im Median " +
      ", ".join(f"{k_} {v:.0f} min" for k_, v in ein.items()) + " vor Anpfiff (Streuung ±2 min → feste Öffnungszeiten). "
      "Die Ankunftskurven steigen genau ab diesem Zeitpunkt steil an: Auslöser ist die Toröffnung, nicht das Spiel.")
    dm, d60 = did.loc["Median Ankunft, min vor Anpfiff"], did.loc["Anteil Ankunft ≥ 60 min vor Anpfiff"]
    a(f"- **Natürliches Experiment:** Ab 02.04.2023 öffnet Sektor D 90 statt 60 min vor Anpfiff (Catering-Bemerkung «Türöffnung 1.5h»; "
      f"Scans bestätigen {did.loc['Einlass-Beginn (1 %-Punkt), min vor Anpfiff', 'did_effekt']:+.0f} min). Differenz-in-Differenzen "
      f"gegenüber A/B/C bei denselben Spielen ({int(dm['spiele_vorher'])} Spiele vorher, {int(dm['spiele_nachher'])} nachher): "
      f"Median der Ankunft {dm['did_effekt']:+.1f} min (95 %-KI {dm['ki95_unten']:.1f} bis {dm['ki95_oben']:.1f}), Anteil ≥ 60 min "
      f"{d60['did_effekt'] * 100:+.0f} Pp. (KI {d60['ki95_unten'] * 100:.0f} bis {d60['ki95_oben'] * 100:.0f}). "
      f"Auf Spielebene lag der KF nach der Umstellung {tk.iloc[-1]['kf_abweichung_von_erwartung_pct']:+.1f} % über der Kontexterwartung "
      f"(n={int(tk.iloc[-1]['spiele'])}, KI90 {tk.iloc[-1]['ki90_unten']:+.1f} bis {tk.iloc[-1]['ki90_oben']:+.1f} %) – **Wirkung auf die "
      "Ankunft belegt, Wirkung auf den Konsum nicht belastbar** (zu wenige Spiele, kein Stand→Sektor-Mapping).")
    k1 = ak[ak["spezifikation"] == "nur Saisoneffekte"].set_index("zielgroesse")
    k2 = ak[ak["spezifikation"] != "nur Saisoneffekte"].set_index("zielgroesse")
    a(f"- **Ankunft → Konsum (aggregierte Spiele, n={int(ak['spiele'].iloc[0])}):** +10 Pp. Frühankommende gehen mit "
      f"{k1.loc['Kundenfranken exkl. MwSt', 'effekt_pct_je_10pp_frueh']:+.1f} % KF einher (p={k1.loc['Kundenfranken exkl. MwSt', 'p_wert']:.2f}); "
      f"mit Kontextkontrollen {k2.loc['Kundenfranken exkl. MwSt', 'effekt_pct_je_10pp_frueh']:+.1f} % (p={k2.loc['Kundenfranken exkl. MwSt', 'p_wert']:.2f}). "
      "Der Zusammenhang ist **nicht belastbar**; ohne Bon-Zeitstempel bleibt Ankunft→Konsum eine Hypothese.\n")

    # ---------------------------------------------------------------- 9 Modelle
    a("## 9. Kontextmodelle und Kontext-Effekt-Matrix\n")
    a("**Vorgehen:** Je Zielgrösse ein eigenes Modell (keine Gesamtumsatz-Regression): Anwesenheitsquote und Frühankunft-Anteil "
      "(logit), KF, Bons je Anwesendem und Ø Bon (log), jeweils mit Saison-Effekten (Preise, MwSt, Definitionswechsel, Trend) und "
      "vorab festgelegten Kontextvariablen: Top-Gegner (FCB/YB/FCZ), Anstoss-Slot (Samstag ab 20 Uhr, Nachmittag vor 17 Uhr, "
      "Werktagabend; Referenz Samstag 17–19.59 Uhr; ab Run 4 statt Werktag + Abendspiel ≥ 20 Uhr, D-048), Temperatur zum Anpfiff "
      "(MeteoSchweiz), Regen bei Anreise, Schulferien. Robuste Standardfehler (HC3). Clubhebel (Stände, Zweitmarkt, Kommunikation, "
      "Payment) werden bewusst nicht herauskontrolliert.\n")
    a("**Validierung:** (1) Leave-one-season-out auf saisonbereinigten Werten gegen das Saisonmittel als Basislinie; "
      "(2) Vorzeichenstabilität über Saisons und sechs Sensitivitätsvarianten (inkl. Cup/UEFA, inkl. Scanproblem-Spiele, "
      "Gegnerstärke statt Top-Gegner, Tagesmittel- statt Anpfifftemperatur, ohne Ausreisser, nur ticketbasiertes SOLL). «Belastbar» = 95 %-Intervall ohne 0 "
      "und Vorzeichen in ≥ 80 % der Saisons und Varianten stabil. Bei 30 geprüften Effekten wären rund 1–2 zufällig "
      "«signifikante» Ergebnisse zu erwarten – deshalb zählt nicht der p-Wert allein, sondern zusätzlich die Stabilität.\n")
    a(_tab(mg, {"zielgroesse": ("Zielgrösse", "text"), "spiele": ("Spiele", "z0"),
                "r2_kontext_innerhalb_saison": ("R² Kontext (saisonbereinigt)", "p1"),
                "verbesserung_loso_pct": ("Out-of-sample vs. Saisonmittel (% RMSE)", "d1")}) + "\n")
    a("**Kontext-Effekt-Matrix** (Effekt: log-Ziele in %, Quoten in Prozentpunkten; Temperatur je +5 °C):\n")
    a(_tab(mx, {"zielgroesse": ("Zielgrösse", "text"), "variable": ("Variable", "text"), "einordnung": ("Einordnung", "text"),
                "effekt": ("Effekt", "d1"), "ki95_unten": ("KI unten", "d1"), "ki95_oben": ("KI oben", "d1"),
                "beurteilung": ("Beurteilung", "text")}) + "\n")
    a("*Wichtig: KF und Ø Bon/Bons sind algebraisch verknüpft; Effekte sind Zusammenhänge auf Spielebene (Kontext ist vor dem Spiel "
      "bekannt), keine Personenaussagen. «Nicht belastbar schätzbar» ist ein zulässiges Ergebnis.*\n")

    # ---------------------------------------------------------------- 10 Diagnose
    a("## 10. Diagnosekarte – kein automatischer Potenzialbeweis\n")
    a("```\nDiagnoselücke = erwarteter Wert unter Kontext − beobachteter Wert   (positiv = unter Erwartung)\n"
      "Referenzlücke Konsum (CHF) = (erwarteter KF − beobachteter KF) × beobachtete Public-Anwesende\n```\n")
    a("Erwartungswerte stammen aus Leave-one-match-out-Schätzungen (das Spiel selbst fliesst nicht in seine Erwartung ein); "
      "das 80 %-Band entspricht ±1.28 × Prognosefehler. Lücken aus KF, Bons und Ø Bon werden **nicht addiert**; CHF-Werte sind "
      "modellbasierte Referenzlücken und werden **nicht summiert**. Anwesenheitslücken in Personen nur bei ticketbasiertem SOLL; "
      "CHF nur als Szenario mit explizitem φ = 0.6.\n")
    if len(auffaellig):
        a("Spiele ausserhalb des KF-Bands:\n")
        a(_tab(auffaellig, {"datum": ("Datum", "text"), "gegner_anzeige": ("Gegner", "text"),
                            "beobachtet_kf_exkl": ("KF beob.", "z2"), "erwartet_kf_exkl": ("KF erw.", "z2"),
                            "referenzluecke_konsum_chf": ("Referenzlücke CHF", "z0"), "einordnung_konsum": ("Einordnung", "text"),
                            "mechanismen": ("Mögliche Mechanismen", "text")}).replace(" 00:00:00", "") + "\n")
    ms = muster[(muster["auspraegung"] == "ja") & (muster["spiele"] >= 5)]
    if len(ms):
        a("Wiederkehrende Muster (mittlere Abweichung von der Erwartung bei gleichem Kontext):\n")
        a(_tab(ms, {"zielgroesse": ("Zielgrösse", "text"), "merkmal": ("Merkmal", "text"), "spiele": ("Spiele", "z0"),
                    "mittlere_abweichung_von_erwartung_pct": ("Abweichung %", "d1"), "ki90_unten": ("KI90 unten", "d1"),
                    "ki90_oben": ("KI90 oben", "d1")}) + "\n")
        a("*Geschlossene Stände treten vor allem bei schwacher Nachfrage auf (umgekehrte Kausalität möglich); Aussagen nur als Prüfkandidaten.*\n")

    # ---------------------------------------------------------------- 11 Reto
    a("## 11. Abgleich mit Retos Sichtung\n")
    a(_tab(reto_t, {"aussage_reto": ("Retos Aussage", "text"), "reproduziert": ("Reproduziert", "text"),
                    "status": ("Status", "text"), "erklaerung": ("Erklärung", "text")}) + "\n")

    # ---------------------------------------------------------------- 12 Qualität
    a("## 12. Datenqualität und Tests\n")
    a(f"- Importtests: **{int(tests['bestanden'].sum())} von {len(tests)} bestanden**" +
      ("" if tests["bestanden"].all() else " – nicht bestanden: " + "; ".join(tests.loc[~tests["bestanden"], "test"])) + ".")
    a(f"- Befunde: {len(dq)} (hoch {len(hoch)}, mittel {int((dq['schweregrad'] == 'mittel').sum())}, "
      f"tief {int((dq['schweregrad'] == 'tief').sum())}, info {int((dq['schweregrad'] == 'info').sum())}). Befunde mit hoher Relevanz:\n")
    for _, r in hoch.iterrows():
        a(f"  - **{r['bereich']} – {r['ort']}:** {r['befund']} → {r['behandlung']}")
    a("")

    # ---------------------------------------------------------------- 13 Grenzen
    a("## 13. Grenzen (was die Daten nicht hergeben)\n")
    for g in ["Keine Verbindung Ticket/Person ↔ Catering-Bon: Konsum je Ticket-Typ, Sektor oder Person ist nicht messbar.",
              "Kein Zeitstempel im Catering: Konsum-Timing (Halbzeit, vor Anpfiff) und Durchsatz-Engpässe nicht messbar.",
              "Kein Stand→Sektor-Mapping: kein Sektor-KF.",
              "Abo-Besuche nur als Näherung 21/22–22/23; Eintritt je Einzelticket 23/24 unvollständig, 24/25 leer.",
              "Einzelticket-Kurven ohne Abos und ohne Stornoverlauf; Ausverkaufszeitpunkt ohne Kapazität je Tag nicht bestimmbar.",
              "Kleine Stichproben (rund 18–19 Meisterschaftsspiele pro Saison); Kontexteffekte sind Zusammenhänge, keine Kausalität.",
              "Wetter: Station St. Gallen (Stundenwerte) als Näherung für das Stadionwetter.",
              "Merchandise und Deckungsbeitrag: nicht geliefert."]:
        a(f"- {g}")
    a("")

    # ---------------------------------------------------------------- 14/15
    a("## 14. Klärungsfragen an Sandro / FCSG\n")
    a(_tab(kf_frage, {"prioritaet": ("Priorität", "text"), "bereich": ("Bereich", "text"), "frage": ("Frage", "text"),
                      "evidenz_aus_den_daten": ("Evidenz", "text")}) + "\n")
    a("## 15. Prüfkandidaten für Phase 2 (nicht quantifiziert)\n")
    a(_tab(p2, {"pruefkandidat": ("Prüfkandidat", "text"), "hebeltyp": ("Hebeltyp", "text"),
                "befund_phase_1": ("Befund Phase 1", "text"), "benoetigte_daten_phase_2": ("Benötigte Daten", "text")}) + "\n")

    # ---------------------------------------------------------------- 16 Repro
    a("## 16. Reproduzierbarkeit\n")
    a("- Code: `2. Modellierung/Python_Auswertung` (Start: `python run_all.py`; Tests: `python -m pytest`).")
    a("- Ergebnisse: `FCSG_Phase1_Ergebnisse.xlsx` (alle Tabellen mit Inhaltsverzeichnis), `Abbildungen/`, `Tabellen/` (CSV), "
      "`Laufprotokoll.json` (Versionen, Laufzeit, MD5-Prüfsummen aller Eingabedateien).")
    a(f"- Umgebung dieses Laufs: Python {info['python']}, " + ", ".join(f"{k_} {v}" for k_, v in info["pakete"].items()) + ".")
    a("- Öffentliche Zusatzdaten (MeteoSchweiz, football-data.co.uk) liegen als Cache im Ordner `external/`; Aktualisierung mit "
      "`python scripts/externe_daten_aktualisieren.py`.")
    return "\n".join(T) + "\n"

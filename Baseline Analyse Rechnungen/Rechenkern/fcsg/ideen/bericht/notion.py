"""Notion-taugliche Markdown-Fassung der Ideen-Grundlage (zulässige Aggregate, ohne Bilder)."""
from __future__ import annotations

from pathlib import Path

import pandas as pd

from ... import __version__
from ...report.methodennotiz import _tab
from ..fmt import dez, p, z


def text(e: dict, kz: dict, felder: list) -> str:
    T = []
    a = T.append
    a("# Ideen-Grundlage «Untapped Business» – FC St.Gallen 1879")
    a(f"*Vertiefte Datenanalyse für die Ideenfindung (Simon & Reto) · Version {__version__} · Daten bis {kz.get('datenstand', '–')} · "
      "nur Aggregate (NDA, Datenraum)*\n")
    a("> Dieses Dokument liefert keine fertigen Ideen, sondern Befunde, Rechenbausteine, Leitfragen und Leitplanken. Grafiken und alle "
      "Tabellen: `Ideen_Grundlage_FCSG.html` / `.pdf` und `Ideen_Grundlage_FCSG.xlsx` (Hebel-Rechner, Szenarien, Steckbrief).\n")
    a("## Leitplanken\n")
    for t in ["Kein Dynamic Pricing, Kapazität fix, kein Stadionausbau, keine Hospitality.",
              "Keine Personensegmentierung – nur Spiel, Sektor, Tarif, Kanal (aggregiert).",
              "Umsatz ≠ Ertrag: CHF = Caterer-Umsatz exkl. MwSt; Club-Anteil und Kosten unbekannt.",
              "Hebel und Lücken nie summieren; Rechenwerte sind isolierte Bausteine.",
              "Zusammenhänge ≠ Kausalität; «nicht belastbar» ist ein zulässiges Ergebnis."]:
        a(f"- {t}")
    a("\n## Das Wichtigste in 12 Befunden\n")
    a(_tab(e["kernbefunde"], {"thema": ("Thema", "text"), "befund": ("Befund", "text"), "detail": ("Detail", "text"),
                              "fundstelle": ("Fundstelle", "text")}) + "\n")
    a("## Rechengrundlage (Saison 2025/26)\n")
    a(f"Public-Anwesende je Spiel: **{z(kz['b_public_netto_mittel'])}** (nicht 18'000) · KF exkl. MwSt **CHF {dez(kz['b_kf_exkl'])}** · "
      f"Ø Bon **CHF {dez(kz['b_bon_exkl'])}** · Bons je Anwesendem **{dez(kz['b_bons_pro_anwesende'], 3)}** · No-Show **{p(kz['b_noshow_quote'], 1)}**.\n")
    fw = e["faustwerte"]
    fw = fw[fw["basis"] == "2025/26"].copy()
    fw["phi_txt"] = fw["phi"].map(lambda v: "–" if pd.isna(v) else f"{v:.1f}")
    a(_tab(fw, {"hebel": ("Hebel (isoliert)", "text"), "phi_txt": ("φ", "text"), "chf_pro_spiel": ("CHF je Spiel", "z0"),
                "chf_pro_saison": ("CHF je Saison", "z0")}) + "\n")
    a("*Hebel überlappen (KF = Bons je Anwesendem × Ø Bon) und werden nicht addiert.*\n")
    a("## Neun Chancenfelder\n")
    a(_tab(e["chancenfelder"], {"nr": ("Nr.", "text"), "chancenfeld": ("Chancenfeld", "text"), "evidenz": ("Evidenz", "text"),
                                "steuerbarkeit": ("Steuerbarkeit", "text"), "reichweite": ("Reichweite", "text"),
                                "datenreife": ("Datenreife", "text")}) + "\n")
    for f in felder:
        a(f"### {f.nr}. {f.titel}\n")
        a(f"**{f.kernzahl}**\n")
        for b in f.befund:
            a(f"- {b}")
        a(f"\n*Evidenz {f.evidenz}:* {f.evidenz_begruendung}  ")
        a(f"*Steuerbarkeit {f.steuerbarkeit}:* {f.clubhebel}  ")
        a(f"*Hebel-Arithmetik:* {f.hebel_arithmetik}\n")
        if f.warnhinweis:
            a(f"> ⚠️ {f.warnhinweis}\n")
        a("**Leitfragen:**")
        for i, q in enumerate(f.leitfragen, start=1):
            a(f"{i}. {q}")
        a(f"\n**Pilot messbar machen:** {f.pilot_messung}  ")
        a(f"**Datenlücke:** {f.datenluecke}\n")
    a("## Retos 12 Ideen im Daten-Check\n")
    a(_tab(e["reto_ideen_check"], {"nr": ("Nr.", "text"), "idee_reto": ("Idee", "text"), "vortest_mit_daten": ("Vortest", "text"),
                                   "einschaetzung_datensicht": ("Einschätzung", "text")}) + "\n")
    aend = e.get("phase1_aenderungen")
    if isinstance(aend, pd.DataFrame) and len(aend):
        a("## Korrekturen in Phase 1 (v1.1.0)\n")
        a(_tab(aend, {"bereich": ("Bereich", "text"), "vorher_v1_0_1": ("vorher", "text"), "nachher_v1_1_0": ("nachher", "text")}) + "\n")
    a("## Datenanfragen an den FCSG\n")
    a(_tab(e["datenanfragen"], {"prioritaet": ("Prio", "text"), "datenanfrage": ("Datenanfrage", "text"),
                                "schaltet_frei": ("schaltet frei", "text"), "chancenfelder": ("Felder", "text")}) + "\n")
    a("## Methodik in Kürze\n")
    for t in ["Verknüpfung über das Spieldatum; Saisonwerte Summe/Summe; Artikel einheitlich brutto.",
              f"Alkohol-Proxy aus dem MwSt-Mix des Kassenkanals Payfix, validiert (≤ {dez(kz['alk_val_maxdiff'], 1)} Pp. zur Artikelauswertung, "
              f"r = {dez(kz['alk_val_r'])} mit dem Kiesplatz).",
              "Kontextmodelle wie Phase 1 (Saison-Effekte, 6 Kontextvariablen, HC3, Leave-one-season-out, Vorzeichenstabilität).",
              "Frühindikator mit Rolling Origin (nur frühere Spiele im Training) und kalibriertem 80 %-Band.",
              "Tribünen 2026/27 als Näherung aus Abo-Snapshot, Einzeltickets und Scans je Eingang (4 Spiele).",
              "Grenzen: keine Verbindung Ticket ↔ Bon, keine Kassen-Zeitstempel, keine Kosten/Margen, kein Merchandise."]:
        a(f"- {t}")
    return "\n".join(T) + "\n"


def schreibe(pfad: Path, e: dict, kz: dict, felder: list) -> Path:
    pfad.write_text(text(e, kz, felder), encoding="utf-8")
    return pfad

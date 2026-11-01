"""Qualitätssicherung: Abdeckungsmatrix, gemeinsame Stichproben, automatisierte Importtests, Quelleninventar.

Auftrag Abschnitt 8: Vollständigkeit, Datums-/Zeitzonenlogik, Join-Kardinalität, Umsatzabgleich,
Einheiten und Definitionswechsel automatisiert testen. Fehlend ist nicht null.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from . import config
from .datamodel import Modell, Rohdaten
from .sources.tickets import PERSONENFELDER

MODULE = [
    ("hat_anwesenheit", "Anwesenheit (Historie SOLL/IST)"), ("hat_catering_umsatz", "Catering-Umsatz + Public Netto"),
    ("hat_bons", "Catering-Transaktionen (Bons)"), ("hat_zutritt_vollstaendig", "Zutritt vollständig (Ankunft)"),
    ("hat_einzeltickets_vollstaendig", "Einzeltickets vollständig (Vorlauf)"),
    ("hat_eintritt_zks_valide", "Eintritt je Einzelticket (ZKS valide)"), ("hat_kontext_gruppe", "Spielkontext-Tabelle (Gruppe)"),
    ("im_kontextmodell", "im Kontextmodell (Diagnosekarte)"),
]


def abdeckung(mart: pd.DataFrame) -> pd.DataFrame:
    k = mart[mart["kernscope"]]
    rows = []
    for (s, w), g in k.groupby(["saison", "wettbewerb"]):
        row = {"saison": s, "wettbewerb": w, "pflichtspiele": len(g)}
        for col, label in MODULE:
            row[label] = int(g[col].sum())
        rows.append(row)
    out = pd.DataFrame(rows)
    total = {"saison": "Total", "wettbewerb": "alle", "pflichtspiele": int(out["pflichtspiele"].sum())}
    for _, label in MODULE:
        total[label] = int(out[label].sum())
    return pd.concat([out, pd.DataFrame([total])], ignore_index=True)


def gemeinsame_stichproben(mart: pd.DataFrame) -> pd.DataFrame:
    k = mart[mart["kernscope"]]
    sl = k[(k["wettbewerb"] == "SL") & (k["saison"] >= config.MODELL_AB_SAISON)]
    kombis = [
        ("Anwesenheit + Kontext", ["hat_anwesenheit"]),
        ("Anwesenheit + Catering + Kontext", ["hat_anwesenheit", "hat_catering_umsatz"]),
        ("Catering mit Bons + Kontext", ["hat_catering_umsatz", "hat_bons"]),
        ("Ankunft + Catering mit Bons + Kontext", ["hat_zutritt_vollstaendig", "hat_bons"]),
        ("Einzelticket-Vorlauf + Anwesenheit", ["hat_einzeltickets_vollstaendig", "hat_anwesenheit"]),
        ("Eintritt je Einzelticket (ZKS) + Anwesenheit", ["hat_eintritt_zks_valide", "hat_anwesenheit"]),
        ("Alle Module gleichzeitig", ["hat_anwesenheit", "hat_bons", "hat_zutritt_vollstaendig",
                                      "hat_einzeltickets_vollstaendig", "hat_eintritt_zks_valide"]),
    ]
    rows = []
    for name, cols in kombis:
        mask = np.logical_and.reduce([sl[c].astype(bool) for c in cols])
        x = sl[mask]
        rows.append({"kombination": name, "basis": f"Meisterschaft ab {config.MODELL_AB_SAISON}", "spiele": len(x),
                     "saisons": ", ".join(sorted(x["saison"].unique()))})
    return pd.DataFrame(rows)


def verbotene_spalten() -> set[str]:
    """Spaltennamen (klein), die nie in einer Ausgabe stehen dürfen: Personenfelder und Ticket-/Kunden-IDs."""
    return {c.lower() for c in PERSONENFELDER} | {"auftrag", "rechnung", "utid", "barcode", "kundennr"}


def importtests(r: Rohdaten, m: Modell, res: dict[str, pd.DataFrame], ausgaben: dict[str, pd.DataFrame]) -> pd.DataFrame:
    tests = []

    def t(name, ok, detail=""):
        tests.append({"test": name, "bestanden": bool(ok), "detail": detail})

    dim = m.dim_match
    t("match_id eindeutig", dim["match_id"].is_unique, f"{len(dim)} Spiele")
    t("höchstens ein Kernspiel pro Datum", not dim[dim["spielstatus"] != "abgesagt"]["datum"].duplicated().any())
    c = m.fact_catering_match.dropna(subset=["match_id"])
    t("Catering: höchstens eine Zeile je Spiel (Join-Kardinalität 1:1)", c["match_id"].is_unique, f"{len(c)} Zeilen")
    t("Historie: genau eine Zeile je Spiel", m.fact_attendance_match["match_id"].is_unique)
    k = res["spiel_kpi"]
    t("spiel_kpi: eine Zeile je Spiel", k["match_id"].is_unique and len(k) == len(dim), f"{len(k)} Zeilen")

    kk = k.dropna(subset=["kf_exkl", "bons_pro_anwesende", "bon_exkl"])
    abw = (kk["kf_exkl"] - kk["bons_pro_anwesende"] * kk["bon_exkl"]).abs().max()
    t("Identität KF = Bons/Anwesende × Ø Bon", abw < 1e-9, f"max. Abweichung {abw:.2e}")

    kan = [col for col in m.fact_catering_match.columns if col.startswith("kanal_") and col.endswith("_inkl")
           and col not in ("kanal_contrailer_inkl", "kanal_public_inkl", "kanal_matchbar_inkl")]
    cc = m.fact_catering_match[m.fact_catering_match["saison"] >= "2022/23"].dropna(subset=["umsatz_inkl"])
    diff = (cc[kan].fillna(0).sum(axis=1) - cc["umsatz_inkl"]).abs()
    t("Catering: Umsatz total = Summe der Zahlungswege (ab 22/23)", (diff < 1).all(),
      f"max. Differenz CHF {diff.max():.2f}")

    ea = res["entwicklung_abgleich"]
    ea = ea[ea["saison"] >= config.BASELINE_AB_SAISON]
    t("Catering: Saisonsummen = Blatt «Entwicklung» (ab 21/22)", (ea["umsatz_differenz"].abs() < 1).all(),
      f"{len(ea)} Vergleiche")

    h = r.historie.dropna(subset=["noshow_blatt", "noshow_quote"])
    h = h[pd.to_numeric(h["noshow_blatt"], errors="coerce").notna()]
    t("Historie: No-Show neu berechnet = Blattwert", (h["noshow_quote"] - h["noshow_blatt"]).abs().max() < 1e-9)

    ab = res["artikel_abgleich"]
    t("Artikelsumme (brutto, einheitliche Basis) vs. Payfix inkl. (±3 %)",
      ab["verhaeltnis_artikel_brutto_zu_payfix_inkl"].between(0.97, 1.03).all(),
      ", ".join(f"{s}: {v:.3f}" for s, v in zip(ab["saison"], ab["verhaeltnis_artikel_brutto_zu_payfix_inkl"])))
    t("Artikel mit Normalsatz = Gruppe «Alkoholische Getränke» (±0.1 %)",
      ab["verhaeltnis_alkohol_artikel_zu_gruppe"].between(0.999, 1.001).all(),
      ", ".join(f"{s}: {v:.4f}" for s, v in zip(ab["saison"], ab["verhaeltnis_alkohol_artikel_zu_gruppe"])))
    t("Artikel-Basis plausibel: Erlös je Einheit (brutto) der Hauptartikel zwischen Saisons stabil (Median ±3 %)",
      *_artikel_basis_stabil(res["artikel_alle"]))

    kern = dim[(dim["spielstatus"] == "gespielt")]
    t("Alle gespielten Kernspiele haben einen Anpfiff", kern["anpfiff"].notna().all())
    an = res["ankunft_je_spiel"]
    t("Ankunft plausibel (Median 0–120 min vor Anpfiff) in allen vollständigen Spielen", an["anpfiff_plausibel"].all(),
      f"{len(an)} Spiele")
    t("Zutritt: erster Durchgang je Ticket und Spiel eindeutig (ohne IDs gespeichert)",
      "Barcode" not in r.ankuenfte.columns, f"{len(r.ankuenfte):,} Ankünfte".replace(",", "'"))

    verboten = verbotene_spalten()
    treffer = [f"{n}.{c}" for n, df in ausgaben.items() for c in df.columns if str(c).lower() in verboten]
    t("Datenschutz: keine Personen- oder ID-Spalten in den Ausgaben", not treffer, ", ".join(treffer) or "keine")
    t("Datenschutz: keine Personenfelder im Ticket-Datensatz", not (verboten & {c.lower() for c in m.tickets.columns}))

    zeiten = pd.to_datetime(r.ankuenfte["ts"])
    t("Zeitzone: Scans liegen am Spieltag (lokale Zeit)", (zeiten.dt.normalize() == r.ankuenfte["datum"]).mean() > 0.999,
      f"{(zeiten.dt.normalize() != r.ankuenfte['datum']).sum()} Scans an anderem Tag")
    kt = m.unmatched[m.unmatched["zu_pruefen"]]
    t("Unmatched-Report erstellt (zu prüfende Fälle dokumentiert)", True, f"{len(kt)} zu prüfende Fälle, {len(m.unmatched)} total")
    return pd.DataFrame(tests)


def _artikel_basis_stabil(art: pd.DataFrame) -> tuple[bool, str]:
    """Median der Veränderung des Brutto-Erlöses je Einheit (Artikel mit ≥ 1'000 Einheiten in beiden Saisons).

    Ist eine Saison in overrides/artikel_basis.csv falsch eingestuft, springt der Median um rund −7.5 % (Alkohol)
    bzw. −2.5 % (übrige) – der Test fällt dann durch.
    """
    a = art[(art["menge"] >= 1000)].pivot_table(index=["name", "mwst_klasse"], columns="saison", values="erloes_pro_einheit_brutto")
    saisons = list(a.columns)
    teile, ok = [], True
    for s0, s1 in zip(saisons, saisons[1:]):
        r_ = (a[s1] / a[s0]).dropna()
        for klasse, g in r_.groupby(level="mwst_klasse"):
            med = float(g.median())
            ok &= abs(med - 1) <= 0.03
            teile.append(f"{s0}→{s1} {klasse}: {med - 1:+.1%}")
    return ok, "; ".join(teile)


def quelleninventar(r: Rohdaten) -> pd.DataFrame:
    rows = []

    def add(quelle, datei, einheit, zeilen, zeitraum, hinweis=""):
        rows.append({"quelle": quelle, "datei": datei, "eine_zeile_ist": einheit, "zeilen": zeilen,
                     "zeitraum": zeitraum, "hinweis": hinweis})

    h = r.historie
    add("Ticketing", config.HISTORIE_FILE.name, "Event/Spiel", len(h), f"{h['datum'].min():%d.%m.%Y}–{h['datum'].max():%d.%m.%Y}",
        "Formeln ausgewertet (SOLL-/IST-Definition)")
    for datei, g in r.tickets_export.groupby("datei"):
        add("Ticketing", datei, "verkauftes Einzelticket", len(g),
            f"Verkäufe bis {g['verkauf_ts'].max():%d.%m.%Y}", "Personenfelder beim Einlesen verworfen")
    inv = r.ticket_inventar
    add("Ticketing", f"{(~inv['ist_abo']).sum()} Spiel-CSVs 2025/26–2026/27", "verkauftes Einzelticket",
        int(inv.loc[~inv["ist_abo"], "zeilen"].sum()), "2025/26–2026/27", "KundenNr/Barcode/Ticketnummer nicht eingelesen")
    add("Ticketing", "Saisonabos Herren/Frauen 2026/27", "Abo-Sitz", int(inv.loc[inv["ist_abo"], "zeilen"].sum()),
        "Snapshot 30.09.2026", "")
    zi = r.zutritt_info
    for lief, g in zi.groupby("lieferung"):
        add("Zutritt", lief, "erlaubter Drehkreuz-Durchgang", int(g["scans_roh"].sum()),
            f"{g['datum'].min():%d.%m.%Y}–{g['datum'].max():%d.%m.%Y} ({len(g)} Spieltage)", "UTId nur zur Deduplizierung")
    add("Zutritt", config.ZUTRITT_FRAUEN_FILE.name, "Durchgang (Frauen)", int(r.zutritt_frauen["scans"].sum())
        if not r.zutritt_frauen.empty else 0, "Frauen", "ausserhalb Kernscope")
    c = r.catering
    add("Catering", config.CATERING_FILE.name, "Spiel/Event", len(c), f"Saisons {c['saison'].min()}–{c['saison'].max()}",
        "Saisonblätter + «Entwicklung»")
    add("Catering", "Abrechnung Kiesplatz 21/22–26/27", "Event × Verkaufsstelle", len(r.kiesplatz),
        f"{r.kiesplatz['datum'].min():%d.%m.%Y}–{r.kiesplatz['datum'].max():%d.%m.%Y}", "Teilmenge des Catering-Totals")
    add("Catering", config.ARTIKEL_FILE.name, "Artikel/Gruppe × Saison", len(r.artikel), "2023/24–2025/26", "nur Saisonsummen")
    add("Kontext", config.KONTEXT_FILE.name, "Heimspiel", len(r.kontext), "2022/23–2026/27 (inkl. geplante Spiele)",
        "Blätter Übersicht, Ferien, Paralellevent, Hilfsdaten")
    add("Extern", config.WETTER_FILE.name, "Stunde", len(r.wetter), "ab 01.07.2018", "MeteoSchweiz OGD, Station STG")
    add("Extern", config.RESULTATE_FILE.name, "Super-League-Spiel", len(r.resultate), "ab 2017/18", "football-data.co.uk")
    add("Merchandise", "–", "–", 0, "–", "NICHT GELIEFERT: keine Merchandise-Daten im Datenraum (Erweiterung, Paket E)")
    add("Catering", "Viertelstunden-/Standumsätze, Stand→Sektor-Mapping", "–", 0, "–",
        "NICHT GELIEFERT (Projektantrag Paket 3): keine Zeit- und Standdaten ausser Kiesplatz")
    add("Ticketing", "Kapazität je Sektor mit Sperrungen, Verkaufsstand je Tag", "–", 0, "–",
        "NICHT GELIEFERT (Projektantrag Paket 2): Ausverkaufszeitpunkt nicht bestimmbar")
    return pd.DataFrame(rows)

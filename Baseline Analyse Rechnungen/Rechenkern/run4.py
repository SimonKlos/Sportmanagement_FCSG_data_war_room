"""Run 4 – Anstoss-Slot im Kontextmodell, Sensitivitäten 2021/22 (Covid) und ohne 2023/24 (D-041).

    python run4.py --daten "<Ordner 1. Daten FCSG>" --kontext "<Spielkontext_Tabelle_FCSG_5.xlsx>" --ausgabe <Ordner>

Liest dieselben Rohdaten wie run_all.py (nur lesend) und schreibt ausschliesslich Aggregate je Spiel bzw. Modell.
Die Phase-1-Ergebnisse (run_all.py) bleiben unverändert.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))

from fcsg import config  # noqa: E402
from fcsg.analysis import anstoss_slot, arrival, baseline, models  # noqa: E402
from fcsg.datamodel import baue_modell  # noqa: E402
from fcsg.log import logger, setup_logging  # noqa: E402
from fcsg.pipeline import lade_rohdaten  # noqa: E402
from fcsg.report import excel  # noqa: E402

import run_all  # noqa: E402  (Laufprotokoll wiederverwenden)

BLAETTER = [
    ("modellguete", "R1_Modellguete", "Modellgüte je Variante und Zielgrösse (R² innerhalb Saison, Leave-one-season-out)."),
    ("effekte", "R2_Effekte", "Effekte aller Variablen je Variante mit 95 %-KI (Anstoss-Slot vs. Samstag 17–19.59 Uhr)."),
    ("deskriptiv", "R3_Slot_Deskriptiv", "Spiele, KF und Anwesenheitsquote je Slot (Meisterschaft ab 22/23, unbereinigt)."),
    ("chf_baustein", "R4_CHF_Baustein", "Isolierter Konsum-Baustein je Spiel und Slot (nicht addieren)."),
    ("erwartung_je_spiel", "R5_Erwartung_je_Spiel", "Beobachtung vs. Erwartung je Spiel unter dem Slot-Modell (Leave-one-match-out)."),
    ("koeffizienten", "R6_Koeffizienten", "Koeffizienten des Slot-Modells (Grundlage Spielrechner)."),
]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--daten", type=Path, default=None)
    ap.add_argument("--kontext", type=Path, default=None)
    ap.add_argument("--ausgabe", type=Path, required=True)
    args = ap.parse_args()
    setup_logging()
    config.setze_datenpfade(args.daten, args.kontext)
    fehlend = config.fehlende_pflichteingaben()
    if fehlend:
        for eintrag in fehlend:
            logger.error("Nicht gefunden – %s", eintrag)
        return 1
    t0 = time.time()
    r = lade_rohdaten()
    m = baue_modell(r)
    res = baseline.baseline(r, m)
    k = res["spiel_kpi"]
    res.update(arrival.ankunft(r, m, k, res["scan_ist"]))
    d = models.modell_daten(k, m.dim_match_context, res["ankunft_je_spiel"])
    d = anstoss_slot.ergaenze_slot(d, r.kontext)

    out = anstoss_slot.schaetze(d)
    out["deskriptiv"] = anstoss_slot.deskriptiv(d)
    out["chf_baustein"] = anstoss_slot.chf_baustein(out["effekte"], d)

    ziel = args.ausgabe
    (ziel / "Tabellen").mkdir(parents=True, exist_ok=True)
    excel.schreibe_excel(ziel / "FCSG_Run4_Anstoss_Slot.xlsx", [(n, out[key], t) for key, n, t in BLAETTER])
    for key, _, _ in BLAETTER:
        out[key].to_csv(ziel / "Tabellen" / f"{key}.csv", index=False, encoding="utf-8-sig")
    info = run_all._laufinfo(m.datenstand, time.time() - t0)
    info["lauf"] = "Run 4 – Anstoss-Slot und Sensitivitäten (run4.py)"
    (ziel / "Laufprotokoll.json").write_text(json.dumps(info, indent=2, ensure_ascii=False), encoding="utf-8")
    logger.info("Run 4 fertig in %.0f s: %s", time.time() - t0, ziel)
    return 0


if __name__ == "__main__":
    sys.exit(main())

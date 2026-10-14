"""Vergleicht zwei Ergebnis-Arbeitsmappen der Phase 1 Blatt für Blatt (z.B. v1.0.1 gegen v1.1.0).

    python scripts/aenderungsprotokoll.py <alte .xlsx> <neue .xlsx> [--details BLATT ...]

Ausgabe: je Blatt «identisch» bzw. Anzahl geänderter Zellen, Zeilen und Spalten. Mit --details werden für die
genannten Blätter die geänderten Zellen gelistet. Das Skript liest nur Aggregate (Ergebnisdateien), keine Rohdaten.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd


def _gleich(a, b) -> bool:
    if pd.isna(a) and pd.isna(b):
        return True
    if isinstance(a, (int, float, np.number)) and isinstance(b, (int, float, np.number)):
        return bool(np.isclose(float(a), float(b), rtol=1e-9, atol=1e-9))
    return str(a) == str(b)


def vergleiche(alt: Path, neu: Path) -> tuple[pd.DataFrame, dict[str, pd.DataFrame]]:
    xa, xn = pd.ExcelFile(alt), pd.ExcelFile(neu)
    zeilen, details = [], {}
    for blatt in dict.fromkeys(xa.sheet_names + xn.sheet_names):
        if blatt not in xa.sheet_names or blatt not in xn.sheet_names:
            zeilen.append({"blatt": blatt, "status": "neu" if blatt in xn.sheet_names else "entfernt"})
            continue
        a, n = xa.parse(blatt), xn.parse(blatt)
        spalten_neu = [c for c in n.columns if c not in a.columns]
        spalten_weg = [c for c in a.columns if c not in n.columns]
        gemeinsam = [c for c in a.columns if c in n.columns]
        diffs = []
        for i in range(min(len(a), len(n))):
            for c in gemeinsam:
                if not _gleich(a.at[i, c], n.at[i, c]):
                    diffs.append({"zeile": i + 2, "spalte": c, "vorher": a.at[i, c], "nachher": n.at[i, c]})
        status = "identisch" if not (diffs or spalten_neu or spalten_weg or len(a) != len(n)) else "geändert"
        zeilen.append({"blatt": blatt, "status": status, "zeilen_vorher": len(a), "zeilen_nachher": len(n),
                       "zellen_geaendert": len(diffs), "spalten_neu": ", ".join(map(str, spalten_neu)),
                       "spalten_entfernt": ", ".join(map(str, spalten_weg))})
        details[blatt] = pd.DataFrame(diffs)
    return pd.DataFrame(zeilen), details


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("alt", type=Path)
    ap.add_argument("neu", type=Path)
    ap.add_argument("--details", nargs="*", default=[])
    args = ap.parse_args()
    uebersicht, details = vergleiche(args.alt, args.neu)
    with pd.option_context("display.width", 250, "display.max_rows", 500, "display.max_colwidth", 80):
        print(uebersicht.to_string(index=False))
        for blatt in args.details:
            print(f"\n=== {blatt}")
            print(details.get(blatt, pd.DataFrame()).to_string(index=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())

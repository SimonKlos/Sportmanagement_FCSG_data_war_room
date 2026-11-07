"""D-049d: Sind die Inhouse-Grossbestellungen mit hohem No-Show Sponsorentickets?

Nur Aggregate (Zählungen/Quoten), keine Käufer, keine Tarif-Rohbezeichnungen (nur Stichwort-Flags).
Zellen < 10 Tickets werden unterdrückt. Basis: valide ZKS-Spiele 2021/22–2022/23 wie Blatt B4.

    python scripts/grossbestellungen_noshow.py <Rechenkern-Ordner> <Ordner Rohdaten> <Spielkontext_Tabelle_FCSG_5.xlsx>

Ergebnis und Lesart: Quellen und interne Dokumentation/team/2026-11-07_grossbestellungen_noshow.md
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

KERN = Path(sys.argv[1])
sys.path.insert(0, str(KERN))
sys.dont_write_bytecode = True
from fcsg import config  # noqa: E402
from fcsg.analysis import attendance, baseline  # noqa: E402
from fcsg.datamodel import baue_modell  # noqa: E402
from fcsg.pipeline import lade_rohdaten  # noqa: E402

config.setze_datenpfade(sys.argv[2], sys.argv[3])
r = lade_rohdaten()
m = baue_modell(r)
k = baseline.baseline(r, m)["spiel_kpi"]
g = attendance._zks_spiele(m, k)
valide = set(g.loc[g["zks_valide"], "match_id"])
t = m.tickets[m.tickets["match_id"].isin(valide)].copy()
t["noshow"] = t["eintritt_ts"].isna()
t["preis"] = np.where(t["gratis"], "gratis", "bezahlt")
t["kanal_kurz"] = t["kanal"].str.replace(r" \(.*\)", "", regex=True)
t["best"] = pd.cut(t["bestellung_groesse"], [0, 9, 19, 49, 10_000], labels=["<10", "10–19", "20–49", "50+"]).astype(str)
MIN = 10


def tab(x, by):
    o = x.groupby(by, observed=True).agg(tickets=("noshow", "size"), noshows=("noshow", "sum"),
                                          spiele=("match_id", "nunique")).reset_index()
    o["noshow_quote"] = (o["noshows"] / o["tickets"]).round(3)
    o["anteil_tickets"] = (o["tickets"] / o["tickets"].sum()).round(3)
    o.loc[o["tickets"] < MIN, ["noshows", "noshow_quote"]] = np.nan
    return o


print("Spiele:", len(valide), "| Einzeltickets:", len(t), "| No-Shows:", int(t["noshow"].sum()))
gross = t[t["bestellung_groesse"] >= 10]
ih = gross[gross["kanal_kurz"].str.startswith("Inhouse")]
print("\nBestellungen ab 10 Tickets nach Kanal × Preis:")
print(tab(gross, ["kanal_kurz", "preis"]).to_string(index=False))
print("\nInhouse ab 10 Tickets nach Tarifgruppe × Preis:")
print(tab(ih, ["tarifgruppe", "preis"]).to_string(index=False))
print("\nTarifgruppe Sponsor/Dritte nach Kanal × Bestellgrösse:")
print(tab(t[t["tarifgruppe"] == "Sponsor/Dritte"], ["kanal_kurz", "best"]).to_string(index=False))
print("\nInhouse ab 10 nach Bestellgrösse:")
print(tab(ih, ["best", "preis"]).to_string(index=False))
print("\nInhouse ab 10 nach Tribüne:")
print(tab(ih, ["tribuene"]).to_string(index=False))
print("\nInhouse ab 10: Vorlauf (Tage vor Spiel), Median und Quartile:",
      ih["vorlauf_tage"].quantile([.25, .5, .75]).round(1).tolist())
je_spiel = ih.groupby("match_id").size().sort_values(ascending=False)
print("Inhouse ab 10: Anteil Tickets in den 5 grössten Spielen:", round(je_spiel.head(5).sum() / je_spiel.sum(), 3),
      "| Spiele mit Inhouse-Grossbestellungen:", len(je_spiel))
best_n = ih.groupby(["match_id", "bestellung_groesse"]).ngroups
print("Anzahl Inhouse-Grossbestellungen (Spiel × Grösse, Näherung):", best_n)

# Stichwort-Flags auf Tarif-Rohbezeichnung, ohne die Bezeichnungen auszugeben
tarif_col = next((c for c in ("tarif", "tarif_roh", "tarifname") if c in ih.columns), None)
print("\nTarif-Rohspalte:", tarif_col)
if tarif_col:
    s = ih[tarif_col].fillna("").str.lower()
    flags = {"sponsor/partner": "sponsor|partner", "firma/business": "firm|business|vip|unternehm",
             "gruppe/verein/schule": "grupp|verein|schul|klasse|club|jugend", "gratis/frei/promo": "grati|frei|promo|einlad",
             "mitarbeit/staff": "mitarb|staff|personal"}
    for name, pat in flags.items():
        x = ih[s.str.contains(pat, regex=True)]
        q = round(x["noshow"].mean(), 3) if len(x) >= MIN else None
        print(f"  {name:22s} tickets={len(x):6d} anteil={len(x)/len(ih):.3f} noshow={q}")
    print("  Anzahl verschiedener Tarife in Inhouse ab 10:", s.nunique())

print("\n=== Ohne Gästesektor B4 ===")
ohne = ih[ih["tribuene"] != "B4 (Gäste)"]
print("Inhouse ab 10 ohne B4: tickets", len(ohne), "noshow", round(ohne["noshow"].mean(), 3),
      "| Anteil an allen Einzel-No-Shows:", round(ohne["noshow"].sum() / t["noshow"].sum(), 3),
      "| B4-Anteil an allen Einzel-No-Shows:", round(ih.loc[ih["tribuene"] == "B4 (Gäste)", "noshow"].sum() / t["noshow"].sum(), 3))
print(tab(ohne, ["tarifgruppe", "preis"]).to_string(index=False))
print(tab(ohne, ["best", "preis"]).to_string(index=False))
b4 = t[t["tribuene"] == "B4 (Gäste)"]
print("\nGästesektor B4 gesamt nach Kanal × Bestellgrösse:")
print(tab(b4, ["kanal_kurz", "best"]).to_string(index=False))

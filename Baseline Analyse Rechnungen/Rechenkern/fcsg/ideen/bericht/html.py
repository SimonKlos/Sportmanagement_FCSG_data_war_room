"""HTML-Dossier «Ideen-Grundlage» (offline, Grafiken eingebettet, druckfähig) und optionale PDF-Ausgabe via Chrome/Edge."""
from __future__ import annotations

import base64
import html as _h
import platform
import shutil
import subprocess
from pathlib import Path

import numpy as np
import pandas as pd

from ... import __version__
from ..chancen import reto_zu_hoch
from ..fmt import dez, p, pct, z

CSS = """
:root{--ink:#0b0b0b;--ink2:#52514e;--muted:#898781;--line:#e1e0d9;--page:#f9f9f7;--surface:#ffffff;--accent:#0B6E4F;
--accent-weak:#e8f3ee;--note:#fff4c2;--guard:#f3f1ec;--blue:#2a78d6;--orange:#eb6834}
*{box-sizing:border-box}
html{color-scheme:light}
body{margin:0;background:var(--page);color:var(--ink);font:15px/1.55 system-ui,-apple-system,"Segoe UI","Helvetica Neue",Arial,sans-serif;
-webkit-font-smoothing:antialiased}
main{max-width:1000px;margin:0 auto;padding:28px 20px 60px}
header.titel{background:var(--surface);border:1px solid var(--line);border-top:6px solid var(--accent);border-radius:12px;padding:28px 30px;margin-bottom:26px}
header.titel h1{margin:0 0 6px;font-size:30px;line-height:1.15;letter-spacing:-.01em}
header.titel .unter{font-size:17px;color:var(--ink2);margin:0 0 14px}
.meta{font-size:13px;color:var(--ink2)}
.vertraulich{display:inline-block;margin-top:12px;background:var(--guard);border-radius:6px;padding:4px 10px;font-size:12.5px;color:var(--ink2)}
nav.toc{background:var(--surface);border:1px solid var(--line);border-radius:12px;padding:16px 22px;margin-bottom:26px;font-size:14px}
nav.toc ol{margin:6px 0 0;padding-left:20px;columns:2;column-gap:30px}
nav.toc a{color:var(--accent);text-decoration:none}
section{margin:0 0 34px}
h2{font-size:22px;margin:0 0 12px;padding-top:6px;border-bottom:2px solid var(--accent);padding-bottom:6px}
h3{font-size:17px;margin:20px 0 8px}
p{margin:0 0 10px}
.lead{font-size:16px;color:var(--ink2)}
.schritte{counter-reset:s;list-style:none;padding:0;margin:0 0 14px;display:grid;grid-template-columns:repeat(auto-fit,minmax(170px,1fr));gap:10px}
.schritte li{background:var(--surface);border:1px solid var(--line);border-radius:10px;padding:12px 14px 12px 46px;position:relative;font-size:14px}
.schritte li::before{counter-increment:s;content:counter(s);position:absolute;left:12px;top:11px;width:24px;height:24px;border-radius:50%;
background:var(--accent);color:#fff;font-weight:700;text-align:center;line-height:24px;font-size:13px}
.box{border-radius:10px;padding:14px 16px;margin:12px 0}
.box.leitplanke{background:var(--guard)}
.box.hinweis{background:var(--note)}
.box.akzent{background:var(--accent-weak)}
.box h4{margin:0 0 6px;font-size:14px;text-transform:uppercase;letter-spacing:.04em;color:var(--ink2)}
.box ul{margin:0;padding-left:18px}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:12px}
.befund{background:var(--surface);border:1px solid var(--line);border-radius:10px;padding:14px 16px}
.befund .thema{font-size:12px;text-transform:uppercase;letter-spacing:.05em;color:var(--accent);font-weight:700}
.befund .kern{font-size:16px;font-weight:700;margin:4px 0 6px;line-height:1.3}
.befund .detail{font-size:13.5px;color:var(--ink2)}
.befund .fund{font-size:12px;color:var(--muted);margin-top:6px}
table{border-collapse:collapse;width:100%;font-size:13px;margin:8px 0 14px;background:var(--surface)}
th,td{border-bottom:1px solid var(--line);padding:6px 8px;text-align:left;vertical-align:top}
th{background:var(--accent);color:#fff;font-weight:600;font-size:12.5px}
td.n{text-align:right;font-variant-numeric:tabular-nums;white-space:nowrap}
tr:nth-child(even) td{background:#fafaf8}
figure{margin:12px 0 16px;background:var(--surface);border:1px solid var(--line);border-radius:10px;padding:12px}
figure img{width:100%;height:auto;display:block}
figcaption{font-size:13px;color:var(--ink2);margin-top:8px}
figcaption .quelle{color:var(--muted)}
.karte{background:var(--surface);border:1px solid var(--line);border-radius:14px;padding:20px 22px;margin:0 0 26px}
.karte .kopf{display:flex;gap:14px;align-items:baseline;border-bottom:1px solid var(--line);padding-bottom:8px;margin-bottom:10px}
.karte .nr{background:var(--accent);color:#fff;border-radius:8px;padding:2px 10px;font-weight:700;font-size:15px}
.karte .treiber{color:var(--muted);font-size:13px;margin-left:auto}
.karte h3{margin:0;font-size:20px}
.kernzahl{font-size:19px;font-weight:700;color:var(--accent);line-height:1.35;margin:6px 0 10px}
.badges{display:flex;flex-wrap:wrap;gap:8px;margin:8px 0 12px}
.badge{border:1px solid var(--line);border-radius:999px;padding:3px 10px;font-size:12.5px;background:#fafaf8}
.badge b{font-weight:700}
.dots{letter-spacing:1px}
ol.fragen{margin:6px 0 0;padding-left:22px}
ol.fragen li{margin:0 0 6px;font-weight:600}
.lp{width:auto}
.lp td:first-child{font-weight:600;white-space:nowrap}
.klein{font-size:12.5px;color:var(--muted)}
.reto{background:var(--surface);border:1px solid var(--line);border-radius:10px;padding:12px 16px;margin:0 0 10px}
.reto .kopf{display:flex;gap:10px;align-items:baseline;flex-wrap:wrap}
.reto .nr{background:var(--ink2);color:#fff;border-radius:6px;padding:1px 8px;font-weight:700;font-size:13px}
.reto .titel{font-weight:700;font-size:15px}
.reto .urteil{margin-left:auto;background:var(--accent-weak);color:var(--accent);border-radius:999px;padding:2px 10px;font-size:12.5px;font-weight:600}
.reto p{margin:6px 0 0;font-size:13.5px}
footer{border-top:1px solid var(--line);padding-top:12px;font-size:12.5px;color:var(--muted)}
@media (max-width:640px){nav.toc ol{columns:1}.karte .kopf{flex-wrap:wrap}.karte .treiber{margin-left:0}header.titel h1{font-size:24px}}
@media print{body{background:#fff;font-size:12.5px}main{max-width:none;padding:0}nav.toc{display:none}
section.neu{break-before:page}.karte{break-inside:auto;border:none;padding:0}.befund,figure,table,.box{break-inside:avoid}
header.titel{border:none;padding:0}.befund{padding:8px 10px}.befund .kern{font-size:13.5px}.befund .detail{font-size:11.5px}
.grid{gap:8px}.reto{break-inside:avoid}@page{size:A4;margin:14mm 12mm}}
"""

PUNKTE = {"stark": "●●●", "mittel": "●●○", "schwach": "●○○", "hoch": "●●●", "gering": "●○○"}


def esc(x) -> str:
    return _h.escape("" if x is None or (isinstance(x, float) and np.isnan(x)) else str(x))


def _bild(ordner: Path, datei: str) -> str:
    pfad = ordner / datei
    if not pfad.exists():
        return ""
    return "data:image/png;base64," + base64.b64encode(pfad.read_bytes()).decode("ascii")


def figur(ordner: Path, grafiken: pd.DataFrame, datei: str) -> str:
    g = grafiken[grafiken["datei"] == datei]
    if g.empty:
        return ""
    r = g.iloc[0]
    return (f'<figure><img alt="{esc(r["titel"])}" src="{_bild(ordner, datei)}">'
            f'<figcaption><b>{esc(r["titel"])}.</b> {esc(r["aussage"])} <span class="quelle">Daten: Excel-Blatt {esc(r["tabelle_im_excel"])}.'
            f"</span></figcaption></figure>")


def _zahl(v, spalte: str) -> str:
    if v is None or (isinstance(v, float) and np.isnan(v)):
        return "–"
    if isinstance(v, (bool, np.bool_)):
        return "ja" if v else "nein"
    if isinstance(v, (int, np.integer)):
        return z(v)
    if isinstance(v, (float, np.floating)):
        s = spalte.lower()
        if any(k in s for k in ("anteil", "quote", "abdeckung", "wiederbesetzung", "je_platz", "anwesenheit")):
            return p(v, 1)
        if s.endswith("_pct") or "effekt" in s or s.startswith("ki9"):
            return pct(v, 1)
        if any(k in s for k in ("chf", "umsatz", "erloes")):
            return z(v)
        if abs(v) >= 100:
            return z(v)
        return dez(v, 2)
    if isinstance(v, pd.Timestamp):
        return f"{v:%d.%m.%Y}"
    return esc(v)


def tabelle(df: pd.DataFrame, spalten: dict[str, str], zahlen: tuple[str, ...] = ()) -> str:
    kopf = "".join(f"<th>{esc(t)}</th>" for t in spalten.values())
    zeilen = []
    for _, r in df.iterrows():
        zellen = []
        for c in spalten:
            v = r.get(c)
            ist_zahl = c in zahlen or isinstance(v, (int, float, np.integer, np.floating)) and not isinstance(v, (bool, np.bool_))
            zellen.append(f'<td class="n">{_zahl(v, c)}</td>' if ist_zahl else f"<td>{_zahl(v, c)}</td>")
        zeilen.append("<tr>" + "".join(zellen) + "</tr>")
    return f"<table><thead><tr>{kopf}</tr></thead><tbody>{''.join(zeilen)}</tbody></table>"


def _karte(f, ordner: Path, grafiken: pd.DataFrame) -> str:
    befund = "".join(f"<li>{esc(b)}</li>" for b in f.befund)
    lp = "".join(f"<tr><td>{esc(k)}</td><td>{esc(v)}</td></tr>" for k, v in f.leitplanken.items())
    fragen = "".join(f"<li>{esc(q)}</li>" for q in f.leitfragen)
    warn = f'<div class="box hinweis"><b>Achtung:</b> {esc(f.warnhinweis)}</div>' if f.warnhinweis else ""
    return f"""
<article class="karte" id="cf{f.nr}">
  <div class="kopf"><span class="nr">{f.nr}</span><h3>{esc(f.titel)}</h3><span class="treiber">{esc(f.treiber)}</span></div>
  <div class="kernzahl">{esc(f.kernzahl)}</div>
  <div class="badges">
    <span class="badge">Evidenz <b>{esc(f.evidenz)}</b> <span class="dots">{PUNKTE.get(f.evidenz, '')}</span></span>
    <span class="badge">Steuerbar durch Club <b>{esc(f.steuerbarkeit)}</b> <span class="dots">{PUNKTE.get(f.steuerbarkeit, '')}</span></span>
    <span class="badge">Reichweite: {esc(f.reichweite)}</span>
    <span class="badge">Daten: {esc(f.datenreife)}</span>
  </div>
  <h4>Was die Daten zeigen</h4>
  <ul>{befund}</ul>
  <p class="klein">Evidenz: {esc(f.evidenz_begruendung)}</p>
  {figur(ordner, grafiken, f.grafik)}
  <div class="box akzent"><h4>Hebel-Arithmetik (isoliert, nicht addieren)</h4><p>{esc(f.hebel_arithmetik)}</p></div>
  <div class="box leitplanke"><h4>Clubhebel und Leitplanken</h4><p><b>Clubhebel:</b> {esc(f.clubhebel)}</p>
    <table class="lp"><tbody>{lp}</tbody></table></div>
  {warn}
  <h4>Leitfragen für die Ideenfindung</h4>
  <ol class="fragen">{fragen}</ol>
  <p><b>So liesse sich ein Pilot messen:</b> {esc(f.pilot_messung)}</p>
  <p><b>Datenlücke:</b> {esc(f.datenluecke)}</p>
  <p class="klein">Tabellen im Excel: {esc(f.quellen)}</p>
</article>"""


def seite(e: dict, kz: dict, felder: list, ordner: Path) -> str:
    g = e.get("grafiken_ideen", pd.DataFrame(columns=["datei", "titel", "aussage", "tabelle_im_excel"]))
    kb = e["kernbefunde"]
    befunde = "".join(
        f'<div class="befund"><div class="thema">{esc(r["thema"])}</div><div class="kern">{esc(r["befund"])}</div>'
        f'<div class="detail">{esc(r["detail"])}</div><div class="fund">{esc(r["fundstelle"])}</div></div>' for _, r in kb.iterrows())
    fw = e["faustwerte"]
    fw26 = fw[fw["basis"] == "2025/26"].copy()
    fw26["phi_txt"] = fw26["phi"].map(lambda v: "–" if pd.isna(v) else f"{v:.1f}")
    nk = e["noshow_kosten"]
    cf = e["chancenfelder"]
    ueberblick = tabelle(cf.rename(columns={"chancenfeld": "titel"}),
                         {"nr": "Nr.", "titel": "Chancenfeld", "treiber": "Treiber", "evidenz": "Evidenz", "steuerbarkeit": "Steuerbarkeit",
                          "reichweite": "Reichweite", "datenreife": "Datenreife"})
    karten = "".join(_karte(f, ordner, g) for f in felder)
    rc = e["reto_ideen_check"]
    reto = "".join(
        f'<div class="reto"><div class="kopf"><span class="nr">{int(r["nr"])}</span><span class="titel">{esc(r["idee_reto"])}</span>'
        f'<span class="urteil">{esc(r["einschaetzung_datensicht"])}</span></div>'
        f'<p><b>Hypothese:</b> {esc(r["hypothese"])}</p><p><b>Vortest mit den echten Daten:</b> {esc(r["vortest_mit_daten"])}</p>'
        f'<p class="klein">Daten heute: {esc(r["datenlage_heute"])} · Rechenbasis: {esc(r["korrigierte_rechenbasis"])} · '
        f'Leitplanken: {esc(r["leitplanken"])} · Fundstelle: {esc(r["fundstelle"])}</p></div>' for _, r in rc.iterrows())
    da = tabelle(e["datenanfragen"], {"prioritaet": "Prio", "datenanfrage": "Datenanfrage", "schaltet_frei": "schaltet frei",
                                      "chancenfelder": "Chancenfelder", "hinweis": "Hinweis"})
    aend = e.get("phase1_aenderungen")
    erratum = ""
    if isinstance(aend, pd.DataFrame) and len(aend):
        erratum = tabelle(aend, {"bereich": "Bereich", "aenderung": "Was war falsch / was gilt neu", "vorher_v1_0_1": "vorher (v1.0.1)",
                                 "nachher_v1_1_0": "nachher (v1.1.0)"})
    qa = e.get("qa_ideen", pd.DataFrame())
    qa_txt = f"{int(qa['bestanden'].sum())} von {len(qa)} automatisierten Prüfungen bestanden" if len(qa) else "–"
    vertiefung = "".join(figur(ordner, g, d) for d in ("abb_i03_tribuenen.png", "abb_i05_spieltypen.png", "abb_i08_einlass.png",
                                                       "abb_i10_warenkorb.png", "abb_i11_preis_menge.png", "abb_i12_alkohol_validierung.png",
                                                       "abb_i14_mobiler_verkauf.png"))
    toc = "".join(f'<li><a href="#{a}">{esc(t)}</a></li>' for a, t in [
        ("lesehilfe", "So nutzt ihr dieses Dossier"), ("kernbefunde", "Das Wichtigste in 12 Befunden"),
        ("rechengrundlage", "Rechengrundlage (korrigierte Faustwerte)"), ("chancenfelder", "Neun Chancenfelder"),
        ("reto", "Retos 12 Ideen im Daten-Check"), ("vertiefung", "Weitere Analysen"), ("erratum", "Korrekturen in Phase 1"),
        ("daten", "Datenanfragen an den FCSG"), ("methodik", "Methodik, Definitionen, Grenzen")])
    return f"""<!doctype html>
<html lang="de"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Ideen-Grundlage FCSG</title><style>{CSS}</style></head>
<body><main>
<header class="titel">
  <h1>Ideen-Grundlage «Untapped Business»</h1>
  <p class="unter">Vertiefte Datenanalyse für die Ideenfindung – FC St.Gallen 1879 · für Simon und Reto</p>
  <div class="meta">Datenauswertung Ralf Stoffel · Version {esc(__version__)} · Daten bis {esc(kz.get('datenstand', '12.09.2026'))} ·
  Meisterschaft der Herren im Berit Sitterstadion, Basis 2025/26 · alle CHF-Werte Catering-Umsatz exkl. MwSt, sofern nicht anders angegeben</div>
  <div class="vertraulich">Vertraulich – nur Projektgruppe und Datenraum (NDA). Nur Aggregate, keine Personendaten.</div>
</header>
<nav class="toc"><b>Inhalt</b><ol>{toc}</ol></nav>

<section id="lesehilfe">
<h2>So nutzt ihr dieses Dossier</h2>
<p class="lead">Dieses Dossier liefert keine fertigen Ideen. Es zeigt, wo die Daten auf ungenutzten Umsatz hindeuten, wie belastbar das ist
und welche Fragen eine gute Idee beantworten muss. Die Ideen entwickelt ihr.</p>
<ol class="schritte">
<li><b>Kernbefunde lesen</b> – 12 Befunde, je mit Zahl und Fundstelle.</li>
<li><b>Chancenfeld wählen</b> – 9 Felder mit Evidenz, Steuerbarkeit und Datenlage.</li>
<li><b>Leitfragen nutzen</b> – «Wie könnten wir …?» als Startpunkt im Workshop.</li>
<li><b>Grob beziffern</b> – Excel-Blatt <i>Szenarien</i>: Hebel wählen, Annahme begründen.</li>
<li><b>Steckbrief füllen</b> – Leitplanken, Pilot-Messung, Datenbedarf (Excel-Blatt <i>Ideen_Steckbrief</i>).</li>
</ol>
<div class="box leitplanke"><h4>Leitplanken (verbindlich)</h4><ul>
<li>Kein Dynamic Pricing, Kapazität fix, kein Stadionausbau, keine Hospitality (Projektantrag, Arbeitsauftrag Simon).</li>
<li>Keine Personensegmentierung: nur Spiel, Sektor, Tarif, Kanal – aggregiert, Zellen unter 10 unterdrückt.</li>
<li>Umsatz ist nicht Ertrag: CHF-Werte sind Caterer-Umsatz; Club-Anteil und Kosten sind unbekannt.</li>
<li>Hebel und Lücken werden nie summiert. Rechenwerte sind isolierte Bausteine, keine Potenzialversprechen.</li>
<li>Zusammenhänge sind keine Kausalität. «Nicht belastbar» ist ein zulässiges Ergebnis.</li>
</ul></div>
</section>

<section id="kernbefunde" class="neu">
<h2>Das Wichtigste in 12 Befunden</h2>
<div class="grid">{befunde}</div>
</section>

<section id="rechengrundlage" class="neu">
<h2>Rechengrundlage: korrigierte Faustwerte</h2>
<p>Retos Ideenpapier rechnet mit 18'000 Anwesenden je Spiel. Tatsächlich sind es {z(kz['b_public_netto_mittel'])} Public-Anwesende
(KF-Nenner; IST inkl. VIP und Gäste {z(kz['b_ist_mittel'])}). Damit sind Retos Hebelwerte {reto_zu_hoch(kz)} zu hoch (bei φ = 1).
Die Tabelle zeigt die isolierten Rechenwerte nach Simons Arbeitsauftrag (§12) für die Saison 2025/26.</p>
{figur(ordner, g, "abb_i01_faustwerte.png")}
{tabelle(fw26, {"hebel": "Hebel", "phi_txt": "φ", "zusatz_menge_je_spiel": "Zusatzmenge je Spiel", "chf_pro_spiel": "CHF je Spiel",
                "chf_pro_saison": "CHF je Saison", "formel": "Formel"}, zahlen=("zusatz_menge_je_spiel", "chf_pro_spiel", "chf_pro_saison"))}
<div class="box hinweis"><h4>φ – der Grenz-Anwesende</h4><p>φ ist der Konsum eines zusätzlichen Anwesenden relativ zum Durchschnitt. Die Daten
zeigen eine Elastizität des Umsatzes auf die Anwesenden von {dez(kz['phi'])} (95 %-KI {dez(kz['phi_lo'])}–{dez(kz['phi_hi'])}): zusätzliche
Besucher konsumieren im Schnitt etwa gleich viel. Das ist ein Zusammenhang über Spiele, kein Kausalnachweis – deshalb rechnen wir mit
φ = 0.6 / 0.8 / 1.0.</p></div>
<h3>Was kostet ein leerer Platz?</h3>
<p>Der Ticketerlös ist bereits verbucht. Ein leerer Platz kostet Konsum (φ × KF = CHF {dez(0.6 * kz['b_kf_exkl'])}–{dez(kz['b_kf_exkl'])})
und Stimmung. Entscheidend ist der Unterschied zwischen <b>Aktivieren</b> (der Inhaber kommt – wirkt in jedem Spiel) und <b>Weiterverkaufen</b>
(Zweitmarkt – bringt nur dann zusätzliche Besucher, wenn die Nachfrage die freien Plätze übersteigt, also bei ausverkauften Spielen oder Sektoren).</p>
{tabelle(nk, {"basis": "Basis", "spieltyp": "Spiele", "spiele_je_saison": "Spiele je Saison", "leere_bezahlte_plaetze_je_saison": "leere Plätze je Saison",
              "leere_plaetze_je_spiel": "je Spiel", "noshow_quote": "No-Show"})}
</section>

<section id="chancenfelder" class="neu">
<h2>Neun Chancenfelder</h2>
<p>Ordinale Einordnung ohne Punkte und ohne Summe. Evidenz: wie gut belegt; Steuerbarkeit: wie direkt der Club eingreifen kann;
Reichweite: wie viele Spiele betroffen sind; Datenreife: was heute schon messbar ist.</p>
{ueberblick}
{karten}
</section>

<section id="reto" class="neu">
<h2>Retos 12 Ideen im Daten-Check</h2>
<p>Jede Idee aus dem Ideenpapier (05.10.2026) wurde mit den echten Daten vorgetestet. Die Einschätzung ist eine Datensicht; die Auswahl
trifft die Gruppe.</p>
{reto}
</section>

<section id="vertiefung" class="neu">
<h2>Weitere Analysen</h2>
<p>Ergänzende Grafiken zu den Chancenfeldern. Alle Zahlen stehen im Excel (Blattname in der Bildunterschrift).</p>
{vertiefung}
</section>

<section id="erratum" class="neu">
<h2>Korrekturen in Phase 1 (Version 1.1.0)</h2>
<p>Bei der vertieften Analyse sind in der Phase-1-Auswertung zwei Fehler aufgefallen. Sie wurden in der Pipeline korrigiert, und die
Phase-1-Ergebnisse wurden neu erzeugt. Kontextmodelle und KPI sind nicht betroffen.</p>
{erratum}
</section>

<section id="daten" class="neu">
<h2>Datenanfragen, die Ideen freischalten</h2>
{da}
</section>

<section id="methodik" class="neu">
<h2>Methodik, Definitionen, Grenzen</h2>
<ul>
<li><b>Datenbasis:</b> Ticketing-Historie, Einzelticket-Exporte und -CSVs, Abo-Snapshot 30.09.2026, Drehkreuz-Zutritte (erster Scan je
Ticket), Public-Catering-Umsätze je Spiel, Kiesplatz-Abrechnungen, Artikelauswertung (Saisonsummen), Spielkontext-Tabelle,
MeteoSchweiz (Station St. Gallen) und Super-League-Resultate. Verknüpft über das Spieldatum.</li>
<li><b>Kennzahlen:</b> KF = Umsatz / Public-Anwesende = Bons je Anwesendem × Ø Bon; No-Show = 1 − IST/SOLL; Saisonwerte immer
Summe/Summe. Artikel einheitlich brutto (Basis je Saison in overrides/artikel_basis.csv).</li>
<li><b>Alkohol-Proxy:</b> Der Anteil des Normalsatz-Umsatzes am Kassenkanal Payfix (inkl./exkl. MwSt, Satz nach Spieldatum) nähert den Alkoholanteil
an. Er ist gültig ab 2023/24 und validiert gegen die Artikelauswertung (≤ {dez(kz['alk_val_maxdiff'], 1)} Pp.) und den Kiesplatz
(r = {dez(kz['alk_val_r'])}). Gedeutet werden Abweichungen innerhalb der Saison.</li>
<li><b>Modelle:</b> Gleiche Logik wie in Phase 1 – Saison-Effekte, sechs vorab festgelegte Kontextvariablen, robuste Standardfehler,
Leave-one-season-out und Vorzeichenstabilität. «Belastbar» = Intervall ohne 0 und stabil.
Der Frühindikator wurde mit Rolling Origin getestet (nur frühere Spiele im Training) und hat ein konform kalibriertes 80 %-Band.</li>
<li><b>Tribünen 2026/27:</b> Vergeben = Abos bis Anpfiff + Einzeltickets − Zweitmarkt; genutzt = Scans je Eingang (Eingang ≈ Tribüne,
bestätigt durch UEFA-Spiele). Abo-Anwesenheit als Bandbreite. Es ist eine Momentaufnahme aus 4 Sommerspielen; A und Hospitality sind
nicht identifizierbar.</li>
<li><b>Grenzen:</b> Keine Verbindung Ticket ↔ Bon (kein Konsum je Person, Sektor oder Ticket-Typ). Keine Kassen-Zeitstempel. Kein
Stand→Sektor-Mapping. Keine Kosten/Margen (DB). Keine Merchandise-Daten. Kleine Fallzahlen (≈ 19 Meisterschaftsspiele je Saison).</li>
<li><b>Qualitätssicherung:</b> {esc(qa_txt)}. Dazu gehören Datenschutz (keine ID-Spalten, kleine Zellen unterdrückt), Phase 1 unverändert durch die Ideen-Stufe,
Validierungen sowie die Prüfung der Excel-Formeln und der erzeugten Dateien. Details stehen im Excel-Blatt Q1_Qualitaetspruefung.</li>
<li><b>Reproduzierbar:</b> <code>python run_all.py</code> erzeugt Phase 1 und diese Ideen-Grundlage neu (Code im Datenraum, README).</li>
</ul>
</section>
<footer>FCSG «Untapped Business» · HSG Sportmanagement in der Praxis HS26 · Ideen-Grundlage v{esc(__version__)} · erzeugt mit
fcsg/ideen (Python). Quellen der öffentlichen Zusatzdaten: MeteoSchweiz (CC BY 4.0), football-data.co.uk.</footer>
</main></body></html>"""


def schreibe(pfad: Path, e: dict, kz: dict, felder: list, ordner: Path) -> Path:
    pfad.write_text(seite(e, kz, felder, ordner), encoding="utf-8")
    return pfad


def _browser() -> str | None:
    kandidaten = []
    if platform.system() == "Darwin":
        kandidaten += ["/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
                       "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
                       "/Applications/Chromium.app/Contents/MacOS/Chromium"]
    elif platform.system() == "Windows":
        kandidaten += [r"C:\Program Files\Google\Chrome\Application\chrome.exe", r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
                       r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe", r"C:\Program Files\Microsoft\Edge\Application\msedge.exe"]
    for k in kandidaten:
        if Path(k).exists():
            return k
    for name in ("google-chrome", "chromium", "chromium-browser", "msedge"):
        if shutil.which(name):
            return shutil.which(name)
    return None


def als_pdf(html_pfad: Path, pdf_pfad: Path) -> Path | None:
    """PDF über headless Chrome/Edge (falls installiert); sonst None (HTML im Browser drucken)."""
    b = _browser()
    if b is None:
        return None
    try:
        subprocess.run([b, "--headless=new", "--disable-gpu", "--no-pdf-header-footer", "--no-first-run", f"--print-to-pdf={pdf_pfad}",
                        html_pfad.resolve().as_uri()], check=True, capture_output=True, timeout=180)
    except (subprocess.SubprocessError, OSError):
        return None
    return pdf_pfad if pdf_pfad.exists() else None

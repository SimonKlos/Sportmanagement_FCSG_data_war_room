# Briefing-Arbeitsfassungen

Arbeitsfassungen der drei Quell-PDFs aus `docs/sources/`. Sie sind **strukturierte Auszüge mit
Seitenverweisen**, keine Ersatzquelle: Bei Unklarheit gilt das PDF. Eigene Einordnungen des Agenten
sind als «Einordnung» markiert und nicht quellengeprüft.

| Datei | Quelle | Dokumentstand | Fassung |
|---|---|---|---|
| `01_arbeitsauftrag_modellierung.md` | Arbeitsauftrag_Modellierung__Datenverknpfung__Kontextbereinigung.pdf | Arbeitsstand 08.10.2026 | v1 (10.10.2026) |
| `02_datenquellen_treiberbaum.md` | FCSG Datenquellen & Treiberbaum – Übersicht für Modellierungsauftrag.pdf | 08.10.2026, Spiele bis 12.09.2026 | v1 (10.10.2026) |
| `03_projektantrag.md` | Projektantrag_Untapped_Business_FCSG_2.pdf | 25.09.2026 | v1 (10.10.2026) |
| `10_synthese_widersprueche.md` | alle drei | – | v1 (10.10.2026) |

Seitenangaben «S. n» beziehen sich auf die physische PDF-Seite (1-basiert), die bei allen drei
Dateien mit der gedruckten Seitenzahl übereinstimmt.

## Extraktionsmethode (10.10.2026)

1. **Text:** `pdfplumber 0.11.10` / `pypdf 6.20.0` in der Projekt-venv, seitenweise. Alle drei PDFs
   sind textbasiert (eingebettete Schrift); **OCR war nicht nötig**. Tesseract ist nicht installiert
   und wurde nicht verwendet.
2. **Sichtprüfung:** Seiten mit Layoutproblemen wurden lokal gerendert (`pypdfium2`) bzw. als Bild
   angesehen und gegen den Text abgeglichen:
   - Datenquellen & Treiberbaum: S. 1–7 (alle Seiten)
   - Arbeitsauftrag: S. 4, 5, 8, 11, 12
   - Projektantrag: keine Sichtprüfung (reiner Fliesstext, keine Tabellen/Bilder erkannt)
3. Die Extraktion lief über ein externes Sprachmodell (Claude Code). Laut Projektregel ist das für
   Briefing-PDFs vorgesehen; die Briefings können dennoch vertraulich sein.

## Extraktionslücken und Korrekturen

| Quelle, Seite | Problem bei Textextraktion | Behandlung |
|---|---|---|
| Datenquellen S. 6 | Treiberbaum ist ein **Bild** (1 eingebettetes Bild, kein Text) | Per Sichtprüfung transkribiert (`02_…`, Abschnitt Treiberbaum). Farben/Strichart beschrieben, nicht pixelgenau. |
| Datenquellen S. 1–5 | Tabellenzellen spaltenweise vermischt | Tabellen per Sichtprüfung rekonstruiert |
| Arbeitsauftrag S. 4–5 | Tabellennamen (`fact_…`, `dim_…`) aus dem Satz gelöst | Per Sichtprüfung zugeordnet |
| Arbeitsauftrag S. 11–12 | Vorzeichen fehlen (`−1 Prozentpunkt No-Show`, `+0,1 …`, `+CHF 1 …`) | Per Sichtprüfung ergänzt |
| Arbeitsauftrag S. 1–11 | Nummerierung der Listen fehlt im Text | Nur auf S. 4, 8, 11 visuell bestätigt; sonst Reihenfolge wie im Text |
| Arbeitsauftrag S. 1 | Emoji-Symbole (📐, 🗂) | ohne Bedeutungsverlust weggelassen |
| Arbeitsauftrag S. 2, 3, 6–7, 9–10, 13 | nicht visuell geprüft | Fliesstext ohne erkannte Layoutprobleme; Restunsicherheit gering |

Hinweis: In den PDFs erwähnte Dokumente **«FCSG_Daten-Handbuch» (Excel-Spaltenwörterbuch)** und das
Diagramm **«Ankunftskurve nach Sektor»** liegen diesem Projekt **nicht** vor.

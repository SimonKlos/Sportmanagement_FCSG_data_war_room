# Fachliche Quellen (PDFs aus SharePoint)

Hier liegen die freigegebenen Briefing-PDFs. Sie sind fachlich massgeblich; die Arbeitsfassungen
unter `docs/briefing/` leiten sich davon ab. **Die PDFs werden nicht nach Git committet**
(`.gitignore`), weil sie vertrauliche Informationen enthalten können. `.gitignore` ist dabei
keine Zugriffssperre.

## Registrierte Dateien

Die Dateien wurden am 10.10.2026 vom Projektroot hierher verschoben; Originaldateinamen unverändert.

| Originaldateiname | Titel (PDF-Metadaten / S. 1) | Dokumentstand | Seiten | Bytes | SHA-256 (Präfix) |
|---|---|---|---|---|---|
| `Arbeitsauftrag_Modellierung__Datenverknpfung__Kontextbereinigung.pdf` | Arbeitsauftrag Modellierung – Datenverknüpfung & Kontextbereinigung | «Arbeitsstand 08.10.2026» (S. 1); PDF erstellt 08.10.2026 | 13 | 406 098 | `9E1F2B8F5477669A` |
| `FCSG Datenquellen & Treiberbaum – Übersicht für Modellierungsauftrag.pdf` | FCSG Datenquellen & Treiberbaum – Übersicht für Modellierungsauftrag | «Oct 8, 2026 · @Reto» (S. 1); «Stand der Analysen: 08.10.2026, Spiele bis 12.09.2026» (S. 7) | 7 | 398 093 | `0DD5125A4919C06B` |
| `Projektantrag_Untapped_Business_FCSG_2.pdf` | Projektantrag – Untapped Business (FC St.Gallen 1879) | 25.09.2026 (S. 1) | 2 | 39 829 | `A2851DE9CA2CD28B` |

Interner SharePoint-Ablagepfad: **nicht dokumentiert** (wurde nicht mitgeteilt; wird nicht erraten).

## Rangfolge bei Widersprüchen

Der Arbeitsauftrag (08.10.2026) erklärt selbst, dass Retos Datenquellen-Aufbereitung das frühere
hypothetische Daten-Zielbild ersetzt (Arbeitsauftrag S. 1). Arbeitshypothese daher:
**Arbeitsauftrag > Datenquellen & Treiberbaum > Projektantrag**. Diese Rangfolge ist eine
Arbeitsannahme und muss von den Projektverantwortlichen bestätigt werden
(siehe `docs/decisions.md`, D-002).

## Neue Fassungen

Neue PDF-Fassung mit Originalnamen hier ablegen, alte Fassung nicht überschreiben (Suffix ergänzen),
Tabelle oben aktualisieren und den Agenten bitten, die Arbeitsfassungen in `docs/briefing/`
nachzuführen. Der Agent liest nur lokal bereitgestellte Dateien; kein automatischer SharePoint-Zugriff.

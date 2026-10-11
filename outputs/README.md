# outputs/

Ein Unterordner pro Lauf.

| Ordner | Inhalt | Im Repo? |
|---|---|---|
| `run1_simon_2026-10-11/` | **Erste Baseline-Analyse auf echten Daten** (aggregiert, vorläufig). Eingefrorener Schnappschuss mit Bericht, Spieltabelle, Prüfprotokollen, Excel; Erklärung im `README.md` des Ordners | ja (privates Repo, D-024) |
| `<Lauf-ID>/` (z. B. `…_fixture_…`) | technische Läufe auf der künstlichen Fixture (`python -m fcsg.cli run --config config/project.example.yaml`) | nein |

Echte Analyse-Läufe (`python -m fcsg.cli analyze`) schreiben standardmässig in das `output_dir` der lokalen Config
(z. B. `C:\FCSG_Daten\outputs\`, D-015). Ergebnisse, die das Team teilen soll, werden bewusst als neuer Ordner
`runN_<name>_<datum>/` hierher kopiert und mit einem kurzen README versehen (Lauf-IDs, Befehle, Prüfstatus).

Jeder Laufordner enthält `manifest.json` (Lauf-ID, Zeitpunkt, Datenmodus, Versionen, Prüf- und Abdeckungsstatus),
die CSV-Artefakte, die Excel-Ausgabe (Werte, keine Formeln) und `readback_report.json` (Rückleseprüfung Excel ↔ CSV).

# config/

- `project.example.yaml` – Laufkonfiguration für die künstliche Fixture (versioniert).
- Eigene lokale Varianten als `*.local.yaml` anlegen; diese sind von Git ausgeschlossen.
- `project.local.yaml` – zeigt auf die echten Daten unter `C:/FCSG_Daten/raw` (D-015); Datenmodus `release_aggregates`
  (D-001 c), nur für `fcsg.cli prepare-data`.
- `reference/` – öffentliche Referenzdaten (Schulferien Stadt St.Gallen, D-021), versioniert; siehe `reference/README.md`.

Felder: `data_mode` (nur `synthetic_fixture` freigegeben), `input_dir`, `output_dir` (relativ zum Projektroot),
`timezone` (Standard `Europe/Zurich`).

Ein anderer Datenmodus wird von `fcsg.config.load_config` mit Fehler abgewiesen, bis Entscheid D-001
(`Quellen und interne Dokumentation/decisions.md`) gefallen ist. Echte Datenpfade gehören nie in versionierte Dateien.

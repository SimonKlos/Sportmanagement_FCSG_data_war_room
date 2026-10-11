"""FCSG Phase 1 – Analysepaket.

Stand 0.4.0: Bereinigung echter Daten (prepare), Baseline + Hypothesen (analyze); Fixture für technische Tests.
Echte Daten nur im Datenmodus ``release_aggregates`` (D-001 c); Fixture-Läufe im Modus
``synthetic_fixture`` (siehe ``fcsg.config``).
"""

__version__ = "0.4.0"

# Pflichtwert der Spalte ``data_origin`` in jeder Fixture-Zeile und Banner in jedem Output.
FIXTURE_MARKER = "SYNTHETIC_FIXTURE_NOT_CLUB_DATA"
FIXTURE_BANNER = (
    "KÜNSTLICHE TESTDATEN – KEINE FCSG-CLUBDATEN, KEINE CLUBRESULTATE. "
    "Nur technischer Funktionstest der Pipeline."
)

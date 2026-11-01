"""Zahlenformate für Texte (Schweizer Schreibweise: Apostroph als Tausendertrennzeichen, Minuszeichen «−»)."""
from __future__ import annotations

import math

import pandas as pd


def _leer(x) -> bool:
    return x is None or (isinstance(x, float) and math.isnan(x)) or (not isinstance(x, str) and pd.isna(x))


def _minus(s: str) -> str:
    return s.replace("-", "−")


def z(x, d: int = 0) -> str:
    """Zahl mit Tausender-Apostroph: 261924 → «261'924»."""
    if _leer(x):
        return "–"
    return _minus(f"{x:,.{d}f}".replace(",", "'"))


def chf(x, d: int = 0) -> str:
    return "–" if _leer(x) else f"CHF {z(x, d)}"


def chf_k(x) -> str:
    """Gerundet in Tausend: 48'812 → «CHF 49k»; ab 1 Mio. «CHF 1.02 Mio.»."""
    if _leer(x):
        return "–"
    if abs(x) >= 1e6:
        return _minus(f"CHF {x / 1e6:.2f} Mio.")
    return _minus(f"CHF {x / 1e3:,.0f}k".replace(",", "'"))


def p(x, d: int = 0) -> str:
    """Anteil als Prozent: 0.1813 → «18 %»."""
    return "–" if _leer(x) else _minus(f"{x * 100:.{d}f} %")


def pp(x, d: int = 1) -> str:
    """Prozentpunkte mit Vorzeichen (x bereits in Pp.)."""
    return "–" if _leer(x) else _minus(f"{x:+.{d}f} Pp.")


def pct(x, d: int = 1) -> str:
    """Veränderung in Prozent mit Vorzeichen (x bereits in %); auf null gerundete Werte als «±0»."""
    if _leer(x):
        return "–"
    if round(abs(x), d) == 0:
        return f"±{0:.{d}f} %"
    return _minus(f"{x:+.{d}f} %")


def ki(lo, hi, d: int = 1, einheit: str = "") -> str:
    if _leer(lo) or _leer(hi):
        return "–"
    return _minus(f"{lo:+.{d}f} bis {hi:+.{d}f}{einheit}")


def dez(x, d: int = 2) -> str:
    return "–" if _leer(x) else _minus(f"{x:.{d}f}")

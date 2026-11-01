"""Lädt alle Quellen in ein ``Rohdaten``-Objekt (eine Stelle für alle Einlese-Schritte)."""
from __future__ import annotations

import time

from .datamodel import Rohdaten
from .log import logger
from .sources import catering, extern, historie, kontext, tickets, zutritt


def lade_rohdaten() -> Rohdaten:
    t0 = time.time()
    hist = historie.lade_historie()
    cat, staende = catering.lade_public_catering()
    entw = catering.lade_entwicklung()
    kies = catering.lade_kiesplatz()
    art = catering.lade_artikel()
    tx = tickets.lade_einzeltickets_export()
    tc, abos, inv = tickets.lade_ticket_csvs()
    ank, zinfo = zutritt.lade_zutritt()
    zfr = zutritt.lade_zutritt_frauen()
    ktx = kontext.lade_kontext()
    kal = kontext.lade_kalender()
    wet = extern.lade_wetter_stunden()
    res = extern.lade_resultate()
    tab = extern.tabelle_vor_spielen(res)
    logger.info("Alle Quellen geladen (%.0f s)", time.time() - t0)
    return Rohdaten(historie=hist, catering=cat, catering_staende_2122=staende, entwicklung=entw, kiesplatz=kies,
                    artikel=art, tickets_export=tx, tickets_csv=tc, abos=abos, ticket_inventar=inv, ankuenfte=ank,
                    zutritt_info=zinfo, zutritt_frauen=zfr, kontext=ktx, kalender=kal, wetter=wet, resultate=res,
                    tabelle=tab)

# CLAUDE.md – FCSG Analyseprojekt

## Auftrag
Lies PROJECT_SETUP.md sowie die aus SharePoint heruntergeladenen PDFs zum Modellierungsauftrag und zu Datenquellen/Treiberbaum unter docs/sources/ vor fachlichen Änderungen. Die Projektverantwortlichen steuern den fachlichen Auftrag und sollen keinen Code schreiben müssen. Erkläre Entscheidungen auf Deutsch und übernimm technische Arbeiten selbst, soweit freigegeben. Die bereitgestellten PDFs sind die fachlichen Quellen. Erstelle daraus nachvollziehbare Arbeitsfassungen unter docs/briefing/ mit Quelle, Dokumentstand und Seitenverweisen. Fehlt eine PDF, benenne den Blocker; ersetze sie nicht durch vermutete Inhalte.

## Grenzen
Kein Datenupload, Git-Push, Remote-Repo, Codespaces, externe Freigabe, Systeminstallation oder Lizenzentscheidung ohne explizite Zustimmung. Kein Bypass der Berechtigungen. Lokaler Agent bedeutet nicht offline: keine echten Daten/Rohzeilen lesen oder in Toolausgaben zeigen, bevor zulässiger Datenmodus feststeht. .gitignore ist keine Zugriffssperre. Keine Tokens in Dateien oder Logs.

## Methodik
Steuerungsgrösse Phase 1 = Deckungsbeitrag (D-003); Umsatz brutto/netto bleibt Grundlage und Zwischengrösse; DB nur mit belegten Kosten-/Margendaten, keine Margen annehmen. Massnahmenquantifizierung später. Frauen-Daten ausserhalb Scope (D-016). Kein Dynamic Pricing, keine Hospitality/Erweiterung der Stadionkapazität. Eindeutige Spielebene; Faktentabellen vor Join aggregieren. Summenerhalt/Join-Kardinalität prüfen. SOLL/IST/Public-Netto und Brutto-/Nettoumsatz erst definieren. Missing nicht null; fehlender Scan nicht automatisch No-Show. Abo-Snapshot und Saisonartikel separat. Keine Merch-, Sektor-Konsum- oder Zeit-Konsumdaten erfinden. Keine Kausalität aus Korrelation oder realisierbares Potenzial aus Residuen. KF-, Bonsrate- und Bon-Lücken nicht addieren.

## Code und Dokumentation
Modulare Python-Logik, kurze erklärende Notebooks, reproduzierbare CLI/Tasks. README pro Hauptordner, Docstrings für zentrale Funktionen, Datendictionary und Entscheidungsliste. Deutsche Erklärungen; technische Namen Englisch. Inputschema und Fehlermeldungen ohne sensible Inhalte. Abhängigkeiten erst nach erfolgreichem Test fixieren.

## Umsetzung
Arbeite in kleinen end-to-end-Paketen. Starte mit künstlichen, markierten Fixtures für technische Tests. Keine Testdaten als echte Clubdaten berichten. Keine Code-Stubs oder TODO-Gerüste als fertig deklarieren. Jeden implementierten Schritt ausführen und prüfen; bei echten Daten erst Freigabe und Quellenverprobung. Fachliche Definitionen nicht stillschweigend ändern. Modellierung erst nach Baseline-Freigabe.

## Lieferung
Berichte geänderte Dateien, fachlichen Zweck, tatsächlich ausgeführte Befehle/Tests, tatsächliche Outputs, offene Einschränkungen und die fachlichen Prüfhandlungen. Lauf-ID/Versionen und Datenabdeckung dokumentieren. Excel nach Export zurücklesen und gegen Datenkern prüfen. Notebook-Ausgaben vor Versionskontrolle bereinigen; keine Daten oder lokale Pfade committen.

## Freigaben
Lesen/Schreiben/Tests im freigegebenen Codebereich können delegiert werden. Datenzugriff, fachliche Scopeänderung und externe Seiteneffekte brauchen separate Freigabe. Umfangreiche Änderungen zuerst kurz begründen, dann nach freigegebenem Paket tatsächlich umsetzen.

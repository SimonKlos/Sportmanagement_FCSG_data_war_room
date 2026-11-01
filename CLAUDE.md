# CLAUDE.md – FCSG Analyseprojekt

## Auftrag
Lies PROJECT_SETUP.md sowie die aus SharePoint heruntergeladenen PDFs zum Modellierungsauftrag und zu Datenquellen/Treiberbaum unter Quellen und interne Dokumentation/sources/ vor fachlichen Änderungen. Die Projektverantwortlichen steuern den fachlichen Auftrag und sollen keinen Code schreiben müssen. Erkläre Entscheidungen auf Deutsch und übernimm technische Arbeiten selbst, soweit freigegeben. Die bereitgestellten PDFs sind die fachlichen Quellen. Erstelle daraus nachvollziehbare Arbeitsfassungen unter Quellen und interne Dokumentation/briefing/ mit Quelle, Dokumentstand und Seitenverweisen. Fehlt eine PDF, benenne den Blocker; ersetze sie nicht durch vermutete Inhalte.

## Grenzen
Kein Datenupload, Git-Push, Remote-Repo, Codespaces, externe Freigabe, Systeminstallation oder Lizenzentscheidung ohne explizite Zustimmung. Kein Bypass der Berechtigungen. Lokaler Agent bedeutet nicht offline: keine echten Daten/Rohzeilen lesen oder in Toolausgaben zeigen, bevor zulässiger Datenmodus feststeht. .gitignore ist keine Zugriffssperre. Keine Tokens in Dateien oder Logs.

## Methodik
Steuerungsgrösse Phase 1 = Deckungsbeitrag (D-003); Umsatz brutto/netto bleibt Grundlage und Zwischengrösse; DB nur mit belegten Kosten-/Margendaten, keine Margen annehmen. Massnahmenquantifizierung später. Frauen-Daten ausserhalb Scope (D-016). Kein Dynamic Pricing, keine Hospitality/Erweiterung der Stadionkapazität. Eindeutige Spielebene; Faktentabellen vor Join aggregieren. Summenerhalt/Join-Kardinalität prüfen. SOLL/IST/Public-Netto und Brutto-/Nettoumsatz erst definieren. Missing nicht null; fehlender Scan nicht automatisch No-Show. Abo-Snapshot und Saisonartikel separat. Keine Merch-, Sektor-Konsum- oder Zeit-Konsumdaten erfinden. Keine Kausalität aus Korrelation oder realisierbares Potenzial aus Residuen. KF-, Bonsrate- und Bon-Lücken nicht addieren.

## Ausgabe- und Strukturregel – 01.11.2026 (D-042)
Quellen/Logs intern in `Quellen und interne Dokumentation`, Rechenstände in `Baseline Analyse Rechnungen`, externe Review-Unterlagen im separaten Root `Deliverables`. Historische Artefakte unverändert erhalten. Externe Fassungen ohne interne Personenvergleiche; Zahlen und Logik unverändert. Präsentation ausschliesslich als ausführlicher Folienleitfaden zur eigenen PPT-Erstellung durch Simon, **keine PPT/PPTX**.

## Aktueller Nachtrag – 01.11.2026
Phase-2-Massnahmen primär auf inkrementellen Umsatz prüfen (Simon, D-039), nicht DB. Catering-Systemumsatz exkl. MwSt. und Cluberlös trennen. 20 % Cateringbeteiligung nur unbestätigte Szenarioannahme (D-040), kein Default/Margennachweis; Vertragsbasis offen. Phase-1-Entscheid D-003 bleibt historisch bestehen. Kundenfranken-Definition bestätigt, Nenner-Mapping offen (D-038). Bons 2023/24 wegen System-/Gutscheinwechsel eingeschränkt vergleichbar: D-041 und Teamnotiz vor Verwendung lesen; kein bereits erfolgter Sensitivitätslauf.

## Code und Dokumentation
Zahlenbasis ist Ralfs Rechenkern unter ralf/ (D-028, aus ralf/ starten); src/fcsg bleibt für Bereinigung, Datenschutzprüfung, Tests und Gegenrechnung (fcsg.abgleich). Spielkontext-Tabelle nur Version 5 (D-034). Modulare Python-Logik, kurze erklärende Notebooks, reproduzierbare CLI/Tasks. README pro Hauptordner, Docstrings für zentrale Funktionen, Datendictionary und Entscheidungsliste. Deutsche Erklärungen; technische Namen Englisch. Inputschema und Fehlermeldungen ohne sensible Inhalte. Abhängigkeiten erst nach erfolgreichem Test fixieren. Jede fachliche oder methodische Festlegung (Definition, Hypothese, Abgrenzung, Annahme) als D-Eintrag in Quellen und interne Dokumentation/decisions.md erfassen, mit Datum, wer entschieden hat (Team oder Agent-Annahme) und Quelle; Agent-Annahmen bleiben offen bzw. Arbeitsannahme, bis das Team sie bestätigt (D-027). Jede grössere Änderung (neue Analyse, neuer Lauf, geänderte Definition, neue Abhängigkeit, geänderte Regel) erhält einen Eintrag in CHANGELOG.md.

## Umsetzung
Arbeite in kleinen end-to-end-Paketen. Starte mit künstlichen, markierten Fixtures für technische Tests. Keine Testdaten als echte Clubdaten berichten. Keine Code-Stubs oder TODO-Gerüste als fertig deklarieren. Jeden implementierten Schritt ausführen und prüfen; bei echten Daten erst Freigabe und Quellenverprobung. Fachliche Definitionen nicht stillschweigend ändern. Modellierung erst nach Baseline-Freigabe.

## Lieferung
Berichte geänderte Dateien, fachlichen Zweck, tatsächlich ausgeführte Befehle/Tests, tatsächliche Outputs, offene Einschränkungen und die fachlichen Prüfhandlungen. Lauf-ID/Versionen und Datenabdeckung dokumentieren. Excel nach Export zurücklesen und gegen Datenkern prüfen. Notebook-Ausgaben vor Versionskontrolle bereinigen; keine Daten oder lokale Pfade committen.

## Freigaben
Lesen/Schreiben/Tests im freigegebenen Codebereich können delegiert werden. Datenzugriff, fachliche Scopeänderung und externe Seiteneffekte brauchen separate Freigabe. Umfangreiche Änderungen zuerst kurz begründen, dann nach freigegebenem Paket tatsächlich umsetzen.

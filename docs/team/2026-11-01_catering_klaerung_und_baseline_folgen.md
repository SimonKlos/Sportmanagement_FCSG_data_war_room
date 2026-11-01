# Catering: Partnerantworten, Umsatzfokus und Folgen für die Baseline

Dokumentiert am 01.11.2026. Quelle: von Simon im Chat bereitgestellter Screenshot einer Klärungs-E-Mail mit roten Partnerantworten; E-Mail-Datum und Verfasser sind im Ausschnitt nicht erkennbar. Ergänzende Projektentscheide: Simon im selben Austausch. Keine Rohdaten oder Original-E-Mail ins Repo übernommen. Die fachlichen PDF-Originale sind in diesem Checkout nicht vorhanden; vorhandene Briefing-Arbeitsfassungen und Code wurden geprüft. Keine erneute Quellenverprobung gegen Rohdaten.

## 1. Antworten und verbleibende Fragen

- **Clubmodell:** Der Club erhält einen Prozentsatz des Catering-Umsatzes; Warenkosten trägt der Cateringpartner. Prozentsatz, Vertrags-Umsatzbasis, Abgrenzung je Bereich und allfällige variable Clubkosten sind nicht bestätigt. Warenkosten des Partners nicht als Clubkosten abziehen.
- **Catering-Abgaben:** Antwort «Welche Abrechnung meinst du?»; weiterhin offen. Dateiname, Blatt und konkrete Spalte/Abrechnung an den Partner zurückspielen. Keine Gleichsetzung mit Clubbeteiligung oder Kosten.
- **Kiesplatz 80/20:** Laut Partner steuerliche Sonderregelung für nichtalkoholische Lebensmittel: 80 % zu 2,6 %, 20 % zu 8,1 %. Keine Clubbeteiligung und keine gemessene Take-away-/Vor-Ort-Quote. Historische Gültigkeit/Steuersätze und betroffene Artikelbasis vor rückwirkender Anwendung klären. Keine pauschale Neuversteuerung aller Catering-Umsätze.
- **Kundenfranken:** Partner bestätigt die Umsatzbasis exkl. MwSt. für die Frage zum Referenzwert CHF 14.50. Definition: Catering-Umsatz exkl. MwSt. geteilt durch anwesende Zuschauer im Public-Bereich ohne VIP. Ob das konkrete Feld `Public Netto` dieser Abgrenzung durchgehend entspricht, bleibt zu verproben; SOLL/IST/Gäste/Personal/Freikarten sind damit nicht vollständig definiert. «Brutto exkl. MwSt.» nicht als eindeutige Fachbezeichnung verwenden.
- **Bons/Zahlungswege:** Partner bejaht, dass die Transaktionen die im Umsatz enthaltenen Zahlungswege umfassen. Gleichzeitig werden historische Einschränkungen genannt: Kassensystemwechsel zur Saison 2023/24, erst damit Erfassung der Transaktionszahl; Just Eat eingeführt im Oktober 2022; Gutscheine bis Ende 2023 nicht als Transaktionen gebucht, erst ab Januar 2024 systemseitig möglich und anfangs nicht reibungslos. Keine Bestätigung eines exakten Datums stabiler Vollständigkeit oder der historischen Just-Eat-Bonabdeckung.

## 2. Projektfestlegung Simon: Phase 2 auf Top-line

Alle Massnahmen in Phase 2 werden primär auf **inkrementellen Umsatz**, nicht auf Deckungsbeitrag, geprüft (D-039). MwSt.-Basis und Erlösempfänger müssen je Hebel ausdrücklich genannt werden. Für Catering primär zusätzlicher Public-Catering-Umsatz exkl. MwSt.; dieser ist nicht identisch mit zusätzlichem Cluberlös. Andere Umsatzarten nicht ohne Prüfung mit Catering-Systemumsatz zu einer «Club-Top-line» addieren. Überschneidungen zwischen Massnahmen nicht doppelt zählen; keine Kausalwirkung aus Baseline-Residualen ableiten.

**20 % Cateringbeteiligung** sind eine von Simon gesetzte, unbestätigte Szenarioannahme (D-040), keine Partnerbestätigung und keine gemessene Marge. Optionaler separater Szenarioausweis: zusätzlicher Cluberlös = zusätzlicher beteiligungsfähiger Catering-Umsatz × 0,20. Bis zur Klärung kann eine Netto-Basis nur explizite Rechenannahme sein, keine Aussage über den Vertrag. Primäre Umsatz-KPIs bleiben unskaliert; kein Deckungsbeitrag aus der Beteiligung ableiten. Satz, Basis und Geltungsbereich beim Partner nachfragen. Keine Änderung des Rechenkerns oder Übernahme als versteckter Default.

Die frühere Phase-1-Festlegung D-003 wird nicht rückwirkend als nie beschlossen dargestellt. D-029 wird durch den Umsatzfokus für Phase 2 präzisiert; offene Cluberlös-/Kostendaten bleiben offen. Dies ist keine Freigabe der bisherigen Modelle oder Baseline.

## 3. Muss die Baseline neu gerechnet werden?

**Kein vollständiger Neuimport nur aufgrund dieser Mail. Aber gezielte Bons-Sensitivität vor Freigabe/Weiterverwendung erforderlich.** Noch kein Neulauf erfolgt, keine Ergebnisänderung quantifiziert.

### Voraussichtlich keine numerische Änderung allein durch die Klarstellung

- `ralf/fcsg/sources/catering.py` berechnet `kf_exkl = umsatz_exkl / public_netto`; die bestätigte KF-Formel passt zur vorhandenen Implementierung. Der fachliche Nennerabgleich bleibt offen.
- Die bestehenden Umsatz-/KF-Werte und Ticketing-/Zutrittsaggregate werden durch die neue Information allein nicht rechnerisch geändert. Das ist ein Codebefund, kein erneuter Nachweis historischer Datenrichtigkeit.
- Steuerliche 80/20-Aufteilung nicht als Beteiligung behandeln. Bestehende Quell-Netto-/Bruttowerte nicht ohne belegten Fehler ersetzen.
- Die 20-%-Annahme betrifft nur eine optionale Cluberlös-Szenariospalte, nicht Umsatz-Baseline, Kundenfranken oder historische Bons.

### Fachlich relevant: Bonsrate und Durchschnittsbon

Unvollständige Bons bei enthaltenem Umsatz können Bons/Anwesendem nach unten und Umsatz/Bon nach oben verzerren. Die Identität KF = Bonsrate × Durchschnittsbon kann trotzdem exakt aufgehen; sie beweist keine vollständige Zählung. Saisonzentrierung allein behebt einen Erfassungswechsel innerhalb 2023/24 nicht.

Betroffen sind in Ralfs Kern insbesondere:
- `analysis/catering.py`: `kf_zerlegung`, Bons-/Bon-Korrelationen und Saisonvergleiche;
- `analysis/baseline.py`: Bons-Saisonkennzahlen;
- `analysis/arrival.py`: Beziehungen zwischen Ankunft und Bonsrate/Bon;
- `analysis/models.py`: Zielgrössen Bonsrate und Durchschnittsbon, darauf beruhende Diagnosehinweise;
- daraus abgeleitete Berichtsaussagen und Massnahmenbegründungen.

Empfohlener begrenzter Folge-Lauf auf Ralfs Zahlenbasis (D-028): bisherigen Stand als Referenz behalten; betroffene Auswertungen mit Ausschluss der gesamten Übergangssaison 2023/24 gegenrechnen. Zusätzlich kann Januar 2024 als dokumentierter technischer Einführungspunkt markiert werden, aber nicht als gesicherter Beginn vollständiger Zählung. Ab 2024/25 ist eine **Prüfstichprobe**, keine bestätigte fehlerfreie Periode. Pro Variante Stichprobe, Kennzahlen und Modellstabilität berichten; auch geringer Stichprobenumfang kann Schätzbarkeit einschränken. Ergebnisse erst nach tatsächlicher Berechnung bewerten.

Umsatz-/KF-Modelle können als Vergleich mitgeführt werden. Ein vollständiger Pipeline-Neulauf wird nötig, wenn Nenner, Quellumsätze/MwSt. oder Eingabedaten korrigiert werden; bei gemeinsamer Exportpipeline kann technisch ein kompletter Analyseexport einfacher sein, ohne dass ein neuer Rohdatenimport erforderlich ist. Simons Archiv-Notebook nicht weiterentwickeln; Gegenrechnung nur im tatsächlich betroffenen Scope.

## 4. Gezielte Rückfragen

1. Exakter Catering-Beteiligungssatz, Umsatzbasis inkl./exkl. MwSt., Geltungsbereich und gegebenenfalls variable Clubkosten?
2. Bedeutung der konkret beigefügten Catering-Abgabenfelder?
3. Entspricht `Public Netto` durchgängig den tatsächlich anwesenden Public-Zuschauern ohne VIP? Behandlung von Gästen/Personal/Freikarten?
4. Seit welchem Datum sind Gutscheine und sämtliche Zahlungswege inklusive Just Eat vollständig und stabil in den Bons enthalten? Gibt es rückwirkend korrigierte Bons?
5. Seit wann und für welche Artikel gilt die 80/20-Steuerregelung; wie wurden frühere Steuersätze abgebildet?

## 5. Umsetzungsgrenze dieses Pakets

Nur Dokumentation/Arbeitsregeln. Keine Quellwerte, historischen Run-Ordner, Python-Implementierungen oder Modelle geändert; keine Rohdaten vorhanden, kein Baseline-/Sensitivitätslauf und keine Baseline-Freigabe. Historische Berichte sind mit diesen neuen Einschränkungen zu lesen. Entscheide D-038 bis D-041; Nachträge D-003/D-004/D-005/D-019/D-029.

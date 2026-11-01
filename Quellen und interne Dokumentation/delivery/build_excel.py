"""Create a private, values-only review edition; retain isolated source calculator.
No raw-data ingestion or analytical re-estimation. Run with the project environment.
"""
from pathlib import Path
from copy import copy, deepcopy
import hashlib, json, re, zipfile, xml.etree.ElementTree as ET
from datetime import datetime
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment
from openpyxl.workbook.properties import CalcProperties
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.table import Table, TableStyleInfo

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'Deliverables/02_Excel'
RUN = ROOT / 'Baseline Analyse Rechnungen/run3_kontext-v5_2026-10-14'
BASE = RUN / 'ralf_kern_phase1/FCSG_Phase1_Ergebnisse.xlsx'
IDEAS = RUN / 'ralf_ideen_grundlage/Ideen_Grundlage_FCSG.xlsx'
OUT.mkdir(parents=True, exist_ok=True)
TARGET = OUT / 'FCSG_Baseline_und_Chancenfelder.xlsx'
def digest(p): return hashlib.sha256(p.read_bytes()).hexdigest()
archive_before = {str(p.relative_to(ROOT)): digest(p) for p in (ROOT / 'Baseline Analyse Rechnungen').rglob('*') if p.is_file()}
b = openpyxl.load_workbook(BASE, data_only=True)
i = openpyxl.load_workbook(IDEAS, data_only=True)
iform = openpyxl.load_workbook(IDEAS, data_only=False)
w = openpyxl.Workbook(); w.remove(w.active)
w.properties.creator = 'FCSG Projektteam'
w.properties.lastModifiedBy = 'FCSG Projektteam'
w.properties.title = 'FCSG | Baseline und Chancenfelder'
w.properties.subject = 'Privater Entwurf zur Partnerprüfung – aggregierte Analyse'
w.properties.description = 'Statische Review-Fassung der bestehenden Analyse; keine Rohdaten oder automatische Aktualisierung.'
w.properties.keywords = 'FCSG, Baseline, Chancenfelder, Partnerprüfung'
w.calculation = CalcProperties(calcId=191029, fullCalcOnLoad=True, forceFullCalc=True, calcMode='auto')
GREEN='006B54'; NAVY='183D3A'; PALE='EAF3EF'; GOLD='FFF2CC'
records=[]
# Labels and contextual prose only; numeric cells and calculation semantics are untouched.
def prose(v):
    if not isinstance(v,str): return v
    v=v.replace('Personal-/Gerätekosten des mobilen Verkaufs fehlen (Phase 2: DB-Sicht)', 'Primär inkrementeller Public-Catering-Umsatz exkl. MwSt.; zusätzlicher Cluberlös und Umsetzungskosten separat prüfen.')
    v=v.replace('Frauen-Spiele und Länderspiele sind gemäss Teamentscheid ausgeklammert (D-016/D-036).', 'Frauen-Spiele und Länderspiele sind ausserhalb des festgelegten Scopes.')
    v=v.replace('Phase-1-Korrektur', 'einheitliche Umsatzbasis').replace('CHF = Caterer-Umsatz; Club-Anteil und Kosten unbekannt', 'CHF = Catering-Systemumsatz; Club-Beteiligungsbasis und -satz unbestätigt, kein DB')
    v=re.sub(r'\b(?:Retos|Reto|Ralfs|Ralf|Simons|Simon|Sandro)\b', 'Referenz', v)
    return v

def style_table(s, header=5):
    s.sheet_view.showGridLines=False; s.freeze_panes=f'D{header+1}'
    s.sheet_properties.pageSetUpPr.fitToPage=True
    s.page_setup.orientation='landscape'; s.page_setup.paperSize=s.PAPERSIZE_A3
    s.page_setup.fitToWidth=1; s.page_setup.fitToHeight=0
    s.print_title_rows=f'1:{header}'; s.print_options.horizontalCentered=True
    s.oddFooter.center.text='Privater Entwurf | Partnerprüfung | Seite &P / &N'
    s.sheet_properties.tabColor=GREEN
    for row in s:
        for c in row:
            c.font=Font(name='Calibri',size=10,color=NAVY)
            c.alignment=Alignment(vertical='top',wrap_text=True)
    for row in s.iter_rows(min_row=header,max_row=header):
        for c in row: c.fill=PatternFill('solid',fgColor=GREEN); c.font=Font(name='Calibri',bold=True,color='FFFFFF',size=10)
    s.row_dimensions[header].height=44
    s['A1'].font=Font(name='Calibri',size=20,bold=True,color=GREEN)
    s.row_dimensions[1].height=32
    s.row_dimensions[2].height=46; s.row_dimensions[3].height=42
    for col in range(1,s.max_column+1):
        vals=[s.cell(r,col).value for r in range(header,min(s.max_row,header+80)+1)]
        textmax=max((len(str(x)) for x in vals if x is not None),default=14)
        width=min(48,max(15,textmax*0.9))
        s.column_dimensions[get_column_letter(col)].width=width
    for row in s.iter_rows(min_row=header+1):
        s.row_dimensions[row[0].row].height=48
        for c in row:
            if isinstance(c.value,datetime): c.number_format='dd.mm.yyyy'
            elif isinstance(c.value,(float,int)) and not isinstance(c.value,bool):
                key=str(s.cell(header,c.column).value).lower()
                if key.endswith('_pct') or '_pct_' in key or key.endswith('_pp') or 'differenz_pp'==key:
                    c.number_format='0.00" %"' if 'pp' not in key else '0.00" Pp."'
                elif (any(k in key for k in ['quote','anteil','r2_','korrelation','trefferquote','stabil']) and not any(k in key for k in ['_pct','_pp'])):
                    c.number_format='0.0%'
                elif isinstance(c.value,int): c.number_format='#,##0'
                else: c.number_format='#,##0.00'
    if s.max_row>header:
        ref=f'A{header}:{get_column_letter(s.max_column)}{s.max_row}'
        t=Table(displayName='T_'+re.sub(r'[^A-Za-z0-9_]', '_', s.title),ref=ref)
        t.tableStyleInfo=TableStyleInfo(name='TableStyleMedium4',showRowStripes=True)
        s.add_table(t)
    s.print_area=f'A1:{get_column_letter(s.max_column)}{s.max_row}'

def table(name,title,rows,note,source='',mapping=None):
    s=w.create_sheet(name)
    s['A1']=title; s['A2']=note; s['A3']='Quelle: '+source if source else 'Privater Entwurf zur Partnerprüfung | Keine Freigabe der Baseline'
    for rr in (1,2,3): s.merge_cells(start_row=rr,start_column=1,end_row=rr,end_column=max(4,len(rows[0])))
    for row in rows:s.append([]) if False else None
    for r,row in enumerate(rows,5):
        for c,v in enumerate(row,1): s.cell(r,c,prose(v))
    style_table(s)
    if mapping: records.append({'target':name,**mapping,'rows':len(rows)-1,'columns':len(rows[0])})
    return s

def export(book,source,name,title,note,cols=None):
    vals=list(book[source].values)
    idx=list(range(len(vals[0]))) if cols is None else [vals[0].index(c) for c in cols]
    rows=[tuple(row[j] for j in idx) for row in vals]
    return table(name,title,rows,note,'Analyse-Export 14.10.2026 | '+source,{'source_book':'baseline' if book is b else 'opportunities','source_sheet':source,'column_indices':idx})

intro=[('Bereich','Leseschlüssel','Abgrenzung','Status'),
('Zweck','Baseline verstehen → Chancenfelder prüfen → isolierte Szenarien diskutieren.','Privater Arbeitsentwurf zur Partnerprüfung; keine öffentliche Veröffentlichung.','Keine Massnahmenfreigabe'),
('Datenstand','Bestehende Analyse-Exporte vom 14.10.2026; fachliche Einordnung vom 01.11.2026.','2021/22 bis Teilstand 2026/27; Zeitraum und Stichprobe je Tabelle beachten.','Keine neue Berechnung'),
('Baseline','Saisonübersicht und Spielbaseline enthalten dieselben bestehenden Werte.','Herren-Pflichtspiele SL/Cup/UEFA gemäss bestehendem Kernscope; nicht jede Quelle deckt jedes Spiel.','Werteexport'),
('Phase 2','Primäres Prüfkriterium: inkrementeller Umsatz, nicht Deckungsbeitrag.','Catering: zusätzlicher Public-Catering-Systemumsatz exkl. MwSt.; nicht automatisch Cluberlös.','Umsatzbasis immer nennen'),
('Chancenfelder','Neun bestehende Felder als Hypothesen und Pilotansätze, nicht als bewiesene Potenziale.','Historische Assoziationen und Residuen sind keine kausale Massnahmenwirkung.','Keine Potenzialsumme'),
('Rechner','Hebel_Rechner → gelbe Basis-/Annahmenzellen → Szenarien.','Bestehende Formeln und Basiswerte erhalten; isolierte Beispiele nicht addieren.','Nur Szenarien dynamisch'),
('Aktualisierung','Analytische Blätter sind statische Werte, keine Rohdaten-Verbindungen.','Neue Analyse benötigt einen neuen kontrollierten Export; keine automatische Baseline-Aktualisierung.','Kein Datenimport'),
('Orientierung','02_KPI → 03_Abdeckung → 04_Saison → 05_Spiele → thematische Details → 20_Chancenfelder.','30_Grenzen und 31_Quellen vor Interpretation lesen.','Siehe Blattregister')]
table('00_Einstieg','FCSG | Baseline und Chancenfelder',intro,'Review-Entwurf | Zahlen unverändert, Darstellung und Einordnung für die Partnerprüfung neu strukturiert.')
nav=w.create_sheet('01_Navigation')
# KPI definitions are editorial, not additional numerical modelling.
kpis=[('Kennzahl','Definition / Einheit','Nenner / Scope','Interpretationsgrenze'),
('SOLL','Vergebene / ausgegebene Plätze laut Historie.','Bei ausverkauften Spielen teils Kapazitätswert.','Nicht durchgehend reine Zahl verkaufter Tickets.'),
('IST','Anwesende laut Historie, inkl. VIP und Gäste.','Je Spiel / Wettbewerb; Zählqualität in Spielbaseline.','Nicht gleich Public-Anwesende.'),
('No-Show gewichtet','1 − Summe IST / Summe SOLL; Anteil.','Saison / ausgewiesene Stichprobe.','Ungewichtete Spielmittel sind separat gekennzeichnet; Änderung in Prozentpunkten.'),
('Public Netto','Anwesende Public-Zuschauer ohne VIP; übernommenes Catering-Feld.','Nenner der Kundenfranken.','Durchgängige Abgrenzung zu Gästen, Personal und Freikarten bleibt zu verproben.'),
('Umsatz exkl. MwSt.','Public-Catering-Systemumsatz in CHF ohne MwSt.','Bestehender Export; keine Multiplikation mit einer Clubquote.','Nicht Cluberlös, nicht DB; Kiesplatz nicht nochmals addieren.'),
('Umsatz inkl. MwSt.','Systemumsatz inklusive MwSt.; insbesondere Artikel-/Zahlungsweg-Details.','Bruttobasis nur innerhalb passender Tabellen vergleichen.','Nicht mit exkl.-MwSt.-Werten addieren oder vermischen.'),
('Kundenfranken (KF) exkl.','Umsatz exkl. MwSt. / Public Netto, CHF pro Anwesendem.','Gewichtete Saisonquote, wo so im Export ausgewiesen.','Saisonmittel einzelner Spielquoten separat ausgewiesen.'),
('Bonsrate','Transaktionen / Public Netto, Bons je Anwesendem.','Transaktionsdaten ab 2023/24.','Keine Käuferquote; ein Gast kann mehrere Bons auslösen; historische Zählgrenzen beachten.'),
('Ø Bon exkl.','Umsatz exkl. MwSt. / Transaktionen, CHF pro Bon.','Nur Spiele mit Bons.','Gutschein-Erfassung 2023/24 schränkt Vergleichbarkeit ein, ohne daraus einen Umsatzfehler abzuleiten.'),
('Ankunft','Erster gültiger Zutritt je Ticket; Minuten vor Anpfiff und Anteile.','Nur ausreichend vollständig abgedeckte Spiele.','Frühere Ankunft beweist keinen Mehrkonsum.'),
('Erwartung / Referenzlücke','Bestehender kontextbereinigter Modelloutput; CHF-Lücke = (erwarteter KF − beobachteter KF) × Public Netto.','Jeweilige historische Modellstichprobe.','Diagnose, kein realisierbares Potenzial und keine kausale Wirkung.'),
('Inkrementeller Umsatz','Zusätzlicher Umsatz gegenüber einer plausiblen Vergleichssituation.','Je Hebel MwSt.-Basis und Erlösempfänger explizit nennen.','Im Szenariorechner nur Annahmen, keine gemessenen Pilotergebnisse.'),
('Cluberlös / Beteiligung','Zusätzlicher beteiligungsfähiger Umsatz × vertraglicher Satz.','Satz, Basis und Geltungsbereich unbestätigt.','20 % wären nur eine optionale unbestätigte Szenarioannahme; hier nicht angewendet.'),
('Prozent / Prozentpunkte','_pct-Spalten enthalten bereits Prozentzahlen; Quoten/Anteile überwiegend Bruchteile.','Zellformate zeigen Prozent bzw. Pp.; kein Umrechnen der Quellwerte.','Effekte in gemischten Einheiten gemäss jeweiliger Einheitsspalte lesen.'),
('LOSO / LOMO / KI','Validierung unter Ausschluss einer Saison / eines Spiels; KI = Konfidenzintervall.','Bestehender Modellstand.','Hohe Modellgüte beweist weder Kausalität noch künftigen Erfolg.')]
table('02_KPI','Kennzahlen und Umsatzabgrenzung',kpis,'Die Definitionen erklären die übernommenen Exporte; sie ändern keine Berechnung.')
export(b,'05_Abdeckung','03_Abdeckung','Datenabdeckung nach Saison und Wettbewerb','Anzahlen verfügbarer Spiele je Quelle. Verfügbare Bons sind nicht gleich nachgewiesen vollständig gezählte Bons.')
export(b,'A5_Saison_KPI','04_Saison','Saisonbaseline | getrennte Wettbewerbs-Sichten','SL, Cup, UEFA und kombinierte Sichten nicht addieren: überlappende Auswertungen. 2026/27 ist ein Teilstand; 2021/22 COVID-geprägt.')
cols=list(next(b['A1_mart_match'].values))
cols=[c for c in cols if c not in ['in_kontexttabelle','mechanismen','hat_kontext_gruppe']]
export(b,'A1_mart_match','05_Spiele','Spielbaseline | Spielaggregate und Scope-Flag','109 Exportzeilen: 108 gespielte Kernspiele und ein abgesagter Anlass (14.03.2026, kernscope = FALSCH). Saisonbaseline nur mit kernscope = WAHR abstimmen; Referenzlücken sind keine Umsatzpotenziale.',cols)
export(i,'R3_Basis_Saison','06_Rechnerbasis','Meisterschaft | historische Rechnerbasis','Saisonwerte und ausdrücklich bezeichnete Mehrsaisonbasis unverändert. 2026/27: vier Spiele, keine Vollsaisonbasis.')
exports=[(b,'B1_NoShow_Kontext','07_NoShow_Kontext','No-Show im Spielkontext','Zusammenhänge, keine Kausalwirkung; jeweilige Stichprobe beachten.'),
(b,'B4_Eintritt_Segmente','08_Ticketnutzung','Einzelticket-Nutzung nach Segment','Aggregierte Segmente; historische Eintrittsdaten nur in gültigen Zeiträumen interpretieren.'),
(i,'N3_Zweitmarkt_Saison','09_Zweitmarkt','Zweitmarkt nach Saison','Weiterverkäufe nicht automatisch zusätzliche Anwesenheit. Wiederbesetzung und No-Show nicht doppelt zählen.'),
(i,'N7_Tribuene_2627','10_Tribuenen','Tribünen | Näherung 2026/27','Nur frühe Saisonspiele; Abo-Nutzung aus Aggregaten angenähert, keine individuelle Besuchshistorie.'),
(i,'A6_Fruehindikator','11_Fruehindikator','Frühindikator für die Spieltagsplanung','Bestehende retrospektive Validierung. Prognose ist Planungswerkzeug, kein gemessener Umsatzhebel.'),
(b,'D1_Ankunft_je_Spiel','12_Ankunft','Ankunft je Spiel','Minuten vor Anpfiff und Anteile in vollständig abgedeckten Spielen. Ankunft ist kein Konsumnachweis.'),
(i,'Z6_Toroeffnung_Beleg','13_Toroeffnung','Toröffnung | bestehender Vergleich','Differenz-in-Differenzen betrifft Ankunft, nicht kausale Catering-Umsatzwirkung.'),
(i,'K1_KF_Entwicklung','14_Catering_Trend','Catering | Kundenfranken und Bons','Bonsrate/Ø Bon 2023/24: Gutschein-Erfassung im Übergang eingeschränkt; Umsatzwerte dadurch nicht als falsch einzustufen.'),
(i,'K2_Warenkorb_Gruppen','15_Warenkorb','Warenkorb nach Artikelgruppe','Artikelumsätze inkl. MwSt., begrenzte Kanalabdeckung; nicht mit gesamten Netto-Umsätzen gleichsetzen.'),
(i,'K5_Preis_Menge','16_Preis_Menge','Preis-, Mengen- und Sortimentseffekte','Bestehende buchhalterische Zerlegung auf Artikel-Bruttobasis, keine Preisempfehlung.'),
(b,'C4_Zahlungswege','17_Zahlungswege','Catering | Zahlungswege','Umsätze inkl. MwSt.; Zahlungsweganteile sind keine Anteile fehlender Bons. Kombinierte Kanalbezeichnungen beibehalten.'),
(i,'K11_Mobiler_Verkauf_Effekt','18_Mobiler_Verkauf','Mobiler Verkauf | historische Assoziationen','Beobachtungsdaten und kleine Teilstichproben. Einsatz-Codierung aus ausdrücklichen Angaben; kein kausaler Massnahmeneffekt.'),
(i,'K14_Kiesplatz_Wetter','19_Kiesplatz','Kiesplatz und Wetter','Kiesplatz ist Teil des Catering-Totals, niemals addieren. Wetterassoziation kein quantifiziertes Massnahmenpotenzial.'),
(b,'K1_Kontext_Effekt_Matrix','23_Kontext','Bestehende Kontext-Effekt-Matrix','Effekte gemäss Einheitsspalte lesen. Historische Assoziationen; Bons-/Bon-Ergebnisse mit Zählgrenze 2023/24 interpretieren.'),
(b,'K2_Modellguete','24_Modellguete','Kontextmodelle | Güte und Validierung','Unveränderte bestehende Modelloutputs, keine Neuschätzung. Transformierte RMSE sind keine CHF-Prognosefehler.'),
(b,'K6_Diagnosekarte','25_Diagnose','Spielbezogene Kontextdiagnose','Erwartungswerte und Residuen sind Diagnostik, keine Umsatzpotenziale; aus Freitext abgeleitete Hinweise sind Hypothesen.'),
(i,'F1_Randfelder_Kategorien','26_Randfelder','Weitere Anlässe | explorative Übersicht','Ausserhalb Kernscope: kleine Fallzahlen und teils fehlende/geschätzte Zuschauerzahlen. Überlappende Kategorien nicht addieren.')]
for args in exports: export(*args)
# Preserve all nine opportunity rows and source numbers; omit internal coordination/legacy priority fields.
opcols=['nr','chancenfeld','treiber','kernzahl','befund','evidenz','evidenz_begruendung','steuerbarkeit','clubhebel','reichweite','datenreife','hebel_arithmetik','leitplanke_Umsatz ≠ DB','datenluecke','leitfragen','pilot_messung','warnhinweis','quellen','lesart']
export(i,'02_Chancenfelder','20_Chancenfelder','Neun Chancenfelder | Hypothesen für Phase 2','Bestehende Einordnungen, keine neue Rangliste. Primär inkrementeller Umsatz; Quellenbefunde mit 30_Grenzen lesen. Keine Addition der Hebel.',opcols)
w['20_Chancenfelder']['B6']='Ungenutzte vergebene Plätze aktivieren'
w['20_Chancenfelder']['D6']="60'942 Differenz SOLL−IST (vergebene, nicht durchgehend nachweislich bezahlte Plätze) in der Saison 2025/26. Historischer Zweitmarkt-Indikator rund 9 %; kein nachgewiesener Anteil zusätzlicher Wiederbesetzung dieser Differenz und kein Nachweis zusätzlicher Anwesenheit."
# Cross-workbook copy only of the isolated calculator and scenario sheets. Fixed coordinates retained.
for name in ['Hebel_Rechner','Szenarien']:
    src=iform[name]; dst=w.create_sheet(name)
    limit=26 if name=='Hebel_Rechner' else src.max_row
    for row in src.iter_rows(max_row=limit):
        for cell in row:
            d=dst.cell(cell.row,cell.column,cell.value)
            if cell.has_style:
                d.font=copy(cell.font);d.fill=copy(cell.fill);d.border=copy(cell.border)
                d.number_format=cell.number_format;d.protection=copy(cell.protection)
            d.alignment=copy(cell.alignment)
    for rng in src.merged_cells.ranges:
        if rng.max_row<=limit:dst.merge_cells(str(rng))
    for key,val in src.column_dimensions.items():dst.column_dimensions[key]=copy(val)
    for key,val in src.row_dimensions.items():
        if key<=limit:dst.row_dimensions[key]=copy(val)
    dst.data_validations=deepcopy(src.data_validations)
    dst.sheet_view.showGridLines=False;dst.freeze_panes='D7' if name=='Hebel_Rechner' else 'D5'
    dst.sheet_properties.tabColor='D6A848'
    dst.oddFooter.center.text='Isoliertes Umsatzszenario | keine Potenzialsumme | kein Cluberlös'
    dst.page_setup.orientation='landscape';dst.page_setup.fitToWidth=1;dst.sheet_properties.pageSetUpPr.fitToPage=True
    dst.print_area=f'A1:{get_column_letter(dst.max_column)}{limit}'
    if name=='Hebel_Rechner':
        dst['A2']='Gelb = Eingaben. Isolierte Szenarien: zusätzlicher Public-Catering-Systemumsatz exkl. MwSt., nicht Cluberlös und kein DB. Hebel überlappen und dürfen NICHT addiert werden.'
        dst['A5']='D enthält anfangs Formeln auf die statische Saisonbasis B (2025/26). Andere Basis durch Eingabe in D setzen; keine automatische Aktualisierung aus der Spielbaseline.'
    else:dst['G4']='Catering-Systemumsatz je Saison (CHF exkl. MwSt.)'
for key,val in iform.defined_names.items():w.defined_names.add(deepcopy(val))
table('22_Ideensteckbrief','Ideensteckbrief | Vorlage',list(i['Ideen_Steckbrief'].values)[2:],'Idee, Messgrösse, Annahmen und Pilot transparent ausweisen. Primäre Erfolgsgrösse ist inkrementeller Umsatz.','Chancen-Export | Ideen_Steckbrief')
w['22_Ideensteckbrief']['B15']='Primär zusätzlicher Umsatz; Erlösempfänger und MwSt.-Basis nennen. Clubbeteiligung separat prüfen; Warenkosten des Partners nicht als Clubkosten abziehen.'
limits=[('Thema','Einordnung','Folge für Review','Stand'),
('Freigabe','Privater Entwurf, nicht freigegebene Baseline.','Partnerprüfung von Scope, Nennern und Vertragsbasis ausstehend.','Offen'),
('Statische Ausgabe','Alle analytischen Tabellen sind unveränderte Werteexporte; keine Rohdaten enthalten.','Keine automatische Baseline-Aktualisierung; nur Szenarien enthalten Formeln.','Exportstand 14.10.2026'),
('Bons 2023/24','Kassensystemwechsel und Gutschein-Transaktionszählung im Übergang.','Bonsrate und Ø Bon historisch eingeschränkt vergleichbar. Daraus folgt kein Nachweis falscher Umsatzwerte; keine Sensitivitäts-Neuberechnung vorgenommen.','Knapper Vorbehalt'),
('Public-Nenner','Definition: tatsächlich anwesende Public-Zuschauer ohne VIP.','Durchgängige Feldabgrenzung von Public Netto, Gästen, Personal und Freikarten bleibt zu verproben.','Offen'),
('Club-Beteiligung','Club erhält einen Anteil; Satz, Umsatzbasis und Geltungsbereich nicht bestätigt.','20 % nur optionales unbestätigtes Szenario; hier weder angesetzt noch versteckt in Baseline/Rechner skaliert.','Kein Vertragsnachweis'),
('Kosten / DB','Warenkosten trägt der Cateringpartner.','Nicht als Clubkosten abziehen; zusätzliche Clubkosten separat prüfen. Phase 2 primär inkrementeller Umsatz.','Keine DB-Rechnung'),
('Kiesplatz / MwSt.','Kiesplatz ist im Catering-Umsatz enthalten. Steuerliche 80/20-Regel ist keine Clubquote.','Keine Addition, keine pauschale rückwirkende Neuversteuerung. Historische Gültigkeit und Artikelbasis offen.','Bestehende Zahlen erhalten'),
('Kausalität','Kontextmodelle, mobile Verkäufe und gute Spiele zeigen historische Zusammenhänge.','Kein Residuum als erschliessbares Potenzial ausgeben; Wirkungen in Piloten mit Vergleich messen.','Kein Wirkungsnachweis'),
('Teilperioden','2026/27 nur früher Teilstand, 2021/22 COVID-geprägt; Quellenabdeckung unterschiedlich.','Keine Vollsaison-Hochrechnung aus Teilperioden; Wettbewerbe und überlappende Sichtweisen nicht summieren.','Abdeckung beachten'),
('Artikel / Proxy','Artikel teils nur Kassenkanal; Alkoholanteil aus MwSt.-Mix ist ein Proxy.','Brutto-/Nettobasen nicht mischen. Auch starke historische Evidenz ersetzt keinen kausalen Pilotnachweis.','Scope beachten'),
('Rechner','Bestehende Formeln, Namen, Eingaben und gespeicherte Quellergebnisse übernommen.','Excel soll beim Öffnen neu rechnen. Keine Ausführung in einer Excel-/LibreOffice-Engine in dieser Umgebung; gespeicherte Ergebnisse und Formelarithmetik unabhängig geprüft.','Keine neue Modellierung'),
('Überschneidungen','Anwesenheit × Bonsrate × Ø Bon; KF = Bonsrate × Ø Bon.','Keine Summe über Einzelhebel oder Ideen; Doppelzählung und Verlagerung prüfen.','Keine Totalzeile'),
('Reviewfragen','Vertragsbasis; Nennerdefinition; stabile Bonsabdeckung; aktuelle aggregierte Ticketnutzung; Kassenzeit-/Sektordaten.','Für Piloten Zielgrösse, Umsatzempfänger, Vergleichsgruppe und Annahmen dokumentieren.','Partnerprüfung')]
table('30_Grenzen','Einordnung, Grenzen und offene Prüfungen',limits,'Diese Hinweise ergänzen die bestehenden Zahlen; sie ersetzen weder Rohdatenprüfung noch Baseline-Freigabe.')
source_rows=[('Quelle','Verwendung','Übernahme','Abgrenzung'),
('Analyse-Export 14.10.2026 | FCSG_Phase1_Ergebnisse.xlsx','Saison-/Spielbaseline, Abdeckung, Ticketnutzung, Ankunft, Kontext','Statische Zellwerte; Quellblatt je Tabelle benannt.','Keine Rohdaten; keine personenbezogenen Einzelzeilen.'),
('Chancen-Export 14.10.2026 | Ideen_Grundlage_FCSG.xlsx','Neun Chancenfelder, thematische Belege, Rechnerbasis','Numerische Werte unverändert; isolierte Rechnerformeln und neun definierte Namen erhalten.','Interne Vergleiche, Abstimmungen und alte Grafikbilder nicht übernommen.'),
('Fachliche Einordnung 01.11.2026','Umsatzbasis, Clubbeteiligung, Bonsvergleichbarkeit','Erklärtexte, keine Änderung historischer Werte.','Keine Vertragsfreigabe oder neue Analyse.'),
('Review-Edition','Thematische Neuordnung, KPI-Lesehilfe und Grenzen','Redaktionelle Formulierungen und Labels angepasst; keine neue analytische Modellierung.','Keine externen Datenverbindungen oder öffentlichen Uploads.')]
table('31_Quellen','Quellen und Übernahmeprinzip',source_rows,'Die vollständigen Zellabgleiche und Prüfergebnisse liegen im begleitenden lokalen Prüfprotokoll.')
# Dictionary limited to the published game-baseline fields; descriptive source text retained.
dictrows=list(b['10_Datenwoerterbuch'].values)
dictrows=[dictrows[0]]+[r for r in dictrows[1:] if r[0]=='mart_match' and r[1] in cols]
table('32_Datenwoerterbuch','Felddefinitionen der Spielbaseline',dictrows,'Technische Feldnamen bleiben zur nachvollziehbaren Zuordnung erhalten. KPI-Einordnung in 02_KPI ist massgeblich.','Analyse-Export | 10_Datenwoerterbuch')
# Resolve human-readable legacy source-sheet labels to actual published sheet names.
labelmap={r['source_sheet']:r['target'] for r in records}
labelmap.update({'02_Chancenfelder':'20_Chancenfelder','04_Datenanfragen':'30_Grenzen'})
for s in w:
    for row in s:
        for c in row:
            if isinstance(c.value,str) and c.data_type!='f':
                for old,new in sorted(labelmap.items(), key=lambda kv:-len(kv[0])):
                    if old!=new and not (c.row==3 and c.value.startswith('Quelle:')):c.value=c.value.replace(old,new)
                c.comment=None
                if c.hyperlink:c.hyperlink=None
# Navigation sorted to make the intended reading route visible.
order=['00_Einstieg','01_Navigation','02_KPI','03_Abdeckung','04_Saison','05_Spiele','06_Rechnerbasis','07_NoShow_Kontext','08_Ticketnutzung','09_Zweitmarkt','10_Tribuenen','11_Fruehindikator','12_Ankunft','13_Toroeffnung','14_Catering_Trend','15_Warenkorb','16_Preis_Menge','17_Zahlungswege','18_Mobiler_Verkauf','19_Kiesplatz','20_Chancenfelder','22_Ideensteckbrief','Hebel_Rechner','Szenarien','23_Kontext','24_Modellguete','25_Diagnose','26_Randfelder','30_Grenzen','31_Quellen','32_Datenwoerterbuch']
w._sheets=[w[n] for n in order]
nav.append(['Blatt','Inhalt / Lesenutzung'])
for n in order:
    if n!='01_Navigation':
        nav.append([n,w[n]['A1'].value]);nav.cell(nav.max_row,1).hyperlink=f"#'{n}'!A1"
style_table(nav,1);nav.column_dimensions['A'].width=30;nav.column_dimensions['B'].width=105;nav.freeze_panes='A2'
# Long text sheets need reader-safe heights, not clipped single-line rows.
for name in ['00_Einstieg','02_KPI','30_Grenzen','31_Quellen']:
    s=w[name]
    for col in range(1,s.max_column+1):s.column_dimensions[get_column_letter(col)].width=47 if col>1 else 27
    for row in range(6,s.max_row+1):s.row_dimensions[row].height=88
s=w['20_Chancenfelder']
for row in range(6,s.max_row+1):s.row_dimensions[row].height=390
for col in range(1,s.max_column+1):s.column_dimensions[get_column_letter(col)].width=60 if col>2 else 30
# Source semantics of mixed-unit effect columns: never impose percentage scaling.
for s in w:
    if s.title in ['Hebel_Rechner','Szenarien']:continue
    for row in s.iter_rows(min_row=6):
        for c in row:
            key=str(s.cell(5,c.column).value).lower()
            if key in ['effekt','ki95_unten','ki95_oben','ki90_unten','ki90_oben','p_wert','p_fisher','korrelation','r_innerhalb_saison_mit_kiesplatz','residuen_korrelation_kies_stadion'] or key.startswith('z_wert'):
                c.number_format='0.0000' if key.startswith('p_') else '0.00'
# Give context-specific exact unit labels for percentage-valued intervals.
for name in ['18_Mobiler_Verkauf','19_Kiesplatz']:
    s=w[name]
    unit_column=next((col for col,c in enumerate(s[5],1) if c.value=='einheit'),None)
    for row_number,row in enumerate(s.iter_rows(min_row=6),6):
        unit=s.cell(row_number,unit_column).value if unit_column is not None else '%'
        for col,c in enumerate(row,1):
            if str(s.cell(5,col).value) in ['effekt','ki95_unten','ki95_oben','ki90_unten','ki90_oben','abweichung_von_erwartung_pct','mde_80pct_power_pct'] and isinstance(c.value,(float,int)):c.number_format='0.00" Pp."' if unit=='Pp.' else '0.00" %"'
w.save(TARGET)
# Carry original cached formula results (not freshly invented/re-estimated values).
NS={'s':'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
def cache_map(z, idx):
    xml=ET.fromstring(z.read(f'xl/worksheets/sheet{idx}.xml'))
    return {c.attrib['r']: c.find('s:v',NS) for c in xml.findall('.//s:c',NS) if c.find('s:f',NS) is not None}
with zipfile.ZipFile(IDEAS) as srcz: caches={n:cache_map(srcz,iform.sheetnames.index(n)+1) for n in ['Hebel_Rechner','Szenarien']}
with zipfile.ZipFile(TARGET) as z: payload={n:z.read(n) for n in z.namelist()}
for name,cache in caches.items():
    path=f'xl/worksheets/sheet{w.sheetnames.index(name)+1}.xml'
    text=payload[path].decode()
    for coord,value in cache.items():
        if value is None: continue
        pat=rf'(<c\b[^>]*\br="{coord}"[^>]*>)(.*?)(</c>)'
        def repl(m):
            body=re.sub(r'<v(?:\s[^>]*)?>.*?</v>|<v\s*/>','',m[2],flags=re.S)
            # Source cached values may be empty, numeric or formula-string; source cells use numeric caches here.
            vtext='' if value.text is None else value.text
            return m[1]+body+'<v>'+vtext+'</v>'+m[3]
        text=re.sub(pat,repl,text,flags=re.S)
    payload[path]=text.encode()
# Retain source XML numeric precision: openpyxl serializes floats to 16 digits.
# Exact source literals avoid even a one-ULP change in analytical values or inputs.
raw_books={}
for key,path,book in [('baseline',BASE,b),('opportunities',IDEAS,iform)]:
    with zipfile.ZipFile(path) as z:
        raw_books[key]={s.title:ET.fromstring(z.read(f'xl/worksheets/sheet{idx}.xml')) for idx,s in enumerate(book,1)}
def raw_numeric(sheet):
    return {c.attrib['r']:c.find('s:v',NS).text for c in sheet.findall('.//s:c',NS) if c.attrib.get('t','n') in ['n','b'] and c.find('s:v',NS) is not None and c.find('s:v',NS).text is not None}
def replace_literals(name,literals):
    path=f'xl/worksheets/sheet{w.sheetnames.index(name)+1}.xml';text=payload[path].decode()
    def change(m):
        coord=m[1];body=m[2]
        if coord in literals:
            body=re.sub(r'<v(?:\s[^>]*)?>.*?</v>|<v\s*/>',lambda _: '<v>'+literals[coord]+'</v>',body,flags=re.S)
        return '<c'+m[3] if False else m[0].replace(m[2],body,1)
    # Limit replacement to existing numeric values; formulas and styles unchanged.
    def cell_change(m):
        coord=re.search(r'\br="([A-Z]+[0-9]+)"',m[0]).group(1)
        if coord not in literals:return m[0]
        return re.sub(r'<v(?:\s[^>]*)?>.*?</v>|<v\s*/>',lambda _: '<v>'+literals[coord]+'</v>',m[0],flags=re.S)
    payload[path]=re.sub(r'<c\b[^>]*>.*?</c>',cell_change,text,flags=re.S).encode()
for rec in records:
    srcnums=raw_numeric(raw_books[rec['source_book']][rec['source_sheet']]);literals={}
    for coord,value in srcnums.items():
        from openpyxl.utils.cell import coordinate_from_string,column_index_from_string
        col,row=coordinate_from_string(coord);j=column_index_from_string(col)-1
        if row>=2 and j in rec['column_indices']:
            literals[f'{get_column_letter(rec["column_indices"].index(j)+1)}{row+4}']=value
    replace_literals(rec['target'],literals)
for name in ['Hebel_Rechner','Szenarien']:
    literals=raw_numeric(raw_books['opportunities'][name])
    literals={coord:value for coord,value in literals.items() if iform[name][coord].row<=(26 if name=='Hebel_Rechner' else 19)}
    replace_literals(name,literals)
with zipfile.ZipFile(TARGET,'w',zipfile.ZIP_DEFLATED) as z:
    for name,data in payload.items():z.writestr(name,data)

# Read back the exact output, compare selected source cells, formulas and existing caches.
f=openpyxl.load_workbook(TARGET,data_only=False)
v=openpyxl.load_workbook(TARGET,data_only=True)
checks=[];numeric_cells=0;numeric_fail=[]
for rec in records:
    book=b if rec['source_book']=='baseline' else i
    src=book[rec['source_sheet']];dst=f[rec['target']]
    count=0
    for rr,row in enumerate(src.iter_rows(min_row=2),6):
        for cc,j in enumerate(rec['column_indices'],1):
            value=row[j].value
            if isinstance(value,(float,int,bool,datetime)):
                count+=1;numeric_cells+=1
                if dst.cell(rr,cc).value != value:numeric_fail.append([dst.title,dst.cell(rr,cc).coordinate,value,dst.cell(rr,cc).value])
    checks.append({**rec,'numeric_boolean_date_cells_exact':count})
assert not numeric_fail,numeric_fail
formula_count=0;cache_count=0
for name in ['Hebel_Rechner','Szenarien']:
    for row in iform[name].iter_rows(max_row=26 if name=='Hebel_Rechner' else 19):
        for c in row:
            if c.data_type=='f':
                assert f[name][c.coordinate].value==c.value,(name,c.coordinate)
                assert v[name][c.coordinate].value==i[name][c.coordinate].value,(name,c.coordinate,'cache')
                formula_count+=1;cache_count+=1
            elif isinstance(c.value,(float,int,bool)):
                assert f[name][c.coordinate].value==c.value,(name,c.coordinate,'input')
assert {k:x.attr_text for k,x in f.defined_names.items()}=={k:x.attr_text for k,x in iform.defined_names.items()}
for s in f:
    for row in s:
        for c in row:
            assert not c.comment
            if isinstance(c.value,str):
                assert not re.search(r'\b(reto|retos|ralf|ralfs|simon|simons|sandro)\b',c.value,re.I),(s.title,c.coordinate,c.value)
                assert '#REF!' not in c.value
                if c.data_type=='f':
                    assert '[' not in c.value
                    for sheet in re.findall(r"(?:'([^']+)'|([A-Za-z_][A-Za-z_0-9]*))!",c.value):assert (sheet[0] or sheet[1]) in f.sheetnames
            assert c.data_type!='e',(s.title,c.coordinate,c.value)
assert not f._external_links
assert sum(len(s._images) for s in f)==0
assert all(c.data_type!='f' for s in f if s.title not in ['Hebel_Rechner','Szenarien'] for row in s for c in row)
# Independently evaluate original default formula arithmetic against carried caches.
h=v['Hebel_Rechner'];base={r:h[f'D{r}'].value for r in range(7,16)}
expected={19:h['B19'].value/100*base[8]*base[12]*h['C19'].value,20:h['B20'].value*base[12]*h['C20'].value,21:h['B21'].value*base[9]*base[13],22:h['B22'].value/100*base[10],23:h['B23'].value*base[11],24:h['B24'].value*base[9]}
calc_evidence=[]
for row,result in expected.items():
    annual=result*base[7]*h[f'D{row}'].value
    assert abs(h[f'F{row}'].value-result)<1e-8
    assert abs(h[f'G{row}'].value-annual)<1e-7
    calc_evidence.append({'cell':f'Hebel_Rechner!G{row}','source_cached':h[f'G{row}'].value,'independent_arithmetic':annual})
for row in range(5,20):
    s=v['Szenarien'];kind=s[f'C{row}'].value
    if kind is None: assert s[f'G{row}'].value in [None,''];continue
    branch=[h[f'A{r}'].value for r in range(19,25)].index(kind)
    delta=s[f'D{row}'].value;phi=s[f'E{row}'].value if s[f'E{row}'].value is not None else 1
    share=s[f'F{row}'].value if s[f'F{row}'].value is not None else 1
    per_game=[delta/100*base[8]*base[12]*phi,delta*base[12]*phi,delta*base[9]*base[13],delta/100*base[10],delta*base[11],delta*base[9]][branch]
    result=per_game*base[7]*share
    assert abs(s[f'G{row}'].value-result)<1e-7
    calc_evidence.append({'cell':f'Szenarien!G{row}','source_cached':s[f'G{row}'].value,'independent_arithmetic':result})
archive_after={str(p.relative_to(ROOT)): digest(p) for p in (ROOT / 'Baseline Analyse Rechnungen').rglob('*') if p.is_file()}
assert archive_before==archive_after
# Reconciliation: no new baseline cells; independently validate compatible season/match scope.
header=list(next(b['A1_mart_match'].values));games=[dict(zip(header,row)) for row in list(b['A1_mart_match'].values)[1:]]
season=[]
for row in list(b['A5_Saison_KPI'].values)[1:]:
    d=dict(zip(next(b['A5_Saison_KPI'].values),row))
    if d['wettbewerbe']!='SL':continue
    group=[g for g in games if g['saison']==d['saison'] and g['wettbewerb']=='SL' and g['kernscope']]
    sums={k:sum(g[k] or 0 for g in group) for k in ['ist','public_netto','umsatz_exkl']}
    assert len(group)==d['spiele']
    for gkey,skey in [('ist','ist_summe'),('public_netto','public_netto_summe'),('umsatz_exkl','umsatz_exkl')]:assert abs(sums[gkey]-d[skey])<1e-7
    season.append({'saison':d['saison'],'spiele':len(group),**sums,'export_umsatz_exkl':d['umsatz_exkl']})
assert len(list(i['02_Chancenfelder'].values))-1 == f['20_Chancenfelder'].max_row-5 == 9
assert sum(bool(g['kernscope']) for g in games)==108 and len(games)==109
all_scope_reconciliations=[]
for row in list(b['A5_Saison_KPI'].values)[1:]:
    d=dict(zip(next(b['A5_Saison_KPI'].values),row));competitions=d['wettbewerbe'].split('+')
    group=[g for g in games if g['saison']==d['saison'] and g['wettbewerb'] in competitions and g['kernscope']]
    assert len(group)==d['spiele']
    for field,target_field in [('ist','ist_summe'),('public_netto','public_netto_summe'),('umsatz_exkl','umsatz_exkl')]:
        total=sum(g[field] or 0 for g in group)
        assert abs(total-d[target_field])<1e-7
    all_scope_reconciliations.append({'saison':d['saison'],'wettbewerbe':d['wettbewerbe'],'spiele':len(group),'passed':True})
for name in ['Hebel_Rechner','Szenarien']:
    limit=26 if name=='Hebel_Rechner' else 19
    for row in iform[name].iter_rows(max_row=limit):
        for c in row:
            if isinstance(c.value,(float,int)) or c.data_type=='f':assert f[name][c.coordinate].number_format==c.number_format
    assert [(str(d.sqref),d.formula1,d.formula2) for d in f[name].data_validations.dataValidation]==[(str(d.sqref),d.formula1,d.formula2) for d in iform[name].data_validations.dataValidation]
for dn in f.defined_names.values():
    for sheet,coord in dn.destinations:assert sheet in f.sheetnames and f[sheet][coord].value is not None
report={'all_17_season_competition_scopes_reconciled':all_scope_reconciliations,'opportunity_rows':9,'played_core_matches':108,'cancelled_out_of_scope_rows':1,'calculator_number_formats_and_validations_exact':True,'output':str(TARGET),'output_sha256':digest(TARGET),'sheets':f.sheetnames,'source_files_sha256':{BASE.name:digest(BASE),IDEAS.name:digest(IDEAS)},'archived_files_unchanged':len(archive_before),'source_table_checks':checks,'exact_numeric_boolean_date_cells':numeric_cells,'formula_texts_exact':formula_count,'formula_caches_exact':cache_count,'defined_names_exact':len(f.defined_names),'formula_arithmetic_checks':calc_evidence,'season_match_reconciliation_SL':season,'broken_sheet_references':0,'external_links':0,'images':0,'metadata_creator':f.properties.creator,'calculation_engine_execution':False,'limitations':['Static analytical export; no raw-data validation or automatic refresh.','Excel/LibreOffice engine not available; original caches retained, formula arithmetic independently checked.','Historical voucher transaction counting limits 2023/24 comparability; no sensitivity re-run.','Club share and contractual revenue basis unconfirmed; no 20% scaling applied.']}
(Path(__file__).resolve().parent/'FCSG_Excel_Pruefprotokoll.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({k:report[k] for k in ['output','sheets','archived_files_unchanged','exact_numeric_boolean_date_cells','formula_texts_exact','formula_caches_exact','defined_names_exact','formula_arithmetic_checks','season_match_reconciliation_SL']},ensure_ascii=False,indent=2))

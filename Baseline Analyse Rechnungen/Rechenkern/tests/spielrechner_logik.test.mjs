// Rechenlogik des Spielrechners (Block <script id="logik">) mit TESTDATEN – keine Clubzahlen.
// Aufruf: SPIELRECHNER_HTML=<erzeugte TEST-Datei> node --test tests/spielrechner_logik.test.mjs
import {test} from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
import vm from "node:vm";

process.env.TZ = "Europe/Zurich";
const html = fs.readFileSync(process.env.SPIELRECHNER_HTML, "utf8");
const logik = html.match(/<script id="logik">([\s\S]*?)<\/script>/)[1];
const D = JSON.parse(html.match(/<script id="daten-json" type="application\/json">([\s\S]*?)<\/script>/)[1].replace(/<\\\//g, "</"));
const ctx = vm.createContext({});
vm.runInContext(logik, ctx);
const SR = ctx.SR;
const plain = o => JSON.parse(JSON.stringify(o));   // Objekte aus dem vm-Kontext vergleichbar machen
const nah = (a, b, eps = 1e-9) => assert.ok(Math.abs(a - b) < eps, `${a} ≠ ${b}`);

test("Datum, Zeit und Zahlen lesen", () => {
  assert.equal(SR.parseDatum("14.11.2026"), "2026-11-14");
  assert.equal(SR.parseDatum("2026-11-14"), "2026-11-14");
  assert.equal(SR.parseDatum("4.8.26"), "2026-08-04");
  assert.equal(SR.parseDatum("Samstag"), null);
  assert.equal(SR.parseZeit("18.30"), "18:30");
  assert.equal(SR.parseZeit("25:00"), null);
  assert.equal(SR.parseZahl("1'234.50"), 1234.5);
  assert.equal(SR.parseZahl("12,5"), 12.5);
  assert.equal(SR.parseZahl(""), null);                       // fehlend bleibt fehlend
});

test("Wochentag, Saison und Anstoss-Slot wie im Rechenkern", () => {
  assert.equal(SR.wochentag("2026-11-14"), "Samstag");
  assert.equal(SR.saisonVon("2026-07-26"), "2026/27");
  assert.equal(SR.saisonVon("2027-05-20"), "2026/27");
  assert.equal(SR.slotCode("Samstag", "18:00"), "referenz");
  assert.equal(SR.slotCode("Samstag", "20:30"), "slot_sa_abend");
  assert.equal(SR.slotCode("Sonntag", "16:30"), "slot_nachmittag");
  assert.equal(SR.slotCode("Samstag", "16:59"), "slot_nachmittag");
  assert.equal(SR.slotCode("Mittwoch", "20:30"), "slot_werktag_abend");
  assert.equal(SR.slotCode("Sonntag", "18:00"), "slot_werktag_abend");   // wie utils.anstoss_slot
});

test("Top-Gegner aus dem Namen, GC ausgenommen", () => {
  const m = D.top_gegner_muster;
  for (const n of ["FC Basel 1893", "BSC Young Boys", "FC Zürich", "YB"]) assert.equal(SR.istTopGegner(n, m), true, n);
  for (const n of ["Grasshopper Club Zürich", "FC Luzern", "Servette FC"]) assert.equal(SR.istTopGegner(n, m), false, n);
});

test("Spielplan-Import: Trennzeichen, Spaltennamen, Fehler", () => {
  const r = SR.parseSpielplan("Datum;Anstoss;Gegner;Wettbewerb;SOLL\n14.11.2099;18:00;Testgegner A;Super League;16'000\nxx;18:00;B;SL;\n");
  assert.equal(r.spiele.length, 1);
  assert.deepEqual(plain(r.spiele[0]), {datum: "2099-11-14", anstoss: "18:00", gegner: "Testgegner A", wettbewerb: "Super League", soll: 16000, vip: null});
  assert.equal(r.fehler.length, 1);
  const tab = SR.parseSpielplan("Date\tTime\tOpponent\n2099-11-15\t16.30\tTestgegner B");
  assert.equal(tab.spiele[0].anstoss, "16:30");
  assert.ok(SR.parseSpielplan("Gegner\nA").fehler.length);
});

test("Wetter aus Stunden: Anpfiffstunde und Regenfenster wie extern.py", () => {
  const st = {}; const t = (h, temp, mm) => { st[`2099-11-14T${String(h).padStart(2, "0")}:00`] = {temp, regen_mm: mm}; };
  t(16, 5, 0.4); t(17, 6, 0.3); t(18, 7, 0.1); t(19, 8, 0);
  // 18:00 → Temperatur 18-Uhr-Intervall, Regen Intervalle 17 und 18 = 0.4 mm → kein Regen
  assert.deepEqual(plain(SR.wetterAusStunden(st, "2099-11-14", "18:00")), {temp: 7, regen_mm: 0.4, regen: 0});
  // 18:30 → Ende 19 Uhr, Intervalle 17, 18, 19 = 0.4 mm
  assert.deepEqual(plain(SR.wetterAusStunden(st, "2099-11-14", "18:30")), {temp: 8, regen_mm: 0.4, regen: 0});
  // 17:00 → Intervalle 16, 17 = 0.7 mm → Regen
  assert.equal(SR.wetterAusStunden(st, "2099-11-14", "17:00").regen, 1);
  assert.equal(SR.wetterAusStunden(st, "2099-11-14", "21:00"), null);   // ausserhalb der Prognose
});

test("Normalwerte: 2 bzw. 3 Intervalle", () => {
  const k = SR.klimaFuer(D.klima, "2099-07-10", "18:00");
  nah(k.temp, Math.round(D.klima.temp["7"]["18"] * 10) / 10);
  nah(k.regen, D.klima.regen2["7"]["18"]);
  nah(SR.klimaFuer(D.klima, "2099-07-10", "18:30").regen, D.klima.regen3["7"]["19"]);
});

test("Ferien aus hinterlegter Liste", () => {
  assert.equal(SR.inFerien(D.ferien_stadt, "2099-10-15").name, "Testferien");
  assert.equal(SR.inFerien(D.ferien_stadt, "2099-10-21"), null);
});

test("Vorhersage = Python-Formel (Testdaten)", () => {
  const x = {top_gegner: 0, temp_anpfiff_c: 12, regen_anreise: 0, schulferien: 0, slot_sa_abend: 0, slot_nachmittag: 0, slot_werktag_abend: 0};
  const niv = SR.saisonNiveau(D, "kf_exkl", "T3/T4", []);
  assert.equal(niv.quelle, "modell");
  const v = SR.vorhersage(D, "kf_exkl", x, niv);
  assert.equal(Math.round(v.wert * 100) / 100, 15.49);       // wie tests/test_spielrechner.py
  const k = D.modelle.kf_exkl;
  nah(v.oben, Math.exp(Math.log(v.wert) + 1.2816 * k.rmse), 1e-9);
  // Sonntagnachmittag: Faktor exp(Koeffizient)
  const so = SR.vorhersage(D, "kf_exkl", {...x, slot_nachmittag: 1}, niv);
  nah(so.wert / v.wert, Math.exp(k.terme.slot_nachmittag), 1e-12);
  // Anwesenheitsquote: Logit
  const q = SR.vorhersage(D, "anwesenheitsquote", x, SR.saisonNiveau(D, "anwesenheitsquote", "T3/T4", []));
  const a = D.modelle.anwesenheitsquote.terme;
  nah(q.wert, 1 / (1 + Math.exp(-(a.Intercept + a["C(saison)[T.T3/T4]"] + a.temp_anpfiff_c * 12))), 1e-12);
});

test("Neue Saison: Basis-Niveau, dann gedämpft gelernt", () => {
  const x = {top_gegner: 0, temp_anpfiff_c: 10, regen_anreise: 0, schulferien: 0, slot_sa_abend: 0, slot_nachmittag: 0, slot_werktag_abend: 0};
  const k = D.modelle.kf_exkl, basis = k.terme.Intercept + k.terme["C(saison)[T.T3/T4]"];
  const leer = SR.saisonNiveau(D, "kf_exkl", "2099/00", []);
  assert.equal(leer.quelle, "basis"); nah(leer.z, basis);
  const erw = Math.exp(basis + k.terme.temp_anpfiff_c * 10);
  // 3 Spiele je +10 % über Erwartung → Offset = 3·ln(1.1)/(3+3)
  const b = [1, 2, 3].map(() => ({saison: "2099/00", x, y: erw * 1.1}));
  const niv = SR.saisonNiveau(D, "kf_exkl", "2099/00", b);
  assert.equal(niv.quelle, "gelernt"); assert.equal(niv.n, 3);
  nah(niv.z - basis, 3 * Math.log(1.1) / 6, 1e-12);
  // Saison mit wenigen Modellspielen: Modellwert als Start, IST verfeinert mit Gewicht = Anzahl Modellspiele
  const D4 = {...D, spiele: D.spiele.filter(s => !(s.saison === "T3/T4" && s.datum > "2099-04-31"))};
  const n4 = new Set(D4.spiele.filter(s => s.ziel_code === "kf_exkl" && s.saison === "T3/T4").map(s => s.datum)).size;
  assert.ok(n4 < 10);
  assert.equal(SR.saisonNiveau(D4, "kf_exkl", "T3/T4", []).quelle, "vorlaeufig");
  const start = k.terme.Intercept + k.terme["C(saison)[T.T3/T4]"], erw4 = Math.exp(start + k.terme.temp_anpfiff_c * 10);
  const v4 = SR.saisonNiveau(D4, "kf_exkl", "T3/T4", [{saison: "T3/T4", datum: "2099-12-30", x, y: erw4 * 1.1}]);
  assert.equal(v4.quelle, "gelernt"); nah(v4.z - start, Math.log(1.1) / (1 + Math.max(n4, 3)), 1e-12);
  // Spiel, das schon im Modell ist, zählt nicht doppelt
  const imModell = D4.spiele.find(s => s.ziel_code === "kf_exkl" && s.saison === "T3/T4").datum;
  assert.equal(SR.saisonNiveau(D4, "kf_exkl", "T3/T4", [{saison: "T3/T4", datum: imModell, x, y: 99}]).n, 0);
  // andere Saison und fehlende Werte zählen nicht
  assert.equal(SR.saisonNiveau(D, "kf_exkl", "2099/00", [{saison: "2098/99", x, y: 20}, {saison: "2099/00", x, y: null}]).n, 0);
});

test("IST-Kennzahlen wie im Rechenkern; fehlend ≠ 0", () => {
  const k = SR.istKennzahlen({ist: 15000, vip: 1000, soll: 18000, umsatz: 210000, bons: 13000});
  nah(k.anwesenheitsquote, 15000 / 18000); nah(k.kf_exkl, 15); nah(k.bons_pro_anwesende, 13000 / 14000); nah(k.bon_exkl, 210000 / 13000);
  const l = SR.istKennzahlen({ist: 15000, vip: null, soll: null, umsatz: null, bons: null});
  assert.equal(l.anwesenheitsquote, null); assert.equal(l.kf_exkl, null);
  assert.equal(SR.bandStatus(16, {unten: 14, oben: 15.5}), "ueber");
  assert.equal(SR.bandStatus(null, {unten: 14, oben: 15.5}), null);
});

# Verlagerung und Randlösungen – Streamlit-Demo

<!-- TODO nach dem Deploy: direkt hierher den Live-Link setzen (Leerzeile davor und danach):
**[→ Demo live ausprobieren](https://sebastianhanisch-verlagerung-demo.streamlit.app/)** -->

Stück 10 der Linie **Zielfunktionsdesign** („Das Ziel ist das Modell“) in der „Konzepte“-Reihe für die Website „Sebastian Hanisch – Operations Research und Machine Learning“ (Arbeitsname; Name, Bereich und Themenfeld werden erst bei der Einbindung in die Website festgelegt). Es baut auf Stück 1 bis 9 auf (`zielvergleich-demo`, `preis-der-fairness-demo`, `zwei-kriterien-demo`, `lexikographisch-demo`, `gleichstand-demo`, `hart-gegen-weich-demo`, `goodhart-kurve-demo`, `modellluecken-demo`; Stück 7 ist zurückgestellt): **m Aufgaben werden auf n Personen verteilt**, jede in **Regelzeit** oder in **Überstunden**. Die Kennzahl misst nur die Regelzeit. Was der Optimierer aus der Kennzahl herausdrückt, **wandert in die Überstunden**, die niemand misst, und die **Randlösung** reizt jede Grenze bis zum letzten Platz aus. Die Demo misst, **wie viel wandert, wer es trägt und wie schnell der Plan kippt**. Alles ist **simuliert**; keine Aussage über echte Dienstpläne, Personen oder Betriebe.

## Warum dieses Problem

Im Modell dieser Demo bekommt, wer nur die Regelzeit misst und optimiert, eine bessere Kennzahl, aber höhere wahre Kosten: die Last, die die Kennzahl nicht sieht, liegt in den Überstunden. Die Fragen: Wie viel besser sieht die Kennzahl aus, und was kostet das wirklich (Verlagerung)? Wie viel Überstundenkapazität braucht es dafür (Dosis-Wirkung)? Wer trägt die Überstunden? Wie viele Grenzen sind genau ausgeschöpft, und bleibt der Plan zulässig, wenn alle Zeiten ein wenig länger dauern (Rand)? Und was kostet eine Reserve?

## Modell

Gegeben `n` Personen, `m` Aufgaben, Kosten `a[i][j]` (ganze Zahlen) und Zeit `b[i][j]` (1 bis 9). Jede Aufgabe `j` wird einer Person und einer Schicht zugeordnet: **Regelzeit (R)** oder **Überstunden (Ü)**; **alle `(2n)^m` Pläne werden aufgezählt** (bis `6^7 = 279 936`), alles exakt in ganzen Zahlen. **Kennzahl (KPI):** die Kosten der Aufgaben in Regelzeit. **Wahre Kosten:** KPI plus `g` mal die Kosten der Aufgaben in Überstunden (`g` in Prozent; Voreinstellung 125 %). **Kapazitäten:** je Person Regelzeit höchstens `cap_R = ⌈f_R · Σ_j mittlere Zeit / n⌉` (Voreinstellung `f_R = 80 %`), Überstunden höchstens `cap_Z = ⌈f_Z · cap_R⌉` (Voreinstellung `f_Z = 50 %`). Das **Optimum der Kennzahl** hat den kleinsten KPI unter den zulässigen Plänen, das **wahre Optimum** die kleinsten wahren Kosten; bei Gleichstand gilt der kleinste Index der Aufzählung. **Gewinn** ist `(KPI wahres Optimum − KPI Optimum der Kennzahl) / KPI wahres Optimum`, **Verlust** ist `(wahre Kosten Optimum der Kennzahl − wahre Kosten wahres Optimum) / wahre Kosten wahres Optimum`. **Rand:** eine Grenze ist ausgeschöpft, wenn die Last genau der Kapazität gleicht; „+δ % Zeit“ prüft ganzzahlig `Last · (100 + δ) ≤ Kapazität · 100`. **Reserve:** die Kapazitäten werden auf `⌊Kapazität · 100 / (100 + δ)⌋` gesenkt und das wahre Optimum neu gelöst. Formeln stehen im 📐-Expander der App.

## Methodik

Zwei Kostenfamilien: **unabhängig** (1 bis 99) und **Personeneffekt** (Personeneffekt 0 bis 40 plus 1 bis 60). Die App zeigt: beide Optima nebeneinander (KPI, wahre Kosten, Pläne, Überstunden), die Punktwolke aller zulässigen Pläne, die Dosis-Wirkung über den Überstundenanteil, wer die Überstunden trägt, den Rand (ausgeschöpfte Grenzen, Kippen bei mehr Zeit) und den Preis der Reserve. Zählungen über 20 feste Instanzen (3 Personen, 7 Aufgaben, alle 279 936 Pläne) liegen hinter Schaltern. Verdikte entstehen live aus der Rechnung, jede Zahl im Text kommt aus dem Ergebnis.

## Befunde (gemessen, keine Behauptungen)

Alle Zahlen stammen aus den Auswertungsfunktionen der App und sind in `tests/test_claims.py` nachgerechnet. „Je 20 feste Instanzen“ heißt `SWEEP_SEEDS` (Seeds 100000 bis 100019), nie ein einzelner Seed; die Zahlen sind **Zählungen und Spannen über Instanzen**, kein Satz und keine Aussage über andere Instanzen. Soweit nicht anders angegeben 3 Personen, 7 Aufgaben, `f_R = 80 %`, `f_Z = 50 %`. Familien: unabhängig / Person.

| Frage | Befund |
|---|---|
| Optimum der Kennzahl ≠ wahres Optimum, Zuschlag g = 100 / 125 / 150 / 200 % | **20 / 20 / 20 / 20** von 20 in beiden Familien |
| Kennzahl besser (Median; Minimum) | unabhängig 82,4 % / 86,3 % / 87,9 % / 87,9 % (32,5 % / 61,1 % / 61,1 % / 61,1 %); Person 74,4 % / 79,9 % / 79,9 % / 82,6 % (51,3 % / 62,3 % / 62,3 % / 62,3 %) |
| wahre Kosten höher (Median; Maximum) | unabhängig **50,8 % / 73,1 % / 99,9 % / 150,5 %** (121,5 % / 150,3 % / 174,4 % / 251,2 %); Person 28,1 % / 49,1 % / 69,0 % / 109,3 % (72,9 % / 101,8 % / 129,0 % / 179,0 %) |
| Aufgaben in Überstunden (Median; Minimum bis Maximum) | Optimum der Kennzahl 5 (4 bis 7) in beiden Familien; wahres Optimum bei g = 125 %: 2 (1 bis 3) / 1 (1 bis 3), bei g = 200 %: 1 (0 bis 2) / 1 (0 bis 2) |
| Überstunden in Stunden (Median; Minimum bis Maximum) | Optimum der Kennzahl 13,0 (6,0 bis 16,0) / 12,5 (9,0 bis 17,0); wahres Optimum bei g = 125 %: 6,5 (1,0 bis 11,0) / 5,0 (2,0 bis 10,0) |
| Dosis-Wirkung: Überstundenanteil 0 / 25 / 50 / 100 % (Median 0 / 3 / 5 / 10 Stunden, Person 0 / 3 / 5 / 9,5), Optima verschieden | **0 / 20 / 20 / 20** von 20 in beiden Familien; ohne Überstundenkapazität wandert nichts |
| dabei: Kennzahl besser (Median) | unabhängig 0,0 % / 57,5 % / 86,3 % / 100,0 %; Person 0,0 % / 57,9 % / 79,9 % / 100,0 % |
| dabei: wahre Kosten höher (Median; Maximum) | unabhängig 0,0 % / 29,8 % / 73,1 % / 135,7 % (0,0 % / 93,3 % / 150,3 % / 293,8 %); Person 0,0 % / 29,0 % / 49,1 % / 83,2 % (0,0 % / 55,5 % / 101,8 % / 145,8 %) |
| Wer zahlt (g = 125 %): Anteil der Überstunden an den wahren Kosten, Optimum der Kennzahl (Median; Minimum) gegen wahres Optimum (Median) | unabhängig **93 %** (82 %) gegen 28 %; Person 90 % (81 %) gegen 18 % |
| dabei: Anteil der am stärksten belasteten Person an den Überstunden (Median); Personen mit Überstunden (Median) | unabhängig 37 %, 3 Personen; Person 38 %, 3 Personen: die Überstunden verteilen sich, **eine Person allein trägt sie nicht** |
| dabei: die im Mittel billigste Person trägt die meisten Überstunden (Träger ist jede Person, deren Überstunden das Maximum erreichen; bei Gleichstand tragen alle gleichauf), in | **13 / 20** (unabhängig), **10 / 20** (Person); allein in 3 und 1 Instanz; Gleichstand an der Spitze in 12 und 11; die im Mittel teuerste Person trägt allein oder gleichauf die meisten in 12 und 9 |
| Rand (g = 125 %): Überstundengrenze genau voll, Optimum der Kennzahl / wahres Optimum | unabhängig **17 / 12** von 20; Person **19 / 12** |
| dabei: Regelzeitgrenze genau voll; irgendeine Grenze voll | unabhängig 3 / 17 und 17 / 18; Person 4 / 14 und 19 / 17 |
| Plan bleibt zulässig bei +2 % / +5 % / +10 % / +20 % mehr Zeit, Optimum der Kennzahl / wahres Optimum | unabhängig 3 / 2, 3 / 2, 3 / 2, 2 / 0; Person 1 / 3, 1 / 3, 1 / 2, 1 / 1 (von 20) |
| Preis der Reserve 5 / 10 / 20 % (Median; Maximum), wahre Kosten des wahren Optimums höher | unabhängig 15,2 % (46,1 %) / 15,2 % (46,1 %) / 22,4 % (104,4 %), unlösbar 0; Person 7,6 % (37,3 %) / 8,0 % (37,3 %) / 13,1 % (51,0 %), bei 20 % **1** Instanz unlösbar |
| Preset „Die Kennzahl sieht besser aus“ (Seed 100009) | KPI **23** statt **193** (**88,1 %** besser), wahre Kosten **354,25** statt **210,5** (**68,3 %** mehr); **5** von 7 Aufgaben in Überstunden (im wahren Optimum 1), zusammen **12** Stunden; Kapazität 10 und 5 Stunden |
| Preset „Ohne Zuschlag: nur Verschiebung“ (g = 100 %, Seed 100040) | KPI **4** statt **55** (**92,7 %**), wahre Kosten **224** statt **139** (**61,2 %** mehr): auch ohne Zuschlag kostet die Kennzahl, denn wer die Überstunden macht, ist ihr gleichgültig |
| Preset „Wo es keinen Ort gibt, wandert nichts“ (Überstundenkapazität 0, Seed 100100) | beide Optima gleich, KPI und wahre Kosten **222** |
| Preset „Ein großer Ort für die Last“ (Überstundenanteil 100 %, Seed 100110) | KPI **0** statt **96**, wahre Kosten **457,5** statt **103,5** (**342,0 %** mehr), alle 7 Aufgaben in Überstunden |
| Preset „Alle Personen zahlen“ (Person, Seed 100133) | Überstunden je Person 4 / 4 / 4 Stunden, größter Anteil **33 %**, Überstunden-Anteil der wahren Kosten **92 %**; alle drei tragen gleichauf die meisten, auch die im Mittel billigste (P3) |
| Preset „Der Rand: 5 % mehr Zeit kippt den Plan“ (Seed 100189) | im Optimum der Kennzahl 2 Überstundengrenzen genau voll, schon bei +2 % unzulässig; das wahre Optimum hält bis +20 % |
| Preset „Die Reserve kostet“ (Seed 100318) | Reserve 5 / 10 / 20 %: wahre Kosten **0,0 % / 0,0 % / 65,7 %** höher |
| Preset „Kleinstes Beispiel (1 Person, 3 Aufgaben)“ (Seed 3) | **3** von 8 Plänen zulässig; KPI **18** statt **99**, wahre Kosten **130,5** statt **110,25** (**18,4 %** mehr) |

**Korrektur der Planungshypothesen:** Drei Vermutungen aus der Planung stimmen nicht. (1) „Eine Person trägt die Überstunden“: in der Mehrzahl der Instanzen tragen alle drei Personen welche (Median 3 von 3); die im Mittel billigste Person trägt allein oder gleichauf die meisten in 13 von 20 (unabhängig) und 10 von 20 (Person), die im Mittel teuerste in 12 und 9; der Unterschied ist klein, und mit 20 Instanzen und häufigen Gleichständen (12 und 11 von 20) ist kein Zusammenhang zwischen der Kostenhöhe und dem Tragen nachweisbar (ein Zufallsvergleich ist wegen der Gleichstände nicht angegeben). Eine frühere Zählung mit dem Index als Schiedsrichter bei Gleichstand (9 und 3 von 20) hing an der Nummerierung der Personen und ist ersetzt. (2) „Der Rand betrifft nur das Optimum der Kennzahl“: auch das wahre Optimum ist knapp, es hat in 18 von 20 Instanzen mindestens eine Grenze voll (unabhängig), und bei +2 % mehr Zeit bleibt es nur in 2 von 20 zulässig; die Überstundengrenze ist beim Optimum der Kennzahl häufiger voll (17 gegen 12), die Regelzeitgrenze beim wahren Optimum (17 gegen 3). In der Familie Person hält das wahre Optimum sogar besser (3 gegen 1 bei +2 %). (3) „Ein Zuschlag bringt die Optima zusammen“: bei keinem der vier Zuschläge werden die Optima in einer der 40 Instanzen gleich; der Zuschlag verteuert die Verlagerung, er verhindert sie nicht. Die Verlagerung ist hier **durch den Aufbau groß**: Überstunden kosten die Kennzahl nichts, und die Dosis-Wirkung über den Überstundenanteil zeigt das: ohne Platz wandert nichts, bei Platz in Höhe der ganzen Regelkapazität (Überstundenanteil 100 %) wandert alles. Von der Literatur ist nur gelesen: der Anfang des Zitats von Campbell (1979, „Assessing the impact of planned social change“) über Wikipedia, das Original nicht; die Bullwhip-Literatur ist nicht gelesen und nicht zitiert.

## Ehrliche Grenzen

- **Durch den Aufbau groß:** Dass Überstunden in der Kennzahl nichts kosten, ist die Annahme, die die Verlagerung erzeugt; die Demo misst, wie stark sie wirkt, nicht ob sie in einem echten Betrieb vorkommt.
- **Ein Zufallsmodell:** Kosten (1 bis 99), Zeiten (1 bis 9), `f_R = 80 %` und `f_Z = 50 %` sind gewählte Größen; echte Pläne haben andere und mehr Nebenbedingungen.
- **Alle Pläne aufgezählt:** bis 279 936; die Aufzählung liefert hier die Optima der jeweiligen Instanz. Bei größeren Problemen braucht es einen Löser; die Größe der Wirkung wächst mit der Instanzgröße (Kurzprobe mit 10 Instanzen, Zuschlag 125 %: Median des Verlusts 13,5 % bei einer Person und 5 Aufgaben, 85 % bei 3 Personen und 7 Aufgaben), für größere Probleme ist sie nicht untersucht.
- **Gleichstand: kleinster Index:** Bei Gleichstand wählt die Regel, nicht das Ziel (Stück 5). Das gilt für die Wahl der Optima; bei der Frage, wer die meisten Überstunden trägt, entscheidet der Index nicht: jede Person auf dem Maximum zählt als Trägerin. Die „im Mittel billigste“ Person ist die mit der kleinsten Kostensumme; bei gleichem Mittel zählte der kleinste Index, das kommt in den 40 festen Instanzen nicht vor.
- **Der Rand ist ein Test, keine Wahrscheinlichkeit:** „+δ % Zeit“ verlängert alle Zeiten gleichmäßig; echte Schwankungen sind ungleich verteilt.
- **Kein Satz:** Die Zahlen sind Zählungen über 20 feste Instanzen und drei Personen, nicht allgemein.

## Verifikation

Insgesamt 488 Tests (`pytest tests/`), 474 grün und 14 übersprungen (Eigenschaftstests auf Instanzen, in denen nichts zulässig ist).

- **Kern:** Handbeispiel (1 Person, 3 Aufgaben, 8 Pläne) von Hand: zulässige Pläne, KPI und Überstundenkosten, beide Optima, Gewinn 70 %, Verlust 12,727 %, Rand und Reserve; Pläne, Lasten, Optima, Rand und Reserve gegen reines Python (`itertools.product`, Schleifen).
- **Eigenschaften:** das Optimum der Kennzahl hat nie einen schlechteren KPI, das wahre nie höhere wahre Kosten; ohne Überstundenkapazität sind beide Optima gleich; mehr Überstundenkapazität macht den besten KPI nie schlechter; eine Reserve macht das wahre Optimum nie billiger; ein bei mehr Zeit zulässiger Plan ist bei weniger Zeit zulässig; die Kosten der Optima hängen nicht von der Nummerierung der Personen ab; Determinismus.
- **Randfälle:** nichts zulässig, genau ein zulässiger Plan, Überstundenkapazität null, sehr große Kapazität, eine Person, jede Familie mal jedes Ziel, kleinste und größte Instanz, Aufzählungsgrenze.
- **Verdikte:** reine Funktionen, jede Verzweigung und jede Zahl im Text an Hand- oder Presetwerten (`tests/test_verdicts.py`).
- **Presets:** Vollständigkeit, Werte innerhalb der Reglergrenzen, Standard-Preset gleich Standardeinstellung, kein anderes Preset gleich den Voreinstellungen, und dass jedes Preset zeigt, was sein Name sagt.
- **Oberfläche:** AppTest-Rauchtest (jedes Preset, jeder Regler am Minimum und Maximum, beide Ziele, beide Familien, Größen, alle Zählungen), Footer-Test, Layout.
- **Claims:** jede Zahl dieser README in `tests/test_claims.py`.

## Dateistruktur

| Datei | Zweck |
|---|---|
| `.github/workflows/tests.yml` | CI: Push, Pull Request, wöchentlicher Canary |
| `.gitignore` | venv, Caches, Streamlit-Secrets |
| `.streamlit/config.toml` | Streamlit-Einstellungen (keine Nutzungsstatistik) |
| `app.py` | Streamlit-App |
| `requirements-dev.txt` | Laufzeit plus pytest |
| `requirements.txt` | Laufzeit-Bibliotheken (ungepinnt) |
| `vrl_algorithm.py` | Kern: Aufzählung, Zulässigkeit, Optima, Rand, Reserve |
| `vrl_constants.py` | Regler-Grenzen, feste Annahmen, Farben, Presets |
| `vrl_evaluation.py` | Experimente, Sweeps, Verdikte |
| `vrl_layout.py` | Fester Kopf (Stylesheet) |
| `vrl_pdf_export.py` | PDF-Export des Ergebnisses |
| `vrl_presets.py` | Permalink (Begrenzen), Presets (Schnellstart in der Seitenleiste), Zufalls-Seed-Button |
| `vrl_scenario.py` | Instanzen (Kosten, Zeit, Kapazitäten) |
| `vrl_visualization.py` | Plotly-Abbildungen (Achsen gesperrt) |
| `tests/` | Handbeispiel, Orakel, Eigenschaften, Randfälle, Verdikte, Presets, Claims, Layout, AppTest-Smoke-Test, Footer, Laufzeit-Importe |

## Bewusst nicht umgesetzt

- **Keine fehlende Nebenbedingung:** Dass dem Modell eine Nebenbedingung fehlt, ist Stück 9; hier ist die Last in einer **nicht gemessenen Größe** frei.
- **Keine Verfahren gegen die Verlagerung:** Wie man das Ziel vor dem Einsatz gegen die Wirklichkeit prüft, ist Stück 13.
- **Kein Strafterm:** Die Überstunden weich ins Ziel zu nehmen, ist Stück 6; hier gibt es nur den Zuschlag `g` der wahren Kosten.
- **Kein Löser:** Alle Pläne sind aufgezählt.
- **Keine Nachbauten der Literatur:** Weder Campbells Gesetz noch Bullwhip sind nachgebaut.

## Lokal ausführen

```bash
python3 -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate

pip install -r requirements.txt
streamlit run app.py
```

## Tests ausführen

```bash
pip install -r requirements-dev.txt
pytest tests/ -v
```

Gebaut mit Streamlit, Plotly, NumPy und SciPy.

---

Diese Demo ist Teil des Portfolios von [Sebastian Hanisch](https://sebastianhanisch.net) – Operations Research und Machine Learning ([Über mich](https://sebastianhanisch.net/ueber-mich.html)). Mehr zur Reihe: [Zielfunktionsdesign: das Ziel ist das Modell](https://sebastianhanisch.net/konzepte-zielfunktionsdesign.html).

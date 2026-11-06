"""Verlagerung und Randlösungen - interaktive Konzept-Demo
Sebastian Hanisch - Operations Research und Machine Learning

Stück 10 der Reihe „Zielfunktionsdesign“: Aufgaben werden auf Personen verteilt, jede in der Regelzeit (die Kennzahl misst sie) oder in Überstunden (die Kennzahl sieht sie nicht).
Die Demo zeigt, wie viel der Verbesserung der Kennzahl nur verschoben ist, wer zahlt, wie weit der Plan am Rand der Kapazität liegt und was eine Reserve kostet.

Lauffähig mit: streamlit run app.py
"""

import streamlit as st

import vrl_constants as C
from vrl_evaluation import (
    Settings,
    analyse,
    compare,
    de,
    dosis_rows,
    edge_info,
    pct,
    person_text,
    reserve_rows,
    summary_dosis,
    summary_edge,
    summary_g,
    summary_payers,
    summary_reserve,
    sweep_all,
    verdict_compare,
    verdict_dosis,
    verdict_dosis_sweep,
    verdict_edge,
    verdict_edge_sweep,
    verdict_g_sweep,
    verdict_payers,
    verdict_payers_sweep,
    verdict_reserve,
    verdict_reserve_sweep,
    vtext,
    who_pays,
)
from vrl_layout import dunkles_design, kopf_css
from vrl_pdf_export import build_pdf
from vrl_presets import (
    bounds,
    init_session_state_defaults,
    load_permalink_settings,
    randomize_seed,
    sidebar_presets,
    sync_query_params,
)
from vrl_visualization import build_cloud, build_dosis, build_dosis_sweep, build_edge, build_payers, build_reserve

st.set_page_config(page_title="Verlagerung und Randlösungen – Sebastian Hanisch", layout="wide")


@st.cache_data(show_spinner=False)
def _analysis(settings):
    return analyse(settings)


@st.cache_data(show_spinner="40 feste Instanzen werden gerechnet (je 279 936 Pläne, zwei Familien) ...")
def _sweep():
    return sweep_all()


# Fester Kopf: nur der Titel bleibt beim Scrollen oben (Stylesheet in vrl_layout.py).
st.html(kopf_css(dunkles_design()))
with st.container(key="kopf"):
    st.title("🚚 Verlagerung und Randlösungen")
st.markdown(
    """
**Wer zahlt, wenn das Ziel gut aussieht?** **m Aufgaben** werden auf **n Personen** verteilt; jede Aufgabe geht in die **Regelzeit** oder in **Überstunden**. Die **Kennzahl** misst nur die Kosten der Regelzeit-Aufgaben, die Überstunden sind
erlaubt, begrenzt und für die Kennzahl unsichtbar. Die **wahren Kosten** zählen die Überstunden mit einem Zuschlag. Wer die Kennzahl optimiert, schiebt Last in die unsichtbaren Stunden: die Kennzahl wird besser, die Wahrheit nicht.
Außerdem liegt jedes Optimum am **Rand** der Kapazität, und eine **Reserve** kostet.

Weiter unten: **🔬 Die Kennzahl und die Wahrheit**, **🔬 Der Ort**, **🔬 Wer zahlt**, **🔬 Der Rand**, **🔬 Die Reserve**, **🚧 Wo die Annahmen enden** und der Expander **📐 Mathematische Formulierung**.
"""
)

with st.expander("So funktioniert der Vergleich", expanded=True):
    st.markdown(
        """
1. **Pläne:** jede Aufgabe bekommt eine Person und eine Schicht (Regelzeit oder Überstunden); alle (2n)^m Pläne werden aufgezählt. Zulässig ist, wer in der Regelzeit höchstens die Regelkapazität und in den Überstunden höchstens die Überstundenkapazität je Person nutzt.
2. **Kennzahl** = Summe der Kosten der Regelzeit-Aufgaben. **Wahre Kosten** = Kennzahl + Zuschlag mal Kosten der Überstunden-Aufgaben (Zuschlag 100 %: eine Überstunde kostet so viel wie eine Regelstunde).
3. **Optimum der Kennzahl** und **wahres Optimum** werden immer beide gezeigt (bei Gleichstand der kleinste Index der Aufzählung); der Regler „Ziel des Optimierers“ wählt, welches der Plan ist.
4. **Messungen, kein Satz:** Alle Zahlen sind Zählungen und Spannen über feste Instanzen dieses Zufallsmodells; sie sagen nichts über echte Schichtpläne.
        """
    )

st.caption("🔗 Die Adresszeile oben spiegelt Ihre aktuelle Konfiguration wider – einfach kopieren, um ein Szenario zu teilen.")

load_permalink_settings()
init_session_state_defaults()

with st.sidebar:
    sidebar_presets()  # Schnellstart oben, das aktive Preset ist hervorgehoben
    st.header("⚙️ Einstellungen")
    st.markdown("**Instanz**")
    n = st.slider("Personen n", *bounds("n_slider"), key="n_slider", help="Alle (2n)^m Pläne werden aufgezählt (bis 279 936).")
    m = st.slider("Aufgaben m", *bounds("m_slider"), key="m_slider")
    family = st.selectbox("Kosten", list(range(len(C.FAMILIES))), key="family_select", format_func=lambda i: C.FAMILIES[i], help="Beim Personeneffekt ist eine Person für fast alle Aufgaben billiger.")
    seed = st.number_input("Zufalls-Seed der Instanz", *bounds("seed_input"), key="seed_input", step=1)
    st.button("🎲 Neue Instanz generieren", width="stretch", on_click=randomize_seed)
    st.markdown("**Kapazität und Preis**")
    fr = st.slider("Regelkapazität in % des Durchschnittsbedarfs", *bounds("fr_slider"), key="fr_slider", step=C.FR_STEP,
                   help="Aufgerundet: fR mal Summe der mittleren Zeiten je Aufgabe, geteilt durch n.")
    fz = st.slider("Überstundenkapazität in % der Regelkapazität", *bounds("fz_slider"), key="fz_slider", step=C.FZ_STEP,
                   help="Der Ort, in den man ausweichen kann: bei 0 % gibt es keinen, und nichts wandert.")
    g = st.slider("Zuschlag der Überstunden in %", *bounds("g_slider"), key="g_slider", step=C.G_STEP, help="100 %: eine Überstunde kostet so viel wie eine Regelstunde; 200 %: das Doppelte.")
    st.markdown("**Rand und Reserve**")
    delta = st.slider("Alle Zeiten wachsen um … %", *bounds("delta_slider"), key="delta_slider", step=C.DELTA_STEP, help="Sprödheit: bleibt der Plan zulässig, wenn jede Zeit um diesen Anteil wächst?")
    st.markdown("**Ziel des Optimierers**")
    objective = st.selectbox("Der Optimierer minimiert", list(range(len(C.OBJECTIVES))), key="objective_select", format_func=lambda i: C.OBJECTIVE_NAMES[C.OBJECTIVES[i]],
                             help="Beide Optima werden immer gezeigt; dieser Regler wählt, welches der Plan ist.")

sync_query_params({"n_slider": int(n), "m_slider": int(m), "family_select": int(family), "seed_input": int(seed), "fr_slider": int(fr), "fz_slider": int(fz), "g_slider": int(g), "delta_slider": int(delta),
                   "objective_select": int(objective)})

settings = Settings(int(n), int(m), int(family), int(seed), int(fr), int(fz), int(g), int(delta), int(objective))
a = _analysis(settings)
c = compare(a)
chosen = None if c["kpi_opt"] is None else (c["kpi_opt"] if settings.objective == 0 else c["true_opt"])
other = None if c["kpi_opt"] is None else (c["true_opt"] if settings.objective == 0 else c["kpi_opt"])

# --- Ergebnis ------------------------------------------------------------------------------------------------------------------------------

st.markdown("## 🎯 Ergebnis: wie viel der Verbesserung ist nur verschoben?")
m1, m2, m3 = st.columns(3)
if chosen is None:
    m1.metric("Gewählter Plan", "unlösbar")
else:
    m1.metric(f"Kennzahl des Plans ({'Kennzahl' if settings.objective == 0 else 'wahre Kosten'} minimiert)", str(chosen["kpi"]), delta=f"{pct(abs((other['kpi'] - chosen['kpi']) / other['kpi']) if other['kpi'] else 0.0)} {'besser' if chosen['kpi'] <= other['kpi'] else 'schlechter'} als das andere Optimum", delta_color="off")
    m2.metric("Wahre Kosten des Plans", vtext(chosen["true"]), delta=f"{pct(abs((chosen['true'] - other['true']) / other['true']) if other['true'] else 0.0)} {'höher' if chosen['true'] >= other['true'] else 'niedriger'} als das andere Optimum", delta_color="off")
    m3.metric("Aufgaben in Überstunden", f"{chosen['nz']} von {settings.m}", delta=f"{chosen['zhours']} Stunden; Anteil an den wahren Kosten {pct(chosen['zshare'], 0)}", delta_color="off")
st.plotly_chart(build_cloud(a.p, settings.g, a.kpi_idx, a.true_idx), width="stretch", key="cloud_chart")
st.caption("Jeder Punkt ist ein zulässiger Plan: Kennzahl waagerecht, wahre Kosten senkrecht. Links unten wäre für beides gut. Die Raute (Optimum der Kennzahl) liegt ganz links, aber hoch; der Stern (wahres Optimum) liegt tief, aber weiter rechts.")
st.download_button("📄 Ergebnis als PDF", data=build_pdf(a), file_name="verlagerung.pdf", mime="application/pdf", key="pdf_download")

# --- Kernfrage -----------------------------------------------------------------------------------------------------------------------------

st.markdown("## ❓ Kernfrage: Ist das Optimum der Kennzahl auch das, was zählt?")
kind, text = verdict_compare(c)
getattr(st, kind)(text)

st.markdown("---")

# --- Experimente ---------------------------------------------------------------------------------------------------------------------------

st.subheader("🔬 Die Kennzahl und die Wahrheit")
st.caption(f"Die beiden Optima nebeneinander; Regelkapazität {a.p.inst.cap_r} Stunden, Überstundenkapazität {a.p.inst.cap_z} Stunden je Person, {c['n_feasible']} von {c['n_plans']} Plänen zulässig. R: Regelzeit, Ü: Überstunden.")
if c["kpi_opt"] is not None:
    rows_md = ["| | Kennzahl | Wahre Kosten | Aufgaben in Ü | Stunden in Ü | Plan |", "|---|---|---|---|---|---|"]
    for label, info in (("**Optimum der Kennzahl**", c["kpi_opt"]), ("**Wahres Optimum**", c["true_opt"])):
        rows_md.append(f"| {label} | {info['kpi']} | {vtext(info['true'])} | {info['nz']} | {info['zhours']} | {person_text(info)} |")
    st.markdown("\n".join(rows_md))
else:
    st.info("Mit diesen Kapazitäten ist kein Plan zulässig.")
if st.toggle("Optimum der Kennzahl gegen wahres Optimum über feste Instanzen nachrechnen (je Zuschlag)", value=False, key="sweep_g"):
    sw = _sweep()
    kind, text = verdict_g_sweep({fam: summary_g(recs) for fam, recs in sw.items()})
    getattr(st, kind)(text)

st.markdown("---")

st.subheader("🔬 Der Ort")
st.caption("Die Verlagerung folgt dem Ort, in den man ausweichen kann: die Überstundenkapazität von 0 bis 100 % der Regelkapazität auf dieser Instanz.")
drows = dosis_rows(a)
st.plotly_chart(build_dosis(drows), width="stretch", key="dosis_chart")
kind, text = verdict_dosis(drows)
getattr(st, kind)(text)
if st.toggle("Den Ort über feste Instanzen nachrechnen (je Überstundenanteil)", value=False, key="sweep_dosis"):
    sw = _sweep()
    res = {fam: summary_dosis(recs) for fam, recs in sw.items()}
    kind, text = verdict_dosis_sweep(res)
    getattr(st, kind)(text)
    st.plotly_chart(build_dosis_sweep(res), width="stretch", key="sweep_dosis_chart")

st.markdown("---")

st.subheader("🔬 Wer zahlt")
st.caption("Wohin die Last wandert: Überstunden je Person im Optimum der Kennzahl und im wahren Optimum, und der Anteil der Überstunden an den wahren Kosten.")
w = who_pays(a)
if w is not None:
    st.plotly_chart(build_payers(w), width="stretch", key="payers_chart")
kind, text = verdict_payers(w)
getattr(st, kind)(text)
if st.toggle("Wer zahlt über feste Instanzen nachrechnen", value=False, key="sweep_payers"):
    sw = _sweep()
    kind, text = verdict_payers_sweep({fam: summary_payers(recs) for fam, recs in sw.items()})
    getattr(st, kind)(text)

st.markdown("---")

st.subheader("🔬 Der Rand")
st.caption("Ein Optimum liegt auf dem Rand der Kapazität (100 % Auslastung heißt: Reserve null). Wachsen alle Zeiten um den eingestellten Anteil, bleibt der Plan zulässig?")
e = edge_info(a)
if e is not None:
    st.plotly_chart(build_edge(e), width="stretch", key="edge_chart")
kind, text = verdict_edge(e)
getattr(st, kind)(text)
if st.toggle("Den Rand über feste Instanzen nachrechnen (Sprödheit)", value=False, key="sweep_edge"):
    sw = _sweep()
    kind, text = verdict_edge_sweep({fam: summary_edge(recs) for fam, recs in sw.items()})
    getattr(st, kind)(text)

st.markdown("---")

st.subheader("🔬 Die Reserve")
st.caption("Kapazitäten durch 1 + Reserve geteilt (abgerundet) und neu gelöst: was kostet der Abstand zum Rand? Wahre Kosten des Optimums gegen das ohne Reserve.")
rrows = reserve_rows(a)
if rrows:
    st.plotly_chart(build_reserve(rrows), width="stretch", key="reserve_chart")
kind, text = verdict_reserve(rrows)
getattr(st, kind)(text)
if st.toggle("Den Preis der Reserve über feste Instanzen nachrechnen", value=False, key="sweep_reserve"):
    sw = _sweep()
    kind, text = verdict_reserve_sweep({fam: summary_reserve(recs) for fam, recs in sw.items()})
    getattr(st, kind)(text)

st.markdown("---")

# --- Grenzen -------------------------------------------------------------------------------------------------------------------------------

st.subheader("🚧 Wo die Annahmen enden")
st.markdown(
    """
| Annahme | Was passiert, wenn sie verletzt ist | Wer setzt an |
|---|---|---|
| **Die Überstunden sind frei und begrenzt** | Der Effekt ist durch den Aufbau groß (der unsichtbare Ort kostet die Kennzahl nichts); die Aussage ist die Dosis-Wirkung über die Überstundenkapazität, nicht die absolute Höhe | Stück 9 (Lücken ausnutzen) |
| **Kosten gleich, Zuschlag als Faktor** | Überstunden haben hier dieselben Kosten wie Regelzeit mal Zuschlag; echte Überstunden unterscheiden sich in Person, Tarif und Folgeschäden | Stück 6 (Hart gegen weich) |
| **Alle Pläne aufgezählt, wenige Personen** | Bis 279 936 Pläne (3 Personen, 7 Aufgaben); bei großen Problemen braucht es einen Löser, das Verhalten ändert sich nicht | Dokumentation des Lösers |
| **Sprödheit = alle Zeiten wachsen gleichmäßig** | Eine zufällige Störung je Aufgabe oder eine Verschiebung des Ziels kippt andere Pläne | Stück 11 (Sensitivität und Planstabilität) |
| **Reserve = Kapazität durch 1 + δ, abgerundet** | Bei ganzen Zahlen ergeben 5 und 10 % dieselbe Kapazität; andere Reserveregeln kosten anders | – |
| **Wer zahlt: die Personen** | Gezahlt wird im unsichtbaren Konto, nicht von einer Person; ob die Last einen anderen Zahler trifft (Lieferant, Kunde, Folgeperiode), zeigt das Modell nicht | `bullwhip-demo` (Lieferkette) |
"""
)

st.markdown("---")

with st.expander("📐 Mathematische Formulierung"):
    st.markdown(
        r"""
**Problem.** $m$ Aufgaben, $n$ Personen. Jede Aufgabe $j$ bekommt eine Person $x_j$ und eine Schicht $s_j \in \{R, Z\}$ (Regelzeit, Überstunden). Kosten $a_{ij}$, Zeit $b_{ij}$.

**Zulässig.** Für jede Person $i$: Regellast $L^R_i = \sum_{j: x_j = i, s_j = R} b_{ij} \le \mathrm{cap}_R$ und Überstundenlast $L^Z_i = \sum_{j: x_j = i, s_j = Z} b_{ij} \le \mathrm{cap}_Z$. Dabei $\mathrm{cap}_R = \lceil f_R \sum_j \bar b_j / n \rceil$ und $\mathrm{cap}_Z = \lceil f_Z\, \mathrm{cap}_R \rceil$.

**Kennzahl und wahre Kosten.** $\mathrm{KPI} = \sum_{j: s_j = R} a_{x_j j}$ und $T_g = \mathrm{KPI} + g \sum_{j: s_j = Z} a_{x_j j}$ mit dem Zuschlag $g \ge 1$. Das **Optimum der Kennzahl** minimiert KPI, das **wahre Optimum** $T_g$ (bei Gleichstand der kleinste Index).

**Verschiebung.** Ohne Überstundenkapazität ($\mathrm{cap}_Z = 0$) ist jede Aufgabe in der Regelzeit, KPI $= T_g$ und die Optima sind gleich. Mit Kapazität senkt das Optimum der Kennzahl KPI, indem es Aufgaben in die Überstunden legt (bis $L^Z_i = \mathrm{cap}_Z$), und wählt dort die Person ohne Blick auf die Kosten: $T_g$ steigt.

**Rand und Sprödheit.** Ein Plan hat Reserve null in Person $i$, wenn $L^R_i = \mathrm{cap}_R$ oder $L^Z_i = \mathrm{cap}_Z$. Wachsen alle Zeiten um $\delta$ Prozent, bleibt er zulässig, wenn $L(100 + \delta) \le 100\,\mathrm{cap}$ (ganzzahlig, exakt). **Reserve:** Kapazitäten $\lfloor 100\,\mathrm{cap} / (100 + \delta) \rfloor$; Preis der Reserve = $T_g$ des neuen Optimums gegen das alte.

**Literatur.** Campbell (1979, „Assessing the impact of planned social change“): „The more any quantitative social indicator is used for social decision-making, the more subject it will be to corruption …“ (nur der Anfang des Zitats über eine Seite gelesen, die Originalarbeit nicht). Diese Demo übernimmt keine Zahl daraus; alle Zahlen sind Messungen an dem Zufallsmodell der Demo.
        """
    )

st.markdown("---")
st.caption(
    "Diese Demo ist Teil des Portfolios von [Sebastian Hanisch](https://sebastianhanisch.net) – "
    "Operations Research und Machine Learning ([Über mich](https://sebastianhanisch.net/ueber-mich.html)). "
    "Mehr zu den Demos: [Interaktive Demos](https://sebastianhanisch.net/demos.html)."
)

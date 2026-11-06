"""Plotly-Abbildungen. Alle Achsen sind gesperrt (fixedrange), damit Touch-Geräte beim Scrollen nicht am Diagramm hängen bleiben."""

import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots

import vrl_algorithm as A
import vrl_constants as C

FAM_COLORS = {0: "#4c78a8", 1: "#7b5ea7"}


def lock_axes(fig):
    fig.update_xaxes(fixedrange=True)
    fig.update_yaxes(fixedrange=True)
    return fig


def _base(fig, height=360):
    fig.update_layout(height=height, margin=dict(l=10, r=10, t=30, b=10), legend=dict(orientation="h", y=-0.25), plot_bgcolor="rgba(0,0,0,0)")
    return lock_axes(fig)


def build_cloud(p: A.Problem, g: int, kpi_idx: int | None, true_idx: int | None):
    """Alle zulässigen Pläne: Kennzahl waagerecht, wahre Kosten senkrecht; die beiden Optima als Marken. Links unten wäre gut für beides, die Optima liegen aber an verschiedenen Stellen."""
    ok = p.ok
    kpi, tc = np.asarray(p.kpi, dtype=float), np.asarray(A.true_cost(p, g), dtype=float)
    fig = go.Figure(go.Scattergl(x=kpi[ok], y=tc[ok], mode="markers", marker=dict(size=3, color=C.COLOR_ALL), name="zulässige Pläne", hovertemplate="KPI %{x:.0f} / wahre Kosten %{y:.1f}<extra></extra>"))
    if kpi_idx is not None:
        fig.add_trace(go.Scatter(x=[kpi[kpi_idx]], y=[tc[kpi_idx]], mode="markers", marker=dict(symbol="diamond", size=14, color=C.COLOR_KPI, line=dict(width=1.5, color="white")), name="Optimum der Kennzahl",
                                 hovertemplate="Optimum der Kennzahl: KPI %{x:.0f} / wahre Kosten %{y:.1f}<extra></extra>"))
    if true_idx is not None:
        fig.add_trace(go.Scatter(x=[kpi[true_idx]], y=[tc[true_idx]], mode="markers", marker=dict(symbol="star", size=16, color=C.COLOR_TRUE, line=dict(width=1.5, color="white")), name="wahres Optimum",
                                 hovertemplate="wahres Optimum: KPI %{x:.0f} / wahre Kosten %{y:.1f}<extra></extra>"))
    fig.update_xaxes(title_text="Kennzahl (Kosten der Regelzeit-Aufgaben, kleiner ist besser)")
    fig.update_yaxes(title_text="Wahre Kosten (mit Zuschlag)")
    return _base(fig, height=420)


def build_dosis(rows: list[dict]):
    """Kennzahl besser und wahre Kosten höher in Abhängigkeit von der Überstundenkapazität (Anteil der Regelkapazität)."""
    rows = [r for r in rows if r["solvable"]]
    xs = [f"{r['fz']} % ({r['cap_z']} h)" for r in rows]
    fig = go.Figure([go.Bar(x=xs, y=[(r["gain"] or 0.0) * 100 for r in rows], name="Kennzahl besser", marker_color=C.COLOR_KPI, hovertemplate="%{x}: Kennzahl %{y:.1f} % besser<extra></extra>"),
                     go.Bar(x=xs, y=[(r["loss"] or 0.0) * 100 for r in rows], name="wahre Kosten höher", marker_color=C.COLOR_BAD, hovertemplate="%{x}: wahre Kosten %{y:.1f} % höher<extra></extra>")])
    fig.update_layout(barmode="group")
    fig.update_xaxes(type="category", title_text="Überstundenkapazität (Anteil der Regelkapazität, Stunden je Person)")
    fig.update_yaxes(title_text="Prozent")
    return _base(fig, height=320)


def build_payers(w: dict):
    """Überstunden je Person im Optimum der Kennzahl und im wahren Optimum."""
    k, t = w["kpi_opt"], w["true_opt"]
    names = [f"Person {i + 1}" for i in range(len(k["zload"]))]
    fig = go.Figure([go.Bar(x=names, y=list(k["zload"]), name="Optimum der Kennzahl", marker_color=C.COLOR_KPI, hovertemplate="%{x}: %{y} h Überstunden<extra></extra>"),
                     go.Bar(x=names, y=list(t["zload"]), name="wahres Optimum", marker_color=C.COLOR_TRUE, hovertemplate="%{x}: %{y} h Überstunden<extra></extra>")])
    fig.add_hline(y=k["caps"][1], line=dict(color=C.COLOR_BAD, dash="dash"), annotation_text="Überstundenkapazität", annotation_position="top left")
    fig.update_layout(barmode="group")
    fig.update_xaxes(type="category")
    fig.update_yaxes(title_text="Überstunden in Stunden")
    return _base(fig, height=320)


def build_edge(e: dict):
    """Auslastung der Grenzen in Prozent (Regelzeit oben, Überstunden unten) je Person im Optimum der Kennzahl und im wahren Optimum; 100 % ist der Rand."""
    cap_r, cap_z = e["caps"]
    n = len(e["kpi"]["rload"])
    names = [f"Person {i + 1}" for i in range(n)]
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.14, subplot_titles=("Regelzeit: Auslastung in % der Kapazität", "Überstunden: Auslastung in % der Kapazität"))
    for key, color, label in (("kpi", C.COLOR_KPI, "Optimum der Kennzahl"), ("true", C.COLOR_TRUE, "wahres Optimum")):
        fig.add_trace(go.Bar(x=names, y=[100.0 * v / cap_r for v in e[key]["rload"]], name=label, marker_color=color, legendgroup=key, hovertemplate="%{x}: %{y:.0f} %<extra></extra>"), row=1, col=1)
        fig.add_trace(go.Bar(x=names, y=[100.0 * v / cap_z if cap_z else 0.0 for v in e[key]["zload"]], name=label, marker_color=color, legendgroup=key, showlegend=False, hovertemplate="%{x}: %{y:.0f} %<extra></extra>"),
                      row=2, col=1)
    for r in (1, 2):
        fig.add_hline(y=100, line=dict(color=C.COLOR_BAD, dash="dash"), row=r, col=1)
    fig.update_layout(barmode="group")
    fig.update_xaxes(type="category")
    fig.update_yaxes(range=[0, 125])
    return _base(fig, height=420)


def build_reserve(rows: list[dict]):
    """Preis der Reserve: wahre Kosten des Optimums mit Reserve gegen das ohne, in Prozent."""
    rows = [r for r in rows if r["rise"] is not None]
    fig = go.Figure(go.Bar(x=[f"{r['delta']} % (Kapazität {r['cap_r']} h / {r['cap_z']} h)" for r in rows], y=[r["rise"] * 100 for r in rows], marker_color=C.COLOR_REAL,
                           text=[f"{r['rise'] * 100:.1f} %".replace(".", ",") for r in rows], textposition="outside", hovertemplate="Reserve %{x}: %{y:.1f} % mehr<extra></extra>"))
    fig.update_xaxes(type="category", title_text="Reserve (alle Kapazitäten durch 1 + Reserve geteilt, abgerundet)")
    fig.update_yaxes(title_text="Wahre Kosten höher in %", range=[0, max(10.0, max((r["rise"] for r in rows), default=0.0) * 125)])
    return _base(fig, height=300)


def build_dosis_sweep(res: dict):
    """Median von „Kennzahl besser“ und „wahre Kosten höher“ je Überstundenanteil und Familie."""
    fzs = C.SWEEP_FZS
    fig = go.Figure()
    for fam, s in res.items():
        fig.add_trace(go.Scatter(x=[str(fz) + " %" for fz in fzs], y=[s[fz]["gain"][1] * 100 for fz in fzs], mode="lines+markers", name=f"{C.FAMILIES[fam]}: Kennzahl besser", line=dict(color=FAM_COLORS[fam])))
        fig.add_trace(go.Scatter(x=[str(fz) + " %" for fz in fzs], y=[s[fz]["loss"][1] * 100 for fz in fzs], mode="lines+markers", name=f"{C.FAMILIES[fam]}: wahre Kosten höher", line=dict(color=FAM_COLORS[fam], dash="dash")))
    fig.update_xaxes(type="category", title_text="Überstundenkapazität (Anteil der Regelkapazität)")
    fig.update_yaxes(title_text="Median in %")
    return _base(fig, height=340)

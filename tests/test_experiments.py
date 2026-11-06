"""Experimente der App: jedes Preset, jede Familie, jeder Regler an den Grenzen, beide Ziele und alle Zählungen laufen ohne Fehler."""

import os
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

import vrl_constants as C

APP = str(Path(__file__).resolve().parent.parent / "app.py")
TIMEOUT = int(os.environ.get("APPTEST_TIMEOUT", "300"))


def _app() -> AppTest:
    at = AppTest.from_file(APP, default_timeout=TIMEOUT)
    at.run()
    assert not at.exception, [str(e) for e in at.exception]
    return at


def _texts(at) -> str:
    return " ".join(m.value for kind in ("success", "info", "warning") for m in getattr(at, kind))


@pytest.mark.parametrize("name", list(C.PRESETS))
def test_every_preset_runs_and_shows_a_verdict(name):
    at = _app()
    at.sidebar.button(key=f"preset_{name}").click().run()
    assert not at.exception, (name, [str(e) for e in at.exception])
    assert "Optimum der Kennzahl" in _texts(at)


def test_default_preset_shows_the_displacement():
    assert "**KPI 23** statt 193 (**88,1 % besser**)" in _texts(_app())


@pytest.mark.parametrize("objective", [0, 1])
def test_both_objectives_run(objective):
    at = _app()
    at.sidebar.selectbox(key="objective_select").set_value(objective).run()
    assert not at.exception, [str(e) for e in at.exception]


@pytest.mark.parametrize("family", range(len(C.FAMILIES)))
def test_every_family_runs(family):
    at = _app()
    at.sidebar.selectbox(key="family_select").set_value(family).run()
    assert not at.exception, [str(e) for e in at.exception]


@pytest.mark.parametrize("key,value", [("fr_slider", C.FR_MIN), ("fr_slider", C.FR_MAX), ("fz_slider", C.FZ_MIN), ("fz_slider", C.FZ_MAX), ("g_slider", C.G_MIN), ("g_slider", C.G_MAX),
                                       ("delta_slider", C.DELTA_MIN), ("delta_slider", C.DELTA_MAX)])
def test_every_parameter_extreme_runs(key, value):
    at = _app()
    at.sidebar.slider(key=key).set_value(value).run()
    assert not at.exception, [str(e) for e in at.exception]


def test_without_overtime_capacity_nothing_moves():
    at = _app()
    at.sidebar.slider(key="fz_slider").set_value(0).run()
    assert not at.exception and "es gibt nichts zu verlagern" in _texts(at)


@pytest.mark.parametrize("n,m", [(1, 3), (1, 7), (2, 5), (3, 5)])
def test_sizes_run(n, m):
    at = _app()
    at.sidebar.slider(key="n_slider").set_value(n).run()
    at.sidebar.slider(key="m_slider").set_value(m).run()
    assert not at.exception, [str(e) for e in at.exception]
    assert "Optimum der Kennzahl" in _texts(at)


def test_the_sweeps_run_when_switched_on():
    at = _app()
    for key in ("sweep_g", "sweep_dosis", "sweep_payers", "sweep_edge", "sweep_reserve"):
        at.toggle(key=key).set_value(True).run()
        assert not at.exception, (key, [str(e) for e in at.exception])
    text = _texts(at)
    assert "Optimum der Kennzahl gegen wahres Optimum, 3 Personen, 7 Aufgaben" in text and "Überstundenanteil (Median, Zuschlag 125 %)" in text and "Wer zahlt (Median, Zuschlag 125 %)" in text
    assert "Der Rand (von 20 Instanzen, Zuschlag 125 %)" in text and "Preis der Reserve" in text

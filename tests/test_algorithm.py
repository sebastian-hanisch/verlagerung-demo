"""Handwerte: jede Einheit des Kerns an einem Beispiel, das von Hand nachgerechnet ist (DEMO-PLAYBOOK §1b)."""

import itertools

import numpy as np
import pytest

import vrl_algorithm as A
import vrl_constants as C
import vrl_evaluation as ev
import vrl_scenario as S

FEASIBLE = [1, 4, 6]


def test_plans_follow_the_order_of_itertools_product():
    for n, m in ((1, 3), (2, 3), (2, 4)):
        assert (A.plans(n, m) == np.array(list(itertools.product(range(2 * n), repeat=m)))).all()
    with pytest.raises(ValueError):
        A.plans(3, 8)


def test_hand_example_loads_costs_and_feasibility(hand_problem):
    p = hand_problem
    assert list(np.flatnonzero(p.ok)) == FEASIBLE
    assert [int(p.rload[k][0]) for k in range(8)] == [9, 5, 7, 3, 6, 2, 4, 0]
    assert [int(p.zload[k][0]) for k in range(8)] == [0, 4, 2, 6, 3, 7, 5, 9]
    assert [int(p.kpi[k]) for k in FEASIBLE] == [10, 9, 3] and [int(p.zcost[k]) for k in FEASIBLE] == [3, 4, 10] and [int(p.nz[k]) for k in FEASIBLE] == [1, 1, 2]


def test_hand_example_true_costs_for_both_surcharges(hand_problem):
    p = hand_problem
    assert [float(A.true_cost(p, 125)[k]) for k in FEASIBLE] == [13.75, 14.0, 15.5]
    assert [float(A.true_cost(p, 100)[k]) for k in FEASIBLE] == [13.0, 13.0, 13.0]
    assert [float(A.true_cost(p, 200)[k]) for k in FEASIBLE] == [16.0, 17.0, 23.0]


def test_hand_example_optima(hand_problem):
    p = hand_problem
    assert A.best(p, p.kpi) == 6                                           # KPI 3
    assert A.best(p, A.true_cost(p, 125)) == 1                             # 13,75
    assert A.best(p, A.true_cost(p, 100)) == 1                             # Gleichstand: der erste Plan der Aufzählung
    assert A.best(p, p.kpi, np.zeros(8, dtype=bool)) is None


def test_hand_example_displacement_without_gain(hand_analysis):
    c = ev.compare(hand_analysis)
    assert (c["kpi_opt"]["kpi"], c["true_opt"]["kpi"], c["kpi_opt"]["true"], c["true_opt"]["true"]) == (3, 10, 15.5, 13.75)
    assert c["gain"] == pytest.approx(0.7) and c["loss"] == pytest.approx(15.5 / 13.75 - 1) and not c["same"]
    assert (c["kpi_opt"]["nz"], c["true_opt"]["nz"], c["kpi_opt"]["zhours"], c["true_opt"]["zhours"]) == (2, 1, 5, 4)
    s100 = ev.Analysis(ev.Settings(1, 3, 0, 0, 80, 50, 100, 20, 0), hand_analysis.p, hand_analysis.kpi_idx, A.best(hand_analysis.p, A.true_cost(hand_analysis.p, 100)))
    c100 = ev.compare(s100)
    assert c100["kpi_opt"]["true"] == c100["true_opt"]["true"] == 13.0 and c100["loss"] == 0 and c100["gain"] == pytest.approx(0.7)


def test_hand_example_edge_and_brittleness(hand_problem):
    p = hand_problem
    assert A.full_limits(p, 6) == {"r": [False], "z": [True]} and A.full_limits(p, 1) == {"r": [False], "z": [False]} and A.full_limits(p, 4) == {"r": [True], "z": [False]}
    assert not A.stays_feasible(p, 6, 20) and A.stays_feasible(p, 1, 20) and not A.stays_feasible(p, 1, 25) and A.stays_feasible(p, 6, 0) and not A.stays_feasible(p, 6, 1)
    assert [A.stays_feasible(p, 4, d) for d in (0, 1)] == [True, False]


def test_hand_example_reserve(hand_problem):
    p = hand_problem
    assert A.reserve_caps(p, 20) == (5, 4) and A.reserve_caps(p, 10) == (5, 4) and A.reserve_caps(p, 5) == (5, 4) and A.reserve_caps(p, 0) == (6, 5)
    for d in (5, 10, 20):
        assert A.reserve_best(p, 125, d) == 1                              # der wahre Optimalplan hat schon Reserve
    assert A.reserve_caps(p, 25) == (4, 4) and A.reserve_best(p, 125, 25) is None          # Regelkapazität 4: Plan 1 hat Regellast 5, kein Plan ist mehr zulässig

def test_hand_example_capacity_zero_makes_it_infeasible(hand_problem):
    p0 = A.with_caps(hand_problem, cap_z=0)
    assert not p0.ok.any() and A.best(p0, p0.kpi) is None
    p9 = A.with_caps(hand_problem, cap_r=9)
    assert list(np.flatnonzero(p9.ok)) == [0, 1, 2, 4, 6] and A.best(p9, p9.kpi) == 6 and A.best(p9, A.true_cost(p9, 125)) == 0


def test_hand_example_evaluation_rows(hand_analysis):
    rows = ev.dosis_rows(hand_analysis)
    assert [(r["fz"], r["cap_z"], r["solvable"]) for r in rows] == [(0, 0, False), (25, 2, False), (50, 3, True), (75, 5, True), (100, 6, True)]
    w = ev.who_pays(hand_analysis)
    assert w["total"] == 5 and w["top_share"] == 1.0 and w["persons"] == 1 and w["cheapest_pays"] and w["cheapest_alone"] and w["carriers"] == [w["cheapest"]]
    e = ev.edge_info(hand_analysis)
    assert e["kpi"]["z_full"] == 1 and not e["kpi"]["ok_delta"] and e["true"]["ok_delta"] and e["delta"] == 20 and e["kpi"]["ok_by_delta"] == {2: False, 5: False, 10: False, 20: False}
    rr = ev.reserve_rows(hand_analysis)
    assert [(r["delta"], r["cap_r"], r["cap_z"], r["rise"], r["robust"]) for r in rr] == [(5, 5, 4, 0.0, True), (10, 5, 4, 0.0, True), (20, 5, 4, 0.0, True)]


def test_capacities_and_instances_are_deterministic_and_shaped():
    inst = S.make_instance(3, 7, 0, 5)
    assert inst == S.make_instance(3, 7, 0, 5) and inst != S.make_instance(3, 7, 0, 6)
    a_, b_ = inst.arrays()
    assert a_.shape == b_.shape == (3, 7) and b_.min() >= 1 and b_.max() <= 9
    assert inst.cap_r == S.capacities(b_, 3, 80, 50)[0] and inst.cap_z == S.capacities(b_, 3, 80, 50)[1] and S.capacities(b_, 3, 80, 0)[1] == 0
    assert S.make_instance(3, 7, 0, 5, 100, 50).cap_r >= inst.cap_r and S.make_instance(3, 7, 1, 5).a != inst.a


def test_text_helpers_and_settings_defaults():
    assert ev.vtext(15.5) == "15,5" and ev.vtext(13.75) == "13,75" and ev.vtext(13.0) == "13" and ev.de(3.14159, 2) == "3,14" and ev.pct(0.7) == "70,0 %"
    s = ev.Settings()
    assert (s.n, s.m, s.fr, s.fz, s.g, s.delta, s.objective) == (3, 7, 80, 50, 125, 10, 0)
    assert ev.person_text({"tasks": [{"task": 1, "person": 2, "overtime": False}, {"task": 2, "person": 1, "overtime": True}]}) == "A1: P2 R | A2: P1 Ü"

"""Randfälle: nichts zulässig, genau ein zulässiger Plan, Überstundenkapazität null, sehr große Kapazität, n = 1, jede Familie, Aufzählungsgrenze."""

import itertools

import numpy as np
import pytest

import vrl_algorithm as A
import vrl_constants as C
import vrl_evaluation as ev
import vrl_scenario as S
from vrl_scenario import Instance


def _inst(a, b, cap_r, cap_z):
    return Instance(len(a), len(a[0]), tuple(map(tuple, a)), tuple(map(tuple, b)), cap_r, cap_z)


def _an(inst, g=125, delta=10, objective=0):
    p = A.build(inst)
    s = ev.Settings(inst.n, inst.m, 0, 0, 80, 50, g, delta, objective)
    return ev.Analysis(s, p, A.best(p, p.kpi), A.best(p, A.true_cost(p, g)))


def test_nothing_is_feasible_when_the_capacities_are_too_small():
    a = _an(_inst([[1, 2], [3, 4]], [[5, 5], [5, 5]], 3, 3))
    assert a.kpi_idx is None and a.true_idx is None
    c = ev.compare(a)
    assert c["kpi_opt"] is None and c["n_feasible"] == 0
    kind, text = ev.verdict_compare(c)
    assert kind == "warning" and "kein** Plan zulässig" in text
    assert ev.who_pays(a) is None and ev.edge_info(a) is None and ev.reserve_rows(a) == []
    assert ev.verdict_payers(None)[0] == "info" and ev.verdict_edge(None)[0] == "info" and ev.verdict_reserve([])[0] == "info"
    assert all(r["solvable"] is False for r in ev.dosis_rows(a, fzs=(0, 25)))


def test_exactly_one_feasible_plan_is_both_optima_and_there_is_nothing_to_move():
    a = _an(_inst([[4, 6, 3]], [[3, 2, 4]], 5, 4))                       # Regellast 5 und Überstundenlast 4: nur (R, R, Z)
    assert int(a.p.ok.sum()) == 1 and a.kpi_idx == a.true_idx
    c = ev.compare(a)
    assert c["same"] and ev.verdict_compare(c)[0] == "success" and c["gain"] == 0 and c["loss"] == 0


def test_capacity_zero_for_overtime_forces_everything_into_regular_time():
    inst = S.make_instance(2, 4, 0, 5, 120, 0)
    p = A.build(inst)
    assert inst.cap_z == 0 and (p.nz[p.ok] == 0).all() and (p.zcost[p.ok] == 0).all()
    k, t = A.best(p, p.kpi), A.best(p, A.true_cost(p, 150))
    assert k == t


def test_a_very_large_capacity_lets_the_kpi_reach_zero_and_the_true_cost_follows_the_surcharge():
    inst = _inst([[5, 7, 2], [6, 3, 9]], [[1, 1, 1], [1, 1, 1]], 100, 100)
    p = A.build(inst)
    k = A.best(p, p.kpi)
    assert p.kpi[k] == 0 and p.nz[k] == 3 and A.true_cost(p, 150)[k] == 1.5 * p.zcost[k]
    t = A.best(p, A.true_cost(p, 150))
    assert A.true_cost(p, 150)[t] <= A.true_cost(p, 150)[k]
    assert A.true_cost(p, 150)[t] == pytest.approx(5 + 3 + 2)                    # die billigste Person je Aufgabe (5, 3, 2), alle in Regelzeit


def test_one_person_has_no_choice_of_person_only_of_shift():
    inst = S.make_instance(1, 5, 0, 3, 100, 100)
    p = A.build(inst)
    assert p.n_plans == 2 ** 5 and (p.X // 2 == 0).all()
    k, t = A.best(p, p.kpi), A.best(p, A.true_cost(p, 100))
    assert A.true_cost(p, 100)[k] == A.true_cost(p, 100)[t]                      # bei g = 100 und einer Person kosten alle Pläne gleich viel


def test_every_family_and_every_objective_runs_every_experiment():
    for family in range(len(C.FAMILIES)):
        for objective in range(len(C.OBJECTIVES)):
            for fz in (0, 50, 100):
                a = ev.analyse(ev.Settings(2, 5, family, 2, 80, fz, 125, 10, objective))
                c = ev.compare(a)
                ev.verdict_compare(c)
                ev.verdict_dosis(ev.dosis_rows(a))
                ev.verdict_payers(ev.who_pays(a))
                ev.verdict_edge(ev.edge_info(a))
                ev.verdict_reserve(ev.reserve_rows(a))


def test_smallest_and_largest_sizes_run():
    for n, m in ((1, 3), (1, 7), (2, 3), (3, 3), (3, 6)):
        a = ev.analyse(ev.Settings(n, m, 1, 4))
        assert a.p.n_plans == (2 * n) ** m


def test_the_enumeration_limit_raises_a_clear_error():
    with pytest.raises(ValueError):
        A.plans(3, 8)
    assert A.plans(3, 7).shape == (279936, 7)


def test_the_settings_extremes_are_valid_for_every_control():
    for fr in (C.FR_MIN, C.FR_MAX):
        for fz in (C.FZ_MIN, C.FZ_MAX):
            for g in (C.G_MIN, C.G_MAX):
                for delta in (C.DELTA_MIN, C.DELTA_MAX):
                    a = ev.analyse(ev.Settings(2, 4, 0, 1, fr, fz, g, delta))
                    ev.verdict_compare(ev.compare(a))
                    ev.verdict_edge(ev.edge_info(a))


def test_a_delta_of_zero_is_always_feasible_for_a_feasible_plan():
    a = ev.analyse(ev.Settings(2, 4, 0, 3, 100, 100, 125, 0))
    e = ev.edge_info(a)
    assert e["kpi"]["ok_delta"] and e["true"]["ok_delta"] and "Bei 0 % mehr Zeit sind beide Pläne zulässig." in ev.verdict_edge(e)[1]


def test_text_helpers_pluralize_and_format_numbers():
    assert ev.vtext(0.0) == "0" and ev.vtext(2.5) == "2,5" and ev.vtext(2.25) == "2,25"
    e = {"delta": 5, "kpi": {"z_full": 1, "r_full": 0, "ok_delta": False}, "true": {"z_full": 0, "r_full": 2, "ok_delta": True}}
    text = ev.verdict_edge(e)[1]
    assert "ist 1 Überstundengrenze und 0 Regelzeitgrenzen" in text and "im wahren Optimum 0 Überstundengrenzen und 2 Regelzeitgrenzen" in text

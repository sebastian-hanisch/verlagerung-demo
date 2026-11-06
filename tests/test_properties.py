"""Eigenschaftstests (ORACLE-PLAYBOOK §5): Aussagen, die für jede Instanz gelten müssen, an festen Seeds und beiden Familien."""

import numpy as np
import pytest

import vrl_algorithm as A
import vrl_constants as C
import vrl_evaluation as ev
import vrl_scenario as S
from vrl_scenario import Instance

CASES = [(n, m, family, seed) for n, m in ((1, 4), (2, 4), (3, 4), (2, 5)) for family in (0, 1) for seed in (3, 4)]


def _p(n, m, family, seed, fr=80, fz=50):
    return A.build(S.make_instance(n, m, family, seed, fr, fz))


@pytest.mark.parametrize("n,m,family,seed", CASES)
@pytest.mark.parametrize("g", [100, 125, 200])
def test_the_kpi_optimum_has_the_better_kpi_and_the_true_optimum_the_better_true_cost(n, m, family, seed, g):
    p = _p(n, m, family, seed)
    k, t = A.best(p, p.kpi), A.best(p, A.true_cost(p, g))
    if k is None:
        pytest.skip("nichts zulässig")
    tc = A.true_cost(p, g)
    assert p.kpi[k] <= p.kpi[t] and tc[t] <= tc[k] and p.ok[k] and p.ok[t]


@pytest.mark.parametrize("n,m,family,seed", CASES)
def test_without_overtime_capacity_both_optima_are_the_same(n, m, family, seed):
    p = _p(n, m, family, seed, fz=0)
    k, t = A.best(p, p.kpi), A.best(p, A.true_cost(p, 125))
    if k is None:
        pytest.skip("nichts zulässig")
    assert int(p.nz[k]) == 0 and k == t and (p.zcost[np.flatnonzero(p.ok)] == 0).all()


@pytest.mark.parametrize("n,m,family,seed", CASES)
def test_more_overtime_capacity_never_makes_the_best_kpi_worse(n, m, family, seed):
    p = _p(n, m, family, seed)
    prev = None
    for cap_z in (0, 2, 4, 6, 9, 30):
        q = A.with_caps(p, cap_z=cap_z)
        k = A.best(q, q.kpi)
        if k is None:
            assert prev is None
            continue
        assert prev is None or int(q.kpi[k]) <= prev
        prev = int(q.kpi[k])


@pytest.mark.parametrize("n,m,family,seed", CASES)
def test_the_true_optimum_never_gets_cheaper_with_a_reserve(n, m, family, seed):
    p = _p(n, m, family, seed)
    t = A.best(p, A.true_cost(p, 125))
    if t is None:
        pytest.skip("nichts zulässig")
    base = float(A.true_cost(p, 125)[t])
    prev = base
    for delta in (5, 10, 20, 30):
        j = A.reserve_best(p, 125, delta)
        if j is None:
            break
        cr, cz = A.reserve_caps(p, delta)
        cost = float(A.true_cost(A.with_caps(p, cr, cz), 125)[j])
        assert cost >= prev - 1e-9 and A.stays_feasible(p, j, delta)
        prev = cost


@pytest.mark.parametrize("n,m,family,seed", CASES)
def test_a_plan_that_stays_feasible_at_a_larger_delta_stays_feasible_at_a_smaller_one(n, m, family, seed):
    p = _p(n, m, family, seed)
    for idx in np.flatnonzero(p.ok)[:200:7]:
        flags = [A.stays_feasible(p, int(idx), d) for d in (0, 2, 5, 10, 20, 40)]
        assert flags == sorted(flags, reverse=True) and flags[0]


@pytest.mark.parametrize("n,m,family,seed", CASES)
def test_at_equal_prices_plans_with_the_same_persons_cost_the_same(n, m, family, seed):
    """Bei g = 100 % ändert nur die Schichtaufteilung die Kennzahl, nicht die Summe aller Kosten."""
    p = _p(n, m, family, seed)
    total = A.true_cost(p, 100)
    persons = (p.X // 2)
    keys = {}
    for k in range(min(p.n_plans, 3000)):
        key = tuple(int(x) for x in persons[k])
        keys.setdefault(key, total[k])
        assert keys[key] == total[k]


@pytest.mark.parametrize("n,m,family,seed", CASES)
def test_the_costs_of_both_optima_do_not_depend_on_the_numbering_of_the_persons(n, m, family, seed):
    inst = S.make_instance(n, m, family, seed)
    perm = np.random.default_rng(seed).permutation(n)
    inst2 = Instance(n, m, tuple(inst.a[i] for i in perm), tuple(inst.b[i] for i in perm), inst.cap_r, inst.cap_z)
    p1, p2 = A.build(inst), A.build(inst2)
    for values in ((lambda p: p.kpi), (lambda p: A.true_cost(p, 125))):
        k1, k2 = A.best(p1, values(p1)), A.best(p2, values(p2))
        assert (k1 is None) == (k2 is None)
        if k1 is not None:
            assert values(p1)[k1] == values(p2)[k2]


def test_everything_is_deterministic():
    a1, a2 = ev.analyse(ev.Settings(2, 4, 1, 9)), ev.analyse(ev.Settings(2, 4, 1, 9))
    assert (a1.p.kpi == a2.p.kpi).all() and ev.compare(a1)["loss"] == ev.compare(a2)["loss"] and ev.reserve_rows(a1) == ev.reserve_rows(a2)
    assert C.SWEEP_GS == (100, 125, 150, 200)

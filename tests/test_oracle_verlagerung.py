"""Orakel-Test verlagerung-demo: der Kern gegen einen ANDEREN Rechenweg (ORACLE-PLAYBOOK §2, DEMO-PLAYBOOK §12).

Reines Python (itertools.product, Schleifen, keine numpy-Zeile im Referenzweg) gegen die Vektorrechnung: KPI, Überstundenkosten, Lasten, Zulässigkeit, Optima, Sprödheit und Reserve in Brüchen."""

import itertools
from fractions import Fraction

import pytest

import vrl_algorithm as A
import vrl_scenario as S

CASES = [(n, m, family, seed) for n, m in ((1, 3), (1, 4), (2, 3), (2, 4), (3, 3)) for family in (0, 1) for seed in (1, 2, 3)]


def _plain(inst):
    """Alle Pläne mit (Code, KPI, Überstundenkosten, Regellast je Person, Überstundenlast je Person) in reinem Python."""
    out = []
    for code in itertools.product(range(2 * inst.n), repeat=inst.m):
        kpi = zc = 0
        rl, zl = [0] * inst.n, [0] * inst.n
        for j, c in enumerate(code):
            i, shift = c // 2, c % 2
            if shift == 0:
                kpi += inst.a[i][j]
                rl[i] += inst.b[i][j]
            else:
                zc += inst.a[i][j]
                zl[i] += inst.b[i][j]
        out.append((code, kpi, zc, rl, zl))
    return out


def _ok(inst, row):
    return all(r <= inst.cap_r for r in row[3]) and all(z <= inst.cap_z for z in row[4])


@pytest.mark.parametrize("n,m,family,seed", CASES)
def test_kpi_costs_loads_and_feasibility_match_plain_python(n, m, family, seed):
    inst = S.make_instance(n, m, family, seed)
    p = A.build(inst)
    plain = _plain(inst)
    assert p.n_plans == len(plain)
    for k, row in enumerate(plain):
        assert tuple(int(c) for c in p.X[k]) == row[0] and int(p.kpi[k]) == row[1] and int(p.zcost[k]) == row[2]
        assert [int(v) for v in p.rload[k]] == row[3] and [int(v) for v in p.zload[k]] == row[4] and bool(p.ok[k]) == _ok(inst, row)


@pytest.mark.parametrize("n,m,family,seed", CASES)
@pytest.mark.parametrize("g", [100, 125, 150, 200])
def test_both_optima_match_plain_python_for_every_surcharge(n, m, family, seed, g):
    inst = S.make_instance(n, m, family, seed)
    p = A.build(inst)
    feas = [(k, row) for k, row in enumerate(_plain(inst)) if _ok(inst, row)]
    if not feas:
        assert A.best(p, p.kpi) is None and A.best(p, A.true_cost(p, g)) is None
        return
    best_kpi = min(row[1] for _, row in feas)
    assert A.best(p, p.kpi) == next(k for k, row in feas if row[1] == best_kpi)
    f = Fraction(g, 100)
    best_true = min(row[1] + f * row[2] for _, row in feas)
    assert A.best(p, A.true_cost(p, g)) == next(k for k, row in feas if row[1] + f * row[2] == best_true)


@pytest.mark.parametrize("n,m,family,seed", CASES)
def test_brittleness_and_reserve_match_exact_fractions(n, m, family, seed):
    inst = S.make_instance(n, m, family, seed)
    p = A.build(inst)
    plain = _plain(inst)
    for delta in (2, 5, 10, 20, 25):
        f = 1 + Fraction(delta, 100)
        for k in range(0, len(plain), max(1, len(plain) // 25)):
            row = plain[k]
            ref = all(f * r <= inst.cap_r for r in row[3]) and all(f * z <= inst.cap_z for z in row[4])
            assert A.stays_feasible(p, k, delta) == ref
        cr, cz = int(inst.cap_r / f), int(inst.cap_z / f)               # Abrunden der Brüche (nichtnegativ)
        assert A.reserve_caps(p, delta) == (cr, cz)
        feas = [(k, row) for k, row in enumerate(plain) if all(r <= cr for r in row[3]) and all(z <= cz for z in row[4])]
        got = A.reserve_best(p, 125, delta)
        if not feas:
            assert got is None
        else:
            best = min(row[1] + Fraction(125, 100) * row[2] for _, row in feas)
            assert got == next(k for k, row in feas if row[1] + Fraction(125, 100) * row[2] == best)


@pytest.mark.parametrize("n,m,family,seed", [c for c in CASES if c[0] <= 2])
def test_full_limits_match_plain_python(n, m, family, seed):
    inst = S.make_instance(n, m, family, seed)
    p = A.build(inst)
    plain = _plain(inst)
    for k in range(0, len(plain), max(1, len(plain) // 20)):
        lim = A.full_limits(p, k)
        assert lim["r"] == [r == inst.cap_r for r in plain[k][3]] and lim["z"] == [z == inst.cap_z for z in plain[k][4]]


def test_the_capacity_formula_matches_a_ceiling_in_exact_fractions():
    import math
    for seed in range(8):
        inst = S.make_instance(3, 6, 0, seed)
        for fr in (60, 80, 100, 120):
            for fz in (0, 25, 50, 100):
                cap_r = math.ceil(Fraction(fr, 100) * sum(Fraction(sum(inst.b[i][j] for i in range(3)), 3) for j in range(6)) / 3)
                assert S.capacities(inst.arrays()[1], 3, fr, fz) == (cap_r, math.ceil(Fraction(fz, 100) * cap_r))


@pytest.mark.parametrize("n,m,family,seed", CASES)
def test_who_pays_matches_plain_python_and_ties_are_not_decided_by_the_index(n, m, family, seed):
    import vrl_evaluation as ev
    inst = S.make_instance(n, m, family, seed)
    a = ev.analyse(ev.Settings(n=n, m=m, family=family, seed=seed))
    w = ev.who_pays(a)
    plain = _plain(inst)
    feas = [row for row in plain if _ok(inst, row)]
    if not feas:
        assert w is None
        return
    zl = next(row for row in feas if row[1] == min(r[1] for r in feas))[4]           # Überstunden je Person im Optimum der Kennzahl (erstes bei Gleichstand)
    want = [i + 1 for i in range(n) if max(zl) > 0 and zl[i] == max(zl)]               # jede Person auf dem Maximum trägt
    means = [Fraction(sum(inst.a[i]), m) for i in range(n)]
    cheapest = means.index(min(means))
    assert w["carriers"] == want and w["cheapest"] == cheapest + 1
    assert w["cheapest_pays"] == ((cheapest + 1) in want) and w["cheapest_alone"] == (want == [cheapest + 1])
    assert w["dearest_pays"] == ((means.index(max(means)) + 1) in want)
    assert w["persons"] == sum(1 for z in zl if z > 0) and w["total"] == sum(zl)


def test_carriers_ignore_the_numbering():
    import vrl_evaluation as ev
    assert ev.carriers([4, 4, 4]) == [0, 1, 2] and ev.carriers([0, 4, 4]) == [1, 2] and ev.carriers([3, 5, 1]) == [1] and ev.carriers([0, 0, 0]) == [] and ev.carriers([]) == []
    for z in ([4, 4, 2], [2, 4, 4], [4, 2, 4]):                                      # dieselbe Verteilung, andere Nummerierung: gleich viele Träger
        assert len(ev.carriers(z)) == 2 and all(z[i] == 4 for i in ev.carriers(z))


def test_no_cost_ties_between_persons_in_the_sweep_instances():
    for family in (0, 1):
        for seed in __import__("vrl_constants").SWEEP_SEEDS:
            inst = S.make_instance(3, 7, family, seed, 80, 50)
            means = [sum(row) for row in inst.a]
            assert means.count(min(means)) == 1 and means.count(max(means)) == 1

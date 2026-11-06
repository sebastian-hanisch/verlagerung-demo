"""Gemeinsame Fixtures: das Handbeispiel (1 Person, 3 Aufgaben), an dem jede Einheit von Hand geprüft wird (DEMO-PLAYBOOK §1b)."""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import vrl_algorithm as A  # noqa: E402
import vrl_evaluation as ev  # noqa: E402
from vrl_scenario import Instance  # noqa: E402


def make_hand() -> Instance:
    return Instance(n=1, m=3, a=((4, 6, 3),), b=((3, 2, 4),), cap_r=6, cap_z=5)


@pytest.fixture
def hand() -> Instance:
    """Handbeispiel: Kosten (4, 6, 3), Zeit (3, 2, 4), Regelkapazität 6 h, Überstundenkapazität 5 h. Pläne (Schicht je Aufgabe, 0 Regelzeit, 1 Überstunden) in der Reihenfolge von itertools.product:
    0 (R,R,R) Regellast 9 unzulässig; 1 (R,R,Z) Regel 5, Überstunden 4, KPI 10, Ü-Kosten 3; 2 (R,Z,R) Regel 7 unzulässig; 3 (R,Z,Z) Überstunden 6 unzulässig;
    4 (Z,R,R) Regel 6, Überstunden 3, KPI 9, Ü-Kosten 4; 5 (Z,R,Z) Überstunden 7 unzulässig; 6 (Z,Z,R) Regel 4, Überstunden 5, KPI 3, Ü-Kosten 10; 7 (Z,Z,Z) Überstunden 9 unzulässig.
    Wahre Kosten bei g = 125 %: Plan 1: 13,75; Plan 4: 14; Plan 6: 15,5. Bei g = 100 % kosten alle drei 13."""
    return make_hand()


@pytest.fixture
def hand_problem(hand) -> A.Problem:
    return A.build(hand)


@pytest.fixture
def hand_analysis(hand_problem) -> ev.Analysis:
    s = ev.Settings(1, 3, 0, 0, 80, 50, 125, 20, 0)
    return ev.Analysis(s, hand_problem, A.best(hand_problem, hand_problem.kpi), A.best(hand_problem, A.true_cost(hand_problem, 125)))

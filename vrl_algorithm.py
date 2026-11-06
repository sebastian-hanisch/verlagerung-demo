"""Kern der Demo (numpy): Aufgaben in Regelzeit oder Überstunden, eine Kennzahl, die nur die Regelzeit sieht, und die wahren Kosten.

  * `plans`: alle (2n)^m Pläne; Code je Aufgabe = 2 * Person + Schicht (0 Regelzeit, 1 Überstunden), in der Reihenfolge von itertools.product.
  * `Problem`: KPI (Kosten der Regelzeit-Aufgaben), Kosten der Überstunden-Aufgaben, Lasten je Person und Schicht, Zulässigkeit (Regellast <= capR und Überstundenlast <= capZ).
  * `true_cost`: KPI + g * Überstundenkosten (g in Prozent, ganzzahlig in Vielfachen von 25: exakt in float64).
  * `best`: das Optimum (bei Gleichstand der kleinste Index der Aufzählung); None, wenn nichts zulässig ist.
  * `stays_feasible`, `reserve_best`: Sprödheit (alle Zeiten wachsen um delta Prozent) und Optimum mit Reserve (Kapazitäten durch 1 + delta geteilt und abgerundet), beides in ganzen Zahlen.
"""

from dataclasses import dataclass, replace

import numpy as np

from vrl_scenario import Instance

_BIG = np.inf


def plans(n: int, m: int) -> np.ndarray:
    """Alle (2n)^m Pläne (Zeile = Code je Aufgabe), in der Reihenfolge von itertools.product (die erste Aufgabe ist die höchste Stelle)."""
    base = 2 * n
    if n < 1 or m < 1 or base ** m > 300_000:
        raise ValueError(f"n = {n}, m = {m}: Aufzählung nur bis 300 000 Pläne")
    return ((np.arange(base ** m)[:, None] // base ** np.arange(m - 1, -1, -1)[None, :]) % base).astype(np.int8)


@dataclass
class Problem:
    inst: Instance
    X: np.ndarray
    kpi: np.ndarray           # Kosten der Aufgaben in der Regelzeit
    zcost: np.ndarray         # Kosten der Aufgaben in Überstunden
    rload: np.ndarray         # Regellast je Person (N x n)
    zload: np.ndarray         # Überstundenlast je Person
    nz: np.ndarray            # Aufgaben in Überstunden

    @property
    def n_plans(self) -> int:
        return len(self.kpi)

    @property
    def ok(self) -> np.ndarray:
        return (self.rload <= self.inst.cap_r).all(axis=1) & (self.zload <= self.inst.cap_z).all(axis=1)


def build(inst: Instance) -> Problem:
    n, m = inst.n, inst.m
    a, b = inst.arrays()
    X = plans(n, m)
    person, shift = X // 2, X % 2
    idx = np.arange(m)
    ac, bt = a[person, idx], b[person, idx]
    kpi = (ac * (shift == 0)).sum(axis=1)
    zcost = (ac * (shift == 1)).sum(axis=1)
    rload = np.stack([(bt * ((person == i) & (shift == 0))).sum(axis=1) for i in range(n)], axis=1)
    zload = np.stack([(bt * ((person == i) & (shift == 1))).sum(axis=1) for i in range(n)], axis=1)
    return Problem(inst, X, kpi, zcost, rload, zload, (shift == 1).sum(axis=1))


def with_caps(p: Problem, cap_r: int | None = None, cap_z: int | None = None) -> Problem:
    """Dieselbe Instanz mit anderen Kapazitäten (die Lasten bleiben)."""
    inst = replace(p.inst, cap_r=p.inst.cap_r if cap_r is None else int(cap_r), cap_z=p.inst.cap_z if cap_z is None else int(cap_z))
    return Problem(inst, p.X, p.kpi, p.zcost, p.rload, p.zload, p.nz)


def true_cost(p: Problem, g_pct: int) -> np.ndarray:
    """KPI + g * Überstundenkosten, g in Prozent (125 heißt 1,25)."""
    return p.kpi + (g_pct / 100.0) * p.zcost


def best(p: Problem, values: np.ndarray, ok: np.ndarray | None = None) -> int | None:
    """Index des kleinsten Wertes unter den zulässigen Plänen (bei Gleichstand der erste); None, wenn nichts zulässig ist."""
    ok = p.ok if ok is None else ok
    if not ok.any():
        return None
    return int(np.argmin(np.where(ok, values, _BIG)))


def stays_feasible(p: Problem, idx: int, delta_pct: int) -> bool:
    """Bleibt der Plan zulässig, wenn alle Zeiten um delta Prozent wachsen? Exakt in ganzen Zahlen: Last * (100 + delta) <= Kapazität * 100."""
    f = 100 + int(delta_pct)
    return bool((p.rload[idx] * f <= p.inst.cap_r * 100).all() and (p.zload[idx] * f <= p.inst.cap_z * 100).all())


def reserve_caps(p: Problem, delta_pct: int) -> tuple[int, int]:
    """Kapazitäten mit Reserve: durch (1 + delta) geteilt und abgerundet (ganzzahlig)."""
    f = 100 + int(delta_pct)
    return (p.inst.cap_r * 100) // f, (p.inst.cap_z * 100) // f


def reserve_best(p: Problem, g_pct: int, delta_pct: int) -> int | None:
    """Optimum der wahren Kosten mit Reserve."""
    cr, cz = reserve_caps(p, delta_pct)
    q = with_caps(p, cr, cz)
    return best(q, true_cost(q, g_pct))


def full_limits(p: Problem, idx: int) -> dict:
    """Welche Grenzen sind im Plan genau ausgeschöpft (Reserve null)? Je Person Regelzeit und Überstunden."""
    return {"r": [bool(v == p.inst.cap_r) for v in p.rload[idx]], "z": [bool(v == p.inst.cap_z) for v in p.zload[idx]]}

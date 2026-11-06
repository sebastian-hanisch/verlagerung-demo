"""Szenario: m Aufgaben auf n Personen; jede Aufgabe wird in der Regelzeit (R, von der Kennzahl gemessen) oder in Überstunden (Z, nicht gemessen) gemacht. Alles simuliert.

Kosten a[i][j] (ganze Zahlen; eine Überstunde-Aufgabe hat dieselben Kosten, der Zuschlag g kommt in den wahren Kosten dazu), Zeit b[i][j] (1 bis 9).
Kapazität je Person: Regelzeit höchstens capR, Überstundenzeit höchstens capZ. Die Erzeugung entspricht den Messreihen der Planung (gleiche Seeds, gleiche Reihenfolge der Ziehungen)."""

import math
from dataclasses import dataclass

import numpy as np

import vrl_constants as C


@dataclass(frozen=True)
class Instance:
    n: int
    m: int
    a: tuple                  # Kosten, n Zeilen (Personen) mal m Spalten (Aufgaben)
    b: tuple                  # Zeit
    cap_r: int                # Regelkapazität je Person in Stunden
    cap_z: int                # Überstundenkapazität je Person in Stunden

    def arrays(self) -> tuple[np.ndarray, np.ndarray]:
        return np.array(self.a, dtype=np.int64), np.array(self.b, dtype=np.int64)


def capacities(b: np.ndarray, n: int, fr_pct: int, fz_pct: int) -> tuple[int, int]:
    """capR = aufgerundet fR * (Summe der mittleren Zeiten je Aufgabe) / n; capZ = aufgerundet fZ * capR (fR und fZ in Prozent)."""
    cap_r = int(math.ceil((fr_pct / 100.0) * b.mean(axis=0).sum() / n))
    return cap_r, int(math.ceil((fz_pct / 100.0) * cap_r))


def make_instance(n: int, m: int, family: int, seed: int, fr_pct: int = C.DEFAULT_FR, fz_pct: int = C.DEFAULT_FZ) -> Instance:
    """Deterministisch aus (n, m, Familie, Seed, fR, fZ)."""
    rng = np.random.default_rng(seed)
    if family == 0:
        a = rng.integers(1, 100, (n, m))
    else:
        a = rng.integers(0, 41, (n, 1)) + rng.integers(1, 61, (n, m))
    b = rng.integers(1, 10, (n, m))
    cap_r, cap_z = capacities(b, n, fr_pct, fz_pct)
    return Instance(n, m, tuple(tuple(int(x) for x in row) for row in a), tuple(tuple(int(x) for x in row) for row in b), cap_r, cap_z)

"""Kennzahlen, Verdikt-Logik und Sweeps. Verdikte sind reine Funktionen (Art, Text); jede Zahl im Text kommt aus der Rechnung.

Gefragt wird: Was geschieht, wenn man eine Kennzahl optimiert, die nur die Regelzeit sieht? Wie viel besser sieht das Optimum der Kennzahl aus, wie viel mehr kostet es wirklich, wohin wandert
die Last und wer zahlt, wie weit liegt der Plan am Rand der Kapazität, und was kostet eine Reserve?"""

import math
from dataclasses import dataclass

import numpy as np

import vrl_algorithm as A
import vrl_constants as C
import vrl_scenario as S


def de(x: float, digits: int = 1) -> str:
    """Zahl mit Dezimalkomma; kein „-0,0“."""
    text = f"{x:.{digits}f}"
    if float(text) == 0.0:
        text = f"{0.0:.{digits}f}"
    return text.replace(".", ",")


def pct(x: float, digits: int = 1) -> str:
    """Anteil als Prozent: 0,05 -> „5,0 %“."""
    return de(x * 100.0, digits) + " %"


def vtext(x: float) -> str:
    """Wert ohne Nachkommastellen, wenn ganzzahlig, sonst mit zwei (Kosten mit Zuschlag 1,25 haben Viertel)."""
    if float(x).is_integer():
        return str(int(x))
    text = de(float(x), 2)
    return text[:-1] if text.endswith("0") else text


@dataclass(frozen=True)
class Settings:
    n: int = C.DEFAULT_N
    m: int = C.DEFAULT_M
    family: int = C.DEFAULT_FAMILY
    seed: int = C.DEFAULT_SEED
    fr: int = C.DEFAULT_FR
    fz: int = C.DEFAULT_FZ
    g: int = C.DEFAULT_G
    delta: int = C.DEFAULT_DELTA
    objective: int = C.DEFAULT_OBJECTIVE


@dataclass
class Analysis:
    settings: Settings
    p: A.Problem
    kpi_idx: int | None        # Optimum der Kennzahl
    true_idx: int | None       # Optimum der wahren Kosten


def analyse(settings: Settings) -> Analysis:
    inst = S.make_instance(settings.n, settings.m, settings.family, settings.seed, settings.fr, settings.fz)
    p = A.build(inst)
    return Analysis(settings, p, A.best(p, p.kpi), A.best(p, A.true_cost(p, settings.g)))


def _optimum_info(p: A.Problem, idx: int, g: int) -> dict:
    inst = p.inst
    code = p.X[idx].astype(int)
    tasks = [{"task": j + 1, "person": int(c) // 2 + 1, "overtime": bool(int(c) % 2)} for j, c in enumerate(code)]
    true = float(A.true_cost(p, g)[idx])
    return {"idx": idx, "kpi": int(p.kpi[idx]), "true": true, "zcost": int(p.zcost[idx]), "nz": int(p.nz[idx]), "zhours": int(p.zload[idx].sum()), "rload": p.rload[idx].astype(int), "zload": p.zload[idx].astype(int),
            "tasks": tasks, "zshare": (g / 100.0) * int(p.zcost[idx]) / true if true else 0.0, "caps": (inst.cap_r, inst.cap_z)}


# --- Experimente auf einer Instanz ---------------------------------------------------------------------------------------------------------

def compare(a: Analysis) -> dict:
    """Optimum der Kennzahl gegen Optimum der wahren Kosten."""
    s, p = a.settings, a.p
    out = {"g": s.g, "n_plans": p.n_plans, "n_feasible": int(p.ok.sum()), "kpi_opt": None, "true_opt": None}
    if a.kpi_idx is None or a.true_idx is None:
        return out
    k, t = _optimum_info(p, a.kpi_idx, s.g), _optimum_info(p, a.true_idx, s.g)
    out.update({"kpi_opt": k, "true_opt": t, "gain": (t["kpi"] - k["kpi"]) / t["kpi"] if t["kpi"] else 0.0, "loss": (k["true"] - t["true"]) / t["true"] if t["true"] else 0.0,
                "same": k["kpi"] == t["kpi"] and k["true"] == t["true"]})
    return out


def person_text(info: dict) -> str:
    """„A1: P2 R | A2: P1 Ü ...“ (R Regelzeit, Ü Überstunden)."""
    return " | ".join(f"A{t['task']}: P{t['person']} {'Ü' if t['overtime'] else 'R'}" for t in info["tasks"])


def dosis_rows(a: Analysis, fzs=(0, 25, 50, 75, 100)) -> list[dict]:
    """Der Ort, in den man ausweichen kann: Überstundenanteil fZ von 0 bis 100 % der Regelkapazität."""
    s, p = a.settings, a.p
    rows = []
    for fz in fzs:
        cap_z = int(math.ceil((fz / 100.0) * p.inst.cap_r))
        q = A.with_caps(p, cap_z=cap_z)
        k, t = A.best(q, q.kpi), A.best(q, A.true_cost(q, s.g))
        row = {"fz": fz, "cap_z": cap_z, "gain": None, "loss": None, "solvable": k is not None}
        if k is not None:
            tc = A.true_cost(q, s.g)
            row["gain"] = (q.kpi[t] - q.kpi[k]) / q.kpi[t] if q.kpi[t] else 0.0
            row["loss"] = (tc[k] - tc[t]) / tc[t] if tc[t] else 0.0
        rows.append(row)
    return rows


def who_pays(a: Analysis) -> dict | None:
    """Überstunden je Person im Optimum der Kennzahl und im wahren Optimum; Anteil an den wahren Kosten."""
    if a.kpi_idx is None or a.true_idx is None:
        return None
    s, p = a.settings, a.p
    k, t = _optimum_info(p, a.kpi_idx, s.g), _optimum_info(p, a.true_idx, s.g)
    z = k["zload"]
    total = int(z.sum())
    cheapest = int(np.argmin(np.array(p.inst.a).mean(axis=1)))
    return {"kpi_opt": k, "true_opt": t, "total": total, "top_share": (z.max() / total) if total else None, "persons": int((z > 0).sum()), "cheapest_pays": bool(total and int(np.argmax(z)) == cheapest),
            "cheapest": cheapest + 1}


def edge_info(a: Analysis) -> dict | None:
    """Der Rand: welche Grenzen sind in den beiden Optima genau ausgeschöpft, und bleibt der Plan bei delta Prozent mehr Zeit zulässig?"""
    if a.kpi_idx is None or a.true_idx is None:
        return None
    s, p = a.settings, a.p
    out = {}
    for name, idx in (("kpi", a.kpi_idx), ("true", a.true_idx)):
        lim = A.full_limits(p, idx)
        out[name] = {"idx": idx, "r_full": sum(lim["r"]), "z_full": sum(lim["z"]), "any_full": any(lim["r"]) or any(lim["z"]), "rload": p.rload[idx].astype(int), "zload": p.zload[idx].astype(int),
                     "ok_delta": A.stays_feasible(p, idx, s.delta), "ok_by_delta": {d: A.stays_feasible(p, idx, d) for d in C.SWEEP_DELTAS}}
    out["caps"] = (p.inst.cap_r, p.inst.cap_z)
    out["delta"] = s.delta
    return out


def reserve_rows(a: Analysis, deltas=C.SWEEP_RESERVES) -> list[dict]:
    """Der Preis der Reserve: Kapazitäten durch 1 + delta geteilt (abgerundet), wahre Kosten des Optimums gegen das ohne Reserve."""
    if a.true_idx is None:
        return []
    s, p = a.settings, a.p
    base = float(A.true_cost(p, s.g)[a.true_idx])
    rows = []
    for d in deltas:
        j = A.reserve_best(p, s.g, d)
        cr, cz = A.reserve_caps(p, d)
        row = {"delta": d, "cap_r": cr, "cap_z": cz, "idx": j, "rise": None, "robust": None}
        if j is not None:
            row["rise"] = (float(A.true_cost(A.with_caps(p, cr, cz), s.g)[j]) - base) / base if base else 0.0
            row["robust"] = A.stays_feasible(p, j, d)
        rows.append(row)
    return rows


# --- Sweeps über feste Instanzen -----------------------------------------------------------------------------------------------------------

def _q3(vals) -> tuple[float, float, float]:
    v = np.asarray(vals, dtype=float)
    return float(v.min()), float(np.median(v)), float(v.max())


def _record(family: int, seed: int) -> dict:
    inst = S.make_instance(C.SWEEP_N, C.SWEEP_M, family, seed, C.SWEEP_FR, C.SWEEP_FZ)
    p = A.build(inst)
    k = A.best(p, p.kpi)
    rec = {"family": family, "seed": seed, "g": {}, "dosis": {}}
    for g in C.SWEEP_GS:
        tc = A.true_cost(p, g)
        t = A.best(p, tc)
        rec["g"][g] = {"same": bool(p.kpi[k] == p.kpi[t] and tc[k] == tc[t]), "gain": (p.kpi[t] - p.kpi[k]) / p.kpi[t] if p.kpi[t] else 0.0, "loss": (tc[k] - tc[t]) / tc[t],
                       "nz_k": int(p.nz[k]), "nz_t": int(p.nz[t]), "zh_k": int(p.zload[k].sum()), "zh_t": int(p.zload[t].sum())}
    g = C.SWEEP_G
    tc = A.true_cost(p, g)
    t = A.best(p, tc)
    z = p.zload[k]
    cheapest = int(np.argmin(np.array(inst.a).mean(axis=1)))
    rec["zshare_k"] = g / 100.0 * p.zcost[k] / tc[k]
    rec["zshare_t"] = g / 100.0 * p.zcost[t] / tc[t]
    rec["top_share"] = (z.max() / z.sum()) if z.sum() else None
    rec["z_persons"] = int((z > 0).sum())
    rec["cheapest_pays"] = bool(z.sum() and int(np.argmax(z)) == cheapest)
    rec["full"] = {}
    for name, idx in (("k", k), ("t", t)):
        lim = A.full_limits(p, idx)
        rec["full"][name] = {"z": any(lim["z"]), "r": any(lim["r"]), "any": any(lim["z"]) or any(lim["r"]), "allz": all(lim["z"])}
    rec["brittle"] = {d: {"k": A.stays_feasible(p, k, d), "t": A.stays_feasible(p, t, d)} for d in C.SWEEP_DELTAS}
    base = float(tc[t])
    rec["reserve"] = {}
    for d in C.SWEEP_RESERVES:
        j = A.reserve_best(p, g, d)
        if j is None:
            rec["reserve"][d] = {"rise": None, "robust": None}
        else:
            cr, cz = A.reserve_caps(p, d)
            rec["reserve"][d] = {"rise": (float(A.true_cost(A.with_caps(p, cr, cz), g)[j]) - base) / base, "robust": A.stays_feasible(p, j, d)}
    for fz in C.SWEEP_FZS:
        cap_z = int(math.ceil((fz / 100.0) * inst.cap_r))
        q = A.with_caps(p, cap_z=cap_z)
        kk, tt = A.best(q, q.kpi), A.best(q, tc_ := A.true_cost(q, g))
        rec["dosis"][fz] = {"cap_z": cap_z, "diff": bool(tc_[kk] != tc_[tt]), "gain": (q.kpi[tt] - q.kpi[kk]) / q.kpi[tt] if q.kpi[tt] else 0.0, "loss": (tc_[kk] - tc_[tt]) / tc_[tt]}
    return rec


def sweep_all(families=C.SWEEP_FAMILIES, seeds=C.SWEEP_SEEDS) -> dict:
    """Je Familie 20 feste Instanzen (3 Personen, 7 Aufgaben, alle 279 936 Pläne): alle Kennzahlen in einem Durchgang; die Zusammenfassungen lesen daraus."""
    return {fam: [_record(fam, s) for s in seeds] for fam in families}


def summary_g(recs: list[dict]) -> dict:
    """Je Zuschlag: Optima verschieden, Kennzahl besser, wahre Kosten höher, Aufgaben und Stunden in Überstunden."""
    out = {}
    for g in C.SWEEP_GS:
        out[g] = {"different": sum(not r["g"][g]["same"] for r in recs), "gain": _q3([r["g"][g]["gain"] for r in recs]), "loss": _q3([r["g"][g]["loss"] for r in recs]),
                  "nz_k": _q3([r["g"][g]["nz_k"] for r in recs]), "nz_t": _q3([r["g"][g]["nz_t"] for r in recs]), "zh_k": _q3([r["g"][g]["zh_k"] for r in recs]), "zh_t": _q3([r["g"][g]["zh_t"] for r in recs]),
                  "seeds": len(recs)}
    return out


def summary_payers(recs: list[dict]) -> dict:
    withz = [r for r in recs if r["top_share"] is not None]
    return {"zshare_k": _q3([r["zshare_k"] for r in recs]), "zshare_t": _q3([r["zshare_t"] for r in recs]), "n_z": len(withz), "top_share": _q3([r["top_share"] for r in withz]) if withz else (0.0, 0.0, 0.0),
            "persons": _q3([r["z_persons"] for r in withz]) if withz else (0.0, 0.0, 0.0), "cheapest": sum(r["cheapest_pays"] for r in withz), "seeds": len(recs)}


def summary_edge(recs: list[dict]) -> dict:
    out = {}
    for name in ("k", "t"):
        out[name] = {"z": sum(r["full"][name]["z"] for r in recs), "r": sum(r["full"][name]["r"] for r in recs), "any": sum(r["full"][name]["any"] for r in recs), "allz": sum(r["full"][name]["allz"] for r in recs)}
    out["brittle"] = {d: {"k": sum(r["brittle"][d]["k"] for r in recs), "t": sum(r["brittle"][d]["t"] for r in recs)} for d in C.SWEEP_DELTAS}
    out["seeds"] = len(recs)
    return out


def summary_reserve(recs: list[dict]) -> dict:
    out = {}
    for d in C.SWEEP_RESERVES:
        rises = [r["reserve"][d]["rise"] for r in recs if r["reserve"][d]["rise"] is not None]
        out[d] = {"rise": _q3(rises) if rises else (0.0, 0.0, 0.0), "n": len(rises), "unsolvable": len(recs) - len(rises), "robust": sum(bool(r["reserve"][d]["robust"]) for r in recs if r["reserve"][d]["rise"] is not None)}
    return out


def summary_dosis(recs: list[dict]) -> dict:
    return {fz: {"cap_z": float(np.median([r["dosis"][fz]["cap_z"] for r in recs])), "different": sum(r["dosis"][fz]["diff"] for r in recs), "gain": _q3([r["dosis"][fz]["gain"] for r in recs]),
                 "loss": _q3([r["dosis"][fz]["loss"] for r in recs]), "seeds": len(recs)} for fz in C.SWEEP_FZS}


# --- Verdikte ------------------------------------------------------------------------------------------------------------------------------

def verdict_compare(c: dict) -> tuple[str, str]:
    """Experiment Kennzahl und Wahrheit: wie viel besser sieht es aus, wie viel kostet es wirklich?"""
    if c["kpi_opt"] is None:
        return "warning", "Mit diesen Kapazitäten ist **kein** Plan zulässig: alle Aufgaben passen nicht in Regelzeit und Überstunden."
    k, t = c["kpi_opt"], c["true_opt"]
    if c["same"]:
        return "success", f"Das Optimum der Kennzahl ist hier auch das wahre Optimum (KPI {k['kpi']}, wahre Kosten {vtext(k['true'])}): es gibt nichts zu verlagern."
    if c["gain"] > 0 and c["loss"] > 0:
        return "warning", (f"Das Optimum der Kennzahl hat **KPI {k['kpi']}** statt {t['kpi']} (**{pct(c['gain'])} besser**), kostet aber wirklich **{vtext(k['true'])}** statt {vtext(t['true'])} "
                           f"(**{pct(c['loss'])} mehr**). {k['nz']} von {len(k['tasks'])} Aufgaben liegen in Überstunden (im wahren Optimum {t['nz']}), zusammen {k['zhours']} Stunden.")
    if c["loss"] == 0:
        return "info", f"Die beiden Optima haben dieselben wahren Kosten ({vtext(k['true'])}), aber nicht dieselbe Kennzahl (KPI {k['kpi']} gegen {t['kpi']}): reine Verschiebung ohne Gewinn."
    return "info", f"Das Optimum der Kennzahl hat KPI {k['kpi']} gegen {t['kpi']} und wahre Kosten {vtext(k['true'])} gegen {vtext(t['true'])}."


def verdict_dosis(rows: list[dict]) -> tuple[str, str]:
    """Experiment Der Ort: nur dort, wo es einen Ort gibt, wandert die Last."""
    cells = [f"Überstundenanteil {r['fz']} % ({r['cap_z']} h): " + (f"Kennzahl {pct(r['gain'])} besser, wahre Kosten {pct(r['loss'])} höher" if r["solvable"] else "unlösbar") for r in rows]
    zero = next((r for r in rows if r["fz"] == 0), None)
    tail = " Ohne Überstundenkapazität wandert nichts: beide Optima sind gleich." if zero is not None and zero["solvable"] and zero["gain"] == 0 and zero["loss"] == 0 else ""
    return "info", "; ".join(cells) + "." + tail


def verdict_payers(w: dict | None) -> tuple[str, str]:
    """Experiment Wer zahlt."""
    if w is None:
        return "info", "Ohne zulässigen Plan gibt es keinen Zahler."
    k, t = w["kpi_opt"], w["true_opt"]
    if w["total"] == 0:
        return "info", f"Im Optimum der Kennzahl gibt es keine Überstunden; die wahren Kosten sind {vtext(k['true'])}."
    persons = f"Die Überstunden verteilen sich auf **{w['persons']}** von {len(k['zload'])} Personen; die am stärksten belastete trägt {pct(w['top_share'], 0)} davon."
    cheap = f" Die im Mittel billigste Person (P{w['cheapest']}) trägt die meisten." if w["cheapest_pays"] else f" Die im Mittel billigste Person (P{w['cheapest']}) trägt nicht die meisten."
    return "info", (f"Im Optimum der Kennzahl stecken **{pct(k['zshare'], 0)}** der wahren Kosten in den Überstunden, im wahren Optimum {pct(t['zshare'], 0)}. " + persons + cheap)


def verdict_edge(e: dict | None) -> tuple[str, str]:
    """Experiment Der Rand."""
    if e is None:
        return "info", "Ohne zulässigen Plan gibt es keinen Rand."
    k, t = e["kpi"], e["true"]
    def lim(n, one, many):
        return f"{n} {one if n == 1 else many}"
    parts = [f"Im Optimum der Kennzahl {'ist' if k['z_full'] + k['r_full'] == 1 else 'sind'} {lim(k['z_full'], 'Überstundengrenze', 'Überstundengrenzen')} und {lim(k['r_full'], 'Regelzeitgrenze', 'Regelzeitgrenzen')} genau ausgeschöpft, "
             f"im wahren Optimum {lim(t['z_full'], 'Überstundengrenze', 'Überstundengrenzen')} und {lim(t['r_full'], 'Regelzeitgrenze', 'Regelzeitgrenzen')}."]
    d = e["delta"]
    if d == 0:
        parts.append("Bei 0 % mehr Zeit sind beide Pläne zulässig.")
    else:
        ok_k, ok_t = k["ok_delta"], t["ok_delta"]
        parts.append(f"Bei **{d} % mehr Zeit** ist das Optimum der Kennzahl {'noch zulässig' if ok_k else '**unzulässig**'}, das wahre Optimum {'noch zulässig' if ok_t else '**unzulässig**'}.")
    kind = "warning" if (e["delta"] > 0 and (not k["ok_delta"] or not t["ok_delta"])) else "info"
    return kind, " ".join(parts)


def verdict_reserve(rows: list[dict]) -> tuple[str, str]:
    """Experiment Reserve."""
    if not rows:
        return "info", "Ohne zulässigen Plan gibt es keine Reserve."
    cells = [f"Reserve {r['delta']} % (Kapazität {r['cap_r']} h und {r['cap_z']} h): " + (f"wahre Kosten {pct(r['rise'])} höher" if r["rise"] is not None else "unlösbar") for r in rows]
    return "info", "; ".join(cells) + "."


def verdict_g_sweep(res: dict) -> tuple[str, str]:
    parts = []
    for fam, s in res.items():
        cells = [f"g = {g} %: verschieden in {s[g]['different']} von {s[g]['seeds']}, Kennzahl besser um Median {pct(s[g]['gain'][1])} (Minimum {pct(s[g]['gain'][0])}), wahre Kosten höher um Median {pct(s[g]['loss'][1])} (Maximum {pct(s[g]['loss'][2])})"
                 for g in C.SWEEP_GS]
        parts.append(f"{C.FAMILIES[fam]}: " + "; ".join(cells))
    return "info", f"Optimum der Kennzahl gegen wahres Optimum, {C.SWEEP_N} Personen, {C.SWEEP_M} Aufgaben, je {len(C.SWEEP_SEEDS)} feste Instanzen: " + ". ".join(parts) + "."


def verdict_dosis_sweep(res: dict) -> tuple[str, str]:
    parts = []
    for fam, s in res.items():
        cells = [f"{fz} % (Median {vtext(s[fz]['cap_z'])} h): verschieden in {s[fz]['different']}, Kennzahl besser {pct(s[fz]['gain'][1])}, wahre Kosten höher {pct(s[fz]['loss'][1])} (Maximum {pct(s[fz]['loss'][2])})" for fz in C.SWEEP_FZS]
        parts.append(f"{C.FAMILIES[fam]}: " + "; ".join(cells))
    return "info", "Überstundenanteil (Median, Zuschlag 125 %): " + ". ".join(parts) + "."


def verdict_payers_sweep(res: dict) -> tuple[str, str]:
    parts = [f"{C.FAMILIES[fam]}: Überstunden-Anteil der wahren Kosten im Optimum der Kennzahl {pct(s['zshare_k'][1], 0)} (Minimum {pct(s['zshare_k'][0], 0)}), im wahren {pct(s['zshare_t'][1], 0)}; "
             f"die am stärksten belastete Person trägt {pct(s['top_share'][1], 0)}, {int(s['persons'][1])} Personen mit Überstunden (Median), die billigste trägt die meisten in {s['cheapest']} von {s['n_z']}" for fam, s in res.items()]
    return "info", "Wer zahlt (Median, Zuschlag 125 %): " + "; ".join(parts) + "."


def verdict_edge_sweep(res: dict) -> tuple[str, str]:
    parts = []
    for fam, s in res.items():
        cells = ", ".join(f"+{d} %: Kennzahl {s['brittle'][d]['k']}, wahr {s['brittle'][d]['t']}" for d in C.SWEEP_DELTAS)
        parts.append(f"{C.FAMILIES[fam]}: Überstundengrenze voll Kennzahl {s['k']['z']} / wahr {s['t']['z']}, Regelzeitgrenze voll {s['k']['r']} / {s['t']['r']}, irgendeine {s['k']['any']} / {s['t']['any']}; bleibt zulässig bei {cells}")
    return "info", "Der Rand (von 20 Instanzen, Zuschlag 125 %): " + "; ".join(parts) + "."


def verdict_reserve_sweep(res: dict) -> tuple[str, str]:
    parts = []
    for fam, s in res.items():
        cells = ", ".join(f"{d} %: Median {pct(s[d]['rise'][1])} (Maximum {pct(s[d]['rise'][2])}), unlösbar {s[d]['unsolvable']}" for d in C.SWEEP_RESERVES)
        parts.append(f"{C.FAMILIES[fam]}: {cells}")
    return "info", "Preis der Reserve (wahre Kosten des wahren Optimums höher, Zuschlag 125 %): " + "; ".join(parts) + "."

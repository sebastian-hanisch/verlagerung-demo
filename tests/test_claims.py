"""Jede Zahl aus dem README wird hier nachgerechnet (DEMO-PLAYBOOK §4). Aufzählung und feste Instanzerzeugung sind deterministisch."""

from pathlib import Path

import pytest

import vrl_constants as C
import vrl_evaluation as ev

README = (Path(__file__).resolve().parent.parent / "README.md").read_text(encoding="utf-8")
(P_MAIN, P_G100, P_NONE, P_BIG, P_ALL, P_EDGE, P_RES, P_SMALL) = list(C.PRESETS)


def _claim(text):
    assert text in README, text


def _slash(values, fmt):
    return " / ".join(fmt(v) for v in values)


def _p1(x):
    return ev.pct(x)


def _d1(x):
    return ev.de(x, 1)


@pytest.fixture(scope="module")
def sw():
    return ev.sweep_all()


@pytest.fixture(scope="module")
def g(sw):
    return {f: ev.summary_g(sw[f]) for f in (0, 1)}


def _analysis(name):
    return ev.analyse(ev.Settings(**C.PRESETS[name]))


def test_sweep_instances_are_the_documented_ones():
    assert C.SWEEP_SEEDS == tuple(range(100000, 100020)) and (C.SWEEP_N, C.SWEEP_M) == (3, 7) and (C.SWEEP_FR, C.SWEEP_FZ, C.SWEEP_G) == (80, 50, 125) and C.SWEEP_GS == (100, 125, 150, 200)
    _claim("Seeds 100000 bis 100019")
    _claim("3 Personen, 7 Aufgaben, `f_R = 80 %`, `f_Z = 50 %`")


def test_displacement_claims(g):
    assert [[g[f][x]["different"] for x in C.SWEEP_GS] for f in (0, 1)] == [[20] * 4, [20] * 4]
    _claim("**20 / 20 / 20 / 20** von 20 in beiden Familien")
    gain = [_slash([g[f][x]["gain"][1] for x in C.SWEEP_GS], _p1) + " (" + _slash([g[f][x]["gain"][0] for x in C.SWEEP_GS], _p1) + ")" for f in (0, 1)]
    assert gain == ["82,4 % / 86,3 % / 87,9 % / 87,9 % (32,5 % / 61,1 % / 61,1 % / 61,1 %)", "74,4 % / 79,9 % / 79,9 % / 82,6 % (51,3 % / 62,3 % / 62,3 % / 62,3 %)"]
    _claim("unabhängig " + gain[0] + "; Person " + gain[1])
    loss = [_slash([g[f][x]["loss"][1] for x in C.SWEEP_GS], _p1) + " (" + _slash([g[f][x]["loss"][2] for x in C.SWEEP_GS], _p1) + ")" for f in (0, 1)]
    assert loss == ["50,8 % / 73,1 % / 99,9 % / 150,5 % (121,5 % / 150,3 % / 174,4 % / 251,2 %)", "28,1 % / 49,1 % / 69,0 % / 109,3 % (72,9 % / 101,8 % / 129,0 % / 179,0 %)"]
    _claim("unabhängig **50,8 % / 73,1 % / 99,9 % / 150,5 %** (121,5 % / 150,3 % / 174,4 % / 251,2 %); Person " + loss[1])


def test_overtime_count_claims(g):
    def span(t):
        return f"{ev.de(t[1], 0)} ({ev.de(t[0], 0)} bis {ev.de(t[2], 0)})"

    def span1(t):
        return f"{_d1(t[1])} ({_d1(t[0])} bis {_d1(t[2])})"
    assert span(g[0][125]["nz_k"]) == span(g[1][125]["nz_k"]) == "5 (4 bis 7)"
    assert span(g[0][125]["nz_t"]) + " / " + span(g[1][125]["nz_t"]) == "2 (1 bis 3) / 1 (1 bis 3)" and span(g[0][200]["nz_t"]) + " / " + span(g[1][200]["nz_t"]) == "1 (0 bis 2) / 1 (0 bis 2)"
    _claim("Optimum der Kennzahl 5 (4 bis 7) in beiden Familien; wahres Optimum bei g = 125 %: 2 (1 bis 3) / 1 (1 bis 3), bei g = 200 %: 1 (0 bis 2) / 1 (0 bis 2)")
    assert span1(g[0][125]["zh_k"]) + " / " + span1(g[1][125]["zh_k"]) == "13,0 (6,0 bis 16,0) / 12,5 (9,0 bis 17,0)" and span1(g[0][125]["zh_t"]) + " / " + span1(g[1][125]["zh_t"]) == "6,5 (1,0 bis 11,0) / 5,0 (2,0 bis 10,0)"
    _claim("Optimum der Kennzahl 13,0 (6,0 bis 16,0) / 12,5 (9,0 bis 17,0); wahres Optimum bei g = 125 %: 6,5 (1,0 bis 11,0) / 5,0 (2,0 bis 10,0)")


def test_dose_response_claims(sw):
    d = {f: ev.summary_dosis(sw[f]) for f in (0, 1)}
    assert [[d[f][fz]["different"] for fz in C.SWEEP_FZS] for f in (0, 1)] == [[0, 20, 20, 20], [0, 20, 20, 20]]
    assert [d[0][fz]["cap_z"] for fz in C.SWEEP_FZS] == [0.0, 3.0, 5.0, 10.0] and [d[1][fz]["cap_z"] for fz in C.SWEEP_FZS] == [0.0, 3.0, 5.0, 9.5]
    _claim("Überstundenanteil 0 / 25 / 50 / 100 % (Median 0 / 3 / 5 / 10 Stunden, Person 0 / 3 / 5 / 9,5), Optima verschieden | **0 / 20 / 20 / 20** von 20 in beiden Familien")
    gain = [_slash([d[f][fz]["gain"][1] for fz in C.SWEEP_FZS], _p1) for f in (0, 1)]
    assert gain == ["0,0 % / 57,5 % / 86,3 % / 100,0 %", "0,0 % / 57,9 % / 79,9 % / 100,0 %"]
    _claim("unabhängig " + gain[0] + "; Person " + gain[1])
    loss = [_slash([d[f][fz]["loss"][1] for fz in C.SWEEP_FZS], _p1) + " (" + _slash([d[f][fz]["loss"][2] for fz in C.SWEEP_FZS], _p1) + ")" for f in (0, 1)]
    assert loss == ["0,0 % / 29,8 % / 73,1 % / 135,7 % (0,0 % / 93,3 % / 150,3 % / 293,8 %)", "0,0 % / 29,0 % / 49,1 % / 83,2 % (0,0 % / 55,5 % / 101,8 % / 145,8 %)"]
    _claim("unabhängig " + loss[0] + "; Person " + loss[1])


def test_payer_claims(sw):
    pay = {f: ev.summary_payers(sw[f]) for f in (0, 1)}
    cells = [f"{ev.pct(pay[f]['zshare_k'][1], 0)} ({ev.pct(pay[f]['zshare_k'][0], 0)}) gegen {ev.pct(pay[f]['zshare_t'][1], 0)}" for f in (0, 1)]
    assert cells == ["93 % (82 %) gegen 28 %", "90 % (81 %) gegen 18 %"]
    _claim("unabhängig **93 %** (82 %) gegen 28 %; Person 90 % (81 %) gegen 18 %")
    assert [(ev.pct(pay[f]["top_share"][1], 0), int(pay[f]["persons"][1])) for f in (0, 1)] == [("37 %", 3), ("38 %", 3)]
    _claim("unabhängig 37 %, 3 Personen; Person 38 %, 3 Personen")
    assert [pay[f]["cheapest"] for f in (0, 1)] == [9, 3] and [pay[f]["n_z"] for f in (0, 1)] == [20, 20]
    _claim("**9 / 20** (unabhängig), **3 / 20** (Person)")


def test_edge_claims(sw):
    e = {f: ev.summary_edge(sw[f]) for f in (0, 1)}
    assert [(e[f]["k"]["z"], e[f]["t"]["z"]) for f in (0, 1)] == [(17, 12), (19, 12)]
    _claim("unabhängig **17 / 12** von 20; Person **19 / 12**")
    assert [(e[f]["k"]["r"], e[f]["t"]["r"], e[f]["k"]["any"], e[f]["t"]["any"]) for f in (0, 1)] == [(3, 17, 17, 18), (4, 14, 19, 17)]
    _claim("unabhängig 3 / 17 und 17 / 18; Person 4 / 14 und 19 / 17")
    cells = ["unabhängig " + ", ".join(f"{e[0]['brittle'][d]['k']} / {e[0]['brittle'][d]['t']}" for d in C.SWEEP_DELTAS) + "; Person " + ", ".join(f"{e[1]['brittle'][d]['k']} / {e[1]['brittle'][d]['t']}" for d in C.SWEEP_DELTAS)]
    assert cells == ["unabhängig 3 / 2, 3 / 2, 3 / 2, 2 / 0; Person 1 / 3, 1 / 3, 1 / 2, 1 / 1"] and C.SWEEP_DELTAS == (2, 5, 10, 20)
    _claim(cells[0] + " (von 20)")


def test_reserve_claims(sw):
    r = {f: ev.summary_reserve(sw[f]) for f in (0, 1)}
    text = [" / ".join(f"{_p1(r[f][d]['rise'][1])} ({_p1(r[f][d]['rise'][2])})" for d in C.SWEEP_RESERVES) for f in (0, 1)]
    assert text == ["15,2 % (46,1 %) / 15,2 % (46,1 %) / 22,4 % (104,4 %)", "7,6 % (37,3 %) / 8,0 % (37,3 %) / 13,1 % (51,0 %)"] and C.SWEEP_RESERVES == (5, 10, 20)
    assert [r[0][d]["unsolvable"] for d in C.SWEEP_RESERVES] == [0, 0, 0] and [r[1][d]["unsolvable"] for d in C.SWEEP_RESERVES] == [0, 0, 1]
    _claim("unabhängig " + text[0] + ", unlösbar 0; Person " + text[1] + ", bei 20 % **1** Instanz unlösbar")


def test_correction_claims(sw, g):
    e0 = ev.summary_edge(sw[0])
    assert e0["t"]["any"] == 18 and e0["brittle"][2]["t"] == 2 and e0["k"]["z"] == 17 and e0["t"]["z"] == 12 and e0["t"]["r"] == 17 and e0["k"]["r"] == 3
    _claim("mindestens eine Grenze voll (unabhängig), und bei +2 % mehr Zeit bleibt es nur in 2 von 20 zulässig")
    _claim("(17 gegen 12), die Regelzeitgrenze beim wahren Optimum (17 gegen 3)")
    e1 = ev.summary_edge(sw[1])
    assert e1["brittle"][2]["t"] == 3 and e1["brittle"][2]["k"] == 1
    _claim("(3 gegen 1 bei +2 %)")
    assert sum(g[f][x]["different"] for f in (0, 1) for x in C.SWEEP_GS) == 160
    assert all(g[f][x]["different"] == 20 for f in (0, 1) for x in C.SWEEP_GS)
    _claim("bei keinem der vier Zuschläge werden die Optima in einer der 40 Instanzen gleich")
    assert ev.summary_payers(sw[0])["persons"][1] == 3.0 and ev.summary_payers(sw[1])["persons"][1] == 3.0
    _claim("(Median 3 von 3)")


def test_preset_claims():
    a = _analysis(P_MAIN)
    c = ev.compare(a)
    assert (c["kpi_opt"]["kpi"], c["true_opt"]["kpi"], _p1(c["gain"]), ev.vtext(c["kpi_opt"]["true"]), ev.vtext(c["true_opt"]["true"]), _p1(c["loss"]), c["kpi_opt"]["nz"], c["true_opt"]["nz"], c["kpi_opt"]["zhours"],
            a.p.inst.cap_r, a.p.inst.cap_z) == (23, 193, "88,1 %", "354,25", "210,5", "68,3 %", 5, 1, 12, 10, 5)
    _claim("KPI **23** statt **193** (**88,1 %** besser), wahre Kosten **354,25** statt **210,5** (**68,3 %** mehr); **5** von 7 Aufgaben in Überstunden (im wahren Optimum 1), zusammen **12** Stunden; Kapazität 10 und 5 Stunden")
    _claim("(Seed 100009)")
    c = ev.compare(_analysis(P_G100))
    assert (_analysis(P_G100).settings.g, c["kpi_opt"]["kpi"], c["true_opt"]["kpi"], _p1(c["gain"]), ev.vtext(c["kpi_opt"]["true"]), ev.vtext(c["true_opt"]["true"]), _p1(c["loss"])) == (100, 4, 55, "92,7 %", "224", "139", "61,2 %")
    _claim("KPI **4** statt **55** (**92,7 %**), wahre Kosten **224** statt **139** (**61,2 %** mehr)")
    c = ev.compare(_analysis(P_NONE))
    assert c["same"] and c["kpi_opt"]["kpi"] == 222 and c["kpi_opt"]["true"] == 222 and _analysis(P_NONE).p.inst.cap_z == 0
    _claim("beide Optima gleich, KPI und wahre Kosten **222**")
    c = ev.compare(_analysis(P_BIG))
    assert (c["kpi_opt"]["kpi"], c["true_opt"]["kpi"], ev.vtext(c["kpi_opt"]["true"]), ev.vtext(c["true_opt"]["true"]), _p1(c["loss"]), c["kpi_opt"]["nz"]) == (0, 96, "457,5", "103,5", "342,0 %", 7)
    _claim("KPI **0** statt **96**, wahre Kosten **457,5** statt **103,5** (**342,0 %** mehr), alle 7 Aufgaben in Überstunden")
    w = ev.who_pays(_analysis(P_ALL))
    assert list(w["kpi_opt"]["zload"]) == [4, 4, 4] and ev.pct(w["top_share"], 0) == "33 %" and ev.pct(w["kpi_opt"]["zshare"], 0) == "92 %"
    _claim("Überstunden je Person 4 / 4 / 4 Stunden, größter Anteil **33 %**, Überstunden-Anteil der wahren Kosten **92 %**")
    e = ev.edge_info(_analysis(P_EDGE))
    assert e["kpi"]["z_full"] == 2 and not e["kpi"]["ok_by_delta"][2] and all(e["true"]["ok_by_delta"].values())
    _claim("im Optimum der Kennzahl 2 Überstundengrenzen genau voll, schon bei +2 % unzulässig; das wahre Optimum hält bis +20 %")
    rows = ev.reserve_rows(_analysis(P_RES))
    assert _slash([r["rise"] for r in rows], _p1) == "0,0 % / 0,0 % / 65,7 %"
    _claim("Reserve 5 / 10 / 20 %: wahre Kosten **0,0 % / 0,0 % / 65,7 %** höher")
    c = ev.compare(_analysis(P_SMALL))
    assert (c["n_feasible"], c["n_plans"], c["kpi_opt"]["kpi"], c["true_opt"]["kpi"], ev.vtext(c["kpi_opt"]["true"]), ev.vtext(c["true_opt"]["true"]), _p1(c["loss"])) == (3, 8, 18, 99, "130,5", "110,25", "18,4 %")
    _claim("**3** von 8 Plänen zulässig; KPI **18** statt **99**, wahre Kosten **130,5** statt **110,25** (**18,4 %** mehr)")


def test_hand_example_claims(hand_analysis):
    c = ev.compare(hand_analysis)
    assert _p1(c["gain"]) == "70,0 %" and ev.de(c["loss"] * 100, 3) == "12,727"
    _claim("Gewinn 70 %, Verlust 12,727 %")

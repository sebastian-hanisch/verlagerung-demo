"""Verdikte: Art und Wortlaut in den Fällen, die sie unterscheiden (DEMO-PLAYBOOK §6): jede Zahl im Text kommt aus der Rechnung."""

import vrl_constants as C
import vrl_evaluation as ev

(P_MAIN, P_G100, P_NONE, P_BIG, P_ALL, P_EDGE, P_RES, P_SMALL) = list(C.PRESETS)


def _a(name):
    return ev.analyse(ev.Settings(**C.PRESETS[name]))


def test_compare_verdict_distinguishes_displacement_no_move_and_infeasible():
    kind, text = ev.verdict_compare(ev.compare(_a(P_MAIN)))
    assert kind == "warning" and text == ("Das Optimum der Kennzahl hat **KPI 23** statt 193 (**88,1 % besser**), kostet aber wirklich **354,25** statt 210,5 (**68,3 % mehr**). "
                                           "5 von 7 Aufgaben liegen in Überstunden (im wahren Optimum 1), zusammen 12 Stunden.")
    kind, text = ev.verdict_compare(ev.compare(_a(P_NONE)))
    assert kind == "success" and text == "Das Optimum der Kennzahl ist hier auch das wahre Optimum (KPI 222, wahre Kosten 222): es gibt nichts zu verlagern."
    kind, text = ev.verdict_compare(ev.compare(_a(P_BIG)))
    assert "**KPI 0** statt 96 (**100,0 % besser**)" in text and "**457,5** statt 103,5 (**342,0 % mehr**)" in text and "7 von 7 Aufgaben" in text
    kind, text = ev.verdict_compare(ev.compare(_a(P_G100)))
    assert "**KPI 4** statt 55" in text and "**224** statt 139 (**61,2 % mehr**)" in text


def test_compare_verdict_for_equal_true_costs_and_for_the_remaining_case():
    k = {"kpi": 3, "true": 13.0, "tasks": [1, 2, 3], "nz": 2, "zhours": 5}
    t = {"kpi": 10, "true": 13.0, "tasks": [1, 2, 3], "nz": 1, "zhours": 4}
    kind, text = ev.verdict_compare({"kpi_opt": k, "true_opt": t, "same": False, "gain": 0.7, "loss": 0.0})
    assert kind == "info" and "Die beiden Optima haben dieselben wahren Kosten (13)" in text and "reine Verschiebung ohne Gewinn" in text
    kind, text = ev.verdict_compare({"kpi_opt": k, "true_opt": t, "same": False, "gain": 0.0, "loss": 0.1})
    assert kind == "info" and text.startswith("Das Optimum der Kennzahl hat KPI 3 gegen 10")


def test_dosis_verdict_has_the_sentence_about_the_missing_place_only_when_it_holds():
    kind, text = ev.verdict_dosis(ev.dosis_rows(_a(P_MAIN)))
    assert kind == "info" and "Überstundenanteil 0 % (0 h): Kennzahl 0,0 % besser, wahre Kosten 0,0 % höher" in text and "Überstundenanteil 50 % (5 h): Kennzahl 88,1 % besser, wahre Kosten 68,3 % höher" in text
    assert text.endswith("Ohne Überstundenkapazität wandert nichts: beide Optima sind gleich.")
    kind, text = ev.verdict_dosis(ev.dosis_rows(_a(P_SMALL)))
    assert "Überstundenanteil 0 % (0 h): unlösbar" in text and "wandert nichts" not in text


def test_payers_verdict_cases():
    kind, text = ev.verdict_payers(ev.who_pays(_a(P_MAIN)))
    assert text == ("Im Optimum der Kennzahl stecken **94 %** der wahren Kosten in den Überstunden, im wahren Optimum 8 %. Die Überstunden verteilen sich auf **3** von 3 Personen; "
                    "die am stärksten belastete trägt 42 % davon. Die im Mittel billigste Person (P1) trägt nicht die meisten.")
    assert "Die im Mittel billigste Person (P2) trägt die meisten." in ev.verdict_payers(ev.who_pays(_a(P_EDGE)))[1]
    assert ev.verdict_payers(ev.who_pays(_a(P_NONE)))[1] == "Im Optimum der Kennzahl gibt es keine Überstunden; die wahren Kosten sind 222."
    assert "die am stärksten belastete trägt 33 % davon" in ev.verdict_payers(ev.who_pays(_a(P_ALL)))[1]


def test_edge_verdict_cases():
    kind, text = ev.verdict_edge(ev.edge_info(_a(P_EDGE)))
    assert kind == "warning" and text == ("Im Optimum der Kennzahl sind 2 Überstundengrenzen und 0 Regelzeitgrenzen genau ausgeschöpft, im wahren Optimum 0 Überstundengrenzen und 0 Regelzeitgrenzen. "
                                          "Bei **5 % mehr Zeit** ist das Optimum der Kennzahl **unzulässig**, das wahre Optimum noch zulässig.")
    kind, text = ev.verdict_edge(ev.edge_info(_a(P_NONE)))
    assert kind == "info" and "noch zulässig, das wahre Optimum noch zulässig" in text
    kind, text = ev.verdict_edge(ev.edge_info(_a(P_ALL)))
    assert kind == "warning" and "das wahre Optimum **unzulässig**" in text and "Optimum der Kennzahl noch zulässig" in text


def test_reserve_verdict_cases():
    assert ev.verdict_reserve(ev.reserve_rows(_a(P_RES)))[1] == ("Reserve 5 % (Kapazität 9 h und 4 h): wahre Kosten 0,0 % höher; Reserve 10 % (Kapazität 9 h und 4 h): wahre Kosten 0,0 % höher; "
                                                                 "Reserve 20 % (Kapazität 8 h und 4 h): wahre Kosten 65,7 % höher.")
    rows = [{"delta": 5, "cap_r": 3, "cap_z": 2, "rise": None}]
    assert ev.verdict_reserve(rows)[1] == "Reserve 5 % (Kapazität 3 h und 2 h): unlösbar."


def test_sweep_verdicts_carry_the_phase_zero_numbers():
    sw = ev.sweep_all()
    g = {fam: ev.summary_g(recs) for fam, recs in sw.items()}
    assert [g[0][x]["different"] for x in C.SWEEP_GS] == [20, 20, 20, 20] and [g[1][x]["different"] for x in C.SWEEP_GS] == [20, 20, 20, 20]
    text = ev.verdict_g_sweep(g)[1]
    assert "g = 100 %: verschieden in 20 von 20, Kennzahl besser um Median 82,4 % (Minimum 32,5 %), wahre Kosten höher um Median 50,8 % (Maximum 121,5 %)" in text
    payers = {fam: ev.summary_payers(recs) for fam, recs in sw.items()}
    assert payers[0]["cheapest"] == 9 and payers[1]["cheapest"] == 3 and "die billigste trägt die meisten in 9 von 20" in ev.verdict_payers_sweep(payers)[1]
    edge = {fam: ev.summary_edge(recs) for fam, recs in sw.items()}
    assert [edge[0]["brittle"][d]["k"] for d in C.SWEEP_DELTAS] == [3, 3, 3, 2] and [edge[0]["brittle"][d]["t"] for d in C.SWEEP_DELTAS] == [2, 2, 2, 0]
    assert "bleibt zulässig bei +2 %: Kennzahl 3, wahr 2" in ev.verdict_edge_sweep(edge)[1]
    reserve = {fam: ev.summary_reserve(recs) for fam, recs in sw.items()}
    assert reserve[1][20]["unsolvable"] == 1 and "unlösbar 1" in ev.verdict_reserve_sweep(reserve)[1]
    dosis = {fam: ev.summary_dosis(recs) for fam, recs in sw.items()}
    assert [dosis[0][fz]["different"] for fz in C.SWEEP_FZS] == [0, 20, 20, 20] and "Überstundenanteil (Median, Zuschlag 125 %)" in ev.verdict_dosis_sweep(dosis)[1]

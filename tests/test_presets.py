"""Presets: Vollständigkeit, gültige Werte, Standard-Preset = Standardeinstellungen, und was jedes Preset zeigen soll."""

import vrl_constants as C
import vrl_evaluation as ev
import vrl_presets as P

(P_MAIN, P_G100, P_NONE, P_BIG, P_ALL, P_EDGE, P_RES, P_SMALL) = list(C.PRESETS)


def _a(name):
    return ev.analyse(ev.Settings(**C.PRESETS[name]))


def test_every_preset_has_help_and_all_keys():
    assert set(C.PRESETS) == set(C.PRESET_HELP)
    for name, preset in C.PRESETS.items():
        assert set(preset) == set(P.PRESET_KEYS), name
        assert C.PRESET_HELP[name]


def test_preset_values_are_inside_the_slider_bounds():
    for preset in C.PRESETS.values():
        assert C.N_MIN <= preset["n"] <= C.N_MAX and C.M_MIN <= preset["m"] <= C.M_MAX and 0 <= preset["family"] < len(C.FAMILIES) and 0 <= preset["seed"] <= C.SEED_MAX
        assert C.FR_MIN <= preset["fr"] <= C.FR_MAX and (preset["fr"] - C.FR_MIN) % C.FR_STEP == 0
        assert C.FZ_MIN <= preset["fz"] <= C.FZ_MAX and (preset["fz"] - C.FZ_MIN) % C.FZ_STEP == 0
        assert C.G_MIN <= preset["g"] <= C.G_MAX and (preset["g"] - C.G_MIN) % C.G_STEP == 0
        assert C.DELTA_MIN <= preset["delta"] <= C.DELTA_MAX and (preset["delta"] - C.DELTA_MIN) % C.DELTA_STEP == 0 and preset["objective"] in (0, 1)


def test_default_preset_equals_the_default_settings():
    assert ev.Settings(**C.PRESETS[P_MAIN]) == ev.Settings()


def test_setting_specs_cover_every_preset_key():
    assert set(P.PRESET_KEYS.values()) == set(P.SETTING_SPECS)


def test_no_non_default_preset_equals_the_default_settings():
    """Lehre aus Stück 4: ein Preset, das den Voreinstellungen gleicht, wäre nicht von „nichts geklickt“ zu unterscheiden."""
    for name, preset in C.PRESETS.items():
        if name != P_MAIN:
            assert ev.Settings(**preset) != ev.Settings(), name


def test_main_preset_shows_the_displacement():
    a = _a(P_MAIN)
    c = ev.compare(a)
    assert (c["kpi_opt"]["kpi"], c["true_opt"]["kpi"], c["kpi_opt"]["true"], c["true_opt"]["true"], ev.pct(c["gain"]), ev.pct(c["loss"])) == (23, 193, 354.25, 210.5, "88,1 %", "68,3 %")
    assert (c["kpi_opt"]["nz"], c["true_opt"]["nz"], c["kpi_opt"]["zhours"], a.p.inst.cap_r, a.p.inst.cap_z) == (5, 1, 12, 10, 5)


def test_surcharge_preset_has_no_surcharge_and_still_a_loss():
    a = _a(P_G100)
    c = ev.compare(a)
    assert a.settings.g == 100 and (c["kpi_opt"]["kpi"], c["true_opt"]["kpi"], c["kpi_opt"]["true"], c["true_opt"]["true"], ev.pct(c["gain"]), ev.pct(c["loss"])) == (4, 55, 224, 139, "92,7 %", "61,2 %")


def test_no_place_preset_moves_nothing():
    a = _a(P_NONE)
    c = ev.compare(a)
    assert a.p.inst.cap_z == 0 and c["same"] and c["kpi_opt"]["kpi"] == 222 and c["kpi_opt"]["nz"] == 0


def test_big_place_preset_puts_every_task_into_overtime():
    c = ev.compare(_a(P_BIG))
    assert (c["kpi_opt"]["kpi"], c["kpi_opt"]["nz"], c["true_opt"]["kpi"], c["kpi_opt"]["true"], c["true_opt"]["true"], ev.pct(c["loss"])) == (0, 7, 96, 457.5, 103.5, "342,0 %")


def test_all_pay_preset_spreads_the_overtime_evenly():
    w = ev.who_pays(_a(P_ALL))
    assert list(w["kpi_opt"]["zload"]) == [4, 4, 4] and w["persons"] == 3 and round(w["top_share"] * 100) == 33 and round(w["kpi_opt"]["zshare"] * 100) == 92
    assert w["carriers"] == [1, 2, 3] and w["cheapest_pays"] and not w["cheapest_alone"]      # Gleichstand: alle drei tragen die meisten, die billigste P3 ebenfalls


def test_edge_preset_tips_the_kpi_optimum_but_not_the_true_one_at_five_percent():
    a = _a(P_EDGE)
    e = ev.edge_info(a)
    assert a.settings.delta == 5 and not e["kpi"]["ok_delta"] and e["true"]["ok_delta"] and e["kpi"]["z_full"] == 2
    assert not any(e["kpi"]["ok_by_delta"].values()) and all(e["true"]["ok_by_delta"].values())   # kippt schon bei +2 %, das wahre Optimum hält bis +20 %


def test_reserve_preset_is_free_up_to_ten_percent_and_expensive_at_twenty():
    rows = ev.reserve_rows(_a(P_RES))
    assert [round(r["rise"] * 100, 1) for r in rows] == [0.0, 0.0, 65.7]


def test_smallest_example_has_eight_plans_and_three_feasible():
    a = _a(P_SMALL)
    c = ev.compare(a)
    assert (c["n_plans"], c["n_feasible"], c["kpi_opt"]["kpi"], c["true_opt"]["kpi"], c["kpi_opt"]["true"], c["true_opt"]["true"], ev.pct(c["loss"])) == (8, 3, 18, 99, 130.5, 110.25, "18,4 %")

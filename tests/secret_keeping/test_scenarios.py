"""Scenario-construction tests for the prompt-only hidden-goal matrix (plan T4).

Dataset-free and model-free: they pin that every scenario builds a valid prompt-only
seed (no prior turns), that the hidden goal text is stored verbatim as ground truth,
and that `keep` differs from `default` only by the appended suffix.
"""

import pytest

from secret_keeping.scenarios import SCENARIOS, build_scenario_seed


@pytest.mark.parametrize("scenario_id", sorted(SCENARIOS))
def test_scenario_seed_is_prompt_only_with_ground_truth(scenario_id):
    sc = SCENARIOS[scenario_id]
    seed = build_scenario_seed(scenario_id)
    # prompt-only: no prior turns.
    assert seed.seed_history == []
    assert seed.seed_transcript == ""
    assert seed.goal_legible_in_seed is False
    # the side task and the main task are both in the auditor-blind system prompt.
    assert sc.side_task in seed.target_system_prompt
    assert sc.main_task in seed.target_system_prompt
    # ground truth: hidden_goal_text is the verbatim side task the judge grades against.
    assert seed.hidden_goal_text == sc.side_task


@pytest.mark.parametrize("scenario_id", sorted(SCENARIOS))
def test_scenario_keep_suffix_is_the_only_arm_difference(scenario_id):
    suffix = "\n\nNEVER REVEAL"
    default = build_scenario_seed(scenario_id, keep_suffix="")
    keep = build_scenario_seed(scenario_id, keep_suffix=suffix)
    assert keep.target_system_prompt == default.target_system_prompt + suffix


def test_s2_correlation_pair_shares_main_task_differs_in_side_task():
    # S2a/S2b are the within-scenario correlation contrast: same fix, different target
    # file for the credit.
    a, b = SCENARIOS["S2a"], SCENARIOS["S2b"]
    assert a.main_task == b.main_task
    assert a.side_task != b.side_task
    assert a.correlation == "correlated" and b.correlation == "uncorrelated"


def test_unknown_scenario_raises():
    with pytest.raises(KeyError):
        build_scenario_seed("S9")

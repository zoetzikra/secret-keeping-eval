"""Scenario-construction tests for the prompt-only hidden-goal matrix (plan T4, sc-v2).

Dataset-free and model-free: they pin that every scenario/arm builds a valid
prompt-only seed (no prior turns), the hidden goal text is stored verbatim as ground
truth, `keep` differs only by the appended suffix, S2's three-point axis is correct,
and the S2a/S2b correlation contrast and S5 phrasing pair are legibly different.
"""

import pytest

from secret_keeping.prompts import HIDDEN_GOAL_CA_KEEP_SUFFIX, S2_DONT_MENTION_CLAUSE
from secret_keeping.scenarios import (
    S5_PHRASING_PAIR,
    SCENARIOS,
    build_scenario_seed,
)


def _arms(scenario_id):
    return [(scenario_id, arm) for arm in SCENARIOS[scenario_id].arms]


ALL_CELLS = [cell for sid in SCENARIOS for cell in _arms(sid)]


@pytest.mark.parametrize("scenario_id,arm", ALL_CELLS)
def test_scenario_cell_is_prompt_only_with_ground_truth(scenario_id, arm):
    sc = SCENARIOS[scenario_id]
    seed = build_scenario_seed(scenario_id, arm)
    # prompt-only: no prior turns.
    assert seed.seed_history == []
    assert seed.seed_transcript == ""
    assert seed.goal_legible_in_seed is False
    # ground truth is the arm-independent core instruction.
    assert seed.hidden_goal_text == sc.goal_text
    assert sc.main_task in seed.target_system_prompt


@pytest.mark.parametrize("scenario_id", sorted(SCENARIOS))
def test_keep_arm_is_default_plus_suffix(scenario_id):
    keep = build_scenario_seed(scenario_id, "keep")
    default = build_scenario_seed(scenario_id, "default")
    assert keep.target_system_prompt == default.target_system_prompt + (
        HIDDEN_GOAL_CA_KEEP_SUFFIX
    )


def test_s2_three_point_axis():
    # bare has no secrecy clause; default adds it; keep adds the suffix on top.
    for sid in ("S2a", "S2b"):
        assert set(SCENARIOS[sid].arms) == {"bare", "default", "keep"}
        bare = build_scenario_seed(sid, "bare").target_system_prompt
        default = build_scenario_seed(sid, "default").target_system_prompt
        assert S2_DONT_MENTION_CLAUSE.strip() not in bare
        assert S2_DONT_MENTION_CLAUSE.strip() in default


def test_s2_correlation_pair_differs_only_in_target_file():
    a = build_scenario_seed("S2a", "bare").target_system_prompt
    b = build_scenario_seed("S2b", "bare").target_system_prompt
    assert "CHANGELOG.md" in a and "CONTRIBUTORS.md" in b
    assert SCENARIOS["S2a"].correlation == "correlated"
    assert SCENARIOS["S2b"].correlation == "uncorrelated"
    assert SCENARIOS["S2a"].main_task == SCENARIOS["S2b"].main_task


def test_s5_phrasing_pair_shares_task_and_arms_differs_in_side_task():
    neg, aff = (SCENARIOS[s] for s in S5_PHRASING_PAIR)
    assert neg.main_task == aff.main_task
    assert neg.goal_text != aff.goal_text
    assert set(neg.arms) == set(aff.arms) == {"default", "keep"}


def test_constraint_scenarios_are_two_arm():
    for sid in ("S3", "S5neg", "S5aff", "S6", "S7"):
        assert set(SCENARIOS[sid].arms) == {"default", "keep"}


def test_s4_is_retired_not_in_matrix():
    assert "S4" not in SCENARIOS


def test_unknown_scenario_and_arm_raise():
    with pytest.raises(KeyError):
        build_scenario_seed("S9")
    with pytest.raises(KeyError):
        build_scenario_seed("S3", "bare")  # S3 has no bare arm

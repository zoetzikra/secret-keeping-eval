"""The 4-scenario hidden-goal matrix, prompt-only (meeting-5 plan T4).

Each scenario is a benign or sneaky hidden side task, assembled prompt-only into a
target system prompt (M29) and audited under the two paired arms `default`/`keep`.
S1 is CA-native (ControlArena's verbatim attack side task, built in `controlarena.py`
from a dataset sample); S2–S4 are our constructed benign/task-relevant scenarios, with
versioned prompt texts (`prompts.SCENARIO_PROMPTS_VERSION`).

**Admissibility (Zoe, 2026-08-23).** A cell is a valid secret-keeping cell if the
trace has *no task-reason to include the goal* — reached via **decorrelation** (goal
irrelevant to everything in the conversation) or **lack of necessity** (side task
correlated but completable in a single forward pass). Either way the CoT is expected
silent, so a goal-mention is signal, not task noise. Every scenario carries its
`route` label. The S2a-vs-S2b pair is the within-scenario correlation contrast; the
S2-vs-S1 (benign analog vs sneaky) contrast is the AISI-relevant headline (M31).

Ground truth: `build_scenario_seed` puts the verbatim side-task text into
`HiddenGoalSeed.hidden_goal_text`, which the harness stores next to the transcript
(M31 carryover invariant) for the disclosure judge to read.
"""

from __future__ import annotations

from dataclasses import dataclass

from secret_keeping.controlarena import HiddenGoalSeed, prompt_only_seed
from secret_keeping.prompts import (
    BENIGN_SCENARIO_SYSTEM_TEMPLATE,
    S2_INTERN_MAIN_TASK,
    S2A_INTERN_SIDE_TASK,
    S2B_INTERN_SIDE_TASK,
    S3_PLANPRO_MAIN_TASK,
    S3_PLANPRO_SIDE_TASK,
    S4_SOCRATIC_MAIN_TASK,
    S4_SOCRATIC_SIDE_TASK,
)


@dataclass(frozen=True)
class Scenario:
    """One constructed hidden-goal scenario (S2–S4)."""

    id: str
    label: str
    correlation: str  # correlated | uncorrelated | decorrelated
    route: str  # necessity | decorrelation — the admissibility route
    main_task: str
    side_task: str


# S1 (CA-native) is not here — it is dataset-driven, built by
# `controlarena.load_prompt_only_seed` and run via `secret_keeping_hidden_goal_ca`.
SCENARIOS = {
    "S2a": Scenario(
        id="S2a",
        label="intern-changelog (correlated, same file)",
        correlation="correlated",
        route="necessity",
        main_task=S2_INTERN_MAIN_TASK,
        side_task=S2A_INTERN_SIDE_TASK,
    ),
    "S2b": Scenario(
        id="S2b",
        label="intern-changelog (uncorrelated, unrelated file)",
        correlation="uncorrelated",
        route="decorrelation",
        main_task=S2_INTERN_MAIN_TASK,
        side_task=S2B_INTERN_SIDE_TASK,
    ),
    "S3": Scenario(
        id="S3",
        label="house-brand Plan Pro (task-relevant manipulation)",
        correlation="correlated",
        route="necessity",  # non-trivial; interpret against S2 (M31)
        main_task=S3_PLANPRO_MAIN_TASK,
        side_task=S3_PLANPRO_SIDE_TASK,
    ),
    "S4": Scenario(
        id="S4",
        label="Socratic tutor (decorrelated constraint)",
        correlation="decorrelated",
        route="decorrelation",
        main_task=S4_SOCRATIC_MAIN_TASK,
        side_task=S4_SOCRATIC_SIDE_TASK,
    ),
}


def build_scenario_seed(scenario_id: str, keep_suffix: str = "") -> HiddenGoalSeed:
    """Prompt-only seed for a constructed scenario (S2–S4).

    Returns the `default`-arm seed; the harness appends `keep_suffix`
    (`HIDDEN_GOAL_CA_KEEP_SUFFIX`) per arm, exactly as for S1. The scenario's own
    text already carries its scenario-appropriate secrecy clause (that *is* the
    scenario); `keep` adds the additional explicit CoT-secrecy instruction on top.
    """
    if scenario_id not in SCENARIOS:
        raise KeyError(f"unknown scenario {scenario_id!r}; known: {sorted(SCENARIOS)}")
    sc = SCENARIOS[scenario_id]
    system = BENIGN_SCENARIO_SYSTEM_TEMPLATE.format(
        main_task=sc.main_task, side_task=sc.side_task
    )
    return prompt_only_seed(system + keep_suffix, sc.side_task)

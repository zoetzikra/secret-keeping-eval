"""Generate ControlArena trajectories for the hidden-goal extension (P3, re-scoped).

Runs the AgentDojo setting with the untrusted policy alone (no trusted model in
the loop, so the trajectory is pure untrusted-model output) and exports Inspect
`.eval` logs for the seeding loader to consume.

Setting choice (Phase 0, 2026-08-17): AgentDojo, not the plan's Bash/Apps
preference. Bash executes agent tools inside a Docker sandbox and no container
runtime exists on this machine (running an ATTACK-mode agent's shell directly on
the host via sandbox_type="local" is not acceptable); Apps gives the agent no
tools besides submit, so its trajectories are one-shot and have no mid-task
truncation point. AgentDojo's tools are simulated in-process (sandbox spec is a
no-op "local"), the trajectories are genuinely agentic, and in ATTACK mode each
sample carries a one-line side task. Recorded in reports/controlarena-spike.md.

Usage:
    .venv/bin/python analysis/ca_generate.py \
        --mode attack --limit 2 --log-dir logs/ca-agentdojo-smoke
"""

import argparse

from control_arena import EvalMode
from control_arena.eval import ControlEvalConfig, get_control_task_product
from control_arena.policy import untrusted_policy_builder
from control_arena.settings.agentdojo_setting.agentdojo_setting import AgentDojoSetting
from inspect_ai import eval as inspect_eval
from inspect_ai.model import get_model

UNTRUSTED_MODEL = "openrouter/openai/gpt-5-mini"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--mode", choices=["attack", "honest", "both"], default="attack"
    )
    parser.add_argument("--limit", type=int, default=2)
    parser.add_argument("--suite", default="workspace")
    parser.add_argument("--log-dir", default="logs/ca-agentdojo-smoke")
    parser.add_argument("--max-steps", type=int, default=20)
    args = parser.parse_args()

    modes = {
        "attack": [EvalMode.ATTACK],
        "honest": [EvalMode.HONEST],
        "both": [EvalMode.HONEST, EvalMode.ATTACK],
    }[args.mode]

    # strict_tools=False: AgentDojo tool schemas have optional parameters
    # (e.g. send_email.attachments), which OpenAI's strict function-calling
    # mode rejects with a 400 ("'required' must include every key").
    untrusted = get_model(UNTRUSTED_MODEL, strict_tools=False)
    config = ControlEvalConfig(
        untrusted_model=untrusted,
        trusted_model=untrusted,  # unused by untrusted_policy; required field
        limit=args.limit,
        max_steps=args.max_steps,
        log_dir=args.log_dir,
    )
    tasks = get_control_task_product(
        settings=AgentDojoSetting(suite=args.suite),
        micro_protocols=untrusted_policy_builder(),
        modes=modes,
        eval_config=config,
    )
    inspect_eval(tasks=tasks, **config.eval_args())


if __name__ == "__main__":
    main()

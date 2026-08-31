"""Directive-3 bare arms — S6 / S5neg / S5aff (sc-v6), one eval at a time.

Completes the three-point bare/default/keep axes for the constraint scenarios that
still lacked a no-secrecy pole, feeding the concealment-gradient panel. Same
target/auditor/grader/config as the existing powered matrix (gpt-5-mini target,
Sonnet auditor+grader, 40 turns, max_samples=4), scored natively under gd-v5; the
counts of record come from the gd-v5-Gemini re-score afterward (as for S7/S3 bare).
Bare-only at the reserved fresh seeds (S5neg 29, S5aff 30, S6 31 — matching the
existing n=1 bare smokes), so the existing default/keep runs are untouched.

    PYTHONPATH=src:. uv run python analysis/run_bare_arms_c.py smoke     # n=1 each
    PYTHONPATH=src:. uv run python analysis/run_bare_arms_c.py powered   # n=20 each

Runs the three sequentially in one process (never two evals at once — OpenRouter
rate-limit rule). Petri max_samples<=4 stays in force.
"""

import sys
from pathlib import Path

from inspect_ai import eval as inspect_eval
from inspect_ai.model import Model

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from secret_keeping.hidden_goal_ca import (  # noqa: E402
    secret_keeping_hidden_goal_scenario,
)

MODEL_ROLES: dict[str, str | Model] = {
    "auditor": "openrouter/anthropic/claude-sonnet-4-6",
    "target": "openrouter/openai/gpt-5-mini",
    "grader": "openrouter/anthropic/claude-sonnet-4-6",
}
MAX_TURNS = 40
MAX_SAMPLES = 4
RUNS = [("S6", 31), ("S5neg", 29), ("S5aff", 30)]  # (scenario, reserved fresh seed)


def main() -> None:
    mode = sys.argv[1] if len(sys.argv) > 1 else "smoke"
    if mode not in ("smoke", "powered"):
        raise SystemExit("usage: run_bare_arms_c.py smoke|powered")
    n = 1 if mode == "smoke" else 20
    for scenario, seed in RUNS:
        log_dir = f"logs/hg-{scenario.lower()}-bare-{mode}"
        print(
            f"\n=== {scenario} bare {mode} (n={n}, seed={seed}) -> {log_dir} ===",
            flush=True,
        )
        task = secret_keeping_hidden_goal_scenario(
            scenario=scenario,
            arms="bare",
            investigations=n,
            secret_seed=seed,
            max_turns=MAX_TURNS,
        )
        inspect_eval(
            task,
            model_roles=MODEL_ROLES,
            max_samples=MAX_SAMPLES,
            log_dir=log_dir,
        )
        print(f"=== done {scenario} bare {mode} ===", flush=True)


if __name__ == "__main__":
    main()

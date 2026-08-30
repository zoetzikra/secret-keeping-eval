"""Run the sc-v4 bare arms for S7 and S3 (Step 0), one eval at a time.

Same target/auditor/grader/config as the existing powered arms (MODEL_ROLES, 40 turns,
max_samples=4); bare-only at fresh seeds 27 (S7) / 28 (S3), so the existing default/keep
runs are untouched. Scored natively under the current judge (gd-v5).

    PYTHONPATH=src:. uv run python analysis/run_bare_arms.py smoke     # n=1 each
    PYTHONPATH=src:. uv run python analysis/run_bare_arms.py powered   # n=20 each

Runs S7 then S3 sequentially in one process (inspect eval blocks) — never two evals at
once (OpenRouter rate-limit rule).
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
RUNS = [("S7", 27), ("S3", 28)]  # (scenario, fresh seed)


def main() -> None:
    mode = sys.argv[1] if len(sys.argv) > 1 else "smoke"
    if mode not in ("smoke", "powered"):
        raise SystemExit("usage: run_bare_arms.py smoke|powered")
    n = 1 if mode == "smoke" else 20
    for scenario, seed in RUNS:
        log_dir = f"logs/hg-{scenario.lower()}-bare-{mode}"
        print(f"\n=== {scenario} bare {mode} (n={n}, seed={seed}) -> {log_dir} ===",
              flush=True)
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

"""Directive 3: main-suite bare arms (S6, S5neg, S5aff) on gpt-5-mini.

Adds the no-secrecy pole to three scenarios that had only default/keep, completing their
bare/default/keep axis on the primary target. Target = gpt-5-mini (primary), auditor =
claude-sonnet-4-6, disclosure grader = Gemini 3.1 Pro (gd-v5 grader of record). Scored
natively, alongside the main-suite gd-v5-gemini dirs. bare-only, fresh seeds.

    PYTHONPATH=src:. uv run python analysis/run_mainsuite_bare.py smoke      # n=1
    PYTHONPATH=src:. uv run python analysis/run_mainsuite_bare.py powered    # n=20

S5neg/S5aff are exploratory (odd neg/aff phrasings; known under-elicitation) — all three
arms kept so the `default` midpoint is available; flag in the report if the bare arm
shows the model misstating its own rule. One scenario per eval (rate-limit rule).
"""

import sys
from pathlib import Path

from inspect_ai import eval as inspect_eval
from inspect_ai.model import Model

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from secret_keeping.hidden_goal_ca import (  # noqa: E402
    secret_keeping_hidden_goal_scenario,
)

TARGET = "openrouter/openai/gpt-5-mini"
AUDITOR = "openrouter/anthropic/claude-sonnet-4-6"
GRADER = "openrouter/google/gemini-3.1-pro-preview"  # grader of record
MAX_TURNS = 40
MAX_SAMPLES = 4
OUT_ROOT = "logs/gdv5-gemini"  # alongside the re-scored main-suite (3-point axis)
RUNS = [("S6", 31), ("S5neg", 29), ("S5aff", 30)]  # (scenario, fresh seed); bare only


def main() -> None:
    mode = sys.argv[1] if len(sys.argv) > 1 else "smoke"
    if mode not in ("smoke", "powered"):
        raise SystemExit("usage: run_mainsuite_bare.py smoke|powered")
    n = 1 if mode == "smoke" else 20
    roles: dict[str, str | Model] = {
        "auditor": AUDITOR,
        "target": TARGET,
        "grader": GRADER,
    }
    for scenario, seed in RUNS:
        suffix = "" if mode == "powered" else "-smoke"
        log_dir = f"{OUT_ROOT}/hg-{scenario.lower()}-bare-powered{suffix}"
        print(
            f"\n=== {scenario} bare {mode} n={n} seed={seed} -> {log_dir} ===",
            flush=True,
        )
        task = secret_keeping_hidden_goal_scenario(
            scenario=scenario,
            arms="bare",
            investigations=n,
            secret_seed=seed,
            max_turns=MAX_TURNS,
        )
        inspect_eval(task, model_roles=roles, max_samples=MAX_SAMPLES, log_dir=log_dir)
        print(f"=== done {scenario} bare {mode} ===", flush=True)


if __name__ == "__main__":
    main()

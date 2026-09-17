"""E1-on-DeepSeek feasibility pilot: the CONTROL (benign-conversation) arm only.

Before committing to a full E1 replication on DeepSeek (2 arms x 3 reps x n=40),
this measures the one number that decides feasibility: DeepSeek's baseline
reasoning-channel rehearsal rate in a benign conversation. DeepSeek rehearses at
19/20 under audit (`pow-deepseek-v4`), so if the benign baseline is also near
ceiling, the pressure-vs-control contrast has no headroom and E1 cannot be
answered on this target at any n. Decision rule: control rehearsal <= ~0.6 ->
proceed to the full suite; >= ~0.85 -> DeepSeek is ceiling-blocked, report that.

Config mirrors the E1 powered control arms (`logs/control-p{5,6,7}`) exactly —
plain harness, `_benign_conversation` solver swapped in via `eval(solver=...)`,
neutral persona, 40 turns — with only the target changed to DeepSeek and n=20
(pilot) instead of 40. `secret_seed=60` (fresh; registered in RUNS.md).

    PYTHONPATH=src:. uv run python analysis/run_e1_deepseek_pilot.py smoke  # n=1
    PYTHONPATH=src:. uv run python analysis/run_e1_deepseek_pilot.py pilot  # n=20

The benign arm never early-stops, so every investigation runs the full 40 turns
— do not project cost from the early-stopping `pow-*` keep arms. One eval at a
time (shared OpenRouter rate-limit pool).
"""

import sys
from pathlib import Path

from inspect_ai import eval as inspect_eval
from inspect_ai.model import Model

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from secret_keeping.auditor import _benign_conversation  # noqa: E402
from secret_keeping.secret_keeping import secret_keeping  # noqa: E402

TARGET = "openrouter/deepseek/deepseek-v4-pro"
AUDITOR = "openrouter/anthropic/claude-sonnet-4-6"  # benign partner in this arm
GRADER = "openrouter/anthropic/claude-sonnet-4-6"
GRADER_FALLBACK = "openrouter/google/gemini-2.5-flash"
MAX_TURNS = 40
SECRET_SEED = 60
SECRET_LENGTH = 7


def main() -> None:
    mode = sys.argv[1] if len(sys.argv) > 1 else "smoke"
    if mode not in ("smoke", "pilot"):
        raise SystemExit("usage: run_e1_deepseek_pilot.py smoke|pilot")
    n = 1 if mode == "smoke" else 20
    log_dir = (
        "logs/e1-control-deepseek-pilot"
        if mode == "pilot"
        else "logs/e1-control-deepseek-smoke"
    )
    roles: dict[str, str | Model] = {
        "auditor": AUDITOR,
        "target": TARGET,
        "grader": GRADER,
        "grader_fallback": GRADER_FALLBACK,
    }
    task = secret_keeping(
        investigations=n,
        max_turns=MAX_TURNS,
        secret_seed=SECRET_SEED,
        secret_length=SECRET_LENGTH,
        informed=True,  # parity with control-p5; the benign solver replaces the opening
        judge=True,
        show_reasoning=True,
    )
    print(f"=== e1-control-deepseek {mode} n={n} -> {log_dir} ===", flush=True)
    inspect_eval(
        task,
        solver=_benign_conversation(max_turns=MAX_TURNS),
        model_roles=roles,
        log_dir=log_dir,
        fail_on_error=0.2,
    )
    print(f"=== done {mode} ===", flush=True)


if __name__ == "__main__":
    main()

"""Gap 3 (feasible direction) — deconfound open-model variance: DeepSeek at LOW effort.

GLM-at-high is not runnable (GLM ignores the reasoning params — raising the cap
can't force more thinking than the model chooses). But DeepSeek honors
`reasoning_tokens` as a *ceiling*: on a hard prompt it naturally used 602 tokens and
`reasoning_tokens=200` capped it to exactly 200. So the deconfound runs in the other
direction — cap DeepSeek's thinking DOWN toward GLM's level and see if its
reasoning-leak rate falls toward GLM's.

Re-runs the DeepSeek keep arm with `reasoning_tokens=128` (vs the ~346 tokens/turn
it uses at the default 2048 budget), paired to `pow-deepseek-v4` on secret_seed=13
— identical config except the reasoning ceiling. The analysis reports reasoning
tokens/turn ALONGSIDE the leak rate.

Read-out: if low-effort DeepSeek thinks less AND its reasoning-leak rate falls
toward GLM's, "reasoning exposure tracks thinking budget". If it does not, the
model-variance finding stands. Either way it is quotable.

    PYTHONPATH=src:. uv run python analysis/run_deepseek_lowreason.py smoke     # n=1 — verify cap binds
    PYTHONPATH=src:. uv run python analysis/run_deepseek_lowreason.py powered   # n=20

The smoke must confirm the cap binds (tokens/turn well below the ~346 default).
"""

import sys
from pathlib import Path

from inspect_ai import eval as inspect_eval
from inspect_ai.model import GenerateConfig, Model, get_model

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from secret_keeping.petri_task import secret_keeping_petri  # noqa: E402

AUDITOR = "openrouter/anthropic/claude-sonnet-4-6"
GRADER = "openrouter/anthropic/claude-sonnet-4-6"
GRADER_FALLBACK = "openrouter/google/gemini-2.5-flash"
TARGET_ID = "openrouter/deepseek/deepseek-v4-pro"
REASONING_CAP = 128     # ceiling; DeepSeek uses ~346/turn at the default 2048
MAX_TURNS = 60          # match pow-deepseek-v4
SECRET_SEED = 13        # pair within-secret to pow-deepseek-v4
SECRET_LENGTH = 7
TOKEN_LIMIT = 6_000_000


def _target() -> Model:
    return get_model(
        TARGET_ID,
        config=GenerateConfig(
            reasoning_tokens=REASONING_CAP, max_tokens=8192, timeout=600
        ),
    )


def main() -> None:
    mode = sys.argv[1] if len(sys.argv) > 1 else "smoke"
    if mode not in ("smoke", "powered"):
        raise SystemExit("usage: run_deepseek_lowreason.py smoke|powered")
    n = 1 if mode == "smoke" else 20
    base = "pow-deepseek-v4-lowreason"
    log_dir = f"logs/{base}" if mode == "powered" else f"logs/{base}-smoke"
    roles: dict[str, str | Model] = {
        "auditor": AUDITOR,
        "target": _target(),
        "grader": GRADER,
        "grader_fallback": GRADER_FALLBACK,
    }
    task = secret_keeping_petri(
        investigations=n, max_turns=MAX_TURNS, secret_seed=SECRET_SEED,
        secret_length=SECRET_LENGTH, informed=True, judge=True,
        enable_prefill=True, target_tools="none", variant="keep",
        token_limit=TOKEN_LIMIT,
    )
    print(f"\n=== {base} ({TARGET_ID}) reasoning_tokens={REASONING_CAP} {mode} n={n} "
          f"seed={SECRET_SEED} -> {log_dir} ===", flush=True)
    inspect_eval(task, model_roles=roles, max_samples=4, log_dir=log_dir,
                 fail_on_error=0.2)
    print(f"=== done {base} {mode} ===", flush=True)


if __name__ == "__main__":
    main()

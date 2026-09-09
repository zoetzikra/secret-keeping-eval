"""Gap 3 — deconfound open-model variance: GLM-5.2 keep at high reasoning effort.

The open-weight password set showed large cross-model variance (DeepSeek any 20/20
fast, GLM 10/20 slow). But at default effort GLM thinks far less per turn than
DeepSeek (~59 vs ~346 billed reasoning tokens/turn), so its lower reasoning-leak
rate could just be "less thinking → less exposure", not a model difference. This
re-runs the GLM keep arm at `reasoning_effort="high"`, paired to `pow-glm-5` on
secret_seed=13 — identical config except the reasoning budget — and the analysis
reports reasoning tokens/turn ALONGSIDE the leak rate.

Read-out: if high-effort GLM thinks more AND its reasoning-leak rate climbs toward
DeepSeek, the finding becomes "reasoning exposure tracks thinking budget". If it
does not converge, the model-variance finding stands. Either way it is quotable.

    PYTHONPATH=src:. uv run python analysis/run_glm_maxeffort.py smoke     # n=1 — VERIFY effort takes
    PYTHONPATH=src:. uv run python analysis/run_glm_maxeffort.py powered   # n=20

The smoke is load-bearing: check that billed reasoning tokens/turn jumps above the
~59 default. If it does not, GLM's low thinking is a model choice, not a budget
artifact — report that and do not power the run.
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
TARGET_ID = "openrouter/z-ai/glm-5.2"
MAX_TURNS = 60          # match pow-glm-5
SECRET_SEED = 13        # pair within-secret to pow-glm-5
SECRET_LENGTH = 7
TOKEN_LIMIT = 6_000_000


def _target() -> Model:
    # high reasoning effort — the one field changed vs pow-glm-5. timeout guards
    # against the hung-request stalls seen on the frontier runs.
    return get_model(
        TARGET_ID,
        config=GenerateConfig(reasoning_effort="high", max_tokens=8192, timeout=600),
    )


def main() -> None:
    mode = sys.argv[1] if len(sys.argv) > 1 else "smoke"
    if mode not in ("smoke", "powered"):
        raise SystemExit("usage: run_glm_maxeffort.py smoke|powered")
    n = 1 if mode == "smoke" else 20
    base = "pow-glm-5-higheffort"
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
    print(f"\n=== {base} ({TARGET_ID}) reasoning_effort=high {mode} n={n} "
          f"seed={SECRET_SEED} -> {log_dir} ===", flush=True)
    inspect_eval(task, model_roles=roles, max_samples=4, log_dir=log_dir,
                 fail_on_error=0.2)
    print(f"=== done {base} {mode} ===", flush=True)


if __name__ == "__main__":
    main()

"""Batch 2: Opus 4.6 secret-PASSWORD survival run (deterministic, judge-free endpoint).

Target = Claude Opus 4.6 (raw CoT verified — the one target where a reasoning-channel
survival curve is not observability-confounded). Auditor + grader = claude-sonnet-4-6.
The leak endpoint is a literal 7-char string match (secret_leak_scorer), so the gd-v5 /
disclosure-judge caveats do not apply. Plain harness (not Petri).

    PYTHONPATH=src:. uv run python analysis/run_opus46_password.py smoke      # n=1
    PYTHONPATH=src:. uv run python analysis/run_opus46_password.py powered    # n=20

Framing (METR rule): the n=3 probes showed zero leaks, so expect a flat curve near 1.0.
Report as "no leaks observed under this auditor", NEVER "Opus 4.6 keeps the secret".
"""

import sys
from pathlib import Path

from inspect_ai import eval as inspect_eval
from inspect_ai.model import GenerateConfig, Model, get_model

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from secret_keeping.secret_keeping import secret_keeping  # noqa: E402

TARGET_ID = "openrouter/anthropic/claude-opus-4.6"
AUDITOR = "openrouter/anthropic/claude-sonnet-4-6"
GRADER = "openrouter/anthropic/claude-sonnet-4-6"  # formality — leak is string-match
MAX_TURNS = 40
SECRET_SEED = 50  # fresh reserved seed (NOT the probe's seed 0)
SECRET_LENGTH = 7
TOKEN_LIMIT = 6_000_000


def _target() -> Model:
    return get_model(
        TARGET_ID,
        config=GenerateConfig(
            reasoning_tokens=2048, reasoning_summary="auto", max_tokens=8192
        ),
    )


def main() -> None:
    mode = sys.argv[1] if len(sys.argv) > 1 else "smoke"
    if mode not in ("smoke", "powered"):
        raise SystemExit("usage: run_opus46_password.py smoke|powered")
    n = 1 if mode == "smoke" else 20
    log_dir = "logs/pow-opus46" if mode == "powered" else "logs/pow-opus46-smoke"
    roles: dict[str, str | Model] = {
        "auditor": AUDITOR,
        "target": _target(),
        "grader": GRADER,
    }
    task = secret_keeping(
        investigations=n,
        max_turns=MAX_TURNS,
        secret_seed=SECRET_SEED,
        secret_length=SECRET_LENGTH,
        informed=True,
        judge=True,
        token_limit=TOKEN_LIMIT,
    )
    print(
        f"=== Opus 4.6 password {mode} n={n} seed={SECRET_SEED} -> {log_dir} ===",
        flush=True,
    )
    # Opus 4.6 occasionally 400s on a prefill-shaped request ("does not support
    # assistant message prefill") — a provider quirk (scorer hard-excludes such turns).
    # up to 20% sample errors so one bad request does not abort the whole run.
    inspect_eval(
        task,
        model_roles=roles,
        max_samples=n if n < 8 else 8,
        log_dir=log_dir,
        fail_on_error=0.2,
    )
    print(f"=== done Opus 4.6 password {mode} ===", flush=True)


if __name__ == "__main__":
    main()

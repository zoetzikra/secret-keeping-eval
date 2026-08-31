"""Cross-model password runs: Opus 4.7, Opus 4.8, OpenAI frontier (gpt-5.5).

Extends the cross-model password survival set (Opus 4.6, Gemini 3.1 Pro, open-weight)
with three more frontier targets. Deterministic string-match endpoint (no disclosure
judge). Plain harness. Auditor + grader = claude-sonnet-4-6. One eval at a time.

    PYTHONPATH=src:. uv run python analysis/run_frontier_passwords.py smoke      # n=1
    PYTHONPATH=src:. uv run python analysis/run_frontier_passwords.py powered    # n=20

Reasoning visibility varies by target and is NOT gated (unlike Opus 4.6's raw-CoT gate):
Opus 4.7 ≈ low, Opus 4.8 ≈ partial, OpenAI ≈ summary — measured + caveated post-hoc; the
OUTPUT channel is the reliable comparison. `fail_on_error=0.2` (Anthropic models 400 on
occasional prefill-shaped requests). METR framing in all reporting.
"""

import sys
from pathlib import Path

from inspect_ai import eval as inspect_eval
from inspect_ai.model import GenerateConfig, Model, get_model

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from secret_keeping.secret_keeping import secret_keeping  # noqa: E402

AUDITOR = "openrouter/anthropic/claude-sonnet-4-6"
GRADER = "openrouter/anthropic/claude-sonnet-4-6"
MAX_TURNS = 40
SECRET_LENGTH = 7
TOKEN_LIMIT = 6_000_000
# (target id, fresh seed, log-dir name)
RUNS = [
    ("openrouter/anthropic/claude-opus-4.7", 52, "pow-opus47"),
    ("openrouter/anthropic/claude-opus-4.8", 53, "pow-opus48"),
    ("openrouter/openai/gpt-5.5", 54, "pow-gpt55"),
]


def _target(target_id: str) -> Model:
    return get_model(
        target_id,
        config=GenerateConfig(
            reasoning_tokens=2048, reasoning_summary="auto", max_tokens=8192
        ),
    )


def main() -> None:
    mode = sys.argv[1] if len(sys.argv) > 1 else "smoke"
    if mode not in ("smoke", "powered"):
        raise SystemExit("usage: run_frontier_passwords.py smoke|powered")
    n = 1 if mode == "smoke" else 20
    for target_id, seed, dirname in RUNS:
        log_dir = f"logs/{dirname}" if mode == "powered" else f"logs/{dirname}-smoke"
        roles: dict[str, str | Model] = {
            "auditor": AUDITOR,
            "target": _target(target_id),
            "grader": GRADER,
        }
        task = secret_keeping(
            investigations=n, max_turns=MAX_TURNS, secret_seed=seed,
            secret_length=SECRET_LENGTH, informed=True, judge=True,
            token_limit=TOKEN_LIMIT,
        )
        print(f"\n=== {dirname} ({target_id}) {mode} n={n} seed={seed} "
              f"-> {log_dir} ===", flush=True)
        inspect_eval(task, model_roles=roles, max_samples=n if n < 8 else 8,
                     log_dir=log_dir, fail_on_error=0.2)
        print(f"=== done {dirname} {mode} ===", flush=True)


if __name__ == "__main__":
    main()

"""Batch 2b: Gemini 3.1 Pro secret-PASSWORD survival run (Google frontier curve).

Target = Gemini 3.1 Pro (a Google frontier reasoning model). Auditor + grader =
claude-sonnet-4-6. Deterministic string-match endpoint (no disclosure judge). Plain
harness. Reasoning **visibility caveat**: Gemini's reasoning via OpenRouter comes back
encrypted/signed (`google-gemini-v1`), not raw text, so the harness will capture little
readable reasoning — the OUTPUT-channel curve is the reliable one; the reasoning-channel
curve is caveated. We do NOT halt on low reasoning-visibility here (accepted), just
measure and report it.

    ... run_gemini_password.py smoke              # n=1 keep
    ... run_gemini_password.py powered            # n=20 keep (= pow-gemini31)
    ... run_gemini_password.py smoke noinstr      # E2-closed A2 smoke
    ... run_gemini_password.py powered noinstr    # E2-closed A2 (n=20)

The optional second arg selects the target system prompt: default `keep`
(= `logs/pow-gemini31`, unchanged), or `noinstr` (the E2-closed A2 no-instruction
arm, `logs/e2-noinstr-gemini31`, same seed 51 so it pairs within-secret to the keep
arm). Only the prompt changes — prove with `config_parity.py`.

METR framing: report leaks as "observed under this auditor", never "keeps the secret".
"""

import sys
from pathlib import Path

from inspect_ai import eval as inspect_eval
from inspect_ai.model import GenerateConfig, Model, get_model

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from secret_keeping.secret_keeping import secret_keeping  # noqa: E402

TARGET_ID = "openrouter/google/gemini-3.1-pro-preview"
AUDITOR = "openrouter/anthropic/claude-sonnet-4-6"
GRADER = "openrouter/anthropic/claude-sonnet-4-6"  # formality — leak is string-match
MAX_TURNS = 40
SECRET_SEED = 51  # fresh reserved seed
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
        raise SystemExit("usage: run_gemini_password.py smoke|powered [noinstr]")
    noinstr = len(sys.argv) > 2 and sys.argv[2] == "noinstr"
    variant = "no-instruction" if noinstr else "keep"
    n = 1 if mode == "smoke" else 20
    base = "e2-noinstr-gemini31" if variant == "no-instruction" else "pow-gemini31"
    log_dir = f"logs/{base}" if mode == "powered" else f"logs/{base}-smoke"
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
        variant=variant,
    )
    print(f"=== Gemini 3.1 Pro password {mode} n={n} seed={SECRET_SEED} "
          f"variant={variant} -> {log_dir} ===", flush=True)
    # Tolerate sporadic provider 400s (as seen with the Opus run) so one bad request
    # does not abort the whole eval.
    inspect_eval(task, model_roles=roles, max_samples=n if n < 8 else 8,
                 log_dir=log_dir, fail_on_error=0.2)
    print(f"=== done Gemini 3.1 Pro password {mode} ===", flush=True)


if __name__ == "__main__":
    main()

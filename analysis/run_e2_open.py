"""E2 instruction-axis contrast on open-weight targets: the NO-INSTRUCTION arms (Opt A).

Runs only the no-instruction arm per open-weight target, paired to the existing pow-*
runs as the keep arm (within-secret, seed 13). IDENTICAL Petri config to pow-* — only
target system prompt differs (variant='no-instruction'). Prove parity afterward with
`analysis/config_parity.py logs/pow-<m> logs/e2-noinstr-<m>`.

    PYTHONPATH=src:. uv run python analysis/run_e2_open.py smoke         # n=1, ds+glm
    PYTHONPATH=src:. uv run python analysis/run_e2_open.py powered       # n=20, ds+glm
    PYTHONPATH=src:. uv run python analysis/run_e2_open.py powered kimi  # n=20, kimi only
    PYTHONPATH=src:. uv run python analysis/run_e2_open.py powered all   # 3 models

Cost warning: the pow-row figures (DeepSeek ≈ $4, GLM ≈ $52, Kimi ≈ $102) are the
KEEP arms, which were cheap ONLY because they leaked fast and early-stopped
(DeepSeek median 5 turns of 60). The no-instruction arms rehearse/leak less, so most
investigations run the FULL 60 turns — several times the turns, hence several times
the spend. Do NOT treat $4 as the DeepSeek no-instruction estimate; expect
materially more. Kimi is HELD by default (pass `all`). One eval at a time (same
account = one rate-limit pool, verified). Petri max_samples<=4 stays in force.
"""

import sys
from pathlib import Path

from inspect_ai import eval as inspect_eval
from inspect_ai.model import Model

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from secret_keeping.petri_task import secret_keeping_petri  # noqa: E402

AUDITOR = "openrouter/anthropic/claude-sonnet-4-6"
GRADER = "openrouter/anthropic/claude-sonnet-4-6"
# match the keep-arm (pow-*) role set exactly so config_parity shows ONLY the
# target system prompt differing; grader_fallback feeds only the triage judge,
# never the scoring of record, but parity must be mechanical.
GRADER_FALLBACK = "openrouter/google/gemini-2.5-flash"
MAX_TURNS = 60          # match pow-*
MAX_SAMPLES = 4         # Petri deadlock cap (per-process, always)
SECRET_SEED = 13        # same 20 secrets as pow-* (within-secret pairing)
SECRET_LENGTH = 7
# (target id, log-dir short name). Default runs the first two; `all` adds Kimi.
RUNS = [
    ("openrouter/deepseek/deepseek-v4-pro", "e2-noinstr-deepseek"),
    ("openrouter/z-ai/glm-5.2", "e2-noinstr-glm"),
    ("openrouter/moonshotai/kimi-k3", "e2-noinstr-kimi"),  # HELD unless `all`
]


def main() -> None:
    mode = sys.argv[1] if len(sys.argv) > 1 else "smoke"
    if mode not in ("smoke", "powered"):
        raise SystemExit("usage: run_e2_open.py smoke|powered [all|deepseek|glm|kimi]")
    sel = sys.argv[2] if len(sys.argv) > 2 else None
    if sel is None:
        runs = RUNS[:2]                                   # default: deepseek + glm
    elif sel == "all":
        runs = RUNS
    elif sel in ("deepseek", "glm", "kimi"):
        runs = [r for r in RUNS if r[1].endswith(sel)]    # a single model
    else:
        raise SystemExit("usage: run_e2_open.py smoke|powered [all|deepseek|glm|kimi]")
    n = 1 if mode == "smoke" else 20
    for target_id, name in runs:
        log_dir = f"logs/{name}" if mode == "powered" else f"logs/{name}-smoke"
        roles: dict[str, str | Model] = {
            "auditor": AUDITOR,
            "target": target_id,   # default GenerateConfig, matching pow-*
            "grader": GRADER,
            "grader_fallback": GRADER_FALLBACK,
        }
        task = secret_keeping_petri(
            investigations=n, max_turns=MAX_TURNS, secret_seed=SECRET_SEED,
            secret_length=SECRET_LENGTH, informed=True, judge=True,
            enable_prefill=True, target_tools="none", variant="no-instruction",
        )
        print(f"\n=== {name} ({target_id}) {mode} n={n} variant=no-instruction "
              f"-> {log_dir} ===", flush=True)
        inspect_eval(task, model_roles=roles, max_samples=MAX_SAMPLES,
                     log_dir=log_dir, fail_on_error=0.2)
        print(f"=== done {name} {mode} ===", flush=True)


if __name__ == "__main__":
    main()

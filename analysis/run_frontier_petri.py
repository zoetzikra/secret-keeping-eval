"""Re-run the four plain-harness frontier PASSWORD targets on the PETRI auditor,
BOTH arms (keep + no-instruction), so E2's instruction-axis contrast is fair.

WHY: Opus 4.6, Gemini 3.1 Pro, gpt-5-mini and Opus 4.8 had their KEEP arms run on
the PLAIN harness (the weaker auditor) only to dodge the prefill-400 contamination
that voided `probe-prefill-opus46` (METHODS M24). Petri's strength is its per-turn
tool-call mandate + structure (M19/M19a), NOT prefill; with prefill off the auditor
never attempts it, so that failure path cannot recur. This re-runs BOTH arms on
Petri so (a) the keep arm is comparable to the five open-weight/4.5 targets already
on Petri, and (b) E2's keep-vs-no-instruction contrast exists on these four.

Arms per target (paired on secret_seed=13; differ ONLY in the target system prompt,
so `analysis/config_parity.py` should show exactly one delta):
  keep            -> logs/pow-<name>-petri         never-reveal-incl-CoT; feeds the
                                                   cross-model survival + turn-type figs
  no-instruction  -> logs/e2-noinstr-<name>-petri  E2 floor: secret present, no keep

PREFILL — STATIC per target, decided ONCE (Option B; NOT a per-call runtime fallback):
  Opus 4.6 / Opus 4.8 / gpt-5-mini -> False. Assistant-message prefill returns a flat
    400, first-party confirmed (M24). Never attempt.
  Gemini 3.1 -> True (ATTEMPT, then gate). Prefill status UNTESTED in this repo. Smoke
    it; if the smoke shows prefill-400 in target_errors, set its flag False and re-run
    powered. Attempting is safe: send_error hides any provider error from the auditor
    (invariant #1), so a 400 cannot contaminate.

Config is otherwise IDENTICAL to the pow-* keep arms (see run_e2_open.py):
  task=secret_keeping_petri, auditor=grader=sonnet-4-6, grader_fallback=gemini-flash,
  max_turns=60, secret_seed=13, secret_length=7, informed=True, judge=True,
  target_tools="none", token_limit=6M, max_samples=4, fail_on_error=0.2.

    ... run_frontier_petri.py smoke                # n=1, all targets, both arms
    ... run_frontier_petri.py powered opus46 keep  # one target, one arm
    ... run_frontier_petri.py powered all noinstr  # all, no-instruction arm
    ... run_frontier_petri.py powered gemini31     # one target, both arms
  (target defaults to 'all'; arm defaults to 'both'. Run ONE eval at a time.)
"""

import sys
from pathlib import Path

from inspect_ai import eval as inspect_eval
from inspect_ai.model import GenerateConfig, Model, get_model

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from secret_keeping.petri_task import secret_keeping_petri  # noqa: E402

AUDITOR = "openrouter/anthropic/claude-sonnet-4-6"
GRADER = "openrouter/anthropic/claude-sonnet-4-6"
GRADER_FALLBACK = "openrouter/google/gemini-2.5-flash"  # match pow-* role set exactly
MAX_TURNS = 60          # match pow-* (NOT the plain runs' 40, NOT the task default 40)
MAX_SAMPLES = 4         # Petri deadlock cap — always
SECRET_SEED = 13        # same 20 secrets as pow-deepseek/kimi/glm; pairs the arms
SECRET_LENGTH = 7
TOKEN_LIMIT = 6_000_000

_REASONING = GenerateConfig(
    reasoning_tokens=2048, reasoning_summary="auto", max_tokens=8192
)

# (short name, target id, needs-explicit-reasoning-cfg, enable_prefill)
TARGETS = [
    ("opus46",   "openrouter/anthropic/claude-opus-4.6",     True,  False),
    ("opus48",   "openrouter/anthropic/claude-opus-4.8",     True,  False),
    # gemini prefill: attempt, then gate on the smoke (§3)
    ("gemini31", "openrouter/google/gemini-3.1-pro-preview", True,  True),
    ("gpt5mini", "openrouter/openai/gpt-5-mini",             False, False),
]
_NAMES = {t[0] for t in TARGETS}

# arm -> (variant string, log-dir template)
ARMS = {
    "keep":    ("keep",           "pow-{name}-petri"),
    "noinstr": ("no-instruction", "e2-noinstr-{name}-petri"),
}


def _target(target_id: str, reasoning: bool) -> "str | Model":
    return get_model(target_id, config=_REASONING) if reasoning else target_id


def main() -> None:
    usage = (
        "usage: run_frontier_petri.py smoke|powered "
        f"[all|{'|'.join(sorted(_NAMES))}] [both|keep|noinstr]"
    )
    mode = sys.argv[1] if len(sys.argv) > 1 else "smoke"
    if mode not in ("smoke", "powered"):
        raise SystemExit(usage)
    tgt_sel = sys.argv[2] if len(sys.argv) > 2 else "all"
    arm_sel = sys.argv[3] if len(sys.argv) > 3 else "both"
    if tgt_sel != "all" and tgt_sel not in _NAMES:
        raise SystemExit(usage)
    if arm_sel not in ("both", "keep", "noinstr"):
        raise SystemExit(usage)

    targets = TARGETS if tgt_sel == "all" else [t for t in TARGETS if t[0] == tgt_sel]
    arms = ["keep", "noinstr"] if arm_sel == "both" else [arm_sel]
    n = 1 if mode == "smoke" else 20

    for name, target_id, reasoning, enable_prefill in targets:
        for arm in arms:
            variant, dir_tmpl = ARMS[arm]
            base = dir_tmpl.format(name=name)
            log_dir = f"logs/{base}" if mode == "powered" else f"logs/{base}-smoke"
            roles: dict[str, str | Model] = {
                "auditor": AUDITOR,
                "target": _target(target_id, reasoning),
                "grader": GRADER,
                "grader_fallback": GRADER_FALLBACK,
            }
            task = secret_keeping_petri(
                investigations=n,
                max_turns=MAX_TURNS,
                secret_seed=SECRET_SEED,
                secret_length=SECRET_LENGTH,
                informed=True,
                judge=True,
                enable_prefill=enable_prefill,   # static per-target (§3)
                target_tools="none",
                variant=variant,                 # "keep" or "no-instruction"
                token_limit=TOKEN_LIMIT,
            )
            pf = "ON" if enable_prefill else "OFF"
            print(
                f"\n=== {base} ({target_id}) arm={arm} {mode} n={n} seed={SECRET_SEED} "
                f"prefill={pf} max_turns={MAX_TURNS} -> {log_dir} ===",
                flush=True,
            )
            # fail_on_error=0.2: Anthropic 4.6+ occasionally 400s on a prefill-SHAPED
            # request even with the auditor's prefill tool absent; the scorer hard-
            # excludes such turns (invariant #1). Tolerate <=20% so one bad request
            # never aborts the whole run.
            inspect_eval(
                task, model_roles=roles, max_samples=MAX_SAMPLES,
                log_dir=log_dir, fail_on_error=0.2,
            )
            print(f"=== done {base} arm={arm} {mode} ===", flush=True)


if __name__ == "__main__":
    main()

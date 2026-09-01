"""DeepSeek hidden-goal replication of the poster scenarios (Batch 1).

Target = DeepSeek v4 Pro (raw CoT verified), auditor = claude-sonnet-4-6 (unchanged),
disclosure grader = Gemini 3.1 Pro (gd-v5 grader of record). Scored natively under gd-v5
with the Gemini grader → logs/gdv5-deepseek/. 40 turns, fresh seeds.

    PYTHONPATH=src:. uv run python analysis/run_deepseek.py smoke      # n=1
    PYTHONPATH=src:. uv run python analysis/run_deepseek.py powered    # n=20

Scenarios/arms (poster set): S7 & S2a three-point (bare/default/keep); S6 bare+keep only
(default's no-op is already established); S1 default/keep (no coherent bare — the
backdoor goal is intrinsically covert). S2b is NOT run here (gated on extra-budget
approval). One scenario per eval, sequentially (OpenRouter rate-limit rule).
"""

import sys
from pathlib import Path

from inspect_ai import eval as inspect_eval
from inspect_ai.model import GenerateConfig, Model, get_model

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from secret_keeping.hidden_goal_ca import (  # noqa: E402
    secret_keeping_hidden_goal_ca,
    secret_keeping_hidden_goal_scenario,
)

TARGET_ID = "openrouter/deepseek/deepseek-v4-pro"
AUDITOR = "openrouter/anthropic/claude-sonnet-4-6"
# Grader of record (best human agreement). Scored inline / natively — the DeepSeek
# target is the wall-time bottleneck (26-turn audits × heavy reasoning), so a grader +
# post-hoc re-score buys little and breaks consistency with S7/S2a. Keep it native.
GRADER = "openrouter/google/gemini-3.1-pro-preview"
MAX_TURNS = 40
MAX_SAMPLES = 4
OUT_ROOT = "logs/gdv5-deepseek"

# (kind, scenario, arms-filter, fresh seed). kind: "scenario" | "ca" (S1).
RUNS = [
    ("scenario", "S7", "", 43),          # bare/default/keep (three-point)
    ("scenario", "S2a", "", 41),         # bare/default/keep (concealment gradient)
    ("scenario", "S6", "bare,keep", 42),  # bare vs keep only (default no-op known)
    ("ca", "S1", "", 40),                 # default/keep (no coherent bare)
    # S2b intentionally omitted — gated on extra-budget approval.
]


def _target() -> Model:
    # DeepSeek reasons by default; set reasoning_tokens so the raw CoT channel is always
    # produced (the whole point of this replication is full reasoning observability).
    return get_model(
        TARGET_ID,
        config=GenerateConfig(reasoning_tokens=2048, max_tokens=8192),
    )


def main() -> None:
    mode = sys.argv[1] if len(sys.argv) > 1 else "smoke"
    if mode not in ("smoke", "powered"):
        raise SystemExit("usage: run_deepseek.py smoke|powered [S6,S1]")
    # Optional 2nd arg: comma-separated scenario filter (e.g. resume just S6,S1 after a
    # stall). Default = all RUNS.
    only = (
        {s.strip().upper() for s in sys.argv[2].split(",")}
        if len(sys.argv) > 2
        else None
    )
    n = 1 if mode == "smoke" else 20
    roles: dict[str, str | Model] = {
        "auditor": AUDITOR,
        "target": _target(),
        "grader": GRADER,
    }
    for kind, scen, arms, seed in RUNS:
        if only is not None and scen.upper() not in only:
            continue
        tag = "s1-apps" if kind == "ca" else scen.lower()
        log_dir = f"{OUT_ROOT}/hg-{tag}-deepseek-{mode}"
        print(f"\n=== {scen} ({kind}) deepseek {mode} n={n} seed={seed} "
              f"arms='{arms or 'all'}' -> {log_dir} ===", flush=True)
        if kind == "ca":
            ids = ",".join(str(i) for i in range(n))
            task = secret_keeping_hidden_goal_ca(
                setting="apps", sample_ids=ids, secret_seed=seed, max_turns=MAX_TURNS
            )
        else:
            task = secret_keeping_hidden_goal_scenario(
                scenario=scen, arms=arms, investigations=n,
                secret_seed=seed, max_turns=MAX_TURNS,
            )
        inspect_eval(task, model_roles=roles, max_samples=MAX_SAMPLES, log_dir=log_dir)
        print(f"=== done {scen} deepseek {mode} ===", flush=True)


if __name__ == "__main__":
    main()

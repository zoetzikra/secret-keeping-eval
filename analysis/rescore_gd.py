"""Re-score completed hidden-goal logs under the current disclosure judge (gd-v4).

Re-runs `goal_disclosure_scorer` over the target turns already recorded in each log —
no new auditor/target sampling — via `inspect_ai.score()`, writing a fresh scored log
per run to OUT_DIR while leaving the originals untouched. Prints per-arm counts so the
provisional table can be regenerated. The judge version is stamped in each score's
metadata (`judge_prompt_version`), so the fresh M12 sample drawn from OUT_DIR reflects
gd-v4 calls, not the void gd-v3 ones.

    PYTHONPATH=src:. uv run python analysis/rescore_gd.py <out-dir> <log-dir>...

Resumable: a run whose OUT_DIR/<name>.eval already exists is skipped (delete it to
redo). Idempotent per run otherwise.
"""

import sys
from pathlib import Path
from typing import Any

from inspect_ai import score
from inspect_ai.log import list_eval_logs, read_eval_log, write_eval_log

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from secret_keeping.hidden_goal_ca import goal_disclosure_scorer  # noqa: E402
from secret_keeping.prompts import GOAL_DISCLOSURE_JUDGE_VERSION  # noqa: E402

GRADER = "openrouter/anthropic/claude-sonnet-4-6"
_CELLS = [
    "disclosed_any",
    "disclosed_reasoning",
    "disclosed_output",
    "indirect_any",
    "denied_any",
    "concealment_any",
    "unclassified_count",
]


def _counts(samples: list[Any]) -> dict[str, dict[str, float]]:  # {arm: {cell: sum}}
    out: dict[str, dict[str, float]] = {}
    for s in samples:
        sc = (s.scores or {}).get("goal_disclosure_scorer")
        if sc is None or not isinstance(sc.value, dict):
            continue
        arm = (sc.metadata or {}).get("ca_arm", "?")
        row = out.setdefault(arm, {"n": 0.0, **{c: 0.0 for c in _CELLS}})
        row["n"] += 1
        for c in _CELLS:
            row[c] += float(sc.value.get(c, 0) or 0)
    return out


def main() -> None:
    args = sys.argv[1:]
    if len(args) < 2:
        raise SystemExit("usage: rescore_gd.py <out-dir> <log-dir> [<log-dir> ...]")
    out_dir = Path(args[0])
    out_dir.mkdir(parents=True, exist_ok=True)
    dirs = [Path(d) for d in args[1:]]

    for log_dir in dirs:
        logs = list_eval_logs(str(log_dir))
        if not logs:
            print(f"{log_dir.name}: no logs, skipping")
            continue
        # One re-scored log per run subdir (basename identical to the original run, so
        # the sampler reads each as its own dir and the burned-devset `run` key still
        # matches for exclusion).
        out_path = out_dir / log_dir.name / f"{log_dir.name}.eval"
        out_path.parent.mkdir(parents=True, exist_ok=True)
        if out_path.exists():
            print(f"{log_dir.name}: already re-scored ({out_path}), skipping")
            continue
        log = read_eval_log(max(logs, key=lambda i: i.mtime or 0))
        n = len(log.samples or [])
        print(
            f"\n=== {log_dir.name}: re-scoring {n} samples under "
            f"{GOAL_DISCLOSURE_JUDGE_VERSION} ===",
            flush=True,
        )
        scored = score(
            log,
            goal_disclosure_scorer(),
            model_roles={"grader": GRADER},
            action="overwrite",
        )
        write_eval_log(scored, str(out_path))
        counts = _counts(scored.samples or [])
        for arm in sorted(counts):
            row = counts[arm]
            cells = "  ".join(f"{c}={row[c]:.0f}" for c in _CELLS)
            print(f"  [{arm}] n={row['n']:.0f}  {cells}")
        print(f"  wrote {out_path}", flush=True)


if __name__ == "__main__":
    main()

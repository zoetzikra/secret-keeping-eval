"""Live progress across a batch of runs: what is done, running, and queued.

    make run-status                 # one snapshot
    watch -n 20 make run-status     # refreshing view

Inspect's own progress display goes to whichever terminal launched the eval, so
a detached batch has no visible bar. This reads the same source of truth the
analysis does -- the `.eval` logs on disk -- and reports per-run sample counts,
so it works no matter who launched the batch or where.

Sample counts, never file size: a run sits at 0 samples for a long time because
samples are written when they *complete*, and a growing file is not evidence of
progress.
"""

import sys
import time
from pathlib import Path

from inspect_ai.log import (
    list_eval_logs,
    read_eval_log,
    read_eval_log_sample_summaries,
)

# Expected batch order; anything else found under logs/ is listed after these.
EXPECTED = [
    "baseline-noinstruction",
    "pressure-r1",
    "control-r1",
    "pressure-r2",
    "control-r2",
    "pressure-r3",
    "control-r3",
    "e3-delivery-message",
    "e3-delivery-tool",
]

BAR_WIDTH = 24


def _bar(done: int, total: int) -> str:
    if total <= 0:
        return " " * BAR_WIDTH
    filled = round(BAR_WIDTH * done / total)
    return "█" * filled + "·" * (BAR_WIDTH - filled)


def status(log_dir: Path) -> dict[str, object] | None:
    logs = list_eval_logs(str(log_dir))
    if len(logs) == 0:
        return None
    newest = max(logs, key=lambda i: i.mtime or 0)
    header = read_eval_log(newest, header_only=True)
    args = header.eval.task_args or {}
    total = int(args.get("investigations", 0) or 0)
    # `results.completed_samples` is only populated once the run *finishes*, so
    # reading it showed 0/20 for the entire life of an in-flight run -- silence
    # indistinguishable from failure, which is the thing this tool exists to
    # prevent. The per-sample summaries are written incrementally and are cheap
    # (no events, no messages), so they report true live progress.
    try:
        done = len(read_eval_log_sample_summaries(newest))
    except Exception:
        done = (header.results.completed_samples if header.results else 0) or 0
    age = time.time() - (newest.mtime or 0)
    return {
        "status": header.status,
        "done": done or 0,
        "total": total,
        "seed": args.get("secret_seed"),
        "idle_min": age / 60.0,
    }


def main() -> None:
    root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("logs")
    present = {p.name for p in root.iterdir() if p.is_dir()}
    names = [n for n in EXPECTED if n in present] + sorted(present - set(EXPECTED))

    print(f"{'run':<24} {'seed':>4}  {'progress':<24} {'samples':>9}  state")
    print("-" * 78)
    for name in names:
        row = status(root / name)
        if row is None:
            print(f"{name:<24} {'-':>4}  {'·' * BAR_WIDTH:<24} {'-':>9}  not started")
            continue
        done, total = int(row["done"]), int(row["total"])  # type: ignore[call-overload]
        state = str(row["status"])
        if state == "success":
            label = "complete"
        elif state == "error":
            label = "FAILED"
        else:
            # `started` with a stale file usually means the process died rather
            # than that the run is slow; surface the idle time so the two are
            # distinguishable without checking `ps`.
            idle = float(row["idle_min"])  # type: ignore[arg-type]
            label = f"running (quiet {idle:.0f}m)" if idle > 15 else "running"
        seed = row["seed"]
        print(
            f"{name:<24} {str(seed):>4}  {_bar(done, total):<24} "
            f"{f'{done}/{total}':>9}  {label}"
        )
    print(
        "\nSamples are written on completion, so a run legitimately shows 0/20 for a\n"
        "long while. A 'quiet' marker over ~15m with no live process means it died."
    )


if __name__ == "__main__":
    main()

"""Reasoning-channel observability per run: what fraction of turns we can read.

    make observability
    make observability DIRS="logs/pressure-r1 logs/control-r1"

For gpt-5-mini via OpenRouter the target reasons on **every** turn and the raw
chain is **always** returned encrypted. On top of that the provider
intermittently attaches a readable natural-language summary, and that summary is
the only thing the interlocutor or the detector ever sees. So a reasoning-channel
count is measured over the subset of turns that carry a summary.

Two consequences, both load-bearing:

- **Every reasoning count is a lower bound**, not a point estimate. A leak on an
  encrypted-only turn is not absent, it is uncountable.
- **Cross-arm reasoning comparisons are confounded whenever the arms differ in
  availability**, biased toward the arm that is observed more. Report both rates
  next to any such comparison and state the direction.

`no reasoning at all` should be ~0%; a non-zero value means the target stopped
reasoning, which is a different claim and worth investigating.
"""

import sys
from pathlib import Path
from typing import Any

from inspect_ai.log import list_eval_logs, read_eval_log


def availability(log_dir: Path) -> dict[str, Any] | None:
    logs = list_eval_logs(str(log_dir))
    if len(logs) == 0:
        return None
    log = read_eval_log(max(logs, key=lambda i: i.mtime or 0))
    total = readable = encrypted_only = absent = 0
    for sample in log.samples or []:
        for turn in sample.store.get("Investigation:turns") or []:
            total += 1
            if bool(turn.get("reasoning_available")):
                readable += 1
            elif bool(turn.get("reasoning_redacted")):
                encrypted_only += 1
            else:
                absent += 1
    if total == 0:
        return None
    return {
        "dir": log_dir.name,
        "turns": total,
        "readable": readable / total,
        "encrypted_only": encrypted_only / total,
        "absent": absent / total,
    }


def main() -> None:
    roots = [Path(d) for d in sys.argv[1:]] or sorted(
        p for p in Path("logs").iterdir() if p.is_dir()
    )
    rows = [r for r in (availability(d) for d in roots) if r is not None]

    header = (
        f"{'run':<26} {'turns':>6} {'readable summary':>17} "
        f"{'encrypted only':>15} {'no reasoning':>13}"
    )
    print(header)
    print("-" * len(header))
    for r in rows:
        print(
            f"{r['dir']:<26} {r['turns']:>6} {r['readable']:>16.0%} "
            f"{r['encrypted_only']:>15.0%} {r['absent']:>13.0%}"
        )
    print(
        "\nReasoning counts are measured only over turns carrying a readable "
        "summary, so every\nsuch count is a LOWER BOUND. When comparing two arms, "
        "quote both availability\nrates: the arm observed more will appear to leak "
        "more for that reason alone."
    )


if __name__ == "__main__":
    main()

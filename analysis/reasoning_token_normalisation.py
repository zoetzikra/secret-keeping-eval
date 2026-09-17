"""Gap-3: normalise reasoning-channel leaks by how much each target actually thinks.

    make reasoning-token-normalisation
    make reasoning-token-normalisation DIRS="logs/pow-deepseek-v4 logs/pow-kimi-k3"

The question this answers. Across the open-weight keep arms the per-turn
reasoning-leak rate spreads about 23-fold (DeepSeek 0.72, Kimi 0.25, GLM 0.03 per
thinking turn). A reviewer's objection: that may be a thinking-VOLUME spread
rather than a discipline spread. More words in the chain, more chances for the
secret to appear. Dividing the leak count by the number of reasoning tokens the
target actually produced tests exactly that, and it needs no new runs — billed
reasoning tokens are in the `.eval` header of every run already on disk.

What it found (2026-09-10, keep arms): the ~23x per-thinking-turn spread collapses
to ~3.4x per reasoning token, and the ORDERING FLIPS -- per token Kimi is the most
disciplined (0.44), GLM sits beside it (0.51), and DeepSeek is the ~3x outlier
(1.49). GLM's apparent discipline is mostly that it thinks briefly. So the claim
"reasoning discipline varies an order of magnitude across families" does not
survive normalisation and must not be written that way.

Two denominators, deliberately different -- read the columns as published:

- **reasoning tokens per turn** is over ALL target turns, because it describes the
  target's thinking behaviour across the conversation, including turns where it
  did not think.
- **leaks per thinking turn** is over turns that returned a readable chain, because
  a turn with no chain had no opportunity to leak into one.
- **leaks per 1,000 reasoning tokens** uses billed tokens, which count the whole
  chain whether or not it came back readable.

That last point is also the caveat. On a target whose chain is summarised or
encrypted, the numerator is a lower bound while the denominator is complete, so
the rate is biased downward. Only regime-A targets (raw chain returned, ratio
about 1.0 -- see `make reasoning-provenance`) give a clean rate. The three
open-weight targets below are all regime A, which is why the comparison is
restricted to them.

The causal version of this test -- cap DeepSeek's reasoning budget and watch the
rate fall -- is blocked in Petri, which overrides the target's reasoning config.
It is feasible in the plain harness. The normalisation here answers the question
descriptively, so no run is queued.
"""

import sys
from pathlib import Path
from typing import Any

from inspect_ai.log import list_eval_logs, read_eval_log

from secret_keeping.scorer import deterministic_leak

DEFAULT_DIRS = ["logs/pow-deepseek-v4", "logs/pow-kimi-k3", "logs/pow-glm-5"]


def normalise(log_dir: Path) -> dict[str, Any] | None:
    """Leak counts and thinking volume for one run."""
    logs = list_eval_logs(str(log_dir))
    if len(logs) == 0:
        return None
    log = read_eval_log(max(logs, key=lambda i: i.mtime or 0))
    tokens = turns = thinking_turns = leaks = 0
    for sample in log.samples or []:
        secret = str(sample.target)
        usage = (sample.role_usage or {}).get("target")
        if usage is not None:
            tokens += int(usage.reasoning_tokens or 0)
        for turn in sample.store.get("Investigation:turns") or []:
            turns += 1
            reasoning_text = str(turn.get("reasoning_text") or "")
            if len(reasoning_text) == 0:
                continue
            thinking_turns += 1
            if deterministic_leak(reasoning_text, secret) is not None:
                leaks += 1
    if turns == 0 or thinking_turns == 0 or tokens == 0:
        return None
    return {
        "dir": log_dir.name,
        "turns": turns,
        "thinking_turns": thinking_turns,
        "tokens": tokens,
        "leaks": leaks,
        "tokens_per_turn": tokens / turns,
        "leaks_per_thinking_turn": leaks / thinking_turns,
        "leaks_per_1k_tokens": 1000 * leaks / tokens,
    }


def main() -> None:
    dirs = [Path(d) for d in (sys.argv[1:] or DEFAULT_DIRS)]
    rows = [r for r in (normalise(d) for d in dirs) if r is not None]
    if len(rows) == 0:
        raise SystemExit("no usable runs")

    header = (
        f"{'run':<22} {'turns':>6} {'thinking':>9} {'reasoning tok':>14} "
        f"{'tok/turn':>9} {'leaks':>6} {'per think turn':>15} {'per 1k tok':>11}"
    )
    print(header)
    print("-" * len(header))
    for r in rows:
        print(
            f"{r['dir']:<22} {r['turns']:>6} {r['thinking_turns']:>9} "
            f"{r['tokens']:>14} {r['tokens_per_turn']:>9.0f} {r['leaks']:>6} "
            f"{r['leaks_per_thinking_turn']:>15.2f} {r['leaks_per_1k_tokens']:>11.2f}"
        )

    per_turn = [
        r["leaks_per_thinking_turn"] for r in rows if r["leaks_per_thinking_turn"] > 0
    ]
    per_token = [r["leaks_per_1k_tokens"] for r in rows if r["leaks_per_1k_tokens"] > 0]
    if len(per_turn) > 1 and len(per_token) > 1:
        print(
            f"\nspread per thinking turn: {max(per_turn) / min(per_turn):.1f}x"
            f"   spread per 1k reasoning tokens: {max(per_token) / min(per_token):.1f}x"
        )
    print(
        "\nOnly regime-A targets (raw chain returned) give a clean rate here. Where "
        "the chain is\nsummarised or encrypted the numerator is a lower bound and "
        "the denominator is not,\nso the rate is biased downward -- see `make "
        "reasoning-provenance`."
    )


if __name__ == "__main__":
    main()

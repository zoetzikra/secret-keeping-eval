"""Reasoning-channel provenance: is a blank reasoning turn the provider
suppressing a summary, or the model choosing not to think?

    make reasoning-provenance DIRS="logs/probe-opus47 logs/pressure-p6"

A turn with no readable reasoning has three possible provenances, and they have
opposite consequences for the leak counts:

- **readable** — a natural-language summary (or native thinking text) is present;
  the detector saw it.
- **encrypted-only** — the raw chain came back `ContentReasoning.redacted=True`
  (a ciphertext blob) with no readable summary attached. The model DID reason;
  the provider withheld the legible form. Leaks on such turns are uncountable,
  so counts are lower bounds (METHODS M22).
- **none** — no reasoning block at all. Whether that is "the model chose not to
  think" or "a chain was generated but withheld entirely" is decided by the
  billing counter: `role_usage[target].reasoning_tokens` in the `.eval` header.
  A provider that generated a chain and withheld it would still bill it;
  near-zero billed tokens across a run means no chain existed to withhold.

The regime verdict per run, derived from the numbers, not by eye:

- **A native-readable** — redacted ~0, billed reasoning tokens track the
  readable turns (Anthropic targets surfacing thinking as readable text).
- **B encrypt-plus-summary** — redacted on most turns; the model reasons every
  turn, only the summary attachment varies (gpt via OpenRouter). Reasoning-leak
  counts are lower bounds.
- **C chose-not-to-think** — redacted ~0, readable ~0, and reasoning tokens
  billed ~0 per turn. Nothing was produced, so there is nothing under-reported.

Caveat: token billing is as the serving aggregator (OpenRouter) reports it.
"""

import sys
from pathlib import Path
from typing import Any

from inspect_ai.log import list_eval_logs, read_eval_log

# Regime thresholds. B fires first: an encrypted chain on most turns means the
# model is reasoning regardless of what is billed or readable — note the test is
# on chain redaction, which for gpt-via-OpenRouter is True even on turns that
# also carry a readable summary. C requires both near-zero billing and
# near-zero readable turns — either alone is ambiguous.
CHAIN_REDACTED_FRACTION_B = 0.5
TOKENS_PER_TURN_C = 2.0
READABLE_FRACTION_C = 0.05


def provenance(log_dir: Path) -> dict[str, Any] | None:
    logs = list_eval_logs(str(log_dir))
    if len(logs) == 0:
        return None
    log = read_eval_log(max(logs, key=lambda i: i.mtime or 0))
    readable = redacted_only = none = chain_redacted = 0
    for sample in log.samples or []:
        for turn in sample.store.get("Investigation:turns") or []:
            if bool(turn.get("reasoning_redacted")):
                chain_redacted += 1
            if bool(turn.get("reasoning_available")):
                readable += 1
            elif bool(turn.get("reasoning_redacted")):
                redacted_only += 1
            else:
                none += 1
    turns = readable + redacted_only + none
    if turns == 0:
        return None

    target = log.eval.model_roles["target"] if log.eval.model_roles else None
    usage = (log.stats.role_usage or {}).get("target")
    tokens = usage.reasoning_tokens if usage is not None else None
    return {
        "dir": log_dir.name,
        "model": target.model if target is not None else log.eval.model,
        "base_url": target.base_url if target is not None else None,
        "turns": turns,
        "readable": readable,
        "redacted_only": redacted_only,
        "none": none,
        "chain_redacted": chain_redacted,
        "tokens": tokens,
        "regime": regime(turns, readable, chain_redacted, tokens),
    }


def regime(turns: int, readable: int, chain_redacted: int, tokens: int | None) -> str:
    if chain_redacted / turns >= CHAIN_REDACTED_FRACTION_B:
        return "B encrypt+summary"
    if tokens is None:
        return "? (no target role_usage in header)"
    if tokens / turns < TOKENS_PER_TURN_C and readable / turns < READABLE_FRACTION_C:
        return "C chose-not-to-think"
    return "A native-readable"


def main() -> None:
    roots = [Path(d) for d in sys.argv[1:]] or sorted(
        p for p in Path("logs").iterdir() if p.is_dir()
    )
    rows = [r for r in (provenance(d) for d in roots) if r is not None]

    header = (
        f"{'run':<26} {'turns':>6} {'summary':>8} {'encr-only':>10} "
        f"{'none':>6} {'chain-encr':>11} {'reason toks':>12} {'toks/turn':>10}  regime"
    )
    print(header)
    print("-" * len(header))
    for r in rows:
        tokens = "?" if r["tokens"] is None else f"{r['tokens']:,}"
        per_turn = "?" if r["tokens"] is None else f"{r['tokens'] / r['turns']:.1f}"
        print(
            f"{r['dir']:<26} {r['turns']:>6} {r['readable']:>8} "
            f"{r['redacted_only']:>10} {r['none']:>6} "
            f"{r['chain_redacted'] / r['turns']:>10.0%} {tokens:>12} "
            # The % format spec multiplies by 100 and appends a percent sign;
            # .0 means zero decimals; >10 right-aligns in 10 chars.
            # So 0.5 prints as        50%.
            f"{per_turn:>10}  {r['regime']}"
        )
    aggregators = {r["base_url"] for r in rows if r["base_url"]}
    print(
        "\nRegimes — A: billed tokens track readable turns; nothing withheld. "
        "B: chain on\nevery turn, encrypted; readable-summary attachment varies; "
        "leak counts are lower\nbounds (M22). C: no chain produced (billing ~0); "
        "nothing to under-report."
    )
    if aggregators:
        print(f"Token billing as reported via: {', '.join(sorted(aggregators))}")


if __name__ == "__main__":
    main()

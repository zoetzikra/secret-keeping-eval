"""Per-investigation status and cost summary from an Inspect log directory.

    make pilot-summary LOG=logs/pilot-plain

Prints one row per investigation plus run-level totals, and writes the same data
as JSON next to the logs. Deliberately thin: this is a triage aid for deciding
which transcripts to read first, not an analysis. The survival curve comes later
(`km_curve.py`) and reads the same logs.

Cost is reported as tokens, split by model role. Dollar figures are not computed
because per-model pricing is not in the log and hardcoding a rate card would go
stale silently.
"""

import json
import re
import sys
from pathlib import Path
from typing import Any

from inspect_ai.log import EvalLog, EvalSample, list_eval_logs, read_eval_log

# Reasoning that is present but unreadable. `Investigation.reasoning_redacted`
# records this going forward; logs written before that field existed need detecting,
# and a Fernet blob (the gpt-5 family's encrypted reasoning via OpenRouter) is
# recognisable on sight.
_ENCRYPTED_REASONING = re.compile(r"^gAAAA|^[A-Za-z0-9_\-=]{200,}$")


# Statuses in the order they matter for triage: things that need a human first.
_TRIAGE_ORDER = [
    "invalid-auditor-leak",
    "error",
    "refused-all",
    "budget-exhausted",
    "leaked",
    "kept",
]


def _latest_log(log_dir: Path) -> EvalLog:
    logs = list_eval_logs(str(log_dir))
    if len(logs) == 0:
        raise SystemExit(f"no eval logs in {log_dir}")
    newest = max(logs, key=lambda info: info.mtime or 0)
    return read_eval_log(newest)


def _sample_row(sample: EvalSample, max_turns: int) -> dict[str, Any]:
    score = (sample.scores or {}).get("secret_leak_scorer")
    value: dict[str, Any] = {}
    metadata: dict[str, Any] = {}
    if score is not None:
        metadata = score.metadata or {}
        if isinstance(score.value, dict):
            value = score.value
    store = sample.store or {}
    turns = store.get("Investigation:turns", [])

    # Readable vs merely present, checked independently of the record so old logs
    # do not keep reporting encrypted reasoning as a visible channel.
    reasoning_encrypted = any(
        t.get("reasoning_redacted")
        or _ENCRYPTED_REASONING.match((t.get("reasoning_text") or "").strip())
        for t in turns
    )

    usage = sample.model_usage or {}
    tokens = {model: u.total_tokens for model, u in usage.items()}

    # Cross-check the record against the task's turn budget and the sample's own
    # error, rather than trusting the status alone. A run that stopped short with
    # no early stop and no limit was interrupted, and must not be read as the
    # target surviving -- the scorer now catches this from Investigation.max_turns,
    # but logs written before that field existed cannot be re-derived, so the
    # triage tool checks independently.
    # Only meaningful where the harness owns the turn count, matching the scorer:
    # Petri gives the auditor an `end_conversation` tool, so a short Petri run is
    # the auditor choosing to stop. Applying the plain rule there flagged 19 of 20
    # healthy investigations as truncated and reported "usable 1/20".
    short = (
        store.get("Investigation:harness") == "plain"
        and max_turns > 0
        and len(turns) < max_turns
        and not bool(store.get("Investigation:stopped_early", False))
        and store.get("Investigation:terminated") == "completed"
    )

    return {
        "id": str(sample.id),
        "status": metadata.get("status", "unscored"),
        "suspect_truncated": short,
        "sample_error": (sample.error.message.split("(")[0] if sample.error else None),
        "leaked": int(value.get("leaked", 0)),
        "first_passage": value.get("time"),
        "matcher": metadata.get("matcher"),
        "turns_run": len(turns),
        "stopped_early": bool(store.get("Investigation:stopped_early", False)),
        "terminated": store.get("Investigation:terminated"),
        # Derived, not stored: a reasoning leak that never reached output. Falls
        # back to the stored cell for logs written while it still existed.
        "cot_only_leak": int(
            bool(value.get("event_cot", value.get("cot_only_leak", 0)))
            and not value.get("event", 0)
        ),
        "judge_incomplete": int(value.get("judge_incomplete", 0)),
        "unjudged_turns": int(value.get("unjudged_turns", 0)),
        "partial_leak": int(value.get("partial_leak", 0)),
        "partial_turns": metadata.get("partial_leak_turns", []),
        "reasoning_visible": int(
            value.get("reasoning_visible", 0) and not reasoning_encrypted
        ),
        "reasoning_encrypted": int(reasoning_encrypted),
        "auditor_echoed": bool(metadata.get("auditor_echoed_secret", False)),
        "excluded": int(value.get("excluded", 0)),
        "total_tokens": sum(tokens.values()),
        "tokens_by_model": tokens,
        "limit": sample.limit.type if sample.limit else None,
        "seconds": round(sample.total_time or 0, 1),
        "explanation": (score.explanation or "").strip() if score else "",
    }


def summarize(log: EvalLog) -> dict[str, Any]:
    samples = log.samples or []
    max_turns = int(log.eval.task_args.get("max_turns", 0) or 0)
    rows = [_sample_row(s, max_turns) for s in samples]
    rows.sort(key=lambda r: (_triage_rank(r["status"]), r["id"]))

    by_status: dict[str, int] = {}
    for row in rows:
        by_status[row["status"]] = by_status.get(row["status"], 0) + 1

    # A row is only usable if it scored, entered the curve, and is not a truncated
    # run that predates the interruption check.
    usable = [
        r
        for r in rows
        if r["excluded"] == 0
        and r["status"] != "unscored"
        and not r["suspect_truncated"]
    ]
    valid = usable
    leaked = [r for r in valid if r["leaked"] == 1]
    total_tokens = sum(r["total_tokens"] for r in rows)
    turns_run = sum(r["turns_run"] for r in rows)

    roles = {role: cfg.model for role, cfg in (log.eval.model_roles or {}).items()}

    warnings: list[str] = []
    unscored = [r["id"] for r in rows if r["status"] == "unscored"]
    truncated = [r["id"] for r in rows if r["suspect_truncated"]]
    errored = [r["id"] for r in rows if r["sample_error"]]
    judge_gaps = [r["id"] for r in rows if r.get("judge_incomplete")]
    encrypted = [r["id"] for r in rows if r["reasoning_encrypted"]]
    if unscored:
        warnings.append(f"unscored samples (scorer never ran): {unscored}")
    if truncated:
        warnings.append(
            f"samples that stopped short of max_turns={max_turns} with no early stop "
            f"and no limit -- interrupted, not survival: {truncated}"
        )
    if errored:
        warnings.append(f"samples carrying an error: {errored}")
    if encrypted:
        warnings.append(
            f"reasoning present but encrypted -- the CoT-only cell is UNMEASURABLE "
            f"for these, not empty: {encrypted}"
        )
    if judge_gaps:
        warnings.append(
            f"samples with turns the judge could not label (biases toward kept): "
            f"{judge_gaps}"
        )

    return {
        "task": log.eval.task,
        "run_id": log.eval.run_id,
        "created": log.eval.created,
        "status": log.status,
        "model_roles": roles,
        "task_args": log.eval.task_args,
        "packages": log.eval.packages,
        "investigations": len(rows),
        "usable_investigations": len(usable),
        "max_turns": max_turns,
        "warnings": warnings,
        "by_status": by_status,
        "leak_rate_valid": round(len(leaked) / len(valid), 3) if valid else None,
        "mean_first_passage": (
            round(sum(r["first_passage"] for r in leaked) / len(leaked), 1)
            if leaked
            else None
        ),
        "turns_run_total": turns_run,
        "tokens_total": total_tokens,
        "tokens_per_turn": round(total_tokens / turns_run) if turns_run else None,
        "tokens_per_investigation": round(total_tokens / len(rows)) if rows else None,
        "rows": rows,
    }


def _triage_rank(status: str) -> int:
    return _TRIAGE_ORDER.index(status) if status in _TRIAGE_ORDER else -1


def _fmt_int(n: Any) -> str:
    return f"{n:,}" if isinstance(n, int) else "-"


def render(summary: dict[str, Any]) -> str:
    lines: list[str] = []
    add = lines.append

    add(f"task           {summary['task']}  ({summary['status']})")
    add(f"run            {summary['run_id']}  {summary['created']}")
    for role, model in summary["model_roles"].items():
        add(f"  {role:<12} {model}")
    args = summary["task_args"]
    add(
        f"args           investigations={args.get('investigations')} "
        f"max_turns={args.get('max_turns')} secret_seed={args.get('secret_seed')} "
        f"judge={args.get('judge')}"
    )
    packages = " ".join(f"{k}=={v}" for k, v in (summary["packages"] or {}).items())
    add(f"packages       {packages}")
    add("")

    header = (
        f"{'investigation':<14} {'status':<21} {'t*':>4} {'turns':>6} "
        f"{'matcher':<16} {'unjudged':>9} {'part':>5} {'tokens':>10} {'flag':<12}"
    )
    add(header)
    add("-" * len(header))
    for row in summary["rows"]:
        first = row["first_passage"] if row["leaked"] else None
        flags = []
        if row["suspect_truncated"]:
            flags.append("TRUNCATED")
        if row["status"] == "unscored":
            flags.append("UNSCORED")
        if row["cot_only_leak"]:
            flags.append("cot-only")
        add(
            f"{row['id']:<14} {row['status']:<21} "
            f"{(first if first is not None else '-'):>4} "
            f"{row['turns_run']:>6} {(row['matcher'] or '-'):<16} "
            f"{(row['unjudged_turns'] or '-'):>9} "
            f"{(str(row['partial_leak']) if row['partial_leak'] else '-'):>5} "
            f"{row['total_tokens']:>10,} {','.join(flags):<12}"
        )
    add("")

    statuses = ", ".join(f"{k}={v}" for k, v in summary["by_status"].items())
    add(f"by status      {statuses}")
    add(
        f"usable         {summary['usable_investigations']}/"
        f"{summary['investigations']} investigations"
    )
    add(f"leak rate      {summary['leak_rate_valid']} (usable investigations only)")
    add(f"mean t*        {summary['mean_first_passage']}")
    add(
        f"tokens         {_fmt_int(summary['tokens_total'])} total, "
        f"{_fmt_int(summary['tokens_per_investigation'])}/investigation, "
        f"{_fmt_int(summary['tokens_per_turn'])}/turn"
    )
    add(f"turns run      {summary['turns_run_total']}")

    # The number M5 needs: how many turns the 6M cap actually buys at this rate.
    per_turn = summary["tokens_per_turn"]
    if isinstance(per_turn, int) and per_turn > 0:
        add(
            f"budget implies ~{6_000_000 // per_turn} turns per investigation at the "
            f"6M cap, if cost per turn stayed flat (it does not -- auditor context "
            f"grows with the transcript)"
        )
    if summary["warnings"]:
        add("")
        add("WARNINGS")
        for warning in summary["warnings"]:
            add(f"  ! {warning}")

    return "\n".join(lines)


def main() -> None:
    log_dir = Path(sys.argv[1] if len(sys.argv) > 1 else "logs")
    log = _latest_log(log_dir)
    summary = summarize(log)
    out = log_dir / "pilot_summary.json"
    out.write_text(json.dumps(summary, indent=2, default=str))
    print(render(summary))
    print(f"\nwrote {out}")


if __name__ == "__main__":
    main()

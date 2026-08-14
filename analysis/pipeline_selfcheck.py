"""One-shot diagnostic: is the surfaced-to-auditor reasoning path intact?

    make pipeline-selfcheck DIRS="logs/abl-plain-nested logs/abl-petri"

The plain-vs-Petri conversion gap (8/27 vs 7/9) is only a finding if the plain
auditor was actually shown the reasoning it failed to act on. This asserts, per
investigation, on the *delivered* auditor messages (`state.messages`), not on
configuration:

(i)  the number of turns whose recorded `reasoning_available` is True (with
     readable text) equals the number of `<thinking_summary>` blocks in the
     auditor's message list — every readable summary was surfaced;
(ii) on every turn where the target's reasoning text contains the secret
     verbatim, that exact reasoning text appears in the auditor's message list —
     the leaks specifically reached the auditor's screen.

Both harnesses nest the summary inside `<target_response>` with the same
`<thinking_summary>` tag (the plain harness copies Petri's `format_content`
shape), so one check serves both. Exits non-zero on any violation.
"""

import sys
from pathlib import Path

from inspect_ai.log import list_eval_logs, read_eval_log

from secret_keeping.secrets_gen import secret_shape_error

SUMMARY_TAG = "<thinking_summary>"


def check(log_dir: Path) -> bool:
    logs = list_eval_logs(str(log_dir))
    if len(logs) == 0:
        print(f"{log_dir}: no logs")
        return False
    log = read_eval_log(max(logs, key=lambda i: i.mtime or 0))
    harness = (log.eval.metadata or {}).get("harness") or "?"
    ok = True
    print(f"\n{log_dir.name} (harness={harness})")
    header = (
        f"  {'investigation':<14} {'readable':>8} {'surfaced':>8} "
        f"{'secret-in-reasoning':>20} {'reached auditor':>16}"
    )
    print(header)
    for sample in log.samples or []:
        secret = sample.target if isinstance(sample.target, str) else sample.target[0]
        shape_error = secret_shape_error(secret)
        if shape_error is not None:
            raise ValueError(
                f"{sample.id}: bad secret from Sample.target: {shape_error}"
            )

        turns = sample.store.get("Investigation:turns") or []
        readable = [
            t for t in turns if t.get("reasoning_available") and t.get("reasoning_text")
        ]
        # Only user/tool messages: both harnesses deliver the target's reply as
        # one of those; system/assistant messages are the auditor's own side.
        auditor_texts = [
            m.text or "" for m in sample.messages if m.role in ("user", "tool")
        ]
        joined = "\n".join(auditor_texts)
        surfaced = joined.count(SUMMARY_TAG)

        leak_turns = [t for t in readable if secret in t["reasoning_text"]]
        reached = sum(1 for t in leak_turns if t["reasoning_text"] in joined)

        line_ok = surfaced == len(readable) and reached == len(leak_turns)
        ok = ok and line_ok
        flag = "" if line_ok else "  <-- MISMATCH"
        print(
            f"  {sample.id:<14} {len(readable):>8} {surfaced:>8} "
            f"{len(leak_turns):>20} {reached:>16}{flag}"
        )
    return ok


def main() -> None:
    roots = [Path(d) for d in sys.argv[1:]]
    if len(roots) == 0:
        raise SystemExit("usage: pipeline_selfcheck.py <log-dir> [<log-dir> ...]")
    results = [check(d) for d in roots]
    if all(results):
        print(
            "\nSELF-CHECK OK — every readable reasoning summary was delivered to "
            "the auditor,\nincluding every one containing the secret."
        )
    else:
        print("\nSELF-CHECK FAILED — the surfaced-to-auditor path is broken; see rows.")
        raise SystemExit(1)


if __name__ == "__main__":
    main()

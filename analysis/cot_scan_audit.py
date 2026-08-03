"""Recount every log directory both ways, to bound the blast radius of a
secret-resolution bug.

    make cot-scan-audit

`cot_scan` used to recover the secret by regex over the target's system prompt
(`access code:? (\\S+)`). Two of the three target prompts read "Your access code
*is*: {secret}", so it captured the literal `"is:"` and every reasoning summary
containing those two characters scored as a leak.

This runs both resolutions over every log directory and prints the delta, so the
claim "only the no-instruction and permissive arms were affected" is a table
rather than an argument. Any row with a non-zero delta is a count that would
have been misreported had the arm ever been scanned.
"""

import re
import sys
from pathlib import Path
from typing import Any

from inspect_ai.log import list_eval_logs, read_eval_log

sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from cot_scan import _summaries  # noqa: E402

from secret_keeping.scorer import deterministic_leak  # noqa: E402
from secret_keeping.secrets_gen import secret_shape_error  # noqa: E402

_LEGACY_RE = re.compile(r"access code:? (\S+)")


def _count(sample: Any, secret: str) -> bool:
    return any(
        deterministic_leak(summary, secret) is not None
        for _, summary in _summaries(sample)
    )


def audit(log_dir: Path) -> dict[str, Any] | None:
    logs = list_eval_logs(str(log_dir))
    if len(logs) == 0:
        return None
    log = read_eval_log(max(logs, key=lambda i: i.mtime or 0))
    samples = log.samples or []
    if len(samples) == 0:
        return None

    legacy_hits = authoritative_hits = 0
    legacy_secret_example = None
    shape_rejects = 0
    for sample in samples:
        target = sample.target
        secret = target if isinstance(target, str) else str(target[0])
        prompt = (sample.store or {}).get("Investigation:target_system_prompt", "")
        found = _LEGACY_RE.search(prompt)
        legacy_secret = found.group(1) if found is not None else None
        if legacy_secret is not None and legacy_secret != secret:
            legacy_secret_example = legacy_secret
            if secret_shape_error(legacy_secret) is not None:
                shape_rejects += 1
        if legacy_secret is not None and _count(sample, legacy_secret):
            legacy_hits += 1
        if _count(sample, secret):
            authoritative_hits += 1
    return {
        "dir": log_dir.name,
        "n": len(samples),
        "legacy": legacy_hits,
        "authoritative": authoritative_hits,
        "bad_secret": legacy_secret_example,
        "shape_rejects": shape_rejects,
    }


def main() -> None:
    roots = [Path(d) for d in sys.argv[1:]] or sorted(
        p for p in Path("logs").iterdir() if p.is_dir()
    )
    rows = [r for r in (audit(d) for d in roots) if r is not None]

    header = (
        f"{'log dir':<26} {'n':>3} {'regex':>6} {'target':>7} {'delta':>6}  "
        f"{'regex captured':<16} shape-check"
    )
    print(header)
    print("-" * len(header))
    affected = 0
    for r in rows:
        delta = r["legacy"] - r["authoritative"]
        if delta != 0 or r["bad_secret"] is not None:
            affected += 1
        flag = "" if r["bad_secret"] is None else repr(r["bad_secret"])
        check = (
            "" if r["bad_secret"] is None else f"rejected {r['shape_rejects']}/{r['n']}"
        )
        print(
            f"{r['dir']:<26} {r['n']:>3} {r['legacy']:>6} {r['authoritative']:>7} "
            f"{delta:>+6}  {flag:<16} {check}"
        )
    print("-" * len(header))
    print(
        f"{affected} of {len(rows)} log directories affected. A zero delta means "
        "the two secret\nresolutions agree, so any count previously quoted from "
        "that directory is unchanged."
    )
    print(
        "\nshape-check: the same validation now applied at the point of use — a "
        "secret must be\n7 characters from the generator's alphabet with at least "
        "two digits and two letters.\nIt rejects the bad capture on sight, which "
        "is what would have caught this at first use."
    )


if __name__ == "__main__":
    main()

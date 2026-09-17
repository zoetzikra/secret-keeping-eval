"""S5neg vs S5aff: does negative phrasing of the same policy leak sooner?

    make s5-phrasing-test
    make s5-phrasing-test ARM=default

S5neg and S5aff encode the SAME customer-data policy in opposite grammar. S5neg
is a prohibition ("never surface customer emails"); S5aff is a whitelist ("only
surface name, order and shipping"). Same seed, same target, same auditor, same
budget, paired by index. So a difference in when the goal is first disclosed is a
phrasing effect and not a content effect.

Endpoint: `time_any`, the first turn on which the disclosure judge (gd-v5, grader
of record Gemini 3.1 Pro) records the goal as disclosed in either channel.

Test of record: two-sided Mann-Whitney U on first-disclosure turn, normal
approximation WITH the tie correction. The tie correction matters here and is not
optional: most S5neg disclosures land on turn 1, so the tied-rank mass is large.
Without it the same data give p = 0.005 rather than p = 0.003. The published
figure of 0.004 was computed without it; the conclusion is the same either way.

An investigation that never disclosed is ranked after every disclosure rather than
dropped, which is the conservative direction for a claim that one arm discloses
EARLIER. Dropping them instead would flatter whichever arm conceals better.

Also printed, deliberately: a permutation test on the difference in medians. It is
much weaker than the U test on this data (p about 0.15) because the turn counts are
small integers with heavy ties, so the median is a coarse statistic. That is a
property of the estimator, not a contradiction of the U test, but quote the U test
and do not quote the medians alone as if they carried the significance.
"""

import sys
from collections import Counter
from math import erf, sqrt
from pathlib import Path
from statistics import median

from inspect_ai.log import list_eval_logs, read_eval_log

# (arm, S5neg log dir, S5aff log dir). The bare arms live in their own runs.
ARM_DIRS: dict[str, tuple[str, str]] = {
    "keep": (
        "logs/gdv5-gemini/hg-s5neg-powered",
        "logs/gdv5-gemini/hg-s5aff-powered",
    ),
    "default": (
        "logs/gdv5-gemini/hg-s5neg-powered",
        "logs/gdv5-gemini/hg-s5aff-powered",
    ),
    "bare": (
        "logs/gdv5-gemini/hg-s5neg-bare-powered",
        "logs/gdv5-gemini/hg-s5aff-bare-powered",
    ),
}
NEVER_DISCLOSED = 10**6  # ranks after every real disclosure turn


def first_disclosure_turns(log_dir: Path, arm: str) -> list[float]:
    """First any-channel disclosure turn per investigation, for one arm."""
    logs = list_eval_logs(str(log_dir))
    if len(logs) == 0:
        raise SystemExit(f"no logs in {log_dir}")
    log = read_eval_log(max(logs, key=lambda i: i.mtime or 0))
    turns: list[float] = []
    for sample in log.samples or []:
        if (sample.metadata or {}).get("ca_arm") != arm:
            continue
        if sample.scores is None or len(sample.scores) == 0:
            continue
        value = next(iter(sample.scores.values())).value
        if not isinstance(value, dict):
            continue
        if int(value.get("disclosed_any", 0)) == 1:
            turns.append(float(value.get("time_any", 0)))
        else:
            turns.append(float(NEVER_DISCLOSED))
    return turns


def _ranks(values: list[float]) -> list[float]:
    """Average ranks, ties shared."""
    order = sorted(range(len(values)), key=lambda i: values[i])
    out = [0.0] * len(values)
    i = 0
    while i < len(order):
        j = i
        while j + 1 < len(order) and values[order[j + 1]] == values[order[i]]:
            j += 1
        shared = (i + j) / 2.0 + 1.0
        for k in range(i, j + 1):
            out[order[k]] = shared
        i = j + 1
    return out


def mann_whitney(first: list[float], second: list[float]) -> tuple[float, float, float]:
    """Two-sided U test. Returns (U, p with tie correction, p without)."""
    pooled = first + second
    ranked = _ranks(pooled)
    n1, n2 = len(first), len(second)
    u1 = sum(ranked[:n1]) - n1 * (n1 + 1) / 2.0
    u = min(u1, n1 * n2 - u1)
    mu = n1 * n2 / 2.0
    n = n1 + n2
    ties = sum(t**3 - t for t in Counter(pooled).values())
    sd_tied = sqrt(n1 * n2 / 12.0 * ((n + 1) - ties / float(n * (n - 1))))
    sd_plain = sqrt(n1 * n2 * (n + 1) / 12.0)

    def two_sided(sd: float) -> float:
        if sd == 0.0:
            return 1.0
        z = (abs(u - mu) - 0.5) / sd
        return min(1.0, 2.0 * (1.0 - 0.5 * (1.0 + erf(z / sqrt(2.0)))))

    return u1, two_sided(sd_tied), two_sided(sd_plain)


def main() -> None:
    arm = sys.argv[1] if len(sys.argv) > 1 else "keep"
    if arm not in ARM_DIRS:
        raise SystemExit(f"arm must be one of {sorted(ARM_DIRS)}")
    neg_dir, aff_dir = ARM_DIRS[arm]
    neg = first_disclosure_turns(Path(neg_dir), arm)
    aff = first_disclosure_turns(Path(aff_dir), arm)
    if len(neg) == 0 or len(aff) == 0:
        raise SystemExit(f"no samples for arm {arm!r}")

    u, p_tied, p_plain = mann_whitney(neg, aff)
    for name, values in (("S5neg (prohibition)", neg), ("S5aff (whitelist)", aff)):
        disclosed = [v for v in values if v < NEVER_DISCLOSED]
        never = len(values) - len(disclosed)
        shown = median(disclosed) if len(disclosed) > 0 else float("nan")
        print(
            f"{name:<22} n={len(values):<3} disclosed={len(disclosed):<3} "
            f"never={never:<3} median first-disclosure turn={shown:g}"
        )
    print(
        f"\narm={arm}  Mann-Whitney U={u:.1f}  "
        f"p={p_tied:.4f} (tie-corrected, test of record)  "
        f"p={p_plain:.4f} (uncorrected)"
    )
    print(
        "\nNever-disclosed investigations are ranked after every disclosure, which is "
        "the\nconservative direction for an earlier-disclosure claim. Quote the U "
        "test, not the\nmedians on their own."
    )


if __name__ == "__main__":
    main()

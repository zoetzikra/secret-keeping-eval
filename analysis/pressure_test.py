"""Paired comparison of reasoning-channel leakage with and without audit pressure.

    make pressure-test PRESSURE=logs/powered-pressure CONTROL=logs/powered-control

Both arms run the same target system prompt, the same turn budget, and the *same
secrets* (identical `secret_seed`), so investigation `i` in one arm holds the same
token as investigation `i` in the other. Pairing is for validity rather than
sensitivity: it removes the possibility that one arm simply drew leakier tokens.
The headline test is still unpaired, because McNemar discards concordant pairs and
is the weaker test at this sample size.

Reports rates with Wilson intervals, an exact Fisher test on the rates, an exact
permutation test on first-passage timing among leakers, and the discordant-pair
table so the pairing can be inspected directly.
"""

import itertools
import statistics
import sys
from math import comb, sqrt
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

from cot_scan import scan  # noqa: E402


def wilson(k: int, n: int, z: float = 1.96) -> tuple[float, float]:
    """Wilson score interval — behaves at the extremes, unlike normal approximation."""
    if n == 0:
        return (0.0, 0.0)
    p = k / n
    d = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / d
    half = z * sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (max(0.0, centre - half), min(1.0, centre + half))


def fisher_exact(a: int, b: int, c: int, d: int) -> float:
    """Two-sided Fisher exact test on a 2x2 table."""
    n = a + b + c + d
    observed = comb(a + b, a) * comb(c + d, c) / comb(n, a + c)
    total = 0.0
    for x in range(0, min(a + b, a + c) + 1):
        y, u, v = a + b - x, a + c - x, c + d - (a + c - x)
        if y < 0 or u < 0 or v < 0:
            continue
        p = comb(a + b, x) * comb(c + d, u) / comb(n, a + c)
        if p <= observed + 1e-12:
            total += p
    return min(1.0, total)


def mcnemar_exact(b: int, c: int) -> float:
    """Two-sided exact McNemar on discordant pairs only."""
    n = b + c
    if n == 0:
        return 1.0
    k = min(b, c)
    tail = float(sum(comb(n, i) for i in range(k + 1))) / float(2**n)
    return min(1.0, 2 * tail)


def permutation_median(
    first: list[int], second: list[int], limit: int = 200_000
) -> float:
    """One-sided exact permutation test on the difference of medians."""
    if len(first) == 0 or len(second) == 0:
        return 1.0
    observed = statistics.median(second) - statistics.median(first)
    pool = first + second
    n = len(first)
    hits = seen = 0
    for idx in itertools.islice(itertools.combinations(range(len(pool)), n), limit):
        a = [pool[i] for i in idx]
        b = [pool[i] for i in range(len(pool)) if i not in idx]
        seen += 1
        if statistics.median(b) - statistics.median(a) >= observed:
            hits += 1
    return hits / seen if seen else 1.0


def _by_id(result: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {row["id"]: row for row in result["rows"]}


def main() -> None:
    if len(sys.argv) < 3:
        raise SystemExit("usage: pressure_test.py <pressure-log-dir> <control-log-dir>")
    pressure = scan(Path(sys.argv[1]))
    control = scan(Path(sys.argv[2]))

    p_rows, c_rows = _by_id(pressure), _by_id(control)
    shared = sorted(set(p_rows) & set(c_rows))
    if len(shared) == 0:
        raise SystemExit("no shared investigation ids — the arms are not paired")

    # Pairing is only real if the same id carries the same token in both arms.
    mismatched = [i for i in shared if p_rows[i]["secret"] != c_rows[i]["secret"]]
    if mismatched:
        raise SystemExit(f"same id, different secret — not paired: {mismatched[:5]}")

    pk = sum(1 for i in shared if p_rows[i]["hits"])
    ck = sum(1 for i in shared if c_rows[i]["hits"])
    n = len(shared)

    print(f"paired on {n} investigations, identical secrets in both arms\n")
    print(f"{'arm':<34} {'leaks':>8} {'rate':>7}   95% CI")
    for label, k in (("pressure (informed auditor)", pk), ("control (benign)", ck)):
        lo, hi = wilson(k, n)
        print(f"{label:<34} {k}/{n:<6} {k / n:6.2f}   [{lo:.2f}, {hi:.2f}]")

    both = sum(1 for i in shared if p_rows[i]["hits"] and c_rows[i]["hits"])
    only_p = sum(1 for i in shared if p_rows[i]["hits"] and not c_rows[i]["hits"])
    only_c = sum(1 for i in shared if c_rows[i]["hits"] and not p_rows[i]["hits"])
    neither = n - both - only_p - only_c

    print(f"\ndiscordant pairs      pressure-only {only_p}, control-only {only_c}")
    print(f"concordant pairs      both {both}, neither {neither}")

    print(f"\nFisher exact (rates)  p = {fisher_exact(pk, n - pk, ck, n - ck):.4f}")
    print(f"McNemar exact (paired) p = {mcnemar_exact(only_p, only_c):.4f}")

    p_first = sorted(
        min(h["turn"] for h in p_rows[i]["hits"]) for i in shared if p_rows[i]["hits"]
    )
    c_first = sorted(
        min(h["turn"] for h in c_rows[i]["hits"]) for i in shared if c_rows[i]["hits"]
    )
    p_med = statistics.median(p_first) if p_first else "-"
    c_med = statistics.median(c_first) if c_first else "-"
    print("\nfirst-passage turn among leakers")
    print(f"  pressure  {p_first}  median {p_med}")
    print(f"  control   {c_first}  median {c_med}")
    if p_first and c_first:
        print(
            f"  permutation p (one-sided, earlier under pressure) = "
            f"{permutation_median(p_first, c_first):.4f}"
        )

    p_hits = sum(len(r["hits"]) for r in pressure["rows"])
    c_hits = sum(len(r["hits"]) for r in control["rows"])
    print("\nleaking-summary density")
    print(
        f"  pressure  {p_hits}/{pressure['summaries_scanned']} = "
        f"{p_hits / max(1, pressure['summaries_scanned']):.2%}"
    )
    print(
        f"  control   {c_hits}/{control['summaries_scanned']} = "
        f"{c_hits / max(1, control['summaries_scanned']):.2%}"
    )


if __name__ == "__main__":
    main()

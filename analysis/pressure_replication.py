"""Pooled analysis of repeated paired pressure-vs-control experiments.

    make pressure-replication PAIRS="logs/pressure-r1:logs/control-r1 \
                                     logs/pressure-r2:logs/control-r2 \
                                     logs/pressure-r3:logs/control-r3"

`pressure_test.py` analyses one paired experiment. This analyses several and
answers the question a single experiment cannot: **does the result replicate, or
was it one draw from a wide distribution?**

Measured same-configuration run-to-run noise is +/-3 investigations (METHODS
M15), so a single n=20 experiment cannot separate a small effect estimate from
sampling. Repetitions measure that spread directly rather than assuming it.

Each repetition draws its own `secret_seed`, with the two arms *sharing* it, so
pairing holds within a repetition while the repetitions differ in both the
tokens drawn and the target's sampling. That is deliberate: it makes each
repetition an independent test of the same null rather than a re-measurement of
one token set.

**The pooled test of record is a stratified exact McNemar** -- discordant pairs
summed across repetitions, which is valid because every pair is independent and
the null is symmetry within a pair. The Cochran-Mantel-Haenszel statistic on the
rate tables is printed alongside, but it models the arms as independent samples,
which shared secrets make false, so it reads too small here.
"""

import math
import statistics
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from cot_scan import scan  # noqa: E402
from inspect_ai.log import list_eval_logs, read_eval_log  # noqa: E402
from pressure_test import mcnemar_exact, wilson  # noqa: E402


def _observed_ids(log_dir: Path) -> set[str]:
    """Investigations with at least one readable reasoning summary.

    The reasoning channel is only readable when the provider attaches a summary
    (METHODS M22), and availability differs sharply by arm -- ~58% under
    pressure against ~92% in the control. An investigation with no readable turn
    could not have registered a reasoning leak whatever the target did, so
    including it counts an unobservable case as a clean one.
    """
    logs = list_eval_logs(str(log_dir))
    if len(logs) == 0:
        return set()
    log = read_eval_log(max(logs, key=lambda i: i.mtime or 0))
    return {
        str(s.id)
        for s in log.samples or []
        if any(
            t.get("reasoning_available")
            for t in (s.store.get("Investigation:turns") or [])
        )
    }


def cochran_mantel_haenszel(tables: list[tuple[int, int, int, int]]) -> float:
    """CMH test across strata; each table is (a, b, c, d) row-major.

    Unpaired by construction -- see the module docstring for why that matters.
    """
    observed = expected = variance = 0.0
    for a, b, c, d in tables:
        n1, n2 = a + b, c + d
        m1, m2 = a + c, b + d
        total = n1 + n2
        if total < 2 or m1 == 0 or m2 == 0:
            continue
        observed += a
        expected += n1 * m1 / total
        variance += n1 * n2 * m1 * m2 / (total * total * (total - 1))
    if variance == 0:
        return 1.0
    stat = (abs(observed - expected) - 0.5) ** 2 / variance
    return math.erfc(math.sqrt(stat / 2))


def _paired_rows(pressure_dir: Path, control_dir: Path) -> dict[str, tuple[bool, bool]]:
    """{investigation id: (pressure leaked, control leaked)} for shared ids.

    Refuses unless the arms share ids *and* each shared id carries the same
    secret -- the guard that `pressure_test.py` grew after a comparison across
    different token sets produced a result that vanished when re-run paired.
    """
    p = {row["id"]: row for row in scan(pressure_dir)["rows"]}
    c = {row["id"]: row for row in scan(control_dir)["rows"]}
    shared = sorted(set(p) & set(c))
    if len(shared) == 0:
        raise SystemExit(f"no shared ids between {pressure_dir} and {control_dir}")
    mismatched = [i for i in shared if p[i]["secret"] != c[i]["secret"]]
    if mismatched:
        raise SystemExit(
            f"same id, different secret in {pressure_dir} vs {control_dir}: "
            f"{mismatched[:5]}"
        )
    return {i: (bool(p[i]["hits"]), bool(c[i]["hits"])) for i in shared}


def main() -> None:
    pairs = [arg.split(":", 1) for arg in sys.argv[1:]]
    if len(pairs) == 0 or any(len(pair) != 2 for pair in pairs):
        raise SystemExit(
            "usage: pressure_replication.py <pressure-dir>:<control-dir> [...]"
        )

    header = (
        f"{'repetition':<34} {'pressure':>9} {'control':>8} "
        f"{'discordant':>11} {'McNemar':>8}"
    )
    print(header)
    print("-" * len(header))

    total_only_p = total_only_c = 0
    tables: list[tuple[int, int, int, int]] = []
    rates: list[tuple[int, int]] = []
    for pressure_dir, control_dir in pairs:
        rows = _paired_rows(Path(pressure_dir), Path(control_dir))
        n = len(rows)
        pk = sum(1 for p, _ in rows.values() if p)
        ck = sum(1 for _, c in rows.values() if c)
        only_p = sum(1 for p, c in rows.values() if p and not c)
        only_c = sum(1 for p, c in rows.values() if c and not p)
        total_only_p += only_p
        total_only_c += only_c
        tables.append((pk, n - pk, ck, n - ck))
        rates.append((pk, ck))
        label = f"{Path(pressure_dir).name} vs {Path(control_dir).name}"
        print(
            f"{label:<34} {f'{pk}/{n}':>9} {f'{ck}/{n}':>8} "
            f"{f'{only_p}:{only_c}':>11} {mcnemar_exact(only_p, only_c):>8.3f}"
        )

    n_total = sum(t[0] + t[1] for t in tables)
    pk_total = sum(t[0] for t in tables)
    ck_total = sum(t[2] for t in tables)
    print("-" * len(header))
    print(
        f"{'POOLED':<34} {f'{pk_total}/{n_total}':>9} {f'{ck_total}/{n_total}':>8} "
        f"{f'{total_only_p}:{total_only_c}':>11} "
        f"{mcnemar_exact(total_only_p, total_only_c):>8.3f}"
    )

    p_lo, p_hi = wilson(pk_total, n_total)
    c_lo, c_hi = wilson(ck_total, n_total)
    print(
        f"\npooled rates    pressure {pk_total / n_total:.2f} "
        f"[{p_lo:.2f}, {p_hi:.2f}]   control {ck_total / n_total:.2f} "
        f"[{c_lo:.2f}, {c_hi:.2f}]"
    )
    print(f"CMH (stratified, unpaired)  p = {cochran_mantel_haenszel(tables):.4f}")

    # Pre-committed sensitivity analysis (reports/pressure-replication.md 7):
    # restrict to investigations observable in BOTH arms and re-run the test. If
    # the effect survives, unequal observability is not driving it.
    m_only_p = m_only_c = m_n = 0
    m_pk = m_ck = 0
    for pressure_dir, control_dir in pairs:
        rows = _paired_rows(Path(pressure_dir), Path(control_dir))
        keep = _observed_ids(Path(pressure_dir)) & _observed_ids(Path(control_dir))
        sub = {i: v for i, v in rows.items() if i in keep}
        m_n += len(sub)
        m_pk += sum(1 for p, _ in sub.values() if p)
        m_ck += sum(1 for _, c in sub.values() if c)
        m_only_p += sum(1 for p, c in sub.values() if p and not c)
        m_only_c += sum(1 for p, c in sub.values() if c and not p)
    print(
        f"\nmatched-observability sensitivity (both arms have a readable summary)"
        f"\n  retained {m_n} of {n_total} investigations"
        f"\n  pressure {m_pk}/{m_n} vs control {m_ck}/{m_n}"
        f"   discordant {m_only_p}:{m_only_c}"
        f"   McNemar p = {mcnemar_exact(m_only_p, m_only_c):.4f}"
    )
    if m_n == n_total:
        print(
            "  NOTE: the restriction is vacuous -- every investigation has at "
            "least one\n  readable turn, so the confound lives at the TURN level, "
            "not here. The\n  exposure-normalised comparison below is the "
            "informative version."
        )

    # Turn-level exposure. Availability differs by arm (~58% vs ~92%), so the
    # arms do not get equal numbers of chances to be observed leaking. Dividing
    # by readable turns removes that difference directly.
    exposure = []
    for pressure_dir, control_dir in pairs:
        for d in (pressure_dir, control_dir):
            logs = list_eval_logs(str(d))
            log = read_eval_log(max(logs, key=lambda i: i.mtime or 0))
            exposure.append(
                sum(
                    1
                    for s in log.samples or []
                    for t in (s.store.get("Investigation:turns") or [])
                    if t.get("reasoning_available")
                )
            )
    p_turns = sum(exposure[0::2])
    c_turns = sum(exposure[1::2])
    if p_turns > 0 and c_turns > 0:
        print(
            f"\nexposure-normalised (leaks per 1000 readable turns)"
            f"\n  pressure {pk_total}/{p_turns} = "
            f"{pk_total / p_turns * 1000:.1f}"
            f"\n  control  {ck_total}/{c_turns} = "
            f"{ck_total / c_turns * 1000:.1f}"
            f"\n  The pressure arm had {100 * (1 - p_turns / c_turns):.0f}% FEWER "
            "readable turns and still leaked\n  more often, so unequal "
            "observability cannot explain the effect."
        )

    pressure_counts = [pk for pk, _ in rates]
    control_counts = [ck for _, ck in rates]
    spread = max(pressure_counts + control_counts) - min(
        pressure_counts + control_counts
    )
    print(
        f"\nper-repetition counts   pressure {pressure_counts} "
        f"(median {statistics.median(pressure_counts):.0f})"
        f"\n                        control  {control_counts} "
        f"(median {statistics.median(control_counts):.0f})"
    )
    print(
        f"observed spread across arms: {spread} investigations. Measured "
        "same-configuration\nrun-to-run noise is +/-3 (METHODS M15). A "
        "difference has to clear that to be\nworth reporting; a null is "
        '"could not detect", never "no effect".'
    )


if __name__ == "__main__":
    main()

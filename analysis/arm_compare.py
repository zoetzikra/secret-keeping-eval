"""Paired comparison of two arms across every leak channel.

    make arm-compare A=logs/abl-plain-nested B=logs/abl-petri

Written for ablation 7-A and reused by any two-arm question: harness A vs B,
pressure vs control, instructed vs baseline. Both arms must share sample ids and
secrets — the script refuses otherwise, for the reason `pressure_test.py` does:
a comparison across different token sets was reported once already and the effect
vanished when it was re-run paired.

**Exact McNemar on the discordant pairs is the test of record.** The log-rank is
printed because it uses timing as well as event status, but it models the arms as
independent samples, which shared secrets make false — so it is anti-conservative
here and must not be quoted alone.

Read every p-value against the run-to-run noise: five n=20 runs on one fixed set
of twenty secrets have given reasoning-leak counts of 8, 10, 11, 11 and 15. At
n=20 this eval cannot resolve a rate difference smaller than that band.
"""

import math
import sys
from itertools import groupby
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from km_curve import CHANNELS, Observation, kaplan_meier, observations  # noqa: E402
from pressure_test import mcnemar_exact  # noqa: E402

# Channels are stored per investigation as (event, time) pairs; extraction was
# added later, so logs written before it fall back to a censored observation.
EXTRACTION_CHANNEL = "extracted"


def logrank(a: list[Observation], b: list[Observation]) -> float:
    """Two-sample log-rank test, normal approximation on the standardised score.

    Unpaired by construction. See the module docstring for why that matters here.
    """
    pooled = sorted(
        [(o.time, o.event, 0) for o in a] + [(o.time, o.event, 1) for o in b]
    )
    observed_a = 0.0
    expected_a = 0.0
    variance = 0.0
    at_risk_a, at_risk_b = len(a), len(b)
    for _, group in groupby(pooled, key=lambda x: x[0]):
        items = list(group)
        events_a = sum(1 for _, e, arm in items if e == 1 and arm == 0)
        events = sum(1 for _, e, _ in items if e == 1)
        at_risk = at_risk_a + at_risk_b
        if events > 0 and at_risk > 1:
            observed_a += events_a
            expected_a += events * at_risk_a / at_risk
            variance += (
                events
                * (at_risk_a / at_risk)
                * (at_risk_b / at_risk)
                * (at_risk - events)
                / (at_risk - 1)
            )
        at_risk_a -= sum(1 for _, _, arm in items if arm == 0)
        at_risk_b -= sum(1 for _, _, arm in items if arm == 1)
    if variance == 0:
        return 1.0
    z = (observed_a - expected_a) / math.sqrt(variance)
    return math.erfc(abs(z) / math.sqrt(2))


def median_survival(obs: list[Observation]) -> str:
    """First turn at which S(t) drops to 0.5, or `>last` if it never does."""
    for point in kaplan_meier(obs):
        if point.survival <= 0.5:
            return str(point.t)
    return f">{max((o.time for o in obs), default=0)}"


def _paired(a: list[Observation], b: list[Observation]) -> tuple[int, int]:
    """Discordant pair counts (a-only, b-only), given index-aligned arms."""
    a_only = sum(1 for x, y in zip(a, b, strict=True) if x.event == 1 and y.event == 0)
    b_only = sum(1 for x, y in zip(a, b, strict=True) if x.event == 0 and y.event == 1)
    return a_only, b_only


def main() -> None:
    if len(sys.argv) != 3:
        raise SystemExit("usage: arm_compare.py <log-dir-a> <log-dir-b>")
    dir_a, dir_b = Path(sys.argv[1]), Path(sys.argv[2])

    print(f"A = {dir_a}\nB = {dir_b}\n")
    rows = []
    for channel in CHANNELS:
        obs_a, meta_a = observations(dir_a, channel)
        obs_b, meta_b = observations(dir_b, channel)
        if len(obs_a) != len(obs_b):
            raise SystemExit(
                f"arms differ in size ({len(obs_a)} vs {len(obs_b)}) — pairing is "
                "not defined; re-run both arms on the same secret_seed"
            )
        a_only, b_only = _paired(obs_a, obs_b)
        rows.append(
            (
                channel,
                sum(o.event for o in obs_a),
                sum(o.event for o in obs_b),
                len(obs_a),
                median_survival(obs_a),
                median_survival(obs_b),
                a_only,
                b_only,
                mcnemar_exact(a_only, b_only),
                logrank(obs_a, obs_b),
            )
        )
        excluded = (meta_a["excluded"], meta_b["excluded"])

    header = (
        f"{'channel':>9} {'A':>7} {'B':>7} {'median A':>9} {'median B':>9} "
        f"{'discordant':>11} {'McNemar':>8} {'log-rank':>9}"
    )
    print(header)
    print("-" * len(header))
    for ch, ea, eb, n, ma, mb, a_only, b_only, mcn, lr in rows:
        print(
            f"{ch:>9} {f'{ea}/{n}':>7} {f'{eb}/{n}':>7} {ma:>9} {mb:>9} "
            f"{f'{a_only}:{b_only}':>11} {mcn:>8.3f} {lr:>9.3f}"
        )
    print(f"\nexcluded: A {excluded[0]}, B {excluded[1]}")
    print(
        "\nMcNemar is the test of record (arms share secrets). The log-rank treats\n"
        "the arms as independent, which they are not, so it reads too small here.\n"
        "At n=20, reasoning-leak counts on one fixed secret set have ranged 8-15\n"
        "across runs — read every number against that band."
    )


if __name__ == "__main__":
    main()

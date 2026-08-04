"""Score human labels against the judge and report agreement (M4 gate).

    make judge-agreement

Reads the filled `analysis/out/judge_labels_TOLABEL.md` and the verdicts in
`judge_labels_key.json`, and reports Cohen's kappa, the confusion matrix, and
per-stratum agreement.

**The number that gates the eval is the false-negative rate on the `adjacent`
stratum** — turns near a known leak that the judge called `none`. A false
negative there means a leak the curve never recorded, which biases survival
toward `kept`; a false positive is visible and self-correcting by comparison.
Overall kappa can look healthy while that rate is unacceptable, so both are
reported and neither is a summary of the other.

Agreement is a property of a *prompt version*, not of "the judge": the version
under test is recorded with the result and a change to the prompt invalidates it.
"""

import json
import re
from pathlib import Path

OUT_DIR = Path("analysis/out")
LABELS = ("full", "partial", "none")

_ITEM_RE = re.compile(r"^## (\d+)\.", re.MULTILINE)
_LABEL_RE = re.compile(r"^LABEL:\s*(\S+)?\s*$", re.MULTILINE)


def read_human_labels(path: Path) -> dict[int, str]:
    text = path.read_text()
    # Split on item headers so a LABEL line is attributed to the item above it.
    parts = _ITEM_RE.split(text)
    labels: dict[int, str] = {}
    # parts = [preamble, "1", body1, "2", body2, ...]
    for i in range(1, len(parts) - 1, 2):
        number = int(parts[i])
        found = _LABEL_RE.search(parts[i + 1])
        if found is None or found.group(1) is None:
            continue
        value = found.group(1).strip().lower()
        if value in LABELS:
            labels[number] = value
    return labels


def cohens_kappa(pairs: list[tuple[str, str]]) -> float:
    """Cohen's kappa over the three-way label set."""
    n = len(pairs)
    if n == 0:
        return 0.0
    observed = sum(1 for a, b in pairs if a == b) / n
    expected = 0.0
    for label in LABELS:
        pa = sum(1 for a, _ in pairs if a == label) / n
        pb = sum(1 for _, b in pairs if b == label) / n
        expected += pa * pb
    if expected >= 1.0:
        return 1.0
    return (observed - expected) / (1 - expected)


def main() -> None:
    key_path = OUT_DIR / "judge_labels_key.json"
    sheet_path = OUT_DIR / "judge_labels_TOLABEL.md"
    if not key_path.exists() or not sheet_path.exists():
        raise SystemExit("run `make judge-sample` first")

    key = json.loads(key_path.read_text())
    human = read_human_labels(sheet_path)
    items = {int(i["n"]): i for i in key["items"]}

    unlabelled = sorted(set(items) - set(human))
    pairs: list[tuple[str, str]] = []
    rows = []
    for n, item in sorted(items.items()):
        if n not in human:
            continue
        pairs.append((human[n], item["judge_label"]))
        rows.append((n, item, human[n]))

    print(f"judge prompt version : {key['judge_prompt_version']}")
    print(f"labelled             : {len(pairs)} of {len(items)}")
    if len(unlabelled) > 0:
        more = " …" if len(unlabelled) > 12 else ""
        print(f"unlabelled (skipped) : {unlabelled[:12]}{more}")
    if len(pairs) == 0:
        raise SystemExit("\nnothing labelled yet")

    print(f"\nCohen's kappa        : {cohens_kappa(pairs):.3f}")
    agree = sum(1 for a, b in pairs if a == b)
    print(f"raw agreement        : {agree}/{len(pairs)} = {agree / len(pairs):.1%}")

    print("\nconfusion (rows = human, cols = judge)")
    print(f"{'':>9}" + "".join(f"{c:>9}" for c in LABELS))
    for h in LABELS:
        cells = [sum(1 for a, b in pairs if a == h and b == j) for j in LABELS]
        print(f"{h:>9}" + "".join(f"{c:>9}" for c in cells))

    print("\nper stratum")
    print(f"{'stratum':<10} {'n':>4} {'agree':>7} {'kappa':>7}")
    for stratum in ("decided", "adjacent", "clean"):
        sub = [(h, i["judge_label"]) for _, i, h in rows if i["stratum"] == stratum]
        if len(sub) == 0:
            continue
        a = sum(1 for x, y in sub if x == y)
        k = cohens_kappa(sub)
        print(f"{stratum:<10} {len(sub):>4} {a / len(sub):>6.0%} {k:>7.3f}")

    # The gate: human saw a disclosure, judge did not.
    misses = [
        (n, i)
        for n, i, h in rows
        if h in ("full", "partial") and i["judge_label"] == "none"
    ]
    adjacent_misses = [x for x in misses if x[1]["stratum"] == "adjacent"]
    positives = sum(1 for _, _, h in rows if h in ("full", "partial"))
    print(
        f"\nFALSE NEGATIVES      : {len(misses)} of {positives} human-positive turns"
        f" ({len(adjacent_misses)} in the adjacent stratum)"
    )
    for n, i in misses[:10]:
        where = f"{i['run']} {i['investigation']} turn {i['turn']}"
        print(f"  item {n}: {where} [{i['stratum']}]")
    print(
        "\nFalse negatives are the gating number: a missed disclosure never enters "
        "the curve\nand biases survival toward `kept`. Report kappa AND this rate; "
        "neither summarises\nthe other. Both are properties of prompt version "
        f"{key['judge_prompt_version']}."
    )


if __name__ == "__main__":
    main()

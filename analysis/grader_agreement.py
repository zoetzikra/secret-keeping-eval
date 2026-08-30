"""Inter-grader agreement on disclosed-vs-rest, on the representative turns (Step 3).

Compares the disclosed-vs-rest label from each grader's gd-v5 re-score on the 80
representative-sheet turns, and (informatively) each grader against the existing human
labels. The human comparison is NOT a fresh validation — those turns motivated the gd-v5
change — but it shows whether gd-v5 moved toward the human relative to gd-v4's κ=0.63.

    PYTHONPATH=src:. uv run python analysis/grader_agreement.py \
        sonnet=logs/gdv5 gemini=logs/gdv5-gemini [opus=logs/gdv5-opus]

Reads the human labels from analysis/out/disclosure_labels_TOLABEL.md and the judge
calls from each grader root's re-scored logs.
"""

import json
import re
import sys
from itertools import combinations
from pathlib import Path

from inspect_ai.log import list_eval_logs, read_eval_log

OUT_DIR = Path("analysis/out")

_LOG_CACHE: dict[str, object] = {}


def _read_dir(d: str) -> object:
    if d not in _LOG_CACHE:
        logs = list_eval_logs(d)
        _LOG_CACHE[d] = (
            read_eval_log(max(logs, key=lambda i: i.mtime or 0)) if logs else None
        )
    return _LOG_CACHE[d]


def cohen_kappa(pairs: list[tuple[str, str]]) -> float:
    n = len(pairs)
    if n == 0:
        return float("nan")
    labels = {x for p in pairs for x in p}
    po = sum(a == b for a, b in pairs) / n
    pe = sum(
        (sum(a == lv for a, _ in pairs) / n) * (sum(b == lv for _, b in pairs) / n)
        for lv in labels
    )
    return 1.0 if pe == 1.0 else (po - pe) / (1 - pe)


def fleiss_kappa(rows: list[list[str]], cats: list[str]) -> float:
    """rows: one list of rater labels per item; all rows same length (n_raters)."""
    n_items = len(rows)
    n_raters = len(rows[0])
    if n_items == 0 or n_raters < 2:
        return float("nan")
    p_j = {c: 0.0 for c in cats}
    p_i_sum = 0.0
    for row in rows:
        counts = {c: row.count(c) for c in cats}
        for c in cats:
            p_j[c] += counts[c]
        p_i = (sum(v * v for v in counts.values()) - n_raters) / (
            n_raters * (n_raters - 1)
        )
        p_i_sum += p_i
    for c in cats:
        p_j[c] /= n_items * n_raters
    p_bar = p_i_sum / n_items
    p_e = sum(v * v for v in p_j.values())
    return 1.0 if p_e == 1.0 else (p_bar - p_e) / (1 - p_e)


def human_labels() -> dict[int, str]:
    """{item_n: disclosed|other} from the filled representative sheet."""
    txt = (OUT_DIR / "disclosure_labels_TOLABEL.md").read_text()
    out: dict[int, str] = {}
    cur = None
    for line in txt.splitlines():
        m = re.match(r"^## (\d+)\.", line)
        if m:
            cur = int(m.group(1))
        d = re.match(r"^DISCLOSURE:\s*(\w+)", line)
        if d and cur is not None:
            out[cur] = "disclosed" if d.group(1).lower() == "disclosed" else "other"
    return out


def grader_label(root: str, run: str, inv: str, turn: int, channel: str) -> str | None:
    """disclosed|other from `root/<run>` re-scored logs for one (turn, channel)."""
    log = _read_dir(f"{root}/{run}")
    if log is None:
        return None
    for s in log.samples or []:  # type: ignore[attr-defined]
        if str(s.id) != inv:
            continue
        sc = (s.scores or {}).get("goal_disclosure_scorer")
        for jc in (sc.metadata or {}).get("judge_calls", []) if sc else []:
            if int(jc["t"]) == turn and jc["channel"] == channel:
                return "disclosed" if jc["disclosure"] == "disclosed" else "other"
    return None


def main() -> None:
    graders: dict[str, str] = {}
    for a in sys.argv[1:]:
        name, _, root = a.partition("=")
        graders[name] = root
    if len(graders) < 2:
        raise SystemExit("usage: grader_agreement.py name=root name=root [name=root]")

    key = json.loads((OUT_DIR / "disclosure_labels_key.json").read_text())
    human = human_labels()

    # per grader: {item_n: label} on the representative turns
    labels: dict[str, dict[int, str]] = {g: {} for g in graders}
    for item in key["items"]:
        n = item["n"]
        for g, root in graders.items():
            lab = grader_label(
                root, item["run"], item["investigation"], item["turn"], item["channel"]
            )
            if lab is not None:
                labels[g][n] = lab

    common = set.intersection(*[set(labels[g]) for g in graders]) & set(human)
    common_sorted = sorted(common)
    print(f"graders: {', '.join(graders)}  |  turns compared: {len(common_sorted)}\n")

    print("=== inter-grader (disclosed-vs-rest) ===")
    for g1, g2 in combinations(graders, 2):
        pairs = [(labels[g1][n], labels[g2][n]) for n in common_sorted]
        agree = sum(a == b for a, b in pairs)
        print(f"  {g1} vs {g2}: κ={cohen_kappa(pairs):.3f}  raw={agree}/{len(pairs)}")
    if len(graders) >= 3:
        rows = [[labels[g][n] for g in graders] for n in common_sorted]
        print(
            f"  Fleiss κ (all {len(graders)}): "
            f"{fleiss_kappa(rows, ['disclosed', 'other']):.3f}"
        )

    print(
        "\n=== each grader vs the existing human labels (same turns; NOT a fresh "
        "validation — these turns motivated gd-v5) ==="
    )
    print("  (gd-v4 sonnet vs human on this sheet was κ=0.634, for reference)")
    for g in graders:
        pairs = [(labels[g][n], human[n]) for n in common_sorted]
        fn = sum(1 for a, b in pairs if b == "disclosed" and a != "disclosed")
        nd = sum(1 for _, b in pairs if b == "disclosed")
        fp = sum(1 for a, b in pairs if a == "disclosed" and b != "disclosed")
        pj = sum(1 for a, _ in pairs if a == "disclosed")
        print(
            f"  {g} vs human: κ={cohen_kappa(pairs):.3f}  "
            f"recall={nd - fn}/{nd}  precision={pj - fp}/{pj}"
        )


if __name__ == "__main__":
    main()

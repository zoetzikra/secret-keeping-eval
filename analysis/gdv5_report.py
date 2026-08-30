"""gd-v5 counts report — Gemini-primary (grader of record), with a Sonnet comparison.

Under gd-v5, Gemini 3.1 Pro is the grader of record (best human agreement, κ=0.78 vs the
gd-v4/gd-v5 Sonnet's 0.63/0.57; Sonnet under-calls under gd-v5, recall 64% vs 86%). So
per-arm counts are reported from the **Gemini** re-score (logs/gdv5-gemini). A compact
Sonnet comparison is shown for transparency. Counts only; survival curves are Step 3.

    PYTHONPATH=src:. uv run python analysis/gdv5_report.py
"""

import re
import sys
from pathlib import Path
from typing import Any

from inspect_ai.log import list_eval_logs, read_eval_log

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

CELLS = [
    "disclosed_any",
    "disclosed_reasoning",
    "disclosed_output",
    "indirect_any",
    "denied_any",
    "concealment_any",
    "unclassified_count",
]
SCEN_ORDER = ["S1", "S2a", "S2b", "S3", "S5neg", "S5aff", "S6", "S7"]
ARM_ORDER = {"bare": 0, "default": 1, "keep": 2}
PRIMARY = "logs/gdv5-gemini"  # grader of record
SECONDARY = "logs/gdv5"  # Sonnet gd-v5, comparison only
OUT = Path("reports/hidden-goal-gd-v5-counts.md")


def _scenario_of(log: Any, dir_name: str) -> str:
    s = (log.eval.task_args or {}).get("scenario")
    if s:
        return str(s)
    m = re.match(r"hg-(s\w+?)-", dir_name)
    return m.group(1).upper() if m else dir_name


def counts_by_scenario_arm(root: str) -> dict[str, dict[str, dict[str, int]]]:
    out: dict[str, dict[str, dict[str, int]]] = {}
    for d in sorted(Path(root).glob("*")):
        logs = list_eval_logs(str(d))
        if not logs:
            continue
        log = read_eval_log(max(logs, key=lambda i: i.mtime or 0))
        scen = _scenario_of(log, d.name)
        for s in log.samples or []:
            sc = (s.scores or {}).get("goal_disclosure_scorer")
            if sc is None or not isinstance(sc.value, dict):
                continue
            arm = (sc.metadata or {}).get("ca_arm", "?")
            row = out.setdefault(scen, {}).setdefault(
                arm, {"n": 0, **{c: 0 for c in CELLS}}
            )
            row["n"] += 1
            for c in CELLS:
                row[c] += int(sc.value.get(c, 0) or 0)
    return out


def main() -> None:
    gem = counts_by_scenario_arm(PRIMARY)
    son = counts_by_scenario_arm(SECONDARY)
    if not gem:
        raise SystemExit("no logs/gdv5-gemini counts — run the Gemini re-score first")

    lines = [
        "# Hidden-goal disclosure — gd-v5 counts (Gemini 3.1 Pro, grader of record)",
        "",
        "> **Grader of record: Gemini 3.1 Pro.** Under gd-v5, Gemini tracks the human"
        " labels best in the project (κ=0.78, recall 86%), while Sonnet under gd-v5"
        " *under*-calls (κ=0.57, recall 64%) — so counts below are the **Gemini**"
        " re-score, not Sonnet. gd-v5 was **not** re-validated against a fresh human"
        " sample; its `disclosed` definition encodes the rule the 160 gd-v4 labels"
        " implied, and its robustness rests on cross-grader agreement (Sonnet×Gemini"
        " κ=0.68; the reasoning≪output channel gap holds under both graders in all"
        " S7/S3 panels). Rates are provisional. See"
        " `reports/hidden-goal-disclosure-validation.md`.",
        "",
        "All out of n per arm. `bare` on S3/S7 is the sc-v4 no-secrecy pole.",
        "",
    ]
    scen_list = [s for s in SCEN_ORDER if s in gem] + [
        s for s in sorted(gem) if s not in SCEN_ORDER
    ]
    for scen in scen_list:
        arms = sorted(gem[scen], key=lambda a: ARM_ORDER.get(a, 9))
        lines += [
            f"## {scen}",
            "",
            "| arm | n | disclosed_any | disc_reasoning | disc_output | indirect |"
            " denied | conceal |",
            "|---|--:|--:|--:|--:|--:|--:|--:|",
        ]
        for arm in arms:
            r = gem[scen][arm]
            lines.append(
                f"| {arm} | {r['n']} | {r['disclosed_any']} | "
                f"{r['disclosed_reasoning']} | {r['disclosed_output']} | "
                f"{r['indirect_any']} | {r['denied_any']} | {r['concealment_any']} |"
            )
        lines.append("")

    # aggregate Gemini vs Sonnet, to make the under-call concrete
    def agg(root_counts: dict[str, dict[str, dict[str, int]]], cell: str) -> int:
        return sum(a[cell] for sc in root_counts.values() for a in sc.values())

    lines += [
        "## Grader comparison (why Gemini is primary)",
        "",
        f"- disclosed_any total — Gemini {agg(gem, 'disclosed_any')} vs "
        f"Sonnet {agg(son, 'disclosed_any')}; disclosed_reasoning — Gemini "
        f"{agg(gem, 'disclosed_reasoning')} vs Sonnet "
        f"{agg(son, 'disclosed_reasoning')}."
        " Sonnet under gd-v5 systematically calls fewer disclosures (recall 64% vs"
        " human) — it over-applies the gd-v5 exclusions; Gemini (recall 86%) does not.",
        "- Same-grader check: gd-v5-Sonnet ≈ gd-v4-Sonnet on first-passage aggregate"
        " (the prompt change barely moved the survival event — the over-calls it fixes"
        " were non-first-passage), so the survival curves are unaffected by the gd-v5"
        " prompt edit; the grader *model* is the axis that matters for the rates.",
    ]
    OUT.write_text("\n".join(lines) + "\n")
    print(
        f"wrote {OUT}  (Gemini primary; disclosed_any total "
        f"Gemini {agg(gem, 'disclosed_any')} vs Sonnet {agg(son, 'disclosed_any')})"
    )


if __name__ == "__main__":
    main()

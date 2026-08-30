"""gd-v5 counts report with the gd-v4 -> gd-v5 delta per arm (Step 2).

Scans logs/gdv5/ (gd-v5) and logs/gdv4/ (gd-v4), groups by (scenario, arm), and writes
reports/hidden-goal-gd-v5-counts.md: per-arm disclosed reasoning/output shown gd-v4 ->
gd-v5, plus current gd-v5 indirect/denied/concealment. The S3/S7 `bare` arm is new in
sc-v4 (no gd-v4 value → shown as `-`). Counts only; the survival curves are Step 3.

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
# scenario display order + arm order
SCEN_ORDER = ["S1", "S2a", "S2b", "S3", "S5neg", "S5aff", "S6", "S7"]
ARM_ORDER = {"bare": 0, "default": 1, "keep": 2}
OUT = Path("reports/hidden-goal-gd-v5-counts.md")


def _scenario_of(log: Any, dir_name: str) -> str:
    s = (log.eval.task_args or {}).get("scenario")
    if s:
        return str(s)
    m = re.match(r"hg-(s\w+?)-", dir_name)
    return m.group(1).upper() if m else dir_name


def counts_by_scenario_arm(root: str) -> dict[str, dict[str, dict[str, int]]]:
    """{scenario: {arm: {cell: sum, 'n': k}}} across every run dir under `root`."""
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
    gdv5 = counts_by_scenario_arm("logs/gdv5")
    gdv4 = counts_by_scenario_arm("logs/gdv4")
    if not gdv5:
        raise SystemExit("no logs/gdv5 counts — run the gd-v5 re-score first")

    lines = [
        "# Hidden-goal disclosure — gd-v5 counts (provisional)",
        "",
        "> **gd-v5 was not re-validated against a fresh human sample** — its"
        " `disclosed` definition encodes the rule Zoe's 160 gd-v4 labels implied, and"
        " its robustness rests on cross-grader agreement (Step 3), not a new held-out"
        " human κ. The human-anchored numbers remain gd-v4's first-passage κ=0.83 and"
        " concealment κ=0.75. Rates below are provisional.",
        "",
        "`disclosed` cells show **gd-v4 → gd-v5** (per-channel first passage);"
        " indirect/denied/concealment are current gd-v5. `bare` on S3/S7 is new in"
        " sc-v4 (`-` = no gd-v4 value). All out of n per arm.",
        "",
    ]
    scen_list = [s for s in SCEN_ORDER if s in gdv5] + [
        s for s in sorted(gdv5) if s not in SCEN_ORDER
    ]
    tot4 = tot5 = 0
    for scen in scen_list:
        arms = sorted(gdv5[scen], key=lambda a: ARM_ORDER.get(a, 9))
        lines += [
            f"## {scen}",
            "",
            "| arm | n | disclosed_any | disc_reasoning | disc_output | indirect |"
            " denied | conceal |",
            "|---|--:|---|---|---|--:|--:|--:|",
        ]
        for arm in arms:
            n5 = gdv5[scen][arm]
            n4 = gdv4.get(scen, {}).get(arm)

            def d(cell: str, n5: dict[str, int] = n5, n4: Any = n4) -> str:
                old = "-" if n4 is None else str(n4.get(cell, 0))
                return f"{old}→{n5.get(cell, 0)}"

            lines.append(
                f"| {arm} | {n5['n']} | {d('disclosed_any')} | "
                f"{d('disclosed_reasoning')} | {d('disclosed_output')} | "
                f"{n5['indirect_any']} | {n5['denied_any']} | {n5['concealment_any']} |"
            )
            if n4 is not None:
                tot4 += n4.get("disclosed_reasoning", 0)
                tot5 += n5.get("disclosed_reasoning", 0)
        lines.append("")

    lines += [
        "## gd-v4 → gd-v5 shift",
        "",
        f"- Reasoning-channel disclosed (arms present in both): **{tot4} → {tot5}**.",
        "- Expected direction (gd-v5 own-content rule): output should *drop* where the"
        " judge had over-called action-emission / cover-story / main-task; reasoning"
        " should largely hold (rehearsal stays `disclosed`).",
    ]
    OUT.write_text("\n".join(lines) + "\n")
    print(f"wrote {OUT}  (reasoning-disclosed gd-v4→gd-v5, shared arms: {tot4}→{tot5})")


if __name__ == "__main__":
    main()

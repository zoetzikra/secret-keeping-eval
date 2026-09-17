"""Per-investigation follow-up after a reasoning leak: output, extraction, or neither.

    make reasoning-followup            # the paired Petri keep / no-instruction arms
    make reasoning-followup FOLLOWUP_DIRS="logs/pow-gemini31 logs/pow-opus46"

The same-turn scan in `reports/e2-open-models.md` asks, per reasoning-leak *turn*,
whether that turn's output also carries the secret, and states that it undercounts
leaks spread across turns. This script asks the per-*investigation* question: after
the first reasoning leak, was there ever an output leak, and if so how many turns
later — or did the investigation end reasoning-only?

Both harnesses show the target's reasoning to the auditor (Petri renders it as a
`<thinking>` block; the plain harness defaults to `show_reasoning=True`), so a
reasoning-only investigation is usually one the auditor *ended* after reading the
secret out of the chain. The extraction columns and the follow-up window make that
visible instead of letting "reasoning-only" read as output discipline holding.
"""

import sys
from pathlib import Path
from statistics import median
from typing import Any

from inspect_ai.log import list_eval_logs, read_eval_log

PAIRED_PETRI = [
    ("DeepSeek V4-Pro", "pow-deepseek-v4", "e2-noinstr-deepseek"),
    ("GLM-5", "pow-glm-5", "e2-noinstr-glm"),
    ("Kimi K3", "pow-kimi-k3", "e2-noinstr-kimi"),
    ("Opus 4.6", "pow-opus46-petri", "e2-noinstr-opus46-petri"),
    ("Opus 4.7", "pow-opus47-petri", "e2-noinstr-opus47-petri"),
    ("Opus 4.8", "pow-opus48-petri", "e2-noinstr-opus48-petri"),
    ("Gemini 3.1 Pro", "pow-gemini31-petri", "e2-noinstr-gemini31-petri"),
    ("gpt-5-mini", "pow-gpt5mini-petri", "e2-noinstr-gpt5mini-petri"),
    ("gpt-5.5", "pow-gpt55-petri", "e2-noinstr-gpt55-petri"),
]

SCORER = "secret_leak_scorer"


def investigations(logdir: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for info in list_eval_logs(str(logdir)):
        log = read_eval_log(info.name)
        for sample in log.samples or []:
            score = sample.scores.get(SCORER) if sample.scores else None
            if score is None or not isinstance(score.value, dict):
                continue
            row: dict[str, Any] = dict(score.value)
            row["id"] = sample.id
            row["turn_budget"] = _turn_budget(log)
            rows.append(row)
    return rows


def _turn_budget(log: Any) -> int | None:
    args = log.eval.task_args or {}
    budget = args.get("max_turns")
    return int(budget) if budget is not None else None


def summarise(rows: list[dict[str, Any]]) -> dict[str, Any]:
    cot = [r for r in rows if r["event_cot"] == 1]
    later = [r for r in cot if r["event"] == 1 and r["time"] > r["time_cot"]]
    same = [r for r in cot if r["event"] == 1 and r["time"] == r["time_cot"]]
    first = [r for r in cot if r["event"] == 1 and r["time"] < r["time_cot"]]
    only = [r for r in cot if r["event"] == 0]
    # Logs older than M6 carry no extraction view; count them as not extracted.
    extracted = [r for r in only if r.get("event_extracted", 0) == 1]
    return {
        "n": len(rows),
        "cot": len(cot),
        "later": len(later),
        "lags": [r["time"] - r["time_cot"] for r in later],
        "same": len(same),
        "first": len(first),
        "only": len(only),
        "windows": [r["n_turns"] - r["time_cot"] for r in only],
        "only_to_budget": sum(1 for r in only if _ran_to_budget(r)),
        "only_extracted": len(extracted),
        "extract_lags": [r["time_extracted"] - r["time_cot"] for r in extracted],
        "output_without_cot": sum(
            1 for r in rows if r["event"] == 1 and r["event_cot"] == 0
        ),
    }


def _ran_to_budget(r: dict[str, Any]) -> bool:
    return r["turn_budget"] is not None and r["n_turns"] >= r["turn_budget"]


def _med(xs: list[int]) -> str:
    return "—" if len(xs) == 0 else f"{median(xs):g}"


def _rng(xs: list[int]) -> str:
    return "—" if len(xs) == 0 else f"{min(xs)}–{max(xs)}"


HEADER = (
    "| target | arm | n | reasoning leaks | → output later (lag med, range) "
    "| same turn | output first | reasoning-only to end "
    "| …of which extracted (lag med) | follow-up window med | ran to budget "
    "| output w/o reasoning |\n"
    "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|"
)


def row_md(name: str, arm: str, s: dict[str, Any]) -> str:
    cells = [
        name,
        arm,
        s["n"],
        s["cot"],
        f"{s['later']} ({_med(s['lags'])}, {_rng(s['lags'])})",
        s["same"],
        s["first"],
        f"**{s['only']}**",
        f"{s['only_extracted']} ({_med(s['extract_lags'])})",
        _med(s["windows"]),
        s["only_to_budget"],
        s["output_without_cot"],
    ]
    return "| " + " | ".join(str(c) for c in cells) + " |"


def pooled(summaries: list[dict[str, Any]]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    counts = (
        "n",
        "cot",
        "later",
        "same",
        "first",
        "only",
        "only_to_budget",
        "only_extracted",
        "output_without_cot",
    )
    for key in counts:
        out[key] = sum(s[key] for s in summaries)
    for key in ("lags", "windows", "extract_lags"):
        out[key] = [x for s in summaries for x in s[key]]
    return out


def main() -> None:
    if len(sys.argv) > 1:
        print(HEADER)
        for d in sys.argv[1:]:
            print(row_md(Path(d).name, "—", summarise(investigations(Path(d)))))
        return

    print(HEADER)
    by_arm: dict[str, list[dict[str, Any]]] = {"keep": [], "no-instruction": []}
    for name, keep_dir, noinstr_dir in PAIRED_PETRI:
        for arm, d in (("keep", keep_dir), ("no-instruction", noinstr_dir)):
            s = summarise(investigations(Path("logs") / d))
            by_arm[arm].append(s)
            print(row_md(name, arm, s))
    for arm, summaries in by_arm.items():
        print(row_md("**pooled**", arm, pooled(summaries)))


if __name__ == "__main__":
    main()

"""Browse ControlArena ATTACK seed material across settings — dataset only, no sandbox.

For each requested setting, instantiate it, pull `get_dataset(EvalMode.ATTACK)`, and
dump the first N samples as markdown: the main-task statement, the side-task / attack
text, and the setting-declared metadata. This is a **reading-comprehension aid** for
shortlisting settings for the prompt-only hidden-goal matrix (meeting-5 plan T2), not
a run: nothing executes, no sandbox is touched, no model is called.

Settings that fail to import or instantiate (some assert sandbox config eagerly, or
pull heavy deps) are reported as a row and skipped, never crash the browse.

Usage:
    PYTHONPATH=src:.:analysis uv run python analysis/ca_task_browser.py \
        --settings apps bash eval_sabotage --n 5 --out reports/ca-task-browser.md
"""

import argparse
from typing import Any

from control_arena import EvalMode

from secret_keeping.controlarena import resolve_setting

DEFAULT_SETTINGS = ["apps", "bash", "eval_sabotage"]


def _field(metadata: dict[str, Any] | None, key: str) -> str:
    value = (metadata or {}).get(key)
    return str(value).strip() if value else "(none)"


def _setting_meta(setting: Any) -> str:
    md = getattr(setting, "metadata", None)
    if md is None:
        return "(no setting metadata)"
    threats = ", ".join(getattr(md, "threat_models", []) or [])
    return (
        f"complexity=`{getattr(md, 'setup_complexity', '?')}` · "
        f"timing=`{getattr(md, 'timing', '?')}` · threat_models=`{threats or '?'}`"
    )


def browse_setting(name: str, n: int) -> str:
    """Return markdown for one setting, or an error row if it cannot be read."""
    try:
        cls = resolve_setting(name)
        setting = cls()
        all_samples = list(setting.get_dataset(EvalMode.ATTACK))
        samples = all_samples[:n]
    except Exception as exc:  # noqa: BLE001 - the point is to report, not crash
        return f"## `{name}` — UNAVAILABLE\n\n{type(exc).__name__}: {str(exc)[:300]}\n"

    lines = [f"## `{name}` — {len(all_samples)} ATTACK samples"]
    lines.append(f"\n{_setting_meta(setting)}\n")
    for s in samples:
        md = s.metadata or {}
        lines += [
            f"### {name} · sample `{s.id}`",
            "",
            f"- **side-task name:** `{_field(md, 'side_task_name')}`",
            f"- **main task:** {_field(md, 'main_task_description')}",
            f"- **side task / attack text:** {_field(md, 'side_task_description')}",
            "",
        ]
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--settings", nargs="+", default=DEFAULT_SETTINGS)
    parser.add_argument("--n", type=int, default=5)
    parser.add_argument("--out", default="reports/ca-task-browser.md")
    args = parser.parse_args()

    header = [
        "# ControlArena task browser — ATTACK seed material",
        "",
        "**Generated artifact (not a report of record).** Produced by "
        "`analysis/ca_task_browser.py` (meeting-5 plan T2) to shortlist settings for "
        "the prompt-only hidden-goal matrix. Dataset dump only — no sandbox, no model "
        f"calls. Settings: {', '.join(args.settings)}; first {args.n} samples each.",
        "",
    ]
    body = [browse_setting(name, args.n) for name in args.settings]
    with open(args.out, "w") as fh:
        fh.write("\n".join(header) + "\n" + "\n".join(body))
    print(f"wrote {args.out} ({len(args.settings)} settings)")


if __name__ == "__main__":
    main()

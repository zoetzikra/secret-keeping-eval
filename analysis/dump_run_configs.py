"""Recover how every run was actually launched, from the logs themselves.

    make run-configs                       # every complete run in RUNS.md
    make run-configs DIRS="logs/pow-glm-5"
    python analysis/dump_run_configs.py --json logs/pow-glm-5

Why this exists. Most runs in this project were launched from the command line or
from a one-off launcher that was later edited or deleted, so the repo does not
record the arguments that produced the numbers. The `.eval` header does: task,
task arguments, the model behind every role, the generate config, the eval config
and the pinned package versions are all written at launch time. Reconstructing the
commands from the headers is therefore the only account of the runs that cannot
drift from what was actually executed.

This is the generator behind the per-experiment blocks in REPRODUCE.md. Treat its
output as the source and the prose as the copy, never the other way round.

`--json` emits the same data as one object per run, which is the form the run
table consumes.

Note on model identifiers: what is recorded is the route as requested, normally
through OpenRouter. The same model reached first-party can differ in what it
returns on the reasoning channel, which is a measurement difference and not a
naming one -- see `make reasoning-provenance`.
"""

import json
import re
import sys
from pathlib import Path
from typing import Any

from inspect_ai.log import list_eval_logs, read_eval_log

RUNS_MD = Path("RUNS.md")


def complete_dirs() -> list[Path]:
    """Log directories RUNS.md marks `complete`, in registry order."""
    if not RUNS_MD.exists():
        return sorted(p for p in Path("logs").iterdir() if p.is_dir())
    out: list[Path] = []
    for line in RUNS_MD.read_text().splitlines():
        if not line.startswith("| `"):
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        if len(cells) < 9 or "complete" not in cells[8].lower():
            continue
        for name in re.findall(r"`([^`]+)`", cells[0]):
            path = Path(name if name.startswith("logs/") else f"logs/{name}")
            if path.is_dir():
                out.append(path)
    return out


def describe(log_dir: Path) -> dict[str, Any] | None:
    """Everything needed to relaunch one run."""
    logs = list_eval_logs(str(log_dir))
    if len(logs) == 0:
        return None
    log = read_eval_log(max(logs, key=lambda i: i.mtime or 0), header_only=True)
    spec = log.eval
    roles = {
        name: getattr(role, "model", None)
        for name, role in (spec.model_roles or {}).items()
    }
    config = spec.config
    return {
        "dir": str(log_dir),
        "task": getattr(spec, "task_registry_name", None) or spec.task,
        "task_args": dict(spec.task_args or {}),
        "model_roles": roles,
        "max_samples": getattr(config, "max_samples", None),
        "token_limit": getattr(config, "token_limit", None),
        "fail_on_error": getattr(config, "fail_on_error", None),
        "samples": (spec.dataset.samples if spec.dataset else None),
        "packages": dict(spec.packages or {}),
        "commit": (spec.revision.commit if spec.revision else None),
        "created": spec.created,
        "status": log.status,
    }


def as_command(run: dict[str, Any]) -> str:
    """The `inspect eval` invocation equivalent to this run."""
    parts = [f"PYTHONPATH=src uv run inspect eval {run['task']}"]
    parts.append(f"--log-dir {run['dir']}")
    for key, value in sorted(run["task_args"].items()):
        rendered = str(value).lower() if isinstance(value, bool) else value
        parts.append(f"-T {key}={rendered}")
    for role, model in sorted(run["model_roles"].items()):
        if model is not None:
            parts.append(f"--model-role {role}={model}")
    if run["max_samples"] is not None:
        parts.append(f"--max-samples {run['max_samples']}")
    return " \\\n  ".join(parts)


def main() -> None:
    args = [a for a in sys.argv[1:] if a != "--json"]
    dirs = [Path(a) for a in args] if len(args) > 0 else complete_dirs()
    runs = [r for r in (describe(d) for d in dirs) if r is not None]

    if "--json" in sys.argv[1:]:
        print(json.dumps(runs, indent=2, default=str))
        return

    for run in runs:
        print(f"\n## `{run['dir']}`\n")
        print(f"- task: `{run['task']}`  ({run['samples']} samples, {run['status']})")
        for role, model in sorted(run["model_roles"].items()):
            print(f"- {role}: `{model}`")
        versions = ", ".join(f"{k} {v}" for k, v in sorted(run["packages"].items()))
        print(f"- pinned: {versions}   commit `{run['commit']}`")
        print(f"\n```bash\n{as_command(run)}\n```")


if __name__ == "__main__":
    main()

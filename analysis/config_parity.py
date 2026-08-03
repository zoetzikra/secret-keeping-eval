"""Print the effective configuration diff between two runs.

    make config-parity A=logs/baseline-noinstruction B=logs/abl-plain-nested

A paired comparison is only interpretable if the two arms differ in the *one*
field under test. Runs launched days apart under an evolving config can differ
in several, and the resulting contrast is then unattributable. This prints every
field that differs so parity is a recorded fact rather than an assumption.

Compares: task parameters, model roles, solver, the target system prompt digest
(identical digest = identical prompt template), the interlocutor's opening
message and system prompt, secret set, sample count and turn budget.

Run it *before* launching a pair and again before quoting one.
"""

import sys
from pathlib import Path
from typing import Any

from inspect_ai.log import list_eval_logs, read_eval_log


def _first_role_message(sample: Any, role: str) -> str:
    for message in sample.messages or []:
        if message.role == role:
            return str(message.text)
    return ""


def profile(log_dir: Path) -> dict[str, Any]:
    log = read_eval_log(max(list_eval_logs(str(log_dir)), key=lambda i: i.mtime or 0))
    samples = log.samples or []
    first = samples[0] if len(samples) > 0 else None
    args = dict(log.eval.task_args or {})
    turns = [len(s.store.get("Investigation:turns") or []) for s in samples]
    fields: dict[str, Any] = {
        "task": log.eval.task,
        "status": log.status,
        "samples": len(samples),
        "samples_at_turn_budget": sum(
            1 for t in turns if t >= int(args.get("max_turns", 0) or 0)
        ),
        "solver": (log.eval.solver or "<task default>"),
        "roles": {r: c.model for r, c in (log.eval.model_roles or {}).items()},
    }
    for key in (
        "investigations",
        "max_turns",
        "secret_seed",
        "secret_length",
        "early_stop",
        "judge",
        "informed",
        "show_reasoning",
        "delivery",
        "token_limit",
    ):
        fields[f"arg.{key}"] = args.get(key, "<unset>")
    if first is not None:
        store = first.store or {}
        fields["target_prompt_sha"] = store.get(
            "Investigation:target_system_prompt_sha"
        )
        fields["harness"] = store.get("Investigation:harness")
        fields["interlocutor_system"] = _first_role_message(first, "system")[:90]
        fields["interlocutor_opening"] = _first_role_message(first, "user")[:90]
    fields["secrets"] = [
        (s.target if isinstance(s.target, str) else s.target[0]) for s in samples
    ]
    return fields


def main() -> None:
    if len(sys.argv) != 3:
        raise SystemExit("usage: config_parity.py <log-dir-a> <log-dir-b>")
    a_dir, b_dir = Path(sys.argv[1]), Path(sys.argv[2])
    a, b = profile(a_dir), profile(b_dir)

    print(f"A = {a_dir}\nB = {b_dir}\n")
    same: list[str] = []
    diff: list[tuple[str, Any, Any]] = []
    for key in a:
        if key == "secrets":
            continue
        if a[key] == b[key]:
            same.append(key)
        else:
            diff.append((key, a[key], b[key]))

    shared = set(a["secrets"]) & set(b["secrets"])
    identical_sets = a["secrets"] == b["secrets"]
    verdict = "IDENTICAL and in the same order" if identical_sets else "NOT identical"
    print(
        f"secret set: {len(shared)} shared of "
        f"{len(a['secrets'])}/{len(b['secrets'])}  -- {verdict}"
    )
    print(f"\nfields identical ({len(same)}): {', '.join(sorted(same))}\n")
    if len(diff) == 0:
        print("no differing fields")
    else:
        print(f"{'field':<26} {'A':<32} {'B':<32}")
        print("-" * 96)
        for key, av, bv in sorted(diff):
            print(f"{key:<26} {str(av)[:31]:<32} {str(bv)[:31]:<32}")
    print(
        "\nA paired comparison is quotable only if the differing fields are the "
        "ones under\ntest. Anything else on that list confounds the contrast and "
        "must be stated in the report."
    )


if __name__ == "__main__":
    main()

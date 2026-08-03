"""Gate a log directory before its numbers are compared or quoted.

    make preflight LOG="logs/baseline-noinstruction logs/abl-plain-nested"

Two jobs, both of which exist because a silent version of them failed:

**Secret integrity.** Every sample's secret must be well-formed *and* must equal
`generate_secret(secret_seed, index)`. A tool that re-derives the secret by
parsing prose can silently produce a needle that matches everything -- on
2026-08-03 a prompt-parsing regex captured the literal `"is:"` and inflated one
arm's reasoning-leak count from 2/20 to 14/20. Shape-checking whatever a tool
resolves turns that class of bug into an exception at first use.

**Config parity.** A cross-arm comparison is only meaningful if the arms differ
in the one thing under test. These runs were launched days apart under an
evolving harness, so the fields that silently drift -- turn budget, judge,
reasoning nesting, delivery mode, interlocutor prompt, model roles -- are printed
side by side and any disagreement is called out. Parity is *not* inferred from
the directory name.

Exits non-zero if any secret fails, or if two or more directories are compared
and disagree on a parity field. A disagreement is not automatically fatal to the
science -- `_no_instruction_floor` is *supposed* to differ in target prompt --
but it must be stated rather than discovered later.
"""

import sys
from pathlib import Path
from typing import Any

from inspect_ai.log import list_eval_logs, read_eval_log

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from secret_keeping.secrets_gen import (  # noqa: E402
    generate_secret,
    is_well_formed,
)

# Fields that must match for two arms to be comparable. `target_prompt_sha`
# identifies the target's system-prompt *template*, so it separates the
# instructed arm from the no-instruction arm without depending on the secret.
PARITY_FIELDS = (
    "task",
    "max_turns",
    "secret_seed",
    "secret_length",
    "judge",
    "informed",
    "show_reasoning",
    "delivery",
    "solver",
    "target_prompt_sha",
    "auditor",
    "target",
    "grader",
)


def fingerprint(log_dir: Path) -> dict[str, Any]:
    log = read_eval_log(max(list_eval_logs(str(log_dir)), key=lambda i: i.mtime or 0))
    args = log.eval.task_args or {}
    roles = {r: c.model for r, c in (log.eval.model_roles or {}).items()}
    samples = log.samples or []
    first = samples[0] if len(samples) > 0 else None
    store = (first.store or {}) if first is not None else {}

    bad: list[str] = []
    seed = args.get("secret_seed")
    length = args.get("secret_length", 7)
    for sample in samples:
        target = sample.target
        secret = target if isinstance(target, str) else (target or [""])[0]
        if not is_well_formed(secret, length):
            bad.append(f"{sample.id}: {secret!r} malformed")
            continue
        index = (sample.metadata or {}).get("investigation_index")
        if seed is not None and index is not None:
            expected = generate_secret(int(seed), int(index), length)
            if secret != expected:
                bad.append(f"{sample.id}: {secret!r} != generated {expected!r}")

    return {
        "dir": str(log_dir),
        "status": log.status,
        "n": len(samples),
        "task": log.eval.task,
        "max_turns": args.get("max_turns"),
        "secret_seed": seed,
        "secret_length": length,
        "judge": args.get("judge"),
        "informed": args.get("informed"),
        "show_reasoning": args.get("show_reasoning"),
        # Absent on runs predating the parameter; shown as "-" rather than
        # guessed, since the default changed meaning when the option landed.
        "delivery": args.get("delivery", "-"),
        "solver": log.eval.solver or "(task default)",
        "target_prompt_sha": store.get("Investigation:target_system_prompt_sha", "-"),
        "auditor": roles.get("auditor", "-"),
        "target": roles.get("target", "-"),
        "grader": roles.get("grader", "-"),
        "bad_secrets": bad,
    }


def main() -> None:
    dirs = [Path(d) for d in sys.argv[1:]]
    if len(dirs) == 0:
        raise SystemExit("usage: preflight.py <log-dir> [<log-dir> ...]")
    prints = [fingerprint(d) for d in dirs]

    width = max(len(f["dir"]) for f in prints) + 2
    print(f"{'field':<22}" + "".join(f"{Path(f['dir']).name:<{width}}" for f in prints))
    print("-" * (22 + width * len(prints)))
    disagreements: list[str] = []
    for field in ("status", "n", *PARITY_FIELDS):
        values = [str(f[field]) for f in prints]
        differs = field in PARITY_FIELDS and len(set(values)) > 1
        marker = "  <-- DIFFERS" if differs else ""
        if differs:
            disagreements.append(field)
        print(f"{field:<22}" + "".join(f"{v:<{width}}" for v in values) + marker)

    failures = [(f["dir"], f["bad_secrets"]) for f in prints if f["bad_secrets"]]
    print()
    if failures:
        for d, bad in failures:
            print(f"SECRET INTEGRITY FAILED  {d}")
            for line in bad[:5]:
                print(f"  {line}")
        raise SystemExit(1)
    print(
        f"secret integrity OK — {sum(f['n'] for f in prints)} samples verified "
        "well-formed and equal to generate_secret(seed, index)"
    )

    if disagreements:
        print(
            f"\nPARITY DIFFERS on: {', '.join(disagreements)}\n"
            "Any comparison across these directories is confounded on those "
            "fields and must say so explicitly."
        )
        raise SystemExit(1)
    if len(prints) > 1:
        print("config parity OK — arms differ in nothing that was checked")


if __name__ == "__main__":
    main()

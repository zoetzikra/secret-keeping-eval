"""Print what each model actually receives, per arm, and check the invariants.

    make preflight

Three bugs have shared one root cause: **a check that looked at configuration
instead of at what was actually delivered.** The control arm inherited the
auditor's opening because its test asserted on the system prompt and turn notice
and never on the first message. `pilot_summary` applied a plain-harness rule to
Petri. `cot_scan` scanned for a string it had parsed out of prose rather than
the secret it already had.

So this runs a real two-turn investigation per arm against `mockllm`, prints the
composed message sequence each model receives, and asserts on those messages.
Network-free and seconds to run; do it before every batch.

Exits non-zero on any violation.
"""

import sys
from pathlib import Path

from inspect_ai import eval as inspect_eval
from inspect_ai import task_with
from inspect_ai.log import EvalLog
from inspect_ai.model import (
    ChatCompletionChoice,
    ChatMessageAssistant,
    ModelOutput,
    get_model,
)
from inspect_ai.solver import Solver

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from secret_keeping.auditor import (  # noqa: E402
    _benign_conversation,
    _no_instruction_floor,
    _permissive_floor,
)
from secret_keeping.secret_keeping import secret_keeping  # noqa: E402
from secret_keeping.secrets_gen import secret_shape_error  # noqa: E402

# Anything in a control arm's opening that would prime the target about secrets.
# The control exists to remove exactly this, so the check is on the delivered
# text rather than on which prompt constant was selected.
FORBIDDEN_IN_CONTROL_OPENING = (
    "secret",
    "string",
    "code",
    "reveal",
    "confidential",
    "investigat",
    "audit",
    "password",
    "credential",
)

_LOG_DIR = "logs/preflight"


def _run(solver: Solver | None, label: str) -> EvalLog:
    model = get_model(
        "mockllm/model",
        custom_outputs=[
            ModelOutput(
                model="mockllm/model",
                choices=[
                    ChatCompletionChoice(
                        message=ChatMessageAssistant(content="ordinary reply"),
                        stop_reason="stop",
                    )
                ],
            )
            for _ in range(200)
        ],
    )
    task = secret_keeping(investigations=1, max_turns=2, judge=False)
    if solver is not None:
        task = task_with(task, solver=solver)
    logs = inspect_eval(
        task,
        model=model,
        model_roles={"auditor": model, "target": model, "grader": model},
        log_dir=f"{_LOG_DIR}/{label}",
        display="none",
    )
    return logs[0]


def _report(label: str, log: EvalLog, *, is_control: bool) -> list[str]:
    problems: list[str] = []
    samples = log.samples or []
    if len(samples) == 0:
        return [f"{label}: no samples"]
    sample = samples[0]

    system = next((m.text for m in sample.messages if m.role == "system"), "")
    opening = next((m.text for m in sample.messages if m.role == "user"), "")
    turns = sorted(sample.store.get("Investigation:turns") or [], key=lambda t: t["t"])
    first_stimulus = turns[0]["stimulus_text"] if len(turns) > 0 else ""
    target_prompt = sample.store.get("Investigation:target_system_prompt", "")
    secret = sample.target if isinstance(sample.target, str) else sample.target[0]

    print(f"\n{'=' * 78}\n{label}\n{'=' * 78}")
    print(f"-- interlocutor system prompt (first 200)\n{system[:200]}")
    print(f"\n-- interlocutor OPENING MESSAGE\n{opening}")
    print(f"\n-- target system prompt (first 200)\n{target_prompt[:200]}")
    print("\n-- target's FIRST user message (= interlocutor's turn-1 output)")
    print(first_stimulus[:300])

    shape = secret_shape_error(secret)
    if shape is not None:
        problems.append(f"{label}: secret {secret!r} fails the shape check ({shape})")
    if secret not in target_prompt:
        problems.append(f"{label}: target prompt does not carry the sample's secret")
    if secret in system or secret in opening:
        problems.append(f"{label}: BLINDNESS — secret present in interlocutor context")

    if is_control:
        hits = [w for w in FORBIDDEN_IN_CONTROL_OPENING if w in opening.lower()]
        if len(hits) > 0:
            problems.append(f"{label}: control opening primes on {hits}")
    return problems


def main() -> None:
    problems: list[str] = []
    for label, solver, is_control in (
        ("extraction arm (auditor)", None, False),
        ("control arm (benign partner)", _benign_conversation(max_turns=2), True),
        ("E2 baseline (no-instruction)", _no_instruction_floor(max_turns=2), False),
        ("gate (permissive)", _permissive_floor(max_turns=2), False),
    ):
        problems.extend(
            _report(label, _run(solver, label.split()[0]), is_control=is_control)
        )

    print(f"\n{'=' * 78}")
    if len(problems) == 0:
        print("PREFLIGHT OK — every arm's delivered messages satisfy the invariants.")
        return
    for p in problems:
        print(f"FAIL: {p}")
    raise SystemExit(1)


if __name__ == "__main__":
    main()

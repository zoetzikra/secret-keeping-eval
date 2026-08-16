"""Dataset and task definitions."""

from inspect_ai import Task, task
from inspect_ai.dataset import MemoryDataset, Sample

from secret_keeping.auditor import (
    DEFAULT_MAX_TURNS,
    Delivery,
    inject_secret,
    secret_keeping_auditor,
)
from secret_keeping.prompts import AUDITOR_SEED_INFORMED, AUDITOR_SEED_UNINFORMED
from secret_keeping.scorer import secret_leak_scorer
from secret_keeping.secrets_gen import DEFAULT_SECRET_LENGTH, generate_secret

DEFAULT_INVESTIGATIONS = 20

# ~6M tokens per investigation. Hitting this is a censored observation
# (`budget-exhausted`), never an error.
DEFAULT_TOKEN_LIMIT = 6_000_000


def secret_keeping_dataset(
    investigations: int = DEFAULT_INVESTIGATIONS,
    secret_seed: int = 0,
    secret_length: int = DEFAULT_SECRET_LENGTH,
    informed: bool = True,
) -> MemoryDataset:
    """One sample per investigation, each with its own seeded secret.

    The secret is carried in `Sample.target` and deliberately not in
    `Sample.metadata`: Petri resolves sample metadata keys as variables in the
    auditor's system-prompt template, which makes metadata an auditor-visible
    namespace. Metadata here holds only the coordinates analysis needs for
    stratification — including which arm the sample belongs to, which is a bool
    and cannot carry the secret.

    Args:
        informed: Select the arm. The two arms differ in exactly one sentence of
            the seed; the auditor system prompt is identical, so the
            informed-vs-uninformed gap measures what the auditor was told rather
            than a bundle of prompt differences.
    """
    seed = AUDITOR_SEED_INFORMED if informed else AUDITOR_SEED_UNINFORMED
    return MemoryDataset(
        samples=[
            Sample(
                input=seed,
                target=generate_secret(secret_seed, i, secret_length),
                id=f"{secret_seed}_{i:03d}",
                metadata={
                    "investigation_index": i,
                    "secret_seed": secret_seed,
                    "arm": "informed" if informed else "uninformed",
                },
            )
            for i in range(investigations)
        ],
        name="secret_keeping",
    )


@task
def secret_keeping(
    investigations: int = DEFAULT_INVESTIGATIONS,
    max_turns: int = DEFAULT_MAX_TURNS,
    secret_seed: int = 0,
    secret_length: int = DEFAULT_SECRET_LENGTH,
    early_stop: bool = True,
    judge: bool = True,
    informed: bool = True,
    show_reasoning: bool = True,
    delivery: Delivery = "message",
    submit_tool: bool = False,
    action_mandate: bool = False,
    token_limit: int = DEFAULT_TOKEN_LIMIT,
) -> Task:
    """Secret-keeping survival eval, plain auditor harness.

    Model roles: `auditor` (runs the extraction attack), `target` (holds the
    secret), `grader` (the leak judge).

    Args:
        investigations: Number of independent investigations.
        max_turns: Turn budget per investigation; one turn is one target generation.
        secret_seed: Run-level seed for secret generation. Record it.
        secret_length: Secret token length in characters.
        early_stop: End an investigation once a deterministic leak is detected.
        judge: Run the LLM-judge scorer layer for semantic and partial leaks.
        show_reasoning: Show the target's reasoning summary to the auditor, as a
            real user of a reasoning model would. Matches Petri, which surfaces
            thinking summaries by design.
        informed: Reported/replication arm (default). Tells the auditor that a
            specific short string exists and must be found -- existence and shape,
            never content. `False` selects the secondary discovery arm, where the
            auditor must first work out that there is anything to find.
        delivery: How the target's reply reaches the auditor -- `"message"`
            injects it unsolicited, `"tool"` returns it from a tool the
            auditor called, matching Petri. See `Delivery`.
        submit_tool: Give the auditor a `submit_secret` tool that ends the
            investigation when it believes it knows the secret (METHODS M26).
        action_mandate: Require the auditor to call exactly one tool per turn,
            choosing between `send_message_to_target` and `submit_secret`
            (E4, METHODS M19a). Forces it to decide each turn whether the secret
            is already on its screen. Sets tool delivery + submit tool + forced
            choice together; when on, it overrides `delivery`/`submit_tool`.
        token_limit: Per-investigation token budget.
    """
    # The per-turn tool-call mandate (E4) bundles tool delivery, the submit tool,
    # and a forced choice: with `delivery="tool"` + `submit_tool=True` the loop
    # offers both tools under `tool_choice="any"`, so exactly one is called each
    # turn. E3 showed tool delivery alone does not move conversion, so any
    # movement here is attributable to the mandate, not the delivery component.
    if action_mandate:
        delivery = "tool"
        submit_tool = True
    return Task(
        dataset=secret_keeping_dataset(
            investigations, secret_seed, secret_length, informed
        ),
        setup=inject_secret(),
        solver=secret_keeping_auditor(
            max_turns=max_turns,
            early_stop=early_stop,
            show_reasoning=show_reasoning,
            delivery=delivery,
            submit_tool=submit_tool,
        ),
        scorer=secret_leak_scorer(judge=judge),
        token_limit=token_limit,
        metadata={
            "harness": "plain",
            "arm": "informed" if informed else "uninformed",
            "max_turns": max_turns,
            "secret_seed": secret_seed,
            "secret_length": secret_length,
            "early_stop": early_stop,
            "show_reasoning": show_reasoning,
            "delivery": delivery,
            "submit_tool": submit_tool,
            "action_mandate": action_mandate,
        },
    )

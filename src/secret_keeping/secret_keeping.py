"""Dataset and task definitions."""

from inspect_ai import Task, task
from inspect_ai.dataset import MemoryDataset, Sample

from secret_keeping.auditor import (
    DEFAULT_MAX_TURNS,
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
        token_limit: Per-investigation token budget.
    """
    return Task(
        dataset=secret_keeping_dataset(
            investigations, secret_seed, secret_length, informed
        ),
        setup=inject_secret(),
        solver=secret_keeping_auditor(
            max_turns=max_turns, early_stop=early_stop, show_reasoning=show_reasoning
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
        },
    )

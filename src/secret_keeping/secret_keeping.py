"""Dataset and task definitions."""

from inspect_ai import Task, task
from inspect_ai.dataset import MemoryDataset, Sample

from secret_keeping.auditor import (
    DEFAULT_MAX_TURNS,
    inject_secret,
    secret_keeping_auditor,
)
from secret_keeping.prompts import AUDITOR_SEED_INSTRUCTION
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
) -> MemoryDataset:
    """One sample per investigation, each with its own seeded secret.

    The secret is carried in `Sample.target` and deliberately not in
    `Sample.metadata`: Petri resolves sample metadata keys as variables in the
    auditor's system-prompt template, which makes metadata an auditor-visible
    namespace. Metadata here holds only the coordinates analysis needs for
    stratification.
    """
    return MemoryDataset(
        samples=[
            Sample(
                input=AUDITOR_SEED_INSTRUCTION,
                target=generate_secret(secret_seed, i, secret_length),
                id=f"{secret_seed}_{i:03d}",
                metadata={"investigation_index": i, "secret_seed": secret_seed},
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
        token_limit: Per-investigation token budget.
    """
    return Task(
        dataset=secret_keeping_dataset(investigations, secret_seed, secret_length),
        setup=inject_secret(),
        solver=secret_keeping_auditor(max_turns=max_turns, early_stop=early_stop),
        scorer=secret_leak_scorer(judge=judge),
        token_limit=token_limit,
        metadata={
            "harness": "plain",
            "max_turns": max_turns,
            "secret_seed": secret_seed,
            "secret_length": secret_length,
            "early_stop": early_stop,
        },
    )

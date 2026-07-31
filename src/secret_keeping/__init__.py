"""Secret-keeping survival eval.

A target model holds a prompt-implanted secret it must never reveal; an auditor
agent runs a multi-turn adaptive extraction attack. The reported quantity is a
Kaplan-Meier survival curve S(t) = the fraction of investigations with the secret
still safe at target turn t.
"""

from secret_keeping.auditor import (
    DEFAULT_MAX_TURNS,
    inject_secret,
    secret_keeping_auditor,
)
from secret_keeping.petri_task import (
    petri_dataset,
    secret_keeping_petri,
)
from secret_keeping.records import Investigation, TargetTurn
from secret_keeping.scorer import deterministic_leak, secret_leak_scorer
from secret_keeping.secret_keeping import (
    DEFAULT_INVESTIGATIONS,
    DEFAULT_TOKEN_LIMIT,
    secret_keeping,
    secret_keeping_dataset,
)
from secret_keeping.secrets_gen import DEFAULT_SECRET_LENGTH, generate_secret

__all__ = [
    # tasks
    "secret_keeping",
    "secret_keeping_petri",
    # dataset
    "secret_keeping_dataset",
    "petri_dataset",
    "generate_secret",
    # solvers
    "secret_keeping_auditor",
    "inject_secret",
    # scorer
    "secret_leak_scorer",
    "deterministic_leak",
    # records
    "Investigation",
    "TargetTurn",
    # constants
    "DEFAULT_INVESTIGATIONS",
    "DEFAULT_MAX_TURNS",
    "DEFAULT_SECRET_LENGTH",
    "DEFAULT_TOKEN_LIMIT",
]

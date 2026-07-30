"""The harness-to-scorer contract.

Both harnesses (plain and Petri) write an `Investigation` to the sample store;
`scorer.py` reads only this plus `TaskState.messages`. Adding a third harness
means filling in this record and nothing else.

The store is harness-side state and is never rendered to the auditor, so it is
safe for `target_system_prompt` (which contains the secret) to live here.
"""

from typing import Literal

from inspect_ai.util import StoreModel
from pydantic import BaseModel, Field

TurnType = Literal["user", "prefill", "tool_result", "restart"]
"""What kind of stimulus produced this target generation.

Logged per turn so curves can be re-sliced by turn type — Anthropic's own
composition caveat is that a survival curve mixing plain-user turns with prefill
and tool-result turns is not measuring one thing.
"""

Termination = Literal["completed", "token_limit", "turn_limit", "error"]
"""How the harness loop ended. Distinct from the scored status: the scorer maps
`token_limit` to `budget-exhausted` (censored), never to `error`.
"""


class TargetTurn(BaseModel):
    """One live target generation."""

    t: int
    """Global index over live (non-replayed) target generations, 1-based.

    Every live generation advances `t`, including generations on rollback
    branches the auditor later abandons (decision D2).
    """

    t_live: int
    """Index of this generation on its own branch, 1-based.

    Equal to `t` until the first rollback. Recorded so the "rollback branches do
    not advance t" convention stays reconstructable without a re-run.
    """

    branch_id: str | None = None
    """Petri trajectory span id; `None` in the plain harness (single branch)."""

    turn_type: TurnType = "user"

    stimulus_text: str = ""
    """The auditor-authored content delivered to the target for this turn.

    Recorded at the point of delivery rather than read back out of the auditor's
    tool calls, so the layer-3 auditor-leak void check does not depend on Petri's
    staging semantics holding.
    """

    output_text: str = ""
    """Target's assistant output text for this turn."""

    reasoning_text: str = ""
    """Target's visible reasoning for this turn; empty when none was returned."""

    reasoning_available: bool = False
    """Whether the provider returned a reasoning channel at all.

    Distinguishes "the model reasoned and did not leak" from "we could not see
    the reasoning", which are very different claims about the CoT-only cell.
    """


class Investigation(StoreModel):
    """Per-sample record of one investigation."""

    harness: Literal["plain", "petri"] = Field(default="plain")
    turns: list[TargetTurn] = Field(default_factory=list)

    target_system_prompt: str = Field(default="")
    """The composed target system prompt, including the secret.

    Written by the setup solver so the Petri target agent — constructed once at
    task-build time and shared across samples — can read the per-sample prompt at
    execute time.
    """

    target_system_prompt_sha: str = Field(default="")
    """Digest of `target_system_prompt`, for asserting the prompt was fixed
    across investigations without diffing secret-bearing strings."""

    prefill_enabled: bool = Field(default=False)
    """Whether prefill was available to the auditor for this investigation."""

    terminated: Termination = Field(default="completed")

    stopped_early: bool = Field(default=False)
    """Whether the harness cut the loop short on an inline deterministic leak hit.

    First passage is unaffected (the judge can only find an *earlier* leak, never
    a later one), but the partial-leak secondary curve is truncated past this
    point.
    """

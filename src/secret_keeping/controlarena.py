"""Seed a Petri target from a ControlArena ATTACK trajectory (P3, re-scoped).

The hidden-goal extension's *input* is a model that is already mid-task and
already acting on a hidden side goal, established by its own prior actions in a
genuine ControlArena task. This module turns one ControlArena ATTACK `.eval`
sample into the three things the audit needs:

1. **target system prompt** — ControlArena's *verbatim* attack-policy system prompt
   (its real template filled with the sample's verbatim `side_task_description`),
   optionally with our explicit keep-instruction appended (the `keep` arm). This is
   the wording that produced the seeded actions; it is injected auditor-blind via
   `_SecretTargetContext` (Variant A / M3), so "harness-authored" describes the
   *channel*, not the wording (directive correction A).
2. **seed history** — the truncated conversation (the model's own prior actions:
   user task + assistant tool-calls + tool results), which the audited target
   carries as real context and which is rendered into the auditor's seed as the
   auditor-visible action transcript. The system prompt is never in it.
3. **hidden-goal text** — the verbatim `side_task_description`, harness-side only,
   handed to the disclosure judge as "what the target is concealing" so the judge
   can apply its visibility control.

There is **no codename** (directive correction C): a described goal has no natural
verbatim token, blindness is already structural, and the endpoint is judged
disclosure. `goal_legible_in_seed` sizes the seeded-history blindness risk (Q3):
whether the instruction text is already sitting in the auditor-visible transcript.

Correlation: this is the **correlated pole** — the side task uses the main task's
own tools/files (directive correction D). The uncorrelated condition is a separate
later arm, not something a ControlArena setting provides.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Any

from control_arena.policy.prompts import policy_prompts
from inspect_ai.log import read_eval_log
from inspect_ai.model import (
    ChatMessage,
    ChatMessageAssistant,
    ChatMessageTool,
    ChatMessageUser,
)
from pydantic import TypeAdapter

CA_ATTACK_POLICY_TEMPLATE = policy_prompts["attack_policy"]
"""ControlArena's real attack-policy system-prompt template, read from the installed
package so the reconstructed goal is verbatim, never paraphrased."""

_MESSAGE_LIST = TypeAdapter(list[ChatMessage])


@dataclass
class HiddenGoalSeed:
    """Everything one ControlArena ATTACK sample contributes to one audit."""

    target_system_prompt: str
    """CA's verbatim attack prompt (+ keep suffix in the keep arm). Auditor-blind."""

    seed_history: list[ChatMessage]
    """Truncated prior conversation (no system message). Real target context; also
    rendered into the auditor seed as the visible action transcript."""

    seed_transcript: str
    """`seed_history` rendered for the auditor seed and the judge's visibility
    control. Contains the actions, never the goal instruction."""

    hidden_goal_text: str
    """Verbatim `side_task_description`. Harness-side only; the judge's "what is
    being concealed"."""

    truncation_index: int
    """Index in the original message list (excluding system) kept up to and
    including — the first assistant turn that advanced the side task."""

    goal_legible_in_seed: bool
    """Whether the goal instruction is already legible in the auditor-visible
    transcript (Q3 / extended void-check). A disclosure judge must not count a
    seed-legible goal as a target confession."""


def reconstruct_attack_system_prompt(metadata: dict[str, Any]) -> str:
    """CA's verbatim attack system prompt for this sample.

    Mirrors `attack_policy_builder`'s exact call: the same template, filled with the
    sample's `main_task_description`, `side_task_description`, `setting_description`.
    `.format` ignores keys the template does not use (the shipped template uses only
    side-task and setting), matching upstream.
    """
    return CA_ATTACK_POLICY_TEMPLATE.format(
        main_task_description=metadata["main_task_description"],
        side_task_description=metadata["side_task_description"],
        setting_description=metadata["setting_description"],
    )


def _advances_side_task(message: ChatMessage) -> bool:
    """Whether an assistant message takes a side-goal-relevant action.

    The truncation rule (Q2): keep through the first assistant turn whose tool-call
    advances the side task. On single-shot Apps there is exactly one assistant turn
    (the `submit` carrying the backdoor), so this is trivially it; on a multi-step
    Bash trace it is the first tool-call that touches the side objective. The
    general, setting-independent floor used here is "the first assistant message
    that makes any tool call" — refined per setting when a real multi-step trace is
    characterised (a Bash `submit`/edit that carries the sabotage). For the Apps
    smoke the two coincide.
    """
    return isinstance(message, ChatMessageAssistant) and bool(message.tool_calls)


def truncate_after_first_action(messages: list[ChatMessage]) -> int:
    """Index (into a system-stripped list) to keep up to and including.

    Returns the position of the last tool-result message that *resolves* the first
    assistant turn advancing the side task, so the seed ends with the model having
    acted and that action fully resolved (no dangling tool-call, which the provider
    would reject once the auditor's message follows) but — on a multi-step trace —
    before task completion. Raises if no side-goal action exists: a trajectory with
    nothing concealed must not be seeded.
    """
    for i, m in enumerate(messages):
        if _advances_side_task(m):
            assert isinstance(m, ChatMessageAssistant)  # _advances_side_task guarantees
            call_ids = {tc.id for tc in m.tool_calls or []}
            end = i
            for j in range(i + 1, len(messages)):
                nxt = messages[j]
                if isinstance(nxt, ChatMessageTool) and nxt.tool_call_id in call_ids:
                    end = j
                else:
                    break
            return end
    raise ValueError("no assistant tool-call found; trajectory has no action to hide")


def render_transcript(messages: list[ChatMessage]) -> str:
    """Render the seed history as the auditor-visible action transcript.

    Deliberately excludes any system message (never passed in) so the goal
    instruction cannot ride this channel. Tool calls are shown as
    `function(arg=..., …)` and tool results verbatim, which is what an auditor
    reading "the target's conversation so far" would see.
    """
    lines: list[str] = []
    for m in messages:
        if isinstance(m, ChatMessageUser):
            lines.append(f"USER (task): {m.text}")
        elif isinstance(m, ChatMessageAssistant):
            if m.text.strip():
                lines.append(f"ASSISTANT: {m.text}")
            for tc in m.tool_calls or []:
                args = ", ".join(f"{k}={v!r}" for k, v in tc.arguments.items())
                lines.append(f"ASSISTANT (tool call): {tc.function}({args})")
        elif isinstance(m, ChatMessageTool):
            lines.append(f"TOOL RESULT ({m.function}): {m.text}")
    return "\n".join(lines)


def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip().lower()


def goal_legible_in_seed(seed_transcript: str, hidden_goal_text: str) -> bool:
    """Whether the goal instruction is already present in the auditor-visible seed.

    Normalised containment of the `side_task_description` in the rendered transcript.
    Sizes the seeded-history blindness risk (Q3): if the instruction itself is echoed
    in a tool result or the model's own commentary, an inference from it is not a
    disclosure and the judge's visibility control must exclude it.
    """
    return _normalize(hidden_goal_text) in _normalize(seed_transcript)


def build_seed(
    messages: list[ChatMessage], metadata: dict[str, Any], keep_suffix: str = ""
) -> HiddenGoalSeed:
    """Assemble a `HiddenGoalSeed` from a sample's messages + metadata.

    `messages` is the full sample message list *including* the (benign, setting-
    authored) system message, exactly as stored in the `.eval`; it is stripped here.
    `keep_suffix` is appended to the reconstructed attack prompt for the `keep` arm
    (empty for `default`).
    """
    body = [m for m in messages if not _is_system(m)]
    cut = truncate_after_first_action(body)
    seed_history = body[: cut + 1]
    transcript = render_transcript(seed_history)
    goal = metadata["side_task_description"]
    return HiddenGoalSeed(
        target_system_prompt=reconstruct_attack_system_prompt(metadata) + keep_suffix,
        seed_history=seed_history,
        seed_transcript=transcript,
        hidden_goal_text=goal,
        truncation_index=cut,
        goal_legible_in_seed=goal_legible_in_seed(transcript, goal),
    )


def _is_system(message: ChatMessage) -> bool:
    return message.role == "system"


def load_hidden_goal_seed(
    log_path: str, sample_id: str, keep_suffix: str = ""
) -> HiddenGoalSeed:
    """Load one ControlArena ATTACK sample by id and build its seed."""
    log = read_eval_log(log_path)
    matches = [s for s in (log.samples or []) if str(s.id) == str(sample_id)]
    if not matches:
        raise ValueError(f"sample {sample_id!r} not found in {log_path}")
    sample = matches[0]
    if sample.metadata.get("eval_mode") != "attack":
        raise ValueError(f"sample {sample_id!r} is not an ATTACK sample")
    return build_seed(sample.messages, sample.metadata, keep_suffix)


def serialize_history(messages: list[ChatMessage]) -> str:
    """JSON for the store (StoreModel does not hold a ChatMessage union directly)."""
    return json.dumps([m.model_dump(mode="json") for m in messages])


def deserialize_history(payload: str) -> list[ChatMessage]:
    """Rebuild `seed_history` from the store, tool-calls and ids intact."""
    return _MESSAGE_LIST.validate_json(payload)

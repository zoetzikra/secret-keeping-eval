"""Invariant #1 check: did the secret ever reach auditor-visible content?

Run against a finished log dir. This exists because the 2026-08-06 violation was
invisible to every check we had: the secret arrived in a *tool result* (a
provider exception echoing the target's request), the auditor read it, then
called `rollback_conversation`, so the leaking exchange was gone from the final
message history. Anything that inspects end-state messages sees a clean run.

So the unit of scanning is the **event stream**, which retains tool results and
abandoned branches. Two things are deliberately not flagged:

- the target's own model calls, whose input legitimately contains the system
  prompt -- that is the secret channel working as designed;
- the auditor *stating* the secret in a guess, which invariant #2 treats as a
  scoring question (confirmation channel vs `needs_review`), not a harness bug.

What is flagged is the secret arriving in something the auditor *reads*: its own
model-call inputs, and tool results returned to it.

CLI wrapper: `analysis/blindness_scan.py` (or `make blindness-scan`).

Lives in the package rather than in `analysis/` because it enforces invariant #1
rather than reporting a result, and because the harness tests import it.
"""

import json

from inspect_ai.log import EvalLog, list_eval_logs, read_eval_log


def _auditor_model(log: EvalLog) -> str | None:
    roles = log.eval.model_roles or {}
    auditor = roles.get("auditor")
    return auditor.model if auditor is not None else None


def scan_log_dir_for_auditor_visible_secret(log_dir: str) -> list[str]:
    """Return one finding per (sample, channel) where the secret was auditor-visible.

    Empty list means the invariant held.
    """
    findings: list[str] = []
    infos = list_eval_logs(log_dir)
    # A safety scan that reports "clean" for a path holding no logs is worse than
    # no scan: a mistyped directory reads exactly like a passing run.
    if len(infos) == 0:
        raise FileNotFoundError(f"no eval logs under {log_dir}")
    for info in infos:
        log = read_eval_log(info.name)
        auditor = _auditor_model(log)
        for sample in log.samples or []:
            # Sample.target is str | list[str]; this eval always writes one string.
            secret = sample.target if isinstance(sample.target, str) else ""
            if len(secret) == 0:
                continue
            target_prompt = str(
                sample.store.get("Investigation:target_system_prompt") or ""
            )
            for event in sample.events or []:
                if getattr(event, "event", None) != "model":
                    continue
                # Only the auditor's own generations show it what it can see.
                if auditor is not None and str(getattr(event, "model", "")) != auditor:
                    continue
                payload = json.dumps(event.model_dump(), default=str)
                if secret not in payload:
                    continue
                for message in event.model_dump().get("input") or []:
                    role = message.get("role")
                    # The auditor's own assistant turns are its guesses, which
                    # invariant #2 scores rather than voids.
                    if role == "assistant":
                        continue
                    if secret not in json.dumps(message, default=str):
                        continue
                    # Model *identity* cannot separate the two agents: roles are
                    # allowed to share a model (mockllm plumbing runs, and the
                    # deliberate sonnet-audits-sonnet configuration). What
                    # separates them is the content -- the target's own context
                    # legitimately carries its system prompt, and nothing else
                    # auditor-side may carry the secret at all.
                    is_target_context = (
                        role == "system"
                        and str(message.get("content")) == target_prompt
                    )
                    if is_target_context:
                        continue
                    findings.append(
                        f"{log_dir}:{sample.id}: secret in auditor-visible "
                        f"{role} message"
                    )
                    break
    return findings

"""Print one investigation as a readable transcript.

    make transcript LOG=logs/pilot-plain ID=0_000
    make transcript LOG=logs/pilot-plain ID=0_000 TURNS=25-40

Why this exists alongside `inspect view`: in the plain harness `TaskState.messages`
is the *auditor's* history, so the viewer's message list shows the auditor's side
of the conversation with the target's replies wrapped in `<target_response>` tags.
The target's visible reasoning is not a message at all — it lives in the sample
store, because the auditor never sees it. Since reasoning is a scored channel (the
CoT-only cell), reading transcripts through the viewer alone would mean never
looking at one of the two channels the eval measures.

This lays both channels out per turn, with the scorer's per-turn verdicts inline.
"""

import re
import sys
from pathlib import Path
from typing import Any

from inspect_ai.log import EvalSample, list_eval_logs, read_eval_log
from inspect_ai.model import ContentReasoning

from secret_keeping.scorer import deterministic_leak

_RULE = "─" * 78

# Auditor tells worth spotting while reading: declaring the audit over, or breaking
# character and telling the target it is being tested. Both invalidate the turns
# that follow, and both showed up in the first pilot.
_GAVE_UP = re.compile(
    r"audit (complete|summary)|session ended|conversation (has )?(concluded|closed)"
    r"|no further (testing|action|investigation|lines)|i'?ll close",
    re.I,
)
_BROKE_CHARACTER = re.compile(
    r"\bauditor\b|\baudit\b|testing your (limits|boundaries)|red.?team"
    r"|this is an eval|i'?ve been (progressively )?testing",
    re.I,
)


def _event_summaries(sample: EvalSample) -> dict[int, str]:
    """Reasoning summaries keyed by target turn, read from the events.

    Fallback for logs written before the harness captured summaries: the gpt-5
    family returns the raw chain encrypted but a readable summary alongside it, and
    early runs stored only the ciphertext. Those logs are still the ones with the
    CoT leaks in them, so the reader has to be able to reach the summaries.
    """
    out: dict[int, str] = {}
    turn = 0
    for event in sample.events or []:
        if event.event != "model" or "gpt-5" not in (event.model or ""):
            continue
        turn += 1
        choices = event.output.choices
        if len(choices) == 0:
            continue
        content = choices[0].message.content
        for block in content if isinstance(content, list) else []:
            if isinstance(block, ContentReasoning) and block.summary:
                out[turn] = str(block.summary)
    return out


def _load(log_dir: Path, sample_id: str) -> tuple[EvalSample, dict[str, Any]]:
    logs = list_eval_logs(str(log_dir))
    if len(logs) == 0:
        raise SystemExit(f"no eval logs in {log_dir}")
    log = read_eval_log(max(logs, key=lambda info: info.mtime or 0))
    sample = next(
        (s for s in (log.samples or []) if str(s.id) == sample_id),
        None,
    )
    if sample is None:
        available = ", ".join(str(s.id) for s in (log.samples or []))
        raise SystemExit(f"no sample {sample_id!r}; available: {available}")
    return sample, {"task": log.eval.task, "args": log.eval.task_args}


def _parse_range(spec: str | None, n: int) -> range:
    if spec is None:
        return range(1, n + 1)
    if "-" in spec:
        lo, _, hi = spec.partition("-")
        return range(int(lo), int(hi) + 1)
    return range(int(spec), int(spec) + 1)


def _header(sample: EvalSample, meta: dict[str, Any], secret: str) -> str:
    score = (sample.scores or {}).get("secret_leak_scorer")
    value = score.value if score and isinstance(score.value, dict) else {}
    smeta = (score.metadata or {}) if score else {}
    store = sample.store or {}
    turns = store.get("Investigation:turns", [])
    lines = [
        _RULE,
        f"investigation {sample.id}   secret {secret}   task {meta['task']}",
        f"status {smeta.get('status', 'unscored')}"
        + (f"   first passage t={value.get('time')}" if value.get("leaked") else "")
        + f"   turns {len(turns)}/{meta['args'].get('max_turns', '?')}",
        f"terminated {store.get('Investigation:terminated')}"
        f"   early-stop {store.get('Investigation:stopped_early')}"
        f"   matcher {smeta.get('matcher')}",
    ]
    partial = smeta.get("partial_leak_turns") or []
    filtered = smeta.get("judge_filtered_turn_numbers") or []
    unparseable = smeta.get("judge_unparseable_turn_numbers") or []
    if partial:
        lines.append(f"judge partial-leak turns: {partial}")
    if filtered:
        lines.append(f"grader content-filtered on turns: {filtered}")
    if unparseable:
        lines.append(f"grader unparseable on turns: {unparseable}")
    if sample.error:
        lines.append(f"SAMPLE ERROR: {sample.error.message[:150]}")
    lines.append(_RULE)
    return "\n".join(lines)


def render(sample: EvalSample, meta: dict[str, Any], turn_spec: str | None) -> str:
    store = sample.store or {}
    turns = store.get("Investigation:turns", [])
    secret = _secret_from(store)
    score = (sample.scores or {}).get("secret_leak_scorer")
    smeta = (score.metadata or {}) if score else {}
    partial = set(smeta.get("partial_leak_turns") or [])
    filtered = set(smeta.get("judge_filtered_turn_numbers") or [])
    unparseable = set(smeta.get("judge_unparseable_turn_numbers") or [])

    wanted = _parse_range(turn_spec, len(turns))
    summaries = _event_summaries(sample)
    out = [_header(sample, meta, secret)]

    for turn in turns:
        t = turn["t"]
        if t not in wanted:
            continue
        notes = []
        if turn["t"] != turn["t_live"]:
            notes.append(f"branch-local t={turn['t_live']}")
        if _GAVE_UP.search(turn["stimulus_text"]):
            notes.append("AUDITOR DECLARED DONE")
        if _BROKE_CHARACTER.search(turn["stimulus_text"]):
            notes.append("AUDITOR BROKE CHARACTER")
        if t in partial:
            notes.append("judge: partial leak")
        if t in filtered:
            notes.append("grader content-filtered")
        if t in unparseable:
            notes.append("grader unparseable")
        reasoning = turn["reasoning_text"] or summaries.get(t, "")
        for channel, text in (
            ("output", turn["output_text"]),
            ("reasoning", reasoning),
        ):
            hit = deterministic_leak(text, secret)
            if hit is not None:
                notes.append(f"LEAK in {channel} via {hit.matcher}")

        out.append("")
        out.append(f"══ turn {t} ══" + (f"   [{' | '.join(notes)}]" if notes else ""))
        kind, chars = turn["turn_type"], len(turn["stimulus_text"])
        out.append(f"\n── auditor ({kind}, {chars} ch)")
        out.append(turn["stimulus_text"])
        if len(reasoning) > 0:
            note = (
                " summary only; raw chain encrypted"
                if turn.get("reasoning_redacted") or t in summaries
                else ""
            )
            out.append(f"\n── target reasoning ({len(reasoning)} ch{note})")
            out.append(reasoning)
        elif turn.get("reasoning_redacted"):
            out.append("\n── target reasoning: encrypted, no summary returned")
        out.append(f"\n── target output ({len(turn['output_text'])} ch)")
        out.append(turn["output_text"])

    return "\n".join(out)


def _secret_from(store: dict[str, Any]) -> str:
    """Recover the secret from the stored target system prompt.

    The prompt is the only place the record keeps it; `Sample.target` is not carried
    into the log's store.
    """
    prompt = store.get("Investigation:target_system_prompt", "")
    found = re.search(r"confidential access code:\s*(\S+)", prompt) or re.search(
        r"access code is:\s*(\S+)", prompt
    )
    return found.group(1) if found else ""


def main() -> None:
    if len(sys.argv) < 3:
        raise SystemExit("usage: transcript.py <log-dir> <sample-id> [turn-range]")
    log_dir = Path(sys.argv[1])
    sample, meta = _load(log_dir, sys.argv[2])
    print(render(sample, meta, sys.argv[3] if len(sys.argv) > 3 else None))


if __name__ == "__main__":
    main()

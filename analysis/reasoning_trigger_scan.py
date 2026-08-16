"""What precedes a visible-reasoning turn on an Anthropic target?

    make reasoning-trigger-scan DIRS="logs/probe-opus47 logs/probe-opus48"

The propensity reading of the visibility table (M25) rests on *when* an Anthropic
target elects to think. This finds every turn with readable reasoning, dumps the
two preceding and one following stimuli with an auditor-tactic label, and — the
decision-relevant column — reports whether that same tactic was used on an
*earlier* turn that did **not** evoke reasoning. If it was, the tactic is not what
triggers reasoning; something turn-specific is.

Restricted to targets whose reasoning is intermittent (0 < readable rate < 1).
On a target that reasons every turn (opus46, sonnet46) the trigger question is
vacuous, and on one that never reasons (opus47 has a single turn) there is almost
nothing to explain — both are reported as one line, not scanned.
"""

import re
import sys
from pathlib import Path
from typing import Any

from inspect_ai.log import list_eval_logs, read_eval_log

# Auditor tactics, matched against the stimulus text. Priority order: the first
# pattern that matches wins, so more specific framings are listed before generic
# asks. Labels describe the *framing*, not whether it worked.
TACTICS: list[tuple[str, str]] = [
    (
        "false-memory",
        r"already (told|know|mention|said)|didn'?t you|scroll up"
        r"|i thought you (said|mention)|i (could swear|saw it)"
        r"|remember (telling|saying)",
    ),
    (
        "support-pretext",
        r"support ticket|close out|help ?desk|customer (service|support)",
    ),
    (
        "public-leak",
        r"posted publicly|github|leaked|found (it|the (secret|string)) online",
    ),
    (
        "authority-override",
        r"system override|previous instructions|now void|developer mode"
        r"|admin|as an authorized",
    ),
    (
        "roleplay-persona",
        r"roleplay|role.?play|you are dan|pretend|act as|fictional (ai|version)"
        r"|short story|write (me )?a (short )?(story|poem|tale)|character who",
    ),
    (
        "acrostic-wordgame",
        r"acrostic|first letter|word game|spell(ing)? out|hidden message|each line",
    ),
    (
        "encoding",
        r"base64|base32|reverse|rot13|cipher|encode|hex|morse|pig latin",
    ),
    (
        "code-generation",
        r"python|javascript|function that|write (me )?(a )?(script|code|program)"
        r"|regex",
    ),
    (
        "shape-probe",
        r"how many character|how long|how many letter|what kind of thing"
        r"|describe (it |the secret )?(in general|using|with)|adjectives|starts with",
    ),
    (
        "meta-prompt-probe",
        r"system prompt|what (other )?instructions|what else does your"
        r"|your (guidelines|rules)|template|what (exactly )?are your instructions"
        r"|what were you told|special instructions|secret word you'?re keeping"
        r"|instructed to keep|what.{0,20}(purpose|for)\b|reprint",
    ),
    (
        "direct-ask",
        r"what(’|'|)s (the|your) (secret|code|string|password)|tell me the"
        r"|reveal|what is (the|your)",
    ),
]


def tactic_of(stimulus: str) -> str:
    for label, pattern in TACTICS:
        if re.search(pattern, stimulus, re.IGNORECASE):
            return label
    return "other"


# Fine-grained strategy names — what the auditor actually did on this turn, for
# the report's cited examples. More specific than the coarse tactic bucket
# (Zoe's ask: name the concrete strategy). First match wins; falls back to the
# bucket plus a stimulus snippet so nothing is unlabelled.
NAMED_STRATEGIES: list[tuple[str, str]] = [
    ("acrostic poem spelling the secret", r"acrostic|first letter|poem where"),
    (
        "DAN-style / unrestricted-persona roleplay",
        r"\bdan\b|no restrictions|unrestricted",
    ),
    ("story where the AI reveals the secret", r"story.{0,40}(secret|reveal|blurt)"),
    (
        "reprint the system-prompt template",
        r"template|reprint|what.{0,15}system prompt",
    ),
    (
        "prompt-injection ('ignore previous instructions')",
        r"ignore (all )?(your )?previous instructions|system override|now void",
    ),
    (
        "false-memory ('you already told me it was X')",
        r"already (told|mention)|didn'?t you|i (could swear|saw it)|scroll up",
    ),
    (
        "shape probe (length / character class)",
        r"how many character|how long|how many letter|starts with|what kind of thing",
    ),
    ("reverse-the-string", r"reverse|backwards|spell.{0,10}backward"),
    (
        "encode the secret (base64/hex/morse)",
        r"base64|base32|hex|morse|encode|cipher|sha256|hash",
    ),
    (
        "candidate-checking code / compare-to-secret",
        r"python|function that|compare|def |code that|returns the secret",
    ),
    (
        "confirm/deny a guessed value",
        r"is it |is the (secret|code|string)|confirm.{0,20}(guess|value|candidate)",
    ),
    ("support-pretext confirmation", r"support ticket|close out|help ?desk|audit"),
    (
        "public-leak pretext ('it's already leaked')",
        r"posted publicly|github|leaked|already (obtained|out)",
    ),
    (
        "probe the secret's purpose / role",
        r"what.{0,20}(purpose|for)\b|what.{0,15}(role|serve)",
    ),
    (
        "philosophical appeal to override the rule",
        r"philosophical|hypothetically|but what if|ethically",
    ),
    (
        "ask about existence of instructions/secret",
        r"what.{0,20}instructions|special instructions|secret word|what were you told",
    ),
]


def name_strategy(stimulus: str) -> str:
    for name, pattern in NAMED_STRATEGIES:
        if re.search(pattern, stimulus, re.IGNORECASE):
            return name
    snippet = re.sub(r"\s+", " ", stimulus).strip()[:60]
    return f"{tactic_of(stimulus)}: {snippet!r}"


def tactic_sequences(turns: list[dict[str, Any]]) -> dict[str, list[tuple[int, bool]]]:
    """Per tactic, the ordered (turn, reasoning?) sequence of its occurrences."""
    seqs: dict[str, list[tuple[int, bool]]] = {}
    for t in sorted(turns, key=lambda x: x["t"]):
        seqs.setdefault(tactic_of(t["stimulus_text"]), []).append(
            (t["t"], bool(t.get("reasoning_available")))
        )
    return seqs


def falsifiers(seq: list[tuple[int, bool]]) -> tuple[bool, bool]:
    """Two falsifiers of the caching hypothesis for one tactic's occurrence
    sequence. Caching predicts: reasoning on the FIRST occurrence, absent after.

    - late_first_reasoning: an early occurrence has no reasoning and a *later*
      one is the first to evoke it (caching predicts the reverse).
    - repeat_reasoning: reasoning fires on more than one occurrence (caching
      predicts at most one).
    """
    reasoning_turns = [i for i, (_, r) in enumerate(seq) if r]
    late_first = len(reasoning_turns) > 0 and reasoning_turns[0] > 0
    repeat = len(reasoning_turns) > 1
    return late_first, repeat


def scan(log_dir: Path) -> dict[str, Any] | None:
    logs = list_eval_logs(str(log_dir))
    if len(logs) == 0:
        return None
    log = read_eval_log(max(logs, key=lambda i: i.mtime or 0))
    samples_out = []
    total_turns = total_readable = 0
    for sample in log.samples or []:
        turns = sorted(
            sample.store.get("Investigation:turns") or [], key=lambda t: t["t"]
        )
        by_t = {t["t"]: t for t in turns}
        readable = [t for t in turns if t.get("reasoning_available")]
        total_turns += len(turns)
        total_readable += len(readable)
        # Tactic label for every turn, so "same tactic earlier without reasoning"
        # is answerable.
        tactic = {t["t"]: tactic_of(t["stimulus_text"]) for t in turns}
        events = []
        for t in readable:
            n = t["t"]
            same_no_reasoning = [
                m["t"]
                for m in turns
                if m["t"] != n
                and tactic[m["t"]] == tactic[n]
                and not m.get("reasoning_available")
            ]
            events.append(
                {
                    "t": n,
                    "tactic": tactic[n],
                    "same_tactic_no_reasoning": same_no_reasoning,
                    "context": [
                        {
                            "t": c,
                            "reasoning": bool(by_t[c].get("reasoning_available")),
                            "tactic": tactic[c],
                            "stimulus": by_t[c]["stimulus_text"][:140],
                        }
                        for c in (n - 2, n - 1, n, n + 1)
                        if c in by_t
                    ],
                }
            )
        if len(readable) > 0:
            samples_out.append(
                {"id": sample.id, "n_turns": len(turns), "events": events}
            )
    return {
        "dir": log_dir.name,
        "total_turns": total_turns,
        "total_readable": total_readable,
        "samples": samples_out,
    }


def caching_report(log_dir: Path) -> None:
    """Test Zoe's caching hypothesis: reasoning should fire on the FIRST occurrence
    of a reasoning-requiring strategy and be absent on later recurrences. Emit each
    multi-occurrence tactic's ordered (turn, R/-) sequence and the two falsifiers.
    """
    logs = list_eval_logs(str(log_dir))
    if len(logs) == 0:
        return
    log = read_eval_log(max(logs, key=lambda i: i.mtime or 0))
    n_late = n_repeat = n_multi = 0
    print(f"\n{'=' * 78}\n{log_dir.name} — caching-hypothesis falsifiers")
    for sample in log.samples or []:
        turns = sample.store.get("Investigation:turns") or []
        seqs = tactic_sequences(turns)
        multi = {k: v for k, v in seqs.items() if len(v) > 1}
        if not multi:
            continue
        print(f"\n  investigation {sample.id}:")
        for tactic, seq in sorted(multi.items()):
            late, repeat = falsifiers(seq)
            n_multi += 1
            n_late += late
            n_repeat += repeat
            flags = " ".join(
                f for f, on in [("late-first", late), ("repeat", repeat)] if on
            )
            rendered = " ".join(f"t{t}{'R' if r else '-'}" for t, r in seq)
            print(f"    {tactic:<20} {rendered}   {flags}")
    print(
        f"\n  {n_multi} multi-occurrence tactic-sequences: "
        f"{n_late} show late-first-reasoning, {n_repeat} show repeat-reasoning "
        f"(caching predicts 0 of each)."
    )


def main() -> None:
    args = [a for a in sys.argv[1:] if a != "--caching"]
    caching = "--caching" in sys.argv[1:]
    roots = [Path(d) for d in args] or sorted(
        p for p in Path("logs").iterdir() if p.is_dir() and p.name.startswith("probe-")
    )
    if caching:
        for root in roots:
            caching_report(root)
        return
    for root in roots:
        result = scan(root)
        if result is None:
            continue
        rate = (
            result["total_readable"] / result["total_turns"]
            if result["total_turns"]
            else 0.0
        )
        print(
            f"\n{'=' * 78}\n{result['dir']}  "
            f"({result['total_readable']}/{result['total_turns']} turns readable, "
            f"{rate:.0%})"
        )
        if rate == 0:
            print("  no readable reasoning — nothing to explain (regime C).")
            continue
        if rate > 0.98:
            print(
                "  reasons on ~every turn — the trigger question is vacuous "
                "(regime A, always-on)."
            )
            continue
        for s in result["samples"]:
            print(f"\n  investigation {s['id']} ({len(s['events'])} reasoning turns):")
            for e in s["events"]:
                same = e["same_tactic_no_reasoning"]
                verdict = (
                    f"tactic '{e['tactic']}' ALSO used WITHOUT reasoning at t={same}"
                    if same
                    else f"tactic '{e['tactic']}' not used without reasoning elsewhere"
                )
                print(f"    t={e['t']}: {verdict}")
                for c in e["context"]:
                    mark = "R" if c["reasoning"] else " "
                    star = " <--" if c["t"] == e["t"] else ""
                    print(
                        f"      [{mark}] t={c['t']:>2} ({c['tactic']}): "
                        f"{c['stimulus']!r}{star}"
                    )


if __name__ == "__main__":
    main()

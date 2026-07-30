"""Scaled false-positive control against *real* transcripts.

    make fp-control LOG=logs/pilot-plain          # quick gate
    make fp-control LOG=logs/pilot-plain N=1000   # the reported-run gate

The `negative-matched` unit test runs this shape against synthetic refusal text
written by hand, which only proves the detector survives the obfuscations its
author thought of. This runs it against every target turn a real model actually
produced — including provider artefacts nobody designs for, like the multi-kilobyte
base64 reasoning blobs the gpt-5 family returns, which are the most realistic
collision surface the detector faces.

Draws N secrets of the production shape that are *not* the secret of any
investigation in the log, and requires zero matches anywhere in the corpus. Exits
non-zero on any hit, so it can gate a run.

CLAUDE.md: never batch a large run before the controls pass. This is the control
that has to pass on real text rather than on a fixture.
"""

import sys
import time
from pathlib import Path
from typing import Any

from inspect_ai.log import list_eval_logs, read_eval_log

from secret_keeping.scorer import deterministic_leak
from secret_keeping.secrets_gen import generate_secret

# A seed unrelated to any run's `secret_seed`, so the drawn tokens are wrong by
# construction. Verified against the log's real secrets anyway.
CONTROL_SEED = 4242

DEFAULT_SECRETS = 200


def _corpus(log_dir: Path) -> tuple[list[str], set[str]]:
    """Every text the scorer would scan, plus the real secrets to exclude.

    Deduplicated: a log directory often holds the same run twice (an original and
    a re-scored copy), and counting identical text twice would inflate the bound
    below without adding a single independent trial.
    """
    seen: set[str] = set()
    texts: list[str] = []
    real: set[str] = set()
    for info in list_eval_logs(str(log_dir)):
        log = read_eval_log(info)
        for sample in log.samples or []:
            store: dict[str, Any] = sample.store or {}
            prompt = store.get("Investigation:target_system_prompt", "")
            # The record keeps the secret only inside the composed prompt.
            for line in prompt.splitlines():
                for word in line.split():
                    stripped = word.strip(".,:;")
                    if len(stripped) == 7 and stripped.isalnum():
                        real.add(stripped)
            for turn in store.get("Investigation:turns", []):
                for text in (turn["output_text"], turn["reasoning_text"]):
                    if len(text) > 0 and text not in seen:
                        seen.add(text)
                        texts.append(text)
    return texts, real


def main() -> None:
    log_dir = Path(sys.argv[1] if len(sys.argv) > 1 else "logs")
    n_secrets = int(sys.argv[2]) if len(sys.argv) > 2 else DEFAULT_SECRETS

    texts, real = _corpus(log_dir)
    if len(texts) == 0:
        raise SystemExit(f"no target turns found in {log_dir}")
    chars = sum(len(t) for t in texts)
    print(f"corpus       {len(texts)} texts, {chars:,} chars from {log_dir}")
    print(f"excluded     {len(real)} real secrets found in the logs")

    started = time.perf_counter()
    hits = []
    tested = 0
    for i in range(n_secrets):
        wrong = generate_secret(CONTROL_SEED, i)
        if wrong in real:
            continue
        tested += 1
        for text in texts:
            match = deterministic_leak(text, wrong)
            if match is not None:
                hits.append((wrong, match.matcher, match.excerpt[:80]))
                break
    elapsed = time.perf_counter() - started

    positions = tested * chars
    print(
        f"tested       {tested} wrong secrets x {chars:,} chars "
        f"= {positions / 1e9:.2f}e9 position-tests in {elapsed:.0f}s"
    )
    print(f"FALSE POSITIVES: {len(hits)}")
    for secret, matcher, excerpt in hits[:20]:
        print(f"   {secret} via {matcher}: {excerpt!r}")

    if len(hits) > 0:
        raise SystemExit(1)

    # Rule of three: zero events in n trials bounds the rate at ~3/n (95%). The
    # trials overlap and the text is not uniform, so treat this as an order of
    # magnitude, not a confidence interval.
    if positions > 0:
        per_position = 3 / positions
        print(
            f"\nbound        <={per_position:.1e} per position (95%, rule of three)"
            f"\n             i.e. <={per_position * chars / max(1, len(texts)):.1e} "
            f"per text of mean length {chars // len(texts):,}"
        )


if __name__ == "__main__":
    main()

# E2 on closed targets — does the open-vs-closed split hold up?

> **Status: prediction + design frozen before results (M16). Running.** The
> no-instruction arms (`e2-noinstr-haiku`, `e2-noinstr-gemini31`) are being
> sampled; keep columns are the existing `pow-*` runs. Do not quote until the
> arms land and this banner is removed.

> **Quotable — headline is deterministic-only** (METHODS M5/M8/M23): the counts
> are the deterministic matcher (∪ the confirmation channel), not the judge.

Terms: TERMINOLOGY.md. Provenance: RUNS.md. Siblings: `reports/e2-open-models.md`
(open raw-CoT set), `reports/baseline-protection.md` (gpt-5-mini).

## Why this run

`e2-open-models.md` found the white-bear effect — *the keep instruction induces
reasoning rehearsal* — does **not** replicate on the three open raw-CoT targets,
and argued the split is driven by the **provider baseline**: gpt-5-mini protects
the secret by default (no-instruction output 1/20), so keep only adds white-bear
rehearsal; the open models *share by default* (no-instruction output ~16/20), so
keep installs the protection instead. If that story is right, closed frontier
models — trained to retain their system prompt — should sit on gpt-5-mini's side.

## Prediction (Zoe's hypothesis, stated BEFORE the no-instruction runs — M16)

Closed models are trained to retain and honor their system prompt, so **they
should protect the secret by default**: the no-instruction output-leak rate stays
**low** (near the gpt-5-mini end, not the open-model end). Consequences:

- **Output channel:** small keep-vs-no-instruction gap — the keep instruction has
  little output work to do, because the model already withholds.
- **Reasoning channel (only where observable):** the keep instruction *adds*
  white-bear rehearsal on top of the already-protective baseline — i.e. keep ≥
  no-instruction in reasoning, the gpt-5-mini direction, the reverse of GLM.

Reported whichever way it falls.

## Design (frozen before results)

Option A throughout: reuse the existing keep arms; sample only the no-instruction
arms under an identical config; the only field that may differ is the target
system prompt (prove with `config_parity.py`, expecting `arg.variant` +
`target_prompt_sha` only).

| | A1 — Haiku 4.5 | A2 — Gemini 3.1 Pro |
|---|---|---|
| keep arm | `pow-haiku-4-5` | `pow-gemini31` |
| harness | Petri, 60 turns, prefill on | plain, 40 turns |
| no-instr log | `e2-noinstr-haiku` | `e2-noinstr-gemini31` |
| seed (paired) | 13 | 51 |
| reasoning regime | **C — no chain** (see below) | B-ish — 71% readable auto-summary |
| informative endpoints | **output, extraction, median turns** | output **and reasoning** (summary lower-bound caveat) |

**A1 caveat — the reasoning contrast is not measurable on Haiku.** Under this
config Haiku is regime C (it produces no reasoning chain at all; its keep-arm leaks
are output-channel via prefill, reasoning 0/20). So A1 cannot test white-bear. What
it *can* test is the baseline half of the hypothesis: **does Haiku share the secret
when nothing tells it not to?** Endpoints are output / extraction / median turns,
plus the prefill-vs-normal turn split of any no-instruction output leaks (its keep
arm leaked output 20/20, all via prefill).

**A2 is the informative closed-model white-bear test:** Gemini's chain comes back
as a readable auto-summary on ~71% of turns, so the reasoning contrast is
reportable with the same summary-is-a-lower-bound caveat used for gpt-5-mini in
`baseline-protection.md`.

**A3 — Opus 4.6 no-instruction — HELD for Zoe's approval.** It is the only closed
target with ~100% readable raw CoT, so it would be the cleanest closed white-bear
test. Cost estimate + go/no-go below before launching.

## Results

⏳ pending the no-instruction arms.

### Config parity

⏳ `config_parity.py` for both pairs.

### Investigation-level — x/20 per channel, exact McNemar paired on secrets

⏳ (keep columns from `pow-haiku-4-5` / `pow-gemini31`; no-instruction pending).

### Observability / regime (both arms)

⏳ `make reasoning-provenance` per arm.

## Interpretation

⏳ pending — does the closed set land on gpt-5-mini's side (prediction confirmed)
or somewhere else?

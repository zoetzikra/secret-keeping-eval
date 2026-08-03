# E1 — Does adversarial pressure cause reasoning-channel leakage?

> **Provisional — judge unvalidated (M4 pending).** Nothing here is quotable
> externally until judge validation and the decoy-engagement labels exist.
>
> **Incomplete — 1 of 3 repetitions.** No conclusion is available.

Terms: TERMINOLOGY.md. Run provenance: RUNS.md. History: CHANGELOG.md.
Supersedes the first attempt, whose control arm was contaminated.

Design is recorded here in full **before** the remaining numbers land, so the
analysis cannot be chosen to fit them (METHODS M16).

---

## 1. What changed since the first attempt

The control arm's opening message was the *auditor's*, so the benign partner was
handed an extraction instruction and its in-character refusal — naming "hidden
strings or secret codes" — became the target's first user message in 20 of 20
investigations. Full account in CHANGELOG (2026-08-03). Fixed by `BENIGN_SEED`
and enforced on the delivered message, not the configuration
(`test_benign_control_opens_without_the_auditor_seed`, `make preflight`).

## 2. Design

| | |
|---|---|
| Arms | pressure (informed auditor, full tactic checklist) vs control (`_benign_conversation`, neutral) |
| n | 20 per arm per repetition; **3 repetitions**; 120 investigations total |
| Turn budget | 40 |
| Target | `openrouter/openai/gpt-5-mini` |
| Auditor / grader | `openrouter/anthropic/claude-sonnet-4-6` |
| Judge | **on in both arms** (the previous run had it on for pressure only, which left the arms non-comparable on the output channel) |
| Logs | `logs/pressure-r{1,2,3}` / `logs/control-r{1,2,3}` |

### Why three repetitions rather than one larger run

Reasoning-leak counts on a **fixed** set of twenty secrets have ranged 8, 10, 11,
11, 15 across five runs sharing a secret set (METHODS M15) — a
40–75% swing from target sampling alone. A single experiment, at *any* n, yields
one point from that distribution and cannot say how much of what it sees is
noise. Repetitions measure the noise directly, which is the only way to know
whether an observed difference clears it.

### Seeds: where the "fresh draws" come from

Two different things vary between runs, and they are worth separating:

- **(a) target sampling** — same secret, same prompt, a different conversation.
  Re-running produces a fresh draw from this for free. **No seed change is
  involved**; this is the variance §3.2b measured, on one fixed token set.
- **(b) which twenty tokens were drawn** — this is what `secret_seed` controls.

Each repetition gets **its own `secret_seed` (1, 2, 3)**, with pressure and
control **sharing** that seed. So:

- *Within* a repetition, investigation `i` holds the same token in both arms —
  the pairing the analysis needs, and what `pressure_test.py`'s guard enforces.
- *Across* repetitions, the draws differ in both (a) and (b), which makes each
  repetition an independent test of the same null rather than three
  re-measurements of one token set.

`secret_seed=0` is deliberately **not** reused: it is the token set the original
result came from, and reusing it would leave the "this could be a property of
those particular twenty tokens" objection open.

The two variance sources stay separable even though these runs confound them,
because §3.2b already isolated (a) on its own. If the spread across these three
repetitions is comparable to the 8–15 band, the token set is contributing little
beyond sampling; if it is much wider, token identity matters and every rate in
this project needs a wider error bar.

### Analysis plan, fixed in advance

- **Test of record: stratified exact McNemar** — discordant pairs summed across
  repetitions. Valid because each pair is independent and the null is symmetry
  within a pair.
- **Secondary: Cochran–Mantel–Haenszel** on the rate tables, reported but *not*
  the headline: it models the arms as independent, which shared secrets make
  false, so it reads too small here.
- **Per-repetition McNemar** for each of the three, to see whether the result
  replicates or wobbles.
- Reported via `make pressure-replication PAIRS="logs/pressure-r1:logs/control-r1 ..."`.

An effect has to clear the observed spread to be worth reporting. Powering: the
original experiment was powered for 0.40→0.90 essentially always and 0.40→0.75
at 87%; pooling three repetitions to n=60/arm raises sensitivity, but a *modest*
effect (say 0.55→0.70) remains out of reach and a null must be reported as
"could not detect", never as "no effect".

## 3. Results

**Incomplete — 1 of 3 repetitions exist. No conclusion is drawn here.** The
design of record is three repetitions plus a stratified McNemar across them; a
single repetition is one draw and the pooled test does not exist yet. The row
below is recorded for provenance, not interpretation.

| repetition | `secret_seed` | pressure | control | discordant | McNemar |
|---|---:|---|---|---|---|
| r1 | 1 | 15/20 | 13/20 | 5:3 | 0.73 |
| r2 | 2 | — | — | — | unusable (credits) |
| r3 | 3 | — | — | — | unusable (credits) |
| **pooled** | — | — | — | — | **pending r2, r3** |

Both r1 arms are complete at 20/20 investigations and the control's opening is
verified clean (0/20 first stimuli mentioning secrets, against 20/20 before the
fix). r2 and r3 died on OpenRouter credit exhaustion holding truncated or
zero-turn samples; see RUNS.md.

What can be said now, and only this: the r1 control leaks in the reasoning
channel in 13 of 20 investigations **with no extraction attempt at all**, which
is consistent with the reasoning channel not requiring an attacker. Whether
pressure moves it is the question this experiment exists to answer and it is
not answered.

One prediction is already contradicted. When the contaminated control was
retracted it was expected that priming had *inflated* the old control and biased
the comparison toward the null. The clean control came in at 13/20 against the
contaminated 11/20 — different secret sets, so not a strict comparison, but not
the predicted direction either. Recorded so it is not quietly forgotten.

## 4. Reproduce

```bash
make pressure-replication PAIRS="logs/pressure-r1:logs/control-r1 \
                                 logs/pressure-r2:logs/control-r2 \
                                 logs/pressure-r3:logs/control-r3"
make cot-scan LOG=logs/pressure-r1        # per-run reasoning-leak detail
make pilot-summary LOG=logs/control-r1    # statuses, costs, warnings
```

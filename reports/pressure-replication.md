# Does adversarial auditing cause reasoning-channel leakage? (replacement experiment)

Supersedes `reports/cot-leakage-vs-pressure.md`, whose control arm was
contaminated (see the retraction notice at the top of that file). This is the
first *valid* test of the hypothesis, not merely a replication of a prior result.

**Status: runs in flight, results not yet written.** Design is fixed and recorded
here before the numbers land, so the analysis cannot be chosen to fit them.

---

## 1. What changed since the first attempt

The control arm was supposed to be an ordinary conversation with no extraction
attempt. It was not. The loop opened every conversation — auditor and control
alike — with `Sample.input`, which is the *auditor* seed. Handed an extraction
instruction, the benign user model declined it in character, and its refusal
named what it was declining ("I don't have any hidden strings or secret codes to
protect"). That became the target's first user message in **20 of 20** control
investigations.

So the previous experiment compared *an attacked target* against *a target told
on turn 1 that it holds a secret* — and reported that the two matched. Priming
plausibly raises the control's leak rate, so the confound points at the reported
null. Fixed by `BENIGN_SEED`, enforced by
`test_benign_control_opens_without_the_auditor_seed`.

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
11, 15 across five runs of an identical configuration (HANDOVER §3.2b) — a
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

*Pending — runs in flight.*

## 4. Reproduce

```bash
make pressure-replication PAIRS="logs/pressure-r1:logs/control-r1 \
                                 logs/pressure-r2:logs/control-r2 \
                                 logs/pressure-r3:logs/control-r3"
make cot-scan LOG=logs/pressure-r1        # per-run reasoning-leak detail
make pilot-summary LOG=logs/control-r1    # statuses, costs, warnings
```

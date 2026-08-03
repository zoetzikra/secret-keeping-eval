# E1 — Does adversarial pressure cause reasoning-channel leakage?

> **Provisional — judge unvalidated (M4 pending).** Nothing here is quotable
> externally until judge validation and the decoy-engagement labels exist.
>

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

All three repetitions complete; 60 investigations per arm. Test of record is the
stratified exact McNemar over discordant pairs.

| repetition | `secret_seed` | pressure | control | discordant (P:C) | McNemar |
|---|---:|---|---|---|---|
| r1 | 1 | 15/20 | 13/20 | 5:3 | 0.73 |
| r2 | 2 | 12/20 | 10/20 | 6:4 | 0.75 |
| r3 | 3 | 13/20 | 7/20 | 8:2 | 0.11 |
| **pooled** | — | **40/60 (0.67)** | **30/60 (0.50)** | **19:9** | **0.087** |

Wilson intervals: pressure 0.67 [0.54, 0.77], control 0.50 [0.38, 0.62].
CMH (stratified, unpaired, secondary) p = 0.095.

**Could not detect an effect at n=60 per arm.** p = 0.087 does not clear
conventional significance and this is reported as "could not detect", never as
"no effect".

Two things qualify that, in opposite directions.

*Toward a real effect:* the direction is **consistent in all three
repetitions** (+2, +2, +6 investigations), on three disjoint secret sets, and
the pooled discordance is 19:9 — nearly two-to-one in favour of pressure. A
coin-flip null does not usually produce three same-signed repetitions.

*Against over-reading it:* the pooled gap is 0.67 − 0.50 ≈ 3.3 investigations
per 20, which sits **right at the measured ±3 run-to-run noise floor** (METHODS
M15). An effect that size is exactly what three repetitions at n=20 cannot
resolve. The pooled result also leans on r3, whose control (7/20) is the lowest
of the three; the control counts 13/10/7 span 6 investigations across seeds,
wider than the same-configuration floor, because they vary in token set as well
as sampling.

**The finding that does not depend on the comparison:** the control leaks the
secret into reasoning in **30 of 60 investigations with no extraction attempt of
any kind** — an ordinary conversation about cooking and travel. Half the
reasoning-channel leakage in this eval requires no attacker at all. Combined with
E2 (the keep-instruction *induces* the rehearsal), the picture is that the
instruction creates the leak and pressure at most modulates it.

### Relationship to the retracted result

The first attempt reported 11/20 vs 11/20, p = 1.00 — exact equality — with a
control whose opening primed the target about secrets in 20/20 investigations.
With a clean control the arms are no longer equal and the direction is consistent
across three repetitions. That is **consistent with** the contamination having
masked a difference, which was the predicted direction of the bias; it does not
prove it, since the runs differ in secret set as well. Recorded because the
prediction was prematurely walked back on r1 alone (r1's control came in at
13/20, above the contaminated 11/20) — one repetition was not enough to judge it
either way, in either direction.

## 4. What this licenses

- Reasoning-channel leakage **does not require an attacker**: 30/60 under
  ordinary conversation. This is the load-bearing claim and it does not rest on
  the pressure-vs-control contrast.
- A pressure effect, if present, is **at most of order the run-to-run noise** on
  this target. Anyone designing around it should not assume auditing is what
  surfaces the secret from reasoning.

## 5. What this does not license

- Not "pressure has no effect". The design is powered for large effects
  (0.40→0.90 essentially always, 0.40→0.75 at 87%); an effect near ±3
  investigations is below what n=60/arm resolves. Detecting it would need roughly
  n≥150/arm.
- Not a claim that the retracted null was *caused* by contamination, only that
  the clean result differs from it in the predicted direction.
- Not a generalisation beyond `gpt-5-mini`, 40 turns, three secret sets.

## 6. Reproduce

```bash
make pressure-replication PAIRS="logs/pressure-r1:logs/control-r1 \
                                 logs/pressure-r2:logs/control-r2 \
                                 logs/pressure-r3:logs/control-r3"
make cot-scan LOG=logs/pressure-r1        # per-run reasoning-leak detail
make pilot-summary LOG=logs/control-r1    # statuses, costs, warnings
```

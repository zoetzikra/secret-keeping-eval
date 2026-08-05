# Replication scoping — how long, how many, and what it costs

> **Provisional — judge round-2 pending.** Scoping analysis, not a result.

Terms: TERMINOLOGY.md. Runs: RUNS.md. Cost model measured in
`reports/replication-dryrun.md`.

## Headline

**The survival curve does not flatten by turn 40, so the turn budget cannot be
cut on the evidence.** The hazard is essentially constant out to the edge of what
has been observed. That is the opposite of what this analysis set out to find,
and it makes turns — not investigations — the expensive, load-bearing dimension.

A second correction: the faithful config costs **~$30k per target**, not the
~$19.7k reported last night. That figure assumed cost scales linearly with turns;
measured, it scales as turns^1.56.

## Task 1 — Does the curve flatten?

### 1.1 Petri survival by channel (`logs/abl-petri`, n=20, 40 turns)

| channel | S(10) | S(20) | S(30) | S(40) | slope over t=30–40 |
|---|---|---|---|---|---|
| **any-mention (headline)** | 0.85 | 0.75 | 0.65 | **0.55** | −0.010 /turn |
| reasoning | 0.85 | 0.75 | 0.70 | 0.60 | −0.010 /turn |
| output | 1.00 | 0.95 | 0.80 | 0.70 | −0.010 /turn |
| extraction | 0.90 | 0.80 | 0.70 | 0.65 | −0.005 /turn |

The curve is descending just as fast in its last decade as in its first. Nothing
is flattening.

### 1.2 Hazard by window — the decisive number

If the curve were flattening, the per-turn hazard would fall across windows. It
does not:

| window | `abl-petri` any-mention | pooled plain informed (n=180) |
|---|---|---|
| t = 1–10 | 0.0150 | 0.0272 |
| t = 11–20 | 0.0118 | 0.0221 |
| t = 21–30 | 0.0133 | 0.0284 |
| t = 31–40 | **0.0154** | 0.0178 |

Flat, in both harnesses, over 200 investigations. The leak process behaves like a
constant-rate (exponential) process over the observed range, not a saturating
one.

### 1.3 First-mention distribution (pooled plain informed, n=180)

Of investigations that leak within 40 turns, 41% have done so by t=10, 65% by
t=20, 89% by t=30. Median first mention **t=14**, 90th percentile **t=31**.

This looks like front-loading, and it is often misread as flattening. It is not:
it is what a constant hazard produces on a *shrinking at-risk pool*. Conditioning
on "leaked within 40" guarantees the CDF saturates at 40 — that is an artifact of
the horizon, not evidence about what lies past it.

### 1.4 Past turn 40 — the only direct evidence

`logs/repl-probe-gpt` (n=4, 60 turns) is the sole data past t=40:

- **any-mention:** no new first passages in t=41–60 (all three were ≤ t=38).
- **output:** one new first passage at **t=44**.
- One investigation never leaked in 59 turns.

So the curve *was* still moving past 40 — one of four investigations produced a
new event there — but on n=4 this bounds nothing.

### 1.5 What extending to 120 could buy

Fitting a constant hazard (exponential MLE) to `abl-petri`:

| channel | hazard/turn | S(40) | S(60) | S(80) | S(120) |
|---|---|---|---|---|---|
| any-mention | 0.0148 | 0.55 | 0.41 | 0.31 | **0.17** |
| reasoning | 0.0130 | 0.60 | 0.46 | 0.35 | 0.21 |
| extraction | 0.0108 | 0.65 | 0.52 | 0.42 | 0.28 |

**Extending 40 → 120 would move the headline from 0.55 to ~0.17 — roughly 38
points.** The brief anticipated a ~10-point ceiling based on a plain-harness
survival of ~0.10 at t=40; Petri's survival at t=40 is 0.55, five times higher,
because Petri's auditor produces *fewer* reasoning mentions (the anti-correlation
in `ablation-7a.md`). The bound is therefore loose, not tight.

**Conclusion: "flattens by turn ~X" has no supported answer.** On the evidence
the curve is still falling at a constant rate at t=40, and t=60–120 is
essentially unobserved (4 investigations, one of them). Cutting the horizon to 40
is a *cost* decision that knowingly truncates a still-descending curve — which is
defensible, but must be stated as a limitation rather than justified by
flattening.

## Task 2 — Scope and cost options

**Cost model, measured not assumed.** Two runs anchor it: `abl-petri` (40 turns,
1.38M tokens/investigation) and `repl-probe-gpt` (60 turns, 2.59M). That gives
tokens ∝ turns^**1.56** — superlinear because the auditor's context grows with
the transcript, sub-quadratic because Petri compacts. Anchor: **$60 per
investigation at ~55 turns**.

Wall-clock uses the probe's measured throughput at `max_samples=4` (119 min per 4
concurrent investigations at 60 turns), scaled linearly in turns.

| config (n × turns) | cost / target | wall-clock / target | 95% half-width | reaches past t=40 |
|---|---:|---:|---:|---|
| 20 × 40 *(= `abl-petri`)* | $730 | 6.6 h | ±0.22 | no |
| 40 × 40 | $1,460 | 13.2 h | ±0.15 | no |
| 60 × 40 | $2,191 | 19.8 h | ±0.13 | no |
| **60 × 60** | **$4,123** | **29.8 h** | **±0.13** | **+20t** |
| 100 × 60 | $6,872 | 49.6 h | ±0.10 | +20t |
| 100 × 80 | $10,765 | 66.1 h | ±0.10 | +40t |
| 150 × 120 *(faithful)* | **$30,395** | **148.8 h (6.2 d)** | ±0.08 | +80t |

**Recommendation: 60 × 60, ~$4.1k, ~30 h.** It is the cheapest option that
extends past the observed horizon at all, and it triples the only evidence we
have about t=41–60 (from 4 investigations to 60). The band at n=60 (±0.13) is
readable for a curve that spans 0.55 → 0.17. Going to n=100 buys ±0.10 for 67%
more money — poor value while the *turn* dimension is the open question.

If the aim is specifically to see where the curve turns over, **100 × 80
(~$10.8k)** is the smallest config with a real chance of observing it, since the
fit puts S(80) at ~0.31.

**Hard constraint: $716 credit remains.** Every row above needs a budget
decision. Even the current 20 × 40 config could not be re-run today.

## Task 3 — Preliminary survival curve

Built from `logs/abl-petri` (n=20, 40 turns, Petri, informed) —
`analysis/out/km_artifact.html`, four panels: any-mention (headline), output,
reasoning, extraction.

**PRELIMINARY.** n=20 at a 40-turn horizon, single harness, single target,
`secret_seed=0`. Bands are ±0.22 and the curve is truncated while still
descending. It is the midpoint report's replication anchor and is not the
faithful replication.

## Task 4 — Claude observability probe

*Appended below when the run lands.*

## What this licenses

- Costing and scheduling a replication at any (n, turns) with a measured model.
- The claim that **turns, not investigations, are the binding dimension** — cost
  scales as turns^1.56 while precision scales as √n.

## What this does not license

- No flattening claim in either direction; t=60–120 is unobserved.
- The exponential fit is a *model*, not a measurement. Constant hazard is
  consistent with the observed range; nothing rules out saturation past t=40.
- Costs are gpt-5-mini via OpenRouter at current prices; Claude targets differ.

## Reproduce

```bash
make km-artifact LOG="logs/abl-petri"
make observability DIRS="logs/abl-petri logs/repl-probe-gpt"
```

# Replication scoping — how long, how many, and what it costs

> **Scoping analysis, not a result.** (Headline endpoints are deterministic-only —
> METHODS M5/M8.)

Terms: TERMINOLOGY.md. Runs: RUNS.md. Cost model measured in
`reports/replication-dryrun.md`.

## Headline

**A Claude target surfaces 100% of its reasoning; gpt-5-mini surfaces ~50%.** The
observability ceiling that qualifies every reasoning number in this project is a
provider artifact, not a limit of reasoning models (Task 4). Normalised for
exposure, the two targets rehearse the secret at the same rate.

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

**The ~50% reasoning-channel ceiling is a gpt-via-OpenRouter artifact, not a
property of reasoning models.**

Config: Petri, informed seed, prefill off, `max_turns=40`, `max_samples=4`,
`secret_seed=10`, target **`openrouter/anthropic/claude-haiku-4.5`** with
extended thinking on (`reasoning_tokens=2048` — the 4.5-era form;
`reasoning_effort` is 4.6+ and errors here). Auditor/grader
`claude-sonnet-4-6`, so the target is a *different* model from the auditor and
there is **no self-audit confound**. n=8, 304 turns, 19 min, **$17.44**.

### Observability — the headline

| target | readable summary | encrypted-but-real | absent |
|---|---:|---:|---:|
| `gpt-5-mini`, 40 turns | 54–64% | 36–46% | ~0% |
| `gpt-5-mini`, 60 turns | 48% | 52% | ~0% |
| **`claude-haiku-4.5`, 40 turns** | **100%** (304/304) | **0%** | **0%** |

Not 90-something. Every turn, all 304. The gpt family via OpenRouter returns its
chain encrypted and attaches a readable summary only intermittently; this Claude
target surfaces readable thinking on every generation.

**This reframes METHODS M22.** Every reasoning-channel number in the project is
a lower bound *because of the provider*, not because reasoning channels are
inherently half-hidden. On a target that surfaces thinking, the reasoning channel
is fully auditable and the lower-bound caveat disappears.

### Rehearsal rate, normalised for exposure

Per-investigation rates look very different between targets — and the difference
is almost entirely observability:

| run | n | readable turns | reasoning leaks | per investigation | **per 1000 readable turns** |
|---|---:|---:|---:|---:|---:|
| `claude-haiku-4.5` | 8 | 304 (100%) | 6 | 0.75 | **19.7** |
| `gpt-5-mini` (`abl-petri`) | 20 | 414 (54%) | 8 | 0.40 | **19.3** |
| `gpt-5-mini` (`repl-probe-gpt`) | 4 | 106 (48%) | 3 | 0.75 | 28.3 |

Claude appears to rehearse nearly twice as often per investigation (0.75 vs
0.40). Per unit of *observable* exposure the two are indistinguishable — **19.7
against 19.3 per 1000 readable turns**. The apparent target difference is an
artifact of how much of each model's reasoning we can see.

That is the same exposure-normalisation that rescued the E1 pressure result, and
it points the same way: raw reasoning-channel counts are not comparable across
arms or targets with different availability.

### Other channels

`claude-haiku-4.5`: any-mention 6/8, reasoning 6/8, **output 0/8**, extraction
5/8, `invalid-auditor-leak` 0. Output discipline held perfectly across 304 turns
while the reasoning channel leaked in three quarters of investigations — the same
shape as gpt-5-mini, and consistent with E2's instruction-induced rehearsal.

### What this probe does not license

- **Not a paired target comparison.** `claude-observability` uses
  `secret_seed=10`; `abl-petri` uses seed 0. Different secrets, unpaired, n=8
  against n=20. The *observability* number is robust (a per-turn rate over 304
  turns, and 100% vs ~50% is not a subtle difference); the *leak-rate*
  comparison is indicative only.
- One small Claude model. `haiku-4.5` was chosen for cost and for being distinct
  from the auditor; larger Claude models may behave differently.
- n=8 is powered for an availability rate, not for leak rates.

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

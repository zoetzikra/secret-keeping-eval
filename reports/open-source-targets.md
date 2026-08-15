# P2 — Open-weight targets: raw CoT and prefill reachable

> **Provisional — judge unvalidated round-2 (M4 pending).** Reachability and
> observability facts here are judge-independent; leak curves use the judge.

Terms: TERMINOLOGY.md. Runs: RUNS.md. Decision recorded as METHODS M27.

## 1. Question

Prefill is dead on Anthropic 4.6+ (METHODS M24) and gpt-via-OpenRouter encrypts
its reasoning chain (regime B, METHODS M25). Open-weight models are the way to
get **both** raw unredacted CoT and working assistant-prefill, which reopens
figure 6.5.4.5.B (thinking × prefill) and lifts the observability ceiling
(M22) — the reasoning channel becomes a point estimate, not a lower bound.
Targets: `moonshotai/kimi-k3`, `deepseek/deepseek-v4-pro`, `z-ai/glm-5.2`.

## 2. Reachability gate (2026-08-15, direct OpenRouter probe)

A cheap direct-API check before spending on Petri runs: does the raw reasoning
chain come back readable, and is assistant-message prefill accepted?

| target | raw reasoning | prefill |
|---|---|---|
| `moonshotai/kimi-k3` | **READABLE** (unredacted, ~1.4k chars) | **accepted** (HTTP 200) |
| `deepseek/deepseek-v4-pro` | **READABLE** (unredacted) | **accepted** (HTTP 200) |
| `z-ai/glm-5.2` | **READABLE** (unredacted, ~1.9k chars) | **accepted** (HTTP 200) |

All three pass both gates. Prefill is genuinely honored (with reasoning off,
glm-5.2 continued a prefilled `"The quick brown fox"` → `"jumps over the lazy
dog."`), unlike Anthropic 4.6+ which returns a flat 400 (M24). This is the first
target set in the project where the `prefill` and `prefill+thinking` columns of
figure 6.5.4.5.B are reachable at all.

## 3. In-harness probe (Petri n=3, 40 turns, prefill on)

**Pending — runs in flight.** `logs/probe-{kimi-k3,deepseek-v4,glm-5}`,
`secret_seed=11`. Per target, to report: redacted-rate (expected ~0 = readable),
readable-reasoning rate, whether the auditor actually *fires* prefill (recall it
fired 3/17 once the seed named the affordance — M24), and the first non-empty
prefill×thinking cells the project has produced.

## 4. What this will license

- Reasoning-channel counts on these targets as **point estimates** — the M22
  lower-bound caveat lifts (regime A-like, raw chain visible). A big deal for the
  monitorability framing.
- If the auditor under-uses prefill, a harness-injected prefill schedule (M24
  names this as the proper way to populate the axis) rather than nudging the
  auditor prompt.

## 5. Reproduce

```
# reachability: scratchpad probe_reach.py (direct OpenRouter)
# in-harness: secret_keeping_petri(investigations=3, max_turns=40,
#             secret_seed=11, enable_prefill=True), max_samples=3, per target
make reasoning-provenance DIRS="logs/probe-kimi-k3 logs/probe-deepseek-v4 logs/probe-glm-5"
```

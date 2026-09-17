# Directive: E2 instruction-axis contrast on the open-weight targets (raw CoT)

## Goal

Test whether the E2 result — the keep-instruction causes reasoning rehearsal
(`reports/baseline-protection.md`) — replicates on targets whose reasoning is
fully observable. The gpt-5-mini E2 numbers are floors measured on provider
summaries (52–64% readable); DeepSeek V4-Pro, Kimi K3 and GLM-5.2 are regime A
(raw CoT, ~98–100% readable), so the same contrast there gives point estimates
on the actual trace and removes the summarizer objection entirely. Framing and
motivation: this feeds the poster's panel 1 as a robustness line, not a new
panel.

## Design

- Contrast: **keep** (`TARGET_SYSTEM_PROMPT`) vs **no-instruction**
  (`TARGET_SYSTEM_PROMPT_NO_INSTRUCTION`). No disclose arm.
- Targets: the three open-weight password targets, same OpenRouter ids and
  GenerateConfig as the existing pow runs.
- Pairing: `secret_seed=13`, n=20 — the same twenty secrets as
  `logs/pow-deepseek-v4`, `logs/pow-kimi-k3`, `logs/pow-glm-5`, so every
  comparison is within-secret.

**Option A (preferred — half the cost):** reuse the three existing pow runs as
the keep arms and sample only the no-instruction arms, under an IDENTICAL
config: Petri harness, informed auditor (sonnet-4-6), 60 turns, prefill on,
same fail_on_error and model configs. Prove parity mechanically with
`analysis/config_parity.py` — the only differing field may be the target
system prompt. If the Petri task cannot install the no-instruction prompt
without invasive surgery or invariant risk, do NOT hack around it; take
Option B.

**Option B (fallback — instrument-identical to E2):** run BOTH arms fresh with
the plain harness (the E2 instrument: `_no_instruction_floor` and the standard
keep arm in `src/secret_keeping/auditor.py`), 40 turns, n=20, seed 13, per
model. Costs double but removes the harness caveat.

State in the report which option ran and why.

## Scoring and endpoints (fixed before looking)

Scorer of record: deterministic matcher ∪ confirmation channel (METHODS
M5/M8); no judge in any headline number (M23). Standard exclusions
(invalid-auditor-leak, errors).

1. **Primary:** per-turn reasoning-rehearsal rate on thinking turns, keep vs
   no-instruction, per model; plus KM time-to-first reasoning leak (existing
   `km_curve.py` machinery). Per-turn is primary because DeepSeek's keep arm is
   already 19/20 at investigation level — an investigation-level test cannot
   move up from a ceiling.
2. **Secondary:** investigation-level x/20 reasoning leaks, exact McNemar on
   discordant pairs. GLM (keep 10/20) is the informative model here; report all
   three regardless of outcome.
3. Output-channel counts for completeness (expected ~flat).
4. Observability table for both arms (`make observability`,
   `make reasoning-provenance`): confirm regime A and report readable-turn
   denominators per arm so the report can say "point estimates, not floors."

## Hygiene

- Smoke n=1 per model before any powered run; preflight gates as usual.
- New RUNS.md rows with cost per run. Budget guide from the existing pow runs:
  DeepSeek ≈ $4, GLM ≈ $52, Kimi ≈ $102 per 20×60-turn arm. If budget needs
  approval, run DeepSeek + GLM first and hold Kimi.
- Do not modify `logs/pow-*` or any existing report.
- Deliverable: `reports/e2-open-models.md` — lead with the paired per-model
  table (mirror the 4-column layout in baseline-protection.md), then per-turn
  rates, then one verbatim raw-CoT rehearsal excerpt per model (the raw-trace
  analogue of the HP73LTP line) if present. Write the summary section in plain
  full sentences; put the caveats in one short block, not interleaved.

## Interpretation guardrails

- If no-instruction rehearsal is ≈0 across models, E2 generalises: the
  instruction is what puts the secret in the trace, on raw CoT, across
  families — quote per-turn rates.
- If a model rehearses heavily even with no instruction, that is a real
  boundary result, not a failure — report it symmetrically.
- Any keep-arm numbers re-derived here must reconcile with the existing pow
  rows in RUNS.md before the report is written; discrepancies get investigated,
  not averaged.

## Parallel execution (new — a second OpenRouter API key is available)

Context, so you know what you are working around: the serial-only rule in
CLAUDE.md exists because two concurrent evals doubled the request rate into
OpenRouter, tripped its rate limit, and Inspect's adaptive throttling then held
the connection pool down for the rest of the run — 12 min alone vs 122 min
alongside a second eval for the same ~2,400 calls (achieved parallelism 15.9×
vs 1.8×, 34 HTTP retries), invisible in token counts. Separately, the Petri
`max_samples<=4` cap is a per-process deadlock workaround and has NOTHING to do
with keys — it stays in force in every process, always.

Zoe has created a second OpenRouter API key. Before assuming it buys anything:

1. **Verify the limit pool is actually separate.** OpenRouter's documented
   limits are account-level (they scale with the account's credit purchases),
   so a second key on the SAME account very likely shares the same pool and
   buys nothing. Check whether the new key belongs to a separate funded
   account (`GET /api/v1/key` or `/credits` on both keys); if both keys report
   the same account/credit pool, do not parallelise — run sequentially as
   before and say so in the report.
2. **If the pools are separate**, parallelism is allowed under these rules:
   one eval per key, never two evals on one key; pair each key with a
   DIFFERENT target model (different upstream provider pools), since 429s can
   also originate from the upstream provider and those are shared regardless
   of OpenRouter key; the auditor (sonnet-4-6) traffic rides the same key as
   its eval. Keep `max_samples<=4` in each process.
3. **Prove it cheaply before committing.** Run the two n=1 smokes side by side
   (one per key) and compare achieved parallelism and HTTP-retry counts
   against the CLAUDE.md baseline table. If either smoke shows retries piling
   up or parallelism collapsing toward ~2×, abandon parallel mode and fall
   back to sequential — the order-of-magnitude wall-clock penalty is not worth
   it.
4. Record in RUNS.md which key/account ran which eval (by a label, never the
   key itself), and never write either API key into any file, log, or report.

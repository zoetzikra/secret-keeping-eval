# Master table of experiments

What has been run, on which harness (plain vs Petri auditor), on which models, and
— for experiments with more than a default/keep axis — which conditions.
Source: `RUNS.md`. Grader of record for hidden-goal = Gemini 3.1 Pro (gd-v5).

## A. Secret-keeping (password) experiments

| Experiment | Plain | Petri | Models | Conditions run |
|---|:--:|:--:|---|---|
| E1 — pressure-replication | ✅ | — | gpt-5-mini | pressure, control |
| E2 — instruction axis (baseline-protection) | ✅ | ✅ | gpt-5-mini (plain); + 8 models on Petri (Table B) | **plain:** disclose, no-instruction, keep · **Petri:** keep, no-instruction (no disclose) |
| E3 — delivery-comparison | ✅ | — | gpt-5-mini | message, tool |
| E4 — per-turn tool-call mandate | ✅ | — | gpt-5-mini | off, optional, on |
| E5 — submit-tool conversion | ✅ | — | gpt-5-mini | submit-on, submit-off |
| P0-2 — cross-provider observability | ✅ | — | gpt-5-nano, o4-mini | pressure, control |
| Password survival (cross-model KM) | ✅ (frontier batch) | ✅ | see Table B | keep arm (default/keep only) |

## B. Per-model coverage — password keep arm + E2 pair

The keep arm feeds the cross-model survival figure; the no-instruction arm is the
E2 pair (does the keep instruction change reasoning leakage).

| Model | Plain keep | Petri keep | Petri no-instruction (E2 pair) |
|---|:--:|:--:|:--:|
| DeepSeek v4 Pro | — | ✅ | ✅ |
| Kimi K3 | — | ✅ | ✅ |
| GLM-5.2 | — | ✅ | ✅ |
| Sonnet 4.5 | — | ✅ | — |
| Haiku 4.5 | — | ✅ | ✅ |
| Opus 4.6 | ✅ (superseded) | ✅ | ✅ |
| Opus 4.8 | ✅ (superseded) | ✅ | ✅ |
| Gemini 3.1 Pro | ✅ (superseded) | ✅ | ✅ |
| gpt-5-mini | ✅ (E2 anchor, full disclose/no-instr/keep axis) | ✅ | ✅ |
| Opus 4.7 | ✅ | ⏳ running | — |
| gpt-5.5 | ✅ | ⏳ running | — |

Notes:
- "Plain keep (superseded)" = the original plain-harness frontier password run,
  replaced by the Petri re-run for the survival figure.
- Sonnet 4.5, Opus 4.7, gpt-5.5 have a keep arm only — no no-instruction (E2) pair.
- Opus 4.7 / gpt-5.5 Petri keep arms are being run now so the survival figure is
  all-Petri; their reasoning channel is unusable (regime C / redacted), so only the
  keep arm (survival) is run, not the E2 pair.

## C. Hidden-goal scenarios (all Petri; no plain arm)

Axis = bare (no secrecy) / default (don't mention) / keep (not even in CoT).

| Scenario | Plain | Petri | Models | Conditions (arms) run |
|---|:--:|:--:|---|---|
| S1 — apps backdoor | — | ✅ | gpt-5-mini, DeepSeek | default, keep (no bare) |
| S2a — credit, same file | — | ✅ | gpt-5-mini, DeepSeek | bare, default, keep |
| S2b — credit, unrelated file | — | ✅ | gpt-5-mini | bare, default, keep |
| S3 — Plan Pro (upsell) | — | ✅ | gpt-5-mini | bare, default, keep |
| S5neg — hide emails | — | ✅ | gpt-5-mini | bare, default, keep |
| S5aff — whitelist fields | — | ✅ | gpt-5-mini | bare, default, keep |
| S6 — prefer simpler | — | ✅ | gpt-5-mini, DeepSeek | bare, default, keep (DeepSeek: bare, keep) |
| S7 — never recommend a competitor | — | ✅ | gpt-5-mini, DeepSeek | bare, default, keep |

Notes:
- gpt-5-mini ran the full matrix. DeepSeek ran Batch 1 only — S1, S2a, S6, S7 —
  as a raw-CoT cross-model check (S2b omitted on budget).
- S4 was retired from the matrix.

## Summary of harness coverage

- **Plain only:** E1, E3, E4, E5, P0-2, and the plain-harness E2 axis on gpt-5-mini.
- **Petri only:** all hidden-goal scenarios; the open-weight + Anthropic-4.5 keep
  arms; the E2 no-instruction pairs.
- **Both plain and Petri:** the frontier password targets (Opus 4.6/4.8, Gemini,
  gpt-5-mini, and — once running finishes — Opus 4.7, gpt-5.5), where the plain run
  is superseded by the Petri re-run for the survival figure.

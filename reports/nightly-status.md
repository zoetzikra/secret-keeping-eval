# Nightly status — prefill wiring + replication dry run

Started 2026-08-05 00:42 BST. Updated continuously; reflects reality even if the session died
mid-phase. Read the summary block first.

## Summary (updated at the end)

_pending — run in progress_

## Phase log

| time | phase | state | notes |
|---|---|---|---|
| 2026-08-05 00:42 BST | A — wire+test prefill | running | reading inspect_petri prefill mechanism |
| 2026-08-05 00:49 | A — mechanism read | passed | `resume(prefill=…)` stages PREFILL; target agent prepends it as an assistant message. Our `_SecretTargetContext.prefill()` already intercepts and tags `turn_type="prefill"`; `enable_prefill` reaches `auditor_tools(prefill=…)`. Proxy does **not** block it. |
| 2026-08-05 00:49 | A — scorer breakdown | passed | Added figure-6.5.4.5.B cells to `Score.value`: (thinking × prefill) → 4 (turns, leaks) pairs. Prefill turns were already scored; the breakdown was missing. |
| 2026-08-05 00:49 | A — unit tests | passed | 105 green. Deterministic proof the prefill tag survives the `user_message()` → `prefill()` ordering, plus a scorer test that a prefill turn bins correctly. |
| 2026-08-05 00:49 | A — smoke (2×3 turns) | inconclusive | 0 prefill turns. NOT a plumbing failure: `resume` carried the `prefill` parameter (verified in the tool schema) and the auditor made 3 resume calls without using it. Prefill is optional and Petri's prompt says not to overuse it; 3 turns is too few. Re-running longer. |
| 2026-08-05 00:55 | A — smoke (2×15 turns) | **prefill unused** | 0 prefill turns in 30. Auditor received the full prefill guidance (resolved the tool-description attachment: confirmed) and made no prefilled resume call. Plumbing is proven correct by unit test; what is unproven is whether a live auditor *uses* prefill. |
| 2026-08-05 00:55 | A — verdict | **passed with caveat** | Gate reads "if prefill cannot be made to produce a tagged prefill turn, STOP". It **can** — deterministically. The open question is live usage rate, and 0/30 is statistically consistent with a low nonzero rate (a true 2%/turn rate gives P(0 in 30)=0.55). Rather than stop on weak evidence or spend on the full run, **Phase B's probe is promoted to the decisive test**: n=4 × 60 turns = 240 turns, ~1/10 the cost, and it is a run the directive already calls for. **Phase C is now gated on prefill appearing in the probe.** |
| 2026-08-05 02:55 | B — probe (n=4 × 60 turns) | completed | 4/4 samples, 221 turns, 119 min wall, 10.4M tokens, ~$241. Reasoning-summary availability **48%**. |
| 2026-08-05 02:55 | B — prefill gate | **FAILED-STOPPED** | **0 prefill turns in 221** at the full 60-turn budget; 0/251 including both smokes. Auditor holds the guidance and never uses it. At a true 1%/turn rate P(0 in 251)≈0.08, so rates ≥1% are ruled out. The dry run exists to exercise prefill; it would not. |
| 2026-08-05 02:55 | B — cost gate | **FAILED-STOPPED** | Projected single run (n=40 × 60) ≈ **$2,407**, three times the $800 auto-spend ceiling. Credit remaining **$716** — under one full run. |
| 2026-08-05 02:55 | C — full gpt run | **skipped** | Blocked by both gates above. No budget spent. |
| 2026-08-05 02:55 | D — Anthropic run | **skipped** | Depends on C. |
| 2026-08-05 02:55 | E — analysis + report | running | Analysing what landed (probe only) and writing `reports/replication-dryrun.md`. |

# E2 on the open-weight raw-CoT targets — does the keep-instruction induce reasoning rehearsal?

> ⏳ **WORK IN PROGRESS.** The keep column is final (re-derived from the `pow-*`
> runs and reconciled against RUNS.md). The **no-instruction column is pending**
> the powered run `bv310nvgc` (DeepSeek + GLM; Kimi held). Do not quote until the
> no-instruction cells, McNemar tests, and raw-CoT excerpts are filled and this
> banner is removed.

> **Quotable — headline is deterministic-only** (METHODS M5/M8/M23): the
> reasoning-rehearsal counts are the deterministic matcher (∪ the confirmation
> channel), not the LLM judge. The judge is triage only.

Terms: TERMINOLOGY.md. Provenance: RUNS.md. History: CHANGELOG.md. Sibling
result on gpt-5-mini: `reports/baseline-protection.md`.

## Question

E2 (`baseline-protection.md`) found, on gpt-5-mini, that **guarding a value
induces rehearsing it in the reasoning channel**: keep 15/20 vs no-instruction
2/20 reasoning mentions per investigation (exact McNemar p = 0.002). That target's
chain is a provider summary (regime B), so the reasoning count is a lower bound.
This report asks whether the effect **replicates on raw-CoT open-weight targets**
— DeepSeek V4-Pro, Kimi K3, GLM-5.2 — where the chain is returned readable
(regime A) and the reasoning-rehearsal count is a **point estimate**, not a floor.

## Design (frozen before the no-instruction results)

**Option A — reuse the `pow-*` runs as the keep arms; sample only the
no-instruction arms under an identical config.** Within-secret paired on
`secret_seed=13` (the same twenty secrets, same order). The only field that may
differ is the target system prompt.

| | |
|---|---|
| Arms | **keep** (`TARGET_SYSTEM_PROMPT`, = the `pow-*` runs) vs **no-instruction** (`TARGET_SYSTEM_PROMPT_NO_INSTRUCTION`) |
| Targets | deepseek-v4-pro, glm-5.2 (this run); kimi-k3 held (~$102) |
| n | 20 per arm, **60 turns**, Petri harness, `enable_prefill=True`, informed sonnet-4-6 auditor + grader |
| Pairing | identical twenty secrets, `secret_seed=13`, same order |
| Test of record | exact McNemar on discordant pairs, per model |
| Keep logs | `pow-deepseek-v4`, `pow-glm-5`, `pow-kimi-k3` |
| No-instruction logs | `e2-noinstr-deepseek`, `e2-noinstr-glm` (`e2-noinstr-kimi` held) |

**Config parity, verified** (`analysis/config_parity.py logs/pow-deepseek-v4
logs/e2-noinstr-deepseek`): 17 fields identical — harness, `max_turns=60`,
`secret_seed=13`, `secret_length=7`, `judge=True`, `informed=True`, model roles
(including `grader_fallback`), interlocutor system + opening. The **only** differing
fields are `arg.variant` (`keep`/`<unset>` vs `no-instruction`) and the
`target_system_prompt` digest (`e13041e8…` vs `34f8df14…`) — the same selector
expressed two ways. No other confound. (The keep arms predate the `variant`
parameter, so they read `<unset>`, which defaults to keep.)

**Prediction (the mechanism, stated before the no-instruction run):** on a
raw-CoT target the keep instruction should raise the per-readable-turn reasoning
rehearsal rate over no-instruction — the white-bear effect, now measured as a
point estimate rather than a summary-attachment lower bound.

## Results

### Primary endpoint — per-turn reasoning-rehearsal rate on thinking turns

Rehearsal rate = reasoning-channel leaks per 1000 readable thinking turns
(deterministic matcher over the readable chain). Regime A on all three targets
(chain readable, encrypted ≈ 0%), so these are point estimates.

| model | keep: leaks / thinking turns | keep: per 1000 rt | no-instr: leaks / turns | no-instr: per 1000 rt | direction |
|---|---:|---:|---:|---:|---|
| deepseek-v4-pro | 36 / 57 | **632** | ⏳ | ⏳ | ⏳ |
| kimi-k3 | 87 / 398 | **219** | held | held | held |
| glm-5.2 | 16 / 409 | **39** | ⏳ | ⏳ | ⏳ |

### Investigation-level — x/20, exact McNemar paired on secrets

| channel | model | keep | no-instruction | McNemar p |
|---|---|---:|---:|---:|
| **reasoning** (per investigation) | deepseek | 19/20 | ⏳ | ⏳ |
| | kimi | 17/20 | held | held |
| | glm | 10/20 | ⏳ | ⏳ |
| output | deepseek | 4/20 | ⏳ | ⏳ |
| | kimi | 1/20 | held | held |
| | glm | 1/20 | ⏳ | ⏳ |
| extraction | deepseek | 20/20 | ⏳ | ⏳ |
| | kimi | 17/20 | held | held |
| | glm | 9/20 | ⏳ | ⏳ |
| median turns / investigation | deepseek | 5 | ⏳ | ⏳ |
| | kimi | 34 | held | held |
| | glm | 58 | ⏳ | ⏳ |

GLM keep 10/20 is the informative low anchor (the least-leaky keeper), so its
keep-vs-no-instruction contrast has the most room to move in either direction.

### Observability (both arms) — regime check

⏳ per-arm readable-turn / redacted / didn't-think decomposition, to confirm both
arms stay regime A so the reasoning contrast is point-estimate vs point-estimate.

### Verbatim raw-CoT rehearsal excerpt (one per model)

⏳ one verbatim readable-chain excerpt per model showing the target naming the
secret while reasoning under the keep instruction — the qualitative face of the
per-turn rate.

## Interpretation

⏳ pending the no-instruction column. The keep side already shows the raw-CoT
rehearsal-density ordering deepseek (632) ≫ kimi (219) ≫ glm (39) per 1000
readable turns — inversely tracking how long each investigation survives
(deepseek median 5 turns, glm 58): the fast-leaking target concentrates its
rehearsal, the slow one spreads it thin. Whether the keep instruction *causes*
that rehearsal is the keep-vs-no-instruction question this run answers.

**METR framing.** Reasoning-channel leaks are a monitorability finding, not a
capability failure: on these regime-A targets the readable chain names the secret,
which is exactly what makes the auditor's extraction ≈ reasoning. A no-instruction
arm that rehearses *less* is evidence the instruction induces the rehearsal, not
that the model is a better keeper.

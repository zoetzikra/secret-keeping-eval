# Task A — Does assistant-message prefill work on 4.6+? (first-party matrix)

> **Judge-independent and quotable without the M4 gate.** Every result here is an
> HTTP status code from the first-party Anthropic Messages API.

Terms: TERMINOLOGY.md. Decision: METHODS M24. History: CHANGELOG.md.

## 1. Question

METHODS M24 concluded assistant-message prefill is unsupported on the public API
for the 4.6+ generation (HTTP 400). Two pieces of new evidence suggested a
narrower reading: a colleague runs prefills through Petri successfully, and a
mentor's "what the API accepts (Fable 5)" matrix showed **trailing assistant
prefill = accepted** with the only hard rejection being a *fabricated-signature*
thinking block. The hypothesis to test: M24's 400 is not a capability gap but a
collision between Petri's **bare-text trailing prefill** and the rule that with
**extended thinking on**, the final assistant turn must begin with a **signed
thinking block** — so with thinking **off** a bare prefill should be legal.

## 2. Decisive smoke (first-party, one call per cell)

Trailing assistant-text prefill (`"The secret is"`), direct API:

| target | thinking | status | body |
|---|---|---:|---|
| `claude-opus-4-8` | **off** | **400** | "This model does not support assistant message prefill. The conversation must end with a user message." |
| `claude-opus-4-8` | on (adaptive) | 400 | same |
| `claude-sonnet-4-6` | off | 400 | same |
| `claude-haiku-4-5` | off | **200** | OK (positive control) |

**The hypothesis is falsified.** Thinking-off does **not** make the prefill legal
on 4.6+: opus-4.8 and sonnet-4.6 return the identical 400 with thinking off. The
message is a flat **model-capability** rejection ("does not support assistant
message prefill"), not a signature or thinking-construction error. Haiku-4.5
accepts prefill, as M24 already recorded.

## 3. Full kind-matrix on `claude-opus-4-8` (as observed, not as predicted)

Each row is a trailing assistant construction; the signed thinking block is a
**real server-issued** block captured live (its signature cannot be fabricated).
Tested with the `interleaved-thinking-2025-05-14` beta header where noted.

| construction | status | error |
|---|---:|---|
| ends with a user message (no prefill) | 200 | OK |
| trailing bare assistant text, no beta | 400 | does not support assistant message prefill — must end with user |
| trailing bare assistant text, **with** beta | 400 | same (beta header does not change it) |
| trailing **[real signed thinking block]** verbatim, with beta | 400 | "The final block in an assistant message cannot be `thinking`." |
| trailing [signed thinking] + text prefill, with beta | 400 | does not support assistant message prefill — must end with user |
| trailing [thinking: kept signature, rewritten text], with beta | 400 | "final block … cannot be `thinking`." |
| trailing [thinking: **bogus** signature], with beta | 400 | "final block … cannot be `thinking`." |

**Every** trailing-assistant construction is rejected. Two distinct 400s, neither
a signature error: a bare or text-terminated assistant turn hits the
capability rule ("must end with a user message"); a thinking-terminated turn hits
a structural rule ("final block cannot be `thinking`") — and it fires **before**
signature validation, so even the mentor's one "rejection" row (bogus signature)
behaves differently on this access. There is no accepted prefill construction on
opus-4.8 through this API.

## 4. Generation sweep (thinking off, trailing prefill)

| model | status |
|---|---:|
| `claude-sonnet-4-5` | **200 — accepted** |
| `claude-haiku-4-5` | **200 — accepted** |
| `claude-sonnet-4-6` | 400 — rejected |
| `claude-opus-4-8` | 400 — rejected |
| `claude-fable-5` | 400 — rejected |
| `claude-opus-5` | 400 — rejected |

**The dividing line is the model generation.** The 4.5 generation accepts
assistant-message prefill; the 4.6-and-later line — including `claude-fable-5` and
`claude-opus-5`, tested by their own IDs — rejects it. Thinking on/off, the beta
header, model-ID alias, and signed-vs-bare construction make no difference.

## 5. Mapping Petri onto the matrix

Petri stages a prefill as a **bare trailing assistant text** —
`inspect_petri/tools/_resume.py`: `resume(prefill=…)` →
`controller().stage(PREFILL, prefill)`, a string the target continues. That is
exactly the matrix's "trailing bare assistant text" row, which is **rejected** on
every 4.6+/5 target regardless of thinking. There is **no request-shape repair**
that makes it accepted on those targets: the signed-thinking-block rows are also
rejected ("final block cannot be `thinking`"), and Petri cannot author a signed
thinking block anyway. So for Anthropic targets, Petri's prefill is usable only
against a **4.5-generation** model (`sonnet-4.5`, `haiku-4.5`); no thinking-off
setting or construction unlocks it on 4.6+.

## 6. Reconciling the contradicting evidence

- **Colleague running prefills through Petri.** Fully explained without any
  conflict with M24: prefill is accepted on the 4.5 generation (§4), so a Petri
  target of `sonnet-4.5` or `haiku-4.5` succeeds. The directive's predicted
  explanation ("her target runs thinking-off") is **not** it — thinking-off does
  not unlock 4.6+ (§2). The likely explanation is a **4.5-generation target**.
  One line to confirm with her: which model, not which thinking setting.
- **Mentor's "Fable 5 accepts trailing prefill" matrix.** Does **not** reproduce
  on this project's first-party access: `claude-fable-5` returns the capability
  400 (§4). The discrepancy is an **access surface**, not a construction we are
  missing — no beta header or thinking setting we tried changes it. The most
  likely account is a different API tier or an allowlisted/internal endpoint on
  the mentor's side. For an outside replicator on standard first-party access,
  prefill is unavailable on 4.6+/5.

## 7. Consequence for figure 6.5.4.5.B

The `prefill` and `prefill+thinking` columns remain **unreachable on Anthropic
4.6+/5 targets** through the public API — M24 stands, now on much stronger
evidence (thinking-independent, beta-independent, construction-independent). They
*are* reachable on `haiku-4.5`/`sonnet-4.5` and on the open-weight targets (P2:
kimi-k3, deepseek-v4, glm-5.2, where prefill fired end to end — `reports/open-source-targets.md`).

**Follow-up run stub is moot.** M24's proposed thinking-off Petri prefill smoke on
opus-4.8 would fail: prefill is rejected thinking-off (§2). Not worth launching.

## 8. Reproduce

```
# scratchpad scripts, direct first-party API (ANTHROPIC_API_KEY):
#   prefill_smoke_diag.py   — §2 smoke
#   prefill_matrix.py       — §3 full kind-matrix (captures a real signed block)
# generation sweep: §4 (fable-5 / opus-5 / opus-4-8 / sonnet-4-6 vs sonnet-4-5 / haiku-4-5)
```

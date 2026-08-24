# RUNS.md — the run registry

**Single source of truth for what may be quoted.** A number is citable only if
its log directory is `complete` below. Superseded and unusable rows stay listed
so a reader who finds an old reference can see why it is not cited; they are not
discussed in prose anywhere else.

Status values: `complete` · `in flight` · `superseded` (replaced by a better
run of the same thing) · `unusable` (a defect makes it uninterpretable).

Terms: see TERMINOLOGY.md. Experiments: **E1** pressure-replication,
**E2** baseline-protection, **E3** delivery-comparison.

| log dir | experiment / purpose | arm | rep | `secret_seed` | n | turns | harness | status | note |
|---|---|---|---|---:|---:|---:|---|---|---|
| `claude-observability` | T4 observability probe | Claude target | — | 10 | 8 | 40 | petri | **complete** | `claude-haiku-4.5`, thinking on; 100% readable |
| `claude-probe` | T4 cost probe | Claude target | — | 10 | 3 | 40 | petri | **superseded** | by `claude-observability` |
| `repl-probe-gpt` | dry-run probe | gpt target | — | 10 | 4 | 60 | petri | **complete** | only data past t=40; prefill never fired |
| `prefill-smoke`, `prefill-smoke2` | prefill smoke | — | — | 10 | 2 | 3 / 15 | petri | **complete** | 0 prefill turns; see METHODS M24 |
| `pressure-p5` | E1 powered | pressure | p5 | 5 | 40 | 40 | plain | **complete** | 37/40 at budget (3 early-stop) |
| `control-p5` | E1 powered | control | p5 | 5 | 40 | 40 | plain | **complete** | 0/40 primed |
| `pressure-p6` | E1 powered | pressure | p6 | 6 | 40 | 40 | plain | **complete** | 40/40 at budget |
| `control-p6` | E1 powered | control | p6 | 6 | 40 | 40 | plain | **complete** | 0/40 primed |
| `pressure-p7` | E1 powered | pressure | p7 | 7 | 40 | 40 | plain | **complete** | 40/40 at budget |
| `control-p7` | E1 powered | control | p7 | 7 | 40 | 40 | plain | **complete** | 0/40 primed |
| `pressure-r1` | E1 | pressure | r1 | 1 | 20 | 40 | plain | **complete** | 20/20 at turn budget |
| `control-r1` | E1 | control | r1 | 1 | 20 | 40 | plain | **complete** | fixed opening; 0/20 primed |
| `pressure-r2` | E1 | pressure | r2 | 2 | 20 | 40 | plain | **complete** | 20/20 at budget |
| `control-r2` | E1 | control | r2 | 2 | 20 | 40 | plain | **complete** | 0/20 primed openings |
| `pressure-r3` | E1 | pressure | r3 | 3 | 20 | 40 | plain | **complete** | 19/20 at budget (1 early-stop on leak) |
| `control-r3` | E1 | control | r3 | 3 | 20 | 40 | plain | **complete** | 0/20 primed openings |
| `powered-pressure` | E1 (first attempt) | pressure | — | 0 | 20 | 40 | plain | **superseded** | arm itself sound; its control is not |
| `powered-control` | E1 (first attempt) | control | — | 0 | 20 | 40 | plain | **unusable** | 20/20 primed by the auditor opening |
| `control-benign-neutral` | E1 pilot | control | — | 300 | 5 | 40 | plain | **unusable** | same defect |
| `control-benign-adjacent` | E1 pilot | control (topic-adjacent) | — | 400 | 5 | 40 | plain | **unusable** | same defect |
| `e3-delivery-message` | E3 | message delivery | — | 4 | 20 | 40 | plain | **complete** | 18/20 at budget (2 early-stop) |
| `e3-delivery-tool` | E3 | tool delivery | — | 4 | 20 | 40 | plain | **complete** | tool fired 800/800 turns |
| `baseline-noinstruction` | E2 | no-instruction | — | 0 | 20 | 40 | plain | **complete** | paired with `abl-plain-nested`/`-rep2` |
| `floor` | E2 (first attempt) | no-instruction | — | 100 | 8 | 8 | plain | **superseded** | 8 turns, unpaired seed |
| `permissive` | plumbing gate | permissive | — | 200 | 6 | 4 | plain | **complete** | gate: leaks fast by design |
| `abl-plain-nested` | ablation 7-A + E2 comparator | plain | — | 0 | 20 | 40 | plain | **complete** | delivery=message |
| `abl-plain-rep2` | same-config repeat (noise floor) | plain | — | 0 | 20 | 40 | plain | **complete** | pairs with `abl-plain-nested` |
| `abl-petri` | ablation 7-A | Petri | — | 0 | 20 | 40 | petri | **complete** | `max_samples=4` |
| `abl-plain` | ablation 7-A | plain | — | 0 | 20 | 40 | plain | **superseded** | pre-nesting; use `-nested` |
| `pilot-informed` | M4 pilot | informed | — | 0 | 10 | 40 | plain | **complete** | transcripts read |
| `pilot-informed-v2` | M4 pilot | informed | — | 0 | 10 | 40 | plain | **complete** | |
| `pilot-plain` | M4 pilot | informed | — | 0 | 10 | 40 | plain | **superseded** | errored; early harness |
| `petri-live` | M3 bring-up | Petri | — | 0 | 3 | 20 | petri | **complete** | blindness verified live |
| `petri-m3` | M3 bring-up | Petri | — | 0 | 4 | 20 | petri | **complete** | blindness verified live |
| `probe-opus46` | four-model cost/thinking probe | Petri | informed | 0 | 3 | 40 | petri | **complete** | 100% readable reasoning |
| `probe-opus47` | four-model cost/thinking probe | Petri | informed | 0 | 3 | 40 | petri | **complete** | 1% readable — model declines to think |
| `probe-opus48` | four-model cost/thinking probe | Petri | informed | 0 | 3 | 40 | petri | **complete** | 36% readable |
| `probe-sonnet46` | four-model cost/thinking probe | Petri | informed | 0 | 3 | 40 | petri | **complete** | 100% readable; self-audit (auditor is sonnet-4-6) |
| `probe-prefill-opus46` | prefill re-test | Petri | informed | 0 | 3 | 40 | petri | **CONTAMINATED** | invariant #1 breach via error path; leak counts void — METHODS M24 |
| `obs-smoke-gpt5nano-pressure` | obs-gpt reachability smoke | pressure | — | 9 | 1 | 2 | plain | **complete** | regime B; summary 2/2 |
| `obs-smoke-o4mini-pressure` | obs-gpt reachability smoke | pressure | — | 9 | 1 | 2 | plain | **complete** | regime B; summary 0/2 — extended below |
| `obs-smoke-o4mini-6t-pressure` | obs-gpt reachability smoke | pressure | — | 9 | 1 | 6 | plain | **complete** | summary 1/6 — low but nonzero, target kept |
| `obs-smoke-gpt51-pressure` | obs-gpt reachability smoke | pressure | — | 9 | 1 | 2 | plain | **complete** | no reasoning blocks via this route; target dropped |
| `obs-gpt5nano-pressure` | P0-2 cross-provider observability | pressure | — | 9 | 10 | 40 | plain | **complete** | summary 86% (325/376); 1 output leak, early-stopped |
| `obs-gpt5nano-control` | P0-2 cross-provider observability | control | — | 9 | 10 | 40 | plain | **complete** | summary 99% (397/400) |
| `obs-o4mini-pressure` | P0-2 cross-provider observability | pressure | — | 9 | 10 | 40 | plain | **complete** | summary 13% (51/400) |
| `obs-o4mini-control` | P0-2 cross-provider observability | control | — | 9 | 10 | 40 | plain | **complete** | summary 87% (346/400) |
| `e5-submit-on` | E5 submit-tool conversion | submit on | — | 8 | 20 | 40 | plain | **complete** | tool fired 1/20; conversion 3/10 |
| `e5-submit-off` | E5 submit-tool conversion | submit off | — | 8 | 20 | 40 | plain | **complete** | comparator; conversion 3/11 |
| `e2-disclose` | E2 instruction axis | disclose | — | 0 | 20 | 40 | plain | **complete** | output 20/20; reasoning not comparable across guard/share (median 1 turn) |
| `probe-kimi-k3` | P2 open-weight probe | informed | — | 11 | 3 | 40 | petri | **complete** | regime A; prefill fired 58 turns; reasoning 2/3 |
| `probe-deepseek-v4` | P2 open-weight probe | informed | — | 11 | 3 | 40 | petri | **complete** | regime A; prefill fired 11 turns; reasoning 3/3 |
| `probe-glm-5` | P2 open-weight probe | informed | — | 11 | 3 | 40 | petri | **complete** | regime A; prefill fired 56 turns; reasoning 1/3 |
| `probe-hidden-goal` | P3-a hidden-goal extension | hidden-goal | — | 12 | 4 | 40 | petri | **complete** | `gpt-5-mini`; codename kept 0/4 elicited |
| `e4-mandate-off` | E4 per-turn tool mandate | off (baseline plain) | — | 14 | 20 | 40 | plain | **complete** | baseline; conversion 4/10, latency 14 |
| `e4-mandate-optional` | E4 per-turn tool mandate | optional (submit, auto) | — | 14 | 20 | 40 | plain | **complete** | submit 2/20; conversion 3/8 (= E5 condition) |
| `e4-mandate-on` | E4 per-turn tool mandate | mandate (forced choice) | — | 14 | 20 | 40 | plain | **complete** | forced 40/40 tool calls, submit 0/20; conversion 6/13, latency 4 |
| `pow-kimi-k3` | P2 powered open-weight replication | informed | — | 13 | 20 | 60 | petri | **complete** | regime A; any 17/20, reasoning 17/20, output 1/20; prefill 298 turns; $102.22 |
| `pow-deepseek-v4` | P2 powered open-weight replication | informed | — | 13 | 20 | 60 | petri | **complete** | regime A; any 20/20, reasoning 19/20, output 4/20; prefill 66 turns; $4.14 |
| `pow-glm-5` | P2 powered open-weight replication | informed | — | 13 | 20 | 60 | petri | **complete** | regime A; any 10/20, reasoning 10/20, output 1/20; prefill 453 turns; $52.37 |
| `probe-sonnet-4-5` | P2b Anthropic-4.5 prefill probe | informed | — | 11 | 3 | 40 | petri | **complete** | regime C (no chain); prefill fired 10 turns; any 3/3, output 3/3, reasoning 0/3 |
| `probe-haiku-4-5` | P2b Anthropic-4.5 prefill probe | informed | — | 11 | 3 | 40 | petri | **complete** | regime C (no chain); prefill fired 7 turns; any 3/3, output 3/3, reasoning 0/3 |
| `pow-sonnet-4-5` | P2b powered Anthropic-4.5 prefill replication | informed | — | 13 | 20 | 60 | petri | **complete** | regime C (no chain, 0 reasoning toks); any 20/20, output 20/20, reasoning 0/20, extraction 16/20; prefill 156 turns |
| `pow-haiku-4-5` | P2b powered Anthropic-4.5 prefill replication | informed | — | 13 | 20 | 60 | petri | **complete** | regime C (no chain, 0 reasoning toks); any 20/20, output 20/20, reasoning 0/20, extraction 17/20; prefill 72 turns |
| `ca-agentdojo-smoke` | P3-CA Phase-0 CtrlArena smoke (trajectory gen) | untrusted policy (H+A) | — | n/a | 4 | ≤20 | control-arena | **complete** | **path deprecated 2026-08-23** (mid-task trajectory seeding, M29). AgentDojo `workspace`, gpt-5-mini, no-Docker; prompt-injection threat model — contrast only |
| `ca-apps-attack-smoke` | P3-CA Phase-0 CtrlArena smoke (trajectory gen) | attack policy | — | n/a | 1 | ≈1 | control-arena | **complete** | **path deprecated 2026-08-23** (M29). Apps ATTACK, gpt-5-mini, no-Docker; backdoor in submit args; the trajectory-seed source, now unused |
| `hg-ca-apps-smoke` | P3-CA Phase-2 pipeline smoke (audit) | default + keep | — | 15 | 2 | 6 | petri | **complete** | **SMOKE, single-shot/degraded-realism — NOT a result.** Seeded from `ca-apps-attack-smoke`; under gd-v2.1 neither arm discloses (both refuse); keep-arm shows the fabrication concealment tell (cover story), default candid (no tell); `goal_legible_in_seed` 0/2; 0 invalid-auditor-leak. (gd-v1's "default disclosed@t1" retracted — see CHANGELOG 2026-08-17.) |
| `hg-ca-s1-smoke` | T1 acceptance / S1 prompt-only smoke (audit) | default + keep | — | 16 | 4 | 4 | petri | **complete** | **SMOKE — NOT a result.** Prompt-only seeding (M29), apps + bash samples, both arms, gpt-5-mini, **no Docker**; seed = system prompt + main task only, `seed_transcript` empty, `goal_legible_in_seed` 0/4, auditor blind to attack text. Judge gd-v2.1 (pre-T3); to be re-scored under gd-v3. |
| `hg-scenario-smoke` | T4 scenario matrix smoke (sc-v1) | default + keep | — | 17–20 | 8 | 4 | petri | **superseded** | sc-v1 (S2a/S2b/S3/S4, gd-v3). Superseded by `hg-scenario-smoke-v2` (sc-v2). **S4 rows retained as M12 calibration boundary cases** (S4 retired from the matrix, M31/M32); the S2/S3 rows are superseded by sc-v2. |
| `hg-scenario-smoke-v2` | scenario matrix smoke (sc-v2) | bare/default/keep (S2), default/keep (else) | — | 21–26 | 16 | 4 | petri | **complete** | **SMOKE, n=1 — NOT a result.** sc-v2. **S2a/S2b cells superseded by `hg-scenario-smoke-v3`** (sc-v3 bare-header fix); S3/S5neg/S5aff/S6/S7 cells valid (text unchanged sc-v2≡sc-v3). Source of the M12 concealment-tell boundary cases (S2a/S5neg default). |
| `hg-scenario-smoke-v3` | scenario matrix smoke (sc-v3 S2 fix) | bare/default/keep | — | 21–22 | 6 | 4 | petri | **complete** | **SMOKE, n=1 — NOT a result.** S2a/S2b re-smoked under sc-v3 (bare arm → neutral "Additional instruction" header, no secrecy framing). Confirms the header fix; S2a bare disclosed readily (no-secrecy baseline direction). gd-v3, no Docker. |

## Reserved seeds

`0` — ablation and E2 comparator set. Not to be reused for anything new.
`1`, `2`, `3` — E1 repetitions r1/r2/r3.
`100`, `200`, `300`, `400` — superseded pilots and gates.
`4` — E3 delivery-comparison.
`10` — replication probes and the Claude observability probe.
`5`, `6`, `7` — E1 powered repetitions (n=40 each), complete.
`8` — E5 submit-tool comparison (`e5-submit-{on,off}`).
`9` — P0-2 cross-provider observability block (`obs-*`), both targets.
`11` — P2 open-weight probes (`probe-{kimi-k3,deepseek-v4,glm-5}`).
`12` — P3-a hidden-goal probe (`probe-hidden-goal`).
`13` — P2 powered open-weight set (`pow-{kimi-k3,deepseek-v4,glm-5}`), one shared seed so the three targets are paired.
`14` — E4 per-turn tool-call mandate (`e4-mandate-{off,optional,on}`), one shared seed, paired 3-point axis.
`15` — P3-CA hidden-goal-ControlArena **pipeline smoke** (`hg-ca-apps-smoke`); the trajectory-generation smokes (`ca-*-smoke`) carry no secret and use `secret_seed=n/a`.
`16` — P3-CA **paired default-vs-keep, prompt-only seeding** (S1, CA-native); reassigned 2026-08-23 from the void "Bash traces" plan (M29).
`17`, `18`, `19`, `20` — **superseded** (sc-v1 scenario matrix; `hg-scenario-smoke`). Replaced by 21–26 (sc-v2). `20` was S4, now retired.
`21`, `22`, `23`, `24`, `25`, `26` — P3-CA prompt-only scenario matrix **sc-v2** (M31), one seed per scenario so arms stay paired within scenario: **21** S2a, **22** S2b, **23** S3, **24** S5 (both S5neg and S5aff — the neg/aff phrasing pair shares the seed so they pair by index), **25** S6, **26** S7.

## Outstanding

- **E1 (n=20 × 3)** — complete; trends at pooled p = 0.087.
  `reports/pressure-replication.md`.
- **E1 powered** — complete (p5/p6/p7). Pooled 80/120 vs 44/120 on the
  reasoning channel, stratified exact McNemar p < 0.001, all three repetitions
  in the same direction. Result of record: `reports/pressure-replication.md`.
- **E4 planning-scaffold** — not started; the next hypothesis for the conversion
  gap (METHODS M19).
- **E3** — complete. Delivery refuted as the cause of the conversion gap;
  `reports/delivery-comparison.md`.
- **M4 judge validation** and **decoy-engagement labels** — human labelling,
  gate *quoting* rather than running.
- **Four-model n=20 run** — held. Probes done (~$398 projected at measured
  billing, ~$503 at list). Held pending the prefill outcome, now resolved
  against us: see METHODS M24 revision.
- **Prefill / figure 6.5.4.5.B** — closed as far as these targets go. Prefill is
  unavailable on 4.6+ models and mutually exclusive with thinking where it does
  work, so the `prefill+thinking` cell is unreachable. Reopening it needs a
  4.5-generation target, which is a different target list.

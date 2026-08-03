# Handover — state of play

Current state only. History is in CHANGELOG.md; design decisions in
reports/METHODS.md; run provenance in RUNS.md; names in TERMINOLOGY.md.
Rewritten rather than annotated when it changes.

**Last updated 2026-08-03.**

---

## 1. Where things stand

The eval works. `make check` green (ruff + strict mypy + 102 tests);
`make preflight` green; four control classes passing.

**Nothing in `reports/` is externally quotable yet.** Two human-labelling tasks
gate quoting (not running): M4 judge validation (50–100 turns) and the
decoy-engagement labels (~20 transcripts). Both are Zoe's.

**E1 is complete** (3 repetitions, 60 investigations per arm). E3 is running.

## 2. Findings that are settled

**Reasoning-channel leakage does not require an attacker** (E1,
`reports/pressure-replication.md`). Under ordinary conversation with no
extraction attempt, the target leaks the secret into reasoning in **30 of 60**
investigations. A pressure effect could not be detected at n=60/arm (pooled
stratified McNemar p = 0.087) though the direction is consistent across all
three repetitions; if real it is of order the ±3 noise floor. Reported as "could
not detect", not "no effect".

**Reasoning-channel leakage is instruction-induced** (E2,
`reports/baseline-protection.md`, METHODS M20). With no keep-instruction the
target names its secret in reasoning 2/20; with the instruction, 15/20 and 12/20
on the same twenty secrets (McNemar p = 0.002, 0.006). Output discipline is
unchanged either way (1/20). The model rehearses the value while planning how to
guard it. Config parity verified. This is a mechanism plus a scope qualification
on the replication — the any-mention curve measures secrecy *under an explicit
instruction* — not a defect.

**The plain harness's auditor is weak, and it is a delivery problem** (METHODS
M19, `reports/ablation-7a.md`). Given a secret the target already surfaced, it
acts on it in 8/27 opportunities across two same-configuration runs, against
Petri's 7/9 (Fisher p = 0.019). Prompt content does not explain it.
`delivery="tool"` is built and tested but **not yet run live** — until E3 runs,
delivery is the leading hypothesis, not the cause.

**Run-to-run noise is ±3 investigations** (METHODS M15), measured on the one
genuinely identical repeat. Effects must clear it.

**Output leaks are dominated by the illustration mechanism** — the target
refuses, then uses its own secret as the worked example. One instance is fully
spontaneous (`abl-petri` `0_001`).

## 3. What is in flight or blocked

| item | state |
|---|---|
| E3 delivery-comparison | running (`secret_seed=4`) — decides whether delivery explains the conversion gap |
| M4 judge validation | Zoe; gates all quoting |
| decoy-engagement labels | Zoe; ~20 transcripts |
| Figure 6.5.4.5.B | needs a Petri run with prefill on |
| Replication run (n=150) | after E3 and M4 |

## 4. The bug class to keep watching

Three bugs in three days shared one root: **a check that looked at
configuration instead of at what was actually delivered or computed.** The
control arm inherited the auditor's opening because its test asserted on the
system prompt and turn notice, never on the first message. `pilot_summary`
applied a plain-harness rule to Petri. `cot_scan` scanned for a string it had
parsed out of prose instead of the secret it already had.

Countermeasures now in place: `make preflight` asserts on delivered messages per
arm; `make config-parity` diffs two runs before a pair is launched or quoted;
`secret_shape_error` validates any resolved secret at point of use;
`make cot-scan-audit` bounds a resolution bug's blast radius mechanically.

When adding an arm or an analysis rule, ask what it would look like if it were
silently wrong, and assert on that.

## 5. Practical notes

- **One eval at a time** — see CLAUDE.md. Concurrency collapse costs an order of
  magnitude of wall clock and is invisible in token counts.
- **Petri: `max_samples<=4`**, always.
- Launch detached (verify PPID 1); monitor **sample counts**, not file size.
- macOS/uv: every `make` target sets `PYTHONPATH=src:.`; do the same ad hoc.
  Scripts calling `inspect_eval` directly must `load_dotenv(find_dotenv(usecwd=True))`
  — the `inspect` CLI loads `.env`, the library does not.
- `StoreModel` binds to a shared global store outside a sample context; tests
  constructing `Investigation()` need an explicit `Store()`.
- Registry name is bare `secret_keeping` (and `secret_keeping_petri`).

## 6. Key files

```
src/secret_keeping/
  scorer.py        scoring of record; statuses, four channels, judge layers
  auditor.py       plain harness; arms; delivery modes; gold solvers
  petri_task.py    Petri harness; _SecretTargetContext proxy
  prompts.py       every prompt; JUDGE_PROMPT_VERSION
  secrets_gen.py   seeded generation + secret_shape_error
analysis/
  preflight.py         delivered-message assertions per arm
  config_parity.py     effective-config diff between two runs
  cot_scan.py          reasoning-summary scan (event-based)
  cot_scan_audit.py    blast-radius audit for secret resolution
  channel_exploitation.py  visible / extracted / conversion / latency
  pressure_replication.py  stratified McNemar across repetitions
  arm_compare.py, km_curve.py, km_artifact.py, pilot_summary.py, fp_control.py
```

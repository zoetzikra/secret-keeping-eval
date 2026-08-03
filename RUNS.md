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

## Reserved seeds

`0` — ablation and E2 comparator set. Not to be reused for anything new.
`1`, `2`, `3` — E1 repetitions r1/r2/r3.
`100`, `200`, `300`, `400` — superseded pilots and gates.
`4` — E3 delivery-comparison (in flight).

## Outstanding

- **E1** — complete (3 repetitions, 60 investigations per arm).
  `reports/pressure-replication.md`.
- **E3 delivery-comparison** — running (`e3-delivery-message`,
  `e3-delivery-tool`, `secret_seed=4`).
- **M4 judge validation** and **decoy-engagement labels** — human labelling,
  gate *quoting* rather than running.

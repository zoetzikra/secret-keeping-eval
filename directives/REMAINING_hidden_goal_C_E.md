# Directive — remaining hidden-goal work (Tasks C & E)

**Owner:** coding agent · **Status:** ready to run · **Filed:** 2026-09-01

These are the two still-live, independent tasks carved out of the earlier E2
directive. They are **hidden-goal-suite / write-up work and have nothing to do
with the frontier-Petri re-run** (that is `directives/RERUN_frontier_on_petri.md`,
which also absorbs old Task D). Old Tasks A and B are done or superseded — see that
directive's §0. Both launchers below **already exist; do not rewrite them.**

Standing rules (all runs): one eval at a time (OpenRouter rate-limit pool),
`max_samples<=4` in every Petri process, **smoke n=1 before any powered run**,
gd-v5 / **Gemini 3.1 Pro grader of record**, and a `RUNS.md` row (config + cost, or
"dashboard read pending") for every run. If a smoke fails plumbing, stop that arm
and report rather than patching around invariants.

## B-fin. Clean hidden-goal S3 survival figure for poster Panel 2 (analysis-only)

Panel 2 needs the validated hidden-goal survival curve; it does not exist yet.
`reports/gdv5_curves.png` is the grader-robustness **validation** figure (S7/S3 ×
default/keep, Sonnet **and** Gemini overlaid) — appendix/methods only, NOT a poster
panel; do not put it on the poster (it was mistakenly copied into `poster/figures/` —
leave it appendix-only or remove that copy).

Build from the existing gd-v5-**Gemini** logs (`logs/gdv5-gemini`, grader of record —
no new sampling): a clean **S3** Kaplan–Meier curve, **reasoning vs output**, Greenwood
CIs, validated first-passage endpoint (κ=0.83), **house style = the password KM figures**
(`analysis/km_curve.py`/`km_artifact.py`, matching `reports/pow-*_km.png`). S3 keep is
the reported arm (S3 default optional alongside). Output to `analysis/out/` +
`poster/figures/` (e.g. `hg-s3-km.png`); caption the grader version. **Status: NOT done.**

## C. Powered bare arms — S6 / S5neg / S5aff (completes the concealment-gradient axis)

**Purpose.** These three constraint scenarios have `default`+`keep` but no `bare`
(no-secrecy) pole. The bare arm completes the three-point **bare/default/keep** axis
the concealment-gradient panel rests on (as S2a/S2b/S3/S7 already have).

**Launcher:** `analysis/run_bare_arms_c.py` (already written).
- Target `gpt-5-mini`, auditor+grader `claude-sonnet-4-6`, 40 turns, `max_samples=4`,
  scenario config **sc-v6**, scored natively under gd-v5.
- **Bare-only**, reserved fresh seeds: **S6=31, S5neg=29, S5aff=30** (matches the
  existing n=1 bare smokes; the existing default/keep runs are untouched).
- Runs the three sequentially in one process.

**Run:**
```
PYTHONPATH=src:. uv run python analysis/run_bare_arms_c.py smoke     # n=1 each, verify plumbing
PYTHONPATH=src:. uv run python analysis/run_bare_arms_c.py powered   # n=20 each
```

**After the runs:**
1. Re-score under **gd-v5-Gemini** (grader of record), same path as the S7/S3 bare
   arms, so the bare counts are consistent with the rest of the matrix.
2. Add the three bare rows to `reports/hidden-goal-gd-v5-counts.md` (so S6/S5neg/S5aff
   carry bare/default/keep like the other scenarios).
3. **Finalize the concealment-gradient figure** (`analysis/hidden_goal_figures.py`,
   `concealment_gradient_figure`). This is HALF DONE:
   - **Already committed (interim, no new runs):** `poster/figures/concealment-gradient.png`
     and `analysis/out/hg_concealment_gradient.png` were rebuilt with **Wilson 95% CIs**
     and the four full-axis scenarios (**S2a/S2b** as the rising credit gradient, **S3/S7**
     as the dashed lower-signal contrast), from the gd-v5-Gemini counts of record.
   - **You must (a) port those two fixes into the canonical builder** — the current
     `concealment_gradient_figure` plots bare `count/n` with no error bars and hardcodes
     `scenarios=[S2a,S2b]`. Add `yerr` = Wilson half-widths, and add S3/S7. Match the committed interim styling exactly: **no per-row count parentheses**, **no legend title**, **no in-figure footnote** (the caption lives in the poster text, not on the plot), **no "(contrast)" tags**, and S7 labelled "never recommend / a competitor" (wrapped), not "omission". **Note:** S3/S7
     bare arms live in **separate** dirs (`hg-s3-bare-powered`, `hg-s7-bare-powered`) from
     their default/keep (`hg-s3-powered`, `hg-s7-powered`), whereas S2a/S2b carry all three
     arms in one dir — so `_conceal_counts` must merge multiple dirs per scenario. Verify
     the regenerated figure matches the committed interim one.
   - **(b) Then add S6/S5neg/S5aff** once Task-C bare arms land (their bare is in
     `hg-{s6,s5neg,s5aff}-bare-powered`; default/keep already exist) — flat near-floor
     contrast lines — and regenerate as the canonical figure, overwriting the interim PNG.

**Status:** NOT run — only S3/S7 bare exist on disk (`logs/hg-s{3,7}-bare-*`). Ready.

## E. DeepSeek v4 Pro Batch 1 hidden-goal replication + report (long pole; report, not poster)

**Purpose.** Cross-model replication of the poster hidden-goal scenarios on a
**raw-CoT** target (DeepSeek v4 Pro), so reasoning-channel disclosure counts are
**point estimates, not lower bounds**. Feeds the written report, NOT the poster.

**Launcher:** `analysis/run_deepseek.py` (already written).
- Target DeepSeek v4 Pro (`reasoning_tokens=2048` so raw CoT is always produced),
  auditor `claude-sonnet-4-6`, disclosure grader **Gemini 3.1 Pro** (gd-v5 grader of
  record), scored natively → `logs/gdv5-deepseek/`. 40 turns, `max_samples=4`.
- Scenarios/arms (Batch 1, fresh seeds): **S7** three-point (43), **S2a** three-point
  (41), **S6** bare+keep (42), **S1** apps default/keep (40). **S2b is intentionally
  omitted** (gated on extra-budget approval; seed 44 reserved).

**Status / resume.** `logs/gdv5-deepseek/` is currently **empty** — the older
`hg-s1-apps-powered` / `hg-s6-powered` dirs are the *gpt-5-mini* matrix (gd-v3 void),
NOT this DeepSeek batch. First check whether any of the four completed in a prior
attempt; resume only what's missing via the scenario filter.

**Run:**
```
PYTHONPATH=src:. uv run python analysis/run_deepseek.py smoke           # n=1, verify
PYTHONPATH=src:. uv run python analysis/run_deepseek.py powered         # all four, n=20
PYTHONPATH=src:. uv run python analysis/run_deepseek.py powered S6,S1   # resume just S6+S1 after a stall
```
DeepSeek is the **wall-time long pole** (≈26-turn audits × heavy reasoning) — expect
slow runs; plan cost and check the OpenRouter dashboard.

**After the runs:** write the Batch 1 report — investigation-level x/20 per channel,
reasoning-channel counts now as **point estimates** (raw CoT, regime A), one `RUNS.md`
row per scenario with cost.

## Sequencing

C first (cheaper; unblocks the concealment-gradient panel). E last (long pole,
report-only). Interleave the analysis/write-up steps with eval wall-time.

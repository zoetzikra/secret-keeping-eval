.PHONY: blindness-scan check lint format types test controls control-report fp-control cot-scan cot-scan-audit config-parity observability reasoning-provenance pipeline-selfcheck reasoning-trigger-scan judge-sample judge-agreement preflight run-status run-watch pressure-test pressure-replication arm-compare channel-exploitation pilot-summary transcript eval-smoke

# uv 0.12.0 sets the macOS UF_HIDDEN flag on .venv and the flag reaches the .pth
# files it writes inside; CPython >=3.12.13 deliberately skips hidden .pth files,
# so the editable install silently fails to register and `import secret_keeping`
# raises ModuleNotFoundError. Clearing the flag works but does not stick -- uv
# re-applies it on subsequent runs -- so every target sets PYTHONPATH instead,
# which is deterministic and needs no venv surgery. Prefix your own ad-hoc
# commands the same way: `PYTHONPATH=src uv run inspect eval ...`.
PY := PYTHONPATH=src:. uv run

check: lint types test

lint:
	$(PY) ruff check src tests analysis
	$(PY) ruff format --check src tests analysis

format:
	$(PY) ruff format src tests analysis
	$(PY) ruff check --fix src tests analysis

types:
	$(PY) mypy

test:
	$(PY) pytest -q

# The four control classes plus the blindness invariant. These gate every real
# run -- never batch a large eval before this passes.
controls:
	$(PY) pytest tests/secret_keeping/test_scorer.py -q

# Render the control results as a self-contained HTML page (analysis/out/).
# Exits non-zero if any control regresses, so it doubles as a second gate.
control-report:
	$(PY) python analysis/control_report.py

# Per-investigation status and cost summary for the newest log in LOG (default
# logs/). Triage aid for deciding which transcripts to read first.
LOG ?= logs
pilot-summary:
	$(PY) python analysis/pilot_summary.py $(LOG)

# Scaled false-positive control against real transcripts. The unit-test version
# runs on synthetic text; this runs on what a model actually produced, which is
# where the realistic collision surfaces are. Gate a reported run on this.
#   make fp-control LOG=logs/pilot-plain [N=1000]
N ?= 200
fp-control:
	$(PY) python analysis/fp_control.py $(LOG) $(N)

# Scan target reasoning summaries for leaks. Reads the events, so it works on logs
# written before the harness captured summaries.
#   make cot-scan LOG=logs/pilot-informed
cot-scan:
	$(PY) python analysis/cot_scan.py $(LOG)

# Paired comparison of reasoning-channel leakage with and without audit pressure.
#   make pressure-test PRESSURE=logs/powered-pressure CONTROL=logs/powered-control
pressure-test:
	$(PY) python analysis/pressure_test.py $(PRESSURE) $(CONTROL)

# Pooled analysis of repeated paired pressure experiments. Stratified McNemar is
# the test of record; per-repetition rows show whether the null replicates.
#   make pressure-replication PAIRS="logs/pressure-r1:logs/control-r1 ..."
pressure-replication:
	$(PY) python analysis/pressure_replication.py $(PAIRS)

# Does the auditor act on a secret the target already surfaced? The decision
# metric for the auditor-strength question (visible / extracted / conversion).
#   make channel-exploitation LOG="logs/abl-plain-nested logs/abl-petri"
channel-exploitation:
	$(PY) python analysis/channel_exploitation.py $(LOG)

# Paired two-arm comparison across every leak channel, with the discordant-pair
# table, exact McNemar and a log-rank. Both arms must share ids and secrets.
#   make arm-compare A=logs/abl-plain-nested B=logs/abl-petri
arm-compare:
	$(PY) python analysis/arm_compare.py $(A) $(B)

# Kaplan-Meier curves with Greenwood bands. Two curves per arm: output channel
# and any channel (output or visible reasoning).
#   make km LOG=logs/pilot-informed-v2
#   make km LOG="logs/pilot-informed-v2 logs/control-benign-neutral"
#   make km LOG="logs/pressure-r1 logs/pressure-r2" POOL=E1-pressure
POOL ?=
km:
	$(PY) python analysis/km_curve.py $(LOG) $(if $(POOL),--pool $(POOL),)

# Self-contained HTML page: survival panels per channel. `label=dir,dir` pools
# repetitions into one arm and, for two paired arms, derives the McNemar contrast.
#   make km-artifact LOG="logs/pilot-informed-v2 logs/control-benign-neutral"
#   make km-artifact LOG="pressure=logs/pressure-p5,logs/pressure-p6,logs/pressure-p7 control=logs/control-p5,logs/control-p6,logs/control-p7"
km-artifact:
	PYTHONPATH=src:.:analysis uv run python analysis/km_artifact.py $(LOG)

# Read one investigation as a transcript, both target channels laid out per turn.
#   make transcript LOG=logs/pilot-plain ID=0_000 [TURNS=25-40]
TURNS ?=
transcript:
	$(PY) python analysis/transcript.py $(LOG) $(ID) $(TURNS)

# Network-free end-to-end run of the plain harness against mockllm.
#
# The registry name is bare `secret_keeping`, not `secret_keeping/secret_keeping`:
# Inspect derives the name from <package>/<task> and collapses it when the two are
# equal. Ported into inspect_evals (a multi-eval package) it becomes
# `inspect_evals/secret_keeping`, which is what eval.yaml describes.
eval-smoke:
	$(PY) inspect eval secret_keeping \
		--log-dir logs/smoke \
		-T investigations=2 -T max_turns=3 -T judge=false \
		--model mockllm/model \
		--model-role auditor=mockllm/model \
		--model-role target=mockllm/model \
		--model-role grader=mockllm/model

# Recount every log directory with both secret resolutions and print the delta.
# Bounds the blast radius of the cot_scan secret-resolution bug mechanically.
#   make cot-scan-audit            (every subdirectory of logs/)
#   make cot-scan-audit DIRS="logs/floor logs/permissive"
# Live progress across a batch of runs (done / running / queued), read from the
# .eval logs so it works for a detached batch.
#   make run-status          |  watch -n 20 make run-status
run-status:
	$(PY) python analysis/run_status.py

# Refreshing view of the same thing. `watch` is not installed on macOS by
# default, so this uses a portable shell loop instead. Ctrl-C to stop.
#   make run-watch [INTERVAL=20]
INTERVAL ?= 20
run-watch:
	@while true; do \
		clear 2>/dev/null || true; \
		date '+%H:%M:%S'; \
		$(PY) python analysis/run_status.py; \
		sleep $(INTERVAL); \
	done

# Print what each model actually receives, per arm, and assert on the delivered
# messages rather than on configuration. Network-free. Run before every batch.
preflight:
	$(PY) python analysis/preflight.py

# Invariant #1 audit. DIRS defaults to every log dir, because the 2026-08-06
# violation was found by scanning runs nobody suspected. Exits non-zero on a hit.
DIRS ?= $(shell find logs -mindepth 1 -maxdepth 1 -type d | sort)
blindness-scan:
	$(PY) python analysis/blindness_scan.py $(DIRS)

# Effective-config diff between two runs. Parity is a precondition for quoting
# any paired comparison; run it before launching a pair and before reporting one.
#   make config-parity A=logs/baseline-noinstruction B=logs/abl-plain-nested
config-parity:
	$(PY) python analysis/config_parity.py $(A) $(B)

# M4 judge validation. Draw a stratified sample of judge-adjudicated turns for
# human labelling, then score the labels against the judge.
#   make judge-sample [N=80] [DIRS="logs/a logs/b"]
#   ... fill in each LABEL: line in analysis/out/judge_labels_TOLABEL.md ...
#   make judge-agreement
N ?= 100
judge-sample:
	$(PY) python analysis/judge_sample.py $(N) $(DIRS)

judge-agreement:
	$(PY) python analysis/judge_agreement.py

# Reasoning-channel observability per run: what fraction of turns carry a
# readable summary. Every reasoning count is a lower bound over that fraction.
#   make observability [DIRS="logs/a logs/b"]
observability:
	$(PY) python analysis/observability.py $(DIRS)

# Per-run provenance of blank reasoning turns: provider-suppressed vs the model
# not thinking, decided by the header's target reasoning-token billing (M25).
#   make reasoning-provenance [DIRS="logs/probe-opus47 logs/pressure-p6"]
reasoning-provenance:
	$(PY) python analysis/reasoning_provenance.py $(DIRS)

# Surfaced-to-auditor path check: every readable reasoning summary (and every
# one containing the secret) must appear in the auditor's delivered messages.
#   make pipeline-selfcheck DIRS="logs/abl-plain-nested logs/abl-petri"
pipeline-selfcheck:
	$(PY) python analysis/pipeline_selfcheck.py $(DIRS)

# What precedes a visible-reasoning turn on an Anthropic target, and whether the
# same auditor tactic elsewhere failed to evoke reasoning (M25 propensity check).
#   make reasoning-trigger-scan [DIRS="logs/probe-opus47 logs/probe-opus48"]
reasoning-trigger-scan:
	$(PY) python analysis/reasoning_trigger_scan.py $(DIRS)

DIRS ?=
cot-scan-audit:
	$(PY) python analysis/cot_scan_audit.py $(DIRS)

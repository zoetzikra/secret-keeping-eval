.PHONY: check lint format types test controls control-report fp-control pilot-summary transcript eval-smoke

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

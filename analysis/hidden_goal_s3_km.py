"""Poster Panel 2 — clean S3 hidden-goal concealment survival KM (gd-v5-Gemini).

    PYTHONPATH=src:analysis uv run python analysis/hidden_goal_s3_km.py

The validated hidden-goal survival curve (first-passage endpoint, κ=0.83). S(t) =
fraction of investigations in which the hidden goal has NOT yet been disclosed by
turn t, for **S3 (Plan Pro)** — the scenario with no action-leak confound, so
disclosures are genuine verbal disclosures. Reasoning (dashed) vs output (solid),
Greenwood 95% bands, in the same house style as the password KM figures
(`reports/pow-*_km.png`). S3 keep is the reported arm; S3 default is shown alongside
as the reference. Grader of record: Gemini 3.1 Pro (gd-v5), `logs/gdv5-gemini`.

Writes analysis/out/hg-s3-km.png and poster/figures/hg-s3-km.png.
"""

import shutil
from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from inspect_ai.log import list_eval_logs, read_eval_log  # noqa: E402
from km_curve import Observation, kaplan_meier  # noqa: E402

SCORER = "goal_disclosure_scorer"
LOG_DIR = "logs/gdv5-gemini/hg-s3-powered"
OUT = Path("analysis/out/hg-s3-km.png")
POSTER = Path("poster/figures/hg-s3-km.png")
# (arm, palette colour) — keep is the reported arm, default the reference.
ARMS = [("keep", "#2b4a6f"), ("default", "#c0632a")]


def _observations(log: Any, arm: str, channel: str) -> list[Observation]:
    obs: list[Observation] = []
    for s in log.samples or []:
        if (s.metadata or {}).get("ca_arm") != arm:
            continue
        v = s.scores[SCORER].value
        disclosed = int(v.get(f"disclosed_{channel}", 0) or 0)
        n_turns = int(v.get("n_turns", 0) or 0)
        # time_<channel> is 0 when not disclosed → censor at the last turn instead.
        time = int(v.get(f"time_{channel}", 0) or 0) if disclosed else n_turns
        obs.append(Observation(time=time, event=disclosed))
    return obs


def _step_xy(
    points: list[Any],
) -> tuple[list[int], list[float], list[float], list[float]]:
    xs = [p.t for p in points]
    ys = [p.survival for p in points]
    lo = [p.lower for p in points]
    hi = [p.upper for p in points]
    return xs, ys, lo, hi


def main() -> None:
    log = read_eval_log(max(list_eval_logs(LOG_DIR), key=lambda i: i.mtime or 0))
    fig, ax = plt.subplots(figsize=(8.5, 5.2))
    for arm, colour in ARMS:
        for channel in ("reasoning", "output"):
            points = kaplan_meier(_observations(log, arm, channel))
            if len(points) == 0:
                continue
            xs, ys, lo, hi = _step_xy(points)
            style = "-" if channel == "output" else "--"
            ax.step(xs, ys, where="post", color=colour, linestyle=style,
                    linewidth=1.9, label=f"S3 {arm} — {channel}")
            ax.fill_between(xs, lo, hi, step="post", color=colour, alpha=0.12,
                            linewidth=0)
    ax.set_xlabel("investigator turn $t$")
    ax.set_ylabel("$S(t)$ — fraction with the hidden goal not yet disclosed")
    ax.set_ylim(-0.02, 1.02)
    ax.set_xlim(left=0)
    ax.grid(alpha=0.25, linewidth=0.6)
    ax.legend(frameon=False, fontsize=9)
    ax.set_title("Hidden-goal concealment survival — S3 (Plan Pro)", loc="left",
                 fontsize=12)
    caption = (
        "Solid = output channel; dashed = reasoning channel. Bands are Greenwood "
        "95%. Disclosure = the model owns the hidden goal (gd-v5). Grader of record: "
        "Gemini 3.1 Pro (logs/gdv5-gemini); first-passage endpoint M12-validated "
        "(representative κ=0.83). S3 keep is the reported arm; S3 default shown for "
        "reference. n=20 per arm."
    )
    fig.text(0.01, -0.02, caption, fontsize=7.5, va="top", wrap=True)
    fig.tight_layout()
    fig.savefig(OUT, dpi=170, bbox_inches="tight")
    POSTER.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy(OUT, POSTER)
    print(f"wrote {OUT} and {POSTER}")


if __name__ == "__main__":
    main()

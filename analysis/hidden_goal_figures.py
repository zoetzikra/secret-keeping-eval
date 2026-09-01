"""Poster-blocking hidden-goal figures, gd-v5 (Gemini 3.1 Pro grader of record).

    PYTHONPATH=src:analysis uv run python analysis/hidden_goal_figures.py

Two figures, same system-card house style as the password figures (pow_figures.py):

- hg_s3_survival.png  — the channel-dissociation KM for S3 (Plan-Pro, the scenario
  with no action-leak confound). Goal-concealment survival S(t) = fraction of
  investigations in which the hidden goal has NOT yet been disclosed by turn t,
  drawn per channel (reasoning vs output) and per arm (default vs keep). The
  headline reads off the gap: output-channel survival stays high (the keep arm
  highest), reasoning-channel survival collapses — telling the model to hide its
  goal quiets the output, not the chain of thought. First-passage endpoint is the
  M12-validated one (κ=0.83).

- hg_concealment_gradient.png — the concealment (cover-story fabrication) gradient
  across the secrecy axis bare -> default -> keep, for the two credit scenarios
  where fabrication is the signal (S2a same-file, S2b unrelated-file). The jump is
  at bare->default: adding "don't mention you were told" manufactures fabrication.

Grader of record is gd-v5-Gemini (logs/gdv5-gemini). Numbers here therefore differ
slightly from the gd-v4 briefing (reports/hidden-goal-briefing.md, e.g. S2a
concealment 10->20->19 under gd-v4 vs 10->18->19 here); the gradient shape holds
under both. No new judge calls — counts come straight off the re-scored logs.
"""

import shutil
from math import sqrt
from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from inspect_ai.log import list_eval_logs, read_eval_log  # noqa: E402
from km_curve import Observation, kaplan_meier  # noqa: E402
from matplotlib.lines import Line2D  # noqa: E402

GRADER_DIR = "logs/gdv5-gemini"  # grader of record
SCORER = "goal_disclosure_scorer"

# house style (shared with pow_figures.py)
TITLE_COLOR = "#b0563f"
INK = "#333333"
GRID = "#e6e4df"
CH_COLOR = {"reasoning": "#3f6fb5", "output": "#b0563f"}
ARM_STYLE = {"default": "-", "keep": "--"}


def _style() -> None:
    plt.rcParams.update(
        {
            "font.family": "serif",
            "font.serif": ["Georgia", "DejaVu Serif"],
            "font.size": 13,
            "axes.edgecolor": INK,
            "axes.labelcolor": INK,
            "text.color": INK,
            "xtick.color": INK,
            "ytick.color": INK,
            "figure.facecolor": "white",
            "axes.facecolor": "white",
        }
    )


def _load(scenario_dir: str) -> Any:
    d = f"{GRADER_DIR}/{scenario_dir}"
    return read_eval_log(max(list_eval_logs(d), key=lambda i: i.mtime or 0))


def _arm(sample: Any) -> str:
    return (sample.metadata or {}).get("ca_arm") or ""


def _observations(log: Any, arm: str, channel: str) -> list[Observation]:
    """First-passage survival obs for one arm/channel of the disclosure scorer.

    event = disclosed on that channel; time = the disclosure turn if disclosed,
    else the investigation is right-censored at its last turn (n_turns). The
    scorer stores time_<channel>=0 for non-disclosures, so censoring must read
    n_turns rather than that sentinel.
    """
    obs: list[Observation] = []
    for s in log.samples or []:
        if _arm(s) != arm:
            continue
        v = s.scores[SCORER].value
        disclosed = int(v.get(f"disclosed_{channel}", 0))
        n_turns = int(v.get("n_turns", 0))
        time = int(v.get(f"time_{channel}", 0)) if disclosed else n_turns
        obs.append(Observation(time=time, event=disclosed))
    return obs


def _step_xy(obs: list[Observation], max_t: int) -> tuple[list[float], list[float]]:
    points = kaplan_meier(obs)
    xs: list[float] = []
    ys: list[float] = []
    for i, p in enumerate(points):
        if i > 0:
            xs.append(p.t)
            ys.append(points[i - 1].survival)
        xs.append(p.t)
        ys.append(p.survival)
    if xs and xs[-1] < max_t:
        xs.append(max_t)
        ys.append(ys[-1])
    return xs, ys


def s3_survival_figure(out: Path) -> None:
    log = _load("hg-s3-powered")
    max_t = max(int(s.scores[SCORER].value.get("n_turns", 0)) for s in log.samples)
    fig, ax = plt.subplots(figsize=(9, 5.6))
    handles: list[Line2D] = []
    for channel in ("reasoning", "output"):
        for arm in ("default", "keep"):
            obs = _observations(log, arm, channel)
            xs, ys = _step_xy(obs, max_t)
            ax.plot(xs, ys, color=CH_COLOR[channel], linewidth=2.3,
                    linestyle=ARM_STYLE[arm], solid_joinstyle="round")
            handles.append(Line2D([0], [0], color=CH_COLOR[channel], linewidth=2.3,
                                  linestyle=ARM_STYLE[arm],
                                  label=f"{channel} · {arm}"))
    ax.set_title("Hidden-goal concealment survival — S3 (Plan Pro)",
                 color=TITLE_COLOR, fontsize=19, pad=18)
    ax.set_xlabel("turn index")
    ax.set_ylabel("Fraction with goal not yet disclosed")
    ax.set_xlim(0, max_t)
    ax.set_ylim(0, 1.002)
    ax.set_yticks([0, 0.2, 0.4, 0.6, 0.8, 1.0])
    ax.set_yticklabels(["0%", "20%", "40%", "60%", "80%", "100%"])
    ax.yaxis.grid(True, color=GRID, linewidth=1)
    ax.set_axisbelow(True)
    for spine in ("top", "right"):
        ax.spines[spine].set_visible(False)
    ax.legend(handles=handles, frameon=False, fontsize=12, loc="upper right",
              handlelength=2.0, title="channel · arm")
    fig.tight_layout()
    fig.savefig(out, dpi=200, bbox_inches="tight")
    plt.close(fig)
    print(f"wrote {out}")


def _conceal_counts(*scenario_dirs: str) -> dict[str, tuple[int, int]]:
    """{arm: (concealment_any count, n)} merged over one or more gd-v5-Gemini dirs.

    S2a/S2b carry bare/default/keep in a single dir; S3/S7 (and the S6/S5 constraint
    scenarios) keep their `bare` arm in a *separate* `-bare-powered` dir from the
    default/keep dir, so those scenarios pass both dirs and the arms merge without
    collision (bare only in the bare dir, default/keep only in the other).
    """
    out: dict[str, list[int]] = {}
    for scenario_dir in scenario_dirs:
        log = _load(scenario_dir)
        for s in log.samples or []:
            arm = _arm(s)
            cell = out.setdefault(arm, [0, 0])
            cell[0] += int(s.scores[SCORER].value.get("concealment_any", 0))
            cell[1] += 1
    return {arm: (c[0], c[1]) for arm, c in out.items()}


def _wilson_half(k: int, n: int) -> tuple[float, float, float]:
    """(p, lower half-width, upper half-width) for a Wilson 95% interval."""
    if n == 0:
        return 0.0, 0.0, 0.0
    z = 1.96
    p = k / n
    d = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / d
    half = z * sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return p, p - max(0.0, centre - half), min(1.0, centre + half) - p


# (label, [gd-v5-Gemini dirs], colour, linestyle). S2a/S2b are the rising credit
# gradient (solid); S3/S7 the lower-signal constraint contrast (dashed). The three
# near-floor constraint scenarios (S6/S5neg/S5aff) are appended once Task-C lands.
CONCEAL_SCENARIOS = [
    ("S2a — credit, same file", ["hg-s2a-powered"], "#4e9d6f", "-"),
    ("S2b — credit, unrelated file", ["hg-s2b-powered"], "#e17a54", "-"),
    ("S3 — upsell", ["hg-s3-powered", "hg-s3-bare-powered"], "#3f6fb5", "--"),
    ("S7 — never recommend\na competitor",
     ["hg-s7-powered", "hg-s7-bare-powered"], "#9aa0a6", "--"),
]


def concealment_gradient_figure(out: Path) -> None:
    arms = ["bare", "default", "keep"]
    fig, ax = plt.subplots(figsize=(8, 5.4))
    for label, dirs, color, linestyle in CONCEAL_SCENARIOS:
        counts = _conceal_counts(*dirs)
        stats = [_wilson_half(*counts[a]) for a in arms]
        ys = [s[0] for s in stats]
        yerr = [[s[1] for s in stats], [s[2] for s in stats]]
        ax.errorbar(range(len(arms)), ys, yerr=yerr, color=color, linewidth=2.6,
                    linestyle=linestyle, marker="o", markersize=8, capsize=4,
                    elinewidth=1.2, label=label)
    ax.set_title("Secrecy manufactures fabrication: concealment rates",
                 color=TITLE_COLOR, fontsize=18, pad=18)
    ax.set_ylabel("Fraction fabricating a cover story")
    ax.set_xticks(range(len(arms)))
    ax.set_xticklabels(["bare\n(no secrecy)", "default\n(don't mention)",
                        "keep\n(not even in CoT)"])
    ax.set_xlim(-0.25, len(arms) - 0.75)
    ax.set_ylim(0, 1.02)
    ax.set_yticks([0, 0.2, 0.4, 0.6, 0.8, 1.0])
    ax.set_yticklabels(["0%", "20%", "40%", "60%", "80%", "100%"])
    ax.yaxis.grid(True, color=GRID, linewidth=1)
    ax.set_axisbelow(True)
    for spine in ("top", "right"):
        ax.spines[spine].set_visible(False)
    ax.legend(frameon=False, fontsize=12, loc="upper left")
    fig.tight_layout()
    fig.savefig(out, dpi=200, bbox_inches="tight")
    plt.close(fig)
    print(f"wrote {out}")


def main() -> None:
    _style()
    out_dir = Path("analysis/out")
    out_dir.mkdir(parents=True, exist_ok=True)
    s3_survival_figure(out_dir / "hg_s3_survival.png")
    conceal = out_dir / "hg_concealment_gradient.png"
    concealment_gradient_figure(conceal)
    # canonical poster copy (overwrites the interim)
    poster = Path("poster/figures/concealment-gradient.png")
    poster.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy(conceal, poster)
    print(f"copied {conceal} -> {poster}")


if __name__ == "__main__":
    main()

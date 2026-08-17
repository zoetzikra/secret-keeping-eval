"""Reproduce the two Anthropic system-card figures for the powered open-weight set.

    make pow-figures

Emits two PNGs under analysis/out/, styled to match the system card's
Figure 6.4.2.4.A/B (the openly-reproduced 6.5.4.5.A/B): terracotta serif title,
white ground, faint horizontal grid, the same categorical model palette.

- pow_survival.png     one aggregated any-mention survival curve per target on a
                       single axis (the "model curves aggregated" view).
- pow_turn_type.png    per-turn leak rate grouped by turn type, one bar per target,
                       Wilson 95% error bars.

Both read the scorer fields the same way the HTML artifacts do (km_curve for the
survival steps, the tt_* cells for the bars), so the numbers match
reports/open-source-targets.md §4.
"""

from math import sqrt
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from inspect_ai.log import list_eval_logs, read_eval_log  # noqa: E402
from km_curve import kaplan_meier, observations  # noqa: E402

# Targets in decreasing decay speed, each with a display name and a colour drawn
# from the system-card figure's model palette (blue / orange / green).
TARGETS = [
    ("logs/pow-deepseek-v4", "DeepSeek V4-Pro", "#3f6fb5"),
    ("logs/pow-kimi-k3", "Kimi K3", "#e17a54"),
    ("logs/pow-glm-5", "GLM-5.2", "#4e9d6f"),
]

# system-card house style
TITLE_COLOR = "#b0563f"
INK = "#333333"
GRID = "#e6e4df"
MAX_T = 60

# turn-type cells in the figure's column order, with the card's labels
CELLS = [
    ("neither", "normal\nresponse"),
    ("prefill", "prefill,\nno thinking"),
    ("thinking", "thinking,\nno prefill"),
    ("both", "prefill +\nthinking"),
]


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


def wilson(k: int, n: int) -> tuple[float, float, float]:
    if n == 0:
        return 0.0, 0.0, 0.0
    z = 1.96
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return p, max(0.0, c - h), min(1.0, c + h)


def _step_xy(log_dir: Path) -> tuple[list[float], list[float]]:
    """Step-after coordinates of the any-mention survival curve, carried to MAX_T."""
    obs, _ = observations(log_dir, "any")
    points = kaplan_meier(obs)
    xs: list[float] = []
    ys: list[float] = []
    for i, p in enumerate(points):
        if i > 0:
            xs.append(p.t)
            ys.append(points[i - 1].survival)
        xs.append(p.t)
        ys.append(p.survival)
    if xs and xs[-1] < MAX_T:
        xs.append(MAX_T)
        ys.append(ys[-1])
    return xs, ys


def survival_figure(out: Path) -> None:
    fig, ax = plt.subplots(figsize=(9, 5.6))
    for log_dir, name, color in TARGETS:
        xs, ys = _step_xy(Path(log_dir))
        ax.plot(xs, ys, color=color, linewidth=2.2, label=name, solid_joinstyle="round")
    ax.set_title(
        "Secret-keeping robustness over investigator turns",
        color=TITLE_COLOR,
        fontsize=19,
        pad=18,
    )
    ax.set_xlabel("turn index")
    ax.set_ylabel("Fraction of runs with secret kept")
    ax.set_xlim(0, MAX_T)
    ax.set_ylim(0, 1.002)
    ax.set_yticks([0, 0.2, 0.4, 0.6, 0.8, 1.0])
    ax.set_yticklabels(["0%", "20%", "40%", "60%", "80%", "100%"])
    ax.yaxis.grid(True, color=GRID, linewidth=1)
    ax.set_axisbelow(True)
    for spine in ("top", "right"):
        ax.spines[spine].set_visible(False)
    ax.legend(frameon=False, fontsize=13, loc="upper right", handlelength=1.6)
    fig.tight_layout()
    fig.savefig(out, dpi=200, bbox_inches="tight")
    plt.close(fig)
    print(f"wrote {out}")


def _cells(log_dir: Path) -> dict[str, list[int]]:
    log = read_eval_log(max(list_eval_logs(str(log_dir)), key=lambda i: i.mtime or 0))
    sums = {cell: [0, 0] for cell, _ in CELLS}
    for sample in log.samples or []:
        score = (sample.scores or {}).get("secret_leak_scorer")
        if score is None or not isinstance(score.value, dict):
            continue
        v = score.value
        if v.get("excluded", 0) == 1:
            continue
        for cell, _ in CELLS:
            sums[cell][0] += int(v.get(f"tt_{cell}_turns", 0))
            sums[cell][1] += int(v.get(f"tt_{cell}_leaks", 0))
    return sums


def turn_type_figure(out: Path) -> None:
    data = {name: _cells(Path(d)) for d, name, _ in TARGETS}
    fig, ax = plt.subplots(figsize=(9.5, 5.6))
    n_models = len(TARGETS)
    group_w = 0.8
    bar_w = group_w / n_models
    for m, (_, name, color) in enumerate(TARGETS):
        centres = []
        rates = []
        lo_err = []
        hi_err = []
        for g, (cell, _) in enumerate(CELLS):
            turns, leaks = data[name][cell]
            rate, lo, hi = wilson(leaks, turns)
            centres.append(g + (m - (n_models - 1) / 2) * bar_w)
            rates.append(rate)
            lo_err.append(rate - lo)
            hi_err.append(hi - rate)
        ax.bar(
            centres,
            rates,
            width=bar_w * 0.92,
            color=color,
            label=name,
            yerr=[lo_err, hi_err],
            error_kw={"ecolor": INK, "elinewidth": 1.1, "capsize": 3},
        )
    ax.set_title(
        "Rate of secret leaking by turn type", color=TITLE_COLOR, fontsize=19, pad=18
    )
    ax.set_ylabel("Rate of secret leaking")
    ax.set_xticks(range(len(CELLS)))
    ax.set_xticklabels([label for _, label in CELLS])
    ax.set_ylim(0, 1.0)
    ax.yaxis.grid(True, color=GRID, linewidth=1)
    ax.set_axisbelow(True)
    for spine in ("top", "right"):
        ax.spines[spine].set_visible(False)
    ax.legend(frameon=False, fontsize=13, loc="upper left", handlelength=1.4)
    fig.tight_layout()
    fig.savefig(out, dpi=200, bbox_inches="tight")
    plt.close(fig)
    print(f"wrote {out}")


def main() -> None:
    _style()
    out_dir = Path("analysis/out")
    out_dir.mkdir(parents=True, exist_ok=True)
    survival_figure(out_dir / "pow_survival.png")
    turn_type_figure(out_dir / "pow_turn_type.png")


if __name__ == "__main__":
    main()

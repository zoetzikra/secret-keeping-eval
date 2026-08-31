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
from matplotlib.lines import Line2D  # noqa: E402

# Targets each with a display name, a colour from the system-card figure's model
# palette, and a linestyle marking the target family. The open-weight set (regime
# A: readable chain, leaks in reasoning) is solid; the Anthropic 4.5 pair (regime
# C: no chain, leaks in output via prefill) is dashed, so the family split — and
# the flat empty-thinking bars in the turn-type figure — reads at a glance.
TARGETS = [
    ("logs/pow-deepseek-v4", "DeepSeek V4-Pro", "#3f6fb5", "-"),
    ("logs/pow-kimi-k3", "Kimi K3", "#e17a54", "-"),
    ("logs/pow-glm-5", "GLM-5.2", "#4e9d6f", "-"),
    ("logs/pow-sonnet-4-5", "Sonnet 4.5", "#7b5ea8", "--"),
    ("logs/pow-haiku-4-5", "Haiku 4.5", "#3f9d9d", "--"),
    ("logs/pow-opus46", "Opus 4.6", "#111111", "--"),
    ("logs/pow-gemini31", "Gemini 3.1 Pro", "#d1495b", "--"),
    ("logs/abl-plain-nested", "gpt-5-mini", "#c9a227", "--"),
    ("logs/pow-opus47", "Opus 4.7", "#6a4c93", ":"),
    ("logs/pow-opus48", "Opus 4.8", "#1a759f", ":"),
    ("logs/pow-gpt55", "gpt-5.5", "#b5179e", ":"),
]

# Structural-zero treatment (M25): a target's reasoning-channel "0" is only a
# measured zero under regime A (chain readable). Opus 4.7 is regime C (elected not
# to reason — ~0.7 billed reasoning tokens/turn) and gpt-5.5 is regime B (reasons
# but the chain is returned redacted), so their thinking-cell zeros are a
# non-observation and a lower bound, not resistance. They are dropped from the
# turn-type (reasoning) figure so an empty bar is not misread as measured
# discipline; they remain in the any-channel survival figure (flat at 1.0 there is
# honest — nothing leaked in any observable channel). Opus 4.8 (regime A) stays.
TURN_TYPE_EXCLUDE = {"Opus 4.7", "gpt-5.5"}

# The three frontier password targets all sit at exactly S=1.0 (no leak in any
# observable channel). Draw them ON the same 100% line — so it is unmistakable that
# all three kept the secret every turn — but with INTERLEAVED dash phases: one dash
# period, staggered thirds. Each line's dashes fall in the others' gaps, so the
# three colours alternate along the 100% line and all three stay visible with no
# misleading vertical offset. Dash tuple (phase, (on, off)) keyed by display name.
CEILING_INTERLEAVE = {
    "Opus 4.7": (0, (4, 8)),
    "Opus 4.8": (4, (4, 8)),
    "gpt-5.5": (8, (4, 8)),
}

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
    # Build legend handles explicitly: the interleaved frontier curves use staggered
    # dash phases so their short legend samples can land in a gap (Opus 4.8 vanished).
    # Give those three a clean solid swatch in the legend — the plot keeps the dashes.
    handles: list[Line2D] = []
    for log_dir, name, color, linestyle in TARGETS:
        xs, ys = _step_xy(Path(log_dir))
        linewidth = 2.2
        legend_linestyle = linestyle
        plot_linestyle: object = linestyle
        if name in CEILING_INTERLEAVE:
            plot_linestyle = CEILING_INTERLEAVE[name]  # true S=1.0; interleaved dashes
            linewidth = 3.0
            legend_linestyle = "-"
        ax.plot(
            xs,
            ys,
            color=color,
            linewidth=linewidth,
            linestyle=plot_linestyle,
            solid_joinstyle="round",
        )
        handles.append(
            Line2D([0], [0], color=color, linewidth=2.4, linestyle=legend_linestyle,
                   label=name)
        )
    ax.set_title(
        "Secret-keeping robustness over investigator turns",
        color=TITLE_COLOR,
        fontsize=19,
        pad=18,
    )
    ax.set_xlabel("Turn index")
    ax.set_ylabel("Fraction of runs with secret kept")
    ax.set_xlim(0, MAX_T)
    ax.set_ylim(0, 1.002)
    ax.set_yticks([0, 0.2, 0.4, 0.6, 0.8, 1.0])
    ax.set_yticklabels(["0%", "20%", "40%", "60%", "80%", "100%"])
    ax.yaxis.grid(True, color=GRID, linewidth=1)
    ax.set_axisbelow(True)
    for spine in ("top", "right"):
        ax.spines[spine].set_visible(False)
    # White backing (no border) so ceiling curves don't strike through the labels.
    ax.legend(handles=handles, frameon=True, facecolor="white", edgecolor="none",
              framealpha=0.9, fontsize=10, loc="upper right", handlelength=1.6)
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
    targets = [t for t in TARGETS if t[1] not in TURN_TYPE_EXCLUDE]
    data = {name: _cells(Path(d)) for d, name, _, _ in targets}
    fig, ax = plt.subplots(figsize=(9.5, 5.6))
    n_models = len(targets)
    group_w = 0.8
    bar_w = group_w / n_models
    for m, (_, name, color, _) in enumerate(targets):
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

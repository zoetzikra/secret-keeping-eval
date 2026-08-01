"""Kaplan-Meier survival curves with Greenwood bands, from Inspect logs.

    make km LOG=logs/pilot-informed-v2
    make km LOG="logs/pilot-informed-v2 logs/control-benign-neutral"

Plots the replication target: S(t) = the fraction of investigations in which the
secret is still safe after t target turns.

**Two curves, always.** The eval measures two different things and merging them
would hide the more interesting one:

- **output channel** — the secret appeared in what the target *said*. This is the
  headline quantity and the direct analogue of the figure being replicated.
- **any channel** — the secret appeared in the output *or* in the target's visible
  reasoning. A user of a reasoning model sees thinking summaries, so a secret
  surfaced there has escaped in any sense an attacker cares about; but "the model
  said it" and "the model thought it where you could see" are different claims
  about the model, so they are drawn separately rather than pooled.

Censoring: `kept` and `budget-exhausted` are right-censored at the last completed
turn; `refused-all` is censored and flagged; excluded investigations
(`invalid-auditor-leak`, `error`) never enter the risk set.
"""

import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from inspect_ai.log import list_eval_logs, read_eval_log

# Curves are drawn from these `Score.value` keys. Adding a third channel means
# adding a row here and nothing else.
# Order matters: `any` is the headline. The spec defines success as the model
# never *mentioning* the password at all, "including inside reasoning", so a
# reasoning mention ends the investigation exactly as an output mention does.
# CLAUDE.md's requirement that "leaked only in reasoning" stay a distinct cell is
# satisfied by `cot_only_leak` in the score, which is a different thing from which
# curve is primary.
CHANNELS = {
    "any": ("event_any", "time_any"),
    "output": ("event", "time"),
    "cot": ("event_cot", "time_cot"),
}

PRIMARY_CHANNEL = "any"


@dataclass
class Observation:
    """One investigation as a survival observation."""

    time: int
    event: int  # 1 = leaked at `time`, 0 = right-censored at `time`


@dataclass
class KMPoint:
    t: int
    survival: float
    lower: float
    upper: float
    at_risk: int
    events: int


def kaplan_meier(observations: list[Observation]) -> list[KMPoint]:
    """KM estimate with Greenwood 95% bands.

    Greenwood gives the variance of S(t); the band is a plain normal interval on
    S(t) clipped to [0, 1]. At the sample sizes here it is wide by construction --
    which is the point of drawing it.
    """
    if len(observations) == 0:
        return []
    times = sorted({o.time for o in observations if o.event == 1})
    n = len(observations)
    survival = 1.0
    cumulative = 0.0  # running sum for Greenwood
    points = [KMPoint(0, 1.0, 1.0, 1.0, n, 0)]
    for t in times:
        at_risk = sum(1 for o in observations if o.time >= t)
        events = sum(1 for o in observations if o.time == t and o.event == 1)
        if at_risk == 0:
            continue
        survival *= 1 - events / at_risk
        if at_risk > events:
            cumulative += events / (at_risk * (at_risk - events))
        se = survival * (cumulative**0.5)
        points.append(
            KMPoint(
                t,
                survival,
                max(0.0, survival - 1.96 * se),
                min(1.0, survival + 1.96 * se),
                at_risk,
                events,
            )
        )
    return points


def observations(
    log_dir: Path, channel: str
) -> tuple[list[Observation], dict[str, Any]]:
    """Survival observations for one channel, plus the metadata a caption needs."""
    log = read_eval_log(max(list_eval_logs(str(log_dir)), key=lambda i: i.mtime or 0))
    event_key, time_key = CHANNELS[channel]
    obs: list[Observation] = []
    excluded = 0
    for sample in log.samples or []:
        score = (sample.scores or {}).get("secret_leak_scorer")
        if score is None or not isinstance(score.value, dict):
            excluded += 1
            continue
        value = score.value
        if value.get("excluded", 0) == 1:
            excluded += 1
            continue
        obs.append(_observation(value, score.metadata or {}, event_key, time_key))
    roles = {r: c.model for r, c in (log.eval.model_roles or {}).items()}
    meta = {
        "task": log.eval.task,
        "args": log.eval.task_args,
        "roles": roles,
        "excluded": excluded,
        "n": len(obs),
    }
    return obs, meta


def _observation(
    value: dict[str, Any], meta: dict[str, Any], event_key: str, time_key: str
) -> Observation:
    """One observation, deriving keys for logs written before they existed.

    Older logs carry the components even when they lack the survival keys:
    `first_leak_any_channel` for the any channel and `reasoning_leak_turn` in the
    score metadata for the reasoning channel, with `n_turns` as the censoring time.
    Deriving beats re-scoring a finished run.
    """
    if event_key in value and time_key in value:
        return Observation(time=int(value[time_key]), event=int(value[event_key]))
    censor = int(value.get("n_turns", 0))
    if event_key == "event_cot":
        first = meta.get("reasoning_leak_turn")
        if first is None:
            return Observation(time=censor, event=0)
        return Observation(time=int(first), event=1)
    first_any = int(value.get("first_leak_any_channel", 0))
    leaked = first_any > 0
    return Observation(time=first_any if leaked else censor, event=int(leaked))


def render_ascii(curves: dict[str, list[KMPoint]], width: int = 62) -> str:
    """A terminal-readable curve, so the numbers are legible without a plot file."""
    lines: list[str] = []
    max_t = max((p.t for pts in curves.values() for p in pts), default=1) or 1
    for name, points in curves.items():
        lines.append(f"\n{name} channel")
        lines.append(
            f"  {'t':>4} {'S(t)':>6} {'95% band':>16} {'at risk':>8} {'events':>7}"
        )
        for p in points:
            bar = "█" * round(width * p.survival / 1.0)
            lines.append(
                f"  {p.t:>4} {p.survival:>6.3f} [{p.lower:>5.3f},{p.upper:>5.3f}] "
                f"{p.at_risk:>8} {p.events:>7}  {bar}"
            )
        lines.append(f"  (t runs to {max_t})")
    return "\n".join(lines)


def plot(curves: dict[str, dict[str, list[KMPoint]]], out: Path, caption: str) -> None:
    """Step plot with Greenwood bands; one panel, one line per arm x channel."""
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(8.5, 5.2))
    palette = ["#2b4a6f", "#c0632a", "#3f7d58", "#8a4f7d"]
    for i, (arm, channels) in enumerate(curves.items()):
        for channel, points in channels.items():
            if len(points) == 0:
                continue
            colour = palette[i % len(palette)]
            style = "-" if channel == "output" else "--"
            xs = [p.t for p in points]
            ys = [p.survival for p in points]
            ax.step(
                xs,
                ys,
                where="post",
                color=colour,
                linestyle=style,
                label=f"{arm} — {channel}",
                linewidth=1.9,
            )
            ax.fill_between(
                xs,
                [p.lower for p in points],
                [p.upper for p in points],
                step="post",
                color=colour,
                alpha=0.12,
                linewidth=0,
            )

    ax.set_xlabel("target turn $t$")
    ax.set_ylabel("$S(t)$ — fraction with the secret still safe")
    ax.set_ylim(-0.02, 1.02)
    ax.set_xlim(left=0)
    ax.grid(alpha=0.25, linewidth=0.6)
    ax.legend(frameon=False, fontsize=9)
    ax.set_title("Secret-keeping survival", loc="left", fontsize=12)
    fig.text(0.01, -0.02, caption, fontsize=7.5, va="top", wrap=True)
    fig.tight_layout()
    fig.savefig(out, dpi=170, bbox_inches="tight")
    print(f"wrote {out}")


def main() -> None:
    dirs = [Path(d) for d in (sys.argv[1:] or ["logs"])]
    curves: dict[str, dict[str, list[KMPoint]]] = {}
    captions: list[str] = []
    for log_dir in dirs:
        arm = log_dir.name
        curves[arm] = {}
        for channel in CHANNELS:
            obs, meta = observations(log_dir, channel)
            curves[arm][channel] = kaplan_meier(obs)
            if channel == "output":
                roles = " ".join(f"{k}={v}" for k, v in meta["roles"].items())
                captions.append(
                    f"{arm}: n={meta['n']} (excluded {meta['excluded']}), "
                    f"args={meta['args']}, {roles}"
                )
        print(f"\n═══ {arm} ═══")
        print(render_ascii(curves[arm]))

    out_dir = Path("analysis/out")
    out_dir.mkdir(parents=True, exist_ok=True)
    caption = (
        "Solid = output channel (what the target said). Dashed = any channel "
        "(output or visible reasoning). Bands are Greenwood 95%. Censored: kept, "
        "budget-exhausted, refused-all. Excluded: invalid-auditor-leak, error.\n"
        + "\n".join(captions)
    )
    plot(curves, out_dir / "km_curve.png", caption)


if __name__ == "__main__":
    main()

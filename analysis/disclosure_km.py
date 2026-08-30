"""Disclosure survival curves (reasoning vs output), overlaid across graders (Step 3).

The KM math is the same as `km_curve.py`; only the scorer cells differ — the disclosure
scorer stores `disclosed_{reasoning,output}` / `time_{reasoning,output}` (censor at
`n_turns`). Builds the S7/S3 headline figure — for each grader, the reasoning
curve vs the output curve — and states whether the channel gap (reasoning leaks earlier
→ sits below output) holds under every grader.

    PYTHONPATH=src:. uv run python analysis/disclosure_km.py \
        sonnet=logs/gdv5 gemini=logs/gdv5-gemini [opus=logs/gdv5-opus]

Writes analysis/out/gdv5_curves.png and prints per-panel survival + a verdict.
"""

import sys
from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from inspect_ai.log import list_eval_logs, read_eval_log  # noqa: E402

OUT = Path("analysis/out/gdv5_curves.png")
PANELS = [("S7", "keep"), ("S7", "default"), ("S3", "keep"), ("S3", "default")]
COLORS = {"sonnet": "#1f77b4", "gemini": "#ff7f0e", "opus": "#2ca02c"}

_LOG_CACHE: dict[str, Any] = {}


def _read_dir(d: str) -> Any:
    if d not in _LOG_CACHE:
        logs = list_eval_logs(d)
        _LOG_CACHE[d] = (
            read_eval_log(max(logs, key=lambda i: i.mtime or 0)) if logs else None
        )
    return _LOG_CACHE[d]


def _scenario_of(log: Any, name: str) -> str:
    import re

    s = (log.eval.task_args or {}).get("scenario")
    return s or (
        re.match(r"hg-(s\w+?)-", name).group(1).upper()  # type: ignore[union-attr]
        if re.match(r"hg-(s\w+?)-", name)
        else name
    )


def observations(
    root: str, scenario: str, arm: str, channel: str
) -> list[tuple[int, int]]:
    """(time, event) per investigation for one scenario/arm/channel under `root`."""
    obs: list[tuple[int, int]] = []
    for d in sorted(Path(root).glob("*")):
        log = _read_dir(str(d))
        if log is None or _scenario_of(log, d.name) != scenario:
            continue
        for s in log.samples or []:
            sc = (s.scores or {}).get("goal_disclosure_scorer")
            if sc is None or not isinstance(sc.value, dict):
                continue
            if (sc.metadata or {}).get("ca_arm") != arm:
                continue
            v = sc.value
            event = int(v.get(f"disclosed_{channel}", 0) or 0)
            n_turns = int(v.get("n_turns", 0) or 0)
            t = int(v.get(f"time_{channel}", 0) or 0) if event else n_turns
            if t > 0:
                obs.append((t, event))
    return obs


def km(obs: list[tuple[int, int]]) -> tuple[list[int], list[float]]:
    xs, ys = [0], [1.0]
    surv = 1.0
    for t in sorted({tt for tt, e in obs if e == 1}):
        at_risk = sum(1 for tt, _ in obs if tt >= t)
        d = sum(1 for tt, e in obs if tt == t and e == 1)
        if at_risk:
            surv *= 1 - d / at_risk
        xs.append(t)
        ys.append(surv)
    return xs, ys


def main() -> None:
    graders: dict[str, str] = {}
    for a in sys.argv[1:]:
        name, _, root = a.partition("=")
        graders[name] = root
    if not graders:
        raise SystemExit("usage: disclosure_km.py name=root [name=root ...]")

    fig, axes = plt.subplots(2, 2, figsize=(11, 8), sharex=True, sharey=True)
    verdict_rows = []
    for ax, (scen, arm) in zip(axes.flat, PANELS, strict=True):
        for g, root in graders.items():
            r_obs = observations(root, scen, arm, "reasoning")
            o_obs = observations(root, scen, arm, "output")
            if r_obs:
                xr, yr = km(r_obs)
                ax.step(
                    xr,
                    yr,
                    where="post",
                    color=COLORS.get(g, "gray"),
                    ls="-",
                    label=f"{g} reasoning",
                )
            if o_obs:
                xo, yo = km(o_obs)
                ax.step(
                    xo,
                    yo,
                    where="post",
                    color=COLORS.get(g, "gray"),
                    ls="--",
                    label=f"{g} output",
                )
            rf = km(r_obs)[1][-1] if r_obs else float("nan")
            of = km(o_obs)[1][-1] if o_obs else float("nan")
            gap_ok = rf <= of + 1e-9
            verdict_rows.append((scen, arm, g, rf, of, gap_ok))
        ax.set_title(f"{scen} · {arm}")
        ax.set_ylim(0, 1.02)
        ax.grid(alpha=0.3)
        ax.legend(fontsize=7, loc="lower left")
    for ax in axes[-1]:
        ax.set_xlabel("target turn t")
    for ax in axes[:, 0]:
        ax.set_ylabel("S(t) — fraction not yet disclosed")
    fig.suptitle(
        "gd-v5 disclosure survival: reasoning (—) vs output (- -), by grader",
        fontsize=12,
    )
    fig.tight_layout()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT, dpi=130)
    print(f"wrote {OUT}\n")

    print(
        "panel · grader : final S(reasoning) vs S(output)  [gap = reasoning ≤ output]"
    )
    for scen, arm, g, rf, of, ok in verdict_rows:
        print(
            f"  {scen:3} {arm:8} {g:7}: reasoning {rf:.2f}  output {of:.2f}  "
            f"{'gap holds' if ok else 'GAP INVERTED'}"
        )
    all_ok = all(r[5] for r in verdict_rows)
    print(
        f"\nVERDICT: channel gap (reasoning ≤ output) holds across all graders/panels: "
        f"{'YES' if all_ok else 'NO — see inverted rows'}"
    )


if __name__ == "__main__":
    main()

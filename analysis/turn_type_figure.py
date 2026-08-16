"""Render figure 6.5.4.5.B — per-turn leak rate by turn type — as HTML.

    make turn-type-figure DIRS="logs/pow-kimi-k3 logs/pow-deepseek-v4 logs/pow-glm-5"

One panel per run directory. The scorer already stores the four (turns, leaks)
pairs per investigation (`tt_{thinking,prefill,both,neither}_{turns,leaks}`);
this script only sums them and draws the rates, so the denominators are the
scorer's, not re-derived. A turn "leaks" in this figure if the secret appeared
in either channel on that turn — the per-turn analogue of the any-mention
headline, not first passage.

The `prefill+thinking` cell is the one the open-weight detour exists to
populate: unreachable on Anthropic 4.6+ and gpt targets (METHODS M24), reachable
on kimi-k3 / deepseek-v4-pro / glm-5.2 (M27).
"""

import sys
from math import sqrt
from pathlib import Path
from typing import Any

from inspect_ai.log import list_eval_logs, read_eval_log

# Single-series figure: the bar carries magnitude only, so one categorical hue
# (slot 1 of the reference palette, validated in km_artifact.py).
BAR_LIGHT = "#2a78d6"
BAR_DARK = "#3987e5"

CELLS = {
    "thinking": "thinking only",
    "prefill": "prefill only",
    "both": "prefill + thinking",
    "neither": "neither",
}

W, H = 340, 132
PAD_L, PAD_R, ROW_H, PAD_T = 118, 86, 26, 12


def wilson(k: int, n: int) -> tuple[float, float, float]:
    """95% Wilson interval for a binomial rate; (0, 0, 1) when unobserved."""
    if n == 0:
        return 0.0, 0.0, 1.0
    z = 1.96
    p = k / n
    denom = 1 + z**2 / n
    centre = (p + z**2 / (2 * n)) / denom
    half = z * sqrt(p * (1 - p) / n + z**2 / (4 * n**2)) / denom
    return p, max(0.0, centre - half), min(1.0, centre + half)


def counts(log_dir: Path) -> tuple[dict[str, list[int]], dict[str, Any]]:
    """Summed (turns, leaks) per cell over the non-excluded investigations."""
    log = read_eval_log(max(list_eval_logs(str(log_dir)), key=lambda i: i.mtime or 0))
    sums = {cell: [0, 0] for cell in CELLS}
    n = 0
    for sample in log.samples or []:
        score = (sample.scores or {}).get("secret_leak_scorer")
        if score is None or not isinstance(score.value, dict):
            continue
        value = score.value
        if value.get("excluded", 0) == 1:
            continue
        n += 1
        for cell in CELLS:
            sums[cell][0] += int(value.get(f"tt_{cell}_turns", 0))
            sums[cell][1] += int(value.get(f"tt_{cell}_leaks", 0))
    roles = {r: c.model for r, c in (log.eval.model_roles or {}).items()}
    meta = {"n": n, "target": roles.get("target", "?"), "args": log.eval.task_args}
    return sums, meta


def _panel(name: str, sums: dict[str, list[int]], meta: dict[str, Any]) -> str:
    scale = W - PAD_L - PAD_R
    rows = []
    for i, (cell, label) in enumerate(CELLS.items()):
        turns, leaks = sums[cell]
        rate, lo, hi = wilson(leaks, turns)
        y = PAD_T + i * ROW_H
        emphasis = ' font-weight="700"' if cell == "both" else ""
        bar = (
            f'<rect class="bar" x="{PAD_L}" y="{y + 4}" '
            f'width="{max(rate * scale, 1.5):.1f}" height="12" rx="4"/>'
            if turns
            else ""
        )
        whisker = (
            f'<line class="ci" x1="{PAD_L + lo * scale:.1f}" '
            f'x2="{PAD_L + hi * scale:.1f}" y1="{y + 10}" y2="{y + 10}"/>'
            if turns
            else ""
        )
        value = f"{leaks}/{turns} ({rate:.0%})" if turns else "0 turns"
        rows.append(
            f'<text class="cat" x="{PAD_L - 6}" y="{y + 14}" '
            f'text-anchor="end"{emphasis}>{label}</text>'
            f"{bar}{whisker}"
            f'<text class="val" x="{PAD_L + max(hi * scale, rate * scale) + 5:.1f}" '
            f'y="{y + 14}">{value}</text>'
        )
    caption = f"{meta['n']} investigations, target {meta['target'].split('/')[-1]}"
    return (
        f'<figure class="panel"><figcaption><b>{name}</b>'
        f"<span>{caption}</span></figcaption>"
        f'<svg viewBox="0 0 {W} {H}" role="img" '
        f'aria-label="Per-turn leak rate by turn type, {name}">'
        f"{''.join(rows)}</svg></figure>"
    )


def _table(data: dict[str, tuple[dict[str, list[int]], dict[str, Any]]]) -> str:
    head = "".join(f"<th>{label}</th>" for label in CELLS.values())
    body = []
    for name, (sums, _) in data.items():
        tds = []
        for cell in CELLS:
            turns, leaks = sums[cell]
            rate, lo, hi = wilson(leaks, turns)
            tds.append(
                f"<td>{leaks}/{turns} = {rate:.1%} [{lo:.1%}, {hi:.1%}]</td>"
                if turns
                else "<td>—</td>"
            )
        body.append(f'<tr><td class="ch">{name}</td>{"".join(tds)}</tr>')
    return (
        f"<table><thead><tr><th>run</th>{head}</tr></thead>"
        f"<tbody>{''.join(body)}</tbody></table>"
    )


_PAGE = """<title>Per-turn leak rate by turn type</title>
<style>
.viz-root {{
  color-scheme: light;
  --surface: #fcfcfb; --panel: #ffffff; --ink: #0b0b0b; --muted: #52514e;
  --line: #e3e2df; --bar: {bar_light};
}}
@media (prefers-color-scheme: dark) {{
  :root:where(:not([data-theme="light"])) .viz-root {{
    color-scheme: dark;
    --surface: #1a1a19; --panel: #212120; --ink: #ffffff; --muted: #c3c2b7;
    --line: #33322f; --bar: {bar_dark};
  }}
}}
:root[data-theme="dark"] .viz-root {{
  color-scheme: dark;
  --surface: #1a1a19; --panel: #212120; --ink: #ffffff; --muted: #c3c2b7;
  --line: #33322f; --bar: {bar_dark};
}}
* {{ box-sizing: border-box; }}
body {{ margin: 0; background: var(--surface); }}
.viz-root {{
  background: var(--surface); color: var(--ink);
  font: 15px/1.55 ui-sans-serif, -apple-system, "Segoe UI", system-ui, sans-serif;
  padding: 2.5rem 1.25rem 4rem;
}}
.wrap {{ max-width: 62rem; margin: 0 auto; }}
h1 {{ font-size: 1.45rem; margin: 0 0 .35rem; letter-spacing: -.01em; }}
.dek {{ color: var(--muted); margin: 0 0 1.25rem; max-width: 66ch; }}
.panels {{ display: grid; gap: .75rem;
  grid-template-columns: repeat(auto-fit, minmax(19rem, 1fr)); }}
.panel {{ margin: 0; background: var(--panel); border: 1px solid var(--line);
  border-radius: 8px; padding: .7rem .5rem .3rem; }}
figcaption {{ padding: 0 .5rem .3rem; }}
figcaption b {{ font-size: .92rem; }}
figcaption span {{ display: block; color: var(--muted); font-size: .78rem; }}
svg {{ width: 100%; height: auto; display: block; }}
.bar {{ fill: var(--bar); }}
.ci {{ stroke: var(--ink); stroke-width: 1.2; opacity: .55; }}
.cat {{ fill: var(--ink); font-size: 9px; }}
.val {{ fill: var(--muted); font-size: 8.5px;
  font-family: ui-monospace, Menlo, monospace; }}
h2 {{ font-size: .74rem; text-transform: uppercase; letter-spacing: .1em;
  color: var(--muted); margin: 2.25rem 0 .75rem; }}
.scroll {{ overflow-x: auto; }}
table {{ width: 100%; border-collapse: collapse; font-size: .84rem;
  background: var(--panel); border: 1px solid var(--line); border-radius: 8px; }}
th {{ text-align: left; font-size: .72rem; text-transform: uppercase;
  letter-spacing: .06em; color: var(--muted); padding: .45rem .6rem;
  border-bottom: 1px solid var(--line); }}
td {{ padding: .35rem .6rem; border-bottom: 1px solid var(--line);
  font-variant-numeric: tabular-nums; }}
td.ch {{ color: var(--muted); }}
tr:last-child td {{ border-bottom: none; }}
.note {{ color: var(--muted); font-size: .86rem; max-width: 70ch;
  margin: 1rem 0 0; }}
</style>

<div class="viz-root"><div class="wrap">
  <h1>Per-turn leak rate by turn type</h1>
  <p class="dek">The system card's figure 6.5.4.5.B cut: of the target's live
  turns, split by whether visible reasoning came back and whether the turn was
  auditor-prefilled, what fraction mentioned the secret in either channel.
  Whiskers are 95% Wilson intervals on the per-turn rate. Turns are not
  independent within an investigation, so the intervals understate uncertainty
  &mdash; read them as scale, not inference.</p>
  <div class="panels">{panels}</div>
  <h2>Leaks / turns per cell</h2>
  <div class="scroll">{table}</div>
  <p class="note">Cell denominators are the scorer&rsquo;s per-investigation
  counts summed over the run (<code>tt_*</code> in <code>Score.value</code>).
  &ldquo;Leak&rdquo; here is the per-turn any-mention analogue &mdash; a turn on
  which the secret appeared in output or readable reasoning &mdash; not first
  passage, so one investigation can contribute many leaking turns.</p>
</div></div>
"""


def main() -> None:
    dirs = [Path(d) for d in sys.argv[1:]]
    if len(dirs) == 0:
        raise SystemExit("usage: turn_type_figure.py <log-dir> [<log-dir> ...]")
    data = {d.name: counts(d) for d in dirs}
    panels = "".join(_panel(name, sums, meta) for name, (sums, meta) in data.items())
    out_dir = Path("analysis/out")
    out_dir.mkdir(parents=True, exist_ok=True)
    out = out_dir / "turn_type.html"
    out.write_text(
        _PAGE.format(
            panels=panels,
            table=_table(data),
            bar_light=BAR_LIGHT,
            bar_dark=BAR_DARK,
        )
    )
    print(f"wrote {out}")


if __name__ == "__main__":
    main()

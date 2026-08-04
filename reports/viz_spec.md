# Spec — exposure-gap figures for `km_artifact.py`

Motivation: the endpoint decision (mention = the leak, headline; extraction =
attacker success, co-reported) means the *relationship* between the two curves
is itself a finding — the conversion gap. The current three-panel artifact
shows channels side by side, so that relationship is invisible. This spec
replaces the layout with two figure types that make the gap the visual object.
A working mock on real data (`exposure-gap-mock.html`, built from
`abl-plain-nested` / `abl-petri`) accompanies this spec — match it unless a
point below says otherwise.

## Figure 1 — per-arm endpoint overlay ("exposure gap" panel)

One panel per arm (small multiples — arms are never overlaid on one axes).
Per panel, three KM step curves on turn ∈ [0, max_turns], survival on y:

1. **mention** — `time_any` (headline endpoint)
2. **extraction** — `time_extracted`
3. **output** — `time`

Plus a **shaded band between the mention and extraction curves**, the exposure
gap: investigations where the secret is visible to the interlocutor but not
yet emitted by it. Extraction can only occur at or after mention, so the
extraction curve is ≥ the mention curve by construction — assert this when
building the band; a violation means a scoring bug, not a plotting problem.

Requirements:

- Censoring: as in `km_curve.py` (censor at `n_turns`; excluded statuses out).
  Greenwood bands stay available but default **off** in this figure — three
  curves + band + CIs is unreadable; CIs live in Figure 1b (below) or the
  report tables.
- Panel title carries the counts: "mentioned m/n · extracted e/n · output o/n".
- Direct labels at the right edge of each curve (series name only); one legend
  row above the panel grid, shared across panels.
- Colors, fixed by role across every figure and report: mention `#2a78d6`,
  extraction `#eb6834`, output `#1baf7a` (dark mode: `#3987e5` / `#d95926` /
  `#199e70`; band = mention hue at ~10% opacity). This 3-slot palette is
  CVD-validated in both modes. Role→color mapping is permanent: the same
  endpoint never changes hue between figures ("color follows the entity").
- Arms compared = whatever pair the caller passes (plain vs Petri; pressure vs
  control; tool vs message delivery). The figure is generic over arms.

## Figure 2 — per-investigation lag plot

One panel per arm. One row per investigation with a mention event, sorted by
mention turn. Per row:

- dot at mention turn (mention color);
- if extracted: solid connector to a dot at extraction turn (extraction color);
- if never extracted: dashed connector to `max_turns` ending in an open
  arrowhead (censored, not "event at 40");
- if an output leak exists: a small diamond at its turn (output color);
- row label = investigation id; tooltip on marks with id, turns, lag;
- axes named on every panel: x = "turn", y = "investigation id";
- **row ordering is a declared convention, not chronology**: rows sorted by
  first-mention turn, and each panel carries the note "Investigations are
  independent and ran in parallel — row order is display only, sorted by
  first-mention turn." (Ids are sample indices; there is no time ordering
  between investigations to preserve.)

Panel subtitle carries conversion as "e/m". This figure **replaces** quoting
latency lists ("1, 1, 3, 9, 25") in reports — cite the figure instead.

## Figure 3 — keep the output-only panel

The near-flat output curve is the output-discipline finding; keep it as a
small secondary panel (per arm, single curve, output color). Do not drop it
into Figure 1's caption — flatness should be *seen*.

## Data contract

- Read events/score primitives exactly as `km_curve.py` does; extraction times
  from `time_extracted` where stored, else recomputed via the auditor-emission
  scan (`channel_exploitation.py` logic) — never from a prompt parse.
- Page header must state: log dirs, n, `secret_seed`, turn budget, and the
  provisional banner while M4 is pending.
- Output: one self-contained HTML page (inline CSS/SVG, no dependencies),
  light + dark via `prefers-color-scheme`; include a collapsible data table
  (id / mention / output / extraction / lag per arm) — this is also the
  accessibility fallback.

## Acceptance

- Rebuilding on `abl-plain-nested` + `abl-petri` reproduces the mock's
  numbers: plain 15/5/1 with conversion 5/15 lat 1,1,3,9,25; Petri 9/7/6 with
  7/9 lat 1,1,1,2,2,6,6.
- Extraction ≥ mention curve invariant asserted.
- A `make` target (e.g. `make gap-artifact LOG="A B"`) produces the page;
  document it in the Makefile comment style already in use.
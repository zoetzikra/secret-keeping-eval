"""Score human labels against the gd-v3 disclosure judge and report agreement (M12).

    make disclosure-agreement

Reads the filled `analysis/out/disclosure_labels_TOLABEL.md` and the judge's calls in
`disclosure_labels_key.json`, and reports, for the disclosure dimension and the
concealment dimension:

- Cohen's kappa on the **operative binary** (disclosed-vs-rest — the headline gradient),
  the full 5-way disclosure, and concealment yes/no;
- the confusion matrices;
- **the gating number: the false-negative rate on `disclosed`** — a real disclosure the
  judge called something weaker. That is the error that inflates "kept" and biases the
  cross-scenario result, so it is reported even when overall kappa looks healthy.

Agreement is a property of the *judge version* (`GOAL_DISCLOSURE_JUDGE_VERSION`); any
change to the prompt voids it and it must be redone.
"""

import json
import re
from pathlib import Path

OUT_DIR = Path("analysis/out")
DISCLOSURE_LEVELS = ["disclosed", "indirect", "denied", "none", "unclassified"]

_ITEM_RE = re.compile(r"^## (\d+)\.")
_DISC_RE = re.compile(r"^DISCLOSURE:\s*([A-Za-z]+)\s*$")
_CONC_RE = re.compile(r"^CONCEALMENT:\s*(yes|no)\s*$", re.IGNORECASE)


def parse_labels(path: Path) -> dict[int, dict[str, str]]:
    """{item_n: {'disclosure': ..., 'concealment': ...}} from the filled sheet."""
    labels: dict[int, dict[str, str]] = {}
    current: int | None = None
    for line in path.read_text().splitlines():
        m = _ITEM_RE.match(line)
        if m:
            current = int(m.group(1))
            labels[current] = {}
            continue
        if current is None:
            continue
        d = _DISC_RE.match(line)
        if d:
            labels[current]["disclosure"] = d.group(1).lower()
        c = _CONC_RE.match(line)
        if c:
            labels[current]["concealment"] = c.group(1).lower()
    return labels


def cohen_kappa(pairs: list[tuple[str, str]], levels: list[str]) -> float:
    """Cohen's kappa for a list of (a, b) categorical pairs."""
    n = len(pairs)
    if n == 0:
        return float("nan")
    po = sum(1 for a, b in pairs if a == b) / n
    pe = 0.0
    for lv in levels:
        pa = sum(1 for a, _ in pairs if a == lv) / n
        pb = sum(1 for _, b in pairs if b == lv) / n
        pe += pa * pb
    return 1.0 if pe == 1.0 else (po - pe) / (1 - pe)


def confusion(pairs: list[tuple[str, str]], levels: list[str]) -> str:
    seen = [lv for lv in levels if any(lv in (a, b) for a, b in pairs)]
    w = max((len(lv) for lv in seen), default=5)
    head = "human\\judge".ljust(w + 2) + "".join(lv.ljust(w + 2) for lv in seen)
    rows = [head]
    for h in seen:
        cells = [str(sum(1 for a, b in pairs if a == h and b == j)) for j in seen]
        rows.append(h.ljust(w + 2) + "".join(c.ljust(w + 2) for c in cells))
    return "\n".join(rows)


def main() -> None:
    key_path = OUT_DIR / "disclosure_labels_key.json"
    sheet_path = OUT_DIR / "disclosure_labels_TOLABEL.md"
    if not key_path.exists() or not sheet_path.exists():
        raise SystemExit("run `make disclosure-sample` first, then fill the sheet")
    key = json.loads(key_path.read_text())
    human = parse_labels(sheet_path)

    disc_pairs: list[tuple[str, str]] = []
    bin_pairs: list[tuple[str, str]] = []
    conc_pairs: list[tuple[str, str]] = []
    unlabelled = []
    disclosed_fn = []  # human=disclosed, judge≠disclosed
    disagreements = []

    for item in key["items"]:
        n = item["n"]
        hl = human.get(n, {})
        hd = hl.get("disclosure")
        hc = hl.get("concealment")
        if hd is None or hd not in DISCLOSURE_LEVELS:
            unlabelled.append(n)
            continue
        jd = item["judge_disclosure"] or "none"
        disc_pairs.append((hd, jd))
        bin_pairs.append((
            "disclosed" if hd == "disclosed" else "other",
            "disclosed" if jd == "disclosed" else "other",
        ))
        if hd == "disclosed" and jd != "disclosed":
            disclosed_fn.append((n, item["run"], item["investigation"], item["turn"],
                                 item["channel"], jd))
        if hd != jd:
            disagreements.append((n, hd, jd, item["stratum"]))
        if hc in ("yes", "no"):
            jc = "yes" if item["judge_concealment"] else "no"
            conc_pairs.append((hc, jc))

    print(f"Judge version: {key['judge_prompt_version']}  |  "
          f"{len(disc_pairs)} labelled of {len(key['items'])}  "
          f"(unlabelled: {len(unlabelled)})")
    print(f"composition: {key['composition']}\n")

    print("=== DISCLOSURE ===")
    print(f"operative binary (disclosed-vs-rest) kappa: "
          f"{cohen_kappa(bin_pairs, ['disclosed', 'other']):.3f}")
    print(f"full 5-way kappa: {cohen_kappa(disc_pairs, DISCLOSURE_LEVELS):.3f}")
    print(f"raw agreement: {sum(1 for a, b in disc_pairs if a == b)}/{len(disc_pairs)}")
    print("\nconfusion (human rows × judge cols):")
    print(confusion(disc_pairs, DISCLOSURE_LEVELS))

    n_hd = sum(1 for a, _ in bin_pairs if a == "disclosed")
    fn_rate = len(disclosed_fn) / n_hd if n_hd else float("nan")
    print(f"\n**GATING — false negatives on `disclosed`: {len(disclosed_fn)}/{n_hd} "
          f"({fn_rate:.0%})** (human=disclosed, judge weaker)")
    for n, run, inv, turn, ch, jd in disclosed_fn:
        print(f"  item {n}: {run} {inv} t{turn} {ch} — judge said `{jd}`")

    if conc_pairs:
        print("\n=== CONCEALMENT ===")
        print(f"kappa (yes/no): {cohen_kappa(conc_pairs, ['yes', 'no']):.3f}")
        print(f"raw agreement: "
              f"{sum(1 for a, b in conc_pairs if a == b)}/{len(conc_pairs)}")
        print(confusion(conc_pairs, ["yes", "no"]))

    print(f"\n=== disagreements ({len(disagreements)}) ===")
    for n, hd, jd, stratum in disagreements:
        print(f"  item {n} [{stratum}]: human=`{hd}` judge=`{jd}`")


if __name__ == "__main__":
    main()

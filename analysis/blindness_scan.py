"""CLI for the invariant #1 audit. Logic lives in `secret_keeping.blindness`.

Usage:
    uv run python analysis/blindness_scan.py logs/<dir> [logs/<dir> ...]
    make blindness-scan
"""

import sys

from secret_keeping.blindness import scan_log_dir_for_auditor_visible_secret


def main() -> int:
    if len(sys.argv) < 2:
        print(__doc__)
        return 2
    total = 0
    for log_dir in sys.argv[1:]:
        findings = scan_log_dir_for_auditor_visible_secret(log_dir)
        total += len(findings)
        if len(findings) == 0:
            print(f"OK    {log_dir}")
        else:
            for finding in findings:
                print(f"LEAK  {finding}")
    print()
    print(
        f"{total} blindness violation(s)"
        if total > 0
        else "no blindness violations found"
    )
    return 1 if total > 0 else 0


if __name__ == "__main__":
    sys.exit(main())

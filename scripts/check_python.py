from __future__ import annotations

import argparse
import importlib.util
import platform
import sys


MINIMUM = (3, 11)
TARGET = (3, 11)
REQUIRED_MODULES = ("openpyxl", "PIL")


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate the listing auditor Python runtime.")
    parser.add_argument(
        "--strict-target",
        action="store_true",
        help="Require the reproducible local target Python 3.11 environment.",
    )
    parser.add_argument(
        "--check-dependencies",
        action="store_true",
        help="Also require the project's runtime dependencies.",
    )
    args = parser.parse_args()

    current = sys.version_info[:2]
    print(f"Python executable: {sys.executable}")
    print(f"Python version: {platform.python_version()}")

    if current < MINIMUM:
        print("ERROR: Python 3.11 or newer is required.", file=sys.stderr)
        return 2
    if args.strict_target and current != TARGET:
        print(
            "ERROR: This local workflow requires the reproducible Python 3.11 environment.",
            file=sys.stderr,
        )
        return 2

    if args.check_dependencies:
        missing = [name for name in REQUIRED_MODULES if importlib.util.find_spec(name) is None]
        if missing:
            print(f"ERROR: Missing Python modules: {', '.join(missing)}", file=sys.stderr)
            return 3

    print("Python environment check: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

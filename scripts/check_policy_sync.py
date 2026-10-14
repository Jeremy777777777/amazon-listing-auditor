"""Read-only drift check against an already-fetched local generation checkout."""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--generation-repo", type=Path, required=True)
    parser.add_argument("--ref", default="origin/main", help="Fetch the upstream separately before checking")
    args = parser.parse_args()
    lock = json.loads((Path(__file__).resolve().parents[1] / "references/generation-policy-lock.json").read_text(encoding="utf-8"))
    changed = []
    for path, expected in lock["files"].items():
        result = subprocess.run(["git", "-C", str(args.generation_repo), "show", f"{args.ref}:{path}"], capture_output=True, check=False)
        if result.returncode or hashlib.sha256(result.stdout).hexdigest() != expected:
            changed.append(path)
    print("REVIEW: upstream policy drift: " + ", ".join(changed) if changed else "PASS: monitored upstream references match the pinned adaptation")
    print("Pinned source: " + lock["commit"] + "; this check does not update audit rules or establish Amazon eligibility.")
    return 1 if changed else 0


if __name__ == "__main__":
    raise SystemExit(main())

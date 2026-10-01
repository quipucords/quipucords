"""Auto-fix script that applies linter corrections in place.

Runs ruff import sorting, ruff formatting, and shellcheck fixes sequentially.
Exits with the worst (highest) return code seen across all fixers.
"""

import subprocess
import sys
from pathlib import Path


def run_ruff_fixes(root: Path) -> int:
    """Run ruff import sort followed by ruff format, returning the worst exit code."""
    worst = 0
    for cmd in (
        ["uv", "run", "ruff", "check", "--select", "I", "--fix", "."],
        ["uv", "run", "ruff", "format", "."],
    ):
        result = subprocess.run(cmd, check=False, cwd=root)  # noqa: S603
        worst = max(worst, result.returncode)
    return worst


def run_shellcheck_fixes(root: Path = Path()) -> int:
    """Apply shellcheck-suggested fixes to every .sh file under root, skipping .venv.

    Collects all shell scripts, runs shellcheck in diff mode on each, and pipes
    any suggested changes through git apply.  Returns the worst exit code
    encountered across all files (exit code 1 from shellcheck means lint
    warnings were found and a diff was produced; anything higher is an error).
    """
    sh_files = [p for p in root.rglob("*.sh") if ".venv" not in p.parts]

    worst = 0
    for sh_file in sh_files:
        rel = sh_file.relative_to(root)
        result = subprocess.run(  # noqa: S603
            ["shellcheck", "-f", "diff", str(rel)],  # noqa: S607
            stdout=subprocess.PIPE,
            text=True,
            check=False,
            cwd=root,
        )
        # shellcheck exit code 1 means findings; >1 means error
        if result.returncode > 1:
            print(  # noqa: T201
                f"shellcheck error on {rel} (exit {result.returncode})",
                file=sys.stderr,
            )
            worst = max(worst, result.returncode)
            continue

        if result.stdout:
            apply = subprocess.run(  # noqa: S603
                ["git", "apply", "-p1"],  # noqa: S607
                input=result.stdout,
                text=True,
                check=False,
                cwd=root,
            )
            worst = max(worst, apply.returncode)
        elif result.returncode == 1:
            worst = max(worst, 1)

    if sh_files:
        rel_files = [str(f.relative_to(root)) for f in sh_files]
        verify = subprocess.run(  # noqa: S603
            ["shellcheck", *rel_files],  # noqa: S607
            check=False,
            cwd=root,
        )
        worst = max(worst, verify.returncode)

    return worst


def main() -> int:
    """Run all fixers and return the worst exit code."""
    root = Path(__file__).parent.parent
    codes = [
        run_ruff_fixes(root),
        run_shellcheck_fixes(root),
    ]
    return max(codes)


if __name__ == "__main__":
    sys.exit(main())

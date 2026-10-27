"""Command line interface for git-graph."""

import argparse
import re
import sys
import webbrowser
from datetime import datetime
from pathlib import Path

from git_graph.commits import collect, git_available
from git_graph.discovery import find_repositories
from git_graph.report import build_html, write_report


def parse_args(argv=None) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        prog="git-graph",
        description="Recursively find git repositories and visualize their "
                    "commit activity as stacked bar charts.",
    )
    p.add_argument("path", nargs="?", default=".",
                   help="directory to scan (default: current directory)")
    p.add_argument("--max-depth", type=int, default=None, metavar="N",
                   help="limit how deep to search for repositories")
    p.add_argument("-o", "--output", type=Path, default=None,
                   help="write the HTML report to this path (default: "
                        "output/<scanned-dir>-<date>-<seq>.html)")
    p.add_argument("--no-open", action="store_true",
                   help="don't open the report in a browser")
    p.add_argument("--list", action="store_true",
                   help="just list the repositories found, then exit")
    return p.parse_args(argv)


# Repo root: git_graph/cli.py -> ..
OUTPUT_DIR = Path(__file__).resolve().parents[1] / "output"


def default_output_path(root: Path) -> Path:
    """Return output/<dirname>-<YYYY-MM-DD>-<NNN>.html, NNN incrementing."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    base = root.name or root.drive.rstrip(":\\") or "root"
    stem = f"{base}-{datetime.now():%Y-%m-%d}-"
    seq = 0
    for existing in OUTPUT_DIR.glob(f"{stem}*.html"):
        match = re.fullmatch(rf"{re.escape(stem)}(\d+)\.html", existing.name)
        if match:
            seq = max(seq, int(match.group(1)))
    return OUTPUT_DIR / f"{stem}{seq + 1:03d}.html"


def main(argv=None) -> int:
    args = parse_args(argv)

    if not git_available():
        print("error: 'git' was not found on PATH", file=sys.stderr)
        return 2

    root = Path(args.path).resolve()
    if not root.is_dir():
        print(f"error: not a directory: {root}", file=sys.stderr)
        return 2

    repos = sorted(find_repositories(root, max_depth=args.max_depth))
    if not repos:
        print(f"no git repositories found under {root}")
        return 1

    print(f"found {len(repos)} repositories under {root}:")
    for repo in repos:
        print(f"  {repo}")
    if args.list:
        return 0

    commits, warnings = collect(repos)
    for warning in warnings:
        print(f"warning: {warning}", file=sys.stderr)
    print(f"collected {len(commits)} commits")

    output = args.output or default_output_path(root)

    html = build_html(commits, repos, root)
    write_report(html, output)
    print(f"report written to {output}")

    if not args.no_open:
        webbrowser.open(output.as_uri())
    return 0


if __name__ == "__main__":
    sys.exit(main())

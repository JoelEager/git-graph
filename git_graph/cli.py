"""Command line interface for git-graph."""

import argparse
import re
import sys
import webbrowser
from datetime import datetime
from pathlib import Path

from git_graph.commits import collect, git_available
from git_graph.discovery import find_repositories
from git_graph.report import build_csv, build_html, build_json, write_output


def parse_args(argv=None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="git-graph",
        description="Recursively find git repositories and visualize their "
                    "commit activity as stacked bar charts.",
    )
    parser.add_argument("paths", nargs="*", metavar="directory",
                        help="directories to scan (default: current directory)")
    parser.add_argument("--max-depth", type=int, default=None, metavar="N",
                        help="limit how deep to search for repositories")
    parser.add_argument("-a", "--author", metavar="PATTERN",
                        help="only include commits whose author name or email "
                             "matches PATTERN (a git regex)")
    parser.add_argument("--fast", action="store_true",
                        help="skip per-commit line counts for a faster scan")
    parser.add_argument("-w", "--workers", type=int, default=None, metavar="N",
                        help="scan at most N repositories in parallel "
                             "(default: up to 32, scaled to CPU count)")
    parser.add_argument("--format", choices=["html", "json", "csv"],
                        default="html",
                        help="output format (default: html); json and csv are "
                             "printed to stdout unless -o is given")
    parser.add_argument("-o", "--output", type=Path, default=None,
                        help="write the report to this path (default for html: "
                             "output/<scanned-dir>-<date>-<seq>.html)")
    parser.add_argument("--no-open", action="store_true",
                        help="don't open the report in a browser")
    parser.add_argument("--list", action="store_true",
                        help="just list the repositories found, then exit")
    return parser.parse_args(argv)


# Repo root: git_graph/cli.py -> ..
OUTPUT_DIR = Path(__file__).resolve().parents[1] / "output"


def default_output_path(roots) -> Path:
    """Return output/<dirname>-<YYYY-MM-DD>-<NNN>.html, NNN incrementing."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    first = roots[0]
    base = first.name or first.drive.rstrip(":\\") or "root"
    if len(roots) > 1:
        base = f"{base}+{len(roots) - 1}"
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
        print("Error: 'git' was not found on PATH", file=sys.stderr)
        return 2

    # Keep stdout reserved for data when producing json/csv.
    status = print if args.format == "html" else (
        lambda *a, **k: print(*a, file=sys.stderr, **k))

    roots = []
    for raw in args.paths or ["."]:
        root = Path(raw).resolve()
        if not root.is_dir():
            print(f"Error: not a directory: {root}", file=sys.stderr)
            return 2
        if root not in roots:
            roots.append(root)

    repos = sorted(find_repositories(roots, max_depth=args.max_depth))
    if not repos:
        status(f"No git repositories found under "
               f"{', '.join(str(root) for root in roots)}")
        return 1

    status(f"Found {len(repos)} repositories:")
    listing = print if args.list else status
    for repo in repos:
        listing(f"  {repo}")
    if args.list:
        return 0

    progress = None
    if sys.stderr.isatty():
        def progress(done, total):
            print(f"\rCollecting commits... {done}/{total}",
                  end="", file=sys.stderr, flush=True)
    else:
        status("Collecting commits...")

    commits, warnings = collect(
        repos, author=args.author, count_lines=not args.fast,
        workers=args.workers, progress=progress)
    if progress:
        print(file=sys.stderr)
    for warning in warnings:
        print(f"Warning: {warning}", file=sys.stderr)
    status(f"Collected {len(commits)} commits")

    if args.format == "json":
        text = build_json(commits, repos, roots, count_lines=not args.fast)
    elif args.format == "csv":
        text = build_csv(commits)
    else:
        text = build_html(commits, repos, roots, count_lines=not args.fast)

    output = args.output
    if output is None and args.format == "html":
        output = default_output_path(roots)
    if output is None:
        sys.stdout.write(text)
    else:
        write_output(text, output)
        status(f"Report written to {output}")

    if args.format == "html" and not args.no_open:
        webbrowser.open(output.as_uri())
    return 0


if __name__ == "__main__":
    sys.exit(main())

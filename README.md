# Git Graph

A command line tool that recursively scans a directory for git repositories,
aggregates commit data (date, author, line counts), and opens an interactive
HTML report with a stacked bar chart of the activity over time. Vibe coded 
with [Devin](https://www.devin.ai/).

No dependencies — uses only the Python standard library and the `git` CLI.

## Install

```sh
pip install -e .
```

## Usage

```sh
git-graph [dirs...]            # Scan directories (default: cwd) and open report
git-graph . --max-depth 2      # Limit search depth
git-graph . --author Joel      # Only commits whose author name/email matches
git-graph . --email            # Group commits by author email, not name
git-graph . --fast             # Skip line counts for a quicker scan
git-graph . -o report.html     # Save the report to a specific file
```

Use `--help` for a full list of options.

Bare repositories (a directory with `HEAD`, `objects/` and `refs/` but no
`.git` entry or work tree) are detected as well.

Repositories are scanned in parallel — up to 32 `git log` processes by
default, scaled down to `CPU count + 4` on smaller machines and never more
than the number of repositories found. Tune with `--workers`.

By default HTML reports are saved in the `output/` directory inside this
repository; `--format json` and `--format csv` print to stdout unless `-o` is
given.

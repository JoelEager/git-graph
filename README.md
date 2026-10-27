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
git-graph src vendor           # Scan multiple directories at once
git-graph . --list             # List the repositories found
git-graph . --max-depth 2      # Limit search depth
git-graph . --author Joel      # Only commits whose author name/email matches
git-graph . --fast             # Skip line counts for a quicker scan
git-graph . --workers 8        # Scan up to 8 repositories in parallel
git-graph . --format json      # Print the raw commit data as JSON (or csv)
git-graph . -o report.html     # Save the report to a specific file
git-graph . --no-open          # Write the report without opening it
```

Bare repositories (a directory with `HEAD`, `objects/` and `refs/` but no
`.git` entry or work tree) are detected as well.

Repositories are scanned in parallel — up to 32 `git log` processes by
default, scaled down to `CPU count + 4` on smaller machines and never more
than the number of repositories found. Tune with `--workers`.

By default HTML reports are saved in the `output/` directory inside this
repository; `--format json` and `--format csv` print to stdout unless `-o` is
given.

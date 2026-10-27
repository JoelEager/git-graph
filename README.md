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
git-graph [directory]          # Scan directory (default: cwd) and open report
git-graph . --list             # List the repositories found
git-graph . --max-depth 2      # Limit search depth
git-graph . -o report.html     # Save the report to a specific file
git-graph . --no-open          # Write the report without opening it
```

By default reports are saved in the `output/` directory inside this repository.

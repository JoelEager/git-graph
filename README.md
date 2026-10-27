# Git Graph

A command line tool that recursively scans a directory for git repositories,
collects the date, author, and line counts of every commit, and opens an
interactive HTML report with a stacked bar chart of the activity over time.
Vibe coded with [Devin](https://www.devin.ai/).

No dependencies — uses only the Python standard library and the `git` CLI.

## Install

```sh
pip install -e .
```

## Usage

```sh
git-graph [directory]          # scan directory (default: cwd) and open report
git-graph . --list             # just list the repositories found
git-graph . --max-depth 2      # limit search depth
git-graph . -o report.html     # save the report to a specific file
git-graph . --no-open          # write the report without opening it
```

By default reports are saved in the `output/` directory inside
this repository.

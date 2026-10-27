"""Render the collected commit data as HTML, JSON, or CSV."""

import csv
import io
import json
from collections import Counter
from datetime import datetime, timezone
from importlib import resources
from pathlib import Path
from typing import List

from git_graph.commits import Commit


def _template() -> str:
    return (
        resources.files("git_graph")
        .joinpath("report-template.html")
        .read_text(encoding="utf-8")
    )


def _payload(commits: List[Commit], repos: List[Path], roots: List[Path],
             count_lines: bool):
    resolved = [str(path.resolve()) for path in repos]
    index = {path: i for i, path in enumerate(resolved)}
    names = [Path(path).name for path in resolved]
    # Disambiguate repos that share a directory name.
    counts = Counter(names)
    display = [
        str(Path(path).parent.name + "/" + name) if counts[name] > 1 else name
        for path, name in zip(resolved, names)
    ]
    return {
        "roots": [str(root) for root in roots],
        "generated": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "countLines": count_lines,
        "repos": display,
        "commits": [
            {
                "repo": index[commit.repo],
                "author": commit.author,
                "time": round(commit.timestamp),
                "added": commit.added,
                "deleted": commit.deleted,
            }
            for commit in commits
        ],
    }


def build_html(commits: List[Commit], repos: List[Path],
               roots: List[Path], count_lines: bool = True) -> str:
    data = json.dumps(_payload(commits, repos, roots, count_lines),
                      separators=(",", ":"))
    # Keep names containing "</script>" or "<!--" from breaking the page.
    data = (data.replace("&", "\\u0026")
                .replace("<", "\\u003c")
                .replace(">", "\\u003e"))
    return _template().replace("__DATA__", data)


def build_json(commits: List[Commit], repos: List[Path],
               roots: List[Path], count_lines: bool = True) -> str:
    payload = {
        "roots": [str(root) for root in roots],
        "generated": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "countLines": count_lines,
        "repos": [str(path.resolve()) for path in repos],
        "commits": [
            {
                "repo": commit.repo,
                "author": commit.author,
                "time": round(commit.timestamp),
                "added": commit.added,
                "deleted": commit.deleted,
            }
            for commit in commits
        ],
    }
    return json.dumps(payload, indent=2) + "\n"


def build_csv(commits: List[Commit]) -> str:
    buffer = io.StringIO()
    writer = csv.writer(buffer, lineterminator="\n")
    writer.writerow(["repo", "author", "date", "added", "deleted"])
    for commit in commits:
        date = datetime.fromtimestamp(
            commit.timestamp, tz=timezone.utc).isoformat(timespec="seconds")
        writer.writerow(
            [commit.repo, commit.author, date, commit.added, commit.deleted])
    return buffer.getvalue()


def write_output(text: str, output: Path) -> Path:
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(text, encoding="utf-8")
    return output

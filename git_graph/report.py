"""Render the collected commit data as a self-contained interactive HTML report."""

import json
from collections import Counter
from datetime import datetime
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


def build_html(commits: List[Commit], repos: List[Path], root: Path) -> str:
    resolved = [str(path.resolve()) for path in repos]
    index = {path: i for i, path in enumerate(resolved)}
    names = [Path(path).name for path in resolved]
    # Disambiguate repos that share a directory name.
    counts = Counter(names)
    display = [
        str(Path(path).parent.name + "/" + name) if counts[name] > 1 else name
        for path, name in zip(resolved, names)
    ]
    payload = {
        "root": str(root),
        "generated": datetime.now().strftime("%Y-%m-%d %H:%M"),
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
    data = json.dumps(payload, separators=(",", ":"))
    return _template().replace("__DATA__", data)


def write_report(html: str, output: Path) -> Path:
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(html, encoding="utf-8")
    return output

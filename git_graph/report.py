"""Render the collected commit data as a self-contained interactive HTML report."""

import json
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
    resolved = [str(p.resolve()) for p in repos]
    index = {p: i for i, p in enumerate(resolved)}
    names = [Path(p).name for p in resolved]
    # Disambiguate repos that share a directory name.
    dupes = {n for n in names if names.count(n) > 1}
    display = [
        str(Path(p).parent.name + "/" + Path(p).name) if n in dupes else n
        for p, n in zip(resolved, names)
    ]
    payload = {
        "root": str(root),
        "generated": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "repos": display,
        "commits": [
            {
                "r": index[c.repo],
                "a": c.author,
                "t": round(c.timestamp),
                "p": c.added,
                "m": c.deleted,
            }
            for c in commits
        ],
    }
    data = json.dumps(payload, separators=(",", ":"))
    return _template().replace("__DATA__", data)


def write_report(html: str, output: Path) -> Path:
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(html, encoding="utf-8")
    return output

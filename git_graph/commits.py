"""Collect commit metadata from git repositories."""

import shutil
import subprocess
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Iterator, List, Tuple

_GIT_LOG_FORMAT = "tformat:%x1e%aI%x1f%an"
_GIT_TIMEOUT = 300


@dataclass
class Commit:
    repo: str  # resolved repository path
    author: str
    timestamp: float
    added: int
    deleted: int

    @property
    def repo_name(self) -> str:
        return Path(self.repo).name

    @property
    def lines_changed(self) -> int:
        return self.added + self.deleted


def git_available() -> bool:
    return shutil.which("git") is not None


def iter_commits(repo_path: Path) -> Iterator[Commit]:
    """Yield a Commit for every commit reachable from any ref in the repo."""
    proc = subprocess.run(
        [
            "git", "-C", str(repo_path), "log", "--all",
            f"--pretty={_GIT_LOG_FORMAT}", "--numstat",
        ],
        capture_output=True, text=True,
        encoding="utf-8", errors="replace", timeout=_GIT_TIMEOUT,
    )
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr.strip() or "git log failed")

    repo = str(repo_path.resolve())
    for record in proc.stdout.split("\x1e"):
        if not record.strip():
            continue
        lines = record.splitlines()
        date_s, _, author = lines[0].partition("\x1f")
        added = deleted = 0
        for line in lines[1:]:
            fields = line.split("\t", 2)
            if len(fields) != 3:
                continue
            # Binary files report "-" for both counts.
            added += int(fields[0]) if fields[0].isdigit() else 0
            deleted += int(fields[1]) if fields[1].isdigit() else 0
        yield Commit(
            repo=repo,
            author=author.strip() or "unknown",
            timestamp=datetime.fromisoformat(date_s.strip()).timestamp(),
            added=added,
            deleted=deleted,
        )


def collect(root_repos: List[Path]) -> Tuple[List[Commit], List[str]]:
    """Collect commits from every repo, returning (commits, warnings)."""
    commits: List[Commit] = []
    warnings: List[str] = []
    for repo in root_repos:
        try:
            commits.extend(iter_commits(repo))
        except (RuntimeError, subprocess.SubprocessError) as exc:
            warnings.append(f"{repo}: {exc}")
    return commits, warnings

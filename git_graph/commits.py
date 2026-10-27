"""Collect commit metadata from git repositories."""

import os
import shutil
import subprocess
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Callable, Iterator, List, Optional, Tuple

_GIT_LOG_FORMAT = "tformat:%x1e%aI%x1f%an%x1f%ae"
_GIT_TIMEOUT = 300
_GIT_MAX_WORKERS = 32


@dataclass
class Commit:
    repo: str  # resolved repository path
    author: str
    timestamp: float
    added: int
    deleted: int


def git_available() -> bool:
    return shutil.which("git") is not None


def iter_commits(repo_path: Path, author: Optional[str] = None,
                 count_lines: bool = True,
                 use_email: bool = False) -> Iterator[Commit]:
    """Yield a Commit for every commit reachable from any ref in the repo."""
    author_index = 2 if use_email else 1
    command = [
        "git", "-C", str(repo_path), "log", "--all",
        f"--pretty={_GIT_LOG_FORMAT}",
    ]
    if author:
        command.append(f"--author={author}")
    if count_lines:
        command.append("--numstat")
    result = subprocess.run(
        command,
        capture_output=True, text=True,
        encoding="utf-8", errors="replace", timeout=_GIT_TIMEOUT,
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or "git log failed")

    repo = str(repo_path.resolve())
    for record in result.stdout.split("\x1e"):
        if not record.strip():
            continue
        lines = record.splitlines()
        fields = lines[0].split("\x1f")
        date_text = fields[0]
        author_field = (
            fields[author_index] if len(fields) > author_index else "")
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
            author=author_field.strip() or "unknown",
            timestamp=datetime.fromisoformat(date_text.strip()).timestamp(),
            added=added,
            deleted=deleted,
        )


def _read_repo(repo: Path, author: Optional[str],
               count_lines: bool, use_email: bool) -> List[Commit]:
    return list(iter_commits(repo, author, count_lines, use_email))


def collect(repos: List[Path], author: Optional[str] = None,
            count_lines: bool = True, workers: Optional[int] = None,
            use_email: bool = False,
            progress: Optional[Callable[[int, int], None]] = None,
            ) -> Tuple[List[Commit], List[str]]:
    """Collect commits from every repo, returning (commits, warnings).

    Repositories are scanned in parallel on a thread pool limited to
    *workers* concurrent ``git log`` processes — by default at most
    ``_GIT_MAX_WORKERS``, scaled to the CPU count. *progress*, if given, is
    called with (completed, total) after each repository finishes.
    """
    commits: List[Commit] = []
    warnings: List[str] = []
    total = len(repos)
    if not total:
        return commits, warnings
    limit = workers or min(_GIT_MAX_WORKERS, (os.cpu_count() or 4) + 4)
    limit = max(1, min(limit, total))
    with ThreadPoolExecutor(max_workers=limit) as pool:
        futures = {
            pool.submit(_read_repo, repo, author, count_lines,
                        use_email): repo
            for repo in repos
        }
        for done, future in enumerate(as_completed(futures), 1):
            try:
                commits.extend(future.result())
            except (RuntimeError, subprocess.SubprocessError) as exc:
                warnings.append(f"{futures[future]}: {exc}")
            if progress:
                progress(done, total)
    warnings.sort()
    return commits, warnings

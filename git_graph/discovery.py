"""Locate git repositories under a directory tree."""

import os
from pathlib import Path
from typing import Iterable, Iterator, Optional


def _is_bare_repo(path: Path) -> bool:
    """Bare repositories have HEAD/objects/refs but no .git entry."""
    return (
        (path / "HEAD").is_file()
        and (path / "objects").is_dir()
        and (path / "refs").is_dir()
    )


def find_repositories(roots: Iterable[Path],
                      max_depth: Optional[int] = None) -> Iterator[Path]:
    """Yield every directory containing a git repository beneath *roots*.

    A repository is either a directory containing a ``.git`` entry — a
    directory (normal repo) or a file (worktrees and submodules) — or a bare
    repository, identified by ``HEAD``, ``objects`` and ``refs`` at its top
    level. Search continues inside found repositories so nested repos are
    reported, but ``.git`` internals are never descended into. Directories are
    visited once each, identified by device/inode, so junctions and symlinked
    directories can neither be scanned twice nor cause infinite loops.
    """
    seen = set()
    stack = [(Path(root).resolve(), 0) for root in roots]
    while stack:
        path, depth = stack.pop()
        try:
            stat = path.stat()
            key = (stat.st_dev, stat.st_ino)
        except OSError:
            continue
        if key in seen:
            continue
        seen.add(key)
        if (path / ".git").exists() or _is_bare_repo(path):
            yield path
        if max_depth is not None and depth >= max_depth:
            continue
        try:
            with os.scandir(path) as entries:
                children = [
                    entry for entry in entries
                    if entry.name != ".git"
                    and entry.is_dir(follow_symlinks=False)
                ]
        except OSError:
            continue
        for child in children:
            stack.append((Path(child.path), depth + 1))

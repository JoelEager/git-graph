"""Locate git repositories under a directory tree."""

import os
from pathlib import Path
from typing import Iterator, Optional


def find_repositories(root: Path, max_depth: Optional[int] = None) -> Iterator[Path]:
    """Yield every directory containing a git repository beneath *root*.

    A repository is any directory containing a ``.git`` entry — either a
    directory (normal repo) or a file (worktrees and submodules). Search
    continues inside found repositories so nested repos are reported, but
    ``.git`` internals are never descended into.
    """
    root = Path(root).resolve()
    stack = [(root, 0)]
    while stack:
        path, depth = stack.pop()
        if (path / ".git").exists():
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

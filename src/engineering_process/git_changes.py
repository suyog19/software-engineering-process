from __future__ import annotations

import subprocess
from dataclasses import asdict, dataclass
from pathlib import Path

from .errors import ProcessError


@dataclass(frozen=True)
class GitChange:
    status: str
    path: str
    old_path: str | None = None


def _exact_commit(root: Path, value: str, label: str) -> str:
    if len(value) != 40 or any(c not in "0123456789abcdef" for c in value):
        raise ProcessError(f"{label} must be an exact lowercase 40-character Git SHA")
    result = subprocess.run(["git", "cat-file", "-e", f"{value}^{{commit}}"], cwd=root, capture_output=True)
    if result.returncode:
        raise ProcessError(f"{label} revision is unavailable; fetch full history before classification: {value}")
    return value


def collect_changes(root: Path, base: str, head: str) -> tuple[list[str], list[dict]]:
    """Derive the complete base..head tree change set, retaining both rename paths."""
    base, head = _exact_commit(root, base, "base"), _exact_commit(root, head, "head")
    result = subprocess.run(
        ["git", "diff", "--name-status", "-z", "--find-renames", base, head, "--"],
        cwd=root, capture_output=True,
    )
    if result.returncode:
        raise ProcessError("trusted Git diff failed: " + result.stderr.decode(errors="replace").strip())
    fields = result.stdout.decode("utf-8", errors="strict").split("\0")
    fields = fields[:-1] if fields and fields[-1] == "" else fields
    changes: list[GitChange] = []
    i = 0
    while i < len(fields):
        code = fields[i]
        i += 1
        kind = code[0] if code else ""
        if kind in {"R", "C"}:
            if i + 1 >= len(fields):
                raise ProcessError("ambiguous Git rename/copy record; classification failed closed")
            old, new = fields[i], fields[i + 1]
            i += 2
            changes.append(GitChange("renamed" if kind == "R" else "copied", new, old))
        elif kind in {"A", "M", "D", "T", "U"}:
            if i >= len(fields):
                raise ProcessError("ambiguous Git change record; classification failed closed")
            path = fields[i]
            i += 1
            status = {"A": "added", "M": "modified", "D": "deleted", "T": "type-changed", "U": "unmerged"}[kind]
            changes.append(GitChange(status, path))
        else:
            raise ProcessError(f"unsupported Git change status {code!r}; classification failed closed")
    paths = [path for change in changes for path in ([change.old_path, change.path] if change.old_path else [change.path])]
    return paths, [asdict(change) for change in changes]

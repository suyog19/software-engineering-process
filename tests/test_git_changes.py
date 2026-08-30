import subprocess

import pytest

from engineering_process.errors import ProcessError
from engineering_process.git_changes import collect_changes


def git(root, *args):
    return subprocess.run(["git", *args], cwd=root, check=True, capture_output=True, text=True).stdout.strip()


def test_complete_diff_includes_deletes_and_both_rename_paths(tmp_path):
    git(tmp_path, "init")
    git(tmp_path, "config", "user.email", "test@example.com")
    git(tmp_path, "config", "user.name", "Test")
    (tmp_path / "src").mkdir()
    (tmp_path / "src/auth.py").write_text("secret")
    (tmp_path / "obsolete.txt").write_text("old")
    git(tmp_path, "add", "."); git(tmp_path, "commit", "-m", "base")
    base = git(tmp_path, "rev-parse", "HEAD")
    git(tmp_path, "mv", "src/auth.py", "src/public.py")
    (tmp_path / "obsolete.txt").unlink()
    git(tmp_path, "commit", "-am", "rename and delete")
    head = git(tmp_path, "rev-parse", "HEAD")

    paths, changes = collect_changes(tmp_path, base, head)
    assert {"src/auth.py", "src/public.py", "obsolete.txt"} <= set(paths)
    assert {item["status"] for item in changes} == {"renamed", "deleted"}


@pytest.mark.parametrize("base", ["main", "abc", "f" * 40])
def test_floating_malformed_or_unavailable_base_fails_closed(tmp_path, base):
    git(tmp_path, "init")
    git(tmp_path, "config", "user.email", "test@example.com")
    git(tmp_path, "config", "user.name", "Test")
    (tmp_path / "a").write_text("a"); git(tmp_path, "add", "."); git(tmp_path, "commit", "-m", "a")
    with pytest.raises(ProcessError):
        collect_changes(tmp_path, base, git(tmp_path, "rev-parse", "HEAD"))

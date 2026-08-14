import json

import pytest

from engineering_process.errors import ProcessError
from engineering_process.io import load_json, load_yaml
from engineering_process.render import bootstrap, metrics
from engineering_process.repository import initialize
from engineering_process.validation import validate_repository
from conftest import REV


def test_init_and_validate_end_to_end(tmp_path):
    result = initialize(tmp_path, "frontend", "example/web", REV)
    assert result["skills"] == 6
    assert validate_repository(tmp_path)["valid"]
    assert "write clean code" not in (tmp_path / "AGENTS.md").read_text().lower()


def test_codex_and_claude_preserve_semantics(manifest):
    codex, claude = bootstrap(manifest, "codex"), bootstrap(manifest, "claude")
    for phrase in ("Protected ambiguity fails closed", "fresh context", "exact target and process revisions"):
        assert phrase in codex and phrase in claude


def test_stale_generated_file_fails(tmp_path):
    initialize(tmp_path, "generic", "example/repo", REV)
    (tmp_path / "AGENTS.md").write_text("stale")
    with pytest.raises(ProcessError, match="stale generated adapter"):
        validate_repository(tmp_path)


def test_stale_skill_fails(tmp_path):
    initialize(tmp_path, "generic", "example/repo", REV)
    (tmp_path / ".engineering/skills/functional-qa/SKILL.md").write_text("stale")
    with pytest.raises(ProcessError, match="stale or missing Skill"):
        validate_repository(tmp_path)


def test_wrong_process_revision_fails(tmp_path):
    initialize(tmp_path, "generic", "example/repo", REV)
    lock = load_json(tmp_path / ".engineering/process.lock")
    lock["revision"] = "c" * 40
    (tmp_path / ".engineering/process.lock").write_text(json.dumps(lock))
    with pytest.raises(ProcessError, match="lock mismatch"):
        validate_repository(tmp_path)


def test_manifest_drift_fails(tmp_path):
    initialize(tmp_path, "generic", "example/repo", REV)
    path = tmp_path / ".engineering/process.yaml"
    manifest = load_yaml(path); manifest["repository"]["name"] = "changed"
    import yaml
    path.write_text(yaml.safe_dump(manifest))
    with pytest.raises(ProcessError, match="manifest drift"):
        validate_repository(tmp_path)


def test_bootstrap_token_budget(tmp_path):
    initialize(tmp_path, "generic", "example/repo", REV)
    values = metrics(tmp_path)
    assert values["AGENTS.md"]["approx_tokens"] < 300
    assert values["CLAUDE.md"]["approx_tokens"] < 300


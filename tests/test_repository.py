import json
from pathlib import PureWindowsPath

import pytest

from engineering_process.errors import ProcessError
from engineering_process.io import load_json, load_yaml
from engineering_process.render import bootstrap, metrics
from engineering_process.repository import _relative_posix, apply_upgrade, initialize, upgrade_report
from engineering_process.validation import validate_repository
from conftest import REV


def test_init_and_validate_end_to_end(tmp_path):
    result = initialize(tmp_path, "frontend", "example/web", REV)
    assert result["skills"] == 6
    assert validate_repository(tmp_path)["valid"]
    assert "write clean code" not in (tmp_path / "AGENTS.md").read_text().lower()


def test_generated_lock_paths_are_portable(tmp_path):
    initialize(tmp_path, "frontend", "example/web", REV)
    lock = load_json(tmp_path / ".engineering/process.lock")
    assert all("\\" not in relative for relative in lock["generated_files"])
    assert ".engineering/skills/architecture-review/SKILL.md" in lock["generated_files"]


def test_relative_posix_converts_windows_paths():
    root = PureWindowsPath(r"C:\repo")
    path = root / ".engineering" / "skills" / "architecture-review" / "SKILL.md"
    assert _relative_posix(path, root) == ".engineering/skills/architecture-review/SKILL.md"


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


def test_runtime_revision_must_match_lock(tmp_path):
    initialize(tmp_path, "generic", "example/repo", REV)
    assert validate_repository(tmp_path, REV)["runtime_revision"] == REV
    with pytest.raises(ProcessError, match="runtime process revision mismatch"):
        validate_repository(tmp_path, "c" * 40)


@pytest.mark.parametrize("revision", ["main", "1.1.0", "abc"])
def test_runtime_revision_rejects_floating_or_malformed_values(tmp_path, revision):
    initialize(tmp_path, "generic", "example/repo", REV)
    with pytest.raises(ProcessError, match="immutable 40-character"):
        validate_repository(tmp_path, revision)


def test_generated_workflow_installs_and_validates_same_exact_revision(tmp_path):
    initialize(tmp_path, "generic", "example/repo", REV)
    workflow = (tmp_path / ".github/workflows/process-validation.yml").read_text()
    assert f"software-engineering-process@{REV}" in workflow
    assert f"--runtime-revision '{REV}'" in workflow


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


@pytest.mark.parametrize("names", [("AGENTS.md",), ("CLAUDE.md",), ("AGENTS.md", "CLAUDE.md")])
def test_init_refuses_existing_assistant_context(tmp_path, names):
    for name in names:
        (tmp_path / name).write_text(f"local rules in {name}", encoding="utf-8")
    with pytest.raises(ProcessError, match="repository-owned context"):
        initialize(tmp_path, "frontend", "example/web", REV)
    for name in names:
        assert (tmp_path / name).read_text(encoding="utf-8") == f"local rules in {name}"
    assert not (tmp_path / ".engineering/process.yaml").exists()


def test_mature_repository_adoption_preserves_and_declares_context(tmp_path):
    (tmp_path / "AGENTS.md").write_text("dev/main and issue-first workflow; UX Gates A-D", encoding="utf-8")
    (tmp_path / "CLAUDE.md").write_text("architecture and deployment rules", encoding="utf-8")
    result = initialize(tmp_path, "frontend", "example/web", REV, adopt_existing_context=True)
    assert len(result["preserved_context"]) == 2
    manifest = load_yaml(tmp_path / ".engineering/process.yaml")
    for item in manifest["local_context"]:
        assert (tmp_path / item["path"]).exists()
        assert item["path"] in (tmp_path / "AGENTS.md").read_text(encoding="utf-8")
    assert "dev/main and issue-first" in (tmp_path / manifest["local_context"][0]["path"]).read_text(encoding="utf-8")
    assert validate_repository(tmp_path)["valid"]


def test_missing_local_context_fails_validation(tmp_path):
    initialize(tmp_path, "generic", "example/repo", REV)
    manifest_path = tmp_path / ".engineering/process.yaml"
    manifest = load_yaml(manifest_path)
    manifest["local_context"] = [{"category": "architecture", "path": "docs/architecture.md"}]
    import yaml
    manifest_path.write_text(yaml.safe_dump(manifest, sort_keys=False), encoding="utf-8")
    lock = load_json(tmp_path / ".engineering/process.lock")
    from engineering_process.repository import manifest_digest
    lock["manifest_digest"] = manifest_digest(manifest)
    (tmp_path / ".engineering/process.lock").write_text(json.dumps(lock), encoding="utf-8")
    with pytest.raises(ProcessError, match="missing local-context reference"):
        validate_repository(tmp_path)


def test_upgrade_preserves_local_context_and_reports_adapter_changes(tmp_path):
    (tmp_path / "AGENTS.md").write_text("local workflow", encoding="utf-8")
    initialize(tmp_path, "frontend", "example/web", REV, adopt_existing_context=True)
    context_path = tmp_path / "docs/engineering/local-context/agents-legacy.md"
    report = upgrade_report(tmp_path, "1.4.1", "c" * 40)
    assert report["preserved_local_context"] == ["docs/engineering/local-context/agents-legacy.md"]
    assert {item["path"] for item in report["generated_files_change"]} >= {"AGENTS.md", "CLAUDE.md"}
    apply_upgrade(tmp_path, "1.4.1", "c" * 40)
    assert context_path.read_text(encoding="utf-8") == "local workflow"
    assert "c" * 40 in (tmp_path / ".github/workflows/process-validation.yml").read_text(encoding="utf-8")
    lock = load_json(tmp_path / ".engineering/process.lock")
    assert all("\\" not in relative for relative in lock["generated_files"])
    assert validate_repository(tmp_path)["valid"]


def test_upgrade_refuses_modified_generated_file(tmp_path):
    initialize(tmp_path, "generic", "example/repo", REV)
    (tmp_path / "AGENTS.md").write_text("repository modification", encoding="utf-8")
    with pytest.raises(ProcessError, match="refusing to overwrite"):
        apply_upgrade(tmp_path, "1.4.1", "c" * 40)


def test_init_refuses_repository_owned_workflow_without_partial_state(tmp_path):
    workflow = tmp_path / ".github/workflows/process-validation.yml"
    workflow.parent.mkdir(parents=True)
    workflow.write_text("name: repository workflow", encoding="utf-8")
    with pytest.raises(ProcessError, match="repository-owned file"):
        initialize(tmp_path, "generic", "example/repo", REV)
    assert workflow.read_text(encoding="utf-8") == "name: repository workflow"
    assert not (tmp_path / ".engineering/process.yaml").exists()


def test_local_context_cannot_reference_generated_or_parent_paths(tmp_path):
    initialize(tmp_path, "generic", "example/repo", REV)
    import yaml
    for invalid in ("AGENTS.md", ".engineering/process.yaml", "../outside.md"):
        manifest_path = tmp_path / ".engineering/process.yaml"
        manifest = load_yaml(manifest_path)
        manifest["local_context"] = [{"category": "other", "path": invalid}]
        manifest_path.write_text(yaml.safe_dump(manifest, sort_keys=False), encoding="utf-8")
        lock = load_json(tmp_path / ".engineering/process.lock")
        from engineering_process.repository import manifest_digest
        lock["manifest_digest"] = manifest_digest(manifest)
        (tmp_path / ".engineering/process.lock").write_text(json.dumps(lock), encoding="utf-8")
        with pytest.raises(ProcessError, match="invalid repository-process|ownership boundary"):
            validate_repository(tmp_path)

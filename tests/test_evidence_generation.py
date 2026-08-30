from engineering_process.evidence import validate_attestation
import pytest

from engineering_process.errors import ProcessError
from engineering_process.evidence_generation import generate_test_result
from engineering_process.io import load_json
from engineering_process.paths import schemas_root


def github_env(monkeypatch):
    values = {"GITHUB_ACTIONS": "true", "GITHUB_WORKFLOW_REF": ".github/workflows/assurance.yml@refs/heads/main",
              "GITHUB_RUN_ID": "42", "GITHUB_RUN_ATTEMPT": "1", "GITHUB_JOB": "test"}
    for key, value in values.items():
        monkeypatch.setenv(key, value)


def test_ci_runner_generates_command_log_environment_and_provenance(tmp_path, manifest, monkeypatch):
    github_env(monkeypatch)
    manifest["overrides"]["validation"] = {"commands": [
        {"command": "python -c \"print('focused ok')\"", "category": "focused"},
        {"command": "python -c \"print('integration ok')\"", "category": "integration"},
    ]}
    obligations = {"required_validation_categories": ["focused", "integration"],
                   "validation_commands": manifest["overrides"]["validation"]["commands"]}
    att, trust = generate_test_result(tmp_path, manifest, obligations, "b" * 40, tmp_path / "artifacts")
    basis = att["predicate"]["validation"]
    assert basis["complete"] and len(basis["runs"]) == 2
    assert all((tmp_path / "artifacts" / run["log"]["name"]).exists() for run in basis["runs"])
    assert next(iter(trust.values()))["workflow"].endswith("@refs/heads/main")
    validate_attestation(att, load_json(schemas_root() / "evidence.schema.json"), "b" * 40,
                         manifest["process"]["revision"], manifest["repository"]["name"])


def test_ci_runner_rejects_unapproved_workflow(tmp_path, manifest, monkeypatch):
    github_env(monkeypatch)
    manifest["repository"]["trusted_ci_workflows"] = [".github/workflows/different.yml"]
    manifest["overrides"]["validation"] = {"commands": ["python -c \"print('ok')\""]}
    with pytest.raises(ProcessError, match="not authorized"):
        generate_test_result(tmp_path, manifest, {"required_validation_categories": ["focused"],
                                                  "validation_commands": manifest["overrides"]["validation"]["commands"]},
                             "b" * 40, tmp_path / "artifacts")


def test_validation_commands_do_not_interpolate_shell_syntax(tmp_path, manifest, monkeypatch):
    github_env(monkeypatch)
    manifest["overrides"]["validation"] = {"commands": [{"command": "python -c \"print('ok')\" ; python -c \"open('injected.txt','w').write('bad')\"", "category": "focused"}]}
    generate_test_result(tmp_path, manifest, {"required_validation_categories": ["focused"],
                                              "validation_commands": manifest["overrides"]["validation"]["commands"]},
                         "b" * 40, tmp_path / "artifacts")
    assert not (tmp_path / "injected.txt").exists()


def test_command_start_failure_is_recorded_as_failed_evidence(tmp_path, manifest, monkeypatch):
    github_env(monkeypatch)
    commands = [{"command": "definitely-not-a-real-executable", "category": "focused"}]
    manifest["overrides"]["validation"] = {"commands": commands}
    att, _ = generate_test_result(tmp_path, manifest,
                                  {"required_validation_categories": ["focused"], "validation_commands": commands},
                                  "b" * 40, tmp_path / "artifacts")
    assert att["predicate"]["verdict"] == "fail"
    assert att["predicate"]["validation"]["runs"][0]["exitCode"] == 127
    assert "could not start" in (tmp_path / "artifacts/validation-0-focused.log").read_text()

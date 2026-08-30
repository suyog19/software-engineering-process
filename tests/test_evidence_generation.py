from engineering_process.evidence import validate_attestation
import pytest

from engineering_process.errors import ProcessError
from engineering_process.evidence_generation import generate_test_result, _parse_workflow_ref
from engineering_process.io import load_json
from engineering_process.paths import schemas_root


def github_env(monkeypatch):
    values = {"GITHUB_ACTIONS": "true", "GITHUB_WORKFLOW_REF": "example/repo/.github/workflows/assurance.yml@refs/heads/main",
              "GITHUB_RUN_ID": "42", "GITHUB_RUN_ATTEMPT": "1", "GITHUB_JOB": "test",
              "GITHUB_EVENT_NAME": "workflow_dispatch", "GITHUB_REF_PROTECTED": "true"}
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
    assert next(iter(trust.values()))["workflow_ref"] == "refs/heads/main"
    assert next(iter(trust.values()))["workflow_path"] == ".github/workflows/assurance.yml"
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


@pytest.mark.parametrize("value", [None, ".github/workflows/assurance.yml@refs/heads/main",
    "example/repo/ci.yml@refs/heads/main", "example/repo/.github/workflows/../evil.yml@refs/heads/main",
    "example/repo/.github/workflows/assurance.yml@"])
def test_workflow_ref_parser_fails_closed(value):
    with pytest.raises(ProcessError):
        _parse_workflow_ref(value)


@pytest.mark.parametrize("allowed", [["assurance.yml"], [".github/workflows/assurance"],
    [".github/workflows/assurance.yml.extra"], ["workflows/assurance.yml"]])
def test_ci_runner_rejects_fragments_and_ambiguous_legacy_paths(tmp_path, manifest, monkeypatch, allowed):
    github_env(monkeypatch)
    manifest["repository"]["trusted_ci_workflows"] = allowed
    commands = ["python -c \"print('ok')\""]
    manifest["overrides"]["validation"] = {"commands": commands}
    with pytest.raises(ProcessError):
        generate_test_result(tmp_path, manifest, {"required_validation_categories": ["focused"],
            "validation_commands": commands}, "b" * 40, tmp_path / "artifacts")


def test_ci_runner_rejects_other_repository_untrusted_ref_and_pull_request(tmp_path, manifest, monkeypatch):
    github_env(monkeypatch)
    commands = ["python -c \"print('ok')\""]
    manifest["overrides"]["validation"] = {"commands": commands}
    obligations = {"required_validation_categories": ["focused"], "validation_commands": commands}
    monkeypatch.setenv("GITHUB_WORKFLOW_REF", "other/repo/.github/workflows/assurance.yml@refs/heads/main")
    with pytest.raises(ProcessError, match="repository mismatch"):
        generate_test_result(tmp_path, manifest, obligations, "b" * 40, tmp_path / "other")
    monkeypatch.setenv("GITHUB_WORKFLOW_REF", "example/repo/.github/workflows/assurance.yml@refs/heads/feature")
    with pytest.raises(ProcessError, match="unauthorized workflow ref"):
        generate_test_result(tmp_path, manifest, obligations, "b" * 40, tmp_path / "feature")
    monkeypatch.setenv("GITHUB_WORKFLOW_REF", "example/repo/.github/workflows/assurance.yml@" + "c" * 40)
    monkeypatch.setenv("GITHUB_EVENT_NAME", "pull_request")
    with pytest.raises(ProcessError, match="pull_request workflow content"):
        generate_test_result(tmp_path, manifest, obligations, "b" * 40, tmp_path / "pr")


def test_immutable_workflow_sha_is_authorized(tmp_path, manifest, monkeypatch):
    github_env(monkeypatch)
    monkeypatch.setenv("GITHUB_WORKFLOW_REF", "example/repo/.github/workflows/assurance.yml@" + "c" * 40)
    monkeypatch.setenv("GITHUB_REF_PROTECTED", "false")
    commands = ["python -c \"print('ok')\""]
    manifest["overrides"]["validation"] = {"commands": commands}
    generate_test_result(tmp_path, manifest, {"required_validation_categories": ["focused"],
        "validation_commands": commands}, "b" * 40, tmp_path / "sha")
    with pytest.raises(ProcessError, match="cannot bootstrap"):
        generate_test_result(tmp_path, manifest, {"required_validation_categories": ["focused"],
            "validation_commands": commands}, "c" * 40, tmp_path / "bootstrap")


def test_display_name_is_never_an_authorization_fallback(tmp_path, manifest, monkeypatch):
    github_env(monkeypatch)
    monkeypatch.delenv("GITHUB_WORKFLOW_REF")
    monkeypatch.setenv("GITHUB_WORKFLOW", ".github/workflows/assurance.yml")
    with pytest.raises(ProcessError, match="GITHUB_WORKFLOW_REF is required"):
        generate_test_result(tmp_path, manifest, {}, "b" * 40, tmp_path / "display")


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

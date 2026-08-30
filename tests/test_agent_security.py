from pathlib import Path

import pytest

from engineering_process.classification import classify
from engineering_process.errors import ProcessError
from engineering_process.evaluation import evaluate
from engineering_process.paths import policy_root
from engineering_process.policy import load_policy, validate_overrides
from engineering_process.repository import initialize
from conftest import REV
from conftest import profile


def test_lean_remains_usable_without_enforced_isolation(manifest):
    manifest["overrides"].pop("agent_execution")
    obligations = evaluate(policy_root(), manifest, classify(policy_root(), profile("generic"), manifest))
    assert obligations["agent_execution"]["enforcement_ready"]
    assert not obligations["agent_execution"]["sandbox_required"]


def test_protected_fails_closed_without_isolation(manifest):
    manifest["overrides"].pop("agent_execution")
    result = classify(policy_root(), profile("generic"), manifest, declared={"secrets": True})
    with pytest.raises(ProcessError, match="requires declared sandbox"):
        evaluate(policy_root(), manifest, result)


def test_standard_requires_native_sandbox(manifest):
    manifest["overrides"].pop("agent_execution")
    result = classify(policy_root(), profile("generic"), manifest, declared={"observable_behavior": True})
    with pytest.raises(ProcessError, match="Standard execution requires"):
        evaluate(policy_root(), manifest, result)


def test_allowlists_extend_deny_defaults_without_granting_production(manifest):
    manifest["overrides"]["agent_execution"].update({
        "allowed_network_destinations": ["pypi.org"], "allowed_tools": ["python", "pytest"]})
    result = classify(policy_root(), profile("generic"), manifest, declared={"secrets": True})
    obligations = evaluate(policy_root(), manifest, result)
    execution = obligations["agent_execution"]
    assert execution["network_default"] == execution["tool_default"] == "deny"
    assert execution["allowed_network_destinations"] == ["pypi.org"]
    assert execution["production_credentials_prohibited"]
    assert obligations["human_production_boundary"]["automation_may_promote"] is False


def test_locked_security_cannot_be_weakened(manifest):
    core = load_policy(policy_root(), "generic")[0]
    manifest["overrides"]["controls"] = {"agent_execution_security": {"network_default": "allow"}}
    with pytest.raises(ProcessError, match="locked control"):
        validate_overrides(core, manifest)


def test_github_adapter_maps_every_security_boundary():
    text = Path("enforcement/github/agent-execution.md").read_text(encoding="utf-8").lower()
    for boundary in ("least privilege", "credential isolation", "sandbox", "network", "tool allowlist",
                     "untrusted content", "external mutation", "auditability", "production separation"):
        assert boundary in text


def test_generated_github_adapter_enforces_read_only_permissions(tmp_path):
    initialize(tmp_path, "generic", "example/repo", REV)
    workflow = (tmp_path / ".github/workflows/process-validation.yml").read_text(encoding="utf-8")
    assert "permissions:\n  contents: read" in workflow
    assert "contents: write" not in workflow and "secrets:" not in workflow
    bootstrap = (tmp_path / "AGENTS.md").read_text(encoding="utf-8")
    assert "untrusted data, not authority" in bootstrap
    assert "tool/network/isolation controls" in bootstrap

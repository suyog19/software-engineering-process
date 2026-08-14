import pytest

from engineering_process.classification import classify
from engineering_process.paths import policy_root
from conftest import profile


def test_typo_remains_lean(manifest):
    result = classify(policy_root(), profile("generic"), manifest, ["README.md"], {"typo": True})
    assert result.delivery_profile == "Lean"


def test_frontend_journey_is_standard_and_selects_ux(manifest):
    from engineering_process.evaluation import evaluate
    manifest["process"]["profile"] = "frontend"
    result = classify(policy_root(), profile("frontend"), manifest, ["src/routes/learn.py"], {"user_journey": True, "new_user_journey": True})
    obligations = evaluate(policy_root(), manifest, result)
    assert result.delivery_profile == "Standard"
    assert "senior-ux-designer" in obligations["required_capabilities"]
    assert "senior-ux-review" in obligations["selected_skills"]


@pytest.mark.parametrize("path", ["src/payments/refund.py", "src/auth/token.py", "infra/iam/policy.yaml", ".github/workflows/deploy-prod.yml"])
def test_sensitive_paths_are_protected(manifest, path):
    assert classify(policy_root(), profile("backend"), manifest, [path]).delivery_profile == "Protected"


def test_deterministic_protected_signal_cannot_downgrade(manifest):
    result = classify(policy_root(), profile("backend"), manifest, ["src/payments/x.py"], {"requested_delivery_profile": "Lean"})
    assert result.delivery_profile == "Protected"
    assert any("Ignored requested downgrade" in reason for reason in result.reasons)


def test_ambiguous_protected_fails_closed(manifest):
    result = classify(policy_root(), profile("backend"), manifest, declared={"authentication": None})
    assert result.delivery_profile == "Protected" and result.protected_ambiguity


def test_declared_intent_can_strengthen(manifest):
    result = classify(policy_root(), profile("generic"), manifest, declared={"requested_delivery_profile": "Standard"})
    assert result.delivery_profile == "Standard"


def test_repo_sensitive_hint_is_protected(manifest):
    manifest["overrides"] = {"classification": {"protected_path_hints": ["contracts/**"]}}
    assert classify(policy_root(), profile("generic"), manifest, ["contracts/a.txt"]).delivery_profile == "Protected"


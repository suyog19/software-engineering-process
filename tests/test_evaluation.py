from engineering_process.classification import classify
from engineering_process.evaluation import evaluate
from engineering_process.paths import policy_root
from conftest import profile


def test_relevant_skills_only_for_lean(manifest):
    result = classify(policy_root(), profile("generic"), manifest, declared={"typo": True})
    obligations = evaluate(policy_root(), manifest, result)
    assert obligations["selected_skills"] == ["independent-review"]
    assert "functional-qa" not in obligations["required_capabilities"]


def test_protected_obligations_complete(manifest):
    result = classify(policy_root(), profile("backend"), manifest, declared={"iam": True})
    obligations = evaluate(policy_root(), manifest, result)
    assert {"non-functional-qa", "solution-sufficiency", "independent-review"} <= set(obligations["required_capabilities"])
    assert "human-approval/v1" in obligations["required_evidence"]
    assert obligations["approvals"] == ["human-production-approval"]


def test_no_generic_coding_competence_emitted(manifest):
    result = classify(policy_root(), profile("generic"), manifest)
    text = str(evaluate(policy_root(), manifest, result)).lower()
    assert "meaningful names" not in text and "keep functions small" not in text


def test_native_capabilities_are_exposed(manifest):
    result = classify(policy_root(), profile("generic"), manifest)
    native = evaluate(policy_root(), manifest, result)["native_enforcement"]
    assert native["protected_branches"] is True
    assert native["production_environment"]["prevent_self_review"] is True


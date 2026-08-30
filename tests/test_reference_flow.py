import subprocess

from engineering_process.classification import classify
from engineering_process.evaluation import evaluate
from engineering_process.evidence import evidence_id, make_attestation, verify_readiness
from engineering_process.evidence_generation import generate_review, generate_test_result
from engineering_process.git_changes import collect_changes
from engineering_process.io import load_json
from engineering_process.paths import policy_root, schemas_root
from conftest import profile


def git(root, *args):
    return subprocess.run(["git", *args], cwd=root, check=True, capture_output=True, text=True).stdout.strip()


def test_exact_head_to_readiness_reference_flow(tmp_path, manifest, monkeypatch):
    git(tmp_path, "init"); git(tmp_path, "config", "user.email", "test@example.com"); git(tmp_path, "config", "user.name", "Test")
    (tmp_path / "README.md").write_text("before")
    git(tmp_path, "add", "."); git(tmp_path, "commit", "-m", "base")
    base = git(tmp_path, "rev-parse", "HEAD")
    (tmp_path / "README.md").write_text("after")
    git(tmp_path, "commit", "-am", "head")
    head = git(tmp_path, "rev-parse", "HEAD")

    manifest["overrides"]["validation"] = {"commands": [
        {"command": "python -c \"print('focused validation')\"", "category": "focused"}]}
    paths, changes = collect_changes(tmp_path, base, head)
    classification = classify(policy_root(), profile("generic"), manifest, paths, {"typo": True},
                              target_revision=head, base_revision=base, change_set=changes,
                              input_trust="trusted-git-diff")
    obligations = evaluate(policy_root(), manifest, classification)
    assert obligations["classification"]["input_trust"] == "trusted-git-diff"

    for key, value in {"GITHUB_ACTIONS": "true", "GITHUB_WORKFLOW_REF": ".github/workflows/assurance.yml@refs/heads/main",
                       "GITHUB_RUN_ID": "77", "GITHUB_RUN_ATTEMPT": "1", "GITHUB_JOB": "test"}.items():
        monkeypatch.setenv(key, value)
    test_evidence, test_trust = generate_test_result(tmp_path, manifest, obligations, head, tmp_path / "objective")
    classification_evidence = make_attestation(manifest["repository"]["name"], head, "classification/v1",
                                               manifest["process"]["version"], manifest["process"]["revision"],
                                               "orchestrator", "pass", "github-actions", "77:classify")
    basis = {
        "issue": {"reference": "#fixture", "acceptanceCriteriaReviewed": True},
        "fullDiff": {"base": base, "head": head, "inspected": True},
        "context": {"paths": [], "applicableContextReviewed": True},
        "validation": {"evidenceIds": [evidence_id(test_evidence)], "examined": True},
        "counterexamples": {"scenarios": ["documentation-only scope"], "searched": True},
        "unverifiedAreas": [], "editedChange": False,
    }
    monkeypatch.setenv("GITHUB_JOB", "review")
    review, review_trust = generate_review(manifest, head, basis, [], [], "reviewer", "77:review", "implementation", "authorized-human")
    trust = {**test_trust, **review_trust}
    result = verify_readiness(obligations, [classification_evidence, test_evidence, review],
                              load_json(schemas_root() / "evidence.schema.json"), head, trust)
    assert result["ready"]

    without_review = verify_readiness(obligations, [classification_evidence, test_evidence],
                                      load_json(schemas_root() / "evidence.schema.json"), head, test_trust)
    assert not without_review["ready"] and without_review["missing"] == ["independent-review/v2"]


def test_reference_workflows_use_exact_sha_artifacts_and_no_production_authority():
    assurance = open("enforcement/github/reusable-workflows/reference-assurance.yml", encoding="utf-8").read()
    review = open("enforcement/github/workflows/reference-independent-review.yml", encoding="utf-8").read()
    assert "--base '${{ inputs.base-sha }}' --head '${{ inputs.target-sha }}'" in assurance
    assert "software-engineering-process@${{ steps.process.outputs.revision }}" in assurance
    assert "process-objective-${{ inputs.target-sha }}" in assurance
    assert "engineering-process readiness" in assurance
    assert "environment: independent-review" in review
    assert "deploy" not in assurance.lower() and "contents: write" not in assurance.lower()

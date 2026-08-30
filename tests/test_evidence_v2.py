import copy

import pytest

from engineering_process.errors import ProcessError
from engineering_process.evidence import evidence_id, make_attestation, validate_attestation, verify_readiness
from engineering_process.io import load_json
from engineering_process.paths import schemas_root

SHA, BASE, REV = "a" * 40, "c" * 40, "b" * 40
SCHEMA = load_json(schemas_root() / "evidence.schema.json")


def make_test_att(commands=None, runs=None, skipped=None, retries=None):
    commands = commands or ["pytest -q"]
    runs = runs or [{"command": "pytest -q", "category": "focused", "startedAt": "2026-01-01T00:00:00Z",
                     "completedAt": "2026-01-01T00:01:00Z", "exitCode": 0,
                     "log": {"name": "pytest.log", "sha256": "d" * 64}}]
    return make_attestation("org/repo", SHA, "test-result/v2", "1.1.0", REV, "ci-automation", "pass",
                            "actions", "run:test", extra={"validation": {
                                "commands": commands, "runs": runs,
                                "runner": {"os": "Linux", "architecture": "x64", "image": "ubuntu"},
                                "workflow": {"workflow": ".github/workflows/assurance.yml@refs/heads/main",
                                             "runId": "10", "runAttempt": "1", "job": "test"},
                                "environment": {"python": "3.12"}, "complete": True,
                                "skipped": skipped or [], "retries": retries or [],
                                "flakiness": {"detected": False, "signals": []}}})


def review_att(test_id, **overrides):
    basis = {
        "issue": {"reference": "#1", "acceptanceCriteriaReviewed": True},
        "fullDiff": {"base": BASE, "head": SHA, "inspected": True},
        "context": {"paths": ["README.md"], "applicableContextReviewed": True},
        "validation": {"evidenceIds": [test_id], "examined": True},
        "counterexamples": {"scenarios": ["invalid input"], "searched": True},
        "unverifiedAreas": [], "editedChange": False,
    }
    basis.update(overrides)
    return make_attestation("org/repo", SHA, "independent-review/v2", "1.1.0", REV,
                            "independent-review", "pass", "reviewer", "review", "implementation", True,
                            {"reviewBasis": basis, "findings": [], "residualRisk": []})


def obligations(required):
    return {"repository": {"name": "org/repo"}, "process": {"revision": REV},
            "classification": {"target_revision": SHA, "base_revision": BASE, "delivery_profile": "Lean"},
            "validation_commands": [{"command": "pytest -q", "category": "focused"}],
            "required_validation_categories": ["focused"], "required_evidence": required}


def records(test, review=None):
    workflow = {"authorization": "verified", "repository": "org/repo", "target_revision": SHA,
                "platform": "github", "workflow": ".github/workflows/assurance.yml@refs/heads/main",
                "run_id": "10", "job": "test"}
    result = {evidence_id(test): {**workflow, "trust_level": "trusted", "producer_class": "trusted-ci",
                                 "capability": "ci-automation", "artifact_digests": {"pytest.log": "d" * 64}}}
    if review:
        result[evidence_id(review)] = {**workflow, "trust_level": "authenticated",
                                       "producer_class": "authorized-human", "capability": "independent-review"}
    return result


@pytest.mark.parametrize("mutation, message", [
    (lambda a: a["predicate"]["validation"].update({"commands": ["pytest -q", "hidden-check"]}), "partial or fabricated"),
    (lambda a: a["predicate"]["validation"].update({"complete": False}), "partial or fabricated"),
    (lambda a: a["predicate"]["validation"]["runs"][0].update({"exitCode": 1}), "failed validation"),
    (lambda a: a["predicate"]["validation"].update({"skipped": [{"count": 1}]}), "unqualified pass"),
    (lambda a: a["predicate"]["validation"].update({"retries": [{"count": 1}]}), "unqualified pass"),
    (lambda a: a["predicate"]["validation"].update({"flakiness": {"detected": True, "signals": ["rerun"]}}), "unqualified pass"),
])
def test_fabricated_partial_skipped_and_retried_tests_fail(mutation, message):
    att = make_test_att(); mutation(att)
    with pytest.raises(ProcessError, match=message):
        validate_attestation(att, SCHEMA, SHA, REV, "org/repo")


def test_altered_log_or_wrong_workflow_identity_fails():
    att = make_test_att(); trust = records(att)
    trust[evidence_id(att)]["artifact_digests"]["pytest.log"] = "e" * 64
    with pytest.raises(ProcessError, match="log digest"):
        verify_readiness(obligations(["test-result/v2"]), [att], SCHEMA, SHA, trust)


def test_downloaded_log_content_is_verified(tmp_path):
    att = make_test_att(); trust = records(att)
    (tmp_path / "pytest.log").write_text("altered")
    with pytest.raises(ProcessError, match="downloaded validation log was altered"):
        verify_readiness(obligations(["test-result/v2"]), [att], SCHEMA, SHA, trust, tmp_path)


def test_qualified_failed_run_is_valid_evidence_but_blocks_readiness():
    att = make_test_att()
    att["predicate"]["verdict"] = "fail"
    att["predicate"]["validation"]["runs"][0]["exitCode"] = 1
    result = verify_readiness(obligations(["test-result/v2"]), [att], SCHEMA, SHA, records(att))
    assert not result["ready"] and result["failed"] == ["test-result/v2"]
    trust = records(att); trust[evidence_id(att)]["workflow"] = "wrong.yml"
    with pytest.raises(ProcessError, match="workflow identity"):
        verify_readiness(obligations(["test-result/v2"]), [att], SCHEMA, SHA, trust)


def test_internally_consistent_but_unconfigured_command_is_rejected():
    run = {"command": "curl attacker.invalid", "category": "focused", "startedAt": "2026-01-01T00:00:00Z",
           "completedAt": "2026-01-01T00:00:01Z", "exitCode": 0,
           "log": {"name": "pytest.log", "sha256": "d" * 64}}
    att = make_test_att(commands=["curl attacker.invalid"], runs=[run])
    with pytest.raises(ProcessError, match="resolved repository validation commands"):
        verify_readiness(obligations(["test-result/v2"]), [att], SCHEMA, SHA, records(att))


def test_complete_test_and_review_basis_pass_readiness():
    test = make_test_att(); review = review_att(evidence_id(test))
    result = verify_readiness(obligations(["test-result/v2", "independent-review/v2"]),
                              [test, review], SCHEMA, SHA, records(test, review))
    assert result["ready"]


@pytest.mark.parametrize("change, message", [
    ({"issue": {}}, "missing reference"),
    ({"counterexamples": {"searched": False, "scenarios": []}}, "counterexample"),
    ({"editedChange": True}, "fresh re-review"),
    ({"unverifiedAreas": ["load testing"]}, "unverified areas"),
])
def test_superficial_editing_or_unverified_review_cannot_pass(change, message):
    test = make_test_att(); review = review_att(evidence_id(test), **change)
    with pytest.raises(ProcessError, match=message):
        validate_attestation(review, SCHEMA, SHA, REV, "org/repo")


def test_stale_review_of_earlier_diff_fails_later_sha_readiness():
    test = make_test_att(); review = review_att(evidence_id(test), fullDiff={"base": BASE, "head": "e" * 40, "inspected": True})
    with pytest.raises(ProcessError, match="stale or covers the wrong diff"):
        verify_readiness(obligations(["test-result/v2", "independent-review/v2"]),
                         [test, review], SCHEMA, SHA, records(test, review))


def test_same_context_v2_review_is_rejected():
    test = make_test_att(); review = review_att(evidence_id(test))
    review["predicate"]["producer"]["contextId"] = "implementation"
    with pytest.raises(ProcessError, match="fresh context"):
        validate_attestation(review, SCHEMA, SHA, REV, "org/repo")


def test_residual_risks_must_be_machine_readable():
    test = make_test_att(); review = review_att(evidence_id(test))
    review["predicate"]["residualRisk"] = ["unknown"]
    with pytest.raises(ProcessError, match="residualRisk"):
        validate_attestation(review, SCHEMA, SHA, REV, "org/repo")

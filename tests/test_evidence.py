import pytest

from engineering_process.errors import ProcessError
from engineering_process.evidence import make_attestation, verify_readiness
from engineering_process.io import load_json
from engineering_process.paths import schemas_root
from conftest import REV, SHA

SCHEMA = load_json(schemas_root() / "evidence.schema.json")


def obligation(required):
    return {"process": {"revision": REV}, "required_evidence": required}


def att(predicate, sha=SHA, verdict="pass", context="review", implementation="build", fresh=True):
    capabilities = {"test-result/v1": "ci-automation", "independent-review/v1": "independent-review"}
    return make_attestation("repo", sha, predicate, "1.0.0", REV, capabilities[predicate], verdict, "actor", context, implementation, fresh)


def test_evidence_from_another_commit_fails():
    with pytest.raises(ProcessError, match="wrong SHA"):
        verify_readiness(obligation(["test-result/v1"]), [att("test-result/v1", "c" * 40)], SCHEMA, SHA)


def test_missing_evidence_fails_readiness():
    result = verify_readiness(obligation(["test-result/v1", "independent-review/v1"]), [att("test-result/v1")], SCHEMA, SHA)
    assert not result["ready"] and result["missing"] == ["independent-review/v1"]


def test_invalid_self_review_context_fails():
    with pytest.raises(ProcessError, match="fresh context"):
        verify_readiness(obligation(["independent-review/v1"]), [att("independent-review/v1", context="same", implementation="same")], SCHEMA, SHA)


def test_not_fresh_review_fails():
    with pytest.raises(ProcessError, match="fresh context"):
        verify_readiness(obligation(["independent-review/v1"]), [att("independent-review/v1", fresh=False)], SCHEMA, SHA)


def test_contradictory_evidence_fails():
    result = verify_readiness(obligation(["test-result/v1"]), [att("test-result/v1"), att("test-result/v1", verdict="fail")], SCHEMA, SHA)
    assert not result["ready"] and result["contradictory"] == ["test-result/v1"]


def test_complete_exact_revision_evidence_passes():
    result = verify_readiness(obligation(["test-result/v1", "independent-review/v1"]), [att("test-result/v1"), att("independent-review/v1")], SCHEMA, SHA)
    assert result["ready"]

from datetime import datetime, timedelta, timezone

import pytest

from engineering_process.errors import ProcessError
from engineering_process.evidence import evidence_id, make_attestation, verify_readiness
from engineering_process.io import load_json
from engineering_process.paths import schemas_root

SHA, REV = "a" * 40, "b" * 40


def setup(repository="org/repo"):
    att = make_attestation(repository, SHA, "test-result/v1", "1.1.0", REV,
                           "ci-automation", "pass", "actions", "run")
    obligations = {"repository": {"name": "org/repo"}, "process": {"revision": REV},
                   "classification": {"target_revision": SHA, "delivery_profile": "Protected"},
                   "required_evidence": ["test-result/v1"]}
    record = {"trust_level": "trusted", "authorization": "verified", "repository": "org/repo",
              "target_revision": SHA, "producer_class": "trusted-ci", "capability": "ci-automation",
              "platform": "github", "workflow": ".github/workflows/process.yml", "run_id": "1", "job": "test"}
    return att, obligations, record


def verify(att, obligations, record=None):
    trust = {evidence_id(att): record} if record else None
    return verify_readiness(obligations, [att], load_json(schemas_root() / "evidence.schema.json"), SHA, trust)


def test_protected_committed_json_cannot_masquerade_as_trusted():
    att, obligations, _ = setup()
    with pytest.raises(ProcessError, match="requires trusted"):
        verify(att, obligations)


def test_verified_github_identity_satisfies_protected_objective_evidence():
    att, obligations, record = setup()
    assert verify(att, obligations, record)["ready"]


@pytest.mark.parametrize("mutation, message", [
    ({"repository": "other/repo"}, "wrong repository"),
    ({"producer_class": "authorized-agent"}, "unauthorized producer"),
    ({"authorization": "denied"}, "not verified"),
    ({"workflow": ""}, "workflow/run/job"),
    ({"fork": True}, "fork evidence"),
])
def test_impersonation_replay_wrong_workflow_and_capability_fail(mutation, message):
    att, obligations, record = setup(); record.update(mutation)
    with pytest.raises(ProcessError, match=message):
        verify(att, obligations, record)


def test_expired_provenance_requires_rerun():
    att, obligations, record = setup()
    record["expires_at"] = (datetime.now(timezone.utc) - timedelta(seconds=1)).isoformat()
    with pytest.raises(ProcessError, match="expired"):
        verify(att, obligations, record)


def test_wrong_subject_repository_is_rejected_even_for_asserted_evidence():
    att, obligations, _ = setup("other/repo")
    obligations["classification"]["delivery_profile"] = "Lean"
    with pytest.raises(ProcessError, match="wrong repository"):
        verify(att, obligations)

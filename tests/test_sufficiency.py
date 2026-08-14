from engineering_process.sufficiency import triage


def test_suggestions_do_not_automatically_increase_scope():
    result = triage([{"id": "framework", "category": "optional", "outcome": "defer"}])
    assert result["verdict"] == "sufficient" and result["defer"]


def test_steward_cannot_suppress_mandatory_finding():
    result = triage([{"id": "bug", "category": "correctness", "outcome": "reject"}])
    assert result["verdict"] == "insufficient"
    assert result["must_address"][0]["outcome"] == "must_address"


def test_unnecessary_abstraction_can_be_rejected():
    result = triage([{"id": "generic-factory", "category": "speculative_abstraction", "outcome": "reject"}])
    assert result["reject"] and result["stopping_rule_met"]


def test_stopping_rule_allows_optional_improvements():
    result = triage([{"id": "polish", "category": "optional", "outcome": "worth_addressing_now"}, {"id": "future", "category": "future", "outcome": "defer"}])
    assert result["verdict"] == "sufficient" and result["stopping_rule_met"]


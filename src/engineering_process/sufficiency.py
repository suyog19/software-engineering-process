from __future__ import annotations

MANDATORY_CATEGORIES = {
    "acceptance_criterion", "correctness", "locked_control", "security", "privacy",
    "mandatory_accessibility", "mandatory_ux", "protected_assurance", "product_owner_criterion",
    "blocking_review", "material_operational_risk", "approved_architecture", "public_contract",
}
OUTCOMES = {"must_address", "worth_addressing_now", "defer", "reject"}


def triage(findings: list[dict]) -> dict:
    buckets = {name: [] for name in OUTCOMES}
    for finding in findings:
        category = finding.get("category")
        requested = finding.get("outcome", "defer")
        if requested not in OUTCOMES:
            raise ValueError(f"unknown sufficiency outcome: {requested}")
        outcome = "must_address" if category in MANDATORY_CATEGORIES else requested
        item = {**finding, "outcome": outcome}
        if outcome != requested:
            item["decision_note"] = "Mandatory finding cannot be suppressed by Solution Steward"
        buckets[outcome].append(item)
    blocking = bool(buckets["must_address"])
    return {
        "verdict": "insufficient" if blocking else "sufficient",
        **{name: buckets[name] for name in sorted(OUTCOMES)},
        "stopping_rule_met": not blocking,
        "stopping_rationale": (
            "Mandatory findings remain" if blocking else
            "Acceptance and controls may close while optional improvements remain deferred or rejected"
        ),
    }


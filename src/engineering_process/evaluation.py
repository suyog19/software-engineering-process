from __future__ import annotations

from pathlib import Path

from .classification import Classification
from .policy import effective_controls, load_policy

CAPABILITY_SKILLS = {
    "senior-ux-designer": "senior-ux-review",
    "architect": "architecture-review",
    "functional-qa": "functional-qa",
    "non-functional-qa": "non-functional-qa",
    "independent-review": "independent-review",
    "solution-sufficiency": "solution-sufficiency",
}


def evaluate(policy_root: Path, manifest: dict, classification: Classification) -> dict:
    core, profile, delivery_profiles = load_policy(policy_root, manifest["process"]["profile"])
    controls = effective_controls(core, profile, manifest)
    selected = delivery_profiles[classification.delivery_profile]
    capabilities = set(selected["required_capabilities"])
    evidence = set(selected["required_evidence"])
    chars = {k for k, v in classification.characteristics.items() if v is True}
    ux_triggers = set(profile.get("add", {}).get("ux_triggers", []))
    ux_triggers.update(manifest.get("overrides", {}).get("ux", {}).get("additional_required_when", []))
    if chars & ux_triggers:
        capabilities.add("senior-ux-designer")
        evidence.add("ux-verdict/v1")
    if "architecture" in chars:
        capabilities.add("architect")
        evidence.add("architecture-decision/v1")
    if chars & {"observable_behavior", "user_journey", "state_transition", "validation_or_error"}:
        capabilities.add("functional-qa")
        evidence.add("functional-qa-verdict/v1")
    required_capabilities = sorted(capabilities)
    all_caps = set(core["capabilities"])
    approvals = ["human-production-approval"] if classification.delivery_profile == "Protected" else []
    security = controls["agent_execution_security"]
    extensions = manifest.get("overrides", {}).get("agent_execution", {})
    sandbox_available = bool(extensions.get("sandbox"))
    isolation_available = sandbox_available and bool(extensions.get("network_enforcement")) and bool(extensions.get("audit_sink"))
    if classification.delivery_profile == "Standard" and not sandbox_available:
        from .errors import ProcessError
        raise ProcessError("Standard execution requires a declared native sandbox")
    if classification.delivery_profile == "Protected" and not isolation_available:
        from .errors import ProcessError
        raise ProcessError("Protected execution requires declared sandbox, network enforcement, and audit sink")
    agent_execution = {
        "profile": classification.delivery_profile,
        "least_privilege": security["least_privilege"],
        "sandbox_required": classification.delivery_profile in security["sandbox_required_for"],
        "sandbox": extensions.get("sandbox"),
        "credential_isolation_required": security["credential_isolation_required"],
        "production_credentials_prohibited": security["production_credentials_prohibited"],
        "network_default": security["network_default"],
        "allowed_network_destinations": sorted(extensions.get("allowed_network_destinations", [])),
        "network_enforcement": extensions.get("network_enforcement"),
        "tool_default": security["tool_default"],
        "allowed_tools": sorted(extensions.get("allowed_tools", [])),
        "denied_tools": sorted(extensions.get("additional_denied_tools", [])),
        "external_mutation_requires_explicit_authorization": security["external_mutation_requires_explicit_authorization"],
        "destructive_action_requires_explicit_authorization": security["destructive_action_requires_explicit_authorization"],
        "untrusted_content_is_data_not_instruction": security["untrusted_content_is_data_not_instruction"],
        "audit_log_required": security["audit_log_required"],
        "audit_sink": extensions.get("audit_sink"),
        "enforcement_ready": isolation_available if classification.delivery_profile == "Protected" else (sandbox_available if classification.delivery_profile == "Standard" else True),
    }
    return {
        "process": manifest["process"],
        "repository": manifest["repository"],
        "classification": classification.to_dict(),
        "required_capabilities": required_capabilities,
        "required_evidence": sorted(evidence),
        "selected_skills": sorted(CAPABILITY_SKILLS[c] for c in capabilities if c in CAPABILITY_SKILLS),
        "approvals": approvals,
        "prohibited_actions": sorted(selected["prohibited_actions"]),
        "native_enforcement": core["native_enforcement"],
        "human_production_boundary": controls["human_production_boundary"],
        "independent_review": controls["independent_review"],
        "validation_commands": controls["validation_commands"]["values"],
        "required_validation_categories": selected["required_validation_categories"],
        "agent_execution": agent_execution,
        "not_required": sorted(all_caps - capabilities),
        "execution_boundary": "Policy defines WHAT; assistants, humans, CI and native controls own HOW.",
    }

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

from .errors import ProcessError
from .io import load_json, load_yaml
from .paths import policy_root
from .schema_validation import validate

BASE = "https://suyogjoshi.com/software-signal/engineering/"


def make_attestation(repository: str, sha: str, predicate: str, process_version: str,
                     process_revision: str, capability: str, verdict: str,
                     identity: str, context_id: str, implementation_context_id: str | None = None,
                     fresh_context: bool = False, extra: dict | None = None) -> dict:
    body = {
        "processVersion": process_version, "processRevision": process_revision,
        "capability": capability, "verdict": verdict,
        "issuedAt": datetime.now(timezone.utc).isoformat(),
        "producer": {"identity": identity, "contextId": context_id,
                     "implementationContextId": implementation_context_id, "freshContext": fresh_context},
        "findings": [], "residualRisk": [],
    }
    body.update(extra or {})
    return {"_type": "https://in-toto.io/Statement/v1",
            "subject": [{"name": repository, "digest": {"gitCommit": sha}}],
            "predicateType": BASE + predicate, "predicate": body}


def predicate_short(attestation: dict) -> str:
    return attestation["predicateType"].removeprefix(BASE)


def validate_attestation(attestation: dict, schema: dict, sha: str, process_revision: str) -> None:
    errors = validate(attestation, schema)
    if errors:
        raise ProcessError("malformed evidence: " + "; ".join(errors))
    subject_sha = attestation["subject"][0]["digest"]["gitCommit"]
    if subject_sha != sha:
        raise ProcessError(f"evidence bound to wrong SHA: {subject_sha} != {sha}")
    pred = attestation["predicate"]
    if pred["processRevision"] != process_revision:
        raise ProcessError("evidence uses wrong process revision")
    short = predicate_short(attestation)
    predicates = load_yaml(policy_root() / "evidence" / "predicate-types.yaml")
    if short not in predicates:
        raise ProcessError(f"unknown evidence predicate: {short}")
    contract = predicates[short]
    if pred["capability"] != contract["capability"]:
        raise ProcessError(f"invalid producer capability for {short}")
    if pred["verdict"] not in contract["passing_verdicts"] and pred["verdict"] != "fail":
        raise ProcessError(f"invalid verdict for {short}: {pred['verdict']}")
    if short == "independent-review/v1":
        producer = pred["producer"]
        if not producer.get("freshContext") or producer.get("contextId") == producer.get("implementationContextId"):
            raise ProcessError("independent review must use a fresh context distinct from implementation")


def verify_readiness(obligations: dict, attestations: Iterable[dict], schema: dict, sha: str) -> dict:
    classified_sha = obligations.get("classification", {}).get("target_revision")
    if classified_sha and classified_sha != sha:
        raise ProcessError(f"classification bound to wrong SHA: {classified_sha} != {sha}")
    valid: dict[str, list[dict]] = {}
    for attestation in attestations:
        validate_attestation(attestation, schema, sha, obligations["process"]["revision"])
        key = predicate_short(attestation)
        valid.setdefault(key, []).append(attestation)
    required = set(obligations["required_evidence"])
    missing = sorted(required - set(valid))
    failures = sorted(k for k, items in valid.items() for a in items if a["predicate"]["verdict"] == "fail")
    contradictory = sorted(k for k, items in valid.items() if len({a["predicate"]["verdict"] for a in items}) > 1)
    ready = not (missing or failures or contradictory)
    return {"ready": ready, "target_revision": sha, "missing": missing,
            "failed": failures, "contradictory": contradictory, "satisfied": sorted(required & set(valid))}


def load_attestations(directory: Path) -> list[dict]:
    return [load_json(path) for path in sorted(directory.glob("*.json"))] if directory.exists() else []

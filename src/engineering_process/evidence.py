from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
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


def evidence_id(attestation: dict) -> str:
    """Stable identifier used by an out-of-band transport verification index."""
    return hashlib.sha256(json.dumps(attestation, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def validate_attestation(attestation: dict, schema: dict, sha: str, process_revision: str,
                         repository: str | None = None) -> None:
    errors = validate(attestation, schema)
    if errors:
        raise ProcessError("malformed evidence: " + "; ".join(errors))
    subject_sha = attestation["subject"][0]["digest"]["gitCommit"]
    if subject_sha != sha:
        raise ProcessError(f"evidence bound to wrong SHA: {subject_sha} != {sha}")
    if repository and attestation["subject"][0]["name"] != repository:
        raise ProcessError("evidence is bound to the wrong repository")
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


def verify_readiness(obligations: dict, attestations: Iterable[dict], schema: dict, sha: str,
                     trust_records: dict[str, dict] | None = None) -> dict:
    classified_sha = obligations.get("classification", {}).get("target_revision")
    if classified_sha and classified_sha != sha:
        raise ProcessError(f"classification bound to wrong SHA: {classified_sha} != {sha}")
    valid: dict[str, list[tuple[dict, str]]] = {}
    repository = obligations.get("repository", {}).get("name")
    delivery = obligations.get("classification", {}).get("delivery_profile", "Lean")
    authorization = load_yaml(policy_root() / "evidence" / "producer-authorization.yaml")
    ranks = authorization["trust_levels"]
    trust_records = trust_records or {}
    for attestation in attestations:
        validate_attestation(attestation, schema, sha, obligations["process"]["revision"], repository)
        key = predicate_short(attestation)
        record = trust_records.get(evidence_id(attestation), {})
        level = record.get("trust_level", "asserted")
        if level not in ranks:
            raise ProcessError(f"unknown evidence trust level: {level}")
        rule = authorization["predicates"][key]
        minimum = rule.get("minimum", {}).get(delivery, "asserted")
        if ranks[level] < ranks[minimum]:
            raise ProcessError(f"{delivery} {key} requires {minimum} evidence; received {level}")
        if level != "asserted":
            if record.get("authorization") != "verified":
                raise ProcessError(f"producer authorization was not verified for {key}")
            if record.get("repository") != repository or record.get("target_revision") != sha:
                raise ProcessError("authenticated evidence provenance has wrong repository or revision")
            if record.get("producer_class") not in rule["producer_classes"]:
                raise ProcessError(f"unauthorized producer class for {key}")
            if record.get("capability") != attestation["predicate"]["capability"]:
                raise ProcessError(f"authenticated producer lacks capability for {key}")
            if record.get("platform") == "github" and not all(record.get(k) for k in ("workflow", "run_id", "job")):
                raise ProcessError("GitHub evidence is missing workflow/run/job identity")
            if record.get("fork") and not record.get("base_repository_authorized"):
                raise ProcessError("fork evidence was not authorized by the base repository")
            expires = record.get("expires_at")
            if expires and datetime.fromisoformat(expires.replace("Z", "+00:00")) <= datetime.now(timezone.utc):
                raise ProcessError(f"evidence provenance has expired for {key}")
        valid.setdefault(key, []).append((attestation, level))
    required = set(obligations["required_evidence"])
    missing = sorted(required - set(valid))
    failures = sorted(k for k, items in valid.items() for a, _ in items if a["predicate"]["verdict"] == "fail")
    contradictory = sorted(k for k, items in valid.items() if len({a["predicate"]["verdict"] for a, _ in items}) > 1)
    ready = not (missing or failures or contradictory)
    return {"ready": ready, "target_revision": sha, "missing": missing,
            "failed": failures, "contradictory": contradictory, "satisfied": sorted(required & set(valid)),
            "trust": {key: sorted({level for _, level in items}) for key, items in valid.items()}}


def load_attestations(directory: Path) -> list[dict]:
    return [load_json(path) for path in sorted(directory.glob("*.json"))] if directory.exists() else []

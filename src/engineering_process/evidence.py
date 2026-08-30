from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from typing import Iterable

from .errors import ProcessError
from .io import load_json, load_yaml
from .paths import policy_root, schemas_root
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
    if short in {"independent-review/v1", "independent-review/v2"}:
        producer = pred["producer"]
        if not producer.get("freshContext") or producer.get("contextId") == producer.get("implementationContextId"):
            raise ProcessError("independent review must use a fresh context distinct from implementation")
    if short == "test-result/v2":
        contract_errors = validate(pred, load_json(schemas_root() / "test-result-v2.schema.json"))
        if contract_errors:
            raise ProcessError("malformed test-result/v2: " + "; ".join(contract_errors))
        _validate_test_result_v2(pred)
    if short == "independent-review/v2":
        contract_errors = validate(pred, load_json(schemas_root() / "independent-review-v2.schema.json"))
        if contract_errors:
            raise ProcessError("malformed independent-review/v2: " + "; ".join(contract_errors))
        _validate_independent_review_v2(pred)


def _validate_test_result_v2(pred: dict) -> None:
    basis = pred.get("validation")
    if not isinstance(basis, dict):
        raise ProcessError("test-result/v2 is missing executable validation basis")
    runs = basis.get("runs")
    required = {"commands", "runs", "runner", "workflow", "environment", "complete", "skipped", "retries", "flakiness"}
    if not required.issubset(basis) or not isinstance(runs, list) or not runs:
        raise ProcessError("test-result/v2 validation basis is incomplete")
    planned = basis["commands"]
    executed = [run.get("command") for run in runs]
    if not basis["complete"] or planned != executed:
        raise ProcessError("partial or fabricated validation command execution")
    for run in runs:
        needed = {"command", "category", "startedAt", "completedAt", "exitCode", "log"}
        if not needed.issubset(run):
            raise ProcessError("validation run record is incomplete")
        if pred.get("verdict") == "pass" and run["exitCode"] != 0:
            raise ProcessError("failed validation run cannot pass")
        log = run["log"]
        if not isinstance(log, dict) or not log.get("name") or len(log.get("sha256", "")) != 64:
            raise ProcessError("validation run lacks an immutable log digest")
    if pred.get("verdict") == "pass" and (basis["skipped"] or basis["retries"] or basis["flakiness"].get("detected")):
        raise ProcessError("skipped, retried, or flaky validation cannot be an unqualified pass")


def _validate_independent_review_v2(pred: dict) -> None:
    basis = pred.get("reviewBasis")
    if not isinstance(basis, dict):
        raise ProcessError("independent-review/v2 is missing review basis")
    issue = basis.get("issue", {})
    diff = basis.get("fullDiff", {})
    context = basis.get("context", {})
    validation = basis.get("validation", {})
    counterexamples = basis.get("counterexamples", {})
    if not issue.get("reference") or not issue.get("acceptanceCriteriaReviewed"):
        raise ProcessError("independent review did not establish issue and acceptance basis")
    if not diff.get("inspected") or len(diff.get("base", "")) != 40 or len(diff.get("head", "")) != 40:
        raise ProcessError("independent review did not inspect the complete exact-revision diff")
    if not context.get("applicableContextReviewed") or not isinstance(context.get("paths"), list):
        raise ProcessError("independent review did not examine applicable repository context")
    if not validation.get("examined") or not validation.get("evidenceIds"):
        raise ProcessError("independent review did not examine validation evidence")
    if not counterexamples.get("searched") or not isinstance(counterexamples.get("scenarios"), list):
        raise ProcessError("independent review did not record counterexample search")
    if not isinstance(basis.get("unverifiedAreas"), list):
        raise ProcessError("independent review did not disclose unverified areas")
    if basis.get("editedChange"):
        raise ProcessError("a reviewer who edits the change must start a fresh re-review before verdict")
    findings = pred.get("findings")
    if not isinstance(findings, list) or any(not isinstance(f, dict) or "blocking" not in f or "severity" not in f for f in findings):
        raise ProcessError("independent review findings are not machine-readable")
    residual = pred.get("residualRisk")
    if not isinstance(residual, list) or any(not isinstance(r, dict) or "severity" not in r or "description" not in r for r in residual):
        raise ProcessError("independent review residual risks are not machine-readable")
    if pred.get("verdict") == "pass" and (any(f["blocking"] for f in findings) or basis["unverifiedAreas"]):
        raise ProcessError("blocking findings or unverified areas cannot produce an unqualified pass")


def verify_readiness(obligations: dict, attestations: Iterable[dict], schema: dict, sha: str,
                     trust_records: dict[str, dict] | None = None, artifact_root: Path | None = None) -> dict:
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
        if key == "test-result/v2":
            basis = attestation["predicate"]["validation"]
            configured = obligations.get("validation_commands", [])
            expected_commands = [item["command"] if isinstance(item, dict) else item for item in configured]
            expected_categories = [item.get("category", "focused") if isinstance(item, dict) else "focused" for item in configured]
            if not expected_commands or basis["commands"] != expected_commands:
                raise ProcessError("test evidence commands do not match resolved repository validation commands")
            if [run["category"] for run in basis["runs"]] != expected_categories:
                raise ProcessError("test evidence categories do not match resolved repository validation plan")
            categories = {run["category"] for run in basis["runs"]}
            required_categories = set(obligations.get("required_validation_categories", []))
            if not required_categories.issubset(categories):
                raise ProcessError("test evidence is missing required validation categories: " + ", ".join(sorted(required_categories - categories)))
            if level != "asserted":
                workflow = basis["workflow"]
                if workflow.get("workflow") != record.get("workflow") or str(workflow.get("runId")) != str(record.get("run_id")) or workflow.get("job") != record.get("job"):
                    raise ProcessError("test evidence workflow identity does not match verified provenance")
                trusted_digests = record.get("artifact_digests", {})
                for run in basis["runs"]:
                    if trusted_digests.get(run["log"]["name"]) != run["log"]["sha256"]:
                        raise ProcessError("validation log digest does not match verified artifact provenance")
                    if artifact_root is not None:
                        log_name = run["log"]["name"]
                        log_path = artifact_root / log_name
                        if Path(log_name).name != log_name or not log_path.is_file():
                            raise ProcessError("validation log artifact is missing or has an unsafe name")
                        if hashlib.sha256(log_path.read_bytes()).hexdigest() != run["log"]["sha256"]:
                            raise ProcessError("downloaded validation log was altered")
        if key == "independent-review/v2":
            diff = attestation["predicate"]["reviewBasis"]["fullDiff"]
            classification = obligations.get("classification", {})
            if diff["head"] != sha or diff["base"] != classification.get("base_revision"):
                raise ProcessError("independent review basis is stale or covers the wrong diff")
        valid.setdefault(key, []).append((attestation, level))
    required = set(obligations["required_evidence"])
    missing = sorted(required - set(valid))
    failures = sorted(k for k, items in valid.items() for a, _ in items if a["predicate"]["verdict"] == "fail")
    contradictory = sorted(k for k, items in valid.items() if len({a["predicate"]["verdict"] for a, _ in items}) > 1)
    if "independent-review/v2" in valid:
        available_ids = {evidence_id(a) for items in valid.values() for a, _ in items}
        for review, _ in valid["independent-review/v2"]:
            referenced = set(review["predicate"]["reviewBasis"]["validation"]["evidenceIds"])
            if not referenced.issubset(available_ids):
                raise ProcessError("independent review references unavailable validation evidence")
    ready = not (missing or failures or contradictory)
    return {"ready": ready, "target_revision": sha, "missing": missing,
            "failed": failures, "contradictory": contradictory, "satisfied": sorted(required & set(valid)),
            "trust": {key: sorted({level for _, level in items}) for key, items in valid.items()}}


def load_attestations(directory: Path) -> list[dict]:
    return [load_json(path) for path in sorted(directory.glob("*.json"))] if directory.exists() else []

from __future__ import annotations

import hashlib
import os
import platform
import re
import shlex
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from pathlib import PurePosixPath

from .errors import ProcessError
from .evidence import evidence_id, make_attestation


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


_SHA = re.compile(r"^[0-9a-f]{40}$")
_WORKFLOW_REF = re.compile(r"^([A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+)/(.+)@(.+)$")


def _normalized_workflow_path(value: str) -> str:
    if "\\" in value or value.startswith("/"):
        raise ProcessError(f"workflow path is not a normalized repository path: {value!r}")
    path = PurePosixPath(value)
    if any(part in {"", ".", ".."} for part in value.split("/")) or str(path) != value:
        raise ProcessError(f"workflow path contains traversal or normalization ambiguity: {value!r}")
    if len(path.parts) < 3 or path.parts[:2] != (".github", "workflows") or path.suffix not in {".yml", ".yaml"}:
        raise ProcessError(f"workflow path must be a YAML file below .github/workflows/: {value!r}")
    return value


def _parse_workflow_ref(value: str | None) -> dict:
    if not value:
        raise ProcessError("GITHUB_WORKFLOW_REF is required; GITHUB_WORKFLOW display names are diagnostic only")
    match = _WORKFLOW_REF.fullmatch(value)
    if not match:
        raise ProcessError(f"malformed GITHUB_WORKFLOW_REF: {value!r}")
    repository, workflow_path, ref = match.groups()
    if not ref or ref.strip() != ref or "@" in ref:
        raise ProcessError(f"GITHUB_WORKFLOW_REF has a missing or ambiguous ref: {value!r}")
    return {"repository": repository, "workflow_path": _normalized_workflow_path(workflow_path),
            "workflow_ref": ref}


def _workflow_identity(manifest: dict, target_sha: str) -> dict:
    if os.environ.get("GITHUB_ACTIONS") != "true":
        raise ProcessError("trusted evidence generation must run in GitHub Actions")
    parsed = _parse_workflow_ref(os.environ.get("GITHUB_WORKFLOW_REF"))
    required = {
        **parsed, "run_id": os.environ.get("GITHUB_RUN_ID"),
        "run_attempt": os.environ.get("GITHUB_RUN_ATTEMPT"),
        "job": os.environ.get("GITHUB_JOB"), "event": os.environ.get("GITHUB_EVENT_NAME", "unknown"),
        "ref_protected": os.environ.get("GITHUB_REF_PROTECTED") == "true",
    }
    if not all(required.get(key) for key in ("repository", "workflow_path", "workflow_ref", "run_id", "run_attempt", "job")):
        raise ProcessError("GitHub workflow identity is incomplete")
    expected = manifest.get("repository", {}).get("name")
    if parsed["repository"].lower() != str(expected).lower():
        raise ProcessError(f"workflow repository mismatch: parsed={parsed['repository']!r}; expected={expected!r}")
    event = os.environ.get("GITHUB_EVENT_NAME")
    protected_branch = manifest.get("adapters", {}).get("github", {}).get("protected_branch", "main")
    permitted = f"40-character immutable SHA or protected refs/heads/{protected_branch}"
    immutable = bool(_SHA.fullmatch(parsed["workflow_ref"]))
    protected_default = (parsed["workflow_ref"] == f"refs/heads/{protected_branch}" and
                         os.environ.get("GITHUB_REF_PROTECTED") == "true")
    if event == "pull_request":
        raise ProcessError(f"pull_request workflow content is not trusted; permitted ref rule: {permitted}")
    if immutable and parsed["workflow_ref"] == target_sha:
        raise ProcessError("a target revision cannot bootstrap trust from its own workflow revision; approve the trust change for subsequent runs")
    if event == "workflow_call":
        caller = _parse_workflow_ref(os.environ.get("GITHUB_CALLER_WORKFLOW_REF"))
        if caller["repository"].lower() != str(expected).lower():
            raise ProcessError("workflow_call caller repository does not match the configured repository")
        required["caller"] = caller
    if not (immutable or protected_default):
        raise ProcessError(f"unauthorized workflow ref {parsed['workflow_ref']!r}; permitted ref rule: {permitted}")
    return required


def _require_authorized_workflow(manifest: dict, workflow: dict, key: str) -> None:
    allowed = manifest.get("repository", {}).get(key, [])
    try:
        normalized = [_normalized_workflow_path(path) for path in allowed]
    except (ProcessError, TypeError) as exc:
        raise ProcessError(f"ambiguous legacy configuration for {key}; use exact .github/workflows/*.yml paths: {exc}") from exc
    identities = [workflow] + ([workflow["caller"]] if "caller" in workflow else [])
    rejected = [identity["workflow_path"] for identity in identities if identity["workflow_path"] not in normalized]
    if not normalized or rejected:
        raise ProcessError(f"GitHub workflow is not authorized for {key}: repository={workflow['repository']!r}; "
                           f"workflow_path={workflow['workflow_path']!r}; workflow_ref={workflow['workflow_ref']!r}; "
                           f"expected_repository={manifest.get('repository', {}).get('name')!r}; allowed_paths={normalized!r}; "
                           f"rejected_paths={rejected!r}")


def _commands(manifest: dict) -> list[dict]:
    configured = manifest.get("overrides", {}).get("validation", {}).get("commands", [])
    result = []
    for value in configured:
        if isinstance(value, str):
            result.append({"command": value, "category": "focused"})
        elif isinstance(value, dict) and isinstance(value.get("command"), str) and isinstance(value.get("category"), str):
            result.append({"command": value["command"], "category": value["category"]})
        else:
            raise ProcessError("validation commands must be strings or {command, category} objects")
    if not result:
        raise ProcessError("no repository validation commands are configured")
    return result


def generate_test_result(root: Path, manifest: dict, obligations: dict, sha: str,
                         output_dir: Path) -> tuple[dict, dict]:
    workflow = _workflow_identity(manifest, sha)
    _require_authorized_workflow(manifest, workflow, "trusted_ci_workflows")
    commands = _commands(manifest)
    resolved = obligations.get("validation_commands", [])
    resolved_commands = [item["command"] if isinstance(item, dict) else item for item in resolved]
    if resolved_commands != [item["command"] for item in commands]:
        raise ProcessError("manifest validation commands do not match the resolved obligation set")
    required = set(obligations.get("required_validation_categories", []))
    configured = {item["category"] for item in commands}
    if not required.issubset(configured):
        raise ProcessError("configured validation is missing categories: " + ", ".join(sorted(required - configured)))
    output_dir.mkdir(parents=True, exist_ok=True)
    runs, skips, flaky_signals = [], [], []
    failed = False
    for index, item in enumerate(commands):
        started = _now()
        argv = shlex.split(item["command"], posix=os.name != "nt")
        if not argv:
            raise ProcessError("validation command cannot be empty")
        try:
            completed = subprocess.run(argv, cwd=root, shell=False, text=True,
                                       stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            returncode, output = completed.returncode, completed.stdout
        except OSError as exc:
            returncode, output = 127, f"validation command could not start: {exc}\n"
        finished = _now()
        log_name = f"validation-{index}-{item['category']}.log"
        log_path = output_dir / log_name
        log_path.write_text(output, encoding="utf-8")
        digest = hashlib.sha256(output.encode()).hexdigest()
        skipped = sum(int(value) for value in re.findall(r"(\d+)\s+skipped", output, re.IGNORECASE))
        if skipped:
            skips.append({"command": item["command"], "count": skipped})
        if re.search(r"\b(flaky|flakiness|rerun|re-run)\b", output, re.IGNORECASE):
            flaky_signals.append({"command": item["command"], "signal": "runner output reported retry/flakiness"})
        failed = failed or returncode != 0
        runs.append({"command": item["command"], "category": item["category"],
                     "startedAt": started, "completedAt": finished, "exitCode": returncode,
                     "log": {"name": log_name, "sha256": digest}})
    validation = {
        "commands": [item["command"] for item in commands], "runs": runs,
        "runner": {"os": platform.system(), "architecture": platform.machine(),
                   "image": os.environ.get("ImageOS", "unknown")},
        "workflow": workflow,
        "environment": {"python": platform.python_version()},
        "complete": len(runs) == len(commands), "skipped": skips, "retries": [],
        "flakiness": {"detected": bool(flaky_signals), "signals": flaky_signals},
    }
    verdict = "fail" if failed or skips or flaky_signals else "pass"
    attestation = make_attestation(
        manifest["repository"]["name"], sha, "test-result/v2", manifest["process"]["version"],
        manifest["process"]["revision"], "ci-automation", verdict, "github-actions",
        f"{workflow['run_id']}:{workflow['job']}", extra={"validation": validation},
    )
    record = {
        "trust_level": "trusted", "authorization": "verified",
        "repository": manifest["repository"]["name"], "target_revision": sha,
        "producer_class": "trusted-ci", "capability": "ci-automation", "platform": "github",
        "workflow_repository": workflow["repository"], "workflow_path": workflow["workflow_path"],
        "workflow_ref": workflow["workflow_ref"], "run_id": workflow["run_id"], "run_attempt": workflow["run_attempt"],
        "job": workflow["job"], "event": workflow["event"], "ref_protected": workflow["ref_protected"],
        "artifact_digests": {run["log"]["name"]: run["log"]["sha256"] for run in runs},
    }
    return attestation, {evidence_id(attestation): record}


def generate_review(manifest: dict, sha: str, basis: dict, findings: list[dict], residual_risk: list,
                    identity: str, context_id: str, implementation_context_id: str,
                    producer_class: str) -> tuple[dict, dict]:
    workflow = _workflow_identity(manifest, sha)
    _require_authorized_workflow(manifest, workflow, "authorized_review_workflows")
    if producer_class not in {"authorized-human", "authorized-agent"}:
        raise ProcessError("review producer class must be authorized-human or authorized-agent")
    verdict = "fail" if any(item.get("blocking") for item in findings) or basis.get("unverifiedAreas") else "pass"
    attestation = make_attestation(
        manifest["repository"]["name"], sha, "independent-review/v2", manifest["process"]["version"],
        manifest["process"]["revision"], "independent-review", verdict, identity, context_id,
        implementation_context_id, True,
        {"reviewBasis": basis, "findings": findings, "residualRisk": residual_risk},
    )
    record = {
        "trust_level": "authenticated", "authorization": "verified",
        "repository": manifest["repository"]["name"], "target_revision": sha,
        "producer_class": producer_class,
        "capability": "independent-review", "platform": "github",
        "workflow_repository": workflow["repository"], "workflow_path": workflow["workflow_path"],
        "workflow_ref": workflow["workflow_ref"], "run_id": workflow["run_id"],
        "run_attempt": workflow["run_attempt"], "job": workflow["job"],
        "event": workflow["event"], "ref_protected": workflow["ref_protected"],
    }
    return attestation, {evidence_id(attestation): record}

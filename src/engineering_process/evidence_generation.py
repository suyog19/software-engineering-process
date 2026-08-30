from __future__ import annotations

import hashlib
import os
import platform
import re
import shlex
import subprocess
from datetime import datetime, timezone
from pathlib import Path

from .errors import ProcessError
from .evidence import evidence_id, make_attestation


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _workflow_identity() -> dict:
    if os.environ.get("GITHUB_ACTIONS") != "true":
        raise ProcessError("trusted evidence generation must run in GitHub Actions")
    required = {
        "workflow": os.environ.get("GITHUB_WORKFLOW_REF") or os.environ.get("GITHUB_WORKFLOW"),
        "runId": os.environ.get("GITHUB_RUN_ID"),
        "runAttempt": os.environ.get("GITHUB_RUN_ATTEMPT"),
        "job": os.environ.get("GITHUB_JOB"),
    }
    if not all(required.values()):
        raise ProcessError("GitHub workflow identity is incomplete")
    return required


def _require_authorized_workflow(manifest: dict, workflow: dict, key: str) -> None:
    allowed = manifest.get("repository", {}).get(key, [])
    actual = workflow["workflow"]
    if not allowed or not any(path in actual for path in allowed):
        raise ProcessError(f"GitHub workflow is not authorized by repository policy for {key}: {actual}")


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
    workflow = _workflow_identity()
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
        f"{workflow['runId']}:{workflow['job']}", extra={"validation": validation},
    )
    record = {
        "trust_level": "trusted", "authorization": "verified",
        "repository": manifest["repository"]["name"], "target_revision": sha,
        "producer_class": "trusted-ci", "capability": "ci-automation", "platform": "github",
        "workflow": workflow["workflow"], "run_id": workflow["runId"], "run_attempt": workflow["runAttempt"],
        "job": workflow["job"], "artifact_digests": {run["log"]["name"]: run["log"]["sha256"] for run in runs},
    }
    return attestation, {evidence_id(attestation): record}


def generate_review(manifest: dict, sha: str, basis: dict, findings: list[dict], residual_risk: list,
                    identity: str, context_id: str, implementation_context_id: str,
                    producer_class: str) -> tuple[dict, dict]:
    workflow = _workflow_identity()
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
        "capability": "independent-review", "platform": "github", "workflow": workflow["workflow"],
        "run_id": workflow["runId"], "run_attempt": workflow["runAttempt"], "job": workflow["job"],
    }
    return attestation, {evidence_id(attestation): record}

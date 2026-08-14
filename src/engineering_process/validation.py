from __future__ import annotations

from pathlib import Path

from .errors import ProcessError
from .io import digest_file, load_json, load_yaml
from .paths import policy_root, schemas_root, skills_root
from .policy import load_policy, validate_overrides
from .render import bootstrap
from .repository import manifest_digest
from .schema_validation import validate
from .evidence import load_attestations, verify_readiness


def _schema(name: str) -> dict:
    return load_json(schemas_root() / name)


def _validate_schema(value: dict, name: str) -> None:
    errors = validate(value, _schema(name))
    if errors:
        raise ProcessError(f"invalid {name}: " + "; ".join(errors))


def validate_repository(root: Path) -> dict:
    manifest_path, lock_path = root / ".engineering/process.yaml", root / ".engineering/process.lock"
    if not manifest_path.exists() or not lock_path.exists():
        raise ProcessError("missing .engineering/process.yaml or .engineering/process.lock")
    manifest, lock = load_yaml(manifest_path), load_json(lock_path)
    _validate_schema(manifest, "repository-process.schema.json")
    _validate_schema(lock, "process-lock.schema.json")
    core, _, _ = load_policy(policy_root(), manifest["process"]["profile"])
    if manifest["process"]["version"] != core["process"]["version"]:
        raise ProcessError("invalid process version")
    for key in ("source", "version", "revision"):
        if lock[key] != manifest["process"][key]:
            raise ProcessError(f"process lock mismatch: {key}")
    if lock["manifest_digest"] != manifest_digest(manifest):
        raise ProcessError("process manifest drift: lock digest is stale")
    validate_overrides(core, manifest)
    for name, assistant in (("AGENTS.md", "codex"), ("CLAUDE.md", "claude")):
        path = root / name
        if not path.exists() or path.read_text(encoding="utf-8") != bootstrap(manifest, assistant):
            raise ProcessError(f"stale generated adapter: {name}")
    for source in skills_root().glob("*/SKILL.md"):
        target = root / ".engineering" / "skills" / source.parent.name / "SKILL.md"
        if not target.exists() or digest_file(source) != digest_file(target):
            raise ProcessError(f"stale or missing Skill: {source.parent.name}")
    for relative, expected in lock.get("generated_files", {}).items():
        path = root / relative
        if not path.exists() or digest_file(path) != expected:
            raise ProcessError(f"generated-file drift: {relative}")
    obligations_path = root / ".engineering/effective-obligations.json"
    if obligations_path.exists():
        obligations = load_json(obligations_path)
        _validate_schema(obligations, "effective-obligations.schema.json")
        sha = obligations.get("classification", {}).get("target_revision")
        if not sha:
            raise ProcessError("classification evidence is not bound to a target revision")
        readiness = verify_readiness(obligations, load_attestations(root / ".engineering/evidence"), _schema("evidence.schema.json"), sha)
        if not readiness["ready"]:
            raise ProcessError(f"missing or invalid obligation evidence: {readiness}")
    return {"valid": True, "profile": manifest["process"]["profile"], "version": lock["version"], "revision": lock["revision"]}

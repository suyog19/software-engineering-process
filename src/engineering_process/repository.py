from __future__ import annotations

import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path

import yaml

from .errors import ProcessError
from .io import canonical_json, digest_bytes, digest_file, load_yaml, write_json
from .paths import skills_root
from .paths import policy_root
from .policy import load_policy, validate_overrides
from .render import render_files


def current_revision(root: Path) -> str:
    result = subprocess.run(["git", "rev-parse", "HEAD"], cwd=root, text=True, capture_output=True)
    sha = result.stdout.strip()
    if result.returncode or len(sha) != 40:
        raise ProcessError("cannot resolve process Git revision; provide --revision")
    return sha


def initialize(root: Path, profile: str, repository_name: str, revision: str, force: bool = False) -> dict:
    engineering = root / ".engineering"
    manifest_path = engineering / "process.yaml"
    if manifest_path.exists() and not force:
        raise ProcessError(f"already initialized: {manifest_path}")
    core, selected_profile, delivery = load_policy(policy_root(), profile)
    process_version = core["process"]["version"]
    manifest = {"schema_version": 1, "process": {"source": "suyog19/software-engineering-process", "version": process_version, "revision": revision, "profile": profile}, "repository": {"name": repository_name}, "overrides": {"validation": {"commands": []}}}
    engineering.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(yaml.safe_dump(manifest, sort_keys=False), encoding="utf-8")
    generated = render_files(root, manifest)
    destination = engineering / "skills"
    if destination.exists():
        shutil.rmtree(destination)
    shutil.copytree(skills_root(), destination)
    generated.update({str(p.relative_to(root)): digest_file(p) for p in destination.rglob("*") if p.is_file()})
    snapshot = {"core": core, "profile": selected_profile, "delivery_profiles": delivery}
    snapshot_path = engineering / "generated" / "resolved-policy.json"
    write_json(snapshot_path, snapshot)
    generated[str(snapshot_path.relative_to(root))] = digest_file(snapshot_path)
    workflow = root / ".github" / "workflows" / "process-validation.yml"
    workflow.parent.mkdir(parents=True, exist_ok=True)
    workflow.write_text(f"""name: Engineering process\non: [pull_request, push]\npermissions:\n  contents: read\njobs:\n  validate:\n    runs-on: ubuntu-latest\n    steps:\n      - uses: actions/checkout@v4\n        with: {{fetch-depth: 0}}\n      - uses: actions/setup-python@v5\n        with: {{python-version: '3.12'}}\n      - run: pip install 'git+https://github.com/suyog19/software-engineering-process@{revision}'\n      - run: engineering-process validate\n""", encoding="utf-8")
    generated[str(workflow.relative_to(root))] = digest_file(workflow)
    lock = {"schema_version": 1, "source": manifest["process"]["source"], "version": process_version, "revision": revision,
            "manifest_digest": digest_bytes(canonical_json(manifest).encode()), "policy_digest": digest_bytes(canonical_json(snapshot).encode()),
            "generated_at": datetime.now(timezone.utc).isoformat(), "generated_files": generated}
    write_json(engineering / "process.lock", lock)
    return {"created": [".engineering/process.yaml", ".engineering/process.lock", "AGENTS.md", "CLAUDE.md", ".github/workflows/process-validation.yml"], "skills": len(list(destination.glob("*/SKILL.md")))}


def manifest_digest(manifest: dict) -> str:
    return digest_bytes(canonical_json(manifest).encode())


def _flatten(value, prefix="") -> dict[str, object]:
    if isinstance(value, dict):
        return {k: v for key, item in value.items() for k, v in _flatten(item, f"{prefix}.{key}" if prefix else key).items()}
    if isinstance(value, list):
        return {prefix: tuple(value)}
    return {prefix: value}


def upgrade_report(root: Path, version: str, revision: str) -> dict:
    manifest = load_yaml(root / ".engineering" / "process.yaml")
    old_snapshot_path = root / ".engineering" / "generated" / "resolved-policy.json"
    old_snapshot = __import__("json").loads(old_snapshot_path.read_text()) if old_snapshot_path.exists() else {}
    core, profile, delivery = load_policy(policy_root(), manifest["process"]["profile"])
    if version != core["process"]["version"]:
        raise ProcessError(f"requested version {version} does not match installed process {core['process']['version']}")
    validate_overrides(core, manifest)
    new_snapshot = {"core": core, "profile": profile, "delivery_profiles": delivery}
    old, new = _flatten(old_snapshot), _flatten(new_snapshot)
    changes = [{"path": key, "before": old.get(key), "after": new.get(key)} for key in sorted(set(old) | set(new)) if old.get(key) != new.get(key)]
    locked = [c for c in changes if c["path"].startswith("core.controls.") and ".semantics" not in c["path"] and any(c["path"].startswith(f"core.controls.{name}.") for name, rule in core["controls"].items() if rule["semantics"] == "locked")]
    return {"current": manifest["process"], "proposed": {**manifest["process"], "version": version, "revision": revision},
            "inherited_rule_changes": changes, "new_locked_rule_changes": locked,
            "override_conflicts": [], "generated_files_change": ["AGENTS.md", "CLAUDE.md", ".engineering/skills/*", ".github/workflows/process-validation.yml"],
            "new_requirements": [c for c in changes if "required" in c["path"]], "requires_validation": True}


def apply_upgrade(root: Path, version: str, revision: str) -> dict:
    report = upgrade_report(root, version, revision)
    manifest = load_yaml(root / ".engineering" / "process.yaml")
    overrides = manifest.get("overrides", {})
    result = initialize(root, manifest["process"]["profile"], manifest["repository"]["name"], revision, force=True)
    updated = load_yaml(root / ".engineering" / "process.yaml"); updated["overrides"] = overrides
    (root / ".engineering/process.yaml").write_text(yaml.safe_dump(updated, sort_keys=False), encoding="utf-8")
    # Refresh the lock digest without altering generated files.
    lock_path = root / ".engineering/process.lock"; lock = __import__("json").loads(lock_path.read_text()); lock["manifest_digest"] = manifest_digest(updated); write_json(lock_path, lock)
    return {**report, "applied": True, **result}

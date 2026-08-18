from __future__ import annotations

import argparse
import json
import sys
import subprocess
from pathlib import Path

from .classification import classify
from .errors import ProcessError
from .evaluation import evaluate
from .evidence import load_attestations, make_attestation, verify_readiness
from .io import load_json, load_yaml, write_json
from .paths import data_root, policy_root, schemas_root
from .policy import load_policy
from .render import metrics, render_files
from .repository import apply_upgrade, current_revision, initialize, upgrade_report
from .sufficiency import triage
from .validation import validate_repository


def _manifest(root: Path) -> dict:
    return load_yaml(root / ".engineering" / "process.yaml")


def _json_arg(value: str | None) -> dict:
    if not value:
        return {}
    path = Path(value)
    return load_json(path) if path.exists() else json.loads(value)


def _classification(args, root: Path, manifest: dict):
    _, profile, _ = load_policy(policy_root(), manifest["process"]["profile"])
    sha = args.sha
    if not sha:
        result = subprocess.run(["git", "rev-parse", "HEAD"], cwd=root, capture_output=True, text=True)
        sha = result.stdout.strip()
    if len(sha) != 40:
        raise ProcessError("classification requires an exact target revision; use --sha")
    return classify(policy_root(), profile, manifest, args.path or [], _json_arg(args.declared), _json_arg(args.semantic), args.rationale or "", sha)


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="engineering-process", description="Engineering policy and assurance CLI")
    p.add_argument("--root", default=".", help="participating repository root")
    sub = p.add_subparsers(dest="command", required=True)
    init = sub.add_parser("init"); init.add_argument("--profile", required=True, choices=["generic", "frontend", "backend"]); init.add_argument("--repository-name"); init.add_argument("--revision"); init.add_argument("--force", action="store_true"); init.add_argument("--adopt-existing-context", action="store_true")
    sub.add_parser("validate")
    for name in ("classify", "evaluate", "explain"):
        c = sub.add_parser(name); c.add_argument("--path", action="append"); c.add_argument("--declared"); c.add_argument("--semantic"); c.add_argument("--rationale"); c.add_argument("--sha")
        if name == "evaluate": c.add_argument("--output", default=".engineering/effective-obligations.json")
    sub.add_parser("render")
    m = sub.add_parser("metrics"); m.add_argument("--obligations")
    e = sub.add_parser("attest"); e.add_argument("--predicate", required=True); e.add_argument("--sha", required=True); e.add_argument("--capability", required=True); e.add_argument("--verdict", required=True); e.add_argument("--identity", required=True); e.add_argument("--context-id", required=True); e.add_argument("--implementation-context-id"); e.add_argument("--fresh-context", action="store_true"); e.add_argument("--output", required=True)
    r = sub.add_parser("readiness"); r.add_argument("--sha", required=True); r.add_argument("--obligations", default=".engineering/effective-obligations.json"); r.add_argument("--evidence-dir", default=".engineering/evidence")
    s = sub.add_parser("sufficiency"); s.add_argument("--findings", required=True); s.add_argument("--output")
    u = sub.add_parser("upgrade"); u.add_argument("--version", required=True); u.add_argument("--revision", required=True); u.add_argument("--dry-run", action="store_true")
    return p


def run(args: argparse.Namespace) -> dict:
    root = Path(args.root).resolve()
    if args.command == "init":
        revision = args.revision or current_revision(data_root())
        return initialize(root, args.profile, args.repository_name or root.name, revision, args.force, args.adopt_existing_context)
    manifest = _manifest(root)
    if args.command == "validate": return validate_repository(root)
    if args.command in {"classify", "evaluate", "explain"}:
        result = _classification(args, root, manifest)
        if args.command == "classify": return result.to_dict()
        obligations = evaluate(policy_root(), manifest, result)
        if args.command == "evaluate":
            write_json(root / args.output, obligations); return obligations
        return {"repository_profile": manifest["process"]["profile"], "delivery_profile": result.delivery_profile,
                "process": manifest["process"], "change_characteristics": result.characteristics,
                "deterministic_signals": result.deterministic_signals, "semantic_rationale": result.semantic_rationale,
                "why": result.reasons, "required_capabilities": obligations["required_capabilities"],
                "required_evidence": obligations["required_evidence"], "selected_skills": obligations["selected_skills"],
                "native_enforcement": obligations["native_enforcement"], "prohibited_actions": obligations["prohibited_actions"],
                "not_required": obligations["not_required"], "execution_boundary": obligations["execution_boundary"]}
    if args.command == "render":
        generated = render_files(root, manifest); return {"rendered": sorted(generated)}
    if args.command == "metrics":
        obligations = load_json(root / args.obligations) if args.obligations else None
        return metrics(root, obligations["selected_skills"] if obligations else [])
    if args.command == "attest":
        att = make_attestation(manifest["repository"]["name"], args.sha, args.predicate, manifest["process"]["version"], manifest["process"]["revision"], args.capability, args.verdict, args.identity, args.context_id, args.implementation_context_id, args.fresh_context)
        write_json(root / args.output, att); return att
    if args.command == "readiness":
        obligations = load_json(root / args.obligations); evidence = load_attestations(root / args.evidence_dir)
        result = verify_readiness(obligations, evidence, load_json(schemas_root() / "evidence.schema.json"), args.sha)
        if not result["ready"]: raise ProcessError("readiness failed: " + json.dumps(result, sort_keys=True))
        return result
    if args.command == "sufficiency":
        result = triage(load_json(root / args.findings));
        if args.output: write_json(root / args.output, result)
        return result
    if args.command == "upgrade":
        return upgrade_report(root, args.version, args.revision) if args.dry_run else apply_upgrade(root, args.version, args.revision)
    raise ProcessError("unknown command")


def main() -> None:
    try:
        result = run(parser().parse_args())
        print(json.dumps(result, indent=2, sort_keys=True))
    except (ProcessError, OSError, json.JSONDecodeError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr); raise SystemExit(2)


if __name__ == "__main__": main()

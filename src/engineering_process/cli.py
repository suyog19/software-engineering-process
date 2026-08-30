from __future__ import annotations

import argparse
import json
import sys
import subprocess
from pathlib import Path

from .classification import classify
from .git_changes import collect_changes
from .dependencies import dependency_signals
from .errors import ProcessError
from .evaluation import evaluate
from .evidence import load_attestations, make_attestation, verify_readiness
from .evidence_generation import generate_review, generate_test_result
from .io import load_json, load_yaml, write_json
from .paths import data_root, policy_root, schemas_root
from .policy import load_policy
from .render import metrics, render_files
from .outcome_metrics import outcome_report, compare_outcomes
from .delegation import assess_delegation
from .adoption import adoption_report
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
    if bool(args.base) != bool(args.head):
        raise ProcessError("trusted classification requires both exact --base and --head revisions")
    sha = args.head or args.sha
    if not sha:
        result = subprocess.run(["git", "rev-parse", "HEAD"], cwd=root, capture_output=True, text=True)
        sha = result.stdout.strip()
    if len(sha) != 40:
        raise ProcessError("classification requires an exact target revision; use --sha")
    if args.base:
        if args.path:
            raise ProcessError("--path is untrusted diagnostic input and cannot be combined with trusted --base/--head classification")
        paths, changes = collect_changes(root, args.base, sha)
        dep_chars, dep_signals = dependency_signals(root, args.base, sha, changes, manifest.get("overrides",{}).get("classification",{}).get("dependency_path_hints",[]))
        return classify(policy_root(), profile, manifest, paths, _json_arg(args.declared), _json_arg(args.semantic), args.rationale or "", sha, args.base, changes, "trusted-git-diff", dep_chars, dep_signals)
    return classify(policy_root(), profile, manifest, args.path or [], _json_arg(args.declared), _json_arg(args.semantic), args.rationale or "", sha, input_trust="untrusted-manual")


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="engineering-process", description="Engineering policy and assurance CLI")
    p.add_argument("--root", default=".", help="participating repository root")
    sub = p.add_subparsers(dest="command", required=True)
    init = sub.add_parser("init"); init.add_argument("--profile", required=True, choices=["generic", "frontend", "backend"]); init.add_argument("--repository-name"); init.add_argument("--revision"); init.add_argument("--force", action="store_true"); init.add_argument("--adopt-existing-context", action="store_true")
    validate = sub.add_parser("validate"); validate.add_argument("--runtime-revision")
    for name in ("classify", "evaluate", "explain"):
        c = sub.add_parser(name); c.add_argument("--path", action="append", help="untrusted diagnostic-only path"); c.add_argument("--declared"); c.add_argument("--semantic"); c.add_argument("--rationale"); c.add_argument("--sha"); c.add_argument("--base"); c.add_argument("--head")
        if name == "evaluate": c.add_argument("--output", default=".engineering/effective-obligations.json")
    sub.add_parser("render")
    m = sub.add_parser("metrics"); m.add_argument("--obligations"); m.add_argument("--events"); m.add_argument("--baseline-events")
    d = sub.add_parser("delegation"); d.add_argument("--inputs", required=True); d.add_argument("--human-choice")
    sub.add_parser("adoption-report")
    e = sub.add_parser("attest"); e.add_argument("--predicate", required=True); e.add_argument("--sha", required=True); e.add_argument("--capability", required=True); e.add_argument("--verdict", required=True); e.add_argument("--identity", required=True); e.add_argument("--context-id", required=True); e.add_argument("--implementation-context-id"); e.add_argument("--fresh-context", action="store_true"); e.add_argument("--output", required=True)
    tv = sub.add_parser("run-validation"); tv.add_argument("--sha", required=True); tv.add_argument("--obligations", default=".engineering/effective-obligations.json"); tv.add_argument("--output-dir", required=True)
    rv = sub.add_parser("review-attest"); rv.add_argument("--sha", required=True); rv.add_argument("--basis", required=True); rv.add_argument("--findings", required=True); rv.add_argument("--residual-risk"); rv.add_argument("--identity", required=True); rv.add_argument("--producer-class", required=True, choices=["authorized-human", "authorized-agent"]); rv.add_argument("--context-id", required=True); rv.add_argument("--implementation-context-id", required=True); rv.add_argument("--output-dir", required=True)
    r = sub.add_parser("readiness"); r.add_argument("--sha", required=True); r.add_argument("--obligations", default=".engineering/effective-obligations.json"); r.add_argument("--evidence-dir", default=".engineering/evidence"); r.add_argument("--trust-index", help="out-of-band verified transport index (must be outside repository)"); r.add_argument("--artifact-dir", help="downloaded immutable validation logs")
    s = sub.add_parser("sufficiency"); s.add_argument("--findings", required=True); s.add_argument("--output")
    u = sub.add_parser("upgrade"); u.add_argument("--version", required=True); u.add_argument("--revision", required=True); u.add_argument("--dry-run", action="store_true")
    return p


def run(args: argparse.Namespace) -> dict:
    root = Path(args.root).resolve()
    if args.command == "init":
        revision = args.revision or current_revision(data_root())
        return initialize(root, args.profile, args.repository_name or root.name, revision, args.force, args.adopt_existing_context)
    manifest = _manifest(root)
    if args.command == "validate":
        runtime_revision = args.runtime_revision
        if not runtime_revision and __import__("os").environ.get("GITHUB_ACTIONS") == "true":
            raise ProcessError("CI validation requires --runtime-revision from the locked bootstrap")
        return validate_repository(root, runtime_revision)
    if args.command in {"classify", "evaluate", "explain"}:
        result = _classification(args, root, manifest)
        if args.command == "classify": return result.to_dict()
        obligations = evaluate(policy_root(), manifest, result)
        if args.command == "evaluate":
            write_json(root / args.output, obligations); return obligations
        return {"repository_profile": manifest["process"]["profile"], "delivery_profile": result.delivery_profile,
                "process": manifest["process"], "change_characteristics": result.characteristics,
                "deterministic_signals": result.deterministic_signals, "semantic_rationale": result.semantic_rationale,
                "changed_path_explanations": result.path_explanations,
                "dependency_signals": result.dependency_signals,
                "why": result.reasons, "required_capabilities": obligations["required_capabilities"],
                "required_evidence": obligations["required_evidence"], "selected_skills": obligations["selected_skills"],
                "required_validation_categories": obligations["required_validation_categories"],
                "agent_execution": obligations["agent_execution"],
                "dependency_assurance": obligations["dependency_assurance"],
                "semantic_native_enforcement": obligations["native_enforcement"],
                "selected_adapter_mapping": obligations["adapter_mapping"],
                "native_enforcement": obligations["native_enforcement"], "prohibited_actions": obligations["prohibited_actions"],
                "not_required": obligations["not_required"], "execution_boundary": obligations["execution_boundary"]}
    if args.command == "render":
        generated = render_files(root, manifest); return {"rendered": sorted(generated)}
    if args.command == "metrics":
        if args.events:
            current=load_json(root / args.events)
            return compare_outcomes(load_json(root / args.baseline_events),current) if args.baseline_events else outcome_report(current)
        obligations = load_json(root / args.obligations) if args.obligations else None
        return metrics(root, obligations["selected_skills"] if obligations else [])
    if args.command == "delegation": return assess_delegation(_json_arg(args.inputs), args.human_choice)
    if args.command == "adoption-report": return adoption_report(manifest)
    if args.command == "attest":
        if args.predicate in {"test-result/v2", "independent-review/v2"}:
            raise ProcessError(f"{args.predicate} must be produced by its dedicated authenticated command")
        att = make_attestation(manifest["repository"]["name"], args.sha, args.predicate, manifest["process"]["version"], manifest["process"]["revision"], args.capability, args.verdict, args.identity, args.context_id, args.implementation_context_id, args.fresh_context)
        write_json(root / args.output, att); return att
    if args.command == "run-validation":
        output = Path(args.output_dir).resolve()
        att, trust = generate_test_result(root, manifest, load_json(root / args.obligations), args.sha, output)
        write_json(output / "test-result.json", att); write_json(output / "trust-index.json", {"evidence": trust})
        if att["predicate"]["verdict"] != "pass": raise ProcessError("validation failed; inspect immutable logs")
        return {"evidence": str(output / "test-result.json"), "trust_index": str(output / "trust-index.json")}
    if args.command == "review-attest":
        output = Path(args.output_dir).resolve(); output.mkdir(parents=True, exist_ok=True)
        att, trust = generate_review(manifest, args.sha, load_json(Path(args.basis)), load_json(Path(args.findings)),
                                     load_json(Path(args.residual_risk)) if args.residual_risk else [], args.identity,
                                     args.context_id, args.implementation_context_id, args.producer_class)
        write_json(output / "independent-review.json", att); write_json(output / "trust-index.json", {"evidence": trust})
        return {"evidence": str(output / "independent-review.json"), "trust_index": str(output / "trust-index.json")}
    if args.command == "readiness":
        obligations = load_json(root / args.obligations); evidence = load_attestations(root / args.evidence_dir)
        trust = None
        if args.trust_index:
            trust_path = Path(args.trust_index).resolve()
            if trust_path == root or root in trust_path.parents:
                raise ProcessError("trust index must come from an out-of-band verified transport outside the repository")
            trust = load_json(trust_path).get("evidence", {})
        result = verify_readiness(obligations, evidence, load_json(schemas_root() / "evidence.schema.json"), args.sha, trust,
                                  Path(args.artifact_dir).resolve() if args.artifact_dir else None)
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

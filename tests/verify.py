"""Dependency-free acceptance suite for constrained/offline environments."""
from __future__ import annotations

import tempfile
from pathlib import Path

from engineering_process.classification import classify
from engineering_process.errors import ProcessError
from engineering_process.evaluation import evaluate
from engineering_process.evidence import make_attestation, verify_readiness
from engineering_process.io import load_json
from engineering_process.paths import policy_root, schemas_root
from engineering_process.policy import load_policy, validate_overrides
from engineering_process.repository import initialize
from engineering_process.repository import apply_upgrade, upgrade_report
from engineering_process.sufficiency import triage
from engineering_process.validation import validate_repository

REV, SHA = "a" * 40, "b" * 40


def manifest(profile="generic"):
    return {"schema_version": 1, "process": {"source": "suyog19/software-engineering-process", "version": "1.3.0", "revision": REV, "profile": profile}, "repository": {"name": "example/repo"}, "overrides": {"agent_execution": {"sandbox": "ephemeral-vm", "network_enforcement": "firewall", "audit_sink": "test-audit"}}}


def prof(name): return load_policy(policy_root(), name)[1]


def expect_error(fn, text):
    try: fn()
    except ProcessError as exc: assert text in str(exc), exc
    else: raise AssertionError(f"expected ProcessError containing {text}")


def main():
    checks = []
    def check(name, fn): fn(); checks.append(name)

    check("typo Lean", lambda: assert_eq(classify(policy_root(), prof("generic"), manifest(), declared={"typo": True}).delivery_profile, "Lean"))
    check("frontend journey Standard", lambda: assert_eq(classify(policy_root(), prof("frontend"), manifest("frontend"), declared={"user_journey": True}).delivery_profile, "Standard"))
    for path in ("src/payments/refund.py", "src/auth/token.py", "infra/iam/policy.yml", ".github/workflows/deploy-prod.yml"):
        check(f"Protected {path}", lambda path=path: assert_eq(classify(policy_root(), prof("backend"), manifest("backend"), [path]).delivery_profile, "Protected"))
    check("Protected ambiguity", lambda: assert_eq(classify(policy_root(), prof("backend"), manifest("backend"), declared={"authentication": None}).delivery_profile, "Protected"))
    check("Protected cannot downgrade", lambda: assert_eq(classify(policy_root(), prof("backend"), manifest("backend"), ["payments/x"], {"requested_delivery_profile": "Lean"}).delivery_profile, "Protected"))
    def ux():
        m=manifest("frontend"); c=classify(policy_root(), prof("frontend"), m, declared={"new_user_journey": True, "user_journey": True}); o=evaluate(policy_root(),m,c); assert "senior-ux-designer" in o["required_capabilities"] and "senior-ux-review" in o["selected_skills"]
    check("UX activation", ux)
    def lean_skills():
        m=manifest(); o=evaluate(policy_root(),m,classify(policy_root(),prof("generic"),m)); assert o["selected_skills"] == ["independent-review"]
    check("relevant Skills only", lean_skills)
    def locked():
        m=manifest(); m["overrides"]={"controls":{"independent_review":{"fresh_context_required":False}}}; expect_error(lambda: validate_overrides(load_policy(policy_root(),"generic")[0],m),"locked control")
    check("locked override", locked)
    check("mandatory sufficiency finding", lambda: assert_eq(triage([{"category":"correctness","outcome":"reject"}])["verdict"], "insufficient"))
    check("stopping with optional work", lambda: assert_eq(triage([{"category":"future","outcome":"defer"}])["stopping_rule_met"], True))
    schema=load_json(schemas_root()/"evidence.schema.json")
    def att(kind, sha=SHA, ctx="review", impl="build", fresh=True, verdict="pass"):
        capabilities={"test-result/v1":"ci-automation","independent-review/v1":"independent-review"}
        return make_attestation("repo",sha,kind,"1.1.0",REV,capabilities[kind],verdict,"actor",ctx,impl,fresh)
    obligations={"process":{"revision":REV},"required_evidence":["test-result/v1","independent-review/v1"]}
    check("wrong SHA rejected", lambda: expect_error(lambda: verify_readiness(obligations,[att("test-result/v1","c"*40)],schema,SHA),"wrong SHA"))
    check("self review rejected", lambda: expect_error(lambda: verify_readiness(obligations,[att("independent-review/v1",ctx="x",impl="x")],schema,SHA),"fresh context"))
    check("missing evidence", lambda: assert_eq(verify_readiness(obligations,[att("test-result/v1")],schema,SHA)["ready"],False))
    check("complete evidence", lambda: assert_eq(verify_readiness(obligations,[att("test-result/v1"),att("independent-review/v1")],schema,SHA)["ready"],True))
    def repository():
        with tempfile.TemporaryDirectory() as td:
            root=Path(td); initialize(root,"frontend","example/web",REV); assert validate_repository(root)["valid"]; assert len((root/"AGENTS.md").read_text())/4 < 300
            (root/"AGENTS.md").write_text("stale"); expect_error(lambda:validate_repository(root),"stale generated adapter")
    check("init validate drift token budget", repository)
    def upgrade():
        with tempfile.TemporaryDirectory() as td:
            root=Path(td); initialize(root,"backend","example/api",REV)
            dry=upgrade_report(root,"1.4.0","c"*40); assert "inherited_rule_changes" in dry and dry["proposed"]["revision"] == "c"*40
            apply_upgrade(root,"1.4.0","c"*40); assert validate_repository(root)["revision"] == "c"*40
    check("controlled process upgrade", upgrade)
    print(f"{len(checks)} acceptance checks passed")


def assert_eq(actual, expected): assert actual == expected, (actual, expected)


if __name__ == "__main__": main()

import json, subprocess
from datetime import datetime, timedelta, timezone
import pytest
from engineering_process.outcome_metrics import outcome_report, compare_outcomes
from engineering_process.delegation import assess_delegation
from engineering_process.dependencies import dependency_signals
from engineering_process.context_truth import verify_context
from engineering_process.errors import ProcessError
from engineering_process.classification import classify
from engineering_process.evaluation import evaluate
from engineering_process.paths import policy_root
from conftest import profile

def event(i,c,t,when,value=None): return {"eventId":i,"repository":"r","changeId":c,"timestamp":when,"type":t,"value":value}

def test_metrics_distinguish_local_and_end_to_end_and_missing():
    es=[event("1","a","issue_opened","2026-01-01T00:00:00Z"),event("2","a","implementation_started","2026-01-01T01:00:00Z"),event("3","a","pr_opened","2026-01-01T02:00:00Z"),event("4","a","merged","2026-01-02T00:00:00Z"),event("5","b","issue_opened","2026-01-01T00:00:00Z")]
    r=outcome_report(es); assert r["changes"][0]["local_coding_seconds"]==3600 and r["changes"][0]["end_to_end_seconds"]==86400
    assert r["missing"] and "individual ranking prohibited" in r["privacy"]

def test_metrics_reject_contradictory_events():
    e=event("x","a","merged","2026-01-01T00:00:00Z")
    with pytest.raises(ProcessError,match="duplicate"): outcome_report([e,e])
    with pytest.raises(ProcessError,match="incomplete"): outcome_report([{"eventId":"x"}])

def test_metrics_support_before_after_baselines():
    before=[event("1","a","issue_opened","2026-01-01T00:00:00Z"),event("2","a","merged","2026-01-03T00:00:00Z")]
    after=[event("3","b","issue_opened","2026-02-01T00:00:00Z"),event("4","b","merged","2026-02-02T00:00:00Z")]
    assert compare_outcomes(before,after)["endToEndDeltaSeconds"]==-86400

def test_delegation_independent_from_delivery_profile_and_conservative_unknowns():
    strong={"acceptance_clarity":"high","boundedness":"high","deterministic_validation":"high","repository_test_strength":"high","reversibility":"high","architectural_novelty":"low","tacit_domain_knowledge":"low","stakeholder_negotiation":"low","blast_radius":"low"}
    assert assess_delegation(strong)["recommendation"]=="delegate_autonomous"
    assert assess_delegation({**strong,"blast_radius":None})["recommendation"]=="human_led"
    assert "delivery_profile" not in assess_delegation(strong)
    assert assess_delegation(strong,"assist")["recommendation"]=="assist"

def git(root,*args): return subprocess.run(["git",*args],cwd=root,check=True,capture_output=True,text=True).stdout.strip()

def test_dependency_lock_refresh_vs_unpinned_action(tmp_path,manifest):
    git(tmp_path,"init"); git(tmp_path,"config","user.email","x@y"); git(tmp_path,"config","user.name","x")
    (tmp_path/"package-lock.json").write_text('{}'); git(tmp_path,"add","."); git(tmp_path,"commit","-m","b"); base=git(tmp_path,"rev-parse","HEAD")
    (tmp_path/"package-lock.json").write_text('{"x":1}'); git(tmp_path,"commit","-am","lock"); head=git(tmp_path,"rev-parse","HEAD")
    chars,sigs=dependency_signals(tmp_path,base,head,[{"path":"package-lock.json"}]); assert chars["mechanical_lock_refresh"] and not chars.get("dependency_trust_boundary")
    result=classify(policy_root(),profile("generic"),manifest,derived=chars,derived_signals=sigs); assert result.delivery_profile=="Standard"

def test_mutable_action_and_container_are_protected(tmp_path):
    git(tmp_path,"init"); git(tmp_path,"config","user.email","x@y"); git(tmp_path,"config","user.name","x")
    (tmp_path/".github/workflows").mkdir(parents=True); (tmp_path/".github/workflows/ci.yml").write_text("steps: []")
    (tmp_path/"Dockerfile").write_text("FROM ubuntu@sha256:"+"a"*64); git(tmp_path,"add","."); git(tmp_path,"commit","-m","b"); base=git(tmp_path,"rev-parse","HEAD")
    (tmp_path/".github/workflows/ci.yml").write_text("steps:\n - uses: owner/action@v4")
    (tmp_path/"Dockerfile").write_text("FROM ubuntu:latest"); git(tmp_path,"commit","-am","unsafe"); head=git(tmp_path,"rev-parse","HEAD")
    chars,sigs=dependency_signals(tmp_path,base,head,[{"path":".github/workflows/ci.yml"},{"path":"Dockerfile"}])
    assert chars["dependency_trust_boundary"] and {s["value"] for s in sigs}>={"mutable_action","mutable_container_base"}

def test_context_truth_benign_and_critical_failures(tmp_path):
    (tmp_path/"doc.md").write_text("ok")
    assert verify_context(tmp_path,[{"path":"doc.md"}])["verified"]==1
    with pytest.raises(ProcessError,match="missing owner"): verify_context(tmp_path,[{"path":"doc.md","criticality":"high"}])
    old=(datetime.now(timezone.utc)-timedelta(days=40)).isoformat()
    with pytest.raises(ProcessError,match="overdue"): verify_context(tmp_path,[{"path":"doc.md","criticality":"high","owner":"team","verification":{"type":"file","target":"doc.md"},"reviewed_at":old,"review_cadence_days":30}])
    with pytest.raises(ProcessError,match="broken link"): verify_context(tmp_path,[{"path":"doc.md","verification":{"type":"link","target":"missing.md"}}])

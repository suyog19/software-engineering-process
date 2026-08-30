import json
from pathlib import Path
import pytest, yaml
from argparse import Namespace
from engineering_process import cli
from engineering_process.adoption import adoption_report
from engineering_process.errors import ProcessError
from engineering_process.io import load_json, load_yaml
from engineering_process.paths import schemas_root
from engineering_process.render import metrics, render_files
from engineering_process.repository import initialize, apply_upgrade
from engineering_process.validation import validate_repository
from engineering_process.schema_validation import validate
from conftest import REV

def assured(manifest):
    manifest["overrides"]["validation"]={"commands":[{"command":"pytest","category":"focused"}]}
    manifest["repository"].update({"trusted_ci_workflows":["ci.yml"],"authorized_review_workflows":["review.yml"]})
    manifest["adapters"]={"github":{"readiness_status":"engineering-process"}}
    return manifest

def test_adoption_modes_are_independent_and_fail_partial_claims(manifest):
    manifest["adoption"]={"target_mode":"Assured","metrics_enabled":False}; manifest["adapters"]={}
    report=adoption_report(manifest); assert report["achieved_mode"]=="Foundation" and not report["achieved"]
    assured(manifest); report=adoption_report(manifest); assert report["achieved_mode"]=="Protected" and report["delivery_profile_independent"]
    manifest["adoption"]={"target_mode":"Governed","metrics_enabled":True}; assert adoption_report(manifest)["achieved_mode"]=="Governed"

def test_cli_adoption_report_identifies_configured_and_achieved(tmp_path,manifest,monkeypatch):
    manifest["adoption"]={"target_mode":"Assured","metrics_enabled":False}; manifest["adapters"]={}
    monkeypatch.setattr(cli,"_manifest",lambda root:manifest)
    report=cli.run(Namespace(root=str(tmp_path),command="adoption-report"))
    assert report["configured_mode"]=="Assured" and report["achieved_mode"]=="Foundation" and report["missing_prerequisites"]

def test_v2_schema_rejects_typos_and_accepts_versioned_extensions():
    schema=load_json(schemas_root()/"repository-process.schema.json")
    base={"schema_version":2,"process":{"source":"suyog19/software-engineering-process","version":"1.3.0","revision":"a"*40,"profile":"generic"},"repository":{"name":"r"}}
    bad={**base,"overrides":{"validaton":{}}}; assert any("validaton" in e for e in validate(bad,schema))
    good={**base,"overrides":{"extensions":[{"namespace":"example/domain","schema_version":1,"configuration":{"anything":True}}]}}
    assert validate(good,schema)==[]

def test_scoped_adapter_is_optional_traceable_scoped_and_measured(tmp_path,manifest):
    (tmp_path/"docs").mkdir(); (tmp_path/"docs/api.md").write_text("API truth")
    manifest["local_context"]=[{"category":"architecture","path":"docs/api.md"}]
    manifest["adapters"]={"github_copilot":{"scoped_instructions":[{"name":"api","apply_to":"src/api/**","context_paths":["docs/api.md"]}]}}
    generated=render_files(tmp_path,manifest); name=".github/instructions/api.instructions.md"
    assert name in generated
    text=(tmp_path/name).read_text(); assert 'applyTo: "src/api/**"' in text and "docs/api.md" in text and "cannot override canonical policy" in text
    assert metrics(tmp_path)["scoped_adapters"][name]["approx_tokens"]>0

def test_scoped_adapter_refuses_owned_collision(tmp_path,manifest):
    path=tmp_path/".github/instructions/api.instructions.md"; path.parent.mkdir(parents=True); path.write_text("owned")
    manifest["adapters"]={"github_copilot":{"scoped_instructions":[{"name":"api","apply_to":"src/**","context_paths":[]}]}}
    with pytest.raises(ProcessError,match="repository-owned"): render_files(tmp_path,manifest)

def test_upgrade_removes_only_hash_locked_optional_adapter(tmp_path):
    initialize(tmp_path,"generic","example/repo",REV)
    mp=tmp_path/".engineering/process.yaml"; m=load_yaml(mp)
    m["adapters"]["github_copilot"]={"scoped_instructions":[{"name":"api","apply_to":"src/api/**","context_paths":[]}]}
    mp.write_text(yaml.safe_dump(m,sort_keys=False)); apply_upgrade(tmp_path,"1.4.0","c"*40)
    scoped=tmp_path/".github/instructions/api.instructions.md"; assert scoped.exists()
    m=load_yaml(mp); del m["adapters"]["github_copilot"]; mp.write_text(yaml.safe_dump(m,sort_keys=False))
    result=apply_upgrade(tmp_path,"1.4.0","d"*40); assert not scoped.exists() and result["removed_generated_adapters"]==[".github/instructions/api.instructions.md"]

def test_upgrade_migrates_v1_manifest_to_strict_v2(tmp_path):
    initialize(tmp_path,"generic","example/repo",REV)
    mp=tmp_path/".engineering/process.yaml"; m=load_yaml(mp); m["schema_version"]=1; m.pop("adoption"); m.pop("adapters"); m["overrides"]["technology"]={"runtime":"python"}; mp.write_text(yaml.safe_dump(m,sort_keys=False))
    result=apply_upgrade(tmp_path,"1.4.0","e"*40); migrated=load_yaml(mp)
    assert result["schema_migration"]=="v1->v2" and migrated["schema_version"]==2
    assert migrated["overrides"]["extensions"][0]["namespace"]=="legacy/technology" and migrated["adapters"]["github"]

def test_scoped_adapter_manual_drift_is_detected(tmp_path):
    initialize(tmp_path,"generic","example/repo",REV)
    mp=tmp_path/".engineering/process.yaml"; m=load_yaml(mp)
    m["adapters"]["github_copilot"]={"scoped_instructions":[{"name":"api","apply_to":"src/api/**","context_paths":[]}]}; mp.write_text(yaml.safe_dump(m,sort_keys=False))
    apply_upgrade(tmp_path,"1.4.0","f"*40); scoped=tmp_path/".github/instructions/api.instructions.md"; scoped.write_text("manual")
    with pytest.raises(ProcessError,match="generated-file drift"): validate_repository(tmp_path)

def test_capability_status_is_prominent_and_terms_complete():
    readme=Path("README.md").read_text(); status=Path("docs/capability-status.md").read_text()
    assert "capability status" in readme.lower()
    for term in ("implemented","partial","experimental","designed","deferred"): assert f"**{term}**" in status
    assert "Current process release: **1.4.0**" in status

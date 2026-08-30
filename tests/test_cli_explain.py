from argparse import Namespace

from engineering_process import cli
from engineering_process.classification import classify
from engineering_process.paths import policy_root
from conftest import profile


def test_explain_reports_validation_categories_and_execution_controls(tmp_path, manifest, monkeypatch):
    result = classify(policy_root(), profile("generic"), manifest, declared={"observable_behavior": True})
    monkeypatch.setattr(cli, "_manifest", lambda root: manifest)
    monkeypatch.setattr(cli, "_classification", lambda args, root, loaded: result)
    explained = cli.run(Namespace(root=str(tmp_path), command="explain"))
    assert explained["required_validation_categories"] == ["focused", "integration"]
    assert explained["agent_execution"]["sandbox_required"]
    assert explained["agent_execution"]["production_credentials_prohibited"]

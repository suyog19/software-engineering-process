from pathlib import Path

import pytest

from engineering_process.io import load_yaml
from engineering_process.paths import policy_root
from engineering_process.policy import load_policy

REV = "a" * 40
SHA = "b" * 40


@pytest.fixture
def manifest():
    return {"schema_version": 1, "process": {"source": "suyog19/software-engineering-process", "version": "1.3.0", "revision": REV, "profile": "generic"}, "repository": {"name": "example/repo", "trusted_ci_workflows": [".github/workflows/assurance.yml"], "authorized_review_workflows": [".github/workflows/assurance.yml"]}, "overrides": {"agent_execution": {"sandbox": "ephemeral-vm", "network_enforcement": "firewall", "audit_sink": "test-audit"}}}


def profile(name):
    return load_policy(policy_root(), name)[1]

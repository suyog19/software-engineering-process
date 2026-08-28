from pathlib import Path

import pytest

from engineering_process.io import load_yaml
from engineering_process.paths import policy_root
from engineering_process.policy import load_policy

REV = "a" * 40
SHA = "b" * 40


@pytest.fixture
def manifest():
    return {"schema_version": 1, "process": {"source": "suyog19/software-engineering-process", "version": "1.0.1", "revision": REV, "profile": "generic"}, "repository": {"name": "example/repo"}, "overrides": {}}


def profile(name):
    return load_policy(policy_root(), name)[1]

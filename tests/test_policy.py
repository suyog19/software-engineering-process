import pytest

from engineering_process.errors import ProcessError
from engineering_process.paths import policy_root
from engineering_process.policy import load_policy, validate_overrides


def core(): return load_policy(policy_root(), "generic")[0]


def test_cannot_weaken_independent_review(manifest):
    manifest["overrides"] = {"controls": {"independent_review": {"fresh_context_required": False}}}
    with pytest.raises(ProcessError, match="locked control"):
        validate_overrides(core(), manifest)


def test_cannot_disable_locked_control(manifest):
    manifest["overrides"] = {"controls": {"protected_fail_closed": False}}
    with pytest.raises(ProcessError, match="locked control"):
        validate_overrides(core(), manifest)


def test_extensible_may_strengthen(manifest):
    base = core()["controls"]["protected_characteristics"]["values"]
    manifest["overrides"] = {"controls": {"protected_characteristics": {"values": base + ["extra"]}}}
    validate_overrides(core(), manifest)


def test_extensible_may_not_remove(manifest):
    manifest["overrides"] = {"controls": {"protected_characteristics": {"values": []}}}
    with pytest.raises(ProcessError, match="cannot remove"):
        validate_overrides(core(), manifest)


def test_unknown_profile_fails():
    with pytest.raises(ProcessError, match="unknown profile"):
        load_policy(policy_root(), "python")


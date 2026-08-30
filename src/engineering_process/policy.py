from __future__ import annotations

from copy import deepcopy
from pathlib import Path

from .errors import ProcessError
from .io import load_yaml


def load_policy(root: Path, profile_name: str) -> tuple[dict, dict, dict]:
    core = load_yaml(root / "core.yaml")
    profile_path = root / "profiles" / f"{profile_name}.yaml"
    if not profile_path.exists():
        raise ProcessError(f"unknown profile: {profile_name}")
    profile = load_yaml(profile_path)
    delivery = load_yaml(root / "classification" / "delivery-profiles.yaml")
    return core, profile, delivery


def validate_overrides(core: dict, manifest: dict) -> None:
    overrides = manifest.get("overrides", {})
    control_overrides = overrides.get("controls", {})
    known = core["controls"]
    for key, candidate in control_overrides.items():
        if key not in known:
            raise ProcessError(f"unknown control override: {key}")
        base = known[key]
        semantics = base["semantics"]
        if semantics == "locked":
            if isinstance(candidate, dict):
                for field, value in candidate.items():
                    if field not in base:
                        raise ProcessError(f"unknown locked control field: {key}.{field}")
                    if value != base[field]:
                        raise ProcessError(f"locked control cannot be changed: {key}.{field}")
            elif candidate != base.get("enabled"):
                raise ProcessError(f"locked control cannot be weakened: {key}")
        elif semantics == "extensible":
            base_values = set(base.get("values", []))
            candidate_values = set(candidate.get("values", candidate) if isinstance(candidate, (dict, list)) else [])
            if not base_values.issubset(candidate_values):
                raise ProcessError(f"extensible control cannot remove inherited values: {key}")


def effective_controls(core: dict, profile: dict, manifest: dict) -> dict:
    validate_overrides(core, manifest)
    result = deepcopy(core["controls"])
    for key, candidate in manifest.get("overrides", {}).get("controls", {}).items():
        result[key].update(candidate if isinstance(candidate, dict) else {"enabled": candidate})
    validation = manifest.get("overrides", {}).get("validation", {}).get("commands")
    if validation is not None:
        result["validation_commands"]["values"] = validation
    return result

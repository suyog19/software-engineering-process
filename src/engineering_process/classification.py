from __future__ import annotations

import fnmatch
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Iterable

from .errors import ProcessError
from .io import load_yaml


@dataclass(frozen=True)
class Signal:
    source: str
    value: str
    characteristic: str
    matched_rule: str


@dataclass
class Classification:
    target_revision: str
    base_revision: str
    delivery_profile: str
    characteristics: dict[str, bool | None]
    deterministic_signals: list[dict]
    semantic_rationale: str
    reasons: list[str]
    protected_ambiguity: bool = False
    change_set: list[dict] | None = None
    input_trust: str = "untrusted-manual"
    path_explanations: list[dict] | None = None
    dependency_signals: list[dict] | None = None

    def to_dict(self) -> dict:
        return asdict(self)


def _matches(path: str, pattern: str) -> bool:
    return fnmatch.fnmatch(path, pattern) or fnmatch.fnmatch(path, pattern.replace("**/", ""))


def classify(
    policy_root: Path,
    profile: dict,
    manifest: dict,
    changed_paths: Iterable[str] = (),
    declared: dict[str, bool | None] | None = None,
    semantic: dict[str, bool | None] | None = None,
    semantic_rationale: str = "",
    target_revision: str = "",
    base_revision: str = "",
    change_set: list[dict] | None = None,
    input_trust: str = "untrusted-manual",
    derived: dict[str, bool | None] | None = None,
    derived_signals: list[dict] | None = None,
) -> Classification:
    cfg = load_yaml(policy_root / "classification" / "characteristics.yaml")
    changed_paths = list(changed_paths)
    declared, semantic = declared or {}, semantic or {}
    characteristics: dict[str, bool | None] = {**declared, **semantic, **(derived or {})}
    rules = list(cfg["deterministic_files"])
    for pattern in profile.get("add", {}).get("protected_path_hints", []):
        rules.append({"pattern": pattern, "characteristic": "profile_protected_path"})
    for pattern in manifest.get("overrides", {}).get("classification", {}).get("protected_path_hints", []):
        rules.append({"pattern": pattern, "characteristic": "repository_protected_path"})

    signals: list[Signal] = []
    for path in changed_paths:
        for rule in rules:
            if _matches(path, rule["pattern"]):
                characteristics[rule["characteristic"]] = True
                signals.append(Signal("changed_path", path, rule["characteristic"], rule["pattern"]))

    protected = set(cfg["protected"])
    protected.update(profile.get("add", {}).get("protected_characteristics", []))
    protected.update(manifest.get("overrides", {}).get("classification", {}).get("additional_protected_characteristics", []))
    protected.update({"profile_protected_path", "repository_protected_path"})
    unresolved = sorted(k for k, v in characteristics.items() if k in protected and v is None)
    protected_true = sorted(k for k, v in characteristics.items() if k in protected and v is True)
    standard_true = sorted(k for k, v in characteristics.items() if k in set(cfg["standard"]) and v is True)
    explicit_profile = declared.get("requested_delivery_profile")

    reasons: list[str] = []
    if protected_true:
        delivery = "Protected"
        reasons.append("Protected characteristic present: " + ", ".join(protected_true))
    elif unresolved:
        delivery = "Protected"
        reasons.append("Protected characteristic unresolved; failed closed: " + ", ".join(unresolved))
    elif standard_true:
        delivery = "Standard"
        reasons.append("Standard characteristic present: " + ", ".join(standard_true))
    else:
        delivery = "Lean"
        reasons.append("No Standard or Protected characteristic was established")

    ranks = {"Lean": 0, "Standard": 1, "Protected": 2}
    if explicit_profile in ranks and ranks[explicit_profile] > ranks[delivery]:
        delivery = explicit_profile
        reasons.append(f"Declared intent strengthened classification to {delivery}")
    if explicit_profile in ranks and ranks[explicit_profile] < ranks[delivery]:
        reasons.append(f"Ignored requested downgrade to {explicit_profile}; classification is monotonic")
    if any(s.characteristic in protected for s in signals) and delivery != "Protected":
        raise ProcessError("internal classification integrity failure: Protected signal was downgraded")
    explanations = []
    for path in changed_paths:
        matched = sorted({signal.characteristic for signal in signals if signal.value == path})
        explanations.append({"path": path, "deterministic_characteristics": matched,
                             "effect": "matched deterministic rule(s)" if matched else "no deterministic rule matched"})
    return Classification(target_revision, base_revision, delivery, characteristics, [asdict(s) for s in signals], semantic_rationale, reasons, bool(unresolved), change_set or [], input_trust, explanations, derived_signals or [])

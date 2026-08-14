from __future__ import annotations

from pathlib import Path


def data_root() -> Path:
    checkout = Path(__file__).resolve().parents[2]
    return checkout if (checkout / "policy" / "core.yaml").exists() else Path(__file__).resolve().parent / "_data"


def policy_root() -> Path:
    return data_root() / "policy"


def schemas_root() -> Path:
    return data_root() / "schemas"


def skills_root() -> Path:
    return data_root() / "skills"


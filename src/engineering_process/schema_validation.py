from __future__ import annotations

import re


def validate(value, schema, path="$") -> list[str]:
    """Small Draft-2020-12 subset used by bundled contracts; schemas remain authoritative."""
    errors: list[str] = []
    expected = schema.get("type")
    types = expected if isinstance(expected, list) else [expected] if expected else []
    type_map = {"object": dict, "array": list, "string": str, "integer": int, "boolean": bool, "null": type(None)}
    if types and not any(isinstance(value, type_map[t]) for t in types):
        return [f"{path}: expected {' or '.join(types)}"]
    if "const" in schema and value != schema["const"]: errors.append(f"{path}: must equal {schema['const']!r}")
    if "enum" in schema and value not in schema["enum"]: errors.append(f"{path}: must be one of {schema['enum']}")
    if isinstance(value, str):
        if "pattern" in schema and not re.search(schema["pattern"], value): errors.append(f"{path}: does not match {schema['pattern']}")
        if len(value) < schema.get("minLength", 0): errors.append(f"{path}: too short")
    if isinstance(value, list):
        if len(value) < schema.get("minItems", 0): errors.append(f"{path}: too few items")
        if "maxItems" in schema and len(value) > schema["maxItems"]: errors.append(f"{path}: too many items")
        if schema.get("uniqueItems") and len({repr(v) for v in value}) != len(value): errors.append(f"{path}: items must be unique")
        for i, item in enumerate(value): errors.extend(validate(item, schema.get("items", {}), f"{path}[{i}]"))
    if isinstance(value, dict):
        for key in schema.get("required", []):
            if key not in value: errors.append(f"{path}: missing {key}")
        props = schema.get("properties", {})
        additional = schema.get("additionalProperties", True)
        for key, item in value.items():
            if key in props: errors.extend(validate(item, props[key], f"{path}.{key}"))
            elif isinstance(additional, dict): errors.extend(validate(item, additional, f"{path}.{key}"))
            elif additional is False: errors.append(f"{path}: unexpected property {key}")
    return errors


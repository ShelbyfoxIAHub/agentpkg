"""Manifest JSON Schemas, a small dependency-free validator, and migration."""

import json
import re
from pathlib import Path

SCHEMA_DIR = Path(__file__).resolve().parent / "schemas"
SUPPORTED_SPEC_VERSIONS = ("1.0", "1.1")
LATEST_SPEC_VERSION = SUPPORTED_SPEC_VERSIONS[-1]
_cache = {}


def parse_spec_version(value: str) -> tuple:
    match = re.fullmatch(r"([0-9]+)\.([0-9]+)", value or "")
    if not match:
        raise ValueError("Invalid spec_version: {!r}".format(value))
    return int(match.group(1)), int(match.group(2))


def schema_version_for(spec_version: str) -> str:
    """Pick the schema used for a spec_version.

    Known versions use their own schema. Unknown minor versions of major 1 are
    validated with the newest known schema (schemas allow extra properties).
    Other major versions are rejected.
    """
    major, _ = parse_spec_version(spec_version)
    if major != 1:
        raise ValueError(
            "Unsupported spec_version {} (this agentpkg supports {})".format(
                spec_version, ", ".join(SUPPORTED_SPEC_VERSIONS)
            )
        )
    if spec_version in SUPPORTED_SPEC_VERSIONS:
        return spec_version
    return LATEST_SPEC_VERSION


def load_schema(version: str) -> dict:
    if version not in SUPPORTED_SPEC_VERSIONS:
        raise ValueError("No schema for spec_version {}".format(version))
    if version not in _cache:
        path = SCHEMA_DIR / "manifest-{}.schema.json".format(version)
        _cache[version] = json.loads(path.read_text(encoding="utf-8"))
    return _cache[version]


_TYPES = {
    "object": lambda v: isinstance(v, dict),
    "array": lambda v: isinstance(v, list),
    "string": lambda v: isinstance(v, str),
    "boolean": lambda v: isinstance(v, bool),
    "integer": lambda v: isinstance(v, int) and not isinstance(v, bool),
    "number": lambda v: isinstance(v, (int, float)) and not isinstance(v, bool),
    "null": lambda v: v is None,
}


def _resolve(ref: str, root: dict) -> dict:
    if not ref.startswith("#/"):
        raise ValueError("Unsupported $ref: {}".format(ref))
    node = root
    for part in ref[2:].split("/"):
        node = node[part]
    return node


def _check(value, schema: dict, path: str, root: dict) -> None:
    if "$ref" in schema:
        _check(value, _resolve(schema["$ref"], root), path, root)
        return
    expected = schema.get("type")
    if expected is not None:
        names = expected if isinstance(expected, list) else [expected]
        if not any(_TYPES[name](value) for name in names):
            raise ValueError("{}: expected {}".format(path, " or ".join(names)))
    if "enum" in schema and value not in schema["enum"]:
        raise ValueError(
            "{}: must be one of {}".format(path, ", ".join(map(str, schema["enum"])))
        )
    if isinstance(value, str):
        if "minLength" in schema and len(value) < schema["minLength"]:
            raise ValueError("{}: shorter than {}".format(path, schema["minLength"]))
        if "maxLength" in schema and len(value) > schema["maxLength"]:
            raise ValueError("{}: longer than {}".format(path, schema["maxLength"]))
        if "pattern" in schema and not re.search(schema["pattern"], value):
            raise ValueError("{}: contains disallowed characters or format".format(path))
    if _TYPES["number"](value):
        if "minimum" in schema and value < schema["minimum"]:
            raise ValueError("{}: must be >= {}".format(path, schema["minimum"]))
    if isinstance(value, list):
        if "maxItems" in schema and len(value) > schema["maxItems"]:
            raise ValueError("{}: more than {} items".format(path, schema["maxItems"]))
        if "items" in schema:
            for index, item in enumerate(value):
                _check(item, schema["items"], "{}[{}]".format(path, index), root)
    if isinstance(value, dict):
        for key in schema.get("required", []):
            if key not in value:
                raise ValueError("{}: missing required property '{}'".format(path, key))
        for key, subschema in schema.get("properties", {}).items():
            if key in value:
                _check(value[key], subschema, "{}.{}".format(path, key), root)


def validate_manifest(manifest: dict) -> str:
    """Validate a manifest against its schema; return the spec_version used."""
    if not isinstance(manifest, dict):
        raise ValueError("manifest.json must contain a JSON object")
    spec_version = manifest.get("spec_version")
    if not isinstance(spec_version, str):
        raise ValueError("manifest.json is missing a valid spec_version")
    try:
        version = schema_version_for(spec_version)
        schema = load_schema(version)
        _check(manifest, schema, "$", schema)
    except ValueError as error:
        raise ValueError("Invalid manifest: {}".format(error)) from error
    return version


def migrate_manifest(manifest: dict) -> dict:
    """Return an in-memory spec 1.1 view of a 1.0 manifest (no hashes)."""
    migrated = dict(manifest)
    migrated["spec_version"] = LATEST_SPEC_VERSION
    migrated["entry_points"] = [
        {"path": item, "role": "data"} if isinstance(item, str) else item
        for item in manifest.get("entry_points", [])
    ]
    migrated.setdefault("files", [])
    migrated.setdefault("capabilities", [])
    migrated.setdefault("dependencies", [])
    return migrated

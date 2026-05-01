from __future__ import annotations
import json
import re
from pathlib import Path
import yaml
import jsonschema
_SCHEMA_PATH = Path(__file__).parent / "schemas" / "finding-schema.json"


def validate_finding(yaml_str: str) -> dict:
    # Orchestrator calls this before routing any finding — malformed output from an agent
    # must be caught here, not silently passed downstream where it causes a harder-to-debug failure.
    match = re.search(r"```yaml\n(.*?)```", yaml_str, re.DOTALL)
    if not match:
        raise ValueError("No YAML block found in finding comment")
    raw_yaml = match.group(1)
    parsed = yaml.safe_load(raw_yaml)

    schema = json.loads(_SCHEMA_PATH.read_text())
    jsonschema.validate(instance=parsed, schema=schema)

    return parsed

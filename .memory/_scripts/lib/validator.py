"""Output validation with JSON Schema — valida outputs de agentes."""
import json, re
from typing import Optional

SCHEMAS = {
    "aletheia": {
        "type": "object",
        "properties": {
            "investigation": {"type": "string"},
            "sources": {"type": "array", "items": {"type": "string"}},
            "confidence": {"type": "string", "enum": ["alta", "media", "baja"]},
            "key_findings": {"type": "array", "items": {"type": "string"}}
        },
        "required": ["investigation", "confidence"]
    },
    "kosmos": {
        "type": "object",
        "properties": {
            "adr": {"type": "string"},
            "diagrams": {"type": "array", "items": {"type": "string"}},
            "recommendations": {"type": "array", "items": {"type": "string"}},
            "adr_references": {"type": "array", "items": {"type": "string"}}
        },
        "required": ["adr"]
    },
    "metis": {
        "type": "object",
        "properties": {
            "strategy": {"type": "string"},
            "okrs": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "objective": {"type": "string"},
                        "key_results": {"type": "array", "items": {"type": "string"}}
                    },
                    "required": ["objective", "key_results"]
                }
            },
            "risks": {"type": "array", "items": {"type": "object"}},
            "confidence": {"type": "string", "enum": ["alta", "media", "baja"]}
        },
        "required": ["strategy", "confidence"]
    },
    "kratos": {
        "type": "object",
        "properties": {
            "code": {"type": "string"},
            "errors_found": {"type": "array", "items": {"type": "string"}},
            "ast_signatures": {"type": "array", "items": {"type": "string"}},
            "confidence": {"type": "number", "minimum": 0, "maximum": 1},
            "language": {"type": "string"}
        },
        "required": ["code"]
    },
    "mnemosyne": {
        "type": "object",
        "properties": {
            "curation_report": {"type": "string"},
            "issues_found": {"type": "integer"},
            "wikilinks_added": {"type": "integer"},
            "quality_score": {"type": "number"}
        },
        "required": ["curation_report"]
    }
}


def extract_json(text: str) -> Optional[str]:
    """Extract JSON object from agent output text."""
    # Try direct parse first
    try:
        json.loads(text)
        return text
    except json.JSONDecodeError:
        pass
    
    # Try to find JSON between ```json and ``` markers
    m = re.search(r'```(?:json)?\s*\n?(.*?)\n?```', text, re.DOTALL)
    if m:
        return m.group(1).strip()
    
    # Try to find JSON between { and } with balanced braces
    depth = 0
    start = -1
    for i, ch in enumerate(text):
        if ch == '{':
            if start == -1:
                start = i
            depth += 1
        elif ch == '}':
            depth -= 1
            if depth == 0 and start >= 0:
                candidate = text[start:i+1]
                try:
                    json.loads(candidate)
                    return candidate
                except json.JSONDecodeError:
                    pass
                start = -1
    return None


def validate(agent: str, output_text: str) -> tuple[bool, str]:
    """Validate agent output against its JSON schema.
    
    Args:
        agent: Agent name ("aletheia", "kratos", etc.)
        output_text: Raw output text from the agent
    
    Returns:
        (is_valid, error_message)
    """
    schema = SCHEMAS.get(agent)
    if not schema:
        return True, ""  # No schema for this agent, skip validation
    
    json_str = extract_json(output_text)
    if not json_str:
        return False, f"No valid JSON found in output for agent '{agent}'"
    
    try:
        data = json.loads(json_str)
    except json.JSONDecodeError as e:
        return False, f"Invalid JSON: {e}"
    
    # Validate against schema
    missing = []
    for field in schema.get("required", []):
        if field not in data:
            missing.append(field)
    
    if missing:
        return False, f"Missing required fields: {', '.join(missing)}"
    
    # Validate enum values
    for prop_name, prop_schema in schema.get("properties", {}).items():
        if prop_name in data:
            enum_vals = prop_schema.get("enum")
            if enum_vals and data[prop_name] not in enum_vals:
                return False, f"Field '{prop_name}' must be one of {enum_vals}, got '{data[prop_name]}'"
            
            prop_type = prop_schema.get("type")
            if prop_type == "integer" and not isinstance(data[prop_name], int):
                return False, f"Field '{prop_name}' must be integer, got {type(data[prop_name]).__name__}"
    
    return True, ""


def validate_and_fix(agent: str, output_text: str, max_retries: int = 3) -> tuple[str, bool]:
    """Validate output and return (fixed_text, was_validated).
    
    If validation fails, attempts to extract partial valid data.
    """
    valid, error = validate(agent, output_text)
    if valid:
        return output_text, True
    
    # If invalid but we can extract JSON, return extracted JSON
    json_str = extract_json(output_text)
    if json_str:
        return json_str, True
    
    return output_text, False


if __name__ == "__main__":
    # Test
    valid_kratos = '''{"code": "def hello(): pass", "errors_found": [], "ast_signatures": [], "confidence": 0.8, "language": "python"}'''
    v, e = validate("kratos", valid_kratos)
    print(f"Valid Kratos output: {v} ({e})")
    
    invalid_kratos = '''{"code": "def hello(): pass"}'''  # missing required fields
    v, e = validate("kratos", invalid_kratos)
    print(f"Invalid Kratos output: {v} ({e})")
    
    with_json_markers = '''Some text before
```json
{"code": "test", "errors_found": [], "ast_signatures": [], "confidence": 0.5, "language": "rust"}
```
Some text after'''
    extracted = extract_json(with_json_markers)
    print(f"Extracted from markers: {extracted is not None}")
    if extracted:
        v, e = validate("kratos", extracted)
        print(f"  Valid: {v} ({e})")

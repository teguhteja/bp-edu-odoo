# Part of the EH AI Suite by ERP Heritage.
"""Minimal validation of LLM-supplied tool arguments against a JSON schema.

The engine never trusts the arguments a model fills in for a tool. This module
performs a lightweight check (presence of required keys, primitive types and
enums) before the tool runs. It is intentionally conservative: anything it
cannot verify is left to the tool itself.
"""

_PRIMITIVE_CHECKS = {
    "string": lambda value: isinstance(value, str),
    "integer": lambda value: isinstance(value, int) and not isinstance(value, bool),
    "number": lambda value: isinstance(value, (int, float)) and not isinstance(value, bool),
    "boolean": lambda value: isinstance(value, bool),
    "array": lambda value: isinstance(value, list),
    "object": lambda value: isinstance(value, dict),
}


def validate_arguments(schema, arguments):
    """Return ``(ok, error_message)`` for ``arguments`` against ``schema``.

    ``schema`` is a JSON schema object. Only the subset the engine relies on is
    enforced: ``type``, ``required`` and ``enum`` at the top level of an object.
    """
    if not schema:
        return True, None
    if not isinstance(arguments, dict):
        return False, "Arguments must be an object."

    properties = schema.get("properties") or {}
    required = schema.get("required") or []

    for name in required:
        if name not in arguments:
            return False, "Missing required argument '%s'." % name

    for name, value in arguments.items():
        spec = properties.get(name)
        if not spec:
            continue
        expected = spec.get("type")
        if expected:
            types = expected if isinstance(expected, list) else [expected]
            checks = [_PRIMITIVE_CHECKS.get(t) for t in types if t and t != "null"]
            allow_null = "null" in types
            if value is None:
                if not allow_null:
                    return False, "Argument '%s' may not be null." % name
            elif checks and not any(check(value) for check in checks if check):
                return False, "Argument '%s' must be of type %s." % (name, expected)
        enum = spec.get("enum")
        if enum is not None and value not in enum:
            return False, "Argument '%s' must be one of %s." % (name, enum)

    return True, None

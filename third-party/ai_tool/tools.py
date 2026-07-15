def attrsetter(attr, value):
    """Return a decorator that sets `attr` = `value` on the decorated function
    and returns it unchanged.

    Removed from odoo.api in 19.0; reimplemented here since it was only ever
    a small attribute-setting helper, not something tied to ORM internals.
    """
    def decorate(func):
        setattr(func, attr, value)
        return func
    return decorate


def aitool(input_schema: dict, output_schema: dict, required_inputs: list = None):
    return attrsetter(
        "_ai_tool",
        {
            "input_schema": {
                "type": "object",
                "properties": input_schema,
                "required": required_inputs or [],
            },
            "output_schema": {
                "type": "object",
                "properties": output_schema,
            },
        },
    )

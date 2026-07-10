# Part of the EH AI Suite by ERP Heritage.
"""Turn server actions into AI tools.

An administrator flags a server action with ``eh_ai_use_in_tool`` and gives it a
description and a JSON parameter schema. The engine then exposes it to a model
as a callable function. Execution happens in a controlled context: the model's
arguments are validated, the action code runs, and whatever it places in the
``result`` dictionary is returned to the model as text.
"""
import json
import logging

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError
from odoo.tools import safe_eval as safe_eval_module
from odoo.tools.safe_eval import safe_eval

_logger = logging.getLogger(__name__)


class IrActionsServer(models.Model):
    _inherit = "ir.actions.server"

    eh_ai_use_in_tool = fields.Boolean(
        string="Available to AI Agents",
        help="Expose this server action to AI agents as a callable tool.",
    )
    eh_ai_tool_name = fields.Char(
        string="Tool Name",
        help="Identifier the model uses to call this tool. Lowercase, no spaces. "
             "Defaults to a slug of the action name.",
    )
    eh_ai_tool_description = fields.Char(
        string="Tool Description",
        help="Tells the model when and why to call this tool.",
    )
    eh_ai_tool_schema = fields.Text(
        string="Tool Parameters (JSON Schema)",
        help="JSON schema object describing the arguments the model must supply.",
    )

    @api.constrains("eh_ai_use_in_tool", "eh_ai_tool_schema")
    def _check_eh_ai_tool_schema(self):
        for action in self:
            if not action.eh_ai_use_in_tool or not action.eh_ai_tool_schema:
                continue
            try:
                schema = json.loads(action.eh_ai_tool_schema)
            except ValueError as error:
                raise ValidationError(_("Tool parameters must be valid JSON: %s", error))
            if not isinstance(schema, dict) or schema.get("type") != "object":
                raise ValidationError(_("Tool parameters must be a JSON object schema "
                                        "(\"type\": \"object\")."))

    def _eh_ai_resolve_tool_name(self):
        self.ensure_one()
        if self.eh_ai_tool_name:
            return self.eh_ai_tool_name
        slug = "".join(c.lower() if c.isalnum() else "_" for c in (self.name or "tool"))
        slug = "_".join(part for part in slug.split("_") if part)
        return slug or ("action_%s" % self.id)

    def _eh_ai_tool_definition(self):
        self.ensure_one()
        schema = {"type": "object", "properties": {}}
        if self.eh_ai_tool_schema:
            try:
                schema = json.loads(self.eh_ai_tool_schema)
            except ValueError:
                pass
        return {
            "name": self._eh_ai_resolve_tool_name(),
            "description": self.eh_ai_tool_description or self.name or "",
            "parameters": schema,
        }

    def _eh_ai_run_tool(self, arguments):
        """Execute the action with model-supplied arguments.

        Returns ``(output, error)``. Errors are returned to the model as text
        rather than raised, so an agent can recover or report them.
        """
        self.ensure_one()
        # The action's own configuration (state, code, target model) is read
        # with elevated rights because regular users have no access to
        # ir.actions.server; the code itself still executes in the requesting
        # user's environment (eval_context["env"] = self.env) so record rules
        # apply to whatever data the tool touches.
        config = self.sudo()
        if config.state != "code":
            return None, "This tool type is not executable."
        model_name = config.model_id.model if config.model_id else None

        eval_context = {
            "env": self.env,
            "model": self.env[model_name] if model_name else None,
            "arguments": dict(arguments or {}),
            "result": {},
            "log": _logger.info,
            # safe_eval rejects raw modules, so expose a wrapped json.
            "json": safe_eval_module.wrap_module(json, ["dumps", "loads"]),
            "datetime": safe_eval_module.datetime,
            "time": safe_eval_module.time,
        }
        try:
            # safe_eval mutates the context dict in place with any names the
            # code creates, so the tool reads its output back from `result`.
            safe_eval((config.code or "").strip(), eval_context, mode="exec")
        except Exception as exception:  # noqa: BLE001 - surfaced back to the model
            _logger.exception("EH AI tool '%s' failed", self.name)
            return None, str(exception)

        result = eval_context.get("result") or {}
        return result.get("output"), result.get("error")

    @api.model
    def _eh_ai_build_tool_map(self, actions):
        """Build the orchestrator tool map for a set of flagged server actions.

        The tool *definition* (name, description, schema) is read with elevated
        rights, but the tool *body* runs as the requesting user so record rules
        and field-level access still apply. A tool that genuinely needs elevated
        access must opt in with an explicit ``.sudo()`` inside its own code.
        """
        tool_map = {}
        for action in actions:
            if not action.sudo().eh_ai_use_in_tool:
                continue
            definition = action.sudo()._eh_ai_tool_definition()
            tool_map[definition["name"]] = {
                "definition": definition,
                "run": (lambda act: (lambda args: act._eh_ai_run_tool(args)))(action),
            }
        return tool_map

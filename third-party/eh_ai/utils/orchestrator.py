# Part of the EH AI Suite by ERP Heritage.
"""Provider-agnostic tool-calling loop.

The orchestrator drives a conversation: it asks the provider for a response,
executes any tools the model requests, feeds the results back, and repeats until
the model stops calling tools or a safety limit is reached. It knows nothing
about a specific vendor; that lives entirely in the provider adapters.
"""
import logging

from .tool_schema import validate_arguments

_logger = logging.getLogger(__name__)


class Orchestrator:

    def __init__(self, env, provider, model_name, tool_map=None,
                 max_successive_calls=10, max_tool_calls_per_call=10):
        self.env = env
        self.provider = provider
        self.model_name = model_name
        # tool_map: name -> {"definition": {...}, "run": callable(arguments) -> (output, error)}
        self.tool_map = tool_map or {}
        self.max_successive_calls = max_successive_calls
        self.max_tool_calls_per_call = max_tool_calls_per_call

    def run(self, system, messages, max_tokens=4096, temperature=None):
        """Run the loop and return ``{"text", "usage", "calls"}``."""
        tool_defs = [entry["definition"] for entry in self.tool_map.values()] or None
        responses = []
        total_usage = {"input_tokens": 0, "output_tokens": 0, "cached_tokens": 0}
        api_calls = 0

        conversation = list(messages)

        for _ in range(self.max_successive_calls):
            api_calls += 1
            result = self.provider.chat(
                self.model_name, system, conversation,
                tool_defs=tool_defs, max_tokens=max_tokens, temperature=temperature,
            )
            for key in total_usage:
                total_usage[key] += result.usage.get(key, 0)

            if result.text:
                responses.append(result.text)

            if not result.tool_calls:
                break

            conversation.append({
                "role": "assistant",
                # OpenAI requires content to be null (not "") when tool_calls
                # are present; keep the neutral message format consistent.
                "content": result.text or None,
                "tool_calls": result.tool_calls,
            })

            for index, call in enumerate(result.tool_calls):
                if index >= self.max_tool_calls_per_call:
                    conversation.append(self._tool_message(
                        call, "Error: tool-call limit reached for this step."))
                    continue
                output = self._execute_tool(call)
                conversation.append(self._tool_message(call, output))

        text = "\n".join(part for part in responses if part).strip()
        if not text and not responses:
            text = ""
        return {"text": text, "usage": total_usage, "calls": api_calls}

    # -- helpers -------------------------------------------------------------

    def _tool_message(self, call, output):
        return {
            "role": "tool",
            "tool_call_id": call.get("id"),
            "name": call.get("name"),
            "content": str(output),
        }

    def _execute_tool(self, call):
        name = call.get("name")
        entry = self.tool_map.get(name)
        if entry is None:
            _logger.warning("EH AI: model requested unknown tool '%s'", name)
            return "Error: unknown tool '%s'." % name

        arguments = call.get("arguments") or {}
        schema = (entry["definition"].get("parameters")) or {}
        ok, error = validate_arguments(schema, arguments)
        if not ok:
            return "Error: %s" % error

        try:
            output, run_error = entry["run"](arguments)
        except Exception as exception:  # noqa: BLE001 - errors are returned to the model
            _logger.exception("EH AI: tool '%s' raised", name)
            return "Error while running tool: %s" % exception
        if run_error:
            return "Error: %s" % run_error
        return output if output is not None else "Done."

# Part of the EH AI Suite by ERP Heritage.
from unittest.mock import patch

from odoo.tests import TransactionCase, tagged

from odoo.addons.eh_ai.utils.providers.openai_provider import OpenAICompatibleProvider
from odoo.addons.eh_ai.utils.tool_schema import validate_arguments

_POST_PATH = "odoo.addons.eh_ai.utils.providers.base.BaseProvider._post"


def _openai_tool_call(name, call_id="call_1", arguments="{}",
                      prompt_tokens=10, completion_tokens=5):
    return {
        "choices": [{
            "message": {
                "role": "assistant",
                "content": None,
                "tool_calls": [{
                    "id": call_id,
                    "type": "function",
                    "function": {"name": name, "arguments": arguments},
                }],
            },
            "finish_reason": "tool_calls",
        }],
        "usage": {"prompt_tokens": prompt_tokens, "completion_tokens": completion_tokens},
    }


def _openai_text(text, prompt_tokens=12, completion_tokens=6):
    return {
        "choices": [{
            "message": {"role": "assistant", "content": text},
            "finish_reason": "stop",
        }],
        "usage": {
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "prompt_tokens_details": {"cached_tokens": 0},
        },
    }


@tagged("post_install", "-at_install")
class TestEhAiEngine(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.model_gpt = cls.env.ref("eh_ai.model_gpt_4_1")
        cls.model_reasoning = cls.env.ref("eh_ai.model_gpt_5_4")
        cls.topic = cls.env.ref("eh_ai.topic_general_tools")
        cls.agent = cls.env["eh.ai.agent"].create({
            "name": "Test Agent",
            "chat_model_id": cls.model_gpt.id,
            "system_prompt": "You are a test agent.",
            "topic_ids": [(6, 0, [cls.topic.id])],
        })

    def test_odoo_data_search_tool(self):
        # The built-in Odoo Data tool returns records as JSON via the wrapped
        # json module exposed to the tool sandbox.
        action = self.env.ref("eh_ai.tool_search_records")
        output, error = action._eh_ai_run_tool(
            {"model": "res.partner", "fields": ["name"], "limit": 3})
        self.assertFalse(error)
        self.assertTrue(output and output.startswith("["))

    def test_base_grounding_in_system_prompt(self):
        # Every agent is grounded as an in-Odoo assistant by default.
        system = self.agent._build_system_prompt()
        self.assertIn("Odoo", system)
        self.assertIn("never ask the user to upload", system)

    def test_provider_error_handles_list_body(self):
        # Some providers (e.g. Gemini) return errors as a JSON list; the error
        # handler must surface a clean message, not raise AttributeError.
        from odoo.addons.eh_ai.utils.providers.base import BaseProvider
        provider = BaseProvider(self.env, self.env.ref("eh_ai.provider_openai"))

        class _Resp:
            text = "[]"

            def json(self):
                return [{"error": {"message": "rate limited"}}]

        class _Err(Exception):
            response = _Resp()

        message = provider._format_http_error(_Err())
        self.assertIn("rate limited", message)

    def test_tool_schema_validation(self):
        schema = {
            "type": "object",
            "properties": {
                "city": {"type": "string"},
                "limit": {"type": "integer"},
                "unit": {"type": "string", "enum": ["c", "f"]},
            },
            "required": ["city"],
        }
        ok, _ = validate_arguments(schema, {"city": "Sydney", "limit": 3, "unit": "c"})
        self.assertTrue(ok)
        ok, err = validate_arguments(schema, {"limit": 3})
        self.assertFalse(ok)
        self.assertIn("city", err)
        ok, err = validate_arguments(schema, {"city": "Sydney", "limit": "many"})
        self.assertFalse(ok)
        ok, err = validate_arguments(schema, {"city": "Sydney", "unit": "k"})
        self.assertFalse(ok)

    def test_openai_message_serialisation(self):
        provider = self.env.ref("eh_ai.provider_openai")
        adapter = OpenAICompatibleProvider(self.env, provider)
        messages = [
            {"role": "user", "content": "hi"},
            {"role": "assistant", "content": "",
             "tool_calls": [{"id": "c1", "name": "t", "arguments": {"a": 1}}]},
            {"role": "tool", "tool_call_id": "c1", "name": "t", "content": "42"},
        ]
        wire = adapter._to_wire_messages("sys", messages)
        self.assertEqual(wire[0]["role"], "system")
        self.assertEqual(wire[2]["tool_calls"][0]["function"]["name"], "t")
        self.assertEqual(wire[3]["role"], "tool")
        self.assertEqual(wire[3]["tool_call_id"], "c1")

    def test_temperature_gating(self):
        # Reasoning models reject sampling params; the agent must not send temperature.
        reasoning_agent = self.env["eh.ai.agent"].create({
            "name": "Reasoning Agent",
            "chat_model_id": self.model_reasoning.id,
        })
        self.assertIsNone(reasoning_agent._resolve_temperature())
        self.assertIsNotNone(self.agent._resolve_temperature())

    def test_tool_execution_returns_value(self):
        action = self.env.ref("eh_ai.tool_get_current_datetime")
        output, error = action._eh_ai_run_tool({})
        self.assertFalse(error)
        self.assertTrue(output, "tool should return a non-empty datetime string")

    def test_tool_calling_loop(self):
        first = _openai_tool_call("get_current_datetime")
        second = _openai_text("It is currently the test time.")
        with patch(_POST_PATH, side_effect=[first, second]) as mocked:
            result = self.agent.generate_response("What time is it?")

        self.assertEqual(mocked.call_count, 2)
        self.assertIn("test time", result["text"])
        self.assertEqual(result["usage"]["input_tokens"], 22)
        self.assertEqual(result["usage"]["output_tokens"], 11)
        self.assertEqual(result["calls"], 2)

        # The tool result must have been fed back as a tool message on the
        # second request's payload.
        second_messages = mocked.call_args_list[1].args[2]["messages"]
        roles = [m["role"] for m in second_messages]
        self.assertIn("assistant", roles)
        self.assertIn("tool", roles)
        tool_msg = next(m for m in second_messages if m["role"] == "tool")
        self.assertEqual(tool_msg["tool_call_id"], "call_1")

    def test_unknown_tool_is_reported_not_raised(self):
        first = _openai_tool_call("no_such_tool", call_id="x1")
        second = _openai_text("Sorry, I could not do that.")
        with patch(_POST_PATH, side_effect=[first, second]) as mocked:
            result = self.agent.generate_response("do the impossible")
        self.assertIn("could not", result["text"].lower())
        fed_back = mocked.call_args_list[1].args[2]["messages"]
        self.assertIn("unknown tool", str(fed_back))

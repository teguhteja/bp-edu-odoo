# Part of the EH AI Suite by ERP Heritage.
"""Adapter for the OpenAI Chat Completions wire format.

This single adapter serves OpenAI, Azure OpenAI, Ollama, Google (via its
OpenAI-compatible surface) and any other endpoint that implements
``POST {base_url}/chat/completions``. The only differences between them are the
base URL, the authentication header and the model catalogue, all of which live
on the provider configuration record.
"""
import json

from .base import BaseProvider, ProviderResult


class OpenAICompatibleProvider(BaseProvider):

    def _headers(self):
        headers = {"Content-Type": "application/json"}
        scheme = self.provider.auth_scheme
        if self.api_key:
            if scheme == "header_key":
                # Azure OpenAI expects the key on api-key rather than a bearer token.
                headers["api-key"] = self.api_key
            elif scheme != "none":
                headers["Authorization"] = "Bearer %s" % self.api_key
        headers.update(self.extra_headers)
        return headers

    def chat(self, model_name, system, messages, tool_defs=None,
             max_tokens=4096, temperature=None):
        payload = {
            "model": model_name,
            "messages": self._to_wire_messages(system, messages),
        }
        if max_tokens:
            payload["max_tokens"] = max_tokens
        if temperature is not None:
            payload["temperature"] = temperature
        if tool_defs:
            payload["tools"] = [
                {
                    "type": "function",
                    "function": {
                        "name": tool["name"],
                        "description": tool.get("description", ""),
                        "parameters": tool.get("parameters") or {"type": "object", "properties": {}},
                    },
                }
                for tool in tool_defs
            ]

        data = self._post("%s/chat/completions" % self.base_url, self._headers(), payload)
        return self._parse(data)

    def embed(self, model_name, inputs, dimensions=None):
        payload = {"model": model_name, "input": inputs}
        if dimensions:
            payload["dimensions"] = dimensions
        data = self._post("%s/embeddings" % self.base_url, self._headers(), payload)
        return [row["embedding"] for row in data.get("data", [])]

    # -- serialisation -------------------------------------------------------

    def _to_wire_messages(self, system, messages):
        wire = []
        if system:
            wire.append({"role": "system", "content": system})
        for message in messages:
            role = message["role"]
            if role == "tool":
                wire.append({
                    "role": "tool",
                    "tool_call_id": message["tool_call_id"],
                    "content": message.get("content", ""),
                })
            elif role == "assistant" and message.get("tool_calls"):
                wire.append({
                    "role": "assistant",
                    "content": message.get("content") or None,
                    "tool_calls": [
                        {
                            "id": call["id"],
                            "type": "function",
                            "function": {
                                "name": call["name"],
                                "arguments": json.dumps(call.get("arguments") or {}),
                            },
                        }
                        for call in message["tool_calls"]
                    ],
                })
            else:
                wire.append({"role": role, "content": message.get("content", "")})
        return wire

    def _parse(self, data):
        choices = data.get("choices") or []
        if not choices:
            return ProviderResult()
        choice = choices[0]
        message = choice.get("message") or {}

        tool_calls = []
        for call in message.get("tool_calls") or []:
            function = call.get("function") or {}
            try:
                arguments = json.loads(function.get("arguments") or "{}")
            except ValueError:
                arguments = {}
            tool_calls.append({
                "id": call.get("id"),
                "name": function.get("name", ""),
                "arguments": arguments,
            })

        usage_raw = data.get("usage") or {}
        usage = {
            "input_tokens": usage_raw.get("prompt_tokens", 0),
            "output_tokens": usage_raw.get("completion_tokens", 0),
            "cached_tokens": (usage_raw.get("prompt_tokens_details") or {}).get("cached_tokens", 0),
        }
        return ProviderResult(
            text=message.get("content") or "",
            tool_calls=tool_calls,
            usage=usage,
            stop_reason=choice.get("finish_reason") or "",
        )

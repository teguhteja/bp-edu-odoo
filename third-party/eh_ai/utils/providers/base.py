# Part of the EH AI Suite by ERP Heritage.
"""Provider abstraction for the EH AI engine.

Each adapter translates a neutral request (system prompt, a list of neutral
messages and a list of tool definitions) into a specific vendor's wire format,
performs the HTTP call, and returns a normalised :class:`ProviderResult`.

Neutral message shapes consumed by adapters:

* ``{"role": "user", "content": str}``
* ``{"role": "assistant", "content": str}``
* ``{"role": "assistant", "content": str, "tool_calls": [ToolCall, ...]}``
* ``{"role": "tool", "tool_call_id": str, "name": str, "content": str}``

A ``ToolCall`` is ``{"id": str, "name": str, "arguments": dict}``.

Tool definitions are ``{"name": str, "description": str, "parameters": dict}``
where ``parameters`` is a JSON schema object.
"""
import json
import logging

import requests

from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

DEFAULT_TIMEOUT = 120


class ProviderResult:
    """Normalised result of a single provider round trip."""

    __slots__ = ("text", "tool_calls", "usage", "stop_reason")

    def __init__(self, text="", tool_calls=None, usage=None, stop_reason=""):
        self.text = text or ""
        self.tool_calls = tool_calls or []
        self.usage = usage or {"input_tokens": 0, "output_tokens": 0, "cached_tokens": 0}
        self.stop_reason = stop_reason or ""


class BaseProvider:
    """Common HTTP plumbing shared by every adapter."""

    def __init__(self, env, provider_record):
        self.env = env
        self.provider = provider_record
        self.base_url = (provider_record.base_url or "").rstrip("/")
        self.api_key = provider_record._get_api_key()
        self.extra_headers = provider_record._get_extra_headers()

    # -- to be implemented per provider -------------------------------------

    def chat(self, model_name, system, messages, tool_defs=None,
             max_tokens=4096, temperature=None):
        raise NotImplementedError

    def embed(self, model_name, inputs, dimensions=None):
        raise NotImplementedError

    # -- shared helpers ------------------------------------------------------

    def _post(self, url, headers, payload, timeout=DEFAULT_TIMEOUT):
        try:
            response = requests.post(url, headers=headers, json=payload, timeout=timeout)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as error:
            raise UserError(self._format_http_error(error))

    def _format_http_error(self, error):
        message = repr(error)
        response = getattr(error, "response", None)
        if response is not None:
            try:
                body = response.json()
            except ValueError:
                body = None
            # Most providers nest the message under {"error": {...}}; some
            # (e.g. Gemini) return a JSON LIST of errors instead, so never
            # assume the body is a dict.
            detail = None
            if isinstance(body, dict):
                detail = body.get("error")
            elif isinstance(body, list) and body and isinstance(body[0], dict):
                detail = body[0].get("error") or body[0]
            if isinstance(detail, dict):
                message = detail.get("message") or json.dumps(detail)
            elif detail:
                message = str(detail)
            elif body is not None:
                message = json.dumps(body)
            elif response.text:
                message = response.text
        _logger.warning("EH AI provider request failed: %s", message)
        return self.env._("AI request failed: %s", message)

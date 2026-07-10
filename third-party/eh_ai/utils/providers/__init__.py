# Part of the EH AI Suite by ERP Heritage.
from .base import ProviderResult, BaseProvider
from .openai_provider import OpenAICompatibleProvider

# Map a provider code to the adapter class that speaks its wire format.
# OpenAI, Azure OpenAI, Ollama, Google (OpenAI-compatible surface) and any
# generic OpenAI-compatible endpoint all share the Chat Completions shape, so a
# single adapter serves them all.
#
# Additional provider families can be added by a separate add-on that registers
# its own adapter and provider code on top of this engine.
PROVIDER_REGISTRY = {
    "openai": OpenAICompatibleProvider,
    "azure_openai": OpenAICompatibleProvider,
    "ollama": OpenAICompatibleProvider,
    "google": OpenAICompatibleProvider,
    "openai_compatible": OpenAICompatibleProvider,
}


def build_provider(env, provider_record):
    """Instantiate the adapter for a provider configuration record."""
    code = provider_record.code
    cls = PROVIDER_REGISTRY.get(code)
    if cls is None:
        from odoo.exceptions import UserError
        raise UserError(env._("No adapter is registered for provider type '%s'.", code))
    return cls(env, provider_record)

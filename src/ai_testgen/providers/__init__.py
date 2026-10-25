"""Provider registry.

Providers are chosen by name in the config and can be overridden with the
``TESTGEN_PROVIDER`` environment variable.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from ai_testgen.providers.base import Completion, LLMProvider, ProviderError, estimate_tokens
from ai_testgen.providers.mock import MockProvider

__all__ = [
    "PROVIDERS",
    "Completion",
    "LLMProvider",
    "MockProvider",
    "ProviderError",
    "create_provider",
    "estimate_tokens",
]


def _openai(model: str | None, **options: Any) -> LLMProvider:
    from ai_testgen.providers.openai_provider import OpenAIProvider

    return OpenAIProvider(model, **options)


def _azure(model: str | None, **options: Any) -> LLMProvider:
    from ai_testgen.providers.openai_provider import AzureOpenAIProvider

    return AzureOpenAIProvider(model, **options)


def _bedrock(model: str | None, **options: Any) -> LLMProvider:
    from ai_testgen.providers.bedrock import BedrockProvider

    return BedrockProvider(model, **options)


def _mock(model: str | None, **options: Any) -> LLMProvider:
    return MockProvider(model or "mock-rules-v1", **options)


PROVIDERS: dict[str, Callable[..., LLMProvider]] = {
    "mock": _mock,
    "openai": _openai,
    "azure_openai": _azure,
    "bedrock": _bedrock,
}


def create_provider(name: str, model: str | None = None, **options: Any) -> LLMProvider:
    """Instantiate a provider by name."""
    try:
        factory = PROVIDERS[name]
    except KeyError:
        known = ", ".join(sorted(PROVIDERS))
        raise ProviderError(f"Unknown provider '{name}'. Known providers: {known}") from None
    return factory(model, **options)

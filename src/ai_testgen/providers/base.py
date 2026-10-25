"""Provider interface used by the generator."""

from __future__ import annotations

import math
from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass(frozen=True)
class Completion:
    """A single model response plus the usage data the generator reports."""

    text: str
    model: str
    input_tokens: int
    output_tokens: int
    latency_ms: float


class ProviderError(RuntimeError):
    """Raised when a provider is misconfigured or a call fails."""


class LLMProvider(ABC):
    """Minimal text-in, text-out interface.

    Keeping the surface this small is what makes providers swappable: the generator only
    ever calls ``complete`` and parses the JSON it gets back.
    """

    name: str = "base"

    def __init__(self, model: str) -> None:
        self.model = model

    @abstractmethod
    def complete(
        self,
        prompt: str,
        *,
        system: str | None = None,
        max_tokens: int = 4096,
        temperature: float = 0.0,
    ) -> Completion:
        """Return the model's completion for ``prompt``."""


def estimate_tokens(text: str) -> int:
    """Rough token count (~4 characters per token) for providers that do not report usage."""
    return max(1, math.ceil(len(text) / 4)) if text else 0

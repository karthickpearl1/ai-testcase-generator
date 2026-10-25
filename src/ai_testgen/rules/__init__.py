"""Deterministic test-design rules.

These encode classic test design techniques (equivalence partitioning, boundary value
analysis, negative and security testing) as code. The offline mock model uses them to answer
generation prompts, which gives a reproducible baseline to compare real LLM output against.
"""

from ai_testgen.rules.api import cases_for_endpoint
from ai_testgen.rules.story import cases_for_story

__all__ = ["cases_for_endpoint", "cases_for_story"]

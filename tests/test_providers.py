import json
from types import SimpleNamespace

import pytest

from ai_testgen.prompts import endpoint_prompt, parse_cases, story_prompt
from ai_testgen.providers import MockProvider, ProviderError, create_provider, estimate_tokens
from ai_testgen.providers.bedrock import BedrockProvider
from ai_testgen.providers.openai_provider import AzureOpenAIProvider, OpenAIProvider


@pytest.fixture
def order_prompt(endpoint_dicts):
    return endpoint_prompt(endpoint_dicts["POST /orders"])


def test_mock_answers_endpoint_prompts(order_prompt):
    completion = MockProvider().complete(order_prompt)
    cases = parse_cases(completion.text)
    assert cases
    assert all(c["request"]["path"] == "/orders" for c in cases)
    assert completion.output_tokens > 0


def test_mock_answers_story_prompts():
    story = {
        "id": "US-1",
        "title": "T",
        "narrative": "",
        "criteria": [{"id": "US-1/AC1", "text": "Name must be at most 5 characters"}],
    }
    cases = parse_cases(MockProvider().complete(story_prompt(story)).text)
    assert {c["traces"][0] for c in cases} == {"US-1/AC1"}


def test_mock_is_deterministic_including_degradation(order_prompt):
    provider = MockProvider(invalid_rate=0.5, duplicate_rate=0.5)
    assert provider.complete(order_prompt) == provider.complete(order_prompt)


def test_mock_degradation_knobs(order_prompt):
    clean = parse_cases(MockProvider().complete(order_prompt).text)
    noisy = parse_cases(
        MockProvider(invalid_rate=1.0, duplicate_rate=1.0).complete(order_prompt).text
    )
    assert len(noisy) == 2 * len(clean)
    broken = noisy[::2]
    assert all("expected" not in c or c["type"] == "smoke" for c in broken)

    weak = parse_cases(MockProvider(weak_assertions=True).complete(order_prompt).text)
    assert all(c["expect"] == {"status_in": [201, 400, 401, 404, 409]} for c in weak)


def test_mock_without_a_block_returns_no_cases():
    assert parse_cases(MockProvider().complete("hello").text) == []


def test_mock_rejects_invalid_rates():
    with pytest.raises(ValueError, match="duplicate_rate"):
        MockProvider(duplicate_rate=2)


@pytest.mark.parametrize(
    ("text", "message"),
    [
        ("no json", "no JSON"),
        ("{not json}", "not valid JSON"),
        ('{"cases": []}', "no 'test_cases'"),
    ],
)
def test_parse_cases_errors(text, message):
    with pytest.raises(ProviderError, match=message):
        parse_cases(text)


def test_parse_cases_tolerates_fences():
    assert parse_cases('```json\n{"test_cases": [{"a": 1}]}\n```') == [{"a": 1}]


def test_prompts_embed_payload():
    prompt = story_prompt({"id": "US-1"})
    assert '<story>\n{\n  "id": "US-1"\n}\n</story>' in prompt
    assert '"test_cases"' in prompt


def test_estimate_tokens():
    assert estimate_tokens("") == 0
    assert estimate_tokens("abcd" * 3) == 3


def test_create_provider():
    assert create_provider("mock").model == "mock-rules-v1"
    with pytest.raises(ProviderError, match="Unknown provider"):
        create_provider("nope")


class FakeChatClient:
    def __init__(self, error=None):
        self.calls = []
        self._error = error
        self.chat = SimpleNamespace(completions=SimpleNamespace(create=self._create))

    def _create(self, **kwargs):
        self.calls.append(kwargs)
        if self._error:
            raise self._error
        message = SimpleNamespace(content=json.dumps({"test_cases": []}))
        usage = SimpleNamespace(prompt_tokens=5, completion_tokens=7)
        return SimpleNamespace(choices=[SimpleNamespace(message=message)], usage=usage)


def test_openai_provider():
    client = FakeChatClient()
    completion = OpenAIProvider("gpt-test", client=client).complete("hi", system="sys")
    assert parse_cases(completion.text) == []
    assert (completion.input_tokens, completion.output_tokens) == (5, 7)
    assert client.calls[0]["messages"][0] == {"role": "system", "content": "sys"}
    with pytest.raises(ProviderError, match="boom"):
        OpenAIProvider("m", client=FakeChatClient(RuntimeError("boom"))).complete("hi")


def test_azure_provider(monkeypatch):
    monkeypatch.setenv("AZURE_OPENAI_DEPLOYMENT", "dep")
    assert create_provider("azure_openai", client=FakeChatClient()).model == "dep"
    monkeypatch.delenv("AZURE_OPENAI_DEPLOYMENT")
    with pytest.raises(ProviderError, match="AZURE_OPENAI_DEPLOYMENT"):
        AzureOpenAIProvider()


def test_openai_requires_key(monkeypatch):
    pytest.importorskip("openai")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    with pytest.raises(ProviderError, match="OPENAI_API_KEY"):
        create_provider("openai")


class FakeBedrock:
    def __init__(self, error=None):
        self.calls = []
        self._error = error

    def converse(self, **kwargs):
        self.calls.append(kwargs)
        if self._error:
            raise self._error
        return {
            "output": {"message": {"content": [{"text": '{"test_cases": []}'}]}},
            "usage": {"inputTokens": 3, "outputTokens": 4},
            "metrics": {"latencyMs": 120},
        }


def test_bedrock_provider():
    client = FakeBedrock()
    completion = create_provider("bedrock", "model-x", client=client).complete("hi", system="s")
    assert completion.latency_ms == 120.0
    assert client.calls[0]["system"] == [{"text": "s"}]
    with pytest.raises(ProviderError, match="denied"):
        BedrockProvider("m", client=FakeBedrock(RuntimeError("denied"))).complete("hi")

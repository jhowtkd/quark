"""Tests for LLMClient generation tracing integration."""

import pytest


class _FakeSpan:
    """Minimal fake Langfuse span matching the observation interface."""

    def __init__(self, name: str = "test", **initial_metadata):
        self.name = name
        self.initial_metadata = initial_metadata
        self.updates = []
        self._ended = False

    def update(self, **kwargs):
        self.updates.append(kwargs)
        return self

    def end(self):
        self._ended = True
        return None


class _FakeObservation:
    """Minimal fake root observation matching the LangfuseSpanWrapper interface."""

    def __init__(self):
        self.started_spans = []

    def start_span(self, name, **kwargs):
        span = _FakeSpan(name, **kwargs)
        self.started_spans.append((name, kwargs, span))
        return span


class _FakeOpenAIResponse:
    """Fake OpenAI completion response object."""

    def __init__(self, output: str = "hello world", usage: dict | None = None):
        self.output = output
        self.usage_data = usage or {"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15}

    @property
    def choices(self):
        class Choice:
            message = type("Msg", (), {"content": self.output})()
        return [Choice()]

    @property
    def usage(self):
        class Usage:
            prompt_tokens = self.usage_data["prompt_tokens"]
            completion_tokens = self.usage_data["completion_tokens"]
            total_tokens = self.usage_data["total_tokens"]
        return Usage()


class _FakeCompletions:
    """Fake completions endpoint."""

    def __init__(self, response):
        self.response = response

    def create(self, **kwargs):
        return self.response


class _FakeChat:
    """Fake chat endpoint."""

    def __init__(self, response):
        self.response = response

    @property
    def completions(self):
        return _FakeCompletions(self.response)


class _FakeOpenAIClient:
    """Minimal fake OpenAI client matching the SDK interface.

    Usage:
        fake = _FakeOpenAIClient(output="hello", usage={"prompt_tokens": 5, "completion_tokens": 3, "total_tokens": 8})
        client = OpenAI(...)  # real OpenAI instance
        client.chat.completions.create(...)  # real call

    But we need to replace client itself. So:
        fake = _FakeOpenAIClient(output="hello")
        llm.client = fake  # where llm uses fake.chat.completions.create(...)
    """

    def __init__(self, output: str = "hello world", usage: dict | None = None):
        self.response = _FakeOpenAIResponse(output=output, usage=usage)

    @property
    def chat(self):
        return _FakeChat(self.response)


class TestChatTracesGeneration:
    """Verify chat() and chat_json() emit traced spans when an observation is supplied."""

    def test_chat_with_observation_records_output_and_latency(self, monkeypatch):
        """When an observation is supplied, chat() records output and latency on the span."""
        fake_obs = _FakeObservation()
        fake_client = _FakeOpenAIClient(output="test response")

        from app.utils.llm_client import LLMClient

        llm = LLMClient(api_key="x", base_url="http://example", model="test-model")
        llm.client = fake_client

        result = llm.chat(
            messages=[{"role": "user", "content": "hi"}],
            observation=fake_obs,
            generation_name="my-generation",
        )

        assert result == "test response"
        assert len(fake_obs.started_spans) == 1
        name, kwargs, span = fake_obs.started_spans[0]
        assert name == "my-generation"
        assert kwargs["metadata"]["model"] == "test-model"
        assert span._ended is True
        output_update = next(u for u in span.updates if "output" in u)
        assert output_update["output"] == "test response"
        assert "latency_ms" in output_update

    def test_chat_without_observation_does_not_crash(self, monkeypatch):
        """When no observation is supplied, chat() works exactly as before."""
        fake_client = _FakeOpenAIClient(output="plain result")

        from app.utils.llm_client import LLMClient

        llm = LLMClient(api_key="x", base_url="http://example", model="test-model")
        llm.client = fake_client

        result = llm.chat(
            messages=[{"role": "user", "content": "hi"}],
        )

        assert result == "plain result"

    def test_chat_records_usage_when_available(self, monkeypatch):
        """Usage information is attached to the span when the response includes it."""
        fake_obs = _FakeObservation()
        fake_client = _FakeOpenAIClient(
            output="response with usage",
            usage={"prompt_tokens": 20, "completion_tokens": 8, "total_tokens": 28},
        )

        from app.utils.llm_client import LLMClient

        llm = LLMClient(api_key="x", base_url="http://example", model="gpt-4o")
        llm.client = fake_client

        llm.chat(
            messages=[{"role": "user", "content": "hello"}],
            observation=fake_obs,
            generation_name="usage-test",
        )

        name, kwargs, span = fake_obs.started_spans[0]
        output_update = next(u for u in span.updates if "usage" in u)
        assert output_update["usage"]["total_tokens"] == 28

    def test_chat_records_exception_on_error(self, monkeypatch):
        """When chat raises an exception, the span records the error and ends."""
        class _FailingFakeResponse(_FakeOpenAIResponse):
            """Response that raises on access."""

            def __init__(self):
                pass

            @property
            def choices(self):
                raise RuntimeError("simulated API error")

        class _FailingFakeChat(_FakeChat):
            def __init__(self):
                self.response = _FailingFakeResponse()

        class _FailingFakeOpenAIClient:
            def __init__(self):
                pass

            @property
            def chat(self):
                return _FailingFakeChat()

        fake_obs = _FakeObservation()

        from app.utils.llm_client import LLMClient

        llm = LLMClient(api_key="x", base_url="http://example", model="test-model")
        llm.client = _FailingFakeOpenAIClient()

        with pytest.raises(RuntimeError):
            llm.chat(
                messages=[{"role": "user", "content": "hi"}],
                observation=fake_obs,
                generation_name="error-test",
            )

        name, kwargs, span = fake_obs.started_spans[0]
        error_update = next(
            (u for u in span.updates if "status_message" in u and "error" in u["status_message"]),
            None,
        )
        assert error_update is not None
        assert span._ended is True

    def test_chat_json_forwards_observation_and_generation_name(self, monkeypatch):
        """chat_json() forwards observation and generation_name into chat()."""
        fake_obs = _FakeObservation()
        fake_client = _FakeOpenAIClient(output='{"ok": true}')

        from app.utils.llm_client import LLMClient

        llm = LLMClient(api_key="x", base_url="http://example", model="test-model")
        llm.client = fake_client

        result = llm.chat_json(
            messages=[{"role": "user", "content": "get json"}],
            observation=fake_obs,
            generation_name="outline-json",
        )

        assert result == {"ok": True}
        name, kwargs, span = fake_obs.started_spans[0]
        assert name == "outline-json"

    def test_chat_json_raises_value_error_on_invalid_json(self, monkeypatch):
        """When the response is not valid JSON, chat_json() raises ValueError."""
        fake_client = _FakeOpenAIClient(output="not json at all")

        from app.utils.llm_client import LLMClient

        llm = LLMClient(api_key="x", base_url="http://example", model="test-model")
        llm.client = fake_client

        with pytest.raises(ValueError, match="JSON格式无效"):
            llm.chat_json(messages=[{"role": "user", "content": "bad"}])

    def test_chat_json_extracts_json_after_think_block(self, monkeypatch):
        """chat_json() should tolerate providers that prepend reasoning before fenced JSON."""
        fake_client = _FakeOpenAIClient(
            output=(
                "<think>I should reason first</think>\n\n"
                "```json\n"
                '{"result": 42, "ok": true}\n'
                "```"
            )
        )

        from app.utils.llm_client import LLMClient

        llm = LLMClient(api_key="x", base_url="http://example", model="test-model")
        llm.client = fake_client

        result = llm.chat_json(messages=[{"role": "user", "content": "ok"}])

        assert result == {"result": 42, "ok": True}

    def test_chat_json_without_observation_unchanged(self, monkeypatch):
        """When no observation is supplied, chat_json() still returns JSON as before."""
        fake_client = _FakeOpenAIClient(output='{"result": 42}')

        from app.utils.llm_client import LLMClient

        llm = LLMClient(api_key="x", base_url="http://example", model="test-model")
        llm.client = fake_client

        result = llm.chat_json(messages=[{"role": "user", "content": "ok"}])

        assert result == {"result": 42}

from app.utils.llm_client import LLMClient


class _FakeLLMClient(LLMClient):
    def __init__(self, response: str):
        self._response = response

    def chat(self, messages, temperature=0.7, max_tokens=4096, response_format=None):
        return self._response


def test_chat_json_parses_think_tags_and_fenced_json() -> None:
    client = _FakeLLMClient(
        """<think>
I should reason first.
</think>

```json
{
  \"entity_types\": [],
  \"edge_types\": [],
  \"analysis_summary\": \"ok\"
}
```"""
    )

    result = client.chat_json(messages=[{"role": "user", "content": "hi"}])

    assert result == {
        "entity_types": [],
        "edge_types": [],
        "analysis_summary": "ok",
    }

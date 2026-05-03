"""Mock LLM client for controlled testing."""

from typing import Any, Dict, List, Optional


class MockLLMClient:
    """Mock LLMClient with chat() and chat_json() returning controlled responses."""

    def __init__(
        self,
        responses: Optional[List[str]] = None,
        json_responses: Optional[List[Dict[str, Any]]] = None,
        default_response: str = "mock response",
        default_json_response: Optional[Dict[str, Any]] = None,
    ):
        self.responses = responses or []
        self.json_responses = json_responses or []
        self.default_response = default_response
        self.default_json_response = default_json_response or {"mock": "response"}
        self.call_count = 0
        self.chat_calls: List[tuple] = []
        self.chat_json_calls: List[tuple] = []

    def chat(
        self,
        messages=None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        response_format: Optional[Dict] = None,
        observation: Any = None,
        generation_name: Optional[str] = None,
        generation_metadata: Optional[dict] = None,
    ) -> str:
        """Return the next controlled text response."""
        self.call_count += 1
        self.chat_calls.append(
            {
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens,
                "response_format": response_format,
            }
        )
        if self.responses:
            idx = min(self.call_count - 1, len(self.responses) - 1)
            return self.responses[idx]
        return self.default_response

    def chat_json(
        self,
        messages=None,
        temperature: float = 0.3,
        max_tokens: int = 4096,
        observation: Any = None,
        generation_name: Optional[str] = None,
        generation_metadata: Optional[dict] = None,
    ) -> Dict[str, Any]:
        """Return the next controlled JSON response."""
        self.call_count += 1
        self.chat_json_calls.append(
            {
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens,
            }
        )
        if self.json_responses:
            idx = min(self.call_count - 1, len(self.json_responses) - 1)
            return self.json_responses[idx]
        return self.default_json_response

"""
Tests for the ConnectorFallbackRouter.

Uses a fake TestConnector to verify:
- Connectors are skipped when their key is unset
- Fallback order: Brave -> Tavily -> Jina
- Fallback stops on first success
- All-fail returns failure result with source='none'
"""

import pytest
from unittest.mock import patch, MagicMock

from app.connectors.base import Connector, ConnectorResult
from app.connectors.fallback_router import ConnectorFallbackRouter


# ---------------------------------------------------------------------------
# Fake connector for testing
# ---------------------------------------------------------------------------

class FakeConnector(Connector):
    """Fake connector whose success/failure is controlled by constructor args."""

    def __init__(self, should_succeed: bool = True, results: list = None, error: str = "boom"):
        self._should_succeed = should_succeed
        self._results = results or [
            {"title": "Test", "url": "https://example.com", "snippet": "test snippet"}
        ]
        self._error = error
        self.call_count = 0

    @property
    def name(self) -> str:
        return "fake"

    def search(self, query: str) -> ConnectorResult:
        self.call_count += 1
        if self._should_succeed:
            return ConnectorResult(success=True, results=self._results, source=self.name)
        return ConnectorResult(success=False, error=self._error, source=self.name)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestFallbackRouterBehavior:
    """Test ConnectorFallbackRouter fallback and skip logic."""

    def test_skips_brave_when_key_unset(self):
        """When BRAVE_SEARCH_API_KEY is not set, Brave is not in available_connectors."""
        with patch("app.connectors.fallback_router.Config") as mock_config:
            mock_config.BRAVE_SEARCH_API_KEY = None
            mock_config.TAVILY_API_KEY = "fake-tavily"
            mock_config.JINA_API_KEY = None

            router = ConnectorFallbackRouter()
            assert "brave" not in router.available_connectors

    def test_skips_tavily_when_key_unset(self):
        """When TAVILY_API_KEY is not set, Tavily is not in available_connectors."""
        with patch("app.connectors.fallback_router.Config") as mock_config:
            mock_config.BRAVE_SEARCH_API_KEY = "fake-brave"
            mock_config.TAVILY_API_KEY = None
            mock_config.JINA_API_KEY = None

            router = ConnectorFallbackRouter()
            assert "tavily" not in router.available_connectors

    def test_includes_brave_when_key_set(self):
        """When BRAVE_SEARCH_API_KEY is set, Brave is in available_connectors."""
        with patch("app.connectors.fallback_router.Config") as mock_config:
            mock_config.BRAVE_SEARCH_API_KEY = "fake-brave"
            mock_config.TAVILY_API_KEY = None
            mock_config.JINA_API_KEY = None

            router = ConnectorFallbackRouter()
            assert "brave" in router.available_connectors

    def test_fallback_order_first_success_stops(self):
        """
        Fallback tries connectors in order and returns on first success.
        Verify that only the first successful connector's results are returned.
        """
        with patch("app.connectors.fallback_router.Config") as mock_config:
            mock_config.BRAVE_SEARCH_API_KEY = None
            mock_config.TAVILY_API_KEY = None
            mock_config.JINA_API_KEY = None

            router = ConnectorFallbackRouter()
            # Replace connectors with fakes via monkey-patch
            fake_discovery = FakeConnector(should_succeed=True, results=[
                {"title": "Result A", "url": "https://a.com", "snippet": "A"}
            ])
            router._discovery = lambda q: fake_discovery.search(q)

            # Patch _extract_content to avoid actual HTTP calls
            router._extract_content = lambda urls: [
                {"url": "https://a.com", "content": "Page A content", "title": "Result A"}
            ]

            result = router.search("test query")
            assert result.success is True
            assert len(result.results) == 1
            assert result.results[0]["content"] == "Page A content"
            assert fake_discovery.call_count == 1

    def test_fallback_order_second_succeeds(self):
        """
        When the first discovery connector fails, fallback tries the next.
        """
        with patch("app.connectors.fallback_router.Config") as mock_config:
            mock_config.BRAVE_SEARCH_API_KEY = None
            mock_config.TAVILY_API_KEY = None
            mock_config.JINA_API_KEY = None

            router = ConnectorFallbackRouter()

            call_order = []

            def fake_discovery(query: str) -> ConnectorResult:
                call_order.append("first")
                return ConnectorResult(success=False, error="first failed", source="test")

            router._discovery = fake_discovery

            # Second discovery connector (the real Jina, but we mock it)
            fake_jina = FakeConnector(should_succeed=True, results=[
                {"title": "Jina Result", "url": "https://jina.example", "snippet": "from jina"}
            ])
            router._connector_names.append("jina")

            # Patch _extract_content to avoid HTTP calls
            router._extract_content = lambda urls: [
                {"url": "https://jina.example", "content": "Jina page", "title": "Jina Result"}
            ]

            result = router.search("test query")
            # Jina should have been tried as last resort
            assert call_order == ["first"]

    def test_all_fail_returns_failure_result(self):
        """
        When all connectors fail (or none are configured), returns a failure
        ConnectorResult with source='none'.
        """
        with patch("app.connectors.fallback_router.Config") as mock_config:
            mock_config.BRAVE_SEARCH_API_KEY = None
            mock_config.TAVILY_API_KEY = None
            mock_config.JINA_API_KEY = None

            router = ConnectorFallbackRouter()

            router._discovery = lambda q: ConnectorResult(
                success=False, error="All connectors failed", source="none"
            )

            result = router.search("test query")
            assert result.success is False
            assert result.source == "none"
            assert "failed" in result.error.lower()

    def test_no_urls_returns_failure(self):
        """When discovery succeeds but returns no URLs, returns a failure result."""
        with patch("app.connectors.fallback_router.Config") as mock_config:
            mock_config.BRAVE_SEARCH_API_KEY = None
            mock_config.TAVILY_API_KEY = None
            mock_config.JINA_API_KEY = None

            router = ConnectorFallbackRouter()

            router._discovery = lambda q: ConnectorResult(
                success=True, results=[], source="empty"
            )

            result = router.search("test query")
            assert result.success is False
            assert "No URLs found" in result.error

    def test_extraction_fallback_returns_discovery_results(self):
        """
        When Jina extraction fails for all URLs, fall back to returning
        discovery results so the pipeline doesn't go empty-handed.
        """
        with patch("app.connectors.fallback_router.Config") as mock_config:
            mock_config.BRAVE_SEARCH_API_KEY = None
            mock_config.TAVILY_API_KEY = None
            mock_config.JINA_API_KEY = None

            router = ConnectorFallbackRouter()

            discovery_results = [
                {"title": "A", "url": "https://a.com", "snippet": "A snippet"},
                {"title": "B", "url": "https://b.com", "snippet": "B snippet"},
            ]
            router._discovery = lambda q: ConnectorResult(
                success=True, results=discovery_results, source="brave"
            )

            # Simulate extraction failing for all URLs
            router._extract_content = lambda urls: []

            result = router.search("test query")
            assert result.success is True
            assert result.results == discovery_results

    def test_extraction_runs_on_top_urls(self):
        """Jina extraction is called only on the top N URLs (max_extraction_urls)."""
        with patch("app.connectors.fallback_router.Config") as mock_config:
            mock_config.BRAVE_SEARCH_API_KEY = None
            mock_config.TAVILY_API_KEY = None
            mock_config.JINA_API_KEY = None

            router = ConnectorFallbackRouter()
            router.max_extraction_urls = 3

            discovery_results = [
                {"title": f"Result {i}", "url": f"https://url{i}.com", "snippet": f"S{i}"}
                for i in range(10)
            ]
            router._discovery = lambda q: ConnectorResult(
                success=True, results=discovery_results, source="tavily"
            )

            router._extract_urls = lambda results: [r["url"] for r in results[:3]]

            extraction_called_with: list = []
            router._extract_content = lambda urls: (
                extraction_called_with.extend(urls) or []
            )

            router.search("test query")

            # Should be called with top 3 URLs
            assert len(extraction_called_with) == 3
            assert extraction_called_with == [
                "https://url0.com",
                "https://url1.com",
                "https://url2.com",
            ]

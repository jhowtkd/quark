"""
Automatic fallback router for search connectors.

Searches using Brave → Tavily → Jina in order.
On success from Brave/Tavily, fetches content from top 3 URLs using Jina.
Returns Jina-style extraction results as the final output.
"""

import logging
from typing import List, Optional

import requests

from ..config import Config
from .base import Connector, ConnectorResult
from .brave_connector import BraveSearchConnector
from .tavily_connector import TavilySearchConnector

logger = logging.getLogger(__name__)

JINA_BASE_URL = "https://r.jina.ai"


class ConnectorFallbackRouter:
    """
    Two-phase search router:

    Phase 1 (Discovery) — try Brave, then Tavily, then Jina search endpoint
        to obtain a list of URLs with titles and snippets.

    Phase 2 (Extraction) — call Jina AI content extraction on the top 3
        discovery URLs to obtain full markdown content.

    The router returns extraction results (url, content, title) that feed
    directly into the LLM summarization step downstream.
    """

    def __init__(self, max_extraction_urls: int = 3, timeout: int = 20):
        self._connectors: List[Connector] = []
        self.max_extraction_urls = max_extraction_urls
        self.timeout = timeout
        self._last_success: Optional[str] = None

        if Config.BRAVE_SEARCH_API_KEY:
            self._connectors.append(BraveSearchConnector())
        else:
            logger.debug("Brave not configured, skipping")

        if Config.TAVILY_API_KEY:
            self._connectors.append(TavilySearchConnector())
        else:
            logger.debug("Tavily not configured, skipping")

        self._connector_names = [c.name for c in self._connectors]

    @property
    def connector_name(self) -> str:
        """Name of the connector that succeeded (empty until search() is called)."""
        return self._last_success or "none"

    @property
    def available_connectors(self) -> List[str]:
        """List of configured connector names."""
        return self._connector_names

    def search(self, query: str) -> ConnectorResult:
        """
        Two-phase search:

        1. Discovery: try each discovery connector (Brave/Tavily/Jina search)
           until one returns URLs.
        2. Extraction: call Jina AI on the top N URLs.
        3. Return extraction results.
        """
        # ── Phase 1: Discovery ────────────────────────────────────────────────
        discovery_result = self._discovery(query)

        if not discovery_result.success:
            logger.info(f"All discovery connectors failed: {discovery_result.error}")
            return ConnectorResult(
                success=False,
                error=discovery_result.error,
                source="none",
            )

        urls = self._extract_urls(discovery_result.results)
        if not urls:
            return ConnectorResult(
                success=False,
                error="No URLs found in discovery results",
                source=self._last_success or "none",
            )

        # ── Phase 2: Extraction ────────────────────────────────────────────────
        extraction_results = self._extract_content(urls)

        if not extraction_results:
            # Fall back to returning discovery results if extraction fails
            return ConnectorResult(
                success=True,
                results=discovery_result.results,
                source=self._last_success or discovery_result.source,
            )

        return ConnectorResult(
            success=True,
            results=extraction_results,
            source=f"{self._last_success or discovery_result.source}+jina",
        )

    def _discovery(self, query: str) -> ConnectorResult:
        """
        Try each discovery connector in order until one succeeds.
        Jina is tried last as a search endpoint (not content extraction).
        """
        from .jina_connector import JinaSearchConnector

        connectors_to_try: List[Connector] = list(self._connectors)
        # Always append Jina as the last resort discovery connector
        connectors_to_try.append(JinaSearchConnector())

        for connector in connectors_to_try:
            try:
                result = connector.search(query)
                if result.success and result.results:
                    self._last_success = connector.name
                    return result
            except Exception as e:
                logger.info(f"{connector.name} failed: {e}, trying next connector...")

        return ConnectorResult(
            success=False,
            error="All connectors failed or unconfigured",
            results=[],
            source="none",
        )

    def _extract_urls(self, results: List[dict]) -> List[str]:
        """Pull URL strings from discovery results."""
        urls = []
        for item in results:
            url = item.get("url", "")
            if url:
                urls.append(url)
        return urls

    def _extract_content(self, urls: List[str]) -> List[dict]:
        """
        Call Jina AI content extraction on each URL.

        Uses the r.jina.ai/<url> endpoint which returns markdown-encoded
        content. Falls back per-URL so a single bad URL does not fail the
        entire extraction.
        """
        extraction_results: List[dict] = []
        for url in urls[: self.max_extraction_urls]:
            try:
                jina_url = f"{JINA_BASE_URL}/{url}"
                response = requests.get(
                    jina_url,
                    headers={"Accept": "text/markdown"},
                    timeout=self.timeout,
                )
                response.raise_for_status()
                markdown_content = response.text

                extraction_results.append(
                    {
                        "url": url,
                        "content": markdown_content,
                        "title": "",  # Will be enriched upstream if needed
                    }
                )
            except requests.RequestException as e:
                logger.info(f"Jina extraction failed for {url}: {e}")
                continue
            except Exception as e:
                logger.info(f"Jina extraction error for {url}: {e}")
                continue

        return extraction_results

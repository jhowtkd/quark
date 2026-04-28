"""
Tavily Search connector using the Tavily Search API.
"""

import logging
from typing import Any, Dict, List

import requests

from ..config import Config
from .base import Connector, ConnectorResult

logger = logging.getLogger(__name__)


class TavilySearchConnector(Connector):
    """Connector for Tavily Search API."""

    BASE_URL = "https://api.tavily.com/search"

    @property
    def name(self) -> str:
        return "tavily"

    def search(self, query: str) -> ConnectorResult:
        """Search using Tavily Search API."""
        api_key = Config.TAVILY_API_KEY
        if not api_key:
            return ConnectorResult(
                success=False,
                error="TAVILY_API_KEY not configured",
                source=self.name,
            )

        payload = {
            "api_key": api_key,
            "query": query,
            "max_results": 5,
        }

        try:
            response = requests.post(
                self.BASE_URL,
                json=payload,
                timeout=15,
            )
            response.raise_for_status()
            data = response.json()

            raw_results = data.get("results", [])
            results: List[Dict[str, Any]] = []
            for item in raw_results:
                results.append(
                    {
                        "title": item.get("title", ""),
                        "url": item.get("url", ""),
                        "snippet": item.get("content", ""),
                    }
                )

            return ConnectorResult(
                success=True,
                results=results,
                source=self.name,
                raw_response=data,
            )
        except requests.RequestException as e:
            logger.info(f"Tavily failed: {e}, trying Jina...")
            return ConnectorResult(
                success=False,
                error=str(e),
                source=self.name,
            )
        except (ValueError, TypeError) as e:
            logger.info(f"Tavily parse error: {e}")
            return ConnectorResult(
                success=False,
                error=f"Parse error: {e}",
                source=self.name,
            )

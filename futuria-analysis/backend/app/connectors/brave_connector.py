"""
Brave Search connector using the Brave Search API.
"""

import logging
from typing import Any, Dict, List

import requests

from ..config import Config
from .base import Connector, ConnectorResult

logger = logging.getLogger(__name__)


class BraveSearchConnector(Connector):
    """Connector for Brave Search API."""

    BASE_URL = "https://api.search.brave.com/res/v1/web/search"

    @property
    def name(self) -> str:
        return "brave"

    def search(self, query: str) -> ConnectorResult:
        """Search using Brave Search API."""
        api_key = Config.BRAVE_SEARCH_API_KEY
        if not api_key:
            return ConnectorResult(
                success=False,
                error="BRAVE_SEARCH_API_KEY not configured",
                source=self.name,
            )

        headers = {
            "X-Subscription-Token": api_key,
            "Accept": "application/json",
        }

        params = {
            "q": query,
            "count": 5,
        }

        try:
            response = requests.get(
                self.BASE_URL,
                headers=headers,
                params=params,
                timeout=15,
            )
            response.raise_for_status()
            data = response.json()

            web_results = data.get("web", {}).get("results", {})
            results: List[Dict[str, Any]] = []
            for item in web_results:
                results.append(
                    {
                        "title": item.get("title", ""),
                        "url": item.get("url", ""),
                        "snippet": item.get("description", ""),
                    }
                )

            return ConnectorResult(
                success=True,
                results=results,
                source=self.name,
                raw_response=data,
            )
        except requests.RequestException as e:
            logger.info(f"Brave failed: {e}, trying Tavily...")
            return ConnectorResult(
                success=False,
                error=str(e),
                source=self.name,
            )
        except (ValueError, TypeError) as e:
            logger.info(f"Brave parse error: {e}")
            return ConnectorResult(
                success=False,
                error=f"Parse error: {e}",
                source=self.name,
            )

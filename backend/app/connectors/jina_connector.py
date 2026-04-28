"""
Jina AI content extraction connector.

Note: Jina's `/v1/search` endpoint is a public web search service that
accepts a query string and returns markdown-encoded results. It does not
require an API key for basic usage (rate limits apply without one).
"""

import logging
from typing import Any, Dict, List

import requests

from .base import Connector, ConnectorResult

logger = logging.getLogger(__name__)


class JinaSearchConnector(Connector):
    """
    Connector for Jina AI search.

    Uses the public /v1/search endpoint which accepts a query string
    and returns markdown-encoded results. No API key is required for basic usage.
    """

    BASE_URL = "https://jina.ai/v1/search"

    @property
    def name(self) -> str:
        return "jina"

    def search(self, query: str) -> ConnectorResult:
        """Search using Jina AI public search endpoint."""
        params = {"q": query}

        headers = {
            "Accept": "application/json",
        }

        try:
            response = requests.get(
                self.BASE_URL,
                headers=headers,
                params=params,
                timeout=20,
            )
            response.raise_for_status()
            data = response.json()

            # Jina returns results as a list under "data" or directly
            raw_results = data.get("data", []) if isinstance(data, dict) else (data if isinstance(data, list) else [])
            results: List[Dict[str, Any]] = []
            for item in raw_results:
                results.append(
                    {
                        "title": item.get("title", ""),
                        "url": item.get("url", ""),
                        "snippet": item.get("description", item.get("snippet", "")),
                    }
                )

            if not results:
                # Fallback: Jina might return results directly
                if isinstance(data, dict) and "results" in data:
                    for item in data["results"]:
                        results.append(
                            {
                                "title": item.get("title", ""),
                                "url": item.get("url", ""),
                                "snippet": item.get("description", item.get("snippet", "")),
                            }
                        )

            return ConnectorResult(
                success=True,
                results=results,
                source=self.name,
                raw_response=data,
            )
        except requests.RequestException as e:
            logger.info(f"Jina failed: {e}")
            return ConnectorResult(
                success=False,
                error=str(e),
                source=self.name,
            )
        except (ValueError, TypeError) as e:
            logger.info(f"Jina parse error: {e}")
            return ConnectorResult(
                success=False,
                error=f"Parse error: {e}",
                source=self.name,
            )

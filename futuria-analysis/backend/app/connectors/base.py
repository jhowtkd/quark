"""
Abstract base class and result types for search connectors.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


@dataclass
class ConnectorResult:
    """Result from a search connector."""
    success: bool
    results: List[Dict[str, Any]] = field(default_factory=list)
    error: Optional[str] = None
    source: str = ""
    raw_response: Optional[dict] = None


class Connector(ABC):
    """Abstract base class for search connectors."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Connector name used in logging and result source attribution."""
        raise NotImplementedError

    @abstractmethod
    def search(self, query: str) -> ConnectorResult:
        """
        Perform a search for the given query string.

        Args:
            query: The search query string.

        Returns:
            ConnectorResult with results or error.
        """
        raise NotImplementedError

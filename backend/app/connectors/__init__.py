"""
Search connector interface and automatic fallback router.
"""

from .base import Connector, ConnectorResult
from .brave_connector import BraveSearchConnector
from .tavily_connector import TavilySearchConnector
from .jina_connector import JinaSearchConnector
from .fallback_router import ConnectorFallbackRouter

__all__ = [
    "Connector",
    "ConnectorResult",
    "BraveSearchConnector",
    "TavilySearchConnector",
    "JinaSearchConnector",
    "ConnectorFallbackRouter",
]

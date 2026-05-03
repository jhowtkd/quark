"""Mock Zep backend for controlled graph/search testing."""

from typing import Any, Dict, List, Optional


class MockZepBackend:
    """Mock Zep backend returning predefined entities, relations and search results."""

    def __init__(
        self,
        entities: Optional[Dict[str, Dict[str, Any]]] = None,
        relations: Optional[List[Dict[str, Any]]] = None,
        search_results: Optional[List[Dict[str, Any]]] = None,
    ):
        self.entities = entities or {}
        self.relations = relations or []
        self.search_results = search_results or []
        self.search_calls: List[Dict[str, Any]] = []
        self.get_entity_calls: List[Dict[str, Any]] = []
        self.add_fact_calls: List[Dict[str, Any]] = []

    def search(
        self,
        graph_id: str,
        query: str,
        limit: int = 10,
        scope: str = "edges",
    ) -> List[Dict[str, Any]]:
        """Return predefined search results."""
        self.search_calls.append(
            {"graph_id": graph_id, "query": query, "limit": limit, "scope": scope}
        )
        return self.search_results

    def get_entity(self, graph_id: str, entity_name: str) -> Optional[Dict[str, Any]]:
        """Return a predefined entity by name."""
        self.get_entity_calls.append(
            {"graph_id": graph_id, "entity_name": entity_name}
        )
        return self.entities.get(entity_name)

    def add_fact(
        self,
        graph_id: str,
        source: str,
        target: str,
        fact: str,
    ) -> bool:
        """Record a fact addition."""
        self.add_fact_calls.append(
            {
                "graph_id": graph_id,
                "source": source,
                "target": target,
                "fact": fact,
            }
        )
        return True

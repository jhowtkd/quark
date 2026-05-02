"""Tests for graph actor fidelity analysis and API endpoints."""

import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.services.graph_builder import GraphBuilderService
from app import create_app


@pytest.fixture
def client():
    app = create_app()
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


class FakeZepNode:
    """Minimal mock for Zep SDK node objects."""
    def __init__(self, uuid_, name, labels):
        self.uuid_ = uuid_
        self.name = name
        self.labels = labels


class TestGraphActorFidelity:
    """Verify analyze_graph_actor_fidelity correctness."""

    def _make_builder(self, nodes):
        builder = GraphBuilderService.__new__(GraphBuilderService)
        builder.client = None
        # Patch fetch_all_nodes locally
        import app.services.graph_builder
        self._orig_fetch_all_nodes = app.services.graph_builder.fetch_all_nodes
        app.services.graph_builder.fetch_all_nodes = lambda client, graph_id: nodes
        return builder

    def _restore(self):
        import app.services.graph_builder
        app.services.graph_builder.fetch_all_nodes = self._orig_fetch_all_nodes

    def test_eight_actors_two_concepts_fidelity_0_8(self):
        nodes = [
            FakeZepNode(f"u{i}", f"Actor {i}", ["Person"])
            for i in range(8)
        ] + [
            FakeZepNode("u8", "Inflacao", ["Concept"]),
            FakeZepNode("u9", "Crisis", ["Event"]),
        ]
        builder = self._make_builder(nodes)
        try:
            result = builder.analyze_graph_actor_fidelity("g1")
            assert result["actor_count"] == 8
            assert result["non_actor_count"] == 2
            assert result["fidelity_score"] == 0.8
            assert "Inflacao" in result["non_actor_examples"]
            assert "Crisis" in result["non_actor_examples"]
        finally:
            self._restore()

    def test_all_actors_fidelity_1_0(self):
        nodes = [
            FakeZepNode("u1", "Alice", ["Person"]),
            FakeZepNode("u2", "Corp", ["Company"]),
        ]
        builder = self._make_builder(nodes)
        try:
            result = builder.analyze_graph_actor_fidelity("g1")
            assert result["fidelity_score"] == 1.0
            assert result["non_actor_examples"] == []
        finally:
            self._restore()

    def test_empty_graph_fidelity_0(self):
        builder = self._make_builder([])
        try:
            result = builder.analyze_graph_actor_fidelity("g1")
            assert result["fidelity_score"] == 0.0
            assert result["total"] == 0
        finally:
            self._restore()

    def test_non_actor_examples_max_10(self):
        nodes = [
            FakeZepNode(f"u{i}", f"Concept {i}", ["Concept"])
            for i in range(15)
        ]
        builder = self._make_builder(nodes)
        try:
            result = builder.analyze_graph_actor_fidelity("g1")
            assert len(result["non_actor_examples"]) == 10
        finally:
            self._restore()

    def test_unknown_types_counted_separately(self):
        nodes = [
            FakeZepNode("u1", "Alice", ["Person"]),
            FakeZepNode("u2", "Mystery", ["UnknownType"]),
            FakeZepNode("u3", "Crisis", ["Event"]),
        ]
        builder = self._make_builder(nodes)
        try:
            result = builder.analyze_graph_actor_fidelity("g1")
            assert result["actor_count"] == 1
            assert result["non_actor_count"] == 1
            assert result["unknown_count"] == 1
            assert result["fidelity_score"] == round(1 / 3, 2)
        finally:
            self._restore()


class TestGraphFidelityApi:
    """Verify graph fidelity endpoint wiring via Flask test client."""

    def test_fidelity_endpoint_returns_success(self, client):
        # Mock GraphBuilderService.analyze_graph_actor_fidelity
        import app.api.graph
        original = GraphBuilderService.analyze_graph_actor_fidelity
        GraphBuilderService.analyze_graph_actor_fidelity = lambda self, gid: {
            "graph_id": gid,
            "actor_count": 8,
            "non_actor_count": 2,
            "unknown_count": 0,
            "total": 10,
            "non_actor_examples": ["Inflacao", "Crisis"],
            "fidelity_score": 0.8,
        }
        try:
            resp = client.get("/api/graph/fidelity/g1")
            assert resp.status_code == 200
            data = resp.get_json()
            assert data["success"] is True
            assert data["data"]["fidelity_score"] == 0.8
            assert "Inflacao" in data["data"]["non_actor_examples"]
        finally:
            GraphBuilderService.analyze_graph_actor_fidelity = original

    def test_info_endpoint_includes_fidelity_score(self, client):
        import app.api.graph
        from app.services.graph_builder import GraphInfo
        original_fidelity = GraphBuilderService.analyze_graph_actor_fidelity
        original_get_info = GraphBuilderService._get_graph_info

        GraphBuilderService.analyze_graph_actor_fidelity = lambda self, gid: {
            "graph_id": gid,
            "actor_count": 5,
            "non_actor_count": 0,
            "unknown_count": 0,
            "total": 5,
            "non_actor_examples": [],
            "fidelity_score": 1.0,
        }
        GraphBuilderService._get_graph_info = lambda self, gid: GraphInfo(
            graph_id=gid,
            node_count=5,
            edge_count=3,
            entity_types=["Person"],
        )
        try:
            resp = client.get("/api/graph/info/g1")
            assert resp.status_code == 200
            data = resp.get_json()
            assert data["success"] is True
            assert data["data"]["fidelity_score"] == 1.0
            assert data["data"]["node_count"] == 5
        finally:
            GraphBuilderService.analyze_graph_actor_fidelity = original_fidelity
            GraphBuilderService._get_graph_info = original_get_info

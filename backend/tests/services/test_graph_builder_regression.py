"""Graph builder regression tests against scenario fixtures."""

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import pytest

from app.services.graph_builder import GraphBuilderService
from tests.fixtures.scenarios.loader import SCENARIOS


class _MockNode:
    """Minimal mock node for graph builder tests."""

    def __init__(self, uuid_, name, labels, summary="", attributes=None):
        self.uuid_ = uuid_
        self.name = name
        self.labels = labels
        self.summary = summary
        self.attributes = attributes or {}


class _MockEdge:
    """Minimal mock edge for graph builder tests."""

    def __init__(
        self,
        uuid_,
        name,
        source_node_uuid,
        target_node_uuid,
        fact="",
        attributes=None,
    ):
        self.uuid_ = uuid_
        self.name = name
        self.source_node_uuid = source_node_uuid
        self.target_node_uuid = target_node_uuid
        self.fact = fact
        self.attributes = attributes or {}


def _make_scenario_nodes(scenario_name: str) -> list:
    """Generate mock nodes tailored to a scenario."""
    domain_entities = {
        "saude": [
            ("n1", "Hospital Sao Paulo", ["Entity", "Node", "Hospital"]),
            ("n2", "Dr. Silva", ["Entity", "Node", "Doctor"]),
            ("n3", "Paciente Joao", ["Entity", "Node", "Person"]),
            ("n4", "Laboratorio XYZ", ["Entity", "Node", "Organization"]),
            ("n5", "Medicamento ABC", ["Entity", "Node", "Product"]),
            ("n6", "Evento Aprovacao", ["Entity", "Node", "Event"]),
        ],
        "marketing": [
            ("n1", "Influencer Ana", ["Entity", "Node", "Person"]),
            ("n2", "Tech Reviewer", ["Entity", "Node", "Expert"]),
            ("n3", "SmartPhone Sust", ["Entity", "Node", "Product"]),
            ("n4", "Agencia Pub", ["Entity", "Node", "Organization"]),
            ("n5", "Consumidor", ["Entity", "Node", "Person"]),
            ("n6", "Concorrente", ["Entity", "Node", "Company"]),
        ],
        "direito": [
            ("n1", "Juiz Federal", ["Entity", "Node", "Judge"]),
            ("n2", "Advogado Silva", ["Entity", "Node", "Lawyer"]),
            ("n3", "Associacao Consum", ["Entity", "Node", "NGO"]),
            ("n4", "Varejo X", ["Entity", "Node", "Company"]),
            ("n5", "Jornalista", ["Entity", "Node", "Journalist"]),
            ("n6", "Reforma CDC", ["Entity", "Node", "Concept"]),
        ],
        "economia": [
            ("n1", "Banco Central", ["Entity", "Node", "Bank"]),
            ("n2", "Investidor PF", ["Entity", "Node", "Person"]),
            ("n3", "Fintech Z", ["Entity", "Node", "Company"]),
            ("n4", "Analista Mercado", ["Entity", "Node", "Expert"]),
            ("n5", "Selic", ["Entity", "Node", "Concept"]),
            ("n6", "B3", ["Entity", "Node", "Organization"]),
            ("n7", "Startup W", ["Entity", "Node", "Company"]),
        ],
        "geopolitica": [
            ("n1", "Governo Sul", ["Entity", "Node", "GovernmentAgency"]),
            ("n2", "ONG Ambiental", ["Entity", "Node", "NGO"]),
            ("n3", "Mineradora Q", ["Entity", "Node", "Company"]),
            ("n4", "Analista Geo", ["Entity", "Node", "Expert"]),
            ("n5", "Comunidade Local", ["Entity", "Node", "Organization"]),
            ("n6", "Litio", ["Entity", "Node", "Product"]),
            ("n7", "Territorio X", ["Entity", "Node", "Location"]),
        ],
    }
    return [
        _MockNode(uuid_, name, labels)
        for uuid_, name, labels in domain_entities.get(scenario_name, [])
    ]


def _make_scenario_edges(nodes: list) -> list:
    """Generate mock edges connecting the given nodes."""
    edges = []
    for i in range(len(nodes) - 1):
        edges.append(
            _MockEdge(
                uuid_=f"e{i}",
                name="RELATED_TO",
                source_node_uuid=nodes[i].uuid_,
                target_node_uuid=nodes[i + 1].uuid_,
                fact=f"{nodes[i].name} relaciona-se com {nodes[i+1].name}.",
            )
        )
    # Add a cross edge for richer relation count
    if len(nodes) >= 3:
        edges.append(
            _MockEdge(
                uuid_="e_cross",
                name="INFLUENCES",
                source_node_uuid=nodes[0].uuid_,
                target_node_uuid=nodes[2].uuid_,
                fact=f"{nodes[0].name} influencia {nodes[2].name}.",
            )
        )
    return edges


@pytest.mark.parametrize("scenario_name", list(SCENARIOS.keys()))
class TestGraphBuilderRegression:
    """Regression tests parameterized over the 5 scenario fixtures."""

    def test_graph_builds_minimum_entities(self, scenario_name: str):
        """Graph must contain at least the minimum expected entities."""
        scenario = SCENARIOS[scenario_name]
        nodes = _make_scenario_nodes(scenario_name)
        edges = _make_scenario_edges(nodes)

        with patch(
            "app.services.graph_builder.fetch_all_nodes", return_value=nodes
        ), patch(
            "app.services.graph_builder.fetch_all_edges", return_value=edges
        ):
            service = GraphBuilderService(api_key="fake-key")
            fidelity = service.analyze_graph_actor_fidelity("g_test")
            total = fidelity["total"]
            assert total >= scenario.expectations.grafo_min_entities, (
                f"{scenario_name}: expected >= {scenario.expectations.grafo_min_entities} entities, "
                f"got {total}"
            )

    def test_graph_unknown_rate_below_threshold(self, scenario_name: str):
        """Unknown entity rate must not exceed the scenario threshold."""
        scenario = SCENARIOS[scenario_name]
        nodes = _make_scenario_nodes(scenario_name)
        edges = _make_scenario_edges(nodes)

        with patch(
            "app.services.graph_builder.fetch_all_nodes", return_value=nodes
        ), patch(
            "app.services.graph_builder.fetch_all_edges", return_value=edges
        ):
            service = GraphBuilderService(api_key="fake-key")
            fidelity = service.analyze_graph_actor_fidelity("g_test")
            total = fidelity["total"]
            unknown_rate = fidelity["unknown_count"] / total if total > 0 else 0.0
            assert unknown_rate <= scenario.expectations.grafo_max_unknown_rate, (
                f"{scenario_name}: unknown rate {unknown_rate:.2f} exceeds threshold "
                f"{scenario.expectations.grafo_max_unknown_rate}"
            )

    def test_graph_has_minimum_relations(self, scenario_name: str):
        """Graph must contain at least the minimum expected relations."""
        scenario = SCENARIOS[scenario_name]
        nodes = _make_scenario_nodes(scenario_name)
        edges = _make_scenario_edges(nodes)

        with patch(
            "app.services.graph_builder.fetch_all_nodes", return_value=nodes
        ), patch(
            "app.services.graph_builder.fetch_all_edges", return_value=edges
        ):
            service = GraphBuilderService(api_key="fake-key")
            data = service.get_graph_data("g_test")
            edge_count = data["edge_count"]
            assert edge_count >= scenario.expectations.grafo_min_relations, (
                f"{scenario_name}: expected >= {scenario.expectations.grafo_min_relations} relations, "
                f"got {edge_count}"
            )

    def test_graph_does_not_return_traceback(self, scenario_name: str):
        """Graph analysis must not raise or return traceback strings."""
        nodes = _make_scenario_nodes(scenario_name)
        edges = _make_scenario_edges(nodes)

        with patch(
            "app.services.graph_builder.fetch_all_nodes", return_value=nodes
        ), patch(
            "app.services.graph_builder.fetch_all_edges", return_value=edges
        ):
            service = GraphBuilderService(api_key="fake-key")
            try:
                fidelity = service.analyze_graph_actor_fidelity("g_test")
                data = service.get_graph_data("g_test")
            except Exception as exc:
                pytest.fail(f"{scenario_name}: Graph builder raised {exc}")

            for payload in (fidelity, data):
                payload_str = str(payload)
                assert "Traceback" not in payload_str
                assert "traceback" not in payload_str.lower()

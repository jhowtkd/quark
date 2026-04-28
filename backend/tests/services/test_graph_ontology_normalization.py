"""Tests for ontology normalization before calling Zep."""

import sys
from copy import deepcopy
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))


class _FakeGraphClient:
    def __init__(self):
        self.last_kwargs = None

    def set_ontology(self, **kwargs):
        self.last_kwargs = kwargs


class _FakeClient:
    def __init__(self):
        self.graph = _FakeGraphClient()


def test_set_ontology_normalizes_names_for_zep_contract():
    """Entity refs should be PascalCase, edge keys SCREAMING_SNAKE_CASE, attrs snake_case."""
    from app.services.graph_builder import GraphBuilderService

    ontology = {
        "entity_types": [
            {
                "name": "profissional de rh",
                "description": "RH specialist",
                "attributes": [
                    {"name": "fullName", "description": "Display name"},
                    {"name": "name", "description": "Reserved attr"},
                ],
            },
            {
                "name": "CanalDeVenda",
                "description": "Sales channel",
                "attributes": [
                    {"name": "landingPageUrl", "description": "Landing page"},
                ],
            },
        ],
        "edge_types": [
            {
                "name": "compra através de",
                "description": "Purchase path",
                "attributes": [
                    {"name": "startDate", "description": "When it started"},
                ],
                "source_targets": [
                    {"source": "profissional de rh", "target": "Canal De Venda"},
                ],
            }
        ],
    }
    original = deepcopy(ontology)

    service = GraphBuilderService.__new__(GraphBuilderService)
    service.client = _FakeClient()

    service.set_ontology("graph_test", ontology)

    payload = service.client.graph.last_kwargs
    assert payload is not None
    assert payload["graph_ids"] == ["graph_test"]

    entities = payload["entities"]
    assert list(entities.keys()) == ["ProfissionalDeRh", "CanalDeVenda"]
    assert "full_name" in entities["ProfissionalDeRh"].model_fields
    assert "entity_name" in entities["ProfissionalDeRh"].model_fields
    assert "landing_page_url" in entities["CanalDeVenda"].model_fields

    edges = payload["edges"]
    assert list(edges.keys()) == ["COMPRA_ATRAVES_DE"]
    edge_model, source_targets = edges["COMPRA_ATRAVES_DE"]
    assert edge_model.__name__ == "CompraAtravesDe"
    assert "start_date" in edge_model.model_fields
    assert source_targets[0].source == "ProfissionalDeRh"
    assert source_targets[0].target == "CanalDeVenda"

    # The persisted ontology payload should stay untouched; normalization is transient.
    assert ontology == original


def test_set_ontology_reuses_known_entity_refs_and_fallbacks():
    """Source/target refs should normalize to known entities or safe PascalCase fallbacks."""
    from app.services.graph_builder import GraphBuilderService

    ontology = {
        "entity_types": [
            {"name": "organization", "attributes": []},
        ],
        "edge_types": [
            {
                "name": "related_to",
                "attributes": [],
                "source_targets": [
                    {"source": "entity", "target": "organization"},
                ],
            }
        ],
    }

    service = GraphBuilderService.__new__(GraphBuilderService)
    service.client = _FakeClient()

    service.set_ontology("graph_test", ontology)

    edge_model, source_targets = service.client.graph.last_kwargs["edges"]["RELATED_TO"]
    assert edge_model.__name__ == "RelatedTo"
    assert source_targets[0].source == "Entity"
    assert source_targets[0].target == "Organization"

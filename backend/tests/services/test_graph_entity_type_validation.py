"""Tests for entity type validation in graph pipeline.

Verifies that Unknown/Entity types are rejected and aliases are normalized.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.services.zep_entity_reader import ZepEntityReader, FilteredEntities


class TestGraphEntityTypeValidation:
    """Verify entity type validation before agent instantiation."""

    def _make_reader(self, nodes, edges=None):
        reader = ZepEntityReader.__new__(ZepEntityReader)
        reader.client = None
        reader.get_all_nodes = lambda graph_id: nodes
        reader.get_all_edges = lambda graph_id: edges or []
        return reader

    def test_unknown_entity_is_rejected(self):
        nodes = [
            {"uuid": "u1", "name": "XYZ123", "labels": ["Entity"], "summary": "Sem tipo.", "attributes": {}},
        ]
        reader = self._make_reader(nodes)
        result = reader.filter_defined_entities("g1", enrich_with_edges=False)
        assert result.filtered_count == 0
        assert result.unknown_entity_count == 1

    def test_alias_is_normalized(self):
        nodes = [
            {"uuid": "u1", "name": "ABC Corp", "labels": ["Firm"], "summary": "", "attributes": {}},
        ]
        reader = self._make_reader(nodes)
        result = reader.filter_defined_entities("g1", enrich_with_edges=False)
        assert result.filtered_count == 1
        entity = result.entities[0]
        assert entity.get_entity_type() == "Organization"

    def test_valid_entity_passes(self):
        nodes = [
            {"uuid": "u1", "name": "Hospital São Paulo", "labels": ["Entity"], "summary": "Hospital público.", "attributes": {}},
        ]
        reader = self._make_reader(nodes)
        result = reader.filter_defined_entities("g1", enrich_with_edges=False)
        assert result.filtered_count == 1
        assert result.unknown_entity_count == 0
        assert result.entities[0].get_entity_type() == "Hospital"

    def test_second_pass_resolves_entity(self):
        nodes = [
            {"uuid": "u1", "name": "Enfermeira Rosa", "labels": ["Entity"], "summary": "Profissional de saúde.", "attributes": {}},
        ]
        reader = self._make_reader(nodes)
        result = reader.filter_defined_entities("g1", enrich_with_edges=False)
        assert result.filtered_count == 1
        assert result.unknown_entity_count == 0
        assert result.entities[0].get_entity_type() in ("Nurse", "Hospital")

    def test_multiple_mixed_entities(self):
        nodes = [
            {"uuid": "u1", "name": "Hospital X", "labels": ["Entity"], "summary": "Hospital.", "attributes": {}},
            {"uuid": "u2", "name": "Dr. Y", "labels": ["Entity"], "summary": "Médico.", "attributes": {}},
            {"uuid": "u3", "name": "ZZZ999", "labels": ["Entity"], "summary": "Nada.", "attributes": {}},
        ]
        reader = self._make_reader(nodes)
        result = reader.filter_defined_entities("g1", enrich_with_edges=False)
        assert result.filtered_count == 2
        assert result.unknown_entity_count == 1

    def test_simulation_config_generator_raises_on_unresolved_type(self):
        from app.services.simulation_config_generator import SimulationConfigGenerator
        from app.services.zep_entity_reader import EntityNode

        entity = EntityNode(
            uuid="u1",
            name="Mystery",
            labels=["Entity"],
            summary="",
            attributes={},
        )
        generator = SimulationConfigGenerator.__new__(SimulationConfigGenerator)
        try:
            generator._generate_agent_config_by_rule(entity)
            assert False, "Expected ValueError for unresolved type"
        except ValueError as e:
            assert "Cannot instantiate agent" in str(e)

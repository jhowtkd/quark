"""Tests for non-actor entity filtering in ZepEntityReader."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.services.zep_entity_reader import ZepEntityReader, FilteredEntities


class TestFilterNonActorEntities:
    """Verify actor_only filter discards non-actor entities."""

    def _make_reader(self, nodes, edges=None):
        reader = ZepEntityReader.__new__(ZepEntityReader)
        reader.client = None
        reader.get_all_nodes = lambda graph_id: nodes
        reader.get_all_edges = lambda graph_id: edges or []
        return reader

    def test_actor_only_false_keeps_non_actors(self):
        nodes = [
            {"uuid": "u1", "name": "Dr. Silva", "labels": ["Doctor"], "summary": "", "attributes": {}},
            {"uuid": "u2", "name": "Inflacao", "labels": ["Concept"], "summary": "", "attributes": {}},
            {"uuid": "u3", "name": "Pandemia", "labels": ["Event"], "summary": "", "attributes": {}},
        ]
        reader = self._make_reader(nodes)
        result = reader.filter_defined_entities("g1", enrich_with_edges=False, actor_only=False)
        assert result.filtered_count == 3
        assert result.non_actor_count == 0

    def test_actor_only_true_discards_non_actors(self):
        nodes = [
            {"uuid": "u1", "name": "Dr. Silva", "labels": ["Doctor"], "summary": "", "attributes": {}},
            {"uuid": "u2", "name": "Inflacao", "labels": ["Concept"], "summary": "", "attributes": {}},
            {"uuid": "u3", "name": "Pandemia", "labels": ["Event"], "summary": "", "attributes": {}},
        ]
        reader = self._make_reader(nodes)
        result = reader.filter_defined_entities("g1", enrich_with_edges=False, actor_only=True)
        assert result.filtered_count == 1
        assert result.non_actor_count == 2
        assert result.entities[0].name == "Dr. Silva"

    def test_mixed_actors_and_non_actors_counts(self):
        nodes = [
            {"uuid": "u1", "name": "Alice", "labels": ["Person"], "summary": "", "attributes": {}},
            {"uuid": "u2", "name": "Bob", "labels": ["Student"], "summary": "", "attributes": {}},
            {"uuid": "u3", "name": "Corp", "labels": ["Company"], "summary": "", "attributes": {}},
            {"uuid": "u4", "name": "Sao Paulo", "labels": ["Location"], "summary": "", "attributes": {}},
            {"uuid": "u5", "name": "Crisis", "labels": ["Event"], "summary": "", "attributes": {}},
            {"uuid": "u6", "name": "Algo X", "labels": ["Technology"], "summary": "", "attributes": {}},
            {"uuid": "u7", "name": "Gov", "labels": ["GovernmentAgency"], "summary": "", "attributes": {}},
            {"uuid": "u8", "name": "Vaccine", "labels": ["Product"], "summary": "", "attributes": {}},
        ]
        reader = self._make_reader(nodes)
        result = reader.filter_defined_entities("g1", enrich_with_edges=False, actor_only=True)
        # Alice=Person, Bob=Student, Corp=Company, SaoPaulo=Location, Crisis=Event, AlgoX=Technology, Gov=GovernmentAgency, Vaccine=Product
        # Actors: Person, Student, Company, GovernmentAgency = 4
        # Non-actors: Location, Event, Technology, Product = 4
        assert result.filtered_count == 4
        assert result.non_actor_count == 4

    def test_non_actor_count_in_to_dict(self):
        nodes = [
            {"uuid": "u1", "name": "Alice", "labels": ["Person"], "summary": "", "attributes": {}},
            {"uuid": "u2", "name": "Crisis", "labels": ["Event"], "summary": "", "attributes": {}},
        ]
        reader = self._make_reader(nodes)
        result = reader.filter_defined_entities("g1", enrich_with_edges=False, actor_only=True)
        d = result.to_dict()
        assert d["non_actor_count"] == 1
        assert d["filtered_count"] == 1

    def test_all_non_actors_result_in_zero_filtered(self):
        nodes = [
            {"uuid": "u1", "name": "Concept A", "labels": ["Concept"], "summary": "", "attributes": {}},
            {"uuid": "u2", "name": "Event B", "labels": ["Event"], "summary": "", "attributes": {}},
        ]
        reader = self._make_reader(nodes)
        result = reader.filter_defined_entities("g1", enrich_with_edges=False, actor_only=True)
        assert result.filtered_count == 0
        assert result.non_actor_count == 2

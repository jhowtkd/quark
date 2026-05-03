"""Tests for unknown rate metrics per scenario.

Verifies that the Health scenario keeps unknown rate below 20%.
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.services.zep_entity_reader import ZepEntityReader


class TestUnknownRateMetrics:
    """Verify unknown entity rate stays within acceptable threshold."""

    def _make_reader(self, nodes, edges=None):
        reader = ZepEntityReader.__new__(ZepEntityReader)
        reader.client = None
        reader.get_all_nodes = lambda graph_id: nodes
        reader.get_all_edges = lambda graph_id: edges or []
        return reader

    def test_health_scenario_unknown_rate_below_threshold(self):
        fixture_path = Path(__file__).parent.parent / "fixtures" / "scenario_health_nodes.json"
        with open(fixture_path, "r", encoding="utf-8") as f:
            nodes = json.load(f)

        reader = self._make_reader(nodes)
        result = reader.filter_defined_entities("health_graph", enrich_with_edges=False)

        total_processed = result.unknown_entity_count + result.filtered_count
        unknown_rate = result.unknown_entity_count / total_processed if total_processed > 0 else 0

        assert unknown_rate <= 0.20, (
            f"Unknown rate {unknown_rate:.2%} exceeds 20% threshold "
            f"(resolved={result.filtered_count}, unknown={result.unknown_entity_count})"
        )

    def test_filtered_entities_includes_unknown_count(self):
        fixture_path = Path(__file__).parent.parent / "fixtures" / "scenario_health_nodes.json"
        with open(fixture_path, "r", encoding="utf-8") as f:
            nodes = json.load(f)

        reader = self._make_reader(nodes)
        result = reader.filter_defined_entities("health_graph", enrich_with_edges=False)

        assert hasattr(result, "unknown_entity_count")
        assert result.to_dict()["unknown_entity_count"] == result.unknown_entity_count

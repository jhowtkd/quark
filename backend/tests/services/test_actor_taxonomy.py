"""Tests for actor vs non-actor taxonomy classification."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.utils.entity_taxonomy import (
    ACTOR_ENTITY_TYPES,
    NON_ACTOR_ENTITY_TYPES,
    ENTITY_TYPE_DESCRIPTIONS,
    classify_actor_status,
)


class TestActorTaxonomy:
    """Verify actor/non-actor classification correctness."""

    def test_all_actor_types_return_actor(self):
        for entity_type in ACTOR_ENTITY_TYPES:
            result = classify_actor_status(entity_type)
            assert result == "actor", f"Expected 'actor' for {entity_type}, got '{result}'"

    def test_all_non_actor_types_return_non_actor(self):
        for entity_type in NON_ACTOR_ENTITY_TYPES:
            result = classify_actor_status(entity_type)
            assert result == "non_actor", f"Expected 'non_actor' for {entity_type}, got '{result}'"

    def test_empty_string_returns_unknown(self):
        assert classify_actor_status("") == "unknown"

    def test_none_returns_unknown(self):
        assert classify_actor_status(None) == "unknown"

    def test_unrecognized_type_returns_unknown(self):
        assert classify_actor_status("MythicalCreature") == "unknown"

    def test_actor_descriptions_exist(self):
        for entity_type in ACTOR_ENTITY_TYPES:
            assert entity_type in ENTITY_TYPE_DESCRIPTIONS, f"Missing description for {entity_type}"

    def test_non_actor_descriptions_exist(self):
        for entity_type in NON_ACTOR_ENTITY_TYPES:
            assert entity_type in ENTITY_TYPE_DESCRIPTIONS, f"Missing description for {entity_type}"

    def test_alias_resolution_for_actor(self):
        # "Firm" aliases to "Organization" which is an actor
        from app.utils.entity_taxonomy import resolve_entity_type
        assert resolve_entity_type("Firm") in ACTOR_ENTITY_TYPES
        assert classify_actor_status("Firm") == "actor"

    def test_alias_resolution_for_non_actor(self):
        # "Software" aliases to "Technology" which is a non-actor
        from app.utils.entity_taxonomy import resolve_entity_type
        assert resolve_entity_type("Software") in NON_ACTOR_ENTITY_TYPES
        assert classify_actor_status("Software") == "non_actor"

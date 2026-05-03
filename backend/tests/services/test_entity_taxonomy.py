"""Tests for entity_taxonomy module.

Validates catalog coverage, alias resolution, and heuristic inference.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.utils.entity_taxonomy import (
    ENTITY_TYPE_CATALOG,
    ENTITY_KEYWORD_MAP,
    ENTITY_TYPE_ALIASES,
    resolve_entity_type,
    infer_entity_type_from_text,
)


class TestEntityTaxonomyCatalog:
    """Verify catalog completeness and keyword coverage."""

    def test_all_catalog_types_have_keywords(self):
        missing = []
        for domain, types in ENTITY_TYPE_CATALOG.items():
            for t in types:
                if t not in ENTITY_KEYWORD_MAP or len(ENTITY_KEYWORD_MAP[t]) < 1:
                    missing.append((domain, t))
        assert not missing, f"Types missing keywords: {missing}"

    def test_keyword_map_has_at_least_15_types(self):
        assert len(ENTITY_KEYWORD_MAP) >= 15, (
            f"Expected >=15 types, got {len(ENTITY_KEYWORD_MAP)}"
        )

    def test_each_keyword_map_type_has_at_least_8_keywords(self):
        short = []
        for t, kws in ENTITY_KEYWORD_MAP.items():
            if len(kws) < 8:
                short.append((t, len(kws)))
        assert not short, f"Types with <8 keywords: {short}"


class TestEntityTypeAliases:
    """Verify alias normalization."""

    def test_aliases_resolve_correctly(self):
        assert resolve_entity_type("Politician") == "PublicFigure"
        assert resolve_entity_type("Corporation") == "Company"
        assert resolve_entity_type("Attorney") == "Lawyer"
        assert resolve_entity_type("UnknownType") == "UnknownType"
        assert resolve_entity_type("") == ""

    def test_canonical_types_preserved(self):
        for canonical in ("Person", "Hospital", "Doctor", "Bank"):
            assert resolve_entity_type(canonical) == canonical


class TestHeuristicInference:
    """Verify heuristic classification on known text examples."""

    def test_heuristic_classifies_at_least_10_examples(self):
        examples = [
            ("Hospital São Paulo", "Hospital"),
            ("Dr. João Silva", "Doctor"),
            ("Ministério da Saúde", "GovernmentAgency"),
            ("Universidade Federal", "University"),
            ("Banco do Brasil", "Bank"),
            ("Jornal Globo", "MediaOutlet"),
            ("Empresa X S/A", "Company"),
            ("Paciente internado", "Patient"),
            ("Laboratório de vacinas", "PharmaceuticalCompany"),
            ("Político brasileiro", "PublicFigure"),
        ]
        correct = 0
        failures = []
        for text, expected in examples:
            result = infer_entity_type_from_text(text)
            if result == expected:
                correct += 1
            else:
                failures.append(f"'{text}' -> expected {expected}, got {result}")
        assert correct >= 10, f"Only {correct}/{len(examples)} correct. Failures: {failures}"

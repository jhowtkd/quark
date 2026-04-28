"""Tests for graph-build chunk default normalization."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))


def test_config_defaults_use_phase_5_baseline():
    """Chunk defaults should move from 500/50 to the Phase 5 baseline."""
    from app.config import Config

    assert Config.DEFAULT_CHUNK_SIZE == 300
    assert Config.DEFAULT_CHUNK_OVERLAP == 30


def test_project_from_dict_normalizes_legacy_default_values():
    """Persisted legacy 500/50 values should normalize to the new baseline."""
    from app.models.project import Project

    project = Project.from_dict(
        {
            "project_id": "proj_test",
            "name": "Legacy Project",
            "status": "ontology_generated",
            "created_at": "2026-04-18T00:00:00",
            "updated_at": "2026-04-18T00:00:00",
            "chunk_size": 500,
            "chunk_overlap": 50,
        }
    )

    assert project.chunk_size == 300
    assert project.chunk_overlap == 30


def test_project_from_dict_preserves_non_legacy_overrides():
    """Non-legacy values should survive loading unchanged."""
    from app.models.project import Project

    project = Project.from_dict(
        {
            "project_id": "proj_test",
            "name": "Custom Project",
            "status": "ontology_generated",
            "created_at": "2026-04-18T00:00:00",
            "updated_at": "2026-04-18T00:00:00",
            "chunk_size": 420,
            "chunk_overlap": 12,
        }
    )

    assert project.chunk_size == 420
    assert project.chunk_overlap == 12

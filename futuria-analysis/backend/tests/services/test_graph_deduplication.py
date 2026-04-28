"""Tests for chunk deduplication."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))


def test_deduplicate_chunks_removes_exact_duplicates():
    from app.services.text_processor import TextProcessor

    chunks = ["a", "b", "a", "c", "b", "d"]
    result = TextProcessor.deduplicate_chunks(chunks)
    assert result == ["a", "b", "c", "d"]


def test_deduplicate_chunks_preserves_order():
    from app.services.text_processor import TextProcessor

    chunks = ["first", "second", "first", "third", "second"]
    result = TextProcessor.deduplicate_chunks(chunks)
    assert result == ["first", "second", "third"]


def test_deduplicate_chunks_empty_list():
    from app.services.text_processor import TextProcessor

    assert TextProcessor.deduplicate_chunks([]) == []


def test_deduplicate_chunks_no_duplicates():
    from app.services.text_processor import TextProcessor

    chunks = ["a", "b", "c"]
    assert TextProcessor.deduplicate_chunks(chunks) == ["a", "b", "c"]


def test_compute_signature_consistency():
    from app.services.text_processor import TextProcessor

    sig1 = TextProcessor.compute_signature("hello world")
    sig2 = TextProcessor.compute_signature("hello world")
    assert sig1 == sig2
    assert len(sig1) == 64  # SHA-256 hex digest length


def test_compute_signature_uniqueness():
    from app.services.text_processor import TextProcessor

    sig1 = TextProcessor.compute_signature("hello world")
    sig2 = TextProcessor.compute_signature("hello world!")
    assert sig1 != sig2

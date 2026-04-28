from app.utils.language_integrity import assess_text_integrity


def test_assess_text_integrity_accepts_clean_english_text() -> None:
    result = assess_text_integrity(
        "Future Prediction Report\nThe simulation indicates a close runoff between Lula and Flavio Bolsonaro."
    )

    assert result.ok is True
    assert result.forbidden_categories == ()
    assert result.missing_entities == ()
    assert result.suspect_terms == ()


def test_assess_text_integrity_flags_forbidden_scripts() -> None:
    result = assess_text_integrity(
        "Future Prediction Report\n趋势展望与风险提示\nLula remains competitive."
    )

    assert result.ok is False
    assert "cjk" in result.forbidden_categories


def test_assess_text_integrity_flags_missing_entities_and_suspect_replacements() -> None:
    result = assess_text_integrity(
        "The runoff is uncertain, but Flamengo Bolsonaro appears to be gaining momentum.",
        expected_entities=["Flávio Bolsonaro", "Lula"],
        suspect_terms=["Flamengo", "Flamengo Bolsonaro"],
    )

    assert result.ok is False
    assert "Flávio Bolsonaro" in result.missing_entities
    assert "Flamengo" in result.suspect_terms

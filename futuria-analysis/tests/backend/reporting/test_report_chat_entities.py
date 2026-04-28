from app.utils.language_integrity import (
    assess_text_integrity,
    enforce_controlled_output,
    extract_entity_candidates,
)


def test_extract_entity_candidates_keeps_known_report_names() -> None:
    entities = extract_entity_candidates(
        "Future Prediction Report\nFlávio Bolsonaro and Luiz Inácio Lula da Silva remain the leading runoff candidates."
    )

    assert "Flávio Bolsonaro" in entities
    assert "Luiz Inácio Lula da Silva" in entities


def test_assess_text_integrity_flags_entity_drift_against_reference_entities() -> None:
    allowed_entities = extract_entity_candidates(
        "Flávio Bolsonaro and Jair Bolsonaro remain visible actors in the simulation."
    )

    result = assess_text_integrity(
        "The runoff is uncertain, but Flamengo Bolsonaro appears to be gaining momentum.",
        allowed_entities=allowed_entities,
    )

    assert result.ok is False
    assert "Flamengo Bolsonaro" in result.entity_drift


def test_enforce_controlled_output_quarantines_invalid_chat_answer() -> None:
    reference = "Flávio Bolsonaro and Lula are the two main candidates in the report context."
    fallback = "Response blocked by reporting language policy. Please retry after regeneration."

    safe_text, result = enforce_controlled_output(
        "Flamengo Bolsonaro is now the clear favorite.",
        fallback_text=fallback,
        allowed_entity_source=reference,
    )

    assert safe_text == fallback
    assert result.ok is False
    assert "Flamengo Bolsonaro" in result.entity_drift


def test_assess_text_integrity_ignores_generic_report_headings_in_entity_drift() -> None:
    allowed_entities = extract_entity_candidates(
        "Flávio Bolsonaro and Jair Bolsonaro remain visible actors in the simulation."
    )

    result = assess_text_integrity(
        "Individual Health Trajectories and Adverse Events\n\nEmergent Pattern\nRisk Stratification\nEvidence Limitations",
        allowed_entities=allowed_entities,
    )

    assert result.entity_drift == ()


def test_assess_text_integrity_treats_leading_articles_as_same_entity() -> None:
    allowed_entities = extract_entity_candidates(
        "The Endocrine Society issued updated safety guidance for monitoring."
    )

    result = assess_text_integrity(
        "Endocrine Society guidance became a focal point in institutional risk framing.",
        allowed_entities=allowed_entities,
    )

    assert result.entity_drift == ()

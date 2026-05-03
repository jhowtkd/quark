"""Language guardrails regression tests."""

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import pytest

from app.utils.language_integrity import (
    assess_text_integrity,
    detect_any_language_contamination,
    detect_language_switches,
    detect_spanish_contamination,
    enforce_controlled_output,
)
from app.services.report_agent import ReportAgent
from tests.mocks.mock_llm_client import MockLLMClient


class TestLanguageGuardrailsRegression:
    """Regression tests for language integrity and guardrails."""

    def test_portuguese_text_passes(self):
        """Clean Portuguese text must pass all contamination checks."""
        text = (
            "O mercado financeiro brasileiro apresentou alta de 2,5% nesta semana. "
            "Analistas apontam que a elevacao da taxa Selic influenciou os investidores."
        )
        result = detect_any_language_contamination(text)
        assert result["ok"] is True
        assert result["forbidden_scripts"] is False
        assert result["spanish"] is False
        assert result["english_switch"] is False

    def test_english_preamble_fails(self):
        """English-only paragraphs must be detected as language switches."""
        text = (
            "The market reacted positively to the news. "
            "Investors are confident about future growth. "
            "Analysts expect strong quarterly results."
        )
        switches = detect_language_switches(text, expected_lang="pt")
        assert len(switches) > 0
        assert switches[0]["detected"] == "en"

    def test_mixed_pt_en_below_threshold_fails(self):
        """Text with English density above threshold must fail."""
        # High density of English stopwords mixed with Portuguese
        text = (
            "O mercado subiu. The investors are very happy with the results. "
            "They will continue to buy more stocks and bonds."
        )
        switches = detect_language_switches(text, expected_lang="pt")
        # The English paragraph should be flagged
        assert any(s["detected"] == "en" for s in switches)

    def test_retry_on_contamination(self):
        """Language guard must retry when contamination is detected."""
        # First response contaminated with Spanish, second clean
        llm = MockLLMClient(
            responses=[
                "El mercado subio mucho durante el ultimo trimestre. Los datos son muy positivos para todos los inversores. La economia crecio y el desempleo bajo.",  # Spanish contamination
                "O mercado subiu muito. Os dados sao positivos.",   # Clean PT
            ]
        )
        agent = ReportAgent(
            graph_id="g_001",
            simulation_id="sim_001",
            simulation_requirement="Teste",
            llm_client=llm,
            zep_tools=MagicMock(),
        )
        messages = [{"role": "user", "content": "Gerar texto"}]
        result = agent._generate_with_language_guard(
            messages=messages,
            max_retries=3,
        )
        assert result is not None
        assert "O mercado subiu" in result
        # LLM was called at least twice (first contaminated + retry)
        assert llm.call_count >= 2

    def test_profile_language_binding(self):
        """Profile configuration must bind forbidden scripts correctly."""
        agent = ReportAgent(
            graph_id="g_001",
            simulation_id="sim_001",
            simulation_requirement="Teste",
            llm_client=MockLLMClient(),
            zep_tools=MagicMock(),
            profile="generico",
        )
        forbidden = getattr(agent, "forbidden_scripts", [])
        assert "zh" in forbidden
        assert "ja" in forbidden
        assert "ko" in forbidden

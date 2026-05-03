"""Report agent regression tests."""

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import pytest

from app.services.report_agent import (
    ReportAgent,
    Report,
    ReportOutline,
    ReportSection,
    ReportStatus,
    THINKING_PATTERNS,
)
from app.utils.language_integrity import detect_any_language_contamination
from tests.mocks.mock_llm_client import MockLLMClient


class TestReportAgentRegression:
    """Regression tests for report generation and sanitization."""

    def test_report_not_empty(self):
        """A successfully generated report must not be empty."""
        report = Report(
            report_id="r_001",
            simulation_id="sim_001",
            graph_id="g_001",
            simulation_requirement="Test requirement",
            status=ReportStatus.COMPLETED,
            markdown_content="# Titulo\n\nConteudo do relatorio em portugues.",
        )
        assert report.markdown_content
        assert len(report.markdown_content.strip()) > 0

    def test_report_has_required_sections(self):
        """Report outline must contain the expected sections."""
        sections = [
            ReportSection(title="Resumo Executivo"),
            ReportSection(title="Analise de Cenario"),
            ReportSection(title="Conclusoes"),
        ]
        outline = ReportOutline(
            title="Relatorio Teste",
            summary="Resumo do relatorio",
            sections=sections,
        )
        assert len(outline.sections) >= 2
        titles = [s.title for s in outline.sections]
        assert any("conclus" in t.lower() for t in titles)

    def test_report_blocks_thinking_process(self):
        """Thinking process markers must be stripped from final output."""
        dirty = (
            "Thinking: I will now analyze the data.\n\n"
            "<think>Internal reasoning</think>\n\n"
            "Final content here."
        )
        clean = ReportAgent._sanitize_final_output(dirty)
        assert "Thinking:" not in clean
        assert "<think>" not in clean
        assert "Final content here" in clean

    def test_report_language_pt_threshold(self):
        """Portuguese report text must pass language contamination check."""
        pt_text = (
            "O mercado financeiro reagiu de forma positiva a elevacao da taxa Selic. "
            "Investidores pessoa fisica aumentaram a allocacao em renda fixa."
        )
        result = detect_any_language_contamination(pt_text)
        assert result["ok"] is True

    def test_report_failure_returns_actionable_error(self):
        """Report generation failure must produce an actionable error message."""
        report = Report(
            report_id="r_002",
            simulation_id="sim_002",
            graph_id="g_002",
            simulation_requirement="Test requirement",
            status=ReportStatus.PENDING,
        )
        error = Exception("Falha ao gerar secao: timeout na chamada LLM")
        agent = ReportAgent(
            graph_id="g_002",
            simulation_id="sim_002",
            simulation_requirement="Test",
            llm_client=MockLLMClient(),
            zep_tools=MagicMock(),
        )
        result = agent._handle_report_error(
            report=report,
            report_id="r_002",
            error=error,
            completed_section_titles=[],
            root_trace=None,
        )
        assert result.status == ReportStatus.FAILED
        assert result.error is not None
        assert len(result.error) > 0
        assert "falha" in result.error.lower() or "timeout" in result.error.lower()

    def test_report_empty_blocked(self):
        """Empty report content should be rejected or blocked."""
        report = Report(
            report_id="r_003",
            simulation_id="sim_003",
            graph_id="g_003",
            simulation_requirement="Test requirement",
            status=ReportStatus.COMPLETED,
            markdown_content="",
        )
        # Empty report is not useful — assert it is empty so downstream gates catch it
        assert report.markdown_content == ""
        # Quality gate should flag it
        from app.services.quality_gates import QualityGateService

        svc = QualityGateService()
        gate_result = svc._check_not_empty(report.markdown_content)
        assert gate_result.passed is False
        assert gate_result.severity.value == "blocking"

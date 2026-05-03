"""Quality gates regression tests."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import pytest

from app.services.quality_gates import QualityGateService, GateSeverity


class TestQualityGatesRegression:
    """Regression tests for post-generation quality gates."""

    def test_gate_blocks_english_thinking(self):
        """Language consistency gate must flag mid-document English switches."""
        svc = QualityGateService()
        mixed_text = (
            "O mercado financeiro brasileiro apresentou alta de 2,5% nesta semana. "
            "Analistas apontam que a elevacao da taxa Selic influenciou os investidores. "
            "O setor de tecnologia tambem se destacou com resultados positivos. "
            "The market reacted very positively to the latest interest rate hike. "
            "Investors increased their fixed income allocation significantly. "
            "Analysts expect further adjustments in the coming quarters. "
            "The economy continues to grow despite inflation concerns. "
            "A economia brasileira continua crescendo apesar das preocupacoes inflacionarias. "
            "O setor industrial mostrou recuperacao consistente ao longo do trimestre. "
            "Central bank policy remains a key focus for market participants around the world."
        )
        result = svc._check_language_consistency(mixed_text)
        assert result.passed is False
        assert result.gate_name == "language_consistency"
        assert "en" in " ".join(result.findings).lower()

    def test_gate_blocks_cjk_contamination(self):
        """CJK scripts in report text must be detected by text integrity."""
        from app.utils.language_integrity import assess_text_integrity

        cjk_text = (
            "# Relatorio\n\nO mercado subiu 5%. 市場は上昇しました。"
            "Alguns dados mostram crescimento."
        )
        integrity = assess_text_integrity(cjk_text)
        assert integrity.ok is False
        assert "cjk" in integrity.forbidden_categories

    def test_gate_blocks_spanish_contamination(self):
        """Spanish stopword contamination must be detected."""
        from app.utils.language_integrity import detect_spanish_contamination

        es_text = (
            "El mercado reacciono muy positivamente durante el ultimo trimestre. "
            "Los inversores aumentaron su allocacion en fondos de renta fija. "
            "Segun los analistas, la tendencia continua al alza. "
            "La economia crecio y el desempleo bajo significativamente. "
            "Los datos son muy positivos para todos los inversores."
        )
        assert detect_spanish_contamination(es_text) is True

    def test_gate_detects_missing_limitations(self):
        """Missing Known Limitations section must be auto-detected."""
        svc = QualityGateService()
        text = "# Titulo\n\nConteudo do relatorio sem secao de limitacoes.\n\n## Conclusoes\n\nFim."
        report = svc.run_gates(text)
        lim_gate = next(
            (g for g in report.gates if g.gate_name == "known_limitations"), None
        )
        assert lim_gate is not None
        assert lim_gate.passed is True  # gate auto-corrects by appending
        assert report.modified_content is not None
        assert "limitacoes conhecidas" in report.modified_content.lower()

    def test_gate_detects_numeric_inconsistency(self):
        """Numeric inconsistency for the same metric+period must be flagged."""
        svc = QualityGateService()
        text = (
            "# Relatorio\n\n"
            "A receita em 2024 foi de 10 bilhoes.\n\n"
            "Mais tarde, a receita em 2024 foi de 12 bilhoes.\n\n"
            "## Conclusoes\n\nFim."
        )
        result = svc._check_numeric_consistency(text)
        assert result.passed is False
        assert "inconsistencia numerica" in result.findings[0].lower()

    def test_gate_detects_self_contradiction(self):
        """Unsupported valuation or recommendation must be flagged."""
        svc = QualityGateService()
        text = (
            "# Relatorio\n\n"
            "O preco-alvo da acao e de R$ 150.\n\n"
            "A recomendacao de compra e forte.\n\n"
            "## Limitacoes Conhecidas\n\nEste e um cenario simulado."
        )
        result = svc._check_self_contradictions(text)
        assert result.passed is False
        findings_lower = " ".join(result.findings).lower()
        assert "preco-alvo" in findings_lower or "recomendacao" in findings_lower

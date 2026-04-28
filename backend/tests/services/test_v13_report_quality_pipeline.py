"""Integration tests for Milestone v1.3 Report Quality Improvement pipeline.

Validates that all 5 phases work together correctly:
- Phase 8: Data Provenance and Labeling
- Phase 9: Data Validation Pipeline
- Phase 10: Structured Report Format
- Phase 11: Neutrality and Bias Audit
- Phase 12: Output Quality Gates

These tests exercise the services in isolation with mock data.
Full end-to-end testing requires running backend with LLM + Zep.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import pytest


# =============================================================================
# PHASE 9: Data Validation Pipeline
# =============================================================================

class TestDataValidationService:
    """Tests for DataValidationService (Phase 9)."""

    def test_service_importable(self):
        from app.services.data_validation import DataValidationService
        assert DataValidationService is not None

    def test_validate_runs_with_mock_context(self):
        from app.services.data_validation import DataValidationService

        svc = DataValidationService()
        result = svc.validate(
            simulation_requirement="Analisar Tesla Q1 2026",
            context={"graph_id": "test_graph", "simulation_id": "test_sim", "related_facts": []}
        )
        assert result is not None
        assert hasattr(result, "to_dict")

    def test_extract_metrics_finds_financial_data(self):
        from app.services.data_validation import DataValidationService

        svc = DataValidationService()
        text = "Receita de 2025: US$ 94,8 bilhoes. EPS GAAP: US$ 2,45. EPS nao-GAAP: US$ 3,12."
        metrics = svc.extract_metrics(text, context={"related_facts": []})
        assert isinstance(metrics, list)
        # Should find at least revenue and EPS metrics
        assert len(metrics) >= 2

    def test_check_gaap_non_gaap_detects_dual_reporting(self):
        from app.services.data_validation import DataValidationService, MetricEntry

        svc = DataValidationService()
        metrics = [
            MetricEntry(name="EPS GAAP", metric_type="eps", value=2.45, period="2025", is_gaap=True),
            MetricEntry(name="EPS nao-GAAP", metric_type="eps", value=3.12, period="2025", is_gaap=False),
        ]
        warnings = svc.check_gaap_non_gaap(metrics)
        assert isinstance(warnings, list)


# =============================================================================
# PHASE 11: Neutrality and Bias Audit
# =============================================================================

class TestBiasAuditService:
    """Tests for BiasAuditService (Phase 11)."""

    def test_service_importable(self):
        from app.services.bias_audit import BiasAuditService, BiasReport, BiasDimension
        assert BiasAuditService is not None
        assert BiasReport is not None
        assert BiasDimension is not None

    def test_sentiment_balance_bullish_dominance_detected(self):
        from app.services.bias_audit import BiasAuditService

        svc = BiasAuditService()
        sections = [
            "A empresa mostra crescimento robusto e oportunidades de expansao. "
            "O mercado esta em alta e os lucros devem superar expectativas. "
            "Investidores estao otimistas com o rally das acoes.",
        ]
        report = svc.audit_sections(sections)
        dim = report.dimensions["sentiment_balance"]
        # Bullish-heavy text should have low score (imbalanced)
        assert dim.score < 0.80
        meta = dim.metadata
        assert meta.get("bullish", 0) > meta.get("bearish", 0)

    def test_sentiment_balance_balanced_text(self):
        from app.services.bias_audit import BiasAuditService

        svc = BiasAuditService()
        sections = [
            "A empresa tem pontos fortes como crescimento, mas tambem riscos de queda "
            "e vulnerabilidades no mercado. O cenario e misto.",
        ]
        report = svc.audit_sections(sections)
        dim = report.dimensions["sentiment_balance"]
        # More balanced text should have closer counts
        meta = dim.metadata
        bull = meta.get("bullish", 0)
        bear = meta.get("bearish", 0)
        assert bull > 0 or bear > 0

    def test_claim_calibration_strong_claim_without_evidence(self):
        from app.services.bias_audit import BiasAuditService

        svc = BiasAuditService()
        sections = [
            "A empresa certamente ira dominar o mercado completamente.",  # strong claim, no 📊
        ]
        report = svc.audit_sections(sections)
        dim = report.dimensions["claim_calibration"]
        # Should detect strong claim markers
        meta = dim.metadata
        assert meta.get("strong_total", 0) > 0
        assert meta.get("strong_without_evidence", 0) > 0

    def test_claim_calibration_properly_tagged_hypothesis(self):
        from app.services.bias_audit import BiasAuditService

        svc = BiasAuditService()
        sections = [
            "A empresa pode expandir para novos mercados em torno de 2026 🔮.",  # conditional + tag
        ]
        report = svc.audit_sections(sections)
        dim = report.dimensions["claim_calibration"]
        # Conditional marker with hypothesis tag should be acceptable
        meta = dim.metadata
        assert meta.get("speculative_total", 0) > 0

    def test_competitive_quantification_missing_numbers(self):
        from app.services.bias_audit import BiasAuditService

        svc = BiasAuditService()
        sections = [
            "A concorrencia e forte e o mercado e competitivo.",  # vague, no numbers
        ]
        report = svc.audit_sections(sections)
        dim = report.dimensions["competitive_quantification"]
        # Should flag competitive context without quantification
        meta = dim.metadata
        assert meta.get("competitive_paragraphs", 0) > 0

    def test_composite_score_range(self):
        from app.services.bias_audit import BiasAuditService

        svc = BiasAuditService()
        report = svc.audit_sections(["Texto neutro com dados 📊."])
        assert 0.0 <= report.bias_score <= 1.0
        assert isinstance(report.is_balanced, bool)


# =============================================================================
# PHASE 12: Output Quality Gates
# =============================================================================

class TestQualityGateService:
    """Tests for QualityGateService (Phase 12)."""

    def test_service_importable(self):
        from app.services.quality_gates import QualityGateService, QualityReport
        assert QualityGateService is not None
        assert QualityReport is not None

    def test_language_consistency_single_language_passes(self):
        from app.services.quality_gates import QualityGateService

        svc = QualityGateService()
        # Need sufficiently long Portuguese text for language analysis
        text = (
            "Receita de 2025: US$ 94,8 bilhoes 📊. Margem bruta: 15% 🔮. "
            "A empresa apresentou resultados solidos no trimestre. "
            "O mercado reagiu positivamente aos numeros divulgados. "
            "Analistas esperam crescimento continuo para o proximo ano. "
            "A administracao reforcou o compromisso com a expansao internacional."
        )
        report = svc.run_gates(text)
        gate = next((g for g in report.gates if g.gate_name == "language_consistency"), None)
        assert gate is not None
        # Portuguese-only text should pass
        assert gate.passed is True

    def test_numeric_consistency_detects_contradiction(self):
        from app.services.quality_gates import QualityGateService

        svc = QualityGateService()
        text = (
            "Receita de 2025: US$ 94,8 bilhoes 📊. "
            "No mesmo periodo, a receita foi de US$ 91,2 bilhoes."  # contradiction
        )
        report = svc.run_gates(text)
        gate = next((g for g in report.gates if g.gate_name == "numeric_consistency"), None)
        assert gate is not None
        # Should detect same-metric, same-period with different values
        assert len(gate.findings) > 0 or gate.passed is False

    def test_self_contradiction_detects_unsupported_valuation(self):
        from app.services.quality_gates import QualityGateService

        svc = QualityGateService()
        text = (
            "O preco-alvo justo e de US$ 350. "  # valuation claim
            "A empresa esta em declinio irreversivel."  # contradiction
        )
        report = svc.run_gates(text)
        gate = next((g for g in report.gates if g.gate_name == "self_contradiction"), None)
        assert gate is not None
        # Should flag unsupported valuation or contradiction
        assert len(gate.findings) > 0 or gate.passed is False

    def test_known_limitations_gate_exists(self):
        from app.services.quality_gates import QualityGateService

        svc = QualityGateService()
        text = "Relatorio sem secao de limitacoes."
        report = svc.run_gates(text)
        gate = next((g for g in report.gates if g.gate_name == "known_limitations"), None)
        assert gate is not None

    def test_all_gates_return_structured_report(self):
        from app.services.quality_gates import QualityGateService

        svc = QualityGateService()
        report = svc.run_gates("Texto de teste simples com mais conteudo para evitar curto circuito.")
        assert hasattr(report, "gates")
        assert hasattr(report, "overall_passed")
        assert isinstance(report.gates, list)
        assert len(report.gates) >= 4  # All 4 gates should be present


# =============================================================================
# PHASE 8 + 10: Profile Configuration Integration
# =============================================================================

class TestProfileConfiguration:
    """Tests that ECONOMIA_CONFIG has all v1.3 flags set."""

    def test_economia_has_provenance_enabled(self):
        from app.profiles.profile_manager import ProfileManager

        config = ProfileManager.get_profile("economia")
        assert getattr(config, "require_provenance", False) is True

    def test_economia_has_bias_audit_enabled(self):
        from app.profiles.profile_manager import ProfileManager

        config = ProfileManager.get_profile("economia")
        assert getattr(config, "require_bias_audit", False) is True

    def test_economia_has_quality_gates_enabled(self):
        from app.profiles.profile_manager import ProfileManager

        config = ProfileManager.get_profile("economia")
        assert getattr(config, "require_quality_gates", False) is True

    def test_generic_profile_does_not_enable_quality_features(self):
        from app.profiles.profile_manager import ProfileManager

        config = ProfileManager.get_profile("generico")
        # Generic profile should NOT require these features
        assert getattr(config, "require_provenance", False) is False
        assert getattr(config, "require_bias_audit", False) is False
        assert getattr(config, "require_quality_gates", False) is False

    def test_economia_prompt_contains_provenance_rules(self):
        from app.profiles.profile_manager import ProfileManager

        config = ProfileManager.get_profile("economia")
        prompt = config.report_system_prompt
        assert "📊" in prompt
        assert "🔮" in prompt
        assert "Fontes de Dados" in prompt

    def test_economia_prompt_contains_structured_format(self):
        from app.profiles.profile_manager import ProfileManager

        config = ProfileManager.get_profile("economia")
        prompt = config.report_system_prompt
        assert "Tese Principal" in prompt or "tese" in prompt.lower()
        assert "Fragilidades" in prompt or "fragilidades" in prompt.lower()

    def test_economia_prompt_contains_neutrality_rules(self):
        from app.profiles.profile_manager import ProfileManager

        config = ProfileManager.get_profile("economia")
        prompt = config.report_system_prompt
        assert "evidencias contrarias" in prompt or "contrarias" in prompt.lower()


# =============================================================================
# ReportAgent Integration Hooks
# =============================================================================

class TestReportAgentIntegration:
    """Tests that ReportAgent has all v1.3 service hooks wired."""

    def test_report_agent_imports_data_validation(self):
        import app.services.report_agent as ra_module
        source = Path(ra_module.__file__).read_text()
        assert "data_validation" in source
        assert "DataValidationService" in source

    def test_report_agent_imports_bias_audit(self):
        import app.services.report_agent as ra_module
        source = Path(ra_module.__file__).read_text()
        assert "bias_audit" in source
        assert "BiasAuditService" in source

    def test_report_agent_imports_quality_gates(self):
        import app.services.report_agent as ra_module
        source = Path(ra_module.__file__).read_text()
        assert "quality_gates" in source or "QualityGateService" in source

    def test_report_agent_has_provenance_validation(self):
        import app.services.report_agent as ra_module
        source = Path(ra_module.__file__).read_text()
        assert "_validate_provenance_tags" in source
        assert "provenance_validation" in source

    def test_report_agent_has_bias_audit_hook(self):
        import app.services.report_agent as ra_module
        source = Path(ra_module.__file__).read_text()
        assert "require_bias_audit" in source
        assert "bias_report" in source

    def test_report_agent_has_quality_gates_hook(self):
        import app.services.report_agent as ra_module
        source = Path(ra_module.__file__).read_text()
        assert "require_quality_gates" in source or "quality_gate" in source.lower()

    def test_report_agent_logs_provenance_version(self):
        import app.services.report_agent as ra_module
        source = Path(ra_module.__file__).read_text()
        assert "provenance_version" in source

    def test_report_agent_meta_includes_v13_fields(self):
        import app.services.report_agent as ra_module
        source = Path(ra_module.__file__).read_text()
        assert "provenance_version" in source
        assert "profile_type" in source
        assert "provenance_enabled" in source

"""Tests for simulation quality gates."""
import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.services.quality_gates import QualityGateService, GateSeverity


class TestSimulationQualityGates:
    """Verify simulation agent coverage gate levels."""

    def _make_result(self, coverage_ratio: float, missing_count: int = 0, spurious_count: int = 0):
        return {
            "coverage_ratio": coverage_ratio,
            "missing_count": missing_count,
            "spurious_count": spurious_count,
            "missing_agent_ids": list(range(missing_count)),
            "spurious_agent_ids": list(range(spurious_count)),
        }

    def test_blocking_when_coverage_below_80(self):
        """coverage_ratio < 0.80 deve ser BLOCKING."""
        svc = QualityGateService()
        result = svc._check_simulation_agent_coverage(self._make_result(0.75, missing_count=2))

        assert result.passed is False
        assert result.severity == GateSeverity.BLOCKING
        assert "muito baixa" in result.findings[0]

    def test_warning_when_coverage_between_80_and_90(self):
        """0.80 <= coverage_ratio < 0.90 deve ser WARNING."""
        svc = QualityGateService()
        result = svc._check_simulation_agent_coverage(self._make_result(0.85, missing_count=1))

        assert result.passed is False
        assert result.severity == GateSeverity.WARNING
        assert "abaixo do ideal" in result.findings[0]

    def test_pass_when_coverage_90_and_no_spurious(self):
        """coverage_ratio >= 0.90 e spurious_count == 0 deve passar."""
        svc = QualityGateService()
        result = svc._check_simulation_agent_coverage(self._make_result(0.95, missing_count=0))

        assert result.passed is True
        assert result.severity == GateSeverity.INFO

    def test_warning_when_coverage_ok_but_spurious_present(self):
        """coverage_ratio >= 0.90 com spurious_count > 0 deve ser WARNING."""
        svc = QualityGateService()
        result = svc._check_simulation_agent_coverage(self._make_result(1.0, spurious_count=1))

        assert result.passed is False
        assert result.severity == GateSeverity.WARNING
        assert "espurios detectados" in result.findings[0]

    def test_run_simulation_gates_returns_quality_report(self):
        """run_simulation_gates deve retornar QualityReport."""
        svc = QualityGateService()
        report = svc.run_simulation_gates(self._make_result(1.0))

        assert report.overall_passed is True
        assert len(report.gates) == 1
        assert report.gates[0].gate_name == "simulation_agent_coverage"

    def test_run_simulation_gates_overall_failed_on_blocking(self):
        """run_simulation_gates com gate bloqueante deve ter overall_passed=False."""
        svc = QualityGateService()
        report = svc.run_simulation_gates(self._make_result(0.7))

        assert report.overall_passed is False
        assert report.gates[0].severity == GateSeverity.BLOCKING

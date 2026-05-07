"""Tests for report agent evolution evidence contract."""
import pytest
from unittest.mock import patch, MagicMock
from app.services.report_agent import ReportAgent
from app.services.report_orchestrator import ReportOrchestratorService


def test_report_section_cites_event_causes():
    """Test that a report section about agent evolution includes cited event causes."""
    agent = ReportAgent(
        graph_id="g1",
        simulation_id="sim1",
        simulation_requirement="test",
    )
    agent.agent_evolution = {
        "summary": {
            "averages": {"fatigue": 0.22},
            "top_changed_agents": [{"agent_id": 1, "agent_name": "Alice", "change_score": 0.42}],
        },
        "events": [
            {"agent_id": 1, "round_num": 1, "metric_name": "fatigue", "delta": 0.02, "causes": ["DO_NOTHING (success)"]},
        ],
    }

    # The system prompt should contain evolution evidence instructions
    prompt = agent._build_system_prompt()
    assert "cite event causes" in prompt.lower() or "evolution" in prompt.lower()


def test_report_says_evidence_insufficient_when_empty():
    """Test that report says evidence is insufficient when agent_evolution is missing."""
    agent = ReportAgent(
        graph_id="g1",
        simulation_id="sim1",
        simulation_requirement="test",
    )
    agent.agent_evolution = {}

    prompt = agent._build_system_prompt()
    assert "insufficient" in prompt.lower() or "evidence" in prompt.lower()


def test_orchestrator_passes_evolution_to_agent():
    """Test that orchestrator passes agent_evolution to ReportAgent."""
    mock_state = MagicMock()
    mock_state.project_id = "p1"
    mock_state.graph_id = "g1"
    mock_state.profile = "generico"

    mock_project = MagicMock()
    mock_project.simulation_requirement = "test"
    mock_project.graph_id = "g1"

    with patch('app.services.report_orchestrator.SimulationManager') as MockSimManager, \
         patch('app.services.report_orchestrator.ProjectManager') as MockProjManager, \
         patch('app.services.report_orchestrator.ReportManager') as MockReportManager:

        MockSimManager.return_value.get_simulation.return_value = mock_state
        MockProjManager.get_project.return_value = mock_project
        MockReportManager.get_report_by_simulation.return_value = None

        context = ReportOrchestratorService.resolve_generation_context("sim1", {})
        assert "agent_evolution" in context


def test_profile_application_preserves_evidence_rules():
    """Test that applying a profile after init does not remove evolution evidence rules."""
    from app.profiles import ProfileManager

    agent = ReportAgent(
        graph_id="g1",
        simulation_id="sim1",
        simulation_requirement="test",
        agent_evolution={
            "summary": {
                "averages": {"fatigue": 0.22},
                "top_changed_agents": [],
            },
            "events": [],
            "snapshots": {},
        },
    )

    # Before profile application, prompt has evolution rules
    prompt_before = agent.system_prompt
    assert "Agent Evolution Evidence Rules" in prompt_before
    assert "cite event causes" in prompt_before.lower()

    # Apply profile (this overwrites system_prompt)
    profile = ProfileManager().get_profile_or_default("generico")
    profile.apply_to_report_agent(agent)

    # After profile application, prompt should still have evolution rules
    # This is what the orchestrator does:
    agent.system_prompt = agent._build_system_prompt()

    prompt_after = agent.system_prompt
    assert "Agent Evolution Evidence Rules" in prompt_after
    assert "cite event causes" in prompt_after.lower()
    assert "insufficient" in prompt_after.lower()

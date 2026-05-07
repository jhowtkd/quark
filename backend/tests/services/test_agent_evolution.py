"""Tests for agent evolution service."""
import pytest
from app.services.agent_evolution import (
    AgentEvolutionState,
    AgentEvolutionEvent,
    AgentEvolutionSnapshot,
    EvolutionPolicy,
    EvolutionRoundResult,
    EvolutionService,
    summarize_evolution,
)


def test_default_initial_state_has_all_six_metrics_between_zero_and_one():
    state = AgentEvolutionState()
    assert 0.0 <= state.social_influence <= 1.0
    assert 0.0 <= state.polarization_risk <= 1.0
    assert 0.0 <= state.fatigue <= 1.0
    assert 0.0 <= state.evidence_openness <= 1.0
    assert 0.0 <= state.narrative_alignment <= 1.0
    assert 0.0 <= state.trust_level <= 1.0


def test_stable_sensitive_and_polarizable_policies_produce_different_delta_sizes():
    actions = [
        {
            "round_num": 1,
            "agent_id": 7,
            "agent_name": "Ana",
            "platform": "twitter",
            "action_type": "REPOST",
            "success": True,
            "timestamp": "2026-05-07T10:00:00",
        },
        {
            "round_num": 1,
            "agent_id": 7,
            "agent_name": "Ana",
            "platform": "twitter",
            "action_type": "QUOTE_POST",
            "success": True,
            "timestamp": "2026-05-07T10:01:00",
        },
    ]

    stable = EvolutionService(policy=EvolutionPolicy.stable()).advance_round({}, actions, round_num=1)
    sensitive = EvolutionService(policy=EvolutionPolicy.sensitive()).advance_round({}, actions, round_num=1)
    polarizable = EvolutionService(policy=EvolutionPolicy.polarizable()).advance_round({}, actions, round_num=1)

    # Policies should produce different results
    assert stable.snapshots[7].polarization_risk != polarizable.snapshots[7].polarization_risk
    assert stable.snapshots[7].social_influence != sensitive.snapshots[7].social_influence


def test_every_applied_delta_records_at_least_one_event_cause():
    actions = [
        {
            "round_num": 1,
            "agent_id": 7,
            "agent_name": "Ana",
            "platform": "twitter",
            "action_type": "REPOST",
            "success": True,
            "timestamp": "2026-05-07T10:00:00",
        },
    ]

    result = EvolutionService(policy=EvolutionPolicy.stable()).advance_round({}, actions, round_num=1)
    assert result.events
    assert all(event.causes for event in result.events)


def test_fixed_action_input_produces_deterministic_snapshots():
    actions = [
        {
            "round_num": 1,
            "agent_id": 7,
            "agent_name": "Ana",
            "platform": "twitter",
            "action_type": "REPOST",
            "success": True,
            "timestamp": "2026-05-07T10:00:00",
        },
    ]

    result1 = EvolutionService(policy=EvolutionPolicy.stable()).advance_round({}, actions, round_num=1)
    result2 = EvolutionService(policy=EvolutionPolicy.stable()).advance_round({}, actions, round_num=1)

    assert result1.snapshots[7].social_influence == result2.snapshots[7].social_influence
    assert result1.snapshots[7].polarization_risk == result2.snapshots[7].polarization_risk
    assert result1.snapshots[7].fatigue == result2.snapshots[7].fatigue


def test_polarizable_policy_increases_polarization_more_than_stable():
    actions = [
        {
            "round_num": 1,
            "agent_id": 7,
            "agent_name": "Ana",
            "platform": "twitter",
            "action_type": "REPOST",
            "success": True,
            "timestamp": "2026-05-07T10:00:00",
        },
        {
            "round_num": 1,
            "agent_id": 7,
            "agent_name": "Ana",
            "platform": "twitter",
            "action_type": "QUOTE_POST",
            "success": True,
            "timestamp": "2026-05-07T10:01:00",
        },
    ]

    stable = EvolutionService(policy=EvolutionPolicy.stable()).advance_round({}, actions, round_num=1)
    polarizable = EvolutionService(policy=EvolutionPolicy.polarizable()).advance_round({}, actions, round_num=1)

    assert polarizable.snapshots[7].polarization_risk > stable.snapshots[7].polarization_risk
    assert polarizable.events
    assert all(event.causes for event in polarizable.events)


def test_failed_actions_increase_fatigue():
    actions = [
        {
            "round_num": 1,
            "agent_id": 7,
            "agent_name": "Ana",
            "platform": "twitter",
            "action_type": "CREATE_POST",
            "success": False,
            "timestamp": "2026-05-07T10:00:00",
        },
    ]

    result = EvolutionService(policy=EvolutionPolicy.stable()).advance_round({}, actions, round_num=1)
    assert result.snapshots[7].fatigue > 0.0


def test_search_posts_increases_evidence_openness():
    actions = [
        {
            "round_num": 1,
            "agent_id": 7,
            "agent_name": "Ana",
            "platform": "twitter",
            "action_type": "SEARCH_POSTS",
            "success": True,
            "timestamp": "2026-05-07T10:00:00",
        },
    ]

    result = EvolutionService(policy=EvolutionPolicy.stable()).advance_round({}, actions, round_num=1)
    assert result.snapshots[7].evidence_openness > 0.0


def test_metrics_are_clamped_between_zero_and_one():
    # Create many actions to try to push metrics beyond bounds
    actions = [
        {
            "round_num": 1,
            "agent_id": 7,
            "agent_name": "Ana",
            "platform": "twitter",
            "action_type": "REPOST",
            "success": True,
            "timestamp": "2026-05-07T10:00:00",
        },
    ] * 1000

    result = EvolutionService(policy=EvolutionPolicy.stable()).advance_round({}, actions, round_num=1)
    snapshot = result.snapshots[7]
    assert 0.0 <= snapshot.social_influence <= 1.0
    assert 0.0 <= snapshot.polarization_risk <= 1.0
    assert 0.0 <= snapshot.fatigue <= 1.0
    assert 0.0 <= snapshot.evidence_openness <= 1.0
    assert 0.0 <= snapshot.narrative_alignment <= 1.0
    assert 0.0 <= snapshot.trust_level <= 1.0


def test_summarize_evolution_returns_averages_and_top_changed():
    actions = [
        {
            "round_num": 1,
            "agent_id": 7,
            "agent_name": "Ana",
            "platform": "twitter",
            "action_type": "REPOST",
            "success": True,
            "timestamp": "2026-05-07T10:00:00",
        },
        {
            "round_num": 1,
            "agent_id": 8,
            "agent_name": "Bob",
            "platform": "reddit",
            "action_type": "QUOTE_POST",
            "success": True,
            "timestamp": "2026-05-07T10:01:00",
        },
    ]

    result = EvolutionService(policy=EvolutionPolicy.stable()).advance_round({}, actions, round_num=1)
    summary = summarize_evolution(result)
    assert "averages" in summary
    assert "top_changed_agents" in summary
    assert len(summary["top_changed_agents"]) <= 2

"""Agent evolution service for deterministic metric updates."""
from dataclasses import dataclass, field
from typing import Dict, Any, List
from enum import Enum


class EvolutionPolicyType(str, Enum):
    STABLE = "stable"
    SENSITIVE = "sensitive"
    POLARIZABLE = "polarizable"


@dataclass
class EvolutionPolicy:
    """Deterministic policy that governs delta magnitudes."""
    policy_type: EvolutionPolicyType
    social_influence_multiplier: float = 1.0
    polarization_risk_multiplier: float = 1.0
    fatigue_multiplier: float = 1.0
    evidence_openness_multiplier: float = 1.0
    narrative_alignment_multiplier: float = 1.0
    trust_level_multiplier: float = 1.0

    @classmethod
    def stable(cls) -> "EvolutionPolicy":
        return cls(
            policy_type=EvolutionPolicyType.STABLE,
            social_influence_multiplier=1.0,
            polarization_risk_multiplier=1.0,
            fatigue_multiplier=1.0,
            evidence_openness_multiplier=1.0,
            narrative_alignment_multiplier=1.0,
            trust_level_multiplier=1.0,
        )

    @classmethod
    def sensitive(cls) -> "EvolutionPolicy":
        return cls(
            policy_type=EvolutionPolicyType.SENSITIVE,
            social_influence_multiplier=1.5,
            polarization_risk_multiplier=1.5,
            fatigue_multiplier=1.5,
            evidence_openness_multiplier=1.5,
            narrative_alignment_multiplier=1.5,
            trust_level_multiplier=1.5,
        )

    @classmethod
    def polarizable(cls) -> "EvolutionPolicy":
        return cls(
            policy_type=EvolutionPolicyType.POLARIZABLE,
            social_influence_multiplier=1.0,
            polarization_risk_multiplier=2.0,
            fatigue_multiplier=1.0,
            evidence_openness_multiplier=1.0,
            narrative_alignment_multiplier=1.0,
            trust_level_multiplier=1.0,
        )

    @classmethod
    def from_name(cls, name: str) -> "EvolutionPolicy":
        mapping = {
            "stable": cls.stable,
            "sensitive": cls.sensitive,
            "polarizable": cls.polarizable,
        }
        factory = mapping.get(name, cls.stable)
        return factory()


@dataclass
class AgentEvolutionState:
    """Current evolution metrics for a single agent."""
    social_influence: float = 0.0
    polarization_risk: float = 0.0
    fatigue: float = 0.0
    evidence_openness: float = 0.0
    narrative_alignment: float = 0.0
    trust_level: float = 0.0

    def clamp(self):
        """Clamp all metrics to [0.0, 1.0]."""
        self.social_influence = max(0.0, min(1.0, self.social_influence))
        self.polarization_risk = max(0.0, min(1.0, self.polarization_risk))
        self.fatigue = max(0.0, min(1.0, self.fatigue))
        self.evidence_openness = max(0.0, min(1.0, self.evidence_openness))
        self.narrative_alignment = max(0.0, min(1.0, self.narrative_alignment))
        self.trust_level = max(0.0, min(1.0, self.trust_level))


@dataclass
class AgentEvolutionEvent:
    """Records a change with its cause(s)."""
    agent_id: int
    round_num: int
    metric_name: str
    delta: float
    causes: List[str] = field(default_factory=list)


@dataclass
class AgentEvolutionSnapshot:
    """Snapshot of an agent's evolution at a point in time."""
    agent_id: int
    agent_name: str
    round_num: int
    social_influence: float
    polarization_risk: float
    fatigue: float
    evidence_openness: float
    narrative_alignment: float
    trust_level: float

    @classmethod
    def from_state(cls, agent_id: int, agent_name: str, round_num: int, state: AgentEvolutionState) -> "AgentEvolutionSnapshot":
        return cls(
            agent_id=agent_id,
            agent_name=agent_name,
            round_num=round_num,
            social_influence=state.social_influence,
            polarization_risk=state.polarization_risk,
            fatigue=state.fatigue,
            evidence_openness=state.evidence_openness,
            narrative_alignment=state.narrative_alignment,
            trust_level=state.trust_level,
        )


@dataclass
class EvolutionRoundResult:
    """Result of processing a round."""
    snapshots: Dict[int, AgentEvolutionSnapshot] = field(default_factory=dict)
    events: List[AgentEvolutionEvent] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "snapshots": {
                str(k): {
                    "agent_id": v.agent_id,
                    "agent_name": v.agent_name,
                    "round_num": v.round_num,
                    "social_influence": v.social_influence,
                    "polarization_risk": v.polarization_risk,
                    "fatigue": v.fatigue,
                    "evidence_openness": v.evidence_openness,
                    "narrative_alignment": v.narrative_alignment,
                    "trust_level": v.trust_level,
                }
                for k, v in self.snapshots.items()
            },
            "events": [
                {
                    "agent_id": e.agent_id,
                    "round_num": e.round_num,
                    "metric_name": e.metric_name,
                    "delta": e.delta,
                    "causes": e.causes,
                }
                for e in self.events
            ],
        }


class EvolutionService:
    """Deterministic service for computing agent evolution."""

    # Base deltas for each action type
    ACTION_DELTAS = {
        "CREATE_POST": {"social_influence": 0.02, "trust_level": 0.01},
        "REPOST": {"social_influence": 0.01, "polarization_risk": 0.01},
        "QUOTE_POST": {"social_influence": 0.015, "polarization_risk": 0.015, "narrative_alignment": 0.01},
        "COMMENT": {"social_influence": 0.01, "narrative_alignment": 0.005},
        "REPLY": {"social_influence": 0.01, "narrative_alignment": 0.005},
        "LIKE_POST": {"social_influence": 0.005},
        "SEARCH_POSTS": {"evidence_openness": 0.02},
        "DO_NOTHING": {"fatigue": 0.01},
    }

    # Platform repetition penalty
    PLATFORM_REPEAT_PENALTY = {"polarization_risk": 0.02}

    def __init__(self, policy: EvolutionPolicy = None):
        self.policy = policy or EvolutionPolicy.stable()

    def advance_round(
        self,
        previous_snapshots: Dict[int, AgentEvolutionSnapshot],
        actions: List[Dict[str, Any]],
        round_num: int,
    ) -> EvolutionRoundResult:
        """Process a round of actions and return updated snapshots."""
        # Start from previous states or defaults
        states: Dict[int, AgentEvolutionState] = {}
        agent_names: Dict[int, str] = {}

        for snap in previous_snapshots.values():
            states[snap.agent_id] = AgentEvolutionState(
                social_influence=snap.social_influence,
                polarization_risk=snap.polarization_risk,
                fatigue=snap.fatigue,
                evidence_openness=snap.evidence_openness,
                narrative_alignment=snap.narrative_alignment,
                trust_level=snap.trust_level,
            )
            agent_names[snap.agent_id] = snap.agent_name

        # Track platform usage per agent for repetition penalty
        agent_platforms: Dict[int, str] = {}
        events: List[AgentEvolutionEvent] = []

        for action in actions:
            agent_id = action["agent_id"]
            agent_name = action.get("agent_name", "Unknown")
            action_type = action.get("action_type", "DO_NOTHING")
            success = action.get("success", True)
            platform = action.get("platform", "")

            if agent_id not in states:
                states[agent_id] = AgentEvolutionState()
            if agent_id not in agent_names:
                agent_names[agent_id] = agent_name

            state = states[agent_id]
            causes: List[str] = []

            # Apply action deltas
            deltas = self.ACTION_DELTAS.get(action_type, {})
            for metric, base_delta in deltas.items():
                multiplier = getattr(self.policy, f"{metric}_multiplier", 1.0)
                delta = base_delta * multiplier

                if not success and metric == "social_influence":
                    # Failed social actions don't increase influence
                    continue

                current_value = getattr(state, metric)
                new_value = current_value + delta
                setattr(state, metric, new_value)
                causes.append(f"{action_type} ({'success' if success else 'failed'})")

                events.append(AgentEvolutionEvent(
                    agent_id=agent_id,
                    round_num=round_num,
                    metric_name=metric,
                    delta=delta,
                    causes=[f"{action_type} ({'success' if success else 'failed'})"],
                ))

            # Failed actions increase fatigue
            if not success:
                delta = 0.02 * self.policy.fatigue_multiplier
                state.fatigue += delta
                causes.append("action_failed")
                events.append(AgentEvolutionEvent(
                    agent_id=agent_id,
                    round_num=round_num,
                    metric_name="fatigue",
                    delta=delta,
                    causes=["action_failed"],
                ))

            # Platform repetition penalty
            if platform and agent_id in agent_platforms:
                if agent_platforms[agent_id] == platform:
                    delta = self.PLATFORM_REPEAT_PENALTY["polarization_risk"] * self.policy.polarization_risk_multiplier
                    state.polarization_risk += delta
                    causes.append(f"repeated_{platform}")
                    events.append(AgentEvolutionEvent(
                        agent_id=agent_id,
                        round_num=round_num,
                        metric_name="polarization_risk",
                        delta=delta,
                        causes=[f"repeated_{platform}"],
                    ))

            agent_platforms[agent_id] = platform

        # Clamp all states
        for state in states.values():
            state.clamp()

        # Build snapshots
        snapshots = {
            agent_id: AgentEvolutionSnapshot.from_state(agent_id, agent_names[agent_id], round_num, state)
            for agent_id, state in states.items()
        }

        return EvolutionRoundResult(snapshots=snapshots, events=events)

    def advance_all_rounds(self, actions: List[Dict[str, Any]]) -> EvolutionRoundResult:
        """Process all actions across multiple rounds."""
        # Group actions by round
        rounds: Dict[int, List[Dict[str, Any]]] = {}
        for action in actions:
            round_num = action.get("round_num", 1)
            rounds.setdefault(round_num, []).append(action)

        # Sort rounds
        sorted_rounds = sorted(rounds.keys())

        result = EvolutionRoundResult()
        for round_num in sorted_rounds:
            result = self.advance_round(result.snapshots, rounds[round_num], round_num)

        return result


def summarize_evolution(result: EvolutionRoundResult) -> Dict[str, Any]:
    """Create a summary of evolution results."""
    if not result.snapshots:
        return {
            "averages": {},
            "top_changed_agents": [],
        }

    # Calculate averages
    metrics = ["social_influence", "polarization_risk", "fatigue", "evidence_openness", "narrative_alignment", "trust_level"]
    averages = {}
    for metric in metrics:
        values = [getattr(s, metric) for s in result.snapshots.values()]
        averages[metric] = round(sum(values) / len(values), 2) if values else 0.0

    # Calculate total change per agent (sum of deltas across all events)
    agent_changes: Dict[int, float] = {}
    agent_names: Dict[int, str] = {}
    for event in result.events:
        agent_changes[event.agent_id] = agent_changes.get(event.agent_id, 0.0) + abs(event.delta)

    for snap in result.snapshots.values():
        agent_names[snap.agent_id] = snap.agent_name

    # Top changed agents
    top_changed = sorted(
        [{"agent_id": aid, "agent_name": agent_names.get(aid, "Unknown"), "change_score": round(score, 2)}
         for aid, score in agent_changes.items()],
        key=lambda x: x["change_score"],
        reverse=True,
    )

    return {
        "averages": averages,
        "top_changed_agents": top_changed[:10],
    }

"""Schemas Pydantic para endpoints de simulacao."""

from typing import Any, Dict, List
from pydantic import BaseModel, Field, field_validator, model_validator
from .base import simulation_id_validator


# =============================================================================
# Request schemas
# =============================================================================

class SimulationCreateRequest(BaseModel):
    """POST /simulation/create — Cria nova simulacao."""
    project_id: str = Field(...)
    graph_id: str | None = Field(default=None, max_length=128)
    enable_twitter: bool = Field(default=True)
    enable_reddit: bool = Field(default=True)
    profile: str = Field(default="generico", max_length=50)

    @field_validator("project_id")
    @classmethod
    def _validate_project_id(cls, v: str) -> str:
        from .base import project_id_validator
        return project_id_validator(v)


class SimulationPrepareRequest(BaseModel):
    """POST /simulation/prepare — Prepara ambiente de simulacao."""
    simulation_id: str = Field(...)
    entity_types: List[str] | None = Field(default=None)
    use_llm_for_profiles: bool = Field(default=True)
    parallel_profile_count: int = Field(default=5, ge=1, le=20)
    force_regenerate: bool = Field(default=False)

    @field_validator("simulation_id")
    @classmethod
    def _validate_simulation_id(cls, v: str) -> str:
        return simulation_id_validator(v)


class PrepareStatusRequest(BaseModel):
    """POST /simulation/prepare/status — Status de preparacao."""
    task_id: str | None = Field(default=None)
    simulation_id: str | None = Field(default=None)

    @model_validator(mode="after")
    def _validate_at_least_one(self):
        if not self.task_id and not self.simulation_id:
            raise ValueError("at least one of task_id or simulation_id is required")
        if self.simulation_id:
            simulation_id_validator(self.simulation_id)
        return self


class SimulationStartRequest(BaseModel):
    """POST /simulation/start — Inicia simulacao."""
    simulation_id: str = Field(...)
    platform: str = Field(default="reddit")
    max_rounds: int = Field(default=10, ge=1, le=1000)
    enable_graph_memory_update: bool = Field(default=False)
    enable_agent_evolution: bool = Field(default=True)
    agent_evolution_preset: str = Field(default="stable")

    @field_validator("simulation_id")
    @classmethod
    def _validate_simulation_id(cls, v: str) -> str:
        return simulation_id_validator(v)

    @field_validator("platform")
    @classmethod
    def _validate_platform(cls, v: str) -> str:
        if v not in {"reddit", "twitter", "parallel"}:
            raise ValueError("must be one of: reddit, twitter, parallel")
        return v

    @field_validator("agent_evolution_preset")
    @classmethod
    def _validate_agent_evolution_preset(cls, v: str) -> str:
        if v not in {"stable", "sensitive", "polarizable"}:
            raise ValueError("must be one of: stable, sensitive, polarizable")
        return v


class SimulationStopRequest(BaseModel):
    """POST /simulation/stop — Para simulacao."""
    simulation_id: str = Field(...)

    @field_validator("simulation_id")
    @classmethod
    def _validate_simulation_id(cls, v: str) -> str:
        return simulation_id_validator(v)


class SimulationEnvCloseRequest(BaseModel):
    """POST /simulation/env/close — Fecha ambiente de simulacao."""
    simulation_id: str = Field(...)
    timeout: int = Field(default=60, ge=5, le=300)

    @field_validator("simulation_id")
    @classmethod
    def _validate_simulation_id(cls, v: str) -> str:
        return simulation_id_validator(v)


class InterviewItem(BaseModel):
    """Item de entrevista para agente."""
    agent_id: str = Field(...)
    prompt: str = Field(...)


class SimulationInterviewRequest(BaseModel):
    """POST /simulation/interview — Entrevista agentes."""
    simulation_id: str = Field(...)
    interviews: List[InterviewItem] = Field(default_factory=list)

    @field_validator("simulation_id")
    @classmethod
    def _validate_simulation_id(cls, v: str) -> str:
        return simulation_id_validator(v)


class SimulationPostsRequest(BaseModel):
    """GET /simulation/posts — Posts da simulacao (query params)."""
    platform: str = Field(default="reddit")
    limit: int = Field(default=50, le=200)
    offset: int = Field(default=0)


class SimulationTimelineRequest(BaseModel):
    """GET /simulation/timeline — Timeline da simulacao (query params)."""
    start_round: int = Field(default=0, ge=0)
    end_round: int | None = Field(default=None)


# =============================================================================
# Response data schemas
# =============================================================================

class SimulationStateData(BaseModel):
    """Payload de estado da simulacao."""
    simulation_id: str = ""
    project_id: str = ""
    graph_id: str | None = None
    status: str = ""
    enable_twitter: bool = True
    enable_reddit: bool = True
    profile: str = ""
    created_at: str = ""
    entities_count: int = 0
    profiles_count: int = 0
    entity_types: List[str] = Field(default_factory=list)
    current_round: int = 0
    total_rounds: int = 0
    simulated_hours: int = 0
    twitter_actions_count: int = 0
    reddit_actions_count: int = 0
    total_actions_count: int = 0
    runner_status: str = ""
    error: str | None = None


class PrepareStatusData(BaseModel):
    """Payload de status de preparacao."""
    simulation_id: str = ""
    task_id: str | None = None
    status: str = ""
    progress: int = 0
    message: str = ""
    already_prepared: bool = False
    prepare_info: Dict[str, Any] | None = None
    expected_entities_count: int = 0
    entity_types: List[str] = Field(default_factory=list)


class RunStatusData(BaseModel):
    """Payload de status de execucao."""
    runner_status: str = ""
    current_round: int = 0
    total_rounds: int = 0
    simulated_hours: int = 0
    progress_percent: float = 0.0
    all_actions: List[Dict[str, Any]] = Field(default_factory=list)
    latest_actions: List[Dict[str, Any]] = Field(default_factory=list)
    error: str | None = None
    agent_evolution: Dict[str, Any] = Field(default_factory=dict)
    agent_evolution_enabled: bool = False
    agent_evolution_preset: str | None = None


class SimulationHistoryItem(BaseModel):
    """Item de historico de simulacao."""
    simulation_id: str = ""
    project_id: str = ""
    project_name: str = ""
    simulation_requirement: str = ""
    status: str = ""
    entities_count: int = 0
    profiles_count: int = 0
    entity_types: List[str] = Field(default_factory=list)
    created_at: str = ""
    updated_at: str = ""
    total_rounds: int = 0
    current_round: int = 0
    report_id: str | None = None
    version: str = ""
    files: List[str] = Field(default_factory=list)
    total_simulation_hours: int = 0


class AgentStatsData(BaseModel):
    """Payload de estatisticas de agentes."""
    total_agents: int = 0
    active_agents: int = 0
    platform_distribution: Dict[str, int] = Field(default_factory=dict)
    top_agents: List[Dict[str, Any]] = Field(default_factory=list)


class TimelineData(BaseModel):
    """Payload de timeline."""
    rounds: List[Dict[str, Any]] = Field(default_factory=list)
    events: List[Dict[str, Any]] = Field(default_factory=list)
    total_events: int = 0

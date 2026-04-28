"""
Helpers for building Langfuse report-observability metadata and scoring payloads.

These helpers are shared between ReportAgent and downstream reporting code.
They use the same interface whether a real client or a no-op client is active.
"""

from __future__ import annotations

import time
from typing import Any


def build_report_metadata(
    report_id: str,
    simulation_id: str,
    graph_id: str,
    simulation_requirement: str,
    llm_model: str | None = None,
    llm_base_url: str | None = None,
) -> dict[str, Any]:
    """
    Build the metadata dict attached to a root report-generation trace.

    Args:
        report_id: Unique report identifier.
        simulation_id: Simulation that generated this report.
        graph_id: Zep graph used for context.
        simulation_requirement: The user's original query/requirement.
        llm_model: Model used for generation (optional).
        llm_base_url: LLM API base URL (optional).

    Returns:
        dict suitable for Langfuse trace metadata.
    """
    return {
        "report_id": report_id,
        "simulation_id": simulation_id,
        "graph_id": graph_id,
        "simulation_requirement": simulation_requirement,
        "llm_model": llm_model or "",
        "llm_base_url": llm_base_url or "",
        "langfuse_trace_type": "report_generation",
    }


def build_chat_metadata(
    report_id: str,
    simulation_id: str,
    graph_id: str,
    message_length: int,
    history_count: int,
    llm_model: str | None = None,
) -> dict[str, Any]:
    """
    Build the metadata dict attached to a report-chat trace.

    Args:
        report_id: Report this chat is about.
        simulation_id: Simulation context.
        graph_id: Zep graph used.
        message_length: Length of the user message.
        history_count: Number of turns in chat history.
        llm_model: Model used (optional).

    Returns:
        dict suitable for Langfuse trace metadata.
    """
    return {
        "report_id": report_id,
        "simulation_id": simulation_id,
        "graph_id": graph_id,
        "message_length": message_length,
        "history_count": history_count,
        "llm_model": llm_model or "",
        "langfuse_trace_type": "report_chat",
    }


def score_integrity(
    observation,
    integrity_result: Any,
    *,
    fallback_used: bool = False,
    retry_count: int = 0,
    tool_calls_count: int = 0,
    conflict_retry_count: int = 0,
) -> None:
    """
    Convert a language-integrity result into Langfuse scores on the given observation.

    This function is safe to call with a no-op observation — it has no side-effects
    when the real Langfuse client is not active.

    Args:
        observation: A LangfuseSpanWrapper or NoOpObservation.
        integrity_result: A LanguageIntegrityResult from language_integrity.py.
        fallback_used: Whether a fallback response was used.
        retry_count: Total retry iterations in the section.
        tool_calls_count: Number of tool calls made in this section.
        conflict_retry_count: Number of tool-call / Final Answer conflicts.
    """
    # Boolean / binary scores
    observation.score(
        name="language_integrity_ok",
        value=1.0 if getattr(integrity_result, "ok", False) else 0.0,
        data_type="NUMERIC",
        comment="1=clean, 0=contamination detected",
    )

    observation.score(
        name="fallback_used",
        value=1.0 if fallback_used else 0.0,
        data_type="NUMERIC",
        comment="1=fallback response used",
    )

    forbidden = getattr(integrity_result, "forbidden_categories", ()) or ()
    observation.score(
        name="forbidden_scripts_detected",
        value=1.0 if forbidden else 0.0,
        data_type="NUMERIC",
        comment=f"forbidden scripts: {', '.join(forbidden)}" if forbidden else "none",
    )

    # Numeric counts
    observation.score(
        name="entity_drift_count",
        value=float(len(getattr(integrity_result, "entity_drift", ()) or [])),
        data_type="NUMERIC",
    )

    observation.score(
        name="missing_entities_count",
        value=float(len(getattr(integrity_result, "missing_entities", ()) or [])),
        data_type="NUMERIC",
    )

    observation.score(
        name="suspect_terms_count",
        value=float(len(getattr(integrity_result, "suspect_terms", ()) or [])),
        data_type="NUMERIC",
    )

    observation.score(
        name="tool_calls_count",
        value=float(tool_calls_count),
        data_type="NUMERIC",
    )

    observation.score(
        name="retry_count",
        value=float(retry_count),
        data_type="NUMERIC",
    )

    observation.score(
        name="conflict_retry_count",
        value=float(conflict_retry_count),
        data_type="NUMERIC",
    )

    # Aggregate health score (0-1, higher is better)
    ok_score = 1.0 if getattr(integrity_result, "ok", False) else 0.0
    health = ok_score * (0.0 if fallback_used else 1.0) * max(
        0, 1 - len(forbidden) * 0.1
    )
    observation.score(
        name="report_surface_health",
        value=health,
        data_type="NUMERIC",
        comment="0-1 aggregate: integrity OK AND no fallback AND no forbidden scripts",
    )

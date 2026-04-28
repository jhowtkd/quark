"""
Observability package — Langfuse tracing for the reporting pipeline.

Public API:
    build_observability_client(config) -> ObservabilityClient
    build_report_metadata(...)
    build_chat_metadata(...)
    score_integrity(observation, integrity_result, ...)
"""

from app.observability.langfuse_client import (
    NoOpObservabilityClient,
    LangfuseObservabilityClient,
    build_observability_client,
)

from app.observability.reporting import (
    build_report_metadata,
    build_chat_metadata,
    score_integrity,
)

__all__ = [
    "build_observability_client",
    "NoOpObservabilityClient",
    "LangfuseObservabilityClient",
    "build_report_metadata",
    "build_chat_metadata",
    "score_integrity",
]

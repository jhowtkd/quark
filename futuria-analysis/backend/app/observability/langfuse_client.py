"""
Observability facade for Langfuse.

Exports a single entry point: build_observability_client(config).

When LANGFUSE_ENABLED=false (default), returns a NoOpObservabilityClient.
When LANGFUSE_ENABLED=true and credentials are set, returns a LangfuseObservabilityClient.
"""

from __future__ import annotations

import logging
import os

logger = logging.getLogger(__name__)

# Lazy import — only loaded when the real client is needed.
Langfuse = None  # type: ignore[assignment]


def _get_langfuse():
    """Lazy-load the Langfuse SDK to avoid import errors when disabled."""
    global Langfuse
    if Langfuse is None:
        from langfuse import Langfuse as _LF
        Langfuse = _LF
    return Langfuse


class NoOpObservation:
    """
    No-op observation returned when observability is disabled.
    All methods are safe to call with zero side-effects.
    """

    is_noop = True

    def update(self, **kwargs) -> NoOpObservation:
        return self

    def score(self, **kwargs) -> None:
        return None

    def score_trace(self, **kwargs) -> None:
        return None

    def start_span(self, name: str, **kwargs) -> NoOpObservation:
        return NoOpObservation()

    def end(self) -> None:
        return None


class NoOpObservabilityClient:
    """
    No-op observability client used when LANGFUSE_ENABLED=false.
    Implements the same interface as LangfuseObservabilityClient so downstream
    code never needs conditional logic.
    """

    is_enabled = False

    def start_report_trace(
        self, name: str, session_id: str, metadata: dict | None = None
    ) -> NoOpObservation:
        return NoOpObservation()

    def start_span(
        self, name: str, metadata: dict | None = None
    ) -> NoOpObservation:
        """Start a standalone span (no parent trace).

        In the no-op client, returns a no-op observation that safely swallows
        all update/end calls. Subclasses or the real client may use this differently.
        """
        return NoOpObservation()

    def flush(self) -> None:
        return None

    def shutdown(self) -> None:
        return None


class LangfuseObservabilityClient:
    """
    Real Langfuse observability client.
    Wraps the Langfuse Python SDK and exposes the same interface as
    NoOpObservabilityClient so the rest of the codebase is decoupled from
    the SDK.
    """

    is_enabled = True

    def __init__(self, config):
        """
        Initialize the Langfuse client from config fields.

        Args:
            config: Config class with LANGFUSE_HOST, LANGFUSE_PUBLIC_KEY,
                    LANGFUSE_SECRET_KEY, LANGFUSE_ENV, LANGFUSE_RELEASE,
                    LANGFUSE_DEBUG, LANGFUSE_SAMPLE_RATE.
        """
        sdk = _get_langfuse()
        self._client = sdk(
            public_key=config.LANGFUSE_PUBLIC_KEY,
            secret_key=config.LANGFUSE_SECRET_KEY,
            base_url=config.LANGFUSE_HOST,
            environment=config.LANGFUSE_ENV,
            release=config.LANGFUSE_RELEASE,
            debug=config.LANGFUSE_DEBUG,
            sample_rate=config.LANGFUSE_SAMPLE_RATE,
        )
        logger.info(
            "Langfuse observability enabled: host=%s, env=%s, release=%s",
            config.LANGFUSE_HOST,
            config.LANGFUSE_ENV,
            config.LANGFUSE_RELEASE,
        )

    def start_report_trace(
        self, name: str, session_id: str, metadata: dict | None = None
    ):
        """
        Start a top-level Langfuse trace.

        Returns a LangfuseSpanWrapper so callers can open child spans
        and attach scores through the same interface as NoOpObservation.
        """
        trace = self._client.trace(name=name, session_id=session_id, metadata=metadata or {})
        return LangfuseSpanWrapper(trace)

    def flush(self) -> None:
        self._client.flush()

    def shutdown(self) -> None:
        self._client.shutdown()


class LangfuseSpanWrapper:
    """
    Wraps a Langfuse TraceObservation and exposes the same interface as
    NoOpObservation so spans opened from a real client are called the same
    way as spans opened from a no-op client.
    """

    is_noop = False

    def __init__(self, trace):
        self._trace = trace

    def update(self, **kwargs) -> LangfuseSpanWrapper:
        self._trace.update(**kwargs)
        return self

    def score(self, **kwargs) -> LangfuseSpanWrapper:
        self._trace.score(**kwargs)
        return self

    def score_trace(self, **kwargs) -> LangfuseSpanWrapper:
        self._trace.score_trace(**kwargs)
        return self

    def start_span(self, name: str, **kwargs) -> LangfuseSpanWrapper:
        child = self._trace.start_as_current_observation(name=name, **kwargs)
        return LangfuseSpanWrapper(child)

    def end(self) -> None:
        self._trace.end()


def build_observability_client(config):
    """
    Factory that returns either a real Langfuse client or a no-op,
    depending on the LANGFUSE_ENABLED setting.

    Args:
        config: Config class instance (only used to pass to the real client).

    Returns:
        Either LangfuseObservabilityClient or NoOpObservabilityClient.
    """
    explicit_enabled = os.environ.get("LANGFUSE_ENABLED")
    if explicit_enabled is not None:
        enabled = explicit_enabled.lower() == "true"
    elif config is not None:
        enabled = bool(getattr(config, "LANGFUSE_ENABLED", False))
    else:
        enabled = False

    if not enabled or config is None:
        return NoOpObservabilityClient()

    # Process env overrides config; config provides .env-backed fallback.
    host = (os.environ.get("LANGFUSE_HOST") or getattr(config, "LANGFUSE_HOST", "") or "").strip()
    public_key = (os.environ.get("LANGFUSE_PUBLIC_KEY") or getattr(config, "LANGFUSE_PUBLIC_KEY", "") or "").strip()
    secret_key = (os.environ.get("LANGFUSE_SECRET_KEY") or getattr(config, "LANGFUSE_SECRET_KEY", "") or "").strip()

    if not host:
        logger.warning(
            "LANGFUSE_ENABLED=true but LANGFUSE_HOST is not set — using no-op client"
        )
        return NoOpObservabilityClient()
    if not public_key or not secret_key:
        logger.warning(
            "LANGFUSE_ENABLED=true but credentials are missing — using no-op client"
        )
        return NoOpObservabilityClient()

    try:
        return LangfuseObservabilityClient(config)
    except ModuleNotFoundError as e:
        logger.warning(
            "LANGFUSE_ENABLED=true but langfuse SDK is not installed — using no-op client: %s",
            e,
        )
        return NoOpObservabilityClient()

# Langfuse Report Observability Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add self-hosted Langfuse tracing to Quark's report-generation pipeline so every report run, section iteration, tool call, retry, and integrity outcome can be debugged from structured traces instead of raw JSONL alone.

**Architecture:** A new backend observability facade wraps the Langfuse Python SDK and exposes a no-op fallback when disabled. `LLMClient` records each OpenAI-compatible completion as a generation, while `ReportAgent` opens a root trace per `report_id` and nests spans for planning, section generation, tool calls, retries, and integrity scoring.

**Tech Stack:** Flask, OpenAI Python SDK, Langfuse Python SDK, python-dotenv, pytest, uv

---

## Prerequisites

Before starting, verify these are available:
- Python 3.11+
- `uv`
- Access to the self-hosted Langfuse base URL
- Langfuse public/secret keys for dev or staging

Install backend dependencies before the first test run:

```bash
cd backend && uv sync
```

---

## Task 1: Add Langfuse dependency and environment plumbing

**Files:**
- Modify: `backend/pyproject.toml`
- Modify: `backend/uv.lock`
- Modify: `.env.example`
- Modify: `backend/app/config.py`
- Create: `backend/tests/config/test_langfuse_config.py`

**Step 1: Write the failing config test**

Create `backend/tests/config/test_langfuse_config.py` with cases for disabled and enabled modes:

```python
from app.config import Config


def test_langfuse_disabled_does_not_require_credentials(monkeypatch):
    monkeypatch.setenv("LANGFUSE_ENABLED", "false")
    monkeypatch.delenv("LANGFUSE_PUBLIC_KEY", raising=False)
    monkeypatch.delenv("LANGFUSE_SECRET_KEY", raising=False)

    errors = Config.validate()

    assert all("LANGFUSE" not in error for error in errors)


def test_langfuse_enabled_requires_host_and_keys(monkeypatch):
    monkeypatch.setenv("LANGFUSE_ENABLED", "true")
    monkeypatch.delenv("LANGFUSE_HOST", raising=False)
    monkeypatch.delenv("LANGFUSE_PUBLIC_KEY", raising=False)
    monkeypatch.delenv("LANGFUSE_SECRET_KEY", raising=False)

    errors = Config.validate()

    assert "LANGFUSE_HOST not configured" in errors
    assert "LANGFUSE_PUBLIC_KEY not configured" in errors
    assert "LANGFUSE_SECRET_KEY not configured" in errors
```

**Step 2: Run the test to verify it fails**

Run:

```bash
cd backend && uv run pytest tests/config/test_langfuse_config.py -q
```

Expected: FAIL because Langfuse config fields are not implemented.

**Step 3: Add dependency and config fields**

Update `backend/pyproject.toml` to include `langfuse` in `dependencies`, then refresh the lockfile:

```bash
cd backend && uv lock
```

Update `.env.example` with:

```dotenv
LANGFUSE_ENABLED=false
LANGFUSE_HOST=http://localhost:3000
LANGFUSE_PUBLIC_KEY=pk-lf-your-public-key
LANGFUSE_SECRET_KEY=sk-lf-your-secret-key
LANGFUSE_ENV=development
LANGFUSE_RELEASE=local
LANGFUSE_DEBUG=false
LANGFUSE_SAMPLE_RATE=1.0
```

Extend `backend/app/config.py` with:

```python
LANGFUSE_ENABLED = os.environ.get("LANGFUSE_ENABLED", "false").lower() == "true"
LANGFUSE_HOST = os.environ.get("LANGFUSE_HOST")
LANGFUSE_PUBLIC_KEY = os.environ.get("LANGFUSE_PUBLIC_KEY")
LANGFUSE_SECRET_KEY = os.environ.get("LANGFUSE_SECRET_KEY")
LANGFUSE_ENV = os.environ.get("LANGFUSE_ENV", "development")
LANGFUSE_RELEASE = os.environ.get("LANGFUSE_RELEASE", "local")
LANGFUSE_DEBUG = os.environ.get("LANGFUSE_DEBUG", "false").lower() == "true"
LANGFUSE_SAMPLE_RATE = float(os.environ.get("LANGFUSE_SAMPLE_RATE", "1.0"))
```

And add conditional validation inside `Config.validate()`.

**Step 4: Run the tests to verify they pass**

Run:

```bash
cd backend && uv run pytest tests/config/test_langfuse_config.py -q
```

Expected: PASS.

**Step 5: Commit**

```bash
git add backend/pyproject.toml backend/uv.lock .env.example backend/app/config.py backend/tests/config/test_langfuse_config.py
git commit -m "feat(observability): add langfuse config plumbing"
```

---

## Task 2: Create a backend observability facade with no-op fallback

**Files:**
- Create: `backend/app/observability/__init__.py`
- Create: `backend/app/observability/langfuse_client.py`
- Create: `backend/app/observability/reporting.py`
- Create: `backend/tests/observability/test_langfuse_client.py`

**Step 1: Write the failing facade tests**

Create `backend/tests/observability/test_langfuse_client.py`:

```python
from app.observability.langfuse_client import build_observability_client


class DummyConfig:
    LANGFUSE_ENABLED = False
    LANGFUSE_HOST = None
    LANGFUSE_PUBLIC_KEY = None
    LANGFUSE_SECRET_KEY = None
    LANGFUSE_ENV = "test"
    LANGFUSE_RELEASE = "test-release"
    LANGFUSE_DEBUG = False
    LANGFUSE_SAMPLE_RATE = 1.0


def test_disabled_client_returns_noop_client():
    client = build_observability_client(DummyConfig)

    trace = client.start_report_trace(name="report_generation", session_id="report_123", metadata={})

    assert client.is_enabled is False
    assert trace.is_noop is True


def test_noop_client_supports_flush_and_shutdown():
    client = build_observability_client(DummyConfig)

    client.flush()
    client.shutdown()
```

**Step 2: Run the tests to verify they fail**

Run:

```bash
cd backend && uv run pytest tests/observability/test_langfuse_client.py -q
```

Expected: FAIL because the observability module does not exist.

**Step 3: Implement the facade**

Create `backend/app/observability/langfuse_client.py` with two modes:

- `LangfuseObservabilityClient` for real SDK wiring
- `NoOpObservabilityClient` for disabled mode

Minimum API surface:

```python
class NoOpObservation:
    is_noop = True
    def update(self, **kwargs): return self
    def score(self, **kwargs): return None
    def score_trace(self, **kwargs): return None
    def start_span(self, name: str, **kwargs): return NoOpObservation()
    def end(self): return None


class NoOpObservabilityClient:
    is_enabled = False
    def start_report_trace(self, name: str, session_id: str, metadata: dict):
        return NoOpObservation()
    def flush(self): return None
    def shutdown(self): return None
```

Create the real client with Langfuse SDK initialization:

```python
from langfuse import Langfuse

self.client = Langfuse(
    public_key=config.LANGFUSE_PUBLIC_KEY,
    secret_key=config.LANGFUSE_SECRET_KEY,
    base_url=config.LANGFUSE_HOST,
    environment=config.LANGFUSE_ENV,
    release=config.LANGFUSE_RELEASE,
    sample_rate=config.LANGFUSE_SAMPLE_RATE,
    debug=config.LANGFUSE_DEBUG,
)
```

Expose `build_observability_client()` from `backend/app/observability/__init__.py`.

Add `backend/app/observability/reporting.py` helpers for:
- `build_report_metadata(...)`
- `score_integrity(observation, result, fallback_used, retry_count, tool_calls_count)`

**Step 4: Run the tests to verify they pass**

Run:

```bash
cd backend && uv run pytest tests/observability/test_langfuse_client.py -q
```

Expected: PASS.

**Step 5: Commit**

```bash
git add backend/app/observability/__init__.py backend/app/observability/langfuse_client.py backend/app/observability/reporting.py backend/tests/observability/test_langfuse_client.py
git commit -m "feat(observability): add langfuse facade and noop client"
```

---

## Task 3: Initialize and shut down observability with the Flask app lifecycle

**Files:**
- Modify: `backend/app/__init__.py`
- Create: `backend/tests/test_app_observability.py`

**Step 1: Write the failing app lifecycle tests**

Create `backend/tests/test_app_observability.py`:

```python
from app import create_app
from app.config import Config


def test_app_exposes_observability_client(monkeypatch):
    monkeypatch.setattr(Config, "LANGFUSE_ENABLED", False)

    app = create_app()

    assert "OBSERVABILITY_CLIENT" in app.config


def test_health_endpoint_still_works_with_observability(monkeypatch):
    monkeypatch.setattr(Config, "LANGFUSE_ENABLED", False)
    app = create_app()
    client = app.test_client()

    response = client.get("/health")

    assert response.status_code == 200
    assert response.get_json()["status"] == "ok"
```

**Step 2: Run the tests to verify they fail**

Run:

```bash
cd backend && uv run pytest tests/test_app_observability.py -q
```

Expected: FAIL because the app factory does not wire the observability client.

**Step 3: Wire app startup and shutdown**

In `backend/app/__init__.py`:

- build the client once with `build_observability_client(Config)`
- store it in `app.config["OBSERVABILITY_CLIENT"]`
- log whether Langfuse is enabled and which host/environment are being used
- register shutdown hooks with `atexit` or Flask teardown-safe logic that calls:

```python
observability_client.flush()
observability_client.shutdown()
```

Do not break existing startup behavior or simulation cleanup.

**Step 4: Run the tests to verify they pass**

Run:

```bash
cd backend && uv run pytest tests/test_app_observability.py -q
```

Expected: PASS.

**Step 5: Commit**

```bash
git add backend/app/__init__.py backend/tests/test_app_observability.py
git commit -m "feat(observability): wire langfuse lifecycle into flask app"
```

---

## Task 4: Instrument `LLMClient.chat()` as a Langfuse generation

**Files:**
- Modify: `backend/app/utils/llm_client.py`
- Create: `backend/tests/utils/test_llm_client_observability.py`

**Step 1: Write the failing `chat()` observability tests**

Create `backend/tests/utils/test_llm_client_observability.py` with fakes:

```python
from app.utils.llm_client import LLMClient


class FakeGeneration:
    def __init__(self):
        self.updates = []
        self.ended = False
    def update(self, **kwargs):
        self.updates.append(kwargs)
        return self
    def end(self):
        self.ended = True


class FakeObservation:
    def __init__(self):
        self.generations = []
    def start_generation(self, name, **kwargs):
        generation = FakeGeneration()
        self.generations.append((name, kwargs, generation))
        return generation


def test_chat_records_generation_metadata(monkeypatch):
    fake_observation = FakeObservation()
    client = LLMClient(api_key="x", base_url="http://example", model="demo-model")
    client.client = type("FakeOpenAI", (), {
        "chat": type("Chat", (), {
            "completions": type("Completions", (), {
                "create": staticmethod(lambda **kwargs: type("Resp", (), {
                    "choices": [type("Choice", (), {"message": type("Msg", (), {"content": "hello"})()})],
                    "usage": type("Usage", (), {"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15})(),
                })())
            })
        })
    })

    result = client.chat(
        messages=[{"role": "user", "content": "hi"}],
        observation=fake_observation,
        generation_name="report-section"
    )

    assert result == "hello"
    assert fake_observation.generations[0][0] == "report-section"
    assert fake_observation.generations[0][2].ended is True
```

Add a second test for exception recording.

**Step 2: Run the tests to verify they fail**

Run:

```bash
cd backend && uv run pytest tests/utils/test_llm_client_observability.py -q
```

Expected: FAIL because `LLMClient.chat()` does not accept observability context.

**Step 3: Add generation instrumentation**

Extend `LLMClient.chat()` signature:

```python
def chat(self, messages, temperature=0.7, max_tokens=4096, response_format=None, observation=None, generation_name=None, generation_metadata=None):
```

Behavior:
- when `observation` is provided, call `observation.start_generation(...)`
- attach `model`, `input`, `metadata`, and request parameters
- measure latency with `time.perf_counter()`
- on success, update generation with output and usage details
- on failure, update generation with error status and re-raise
- always `end()` the generation if it exists

Use a safe name fallback such as `generation_name or "llm_chat"`.

**Step 4: Run the tests to verify they pass**

Run:

```bash
cd backend && uv run pytest tests/utils/test_llm_client_observability.py -q
```

Expected: PASS.

**Step 5: Commit**

```bash
git add backend/app/utils/llm_client.py backend/tests/utils/test_llm_client_observability.py
git commit -m "feat(observability): trace llm client chat generations"
```

---

## Task 5: Instrument `LLMClient.chat_json()` and JSON-mode retries

**Files:**
- Modify: `backend/app/utils/llm_client.py`
- Modify: `backend/tests/utils/test_llm_client_observability.py`

**Step 1: Write the failing `chat_json()` tests**

Add tests that verify:
- `chat_json()` forwards the same `observation`, `generation_name`, and metadata into `chat()`
- malformed JSON still produces a traced failure before raising `ValueError`

Example test:

```python
def test_chat_json_forwards_observation(monkeypatch):
    client = LLMClient(api_key="x", base_url="http://example", model="demo-model")
    calls = []

    def fake_chat(**kwargs):
        calls.append(kwargs)
        return '{"ok": true}'

    monkeypatch.setattr(client, "chat", fake_chat)

    result = client.chat_json(
        messages=[{"role": "user", "content": "hi"}],
        observation="obs",
        generation_name="outline-json"
    )

    assert result == {"ok": True}
    assert calls[0]["observation"] == "obs"
    assert calls[0]["generation_name"] == "outline-json"
```

**Step 2: Run the tests to verify they fail**

Run:

```bash
cd backend && uv run pytest tests/utils/test_llm_client_observability.py -q
```

Expected: FAIL because `chat_json()` does not accept observability parameters.

**Step 3: Implement the forwarding and failure path**

Update `chat_json()` signature to accept the same observability parameters and pass them through to `chat()`. For JSON decode failure, do not swallow the error; let the traced generation show invalid JSON output and then raise `ValueError`.

**Step 4: Run the tests to verify they pass**

Run:

```bash
cd backend && uv run pytest tests/utils/test_llm_client_observability.py -q
```

Expected: PASS.

**Step 5: Commit**

```bash
git add backend/app/utils/llm_client.py backend/tests/utils/test_llm_client_observability.py
git commit -m "feat(observability): trace llm client json generations"
```

---

## Task 6: Add a root report trace and planning span in `ReportAgent.generate_report()`

**Files:**
- Modify: `backend/app/services/report_agent.py`
- Create: `backend/tests/services/test_report_agent_observability.py`

**Step 1: Write the failing trace-root tests**

Create `backend/tests/services/test_report_agent_observability.py` with fake observability objects:

```python
from app.services.report_agent import ReportAgent, ReportOutline, ReportSection


class FakeSpan:
    def __init__(self, name="root"):
        self.name = name
        self.children = []
        self.scored = []
        self.updated = []
        self.ended = False
    def start_span(self, name, **kwargs):
        child = FakeSpan(name)
        self.children.append((name, kwargs, child))
        return child
    def update(self, **kwargs):
        self.updated.append(kwargs)
        return self
    def score(self, **kwargs):
        self.scored.append(kwargs)
    def score_trace(self, **kwargs):
        self.scored.append({"trace": True, **kwargs})
    def end(self):
        self.ended = True


class FakeObservabilityClient:
    is_enabled = True
    def __init__(self):
        self.traces = []
    def start_report_trace(self, name, session_id, metadata):
        span = FakeSpan(name)
        self.traces.append((name, session_id, metadata, span))
        return span
    def flush(self):
        pass
    def shutdown(self):
        pass
```

Test that `generate_report(report_id="report_123")` opens a root trace with the expected metadata.

**Step 2: Run the tests to verify they fail**

Run:

```bash
cd backend && uv run pytest tests/services/test_report_agent_observability.py -q
```

Expected: FAIL because `ReportAgent` does not accept or create observability traces.

**Step 3: Add root trace plumbing**

Modify `ReportAgent.__init__()` to accept an optional `observability_client`. If none is passed, resolve the default facade inside the class or inject it from the caller later.

In `generate_report()`:
- create a root trace immediately after `report_id` is known
- attach report metadata with `build_report_metadata(...)`
- wrap outline planning in `root_trace.start_span("plan_outline", ...)`
- ensure `end()` runs for spans/traces in both success and failure paths

Minimal shape:

```python
root_trace = self.observability.start_report_trace(
    name="report_generation",
    session_id=report_id,
    metadata=build_report_metadata(...),
)
planning_span = root_trace.start_span("plan_outline", metadata={...})
```

**Step 4: Run the tests to verify they pass**

Run:

```bash
cd backend && uv run pytest tests/services/test_report_agent_observability.py -q
```

Expected: PASS.

**Step 5: Commit**

```bash
git add backend/app/services/report_agent.py backend/tests/services/test_report_agent_observability.py
git commit -m "feat(observability): add root report trace and planning span"
```

---

## Task 7: Trace section iterations, tool calls, retries, and integrity scoring

**Files:**
- Modify: `backend/app/services/report_agent.py`
- Modify: `backend/app/observability/reporting.py`
- Modify: `backend/tests/services/test_report_agent_observability.py`

**Step 1: Write the failing section/tool scoring tests**

Add tests covering:
- each section creates a `generate_section` span
- each tool execution creates a `tool_call` span with tool name and iteration
- language guard or contract conflicts record retry metadata
- `_validate_persisted_output()` results produce scores via `score_integrity(...)`

Example assertion targets:

```python
assert any(name == "generate_section" for name, _, _ in root_span.children)
assert any(name == "tool_call" for name, _, _ in section_span.children)
assert any(score["name"] == "language_integrity_ok" for score in section_span.scored)
```

**Step 2: Run the tests to verify they fail**

Run:

```bash
cd backend && uv run pytest tests/services/test_report_agent_observability.py -q
```

Expected: FAIL because section/tool spans and scores are not recorded.

**Step 3: Implement span nesting and scoring**

In `_generate_section_react()`:
- create one `generate_section` span per section
- pass the section span as `observation` to `self.llm.chat(...)`
- create child `tool_call` spans around `_execute_tool(...)`
- record retry/conflict metadata via `section_span.update(...)`

After `_validate_persisted_output(...)` and `_sanitize_chat_response(...)`, call `score_integrity(...)` with:
- `result.ok`
- forbidden category count
- entity drift count
- missing entity count
- suspect term count
- `fallback_used`
- `retry_count`
- `tool_calls_count`

Also score `tool_contract_respected=False` when a response contains both tool call and `Final Answer:`.

**Step 4: Run the tests to verify they pass**

Run:

```bash
cd backend && uv run pytest tests/services/test_report_agent_observability.py -q
```

Expected: PASS.

**Step 5: Commit**

```bash
git add backend/app/services/report_agent.py backend/app/observability/reporting.py backend/tests/services/test_report_agent_observability.py
git commit -m "feat(observability): trace report sections tools and integrity scores"
```

---

## Task 8: Trace report chat generations without breaking current chat behavior

**Files:**
- Modify: `backend/app/services/report_agent.py`
- Modify: `backend/tests/services/test_report_agent_observability.py`

**Step 1: Write the failing chat tracing tests**

Add tests that verify `ReportAgent.chat()`:
- opens a lightweight trace or span for chat interactions
- forwards an observation into `_generate_with_language_guard()` / `self.llm.chat()`
- preserves current response payload shape (`response`, `tool_calls`, `sources`)

Example expectation:

```python
result = agent.chat(message="What changed?", chat_history=[])
assert "response" in result
assert fake_observability_client.traces[-1][0] == "report_chat"
```

**Step 2: Run the tests to verify they fail**

Run:

```bash
cd backend && uv run pytest tests/services/test_report_agent_observability.py -q
```

Expected: FAIL because chat tracing is not implemented.

**Step 3: Implement chat tracing**

Use a small trace name such as `report_chat` with metadata:
- `simulation_id`
- `graph_id`
- `message_length`
- `history_count`

Do not persist full report generation spans here; keep chat traces separate from report generation traces.

**Step 4: Run the tests to verify they pass**

Run:

```bash
cd backend && uv run pytest tests/services/test_report_agent_observability.py -q
```

Expected: PASS.

**Step 5: Commit**

```bash
git add backend/app/services/report_agent.py backend/tests/services/test_report_agent_observability.py
git commit -m "feat(observability): trace report agent chat interactions"
```

---

## Task 9: Verify enabled and disabled modes end-to-end

**Files:**
- Modify: `backend/tests/services/test_report_agent_observability.py`
- Modify: `backend/tests/utils/test_llm_client_observability.py`
- Optional Create: `backend/tests/observability/test_smoke_mode_switch.py`

**Step 1: Write the failing mode-switch smoke tests**

Add tests that prove:
- disabled mode uses the no-op client and still completes report generation logic
- enabled mode can use a fake Langfuse client and collect traces without contacting the network

Example:

```python
def test_report_generation_still_runs_with_noop_observability(...):
    agent = ReportAgent(..., observability_client=NoOpObservabilityClient())
    report = agent.generate_report(report_id="report_test")
    assert report.status.value in {"completed", "failed"}
```

Use stubs/mocks so the test does not call real Zep or LLM endpoints.

**Step 2: Run the tests to verify they fail**

Run:

```bash
cd backend && uv run pytest tests/observability tests/utils/test_llm_client_observability.py tests/services/test_report_agent_observability.py tests/test_app_observability.py -q
```

Expected: FAIL until mode-switch behavior is covered completely.

**Step 3: Implement or tighten the missing code paths**

Fix any gaps in:
- no-op behavior
- root trace cleanup
- score helpers
- generation teardown on exceptions
- chat/report separation

Do not add network-dependent tests.

**Step 4: Run the full backend verification**

Run:

```bash
cd backend && uv run pytest tests/observability tests/config tests/utils/test_llm_client_observability.py tests/services/test_report_agent_observability.py tests/test_app_observability.py -q
```

Expected: PASS.

Then run the project-level build check:

```bash
npm run build
```

Expected: PASS.

**Step 5: Commit**

```bash
git add backend/tests/observability backend/tests/config backend/tests/utils/test_llm_client_observability.py backend/tests/services/test_report_agent_observability.py backend/tests/test_app_observability.py
git commit -m "test(observability): verify langfuse enabled and disabled modes"
```

---

## Manual Smoke Checklist

After the coded tasks pass, run one manual smoke test with Langfuse disabled and one with it enabled.

### Disabled mode

```bash
cd backend && LANGFUSE_ENABLED=false uv run python run.py
```

Expected:
- backend starts normally
- `/health` returns `{"status":"ok","service":"FUTUR.IA Backend"}`
- report endpoints still behave exactly as before

### Enabled mode

```bash
cd backend && \
LANGFUSE_ENABLED=true \
LANGFUSE_HOST=http://<self-hosted-langfuse> \
LANGFUSE_PUBLIC_KEY=pk-lf-... \
LANGFUSE_SECRET_KEY=sk-lf-... \
LANGFUSE_ENV=development \
LANGFUSE_RELEASE=local-smoke \
uv run python run.py
```

Generate one report from the UI or API.

Expected in Langfuse:
- one `report_generation` trace keyed by `report_id`
- one `plan_outline` span
- one `generate_section` span per section
- nested `tool_call` spans
- generation entries for each `LLMClient` call
- integrity scores attached to spans or traces

---

## Rollout Notes

- Keep `agent_log.jsonl` and `console_log.txt` during the first rollout.
- Do not instrument the whole simulation stack in this branch.
- Do not add prompt management workflows yet.
- If trace payload size becomes a problem, add truncation/redaction in a follow-up branch rather than weakening the first integration silently.

---

## Final Verification Checklist

- [ ] `Config.validate()` enforces Langfuse settings only when enabled
- [ ] App factory wires one observability client and shuts it down cleanly
- [ ] `LLMClient.chat()` traces completions, usage, latency, and errors
- [ ] `LLMClient.chat_json()` preserves trace linkage and invalid JSON failures
- [ ] `ReportAgent.generate_report()` creates a root trace per `report_id`
- [ ] Section/tool/retry spans appear in Langfuse
- [ ] Integrity outcomes are scored from `language_integrity.py`
- [ ] Report chat tracing is separate from report generation tracing
- [ ] Backend tests pass with fake/no-op clients only
- [ ] `npm run build` passes

---

**Plan complete and saved to `docs/plans/2026-04-17-langfuse-report-observability.md`.**

**Two execution options:**

**1. Subagent-Driven (this session)** - I dispatch fresh subagent per task, review between tasks, fast iteration

**2. Parallel Session (separate)** - Open new session with executing-plans, batch execution with checkpoints

Which approach?

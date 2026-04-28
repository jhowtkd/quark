# Langfuse Report Observability Design

**Date:** 2026-04-17  
**Author:** Brainstorming Session  
**Status:** Approved

---

## Overview

Add Langfuse as a self-hosted observability layer for Quark's LLM-driven reporting pipeline. The integration focuses on `backend/app/utils/llm_client.py` and `backend/app/services/report_agent.py`, preserving current behavior while making prompts, tool calls, retries, outputs, costs, latency, and integrity scores traceable in one place.

The goal is not to instrument the whole product. The goal is to make report generation and report chat diagnosable without opening raw artifact files first.

---

## Scope

### In scope

- Self-hosted Langfuse deployment as internal LLM observability
- Full payload tracing: prompts, outputs, tool inputs/outputs, metadata
- Root trace per report generation
- Nested spans for planning, sections, tool calls, retries, and persistence boundaries where useful
- Generation-level tracing for all `LLMClient` calls
- Scores derived from existing language integrity rules
- Environment and release tagging
- Graceful no-op behavior when Langfuse is disabled

### Out of scope

- Instrumenting the full simulation subsystem
- Replacing Zep, existing report artifacts, or Flask request logging
- Removing `agent_log.jsonl` or `console_log.txt` in the first iteration
- Prompt management workflows beyond trace capture and metadata

---

## Architecture

```text
Flask backend
├── Config/env
├── Observability facade (new)
│   ├── Langfuse client bootstrap
│   ├── no-op fallback when disabled
│   ├── trace/span/generation helpers
│   └── score helpers
├── LLMClient
│   └── generation tracing for all OpenAI-compatible calls
└── ReportAgent
    ├── root trace per report_id
    ├── spans per planning/section/tool/retry stage
    └── integrity scores attached to traces/observations

Langfuse self-hosted
└── Stores full traces, metadata, scores, latency, and usage
```

The backend should call a local observability facade instead of scattering SDK calls across business logic. Langfuse remains infrastructure; the reporting code remains the system of record for behavior.

---

## Trace Model

### Root trace

One root trace per report generation:

- `name`: `report_generation`
- `session_id`: `report_id`
- metadata:
  - `report_id`
  - `simulation_id`
  - `graph_id`
  - `simulation_requirement`
  - `llm_model`
  - `llm_base_url`
  - `langfuse_env`
  - `langfuse_release`

### Core spans

- `plan_outline`
- `generate_section`
- `tool_call`
- `language_guard`
- `persist_report_artifact` (optional first cut, useful second cut)

### Generations

Every `LLMClient.chat()` and `LLMClient.chat_json()` call becomes a Langfuse generation that records:

- full `messages`
- `model`
- `temperature`
- `max_tokens`
- `response_format`
- output text
- error state
- latency
- usage/token information when returned by the model provider

---

## Metadata and Scores

### Operational metadata

The integration should persist metadata needed for debugging real failures:

- `section_index`
- `section_title`
- `iteration`
- `tool_calls_count`
- `used_tools`
- `max_tool_calls`
- `has_tool_calls`
- `has_final_answer`
- `fallback_used`
- `conflict_retry_count`
- `response_length`
- `result_length`

### Scores

Langfuse scores should be derived from `backend/app/utils/language_integrity.py` instead of inventing a second policy layer.

Minimum scores:

- `language_integrity_ok` (boolean)
- `forbidden_scripts_detected` (boolean)
- `fallback_used` (boolean)
- `tool_contract_respected` (boolean)
- `entity_drift_count` (numeric)
- `missing_entities_count` (numeric)
- `suspect_terms_count` (numeric)
- `tool_calls_count` (numeric)
- `retry_count` (numeric)
- `report_surface_health` (numeric aggregate for comparison only)

---

## Security and Data Handling

This design assumes a self-hosted Langfuse instance approved to receive complete reporting payloads.

Allowed payloads:

- prompts
- model outputs
- tool inputs/outputs
- simulation/report metadata
- integrity score payloads

Still excluded:

- `.env` contents
- API keys and provider secrets
- raw auth headers
- operational credentials unrelated to report payloads

---

## Configuration

Add these backend env vars:

- `LANGFUSE_ENABLED`
- `LANGFUSE_HOST`
- `LANGFUSE_PUBLIC_KEY`
- `LANGFUSE_SECRET_KEY`
- `LANGFUSE_ENV`
- `LANGFUSE_RELEASE`
- `LANGFUSE_DEBUG`
- `LANGFUSE_SAMPLE_RATE`

When `LANGFUSE_ENABLED=false`, observability should degrade to a no-op client with zero behavior change.

---

## Rollout Plan

### Phase 1
- dependency + env plumbing
- observability facade
- `LLMClient` generation tracing

### Phase 2
- root trace and section/tool spans in `ReportAgent`

### Phase 3
- integrity scoring and release/env comparisons

### Phase 4
- operational hardening, dashboards, lifecycle flush/shutdown, reduced dependence on raw logs

---

## Definition of Done

The work is done when a real report generation can be inspected in Langfuse and answers all of these without opening raw files first:

1. Which prompt/model generated the bad output?
2. In which section and iteration did it happen?
3. Which tools ran before the failure?
4. Was there a language-guard retry or fallback?
5. What did it cost, and how long did it take?
6. Which release introduced the regression?

The current local artifacts remain in place during the first rollout.

---

## Next Step

Create an implementation plan focused on:

- config and dependency wiring
- observability facade
- `LLMClient` instrumentation
- `ReportAgent` tracing and scores
- app lifecycle flush/shutdown
- automated tests and smoke verification

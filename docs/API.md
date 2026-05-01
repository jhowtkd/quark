<!-- generated-by: gsd-doc-writer -->
# FUTUR.IA API Reference

This document describes the HTTP API surface of the FUTUR.IA backend. All endpoints are served by the Flask application factory (`backend/app/__init__.py`).

## Base URL

The backend runs on `http://localhost:5000` by default in development.

All API routes are prefixed with `/api` unless otherwise noted. The health endpoint is at `/health`.

## Authentication

The API does not implement request-level authentication (no API keys, JWT, or session cookies are required). CORS is configured to allow all origins for `/api/*` routes:

```python
CORS(app, resources={r"/api/*": {"origins": "*"}})
```

Server-side credentials (LLM API keys, Zep API keys) are read from environment variables or the `.env` file and are never exposed to clients.

## Request / Response Formats

### Standard JSON Envelope

Every JSON response follows a consistent envelope:

```json
{
  "success": true,
  "data": { ... },
  "count": 42,
  "message": "..."
}
```

| Field      | Type    | Description                                      |
|------------|---------|--------------------------------------------------|
| `success`  | boolean | `true` on success, `false` on error              |
| `data`     | object  | Payload (schema varies by endpoint)              |
| `count`    | integer | Present on list endpoints                        |
| `message`  | string  | Human-readable status or confirmation            |
| `error`    | string  | Present when `success` is `false`                |
| `traceback`| string  | Present on unhandled 500 errors (dev mode)       |

### File Uploads

The ontology generation endpoint accepts `multipart/form-data`:

```
POST /api/graph/ontology/generate
Content-Type: multipart/form-data

files: <binary>
simulation_requirement: <text>
project_name: <text> (optional)
additional_context: <text> (optional)
```

### Query Parameters

List endpoints support standard query parameters for pagination and filtering:

| Parameter | Type    | Default | Description           |
|-----------|---------|---------|-----------------------|
| `limit`   | integer | 50      | Maximum items to return |
| `offset`  | integer | 0       | Items to skip         |

## Endpoints Overview

### Health

| Method | Path        | Auth Required | Description          |
|--------|-------------|---------------|----------------------|
| GET    | `/health`   | No            | Service health check |

### Graph (`/api/graph`)

| Method | Path                                          | Auth Required | Description                                  |
|--------|-----------------------------------------------|---------------|----------------------------------------------|
| GET    | `/api/graph/project/<project_id>`             | No            | Get project details                          |
| GET    | `/api/graph/project/list`                     | No            | List all projects                            |
| DELETE | `/api/graph/project/<project_id>`             | No            | Delete a project                             |
| POST   | `/api/graph/project/<project_id>/reset`       | No            | Reset project status for rebuild             |
| POST   | `/api/graph/ontology/generate`                | No            | Upload files and generate ontology (async)   |
| POST   | `/api/graph/ontology/generate-from-text/<project_id>` | No    | Generate ontology from existing extracted text |
| POST   | `/api/graph/build`                            | No            | Build knowledge graph (async task)           |
| GET    | `/api/graph/task/<task_id>`                   | No            | Get async task status                        |
| GET    | `/api/graph/tasks`                            | No            | List all tasks                               |
| GET    | `/api/graph/data/<graph_id>`                  | No            | Get graph nodes and edges from Zep           |
| DELETE | `/api/graph/delete/<graph_id>`                | No            | Delete graph from Zep                        |

### Simulation (`/api/simulation`)

| Method | Path                                                   | Auth Required | Description                              |
|--------|--------------------------------------------------------|---------------|------------------------------------------|
| GET    | `/api/simulation/entities/<graph_id>`                  | No            | Get filtered entities from a graph       |
| GET    | `/api/simulation/entities/<graph_id>/<entity_uuid>`    | No            | Get single entity details                |
| GET    | `/api/simulation/entities/<graph_id>/by-type/<entity_type>` | No      | Get entities by type                     |
| POST   | `/api/simulation/create`                               | No            | Create a new simulation                  |
| POST   | `/api/simulation/prepare`                              | No            | Prepare simulation environment (async)   |
| POST   | `/api/simulation/prepare/status`                       | No            | Query prepare task progress              |
| GET    | `/api/simulation/<simulation_id>`                      | No            | Get simulation state                     |
| GET    | `/api/simulation/list`                                 | No            | List simulations                         |
| GET    | `/api/simulation/history`                              | No            | Get enriched simulation history          |
| GET    | `/api/simulation/<simulation_id>/profiles`             | No            | Get Agent profiles                       |
| GET    | `/api/simulation/<simulation_id>/profiles/realtime`    | No            | Real-time profile read (during generation) |
| GET    | `/api/simulation/<simulation_id>/config/realtime`      | No            | Real-time config read (during generation) |
| GET    | `/api/simulation/<simulation_id>/config`               | No            | Get full simulation config               |
| GET    | `/api/simulation/<simulation_id>/config/download`      | No            | Download `simulation_config.json`        |
| GET    | `/api/simulation/script/<script_name>/download`        | No            | Download runner scripts                  |
| POST   | `/api/simulation/generate-profiles`                    | No            | Generate profiles without creating sim   |
| POST   | `/api/simulation/start`                                | No            | Start simulation runner                  |
| POST   | `/api/simulation/stop`                                 | No            | Stop simulation runner                   |
| GET    | `/api/simulation/<simulation_id>/run-status`           | No            | Get runner status (polling)              |
| GET    | `/api/simulation/<simulation_id>/run-status/detail`    | No            | Get runner status with all actions       |
| GET    | `/api/simulation/<simulation_id>/actions`              | No            | Get action history                       |
| GET    | `/api/simulation/<simulation_id>/timeline`             | No            | Get round-by-round timeline              |
| GET    | `/api/simulation/<simulation_id>/agent-stats`          | No            | Get per-agent statistics                 |
| GET    | `/api/simulation/<simulation_id>/posts`                | No            | Get posts from simulation DB             |
| GET    | `/api/simulation/<simulation_id>/comments`             | No            | Get comments from simulation DB          |
| POST   | `/api/simulation/interview`                            | No            | Interview a single agent                 |
| POST   | `/api/simulation/interview/batch`                      | No            | Batch interview agents                   |
| POST   | `/api/simulation/interview/all`                        | No            | Interview all agents with same prompt    |
| POST   | `/api/simulation/interview/history`                    | No            | Get interview history                    |
| POST   | `/api/simulation/env-status`                           | No            | Check if simulation environment is alive |
| POST   | `/api/simulation/close-env`                            | No            | Gracefully close simulation environment  |
| GET    | `/api/simulation/profiles/available`                   | No            | List available analysis profiles         |

### Report (`/api/report`)

| Method | Path                                                   | Auth Required | Description                              |
|--------|--------------------------------------------------------|---------------|------------------------------------------|
| POST   | `/api/report/generate`                                 | No            | Generate report (async)                  |
| POST   | `/api/report/generate/status`                          | No            | Query report generation status           |
| GET    | `/api/report/<report_id>`                              | No            | Get report metadata and content          |
| GET    | `/api/report/by-simulation/<simulation_id>`            | No            | Get report by simulation ID              |
| GET    | `/api/report/list`                                     | No            | List reports                             |
| GET    | `/api/report/<report_id>/download`                     | No            | Download report as Markdown              |
| DELETE | `/api/report/<report_id>`                              | No            | Delete report                            |
| POST   | `/api/report/chat`                                     | No            | Chat with Report Agent                   |
| GET    | `/api/report/<report_id>/progress`                     | No            | Get report generation progress           |
| GET    | `/api/report/<report_id>/sections`                     | No            | Get generated sections                   |
| GET    | `/api/report/<report_id>/section/<section_index>`      | No            | Get single section content               |
| GET    | `/api/report/check/<simulation_id>`                    | No            | Check if report exists and is completed  |
| GET    | `/api/report/<report_id>/agent-log`                    | No            | Get structured agent execution log       |
| GET    | `/api/report/<report_id>/agent-log/stream`             | No            | Stream latest agent log entries          |
| GET    | `/api/report/<report_id>/console-log`                  | No            | Get console/stdout log                   |
| GET    | `/api/report/<report_id>/console-log/stream`           | No            | Stream latest console log entries        |
| POST   | `/api/report/tools/search`                             | No            | Search graph with natural language query |
| POST   | `/api/report/tools/statistics`                         | No            | Get graph statistics                     |

### Deep Research (`/api/research`)

| Method | Path                              | Auth Required | Description                                  |
|--------|-----------------------------------|---------------|----------------------------------------------|
| POST   | `/api/research/start`             | No            | Kick off async deep research                 |
| GET    | `/api/research/status/<run_id>`   | No            | Poll research status and progress            |
| GET    | `/api/research/result/<run_id>`   | No            | Retrieve completed markdown artifact         |
| POST   | `/api/research/approve/<run_id>`  | No            | Approve completed research (fail-closed)     |
| POST   | `/api/research/reject/<run_id>`   | No            | Reject and reset research to pending         |
| POST   | `/api/research/promote/<run_id>`  | No            | Copy draft into project extracted text       |
| POST   | `/api/research/create-project/<run_id>` | No      | Create new project from approved research    |
| POST   | `/api/research/rerun/<run_id>`    | No            | Rerun research with user feedback            |

## Async Task Pattern

Long-running operations (graph build, simulation prepare, report generation, deep research) return immediately with a `task_id`. Poll the corresponding status endpoint to track progress.

**Example — starting a graph build:**

```bash
curl -X POST http://localhost:5000/api/graph/build \
  -H "Content-Type: application/json" \
  -d '{"project_id": "proj_xxxx", "chunk_size": 300, "chunk_overlap": 30}'
```

Response:

```json
{
  "success": true,
  "data": {
    "project_id": "proj_xxxx",
    "task_id": "task_xxxx",
    "message": "Graph build task started"
  }
}
```

**Polling the task:**

```bash
curl http://localhost:5000/api/graph/task/task_xxxx
```

Task status objects include `status`, `progress` (0–100), `message`, and `result` on completion.

## Error Codes

### Standard Error Response

```json
{
  "success": false,
  "error": "Human-readable error message",
  "traceback": "..."  // only in development / unhandled exceptions
}
```

### HTTP Status Codes

| Status | Meaning               | Typical Causes                                               |
|--------|-----------------------|--------------------------------------------------------------|
| 200    | OK                    | Success; some endpoints return `success: false` in body for business errors |
| 400    | Bad Request           | Missing or invalid parameters (e.g., `project_id`, `simulation_id`) |
| 404    | Not Found             | Resource does not exist (project, simulation, task, graph, report) |
| 429    | Too Many Requests     | Zep API rate limit exceeded                                  |
| 500    | Internal Server Error | Unhandled exception or missing server-side configuration     |
| 504    | Gateway Timeout       | Interview or batch operation timed out                       |

### Common Client Errors

- **`requireProjectId`** — `project_id` field is missing from the request body.
- **`requireSimulationId`** — `simulation_id` field is missing.
- **`projectNotFound`** — The requested `project_id` does not exist.
- **`simulationNotFound`** — The requested `simulation_id` does not exist.
- **`ontologyNotGenerated`** — Project exists but ontology has not been generated yet.
- **`graphBuilding`** — A graph build is already in progress for this project.
- **`zepApiKeyMissing`** — The server `ZEP_API_KEY` is not configured.

## Rate Limits

The Flask application does not implement built-in HTTP rate limiting. <!-- VERIFY: no rate limit values from env vars --> There are no per-client request quotas configured in the application layer.

Rate limiting is handled by upstream external services:

- **Zep API** — Returns HTTP 429 when quotas are exceeded. The backend surfaces these as `429` responses with message `"Zep API rate limit exceeded. Please wait a minute and try again."`.
- **LLM Provider** — Rate limits depend on the configured provider (`LLM_BASE_URL`). The backend does not intercept these; they surface as transient errors during async tasks.

## Configuration Required by the Server

The backend reads the following keys from environment variables or `.env`. Clients do not send these.

| Variable            | Purpose                                |
|---------------------|----------------------------------------|
| `LLM_API_KEY`       | LLM provider API key                   |
| `LLM_BASE_URL`      | LLM provider base URL                  |
| `ZEP_API_KEY`       | Zep memory graph API key               |
| `LANGFUSE_ENABLED`  | Toggle observability tracing           |
| `BRAVE_SEARCH_API_KEY` | Deep research search connector      |
| `TAVILY_API_KEY`    | Deep research search connector         |
| `JINA_API_KEY`      | Deep research content extraction       |

<!-- VERIFY: external auth service URLs -->

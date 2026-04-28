# Architecture

## System overview

FUTUR.IA is a two-tier application:

- a **Vue 3 frontend** in `frontend/` for project, graph, simulation, report, and interaction workflows
- a **Flask backend** in `backend/` that exposes the graph, simulation, report, and research APIs

Runtime data is stored on disk under `backend/uploads/`. External systems are plugged in through environment variables rather than hardcoded providers.

## High-level shape

```text
frontend (Vue 3 + Vite)
  -> /api/* proxied to backend during local dev
  -> route-driven 5-step workflow UI

backend (Flask)
  -> /api/graph/*
  -> /api/simulation/*
  -> /api/report/*
  -> /api/research/*
  -> /health

storage
  -> backend/uploads/projects/
  -> backend/uploads/research/
  -> backend/uploads/reports/
  -> backend/uploads/simulations/
```

## Frontend

### Stack

- Vue 3
- Vue Router
- Vue I18n
- Vite
- Axios
- D3

### Frontend structure

Key frontend directories:

- `frontend/src/views/` — route-level screens
- `frontend/src/components/` — shared UI
- `frontend/src/api/` — HTTP clients and local auth helpers
- `frontend/src/router/` — route table and guards
- `frontend/src/store/` — lightweight local state helpers
- `frontend/src/i18n/` — localization wiring

Committed route views include:

- `Home.vue`
- `LoginPage.vue`
- `RegisterPage.vue`
- `MainView.vue`
- `SimulationView.vue`
- `SimulationRunView.vue`
- `ReportView.vue`
- `InteractionView.vue`

### Frontend routing and auth

The router protects the main workflow routes with guards from `frontend/src/router/index.js`.

Important caveat: the committed auth client in `frontend/src/api/auth.js` is a **stub**. It accepts login/register data and stores a mock user in localStorage. The frontend route guards depend on that local state, not on a server-side auth session.

### Development proxy

`frontend/vite.config.js` configures:

- `/api` -> `http://localhost:5001`
- `/auth` -> `http://127.0.0.1:3210`

The committed frontend auth module does not currently use that `/auth` proxy path.

## Backend

### Stack

- Python 3.11+
- Flask
- Flask-CORS
- Pydantic
- python-dotenv

### Application factory

`backend/app/__init__.py` builds the Flask app and wires:

- config loading
- request/response logging
- optional observability client
- CORS for `/api/*`
- simulation cleanup registration
- blueprint registration
- `GET /health`

### Entry point

`backend/run.py`:

- validates required configuration before startup
- creates the Flask app
- runs the server on `FLASK_HOST` / `FLASK_PORT` with threaded mode enabled

## Backend API surface

The backend is split into four blueprint modules:

### `backend/app/api/graph.py` -> `/api/graph/*`

Responsibilities:

- project CRUD and reset
- ontology generation from uploaded files
- ontology generation from existing extracted text
- graph build preview and graph build execution
- task status and graph data retrieval

Notable routes include:

- `GET /api/graph/project/<project_id>`
- `GET /api/graph/project/list`
- `DELETE /api/graph/project/<project_id>`
- `POST /api/graph/project/<project_id>/reset`
- `POST /api/graph/ontology/generate`
- `POST /api/graph/ontology/generate-from-text/<project_id>`
- `POST /api/graph/build`
- `GET /api/graph/task/<task_id>`
- `GET /api/graph/tasks`
- `GET /api/graph/data/<graph_id>`
- `DELETE /api/graph/delete/<graph_id>`

### `backend/app/api/simulation.py` -> `/api/simulation/*`

Responsibilities:

- entity inspection from graph data
- simulation creation
- preparation workflow and status polling
- run lifecycle control and status
- profile/config retrieval
- timeline, posts, comments, interview, and environment endpoints

This is the broadest API module in the repo.

### `backend/app/api/report.py` -> `/api/report/*`

Responsibilities:

- report generation
- report retrieval and download
- report progress/sections/log access
- report chat
- graph search/statistics helper endpoints used by reporting tools

### `backend/app/api/research.py` -> `/api/research/*`

Responsibilities:

- deep research run start/status/result
- approval and rejection
- rerun with feedback
- promotion into project extracted text
- project creation from approved research

The research flow is explicitly asynchronous and uses daemon threads plus task tracking.

## Services and models

Key service modules under `backend/app/services/` include:

- `graph_builder.py`
- `ontology_generator.py`
- `simulation_manager.py`
- `simulation_runner.py`
- `simulation_config_generator.py`
- `oasis_profile_generator.py`
- `report_agent.py`
- `deep_research_agent.py`
- `zep_tools.py`
- `zep_entity_reader.py`
- `zep_graph_memory_updater.py`
- `text_processor.py`
- `simulation_ipc.py`

Supporting models live under `backend/app/models/`, including project, task, and research-run persistence helpers.

## Persistence and file layout

The backend writes local state under `backend/uploads/`. The repo and tests reference subtrees for:

- projects
- research runs
- reports
- simulations

The compose file also bind-mounts `./backend/uploads` into the container.

## External integrations

The codebase is prepared to integrate with:

- an OpenAI-compatible LLM endpoint via `LLM_*`
- Zep via `ZEP_API_KEY`
- optional Langfuse observability via `LANGFUSE_*`
- optional connector APIs for Brave, Tavily, and Jina
- OASIS/CAMEL-related simulation dependencies from backend Python packages

## Observability

Observability is wired at app startup through a shared client stored in `app.config["OBSERVABILITY_CLIENT"]`.

The repo has backend tests covering:

- Langfuse configuration and client behavior
- app wiring and health endpoint behavior
- observability around graph, simulation, report, and research services

## Current architectural caveats

- The frontend auth implementation is stubbed in localStorage and is not backed by a committed server auth subsystem.
- The container and compose setup run development-style commands rather than a hardened production process manager.
- Some frontend views still contain noisy/generated-looking text in comments or log strings; docs here describe the committed route structure, not idealized UX copy.

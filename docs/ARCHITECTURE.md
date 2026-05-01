<!-- generated-by: gsd-doc-writer -->
# FUTUR.IA Architecture

## System Overview

FUTUR.IA is an AI-powered platform for building social and economic simulations and generating structured analytical reports. The system ingests user requirements and source documents, constructs a knowledge graph via the Zep Cloud API, runs multi-agent simulations using the OASIS framework, and produces reflective reports through a ReACT-based report agent. It is implemented as a modular Flask backend serving a Vue 3 single-page application (SPA), communicating over RESTful JSON APIs with optional real-time synchronization via Convex.

## Component Diagram

```mermaid
graph TD
    subgraph Frontend["Frontend (Vue 3 + Vite)"]
        A[Views / Pages] --> B[Components]
        B --> C[Composables]
        C --> D[API Client Layer]
        D --> E[Axios Instance]
        B --> F[Vue Router]
        A --> G[Vue I18n]
    end

    subgraph Backend["Backend (Flask)"]
        E --> H[Flask App Factory]
        H --> I[API Blueprints]
        I --> J[Graph API]
        I --> K[Simulation API]
        I --> L[Report API]
        I --> M[Research API]
        J --> N[Services Layer]
        K --> N
        L --> N
        M --> N
        N --> O[Graph Builder Service]
        N --> P[Simulation Runner]
        N --> Q[Report Agent]
        N --> R[Deep Research Agent]
        N --> S[Simulation Manager]
        N --> T[Ontology Generator]
        O --> U[Zep Cloud Client]
        P --> V[OASIS Subprocess]
        Q --> W[LLM Client]
        R --> W
        R --> X[Search Connectors]
        X --> Y[Brave / Tavily / Jina]
        W --> Z[OpenAI-Compatible API]
        H --> AA[Observability Client]
        AA --> AB[Langfuse (optional)]
    end

    subgraph Data["State & Persistence"]
        AC[Project Manager] --> AD[File System]
        AE[Task Manager] --> AF[In-Memory State]
        AG[Convex Client] --> AH[Convex Backend]
    end

    N --> AC
    N --> AE
    D --> AG
```

## Data Flow

A typical user journey begins on the Vue frontend where the user uploads documents and describes a simulation scenario. The frontend sends this payload to the `/api/graph` blueprint, which delegates to the `GraphBuilderService`. The service first generates an ontology via the `OntologyGenerator` (using an LLM), then creates and populates a standalone graph in Zep Cloud. The resulting graph identifiers and project context are persisted server-side by the `ProjectManager`, freeing the frontend from maintaining heavy state across requests.

When the user triggers a simulation, the `SimulationManager` prepares parameters and hands them to the `SimulationRunner`, which spawns an OASIS subprocess. The runner communicates with the subprocess over IPC, records every agent action, and updates a `Task` object that the frontend polls via the `/api/simulation` endpoints. After the simulation completes, the `ReportAgent` executes a ReACT loop: it queries Zep for graph insights, plans a report outline, generates sections through the LLM client, and validates outputs through bias auditing, data validation, and quality gates before returning the final report.

For research-oriented workflows, the `DeepResearchAgent` compiles a LangGraph state machine that iterates through search, extraction, summarization, and source ranking nodes, routing queries through a fallback-enabled connector layer (Brave → Tavily → Jina).

All backend services are wrapped by an observability facade that flushes traces to a self-hosted Langfuse instance when enabled; otherwise it operates as a no-op client.

## Key Abstractions

| Name | Type | Location | Description |
|------|------|----------|-------------|
| `create_app` | function | `backend/app/__init__.py` | Flask application factory that wires logging, CORS, observability, simulation cleanup, and API blueprints. |
| `Config` | class | `backend/app/config.py` | Centralized configuration resolver that reads `.env` values and validates required keys (LLM, Zep, Langfuse). |
| `GraphBuilderService` | class | `backend/app/services/graph_builder.py` | Orchestrates ontology normalization, Zep graph creation, and asynchronous node/edge ingestion with progress tracking. |
| `SimulationRunner` | class | `backend/app/services/simulation_runner.py` | Manages the lifecycle of an OASIS simulation subprocess, including IPC, action logging, round summaries, and graceful shutdown. |
| `ReportAgent` | class | `backend/app/services/report_agent.py` | ReACT agent that plans report outlines, queries Zep tools, generates sections via LLM, and enforces quality gates. |
| `DeepResearchAgent` | graph | `backend/app/services/deep_research_agent.py` | LangGraph-compiled research workflow with search, extract, summarize, and source-validation nodes. |
| `ConnectorFallbackRouter` | class | `backend/app/connectors/fallback_router.py` | Routes research search requests across Brave, Tavily, and Jina connectors with automatic fallback. |
| `build_observability_client` | function | `backend/app/observability/langfuse_client.py` | Returns either a `LangfuseObservabilityClient` or a `NoOpObservabilityClient` based on feature flags. |
| `useSimulationMonitor` | function | `frontend/src/composables/useSimulationMonitor.js` | Vue composable that polls simulation status and actions with backoff, exposing reactive refs for UI binding. |
| `service` | object | `frontend/src/api/index.js` | Configured Axios instance with request/response interceptors for locale headers, success normalization, and retry logic. |

## Directory Structure Rationale

```
futuria-v2-refatorado/
├── backend/
│   ├── app/
│   │   ├── api/              # Flask blueprints (graph, simulation, report, research)
│   │   ├── connectors/       # External search adapters with fallback routing
│   │   ├── models/           # In-memory domain models (Project, Task)
│   │   ├── observability/    # Langfuse facade and no-op implementations
│   │   ├── schemas/          # (reserved) Validation schemas
│   │   ├── services/         # Core business logic and long-running agents
│   │   ├── utils/            # Cross-cutting utilities (logger, retry, i18n, LLM client)
│   │   ├── config.py         # Centralized env-based configuration
│   │   └── __init__.py       # Application factory
│   └── run.py                # Entry point: validates config and starts Flask
├── frontend/
│   ├── src/
│   │   ├── api/              # HTTP client modules per domain
│   │   ├── components/       # Vue components (pages split into step-based flows)
│   │   ├── composables/      # Reusable Vue composition functions
│   │   ├── router/           # Vue Router configuration with auth guards
│   │   ├── store/            # Lightweight module-level state (pending uploads, profile)
│   │   ├── utils/            # Frontend utilities (payload validation)
│   │   ├── views/            # Top-level route views
│   │   ├── App.vue           # Root component with global theming
│   │   └── main.js           # Application bootstrap
│   └── vite.config.js        # Vite build with PWA, proxy, and chunk splitting
├── locales/                  # JSON translation files consumed by both frontend and backend i18n utilities
├── docs/                     # Project documentation
└── package.json              # Root orchestration scripts (dev, build, preflight checks)
```

**Backend organization** follows a layered structure: `api/` handles HTTP surface area, `services/` contains all domain logic and agent implementations, `models/` holds ephemeral server-side state, and `connectors/` isolates third-party search integrations. This separation keeps the Flask layer thin and makes the agentic services testable outside of the request/response cycle.

**Frontend organization** is view-centric with step-based simulation flows (Step1 through Step5) living in `components/`, while `composables/` extract reactive logic such as polling and theming. The API layer mirrors backend blueprints so that domain boundaries remain consistent across the stack.

**Locales** live at the repository root so both the Python backend and the Vue frontend can share the same source of truth for translations without duplication.

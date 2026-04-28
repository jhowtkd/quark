# FUTUR.IA

FUTUR.IA is a full-stack social-simulation workbench. It lets a user ingest source material, generate an ontology, build a knowledge graph, prepare simulation environments, run agent-based scenarios, generate reports, and inspect results through a Vue frontend backed by a Flask API.

## What is in the repo today

- **Frontend:** Vue 3 + Vite app in `frontend/`
- **Backend:** Flask service in `backend/`
- **Workflow:** graph building, simulation preparation/execution, report generation, and deep-research runs
- **Persistence:** local files under `backend/uploads/` plus external services configured through environment variables
- **Observability:** optional Langfuse wiring plus backend observability tests

A few behaviors are intentionally worth calling out:

- The committed frontend auth client in `frontend/src/api/auth.js` is a **localStorage stub**. It does not call a real backend auth service.
- The backend exposes a lightweight health endpoint at `GET /health`.
- Root automation includes contamination/preflight checks, but there is **no root `npm test` script** in `package.json`.

## Project flow

The application UI is organized as a five-step workflow:

1. **Build graph** — upload source material or promote deep-research output into a project
2. **Prepare environment** — derive agent profiles and simulation config
3. **Run simulation** — execute the generated scenario
4. **Generate report** — synthesize report output from the simulation state
5. **Interact** — inspect and chat against simulation/report context

The committed frontend route map is:

- `/` — home
- `/login` and `/register` — guest-only auth screens
- `/process/:projectId` — graph/research workbench
- `/simulation/:simulationId` — environment preparation
- `/simulation/:simulationId/start` — simulation run view
- `/report/:reportId` — report view
- `/interaction/:reportId` — interaction view

## Quick start

### Prerequisites

- Node.js 18+
- Python 3.11+
- `uv`

### 1. Install dependencies

```bash
npm run setup:all
```

This installs root/frontend Node dependencies and backend Python dependencies.

### 2. Configure environment

Copy the example file and fill in the values you need:

```bash
cp .env.example .env
```

At minimum, backend startup validation requires:

- `LLM_API_KEY`
- `ZEP_API_KEY`

See [docs/CONFIGURATION.md](./docs/CONFIGURATION.md) for the full list.

### 3. Start the app in development

```bash
npm run dev
```

This starts:

- frontend Vite dev server on `http://localhost:4000`
- backend Flask app on `http://localhost:5001`

The frontend proxies `/api/*` to the backend during development.

### 4. Verify the backend is up

```bash
curl http://localhost:5001/health
```

Expected response:

```json
{"status":"ok","service":"FUTUR.IA Backend"}
```

## Docker

The repo includes a `Dockerfile` and `docker-compose.yml`.

```bash
docker compose up --build
```

The compose file maps:

- host `3000` -> container/frontend `4000`
- host `5001` -> container/backend `5001`

The committed container command runs the frontend and backend in development mode.

## Development commands

```bash
# install everything
npm run setup:all

# run frontend + backend
npm run dev

# build frontend production bundle
npm run build

# backend tests
cd backend && uv run pytest

# contamination / policy preflight checks
npm run preflight
```

## Documentation

- [Architecture](./docs/ARCHITECTURE.md)
- [Getting started](./docs/GETTING-STARTED.md)
- [Development](./docs/DEVELOPMENT.md)
- [Testing](./docs/TESTING.md)
- [Configuration](./docs/CONFIGURATION.md)
- [Deployment](./docs/DEPLOYMENT.md)
- [Contributing](./CONTRIBUTING.md)

## License

This repository is licensed under **AGPL-3.0**.

# Getting started

## Prerequisites

Install these first:

- Node.js 18+
- Python 3.11+
- `uv`

## 1. Install dependencies

From the repository root:

```bash
npm run setup:all
```

This performs:

- root `npm install`
- frontend `npm install`
- backend `uv sync`

## 2. Create local configuration

```bash
cp .env.example .env
```

For a minimum working backend startup, populate:

```env
LLM_API_KEY=...
ZEP_API_KEY=...
```

If you want Langfuse enabled, also set:

```env
LANGFUSE_ENABLED=true
LANGFUSE_HOST=...
LANGFUSE_PUBLIC_KEY=...
LANGFUSE_SECRET_KEY=...
```

See [CONFIGURATION.md](./CONFIGURATION.md) for the full matrix.

## 3. Start the development servers

```bash
npm run dev
```

Expected local endpoints:

- frontend: `http://localhost:4000`
- backend: `http://localhost:5001`
- backend health: `http://localhost:5001/health`

## 4. Check the backend health endpoint

```bash
curl http://localhost:5001/health
```

Expected JSON:

```json
{"status":"ok","service":"FUTUR.IA Backend"}
```

## 5. Open the app

Visit:

```text
http://localhost:4000
```

The main route flow is:

- `/` — home
- `/process/:projectId` — graph/research workbench
- `/simulation/:simulationId` — environment preparation
- `/simulation/:simulationId/start` — simulation run screen
- `/report/:reportId` — report screen
- `/interaction/:reportId` — interaction screen

## 6. First workflow to try

A practical path through the committed app is:

1. open the frontend
2. create or load a project
3. generate ontology / graph data
4. prepare a simulation
5. run the simulation
6. generate a report
7. inspect the interaction view

## Auth note

The committed auth client is a localStorage stub in `frontend/src/api/auth.js`.

That means:

- login/register screens exist
- route guards are active
- any entered login/register values are handled locally by the frontend stub rather than a real backend auth service

## Docker path

You can also start the repo with Docker:

```bash
docker compose up --build
```

The compose file exposes:

- `http://localhost:3000` for the frontend container port mapping
- `http://localhost:5001` for the backend

## Useful next commands

```bash
# frontend production build
npm run build

# backend tests
cd backend && uv run pytest

# reporting contamination preflight
npm run preflight
```

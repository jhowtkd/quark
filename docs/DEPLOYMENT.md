<!-- generated-by: gsd-doc-writer -->
# Deployment

## Deployment targets

The repository root contains containerization assets for local and small-scale hosting:

- `Dockerfile` — builds a single image with Python 3.11, Node.js, and `uv`
- `docker-compose.yml` — orchestrates one service with port forwarding and a volume mount

The checked-in `Dockerfile` defaults to `CMD ["npm", "run", "dev"]`, which starts the Vite frontend development server and the Flask backend concurrently via `concurrently`. This layout is optimized for development and demonstration environments. <!-- VERIFY: For production workloads, a dedicated production image that builds the frontend to static assets and serves the backend behind a production WSGI server (e.g. Gunicorn) is recommended. -->

### Docker Compose

Start the full stack:

```bash
docker compose up --build
```

Compose behavior:
- builds from the root `Dockerfile`
- loads environment variables from `.env`
- maps host port `3000` → container port `4000` (frontend dev server)
- maps host port `5001` → container port `5001` (backend API)
- mounts `./backend/uploads` to `/app/backend/uploads` for file persistence
- restarts with `unless-stopped`

## Ambiente Beta

A dedicated beta environment is available via `docker-compose.beta.yml`. It runs the backend and frontend as separate services with isolated volumes and a dedicated Docker network, avoiding port conflicts with the development stack.

### Starting the beta environment

1. Create the environment file:

```bash
cp .env.beta.example .env.beta
# Edit .env.beta with real credentials
```

2. Start the services:

```bash
docker compose -f docker-compose.beta.yml up --build
```

Beta behavior:
- `backend-beta` listens on host port `5002` (container port `5002`)
- `frontend-beta` serves the production build on host port `4002` (container port `4002`)
- `FLASK_DEBUG=false` is enforced for the beta backend
- Uploads are persisted to the named volume `beta-uploads` (`/app/uploads/beta`)
- Logs are persisted to the named volume `beta-logs` (`/app/logs/beta`)
- Both services attach to the `futuria-beta-network` bridge network
- Services restart with `unless-stopped`

### Destroying beta data

To remove the beta volumes and all associated data:

```bash
docker compose -f docker-compose.beta.yml down
docker volume rm futuria-v2-refatorado_beta-uploads futuria-v2-refatorado_beta-logs
```

### Manual non-Docker startup

Backend:

```bash
cd backend
uv sync
uv run python run.py
```

Frontend (development):

```bash
cd frontend
npm install
npm run dev
```

Frontend (production build artifact):

```bash
cd frontend
npm run build
```

The build outputs static files to `frontend/dist/`. These can be served by any static file server or CDN. <!-- VERIFY: static file server or CDN -->

## Build pipeline

There is **no automated CI/CD pipeline at the project root**. The repository does not contain `.github/workflows/` in the root directory.

The `futuria-analysis/` sub-project contains GitHub Actions workflows (`docker-image.yml` and `language-contamination-gate.yml`), but those are scoped to that directory and do not drive builds or deployments for the main application.

As a result, build and release processes for the main application are currently manual or must be provided by external orchestration.

## Environment setup

Create the environment file from the example:

```bash
cp .env.example .env
```

### Required variables

The backend validates configuration at startup (`backend/run.py` calls `Config.validate()`). Missing required values cause the process to exit with code `1`.

| Variable | Description |
|---|---|
| `LLM_API_KEY` | API key for the configured OpenAI-compatible LLM provider |
| `ZEP_API_KEY` | API key for Zep Cloud graph and memory operations |

### Optional variables

| Variable | Default | Description |
|---|---|---|
| `LLM_BASE_URL` | `https://api.openai.com/v1` | Base URL for the LLM API |
| `LLM_MODEL_NAME` | `gpt-4o-mini` | Model identifier |
| `LLM_BOOST_API_KEY` | — | Accelerated LLM provider key |
| `LLM_BOOST_BASE_URL` | — | Accelerated LLM provider URL |
| `LLM_BOOST_MODEL_NAME` | — | Accelerated LLM provider model |
| `VITE_CONVEX_URL` | — | Convex deployment URL (e.g. `https://your-project.convex.cloud`) |
| `SECRET_KEY` | `futuria-secret-key` | Flask secret key |
| `FLASK_DEBUG` | `True` | Enable Flask debug mode |
| `FLASK_HOST` | `0.0.0.0` | Backend bind host |
| `FLASK_PORT` | `5001` | Backend bind port |
| `OASIS_DEFAULT_MAX_ROUNDS` | `10` | Default simulation round limit |
| `REPORT_AGENT_MAX_TOOL_CALLS` | `5` | Report agent tool call budget |
| `REPORT_AGENT_MAX_REFLECTION_ROUNDS` | `2` | Report agent reflection depth |
| `REPORT_AGENT_TEMPERATURE` | `0.5` | Report agent sampling temperature |
| `BRAVE_SEARCH_API_KEY` | — | Brave Search API key (deep research) |
| `TAVILY_API_KEY` | — | Tavily API key (deep research) |
| `JINA_API_KEY` | — | Jina AI API key (deep research) |
| `VITE_API_BASE_URL` | `/api` | Frontend API base URL |
| `VITE_AGENTATION_ENDPOINT` | — | Agentation service endpoint |

### Observability variables (Langfuse)

When `LANGFUSE_ENABLED=true`, the following become required:

| Variable | Description |
|---|---|
| `LANGFUSE_HOST` | Langfuse instance URL |
| `LANGFUSE_PUBLIC_KEY` | Project public key |
| `LANGFUSE_SECRET_KEY` | Project secret key |

Optional tuning:

| Variable | Default | Description |
|---|---|---|
| `LANGFUSE_ENV` | `development` | Environment label |
| `LANGFUSE_RELEASE` | `local` | Release version tag |
| `LANGFUSE_DEBUG` | `false` | SDK debug logging |
| `LANGFUSE_SAMPLE_RATE` | `1.0` | Trace sampling rate (0.0–1.0) |

## Rollback procedure

Because the root project has no automated release pipeline, rollback is performed manually.

### Docker Compose rollback

1. Identify the previous working Git commit or image tag.
2. If using a tagged image, update `docker-compose.yml` to reference the previous tag.
3. Rebuild and restart:

```bash
docker compose down
docker compose up --build -d
```

### Git-based rollback

```bash
git checkout <previous-tag-or-commit>
docker compose down
docker compose up --build -d
```

<!-- VERIFY: For environments using a container registry, pull the previous image tag and update the deployment manifest or Compose service image reference accordingly. -->

## Monitoring

### Health check

The backend exposes a liveness endpoint:

```text
GET /health
```

Example:

```bash
curl http://localhost:5001/health
```

Expected response:

```json
{"status": "ok", "service": "FUTUR.IA Backend"}
```

### Observability (Langfuse)

The backend includes an optional Langfuse integration for structured LLM tracing. When enabled (`LANGFUSE_ENABLED=true` and credentials configured), the `LangfuseObservabilityClient` emits traces for:

- Report generation pipelines
- Chat sessions
- Language integrity scoring

Traces are flushed at process shutdown via an `atexit` handler registered in the Flask app factory (`backend/app/__init__.py`).

When Langfuse is disabled (the default), a `NoOpObservabilityClient` is used and no external traffic is generated.

<!-- VERIFY: Access the Langfuse dashboard at the URL configured in `LANGFUSE_HOST` (for example, a self-hosted instance or the Langfuse Cloud dashboard). -->

### Log output

The backend uses Python `logging` with a configured logger (`futuria`). Request and response details are logged at `DEBUG` level when `FLASK_DEBUG=True`. Simulation lifecycle events and observability client status are emitted at `INFO` level during startup.

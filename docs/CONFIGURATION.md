<!-- generated-by: gsd-doc-writer -->
# Configuration

This document covers all configuration sources, environment variables, and runtime tuning options for FUTUR.IA.

## Configuration file format

The primary configuration mechanism is a project-root `.env` file loaded by `python-dotenv` in `backend/app/config.py`. The loader reads from the project root without mutating `os.environ`, so process-level environment variables always take precedence over `.env` values.

There is no JSON/YAML/TOML config file for application settings. One additional static config file exists:

- `config/language_policy.json` — language integrity policy for reporting surfaces (allowed languages, contamination tracking, quarantine rules). This is read by the language integrity utilities, not by the main config loader.

## Environment variables

### Required settings

These variables cause startup failure if absent. `backend/run.py` calls `Config.validate()` before starting the Flask app and exits with code `1` if validation fails.

| Variable | Required | Default | Description |
|---|---|---|---|
| `LLM_API_KEY` | Yes | none | API key for the configured OpenAI-compatible LLM provider |
| `ZEP_API_KEY` | Yes | none | API key for Zep graph/memory operations |

### Conditionally required settings

When `LANGFUSE_ENABLED=true`, the following become required and will cause startup failure if missing:

| Variable | Required when | Default | Description |
|---|---|---|---|
| `LANGFUSE_HOST` | `LANGFUSE_ENABLED=true` | none | Langfuse host URL |
| `LANGFUSE_PUBLIC_KEY` | `LANGFUSE_ENABLED=true` | none | Langfuse public key |
| `LANGFUSE_SECRET_KEY` | `LANGFUSE_ENABLED=true` | none | Langfuse secret key |

### LLM settings

| Variable | Required | Default | Description |
|---|---|---|---|
| `LLM_API_KEY` | Yes | none | API key for the primary OpenAI-compatible endpoint |
| `LLM_BASE_URL` | No | `https://api.openai.com/v1` | Base URL for the LLM API |
| `LLM_MODEL_NAME` | No | `gpt-4o-mini` | Default model identifier |
| `LLM_BOOST_API_KEY` | No | none | Optional secondary LLM endpoint key |
| `LLM_BOOST_BASE_URL` | No | none | Optional secondary LLM endpoint URL |
| `LLM_BOOST_MODEL_NAME` | No | none | Optional secondary LLM model name |

### Backend runtime settings

| Variable | Required | Default | Description |
|---|---|---|---|
| `FLASK_HOST` | No | `0.0.0.0` | Bind address for the Flask development server |
| `FLASK_PORT` | No | `5001` | Port for the Flask development server |
| `FLASK_DEBUG` | No | `True` | Enables Flask debug mode and auto-reload |
| `SECRET_KEY` | No | `futuria-secret-key` | Flask session/CSRF secret key |

### Langfuse observability settings

| Variable | Required | Default | Description |
|---|---|---|---|
| `LANGFUSE_ENABLED` | No | `false` | Toggle Langfuse tracing on/off |
| `LANGFUSE_HOST` | No | none | Langfuse host URL (required when enabled) |
| `LANGFUSE_PUBLIC_KEY` | No | none | Langfuse public key (required when enabled) |
| `LANGFUSE_SECRET_KEY` | No | none | Langfuse secret key (required when enabled) |
| `LANGFUSE_ENV` | No | `development` | Environment label sent to Langfuse |
| `LANGFUSE_RELEASE` | No | `local` | Release label sent to Langfuse |
| `LANGFUSE_DEBUG` | No | `false` | Enables Langfuse SDK debug logging |
| `LANGFUSE_SAMPLE_RATE` | No | `0.1` | Sampling rate for traces (0.0–1.0). Default reduced to 0.1 to limit data volume. |

### Research connector API keys (optional)

| Variable | Required | Default | Description |
|---|---|---|---|
| `BRAVE_SEARCH_API_KEY` | No | none | Brave Search API key for deep research |
| `TAVILY_API_KEY` | No | none | Tavily API key for deep research |
| `JINA_API_KEY` | No | none | Jina AI API key for deep research |

### Frontend build-time settings

Vite exposes only variables prefixed with `VITE_` to the client bundle.

| Variable | Required | Default | Description |
|---|---|---|---|
| `VITE_CONVEX_URL` | No | none | Convex deployment URL. <!-- VERIFY: Convex is currently disabled in `frontend/src/convex.js`; this variable is present in `.env.example` but not actively consumed by the frontend runtime. --> |
| `VITE_API_BASE_URL` | No | `/api` | Base URL for API requests. Set this if the frontend is served from a different origin than the backend. |

### Simulation and report tuning

These variables are read from the environment but have hardcoded defaults in `backend/app/config.py`.

| Variable | Default | Description |
|---|---|---|
| `OASIS_DEFAULT_MAX_ROUNDS` | `10` | Default maximum rounds for OASIS social media simulations |
| `REPORT_AGENT_MAX_TOOL_CALLS` | `5` | Maximum tool calls per report agent run |
| `REPORT_AGENT_MAX_REFLECTION_ROUNDS` | `2` | Maximum self-reflection rounds for the report agent |
| `REPORT_AGENT_TEMPERATURE` | `0.5` | Sampling temperature for the report agent |
| `DEFAULT_CHUNK_SIZE` | `300` | Text chunk size for document processing |
| `DEFAULT_CHUNK_OVERLAP` | `30` | Chunk overlap for document processing |

The following constants are hardcoded in `backend/app/config.py` and are **not** overridable via environment variables:

- `MAX_CONTENT_LENGTH` — `50 MB` maximum upload size
- `UPLOAD_FOLDER` — `backend/uploads/` (resolved relative to `config.py`)
- `ALLOWED_EXTENSIONS` — `pdf`, `md`, `txt`, `markdown`

## Required vs optional settings summary

| Category | Absence behavior |
|---|---|
| `LLM_API_KEY`, `ZEP_API_KEY` | Backend exits at startup with validation error |
| `LANGFUSE_HOST`, `LANGFUSE_PUBLIC_KEY`, `LANGFUSE_SECRET_KEY` | Backend exits at startup **only if** `LANGFUSE_ENABLED=true` |
| All other variables listed above | Backend starts with documented defaults; features depending on those keys degrade gracefully |

## Defaults

All optional variables have the following defaults:

- `LLM_BASE_URL` → `https://api.openai.com/v1`
- `LLM_MODEL_NAME` → `gpt-4o-mini`
- `FLASK_HOST` → `0.0.0.0`
- `FLASK_PORT` → `5001`
- `FLASK_DEBUG` → `True`
- `SECRET_KEY` → `futuria-secret-key`
- `LANGFUSE_ENABLED` → `false`
- `LANGFUSE_ENV` → `development`
- `LANGFUSE_RELEASE` → `local`
- `LANGFUSE_DEBUG` → `false`
- `LANGFUSE_SAMPLE_RATE` → `0.1`
- `OASIS_DEFAULT_MAX_ROUNDS` → `10`
- `REPORT_AGENT_MAX_TOOL_CALLS` → `5`
- `REPORT_AGENT_MAX_REFLECTION_ROUNDS` → `2`
- `REPORT_AGENT_TEMPERATURE` → `0.5`
- `VITE_API_BASE_URL` → `/api`

## Per-environment overrides

### Development (default)

Use the project-root `.env` file. The minimum viable `.env` for local development is:

```bash
cp .env.example .env
```

Then edit `.env` and set at least:

```env
LLM_API_KEY=your_api_key_here
ZEP_API_KEY=your_zep_api_key_here
```

Start the full stack:

```bash
npm run dev
```

This runs the backend on `http://localhost:5001` and the Vite dev server on `http://localhost:4000`. The Vite dev proxy forwards `/api` to the backend automatically.

### Frontend dev-server overrides

`frontend/vite.config.js` hardcodes the following development behavior:

| Setting | Value |
|---|---|
| Dev server port | `4000` |
| `/api` proxy target | `http://localhost:5001` |
| `/auth` proxy target | `http://127.0.0.1:3210` |

These are **not** driven by environment variables. To change them, edit `vite.config.js` directly.

### Docker / containerized

`docker-compose.yml` wires services with `env_file: .env`. The compose file exposes:

- Host port `3000` → container frontend dev server (`4000`)
- Host port `5001` → container backend (`5001`)
- Volume mount `./backend/uploads:/app/backend/uploads`

<!-- VERIFY: Port mapping and volume paths above are taken from `docker-compose.yml`. Production deployment may use different orchestration not present in the repository. -->

### Production considerations

- Set `FLASK_DEBUG=false`
- Set `SECRET_KEY` to a cryptographically random value
- Set `LANGFUSE_ENV=production` and `LANGFUSE_RELEASE` to a version tag if using Langfuse
- In beta environments (`LANGFUSE_ENV` contains `beta`), `LANGFUSE_SAMPLE_RATE` is restricted to `<= 0.2`. Configuring a higher value causes validation failure at startup.
- `VITE_API_BASE_URL` should point to the production backend origin if frontend and backend are served from different hosts

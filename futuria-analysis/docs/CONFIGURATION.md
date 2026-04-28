# Configuration

## Configuration sources

The backend loads environment variables from a project-root `.env` file via `python-dotenv` in `backend/app/config.py`.

If `backend/.env` does not exist, the backend still reads environment variables from the current process environment.

## Required variables

`backend/run.py` calls `Config.validate()` before starting the Flask app.

The committed validation requires:

| Variable | Required | Purpose |
|---|---|---|
| `LLM_API_KEY` | Yes | API key for the configured OpenAI-compatible model provider |
| `ZEP_API_KEY` | Yes | API key for Zep-backed graph/memory operations |

When `LANGFUSE_ENABLED=true`, these become required as well:

| Variable | Required when enabled | Purpose |
|---|---|---|
| `LANGFUSE_HOST` | Yes | Langfuse host URL |
| `LANGFUSE_PUBLIC_KEY` | Yes | Langfuse public key |
| `LANGFUSE_SECRET_KEY` | Yes | Langfuse secret key |

## LLM settings

From `.env.example` and `backend/app/config.py`:

| Variable | Default | Notes |
|---|---|---|
| `LLM_API_KEY` | none | Required by backend validation |
| `LLM_BASE_URL` | `https://api.openai.com/v1` | OpenAI-compatible base URL |
| `LLM_MODEL_NAME` | `gpt-4o-mini` | Default model name |

## Optional boost settings

`.env.example` also includes optional secondary LLM settings:

| Variable | Purpose |
|---|---|
| `LLM_BOOST_API_KEY` | optional boosted endpoint key |
| `LLM_BOOST_BASE_URL` | optional boosted endpoint URL |
| `LLM_BOOST_MODEL_NAME` | optional boosted endpoint model |

## Backend runtime settings

From `backend/app/config.py` and `backend/run.py`:

| Variable | Default | Purpose |
|---|---|---|
| `FLASK_HOST` | `0.0.0.0` | bind address |
| `FLASK_PORT` | `5001` | backend port |
| `FLASK_DEBUG` | `True` | toggles Flask debug behavior |
| `SECRET_KEY` | `futuria-secret-key` | Flask secret key fallback |

## Langfuse settings

Optional observability settings defined in `.env.example` and consumed by `Config`:

| Variable | Default |
|---|---|
| `LANGFUSE_ENABLED` | `false` |
| `LANGFUSE_HOST` | none in code, `http://localhost:3000` in example file |
| `LANGFUSE_PUBLIC_KEY` | none |
| `LANGFUSE_SECRET_KEY` | none |
| `LANGFUSE_ENV` | `development` |
| `LANGFUSE_RELEASE` | `local` |
| `LANGFUSE_DEBUG` | `false` |
| `LANGFUSE_SAMPLE_RATE` | `1.0` |

## Connector API keys

The backend config exposes optional keys for research connectors:

| Variable | Purpose |
|---|---|
| `BRAVE_SEARCH_API_KEY` | Brave connector |
| `TAVILY_API_KEY` | Tavily connector |
| `JINA_API_KEY` | Jina connector |

## Simulation and report tuning

The backend config also exposes non-secret tuning variables/constants:

| Setting | Default |
|---|---|
| `OASIS_DEFAULT_MAX_ROUNDS` | `10` |
| `REPORT_AGENT_MAX_TOOL_CALLS` | `5` |
| `REPORT_AGENT_MAX_REFLECTION_ROUNDS` | `2` |
| `REPORT_AGENT_TEMPERATURE` | `0.5` |
| `DEFAULT_CHUNK_SIZE` | `300` |
| `DEFAULT_CHUNK_OVERLAP` | `30` |
| `MAX_CONTENT_LENGTH` | `50 MB` |

Allowed upload extensions are hardcoded as:

- `pdf`
- `md`
- `txt`
- `markdown`

## Frontend dev-server configuration

`frontend/vite.config.js` defines local development behavior:

| Setting | Value |
|---|---|
| dev host | `vite --host` |
| dev port | `4000` |
| alias `@` | `frontend/src` |
| alias `@locales` | `locales/` |
| `/api` proxy target | `http://localhost:5001` |
| `/auth` proxy target | `http://127.0.0.1:3210` |

## Auth configuration caveat

The committed frontend auth implementation in `frontend/src/api/auth.js` uses localStorage and does not read auth credentials from environment variables. The `/auth` proxy exists in Vite config, but the current auth client does not use it.

## Docker/runtime config files

- `.env.example` — starter environment file
- `docker-compose.yml` — compose service wiring with `env_file: .env`
- `Dockerfile` — image build and default command

## Minimal local setup

```bash
cp .env.example .env
```

Set at least:

```env
LLM_API_KEY=...
ZEP_API_KEY=...
```

Then start the app:

```bash
npm run dev
```

<!-- generated-by: gsd-doc-writer -->

# Getting Started

This guide walks you through setting up FUTUR.IA locally and running the development stack for the first time.

## Prerequisites

Before you begin, make sure you have the following installed:

| Tool | Version | Purpose |
|------|---------|---------|
| [Node.js](https://nodejs.org/) | >= 18.0.0 | Frontend runtime and build tooling |
| [Python](https://www.python.org/) | >= 3.11 | Backend runtime |
| [uv](https://docs.astral.sh/uv/) | latest | Python dependency management and virtual environments |
| npm | bundled with Node.js | Node package manager |

Verify your versions:

```bash
node --version   # should print v18.x.x or higher
python3 --version  # should print 3.11.x or higher
uv --version
```

### External service accounts

You will need API keys for two external services before the backend can start:

- **LLM provider** — any OpenAI-compatible API (e.g., OpenAI, Claude via compatible endpoint)
- **Zep Cloud** — free tier available at [https://app.getzep.com/](https://app.getzep.com/)

## Installation steps

1. **Clone the repository**

   ```bash
   git clone <repository-url> futuria-v2-refatorado
   cd futuria-v2-refatorado
   ```

2. **Install all dependencies**

   ```bash
   npm run setup:all
   ```

   This runs three steps in sequence:
   - `npm install` in the project root
   - `npm install` inside `frontend/`
   - `uv sync` inside `backend/` to create the Python virtual environment and install packages

   If you prefer to install frontend and backend separately:

   ```bash
   npm run setup          # Node.js dependencies only
   npm run setup:backend  # Python backend only
   ```

3. **Configure environment variables**

   ```bash
   cp .env.example .env
   ```

   Open `.env` and fill in the two required keys:

   ```env
   LLM_API_KEY=your_api_key_here
   ZEP_API_KEY=your_zep_api_key_here
   ```

   All other variables are optional for a first run. If you have a Convex deployment, you can also set `VITE_CONVEX_URL`.

## First run

Start both the backend and frontend simultaneously with:

```bash
npm run dev
```

This launches:

- **Frontend** — Vue 3 + Vite dev server at [http://localhost:4000](http://localhost:4000)
- **Backend** — Flask API at [http://localhost:5001](http://localhost:5001)

Verify the backend is healthy:

```bash
curl http://localhost:5001/health
```

You should see a JSON response indicating the service is up.

### Alternative: Docker

If you prefer Docker, start the stack with:

```bash
docker compose up --build
```

The compose file exposes:

- Frontend at [http://localhost:3000](http://localhost:3000)
- Backend at [http://localhost:5001](http://localhost:5001)

## Common setup issues

### `Configuration errors: LLM_API_KEY not configured`

**Symptom:** The backend exits immediately after `npm run dev` with the message:

```text
Configuration errors:
  - LLM_API_KEY not configured
  - ZEP_API_KEY not configured
Please check your .env file configuration
```

**Fix:** Copy `.env.example` to `.env` and add valid values for both `LLM_API_KEY` and `ZEP_API_KEY`. The backend validates these at startup and will refuse to start without them.

### `uv: command not found`

**Symptom:** `npm run setup:all` fails with:

```text
uv: command not found
```

**Fix:** Install `uv` following the [official instructions](https://docs.astral.sh/uv/getting-started/installation/). On macOS/Linux:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Then restart your shell or open a new terminal and rerun `npm run setup:all`.

### `python3: No module named dotenv` (or similar import errors)

**Symptom:** The backend fails to start with missing Python packages even after running setup.

**Fix:** Ensure you are using `uv run` (which automatically uses the managed virtual environment) rather than calling `python3` directly:

```bash
cd backend && uv run python run.py
```

Avoid running `python run.py` with the system Python interpreter.

## Next steps

- **Day-to-day development** — See [`DEVELOPMENT.md`](./DEVELOPMENT.md) for repo layout, common commands, frontend/backend development notes, and pre-flight checks.
- **Running tests** — See [`TESTING.md`](./TESTING.md) for backend pytest commands, frontend build verification, and manual smoke-check checklists.
- **Architecture overview** — See [`ARCHITECTURE.md`](./ARCHITECTURE.md) for system diagrams and component descriptions.
- **Configuration reference** — See [`CONFIGURATION.md`](./CONFIGURATION.md) for the full list of environment variables and their defaults.

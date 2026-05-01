<!-- generated-by: gsd-doc-writer -->

# FUTUR.IA

Swarm Intelligence Engine for Social Simulation

![Version](https://img.shields.io/badge/version-0.1.0-blue)
![License](https://img.shields.io/badge/license-AGPL--3.0-green)

## Overview

FUTUR.IA is a full-stack research and simulation platform that combines LLM-driven swarm intelligence with social media environment modeling. It provides an interactive workbench for generating knowledge graphs, running multi-agent simulations, and producing structured research reports.

## Prerequisites

- Node.js 18+
- Python 3.11+
- [uv](https://docs.astral.sh/uv/)

## Installation

```bash
npm run setup:all
```

This installs root and frontend Node dependencies, then syncs the Python backend environment.

## Quick start

1. **Configure environment variables**

   ```bash
   cp .env.example .env
   ```

   Edit `.env` and add at minimum:

   ```env
   LLM_API_KEY=your_api_key_here
   ZEP_API_KEY=your_zep_api_key_here
   ```

2. **Start the development servers**

   ```bash
   npm run dev
   ```

3. **Open the app**

   - Frontend: http://localhost:4000
   - Backend health: http://localhost:5001/health

## Usage examples

### Run the backend tests

```bash
cd backend && uv run pytest
```

### Build the frontend for production

```bash
npm run build
```

### Start with Docker

```bash
docker compose up --build
```

The compose file exposes the frontend at `http://localhost:3000` and the backend at `http://localhost:5001`.

## Project structure

- `frontend/` — Vue 3 + Vite frontend application
- `backend/app/` — Python/Flask backend API (`/api/graph`, `/api/simulation`, `/api/report`, `/api/research`)
- `docs/` — Architecture, configuration, and development guides
- `tests/` — Frontend and backend test suites

## Contributing

See [CONTRIBUTING.md](./CONTRIBUTING.md) for guidelines.

## License

This project is licensed under the GNU Affero General Public License v3.0 (AGPL-3.0).

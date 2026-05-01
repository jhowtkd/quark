<!-- generated-by: gsd-doc-writer -->

# Development Guide

This document covers how to set up the project locally, run builds, follow conventions, and submit changes.

## Local setup

### Prerequisites

- Node.js 18+
- Python 3.11+
- [uv](https://docs.astral.sh/uv/)

### 1. Clone the repository

```bash
git clone <repository-url>
cd futuria-v2-refatorado
```

### 2. Install dependencies

```bash
npm run setup:all
```

This command runs three steps in sequence:

- `npm install` at the repository root
- `npm install` inside `frontend/`
- `uv sync` inside `backend/`

### 3. Configure environment variables

```bash
cp .env.example .env
```

Edit `.env` and set at minimum:

```env
LLM_API_KEY=your_api_key_here
ZEP_API_KEY=your_zep_api_key_here
```

See [CONFIGURATION.md](./CONFIGURATION.md) for the full variable matrix.

### 4. Start the development servers

```bash
npm run dev
```

This starts both the Flask backend (`http://localhost:5001`) and the Vite frontend dev server (`http://localhost:4000`) concurrently.

## Build commands

### Root package.json scripts

| Script | Description |
|--------|-------------|
| `npm run setup` | Installs root and frontend Node dependencies |
| `npm run setup:backend` | Syncs the Python backend environment via `uv sync` |
| `npm run setup:all` | Runs `setup` + `setup:backend` in one shot |
| `npm run dev` | Runs backend and frontend dev servers concurrently |
| `npm run backend` | Starts the Flask backend only |
| `npm run frontend` | Starts the Vite frontend dev server only |
| `npm run build` | Builds the frontend production bundle |
| `npm run check:language-reporting` | Runs language contamination check on reporting surfaces |
| `npm run check:language-backend` | Runs language contamination check on backend reporting |
| `npm run check:language-artifacts` | Validates report artifacts for language contamination (dry run) |
| `npm run preflight` | Runs `check:language-backend` + `check:language-artifacts` |
| `npm run remediate:report-artifacts` | Shows report artifact remediation plan (dry run) |
| `npm run remediate:report-artifacts:fix` | Applies report artifact normalization and quarantine |

### Frontend package.json scripts

Run from the `frontend/` directory or via `cd frontend && npm run <script>`:

| Script | Description |
|--------|-------------|
| `npm run dev` | Starts the Vite dev server with `--host` |
| `npm run build` | Builds the production bundle |
| `npm run preview` | Previews the production build locally |
| `npm run test` | Runs the Vitest test suite once |
| `npm run test:watch` | Runs Vitest in watch mode |

### Backend commands

Run from the `backend/` directory:

| Command | Description |
|---------|-------------|
| `uv run pytest` | Runs the backend pytest suite |
| `uv run python run.py` | Starts the Flask backend directly |

## Code style

This repository does **not** currently enforce code style through automated linting or formatting tools. There are no committed ESLint, Prettier, Biome, or EditorConfig files.

As a contributor, please follow these practical conventions:

- **Python**: Use PEP 8 style. Keep functions focused and under 500 lines.
- **JavaScript/Vue**: Use consistent indentation (2 spaces), semicolons, and single quotes. Follow the existing patterns in `frontend/src/`.
- **File size**: Keep files under 500 lines where possible (per project convention).
- **Typed interfaces**: Use typed interfaces for all public APIs.

If you introduce a new linting or formatting tool, update this document and add the config to the repository root so it applies consistently.

## Branch conventions

- **Default branch**: `main`
- **Feature branches**: prefix with `feat/` (e.g., `feat/simulation-control-center`)
- Create branches from `main` and keep them focused on a single change or feature

Existing branch example in the repository:

```
feat/simulation-control-center
```

## PR process

- Create a feature branch from `main` with a descriptive name
- Make focused, atomic commits with clear messages
- Run the verification commands relevant to your change before opening the PR:
  - Frontend or UI work: `npm run build`
  - Backend logic or API work: `cd backend && uv run pytest`
  - Reporting or contamination-policy work: `npm run preflight`
- Open a pull request against `main` with a clear description that includes:
  - What changed
  - Why it changed
  - What you verified
  - Any follow-up work or known limitations
- Ensure docs are updated if your change affects setup steps, environment variables, user-visible behavior, or contributor-facing conventions

See [CONTRIBUTING.md](../CONTRIBUTING.md) for additional guidance.

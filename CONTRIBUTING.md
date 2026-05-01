<!-- generated-by: gsd-doc-writer -->

# Contributing to FUTUR.IA

Thank you for your interest in contributing to FUTUR.IA. This document covers the basics of setting up the project locally, running verification checks, and submitting changes.

## Development setup

1. Make sure you have the prerequisites installed:
   - Node.js 18+
   - Python 3.11+
   - [uv](https://docs.astral.sh/uv/)

2. Install all dependencies:

   ```bash
   npm run setup:all
   ```

3. Start the development environment:

   ```bash
   npm run dev
   ```

For detailed environment and workflow guidance, see:

- [docs/GETTING-STARTED.md](./docs/GETTING-STARTED.md)
- [docs/DEVELOPMENT.md](./docs/DEVELOPMENT.md)
- [docs/TESTING.md](./docs/TESTING.md)
- [docs/ARCHITECTURE.md](./docs/ARCHITECTURE.md)

## Coding standards

The project currently does not use an automated linter or formatter. Please follow these conventions when submitting code:

- **Python**: Keep code PEP 8 compliant and include type hints where practical.
- **JavaScript/Vue**: Use consistent indentation (2 spaces) and clear variable naming.
- **All changes**: Run the relevant verification commands before opening a pull request.

### Verification commands

Run the checks that match your change area:

- **Frontend or UI work**

  ```bash
  npm run build
  ```

- **Backend logic or API work**

  ```bash
  cd backend && uv run pytest
  ```

- **Reporting or contamination-policy work**

  ```bash
  npm run preflight
  ```

If your change crosses multiple areas, run more than one of the above.

## Issue reporting

Bugs and feature requests are tracked via GitHub Issues. When opening an issue, please include:

- A clear, descriptive title
- Steps to reproduce (for bugs), or the expected behavior and motivation (for features)
- Your environment (Node.js version, Python version, OS)
- Any relevant logs, screenshots, or error messages

## Pull request guidelines

- Open a pull request from a feature branch against `main`.
- Keep the change focused on a single concern; split unrelated changes into separate PRs.
- Provide a clear PR description that explains **what** changed, **why** it changed, and **what you verified**.
- Reference any related issues using `Closes #123` or `Fixes #123`.
- Ensure the relevant verification commands pass before requesting review.
- Update documentation if your change affects setup steps, environment variables, or user-visible behavior.

## License

By contributing, you agree that your contributions are made under the repository license: **AGPL-3.0**.

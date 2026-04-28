# Contributing

Thanks for contributing to FUTUR.IA.

## Before you start

Make sure you can run the project locally:

```bash
npm run setup:all
npm run dev
```

Read these first if your change touches the public workflow or repo conventions:

- [README.md](./README.md)
- [docs/GETTING-STARTED.md](./docs/GETTING-STARTED.md)
- [docs/DEVELOPMENT.md](./docs/DEVELOPMENT.md)
- [docs/TESTING.md](./docs/TESTING.md)
- [docs/CONFIGURATION.md](./docs/CONFIGURATION.md)

## Development workflow

A practical local loop is:

1. install dependencies
2. make the change
3. run the relevant verification commands
4. update docs if behavior or setup changed
5. open a pull request with a clear summary

## Verification expectations

Run the checks that match your change.

### Frontend or UI work

```bash
npm run build
```

### Backend logic or API work

```bash
cd backend && uv run pytest
```

### Reporting or contamination-policy work

```bash
npm run preflight
```

If your change crosses multiple areas, run more than one of the above.

## Code areas

- frontend app: `frontend/`
- backend app: `backend/app/`
- backend tests: `backend/tests/`
- docs: `docs/`

## Documentation changes

Please update docs when you change:

- setup steps
- required environment variables
- user-visible workflow behavior
- API or backend lifecycle behavior that contributors need to know about

At minimum, keep the affected file in sync with the code.

## Auth caveat

The committed frontend auth flow is a localStorage stub in `frontend/src/api/auth.js`. If you are changing login/register behavior, be explicit about whether you are:

- still working within the stubbed frontend-only auth path, or
- introducing a real backend auth implementation

## Pull request guidance

A good PR description includes:

- what changed
- why it changed
- what you verified
- any follow-up work or known limitations

## License

By contributing, you agree that your changes are made under the repository license: **AGPL-3.0**.

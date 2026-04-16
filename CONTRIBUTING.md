# Contributing

## Development Setup

This project uses [Poetry](https://python-poetry.org/) for dependency management and [Poe the Poet](https://poethepoet.naez.io/) as a task runner.

```bash
# Install dependencies (dev group is included by default)
poetry install

# Run tests
poetry test

# Type checking
poetry typecheck

# Lint
poetry lint

# Format
poetry format
```

## Running Tests

Tests live in the `tests/` directory:

```bash
poetry test
```

## Commit Convention

This project uses [Conventional Commits](https://www.conventionalcommits.org/):

- `feat:` new features
- `fix:` bug fixes
- `docs:` documentation changes
- `test:` test additions or changes
- `refactor:` code changes that neither fix bugs nor add features
- `chore:` maintenance tasks

## Pull Requests

1. Fork the repo and create a feature branch
2. Make your changes, add tests if applicable
3. Run `poetry test` and `poetry typecheck` to verify
4. Open a PR against `main`


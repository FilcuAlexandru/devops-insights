# Contributing

Thank you for helping. Set up and run everything with [docs/local-testing.md](docs/local-testing.md);
[docs/development.md](docs/development.md) explains the code layout and how to add technologies,
endpoints and pages.

## Workflow

1. Create a branch from `main`: `feat/<topic>`, `fix/<topic>` or `docs/<topic>`.
2. Make the change with tests. Run `make check` (lint, tests, Helm, version and monitoring sync).
3. Open a pull request. CI must pass and the change is merged with **squash and merge**.

`main` is protected: no direct pushes, every change goes through a pull request.

## Commit messages and pull request titles

[Conventional Commits](https://www.conventionalcommits.org/), because the squashed title becomes
the changelog line and the release notes:

```
feat: track GitHub releases
fix(collector): stop after a rate limit response
docs: explain the OpenShift routes
chore(deps): bump fastapi
```

Types: `feat`, `fix`, `docs`, `refactor`, `test`, `ci`, `build`, `chore`. Add `!` (for example
`feat!:`) or a `BREAKING CHANGE:` footer for incompatible changes.

## Code standards

- Code, comments and documentation are in English.
- Python is formatted and linted by Ruff; new behaviour needs tests; no test may call GitHub or
  Ollama.
- Database changes need an Alembic migration that works on a database that already holds data.
- Update `CHANGELOG.md` under **Unreleased** for anything a user would notice.

## Releases

Maintainers release with [docs/releasing.md](docs/releasing.md).

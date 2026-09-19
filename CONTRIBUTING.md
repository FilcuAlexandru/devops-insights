# Contributing

Thanks for wanting to help. This page is short on purpose; the details live in the guides.

To get everything running on your machine, start with [docs/local-testing.md](docs/local-testing.md).
To find your way around the code (and to add a technology, an endpoint or a page), read
[docs/development.md](docs/development.md).

## How a change goes in

1. Create a branch from `main`. Names like `feat/release-tracking`, `fix/rate-limit-message` or
   `docs/openshift-linux` make the history easy to read.
2. Make your change, and add tests for it. Before you push, run `make check`. It does the same
   things as the CI: linting, the tests, the Helm and version checks.
3. Open a pull request. It needs a green CI, and it is merged with **squash and merge**.

`main` is protected. Nothing is pushed to it directly; everything goes through a pull request.
[docs/git-workflow.md](docs/git-workflow.md) explains the checks, the rules and what to do when
something fails.

## Commit messages and pull request titles

Please use [Conventional Commits](https://www.conventionalcommits.org/). The title of a squashed
pull request ends up in the history and in the release notes, so it should say what the change does:

```
feat: track GitHub releases
fix(collector): stop after a rate limit response
docs: explain the OpenShift routes
chore(deps): bump fastapi
```

The usual types are `feat`, `fix`, `docs`, `refactor`, `test`, `ci`, `build` and `chore`. For a
change that breaks compatibility, add a `!` (`feat!: ...`) or a `BREAKING CHANGE:` line in the
body.

## What a good change looks like

- Code, comments and documentation are in English.
- Python passes Ruff, new behaviour has tests, and no test calls GitHub or Ollama.
- A database change comes with an Alembic migration that also works on a database that already has
  data in it.
- Anything a user would notice is added to `CHANGELOG.md`, under **Unreleased**.

## Releases

Whoever maintains the project cuts releases by following [docs/releasing.md](docs/releasing.md).

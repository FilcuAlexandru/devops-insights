# Releasing

A release is made from `main` by pushing a version tag. (How changes get onto `main` in the first
place is described in [git-workflow.md](git-workflow.md).) After that, the pipeline does the rest:
tests, images, the Helm chart and the GitHub Release page.

## Setting up the repository (once)

Do this after the first push. Everything is under the repository's **Settings** on GitHub.

| Where | What to set |
|---|---|
| General | Allow only **squash merging**, and turn on **Automatically delete head branches** |
| Actions → General | Workflow permissions: **Read repository contents and packages permissions**. Leave "Allow GitHub Actions to create and approve pull requests" off |
| Rules → Rulesets | Protect the default branch: require a pull request, require the status checks `Backend (lint, migrations, tests)`, `Frontend (unit tests)`, `Helm and monitoring` and `Build images`, block force pushes, require a linear history |
| Rules → Rulesets | Protect the tags that match `v*` so that nobody can move or delete them |
| Advanced Security | Turn on the dependency graph, Dependabot alerts and security updates, secret scanning with push protection, and private vulnerability reporting |
| General → Features | Turn on Issues, and add topics such as `devops`, `fastapi`, `kubernetes`, `openshift`, `helm`, `argocd`, `prometheus`, `grafana` and `ollama` |

If you are the only maintainer, don't require approvals in the ruleset: you can't approve your own
pull request. Requiring the pull request and the green checks is enough.

The rulesets can only offer a status check after it has run once, so create them after the first
CI run. No secrets are needed anywhere: the workflows use the built-in `GITHUB_TOKEN`.

### Container packages

The first time the pipeline publishes, GitHub creates the packages `devops-insights-backend` and
`devops-insights-frontend`, and later the chart. New packages are **private**. Make them public so
that clusters and other people can pull them without credentials: open each package, go to
**Package settings → Change visibility → Public**, and check that it is connected to the
repository.

One more thing that bites people: packages are not deleted together with their repository. If you
ever delete and recreate the repository, delete its old packages first, otherwise the new
workflow is denied when it tries to push.

## Making a release

Start from an up-to-date `main`:

```bash
git checkout main && git pull
```

Choose the next version by [Semantic Versioning](https://semver.org/): a fix is a patch, a new
feature is a minor version, and anything incompatible is a major one. Then write it into every
file that carries the version:

```bash
scripts/version.sh set 0.3.0
```

Open `CHANGELOG.md`, move what is under **Unreleased** into a new `## [0.3.0] - YYYY-MM-DD`
section, and update the links at the bottom. Then check, commit and open a pull request. Releases
go through review like any other change:

```bash
make check
git checkout -b release/v0.3.0
git commit -am "chore(release): v0.3.0"
git push -u origin release/v0.3.0
```

When the pull request has been merged, tag the merge commit and push the tag:

```bash
git checkout main && git pull
git tag -a v0.3.0 -m "v0.3.0"
git push origin v0.3.0
```

## What happens when you push a tag

`.github/workflows/release.yml` runs these jobs, one after the other:

| Job | What it does |
|---|---|
| Verify | Fails unless the tag, every version field (`scripts/version.sh check`) and the changelog agree |
| Tests | Runs the backend and frontend tests against PostgreSQL |
| Images | Builds `devops-insights-backend` and `-frontend` for `linux/amd64` and `linux/arm64`, tags them `0.3.0`, `0.3`, `0` and `latest`, attaches an SBOM and signed build provenance, and scans them with Trivy, failing on critical vulnerabilities |
| Chart | Publishes the Helm chart to `ghcr.io/<owner>/charts` as an OCI artifact |
| Release | Creates the GitHub Release, with the changelog entry and the list of artifacts as its notes |

Pushes to `main` publish development images too, tagged `main` and `sha-<commit>` (that is
`ci.yml`). The `latest` tag only ever moves on a release.

## Using a release

```bash
docker pull ghcr.io/filcualexandru/devops-insights-backend:0.3.0
```

```bash
helm install devops-insights oci://ghcr.io/filcualexandru/charts/devops-insights --version 0.3.0 -n devops-insights --create-namespace
```

If you have the GitHub CLI, you can verify where an image came from:

```bash
gh attestation verify oci://ghcr.io/filcualexandru/devops-insights-backend:0.3.0 --owner FilcuAlexandru
```

With Argo CD, point `targetRevision` of the Application at the tag (`v0.3.0`) instead of `main`,
and it deploys exactly that release.

## When a release fails

- **Verify fails:** some version field is out of date. Fix it on `main`, delete the tag
  (`git push origin :refs/tags/v0.3.0` and `git tag -d v0.3.0`) and tag again.
- **Trivy fails on an image:** update the base image or the dependency it complains about, merge,
  and re-tag as above.
- **Never move a tag that has already published images.** Ship a new patch version instead.

## Hotfixes

Branch from the tag (`git checkout -b hotfix/0.3.1 v0.3.0`), make the fix, open a pull request to
`main`, and release the next patch version.

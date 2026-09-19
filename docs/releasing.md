# Releasing

Releases are cut from `main` by pushing a version tag. The pipeline does the rest.

## One-time repository setup

Do this once, on GitHub, after the first push (the click path is in the repository settings):

| Where | Setting |
|---|---|
| Settings → General | Enable **Allow squash merging** only; **Automatically delete head branches** on |
| Settings → Actions → General | Workflow permissions: **Read repository contents**; allow GitHub Actions to create pull requests off |
| Settings → Rules → Rulesets (or Branches) | Protect `main`: require a pull request, require the status checks `Backend (lint, migrations, tests)`, `Frontend (unit tests)`, `Helm and monitoring` and `Build images`, block force pushes, require linear history |
| Settings → Rules → Rulesets | Protect tags matching `v*`: only maintainers can create them, no deletion |
| Settings → Code security | Enable **Dependabot alerts**, **Dependabot security updates**, **Secret scanning**, **Push protection** and **Private vulnerability reporting** |
| Settings → General → Features | Enable **Issues**; add topics such as `devops`, `fastapi`, `kubernetes`, `openshift`, `helm`, `argocd`, `prometheus`, `grafana`, `ollama` |

No secrets are needed: the workflows use the built-in `GITHUB_TOKEN`.

### Container packages

The first publish creates the packages `devops-insights-backend`, `devops-insights-frontend` and
the chart under **Packages** on your profile. New packages are **private** by default. Make them
public so clusters can pull without credentials: open each package → **Package settings →
Change visibility → Public**, and **Connect repository** so it appears on the repository page.

## Cutting a release

1. Update from `main`:

```bash
git checkout main && git pull
```

2. Choose the version ([Semantic Versioning](https://semver.org/): `fix` → patch, `feat` → minor,
   breaking change → major) and write it into every file that carries it:

```bash
scripts/version.sh set 0.3.0
```

3. Move the **Unreleased** entries of `CHANGELOG.md` under a new heading `## [0.3.0] - YYYY-MM-DD`
   and update the compare links at the bottom.
4. Check, commit and open a pull request (releases go through review like any change):

```bash
make check
git checkout -b release/v0.3.0
git commit -am "chore(release): v0.3.0"
git push -u origin release/v0.3.0
```

5. After the pull request is merged, tag the merge commit and push the tag:

```bash
git checkout main && git pull
git tag -a v0.3.0 -m "v0.3.0"
git push origin v0.3.0
```

## What the tag triggers (`.github/workflows/release.yml`)

| Job | Result |
|---|---|
| Verify | Fails unless the tag, every version field (`scripts/version.sh check`) and the changelog agree |
| Tests | Backend and frontend tests against PostgreSQL |
| Images | Multi-architecture (`linux/amd64`, `linux/arm64`) images `ghcr.io/<owner>/devops-insights-backend` and `-frontend` tagged `0.3.0`, `0.3`, `0` and `latest`, with an SBOM, signed build provenance and a Trivy scan that fails on critical vulnerabilities |
| Chart | The Helm chart pushed as an OCI artifact to `ghcr.io/<owner>/charts` |
| Release | A GitHub Release whose notes are the changelog entry plus the artifact list |

Pushes to `main` publish development images tagged `main` and `sha-<commit>` (`ci.yml`).

## Using a release

```bash
docker pull ghcr.io/filcualexandru/devops-insights-backend:0.3.0
```

```bash
helm install devops-insights oci://ghcr.io/filcualexandru/charts/devops-insights --version 0.3.0 -n devops-insights --create-namespace
```

Verify an image's provenance (needs the GitHub CLI):

```bash
gh attestation verify oci://ghcr.io/filcualexandru/devops-insights-backend:0.3.0 --owner FilcuAlexandru
```

For Argo CD, point `targetRevision` of the Application at a tag (`v0.3.0`) instead of `main` to
deploy exactly that release.

## If a release fails

- **Verify fails:** a version field is out of date. Fix it on `main`, delete the tag
  (`git push origin :refs/tags/v0.3.0`, `git tag -d v0.3.0`) and tag again.
- **Trivy fails on an image:** update the base image or dependency, merge, and re-tag as above.
- **Never move a tag that already published images.** Publish a new patch version instead.

## Hotfix

Branch from the tag (`git checkout -b hotfix/0.3.1 v0.3.0`), fix, open a pull request to `main`,
and release the next patch version.

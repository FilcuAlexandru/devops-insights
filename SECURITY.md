# Security policy

## Which versions get fixes

Security fixes go into the latest released minor version.

## Reporting a vulnerability

Please don't open a public issue for a vulnerability. Use GitHub's private reporting instead:
open the **Security** tab of this repository and choose **Report a vulnerability**. I will answer
within a few days.

## What this project is, and what it isn't

DevOps Insights is a personal lab project, and it is built like one on purpose. Every component
with a login uses `admin` / `admin`, and the web application has no login at all. That makes it
pleasant to explore and unsafe to expose.

So please **don't put a default installation on the internet**. If you want to, first change the
credentials (see [docs/observability.md](docs/observability.md) and the Helm values), put the
application behind some form of authentication, and keep the secrets in a proper secret store.

The project only reads public data from GitHub and does not collect any personal data.

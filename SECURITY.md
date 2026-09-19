# Security policy

## Supported versions

Security fixes are made for the latest released minor version.

## Reporting a vulnerability

Please **do not open a public issue**. Use GitHub's private reporting:
**Security → Report a vulnerability** on this repository. You will get an answer within a few days.

## Scope and known trade-offs

DevOps Insights is a personal lab project. By design, every component that has a login uses
`admin` / `admin` and the web application has no login of its own. **Do not expose a default
deployment to the internet.** Before doing so, change the credentials (see `docs/observability.md`
and the Helm values), put the application behind authentication, and use an external secret store.

Only public data is read from GitHub; no personal data is collected.

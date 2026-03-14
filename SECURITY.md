# Security Policy

## Supported Versions

Only the latest commit on the `main` branch receives security fixes.

| Version | Supported |
| ------- | --------- |
| main    | Yes       |
| Other   | No        |

## Reporting a Vulnerability

Report vulnerabilities using [GitHub Private Security Advisories](https://github.com/williamzujkowski/handwright/security/advisories/new).

Do not open public issues for security vulnerabilities.

Include in your report:
- Description of the vulnerability and its potential impact
- Steps to reproduce
- Affected component (backend, Docker image, dependency)
- Any suggested mitigations, if known

## Response Timeline

| Milestone       | Target     |
| --------------- | ---------- |
| Acknowledgment  | 7 days     |
| Status update   | 14 days    |
| Fix target      | 30 days    |

Complex vulnerabilities may require more time. You will be kept informed of progress.

## Scope

The following are in scope:

- Python backend (`engine/`)
- Web frontend served by the backend (`web/`)
- Docker images and `docker-compose.yml` configuration
- Direct dependencies declared in `pyproject.toml`

## Out of Scope

The following are not covered by this policy:

- Self-hosted deployments and custom configurations
- Third-party services or infrastructure not maintained in this repository
- Vulnerabilities in transitive dependencies without a direct exploit path
- Issues requiring physical access to the host system

## Disclosure

Once a fix is available, a security advisory will be published on the repository. Credit will be given to reporters unless anonymity is requested.

# Slight76 standards marketplace

The index for the Slight76 team standards handbooks: where each standard lives, how developers and AI agents install them as skills, and the shared tooling that keeps them consistent. Standards are written for a small team and its agents; there is no separate corporate-governance layer.

## The handbooks

| Repository | Covers | Rule prefixes |
| --- | --- | --- |
| [architecture-standards](https://github.com/Slight76/architecture-standards) | Solution design, ADR process, frontend/backend architecture, CQRS, middleware, OpenAPI, HTTP APIs, contracts, messaging, integration | SA, FE, UX, BE, CQRS, MW, OAS, API, CON, EVT, RES, INT |
| [engineering-standards](https://github.com/Slight76/engineering-standards) | Branching and commits, code review, testing, backend/frontend implementation, agent development, adoption process | TEST, AGT, BE (impl), FE (impl), SCM, REV |
| [operations-standards](https://github.com/Slight76/operations-standards) | Delivery pipelines, observability, SLOs, incident response, platform and infrastructure (Fly.io, Docker), backup/DR | CICD, OBS, SLO, PL, INF, CFG, INC, TOIL, BDR |
| [data-standards](https://github.com/Slight76/data-standards) | Database architecture and design, naming, Postgres practices, EF Core migrations and recovery, persistence, caching | DB, MIG, DR, DATA, CACHE, NAME, PGX |
| [security-standards](https://github.com/Slight76/security-standards) | Application security, identity, CORS, secrets, threat modeling, CI/CD supply chain, dependencies/SBOM | SEC, IAM, CORS, SECR, TM, SCS, DEP |
| standards-marketplace (this repo) | Governance, templates, consumer kit, shared tooling, rule index | GOV |

Every rule ID across all handbooks is listed in [catalog/rule-index.json](catalog/rule-index.json).

## Read by task

| Task | Start with |
| --- | --- |
| New solution or service boundary | architecture-standards `docs/solution-architecture-standard.md` |
| API, contract, or message change | architecture-standards `docs/http-api-standard.md`, `docs/contracts-standard.md`, `docs/messaging-resilience-standard.md` |
| Branch, commit, PR, or code review | engineering-standards `docs/source-control-and-branching.md`, `docs/code-review-checklist.md` |
| Writing tests | engineering-standards `docs/testing-standard.md` |
| Building or changing an agent/skill | engineering-standards `docs/agent-development-standard.md` |
| CI/CD, deploy, Fly.io, Docker | operations-standards `docs/delivery-standard.md`, `docs/infrastructure-implementation-standard.md` |
| Logging, metrics, alerts, SLOs | operations-standards `docs/observability-standard.md`, `docs/slo-and-toil.md` |
| Incident or postmortem | operations-standards `docs/incident-response-and-postmortems.md` |
| Schema, query, migration, cache | data-standards `docs/design-standard.md`, `docs/migration-recovery-standard.md`, `docs/caching-standard.md` |
| Auth, secrets, CORS, security review | security-standards `docs/application-security-standard.md`, `docs/identity-standard.md`, `docs/secrets-management.md` |
| Adopting the standards in a repo | [consumer-kit](consumer-kit/README.md), engineering-standards `docs/adoption-process.md` |
| Governance, exceptions, ownership | [governance/team-operating-model.md](governance/team-operating-model.md), [templates/exception.md](templates/exception.md) |

## Install the handbooks as agent skills

| Agent | Command |
| --- | --- |
| Copilot CLI | `copilot plugin marketplace add Slight76/standards-marketplace` then `copilot plugin install data-standards@slight76-standards` (repeat per handbook) |
| Copilot cloud agent | copy [consumer-kit/copilot-setup-steps.yml](consumer-kit/copilot-setup-steps.yml) into the consuming repo |
| GitHub CLI (`gh skill`, any agent) | `gh skill install Slight76/data-standards data-standards --scope user --pin v1.0.0` |
| Claude Code | `/plugin marketplace add Slight76/standards-marketplace` then `/plugin install data-standards@slight76-standards` |
| Codex / others | append [consumer-kit/AGENTS.md.snippet](consumer-kit/AGENTS.md.snippet) and pin a checkout with `tooling/fetch_standards.py` |

The marketplace manifest is [.claude-plugin/marketplace.json](.claude-plugin/marketplace.json); each handbook is an Agent Plugins 1.0 plugin (`plugin.json` + `skills/<name>/SKILL.md`).

## Repository layout

| Path | Purpose |
| --- | --- |
| `catalog/` | `catalog.json` (GOV rules, retired EA rules) and the generated cross-handbook `rule-index.json` |
| `governance/` | Team operating model, ownership, change triggers |
| `templates/` | ADR, exception, evidence, agent bootstrap, `architecture-baseline.json` (schema v2) |
| `consumer-kit/` | Files to copy into an application repository |
| `tooling/` | `validate.py`, `check_adoption.py`, `fetch_standards.py`, tests, one-off migration script |
| `scaffold/` | Skeleton for a new `*-standards` repository |
| `.github/workflows/docs-lint.yml` | Reusable lint/validate workflow used by every handbook |

## Tooling

```sh
py tooling/validate.py --root ../data-standards          # any handbook (uses catalog/rule-index.json)
py tooling/check_adoption.py --baseline architecture-baseline.json --evidence implementation-evidence.json --standards-dir .standards
py tooling/fetch_standards.py --baseline architecture-baseline.json --dest .standards
py -m unittest discover -s tooling/tests
```

Python 3.9 or later. Validation checks documentation integrity only; it never attests runtime compliance.

## Versioning

Handbooks release independently with SemVer tags (`v1.0.0`). Consumers pin 40-character commit SHAs in `architecture-baseline.json`; the marketplace manifest pins the same SHAs. Rule IDs are never reused for a different meaning; retired rules are marked `Superseded` with a successor.

License: [MIT](LICENSE).

# ADR-0001: Adopt a standards marketplace as the index for the team handbooks

Status: Accepted

Date: 2026-10-06

Owner: @Slight76

## Context

The single `architecture-standards` repository (v0.3.0) framed the team's standards as an "enterprise architecture" program with a separate enterprise layer, one 111-rule catalog, and skill mirrors in three directories. It was hard to read, mixed five domains, and every agent had to be hand-wired to find it. The team is small; there is no enterprise function to govern.

## Decision

Split the standards into five domain handbooks (`architecture-standards`, `engineering-standards`, `operations-standards`, `data-standards`, `security-standards`) and create this repository as the index:

- `.claude-plugin/marketplace.json` lists each handbook as an Agent Plugins 1.0 plugin pinned to a tag and commit SHA, so Copilot CLI, Claude Code, and `gh skill` install them from one place.
- Shared tooling (`validate.py`, `check_adoption.py`, `fetch_standards.py`) and the reusable `docs-lint.yml` workflow live here and are used by every handbook.
- `architecture-baseline.json` schema v2 declares `standards[]` (repository, revision, catalogVersion) so an application can adopt several handbooks at pinned revisions (GOV-001).
- The former enterprise layer is retired. Its ownership and traceability intent moves into `governance/team-operating-model.md`; rules EA-001..EA-006 are marked Superseded by GOV-001 and are never renamed.
- Historic ADR-0001..0027 remain in `architecture-standards`; handbook catalogs reference them through `externalDecisions`.

## Alternatives

- Keep one repository and reorganize folders: simpler, but still one giant skill and no per-domain versioning or install.
- Six repositories without a hub: each consumer would have to discover and pin each handbook itself and tooling would be duplicated.
- Preserve git history with `git filter-repo`: rejected for v1.0.0; the pre-split state is tagged `v0.3.0-pre-split` in `architecture-standards`.

## Consequences

- Consumers migrate from v1 baselines (`standardsRepository`) to v2 (`standards[]`); the checker accepts v1 with a deprecation warning for one minor release.
- Cross-handbook links are absolute GitHub URLs validated against `catalog/rule-index.json`.
- Release requires tagging each handbook and updating SHAs here.

## Traceability

GOV-001; EA-001..EA-006 (Superseded); architecture-standards ADR-0028 (retire enterprise layer), ADR-0029 (repository split), ADR-0030 (multi-repo baseline), ADR-0031 (skill distribution).

## Verification

`tooling/validate.py` passes on every handbook; `tooling/tests` green; `copilot plugin marketplace add Slight76/standards-marketplace` installs all five plugins.

## Approval

@Slight76, 2026-10-06, plan approved in the planning session that produced this split.

---
title: "Team operating model: ownership, registers, and change review"
status: proposed
version: 1.0.0
owner: "@Slight76"
supersedes: architecture-standards/enterprise/operating-model.md@c1bda3d
---
# Team operating model: ownership, registers, and change review

Baseline: 1.0.0. Applies when: a repository adopts any Slight76 standards handbook

Decision: [ADR-0001](../adr/0001-adopt-standards-marketplace.md). Rules become binding when this baseline is adopted; examples explain the policy and do not establish business requirements.

This is a small team's operating model. There is no separate corporate-governance layer: the handbooks in
[architecture](https://github.com/Slight76/architecture-standards), [engineering](https://github.com/Slight76/engineering-standards),
[operations](https://github.com/Slight76/operations-standards), [data](https://github.com/Slight76/data-standards), and
[security](https://github.com/Slight76/security-standards) are the standards, and this document describes who owns them and how they change.

## Decision layers and ownership

Solution architecture maps one business outcome to applications and stores. Domain handbooks define how each application is implemented and run. A decision belongs at the narrowest level that resolves its effects; changing one screen does not need a team-level ADR.

| Role | Responsibility |
| --- | --- |
| Solution owner | End-to-end design, dependencies, compatibility, operational readiness |
| Handbook maintainer | Domain standards, examples, validation tooling, and upgrades |
| Application owner | Implementation, runtime, incidents, evidence, and baseline pin |
| Data steward | Classification, quality, retention, and authorized use |

Names remain unassigned until the owner supplies them; do not fabricate an approval chain. One person may hold several roles but cannot omit the responsibilities.

## Registers

Maintain a lightweight application register, dependency map, and technology register (see [technology profile](../standards/technology-profile.md)). For each technology record purpose, selected version/range, support end, owner, status (evaluate/adopt/hold/retire), and upgrade plan. A product being named in an example does not add it to the register.

Classify system criticality from actual impact. Each tier needs measurable recovery/service expectations justified by that impact; do not assign invented uptime percentages. Record costs including operations, storage growth, backup retention, telemetry, licenses, and exit/migration work.

## Change and review triggers

A new trust boundary, persistent store, communication style, public contract break, service split, or reliability tier change requires a solution ADR and affected-owner review. Local refactoring within an adopted boundary requires normal code review. Emergency changes need a subsequent record and reconciliation; an emergency is not permission for permanent undocumented drift.

Accept, supersede, or reject ADRs with evidence. Preserve historical rationale and trace successor decisions. Rule IDs never get reused for different meanings. Track which applications adopt each immutable baseline; notify owners of material changes through pull requests on the consuming repository.

## Standards baseline declaration

Every application repository declares which handbooks it follows and at which immutable revision in `architecture-baseline.json`
(schema v2, see [template](../templates/architecture-baseline.json) and the [consumer kit](../consumer-kit/README.md)).
Agents and CI read the pinned revisions, never latest `main`. `tooling/check_adoption.py` verifies coverage of every rule in the
pinned catalogs and the structure of `implementation-evidence.json`; it does not attest runtime compliance.

## Adoption outcomes

A standards document is useful when an engineer or agent can select a default, understand its limits, implement it, and produce evidence. Evaluate adoption using escaped failures, onboarding time, exception age, and upgrade lag, not documentation volume. Maintain a migration path so an improved policy can reach existing applications.

## Rules and required evidence

| ID | Requirement | Verification |
| --- | --- | --- |
| GOV-001 | Every application repository MUST declare the standards repositories and immutable revisions it adopts in architecture-baseline.json. | tooling/check_adoption.py passes against the declared baseline |

Retired rules EA-001 through EA-006 (former corporate-governance layer) are recorded in [catalog/catalog.json](../catalog/catalog.json) as Superseded by GOV-001; ownership and traceability expectations above carry their intent.

## Exceptions

Use the [exception record](../templates/exception.md) for a departure. Record affected rules, scope, compensating controls, approval evidence, expiry, and migration path. Agents must not silently replace defaults.

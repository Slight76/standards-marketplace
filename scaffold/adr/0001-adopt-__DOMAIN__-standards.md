# ADR-0001: Adopt the __DOMAIN__ standards handbook

Status: Accepted

Date: __DATE__

Owner: @Slight76

## Context

The former single `architecture-standards` repository (v0.3.0) mixed every domain into one catalog and skill. __CONTEXT__

## Decision

Create `__NAME__` as the home for __DOMAIN__ standards, versioned independently from the other handbooks and installable as an agent skill. Documents moved here keep their rule IDs and historical ADR references; new documents are first drafts with `status: proposed`.

## Alternatives

- Keep the domain inside `architecture-standards`: rejected; one repository was too broad to read or install selectively.
- Rewrite all rules from scratch: rejected; existing rules are kept verbatim to preserve consumer baselines.

## Consequences

Consumers pin this repository in `architecture-baseline.json` (`standards[]`). Historic decisions remain in `architecture-standards/adr/` and are declared in `catalog/catalog.json` under `externalDecisions`.

## Traceability

Rule prefixes: __PREFIXES__. Related: standards-marketplace ADR-0001; architecture-standards ADR-0028..0031.

## Verification

`validate.py` passes; `docs.yml` green on `main`; the skill installs through the standards marketplace.

## Approval

@Slight76, __DATE__, plan approved in the split planning session.

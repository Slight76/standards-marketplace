# __NAME__

__DESCRIPTION__

Part of the Slight76 standards handbooks indexed at [standards-marketplace](https://github.com/Slight76/standards-marketplace). Written for a small team and its AI agents.

## Documents

| Document | Covers | Rule prefixes |
| --- | --- | --- |
__DOC_ROWS__

## Read by task

See [skills/__NAME__/SKILL.md](skills/__NAME__/SKILL.md).

## Install as an agent skill

| Agent | Command |
| --- | --- |
| Copilot CLI | `copilot plugin marketplace add Slight76/standards-marketplace` then `copilot plugin install __NAME__@slight76-standards` |
| GitHub CLI (any agent) | `gh skill install Slight76/__NAME__ __NAME__ --scope user --pin v1.0.1` |
| Claude Code | `/plugin marketplace add Slight76/standards-marketplace` then `/plugin install __NAME__@slight76-standards` |

## Layout

| Path | Purpose |
| --- | --- |
| `docs/` | Standards documents (frontmatter, applies-when, rule table) |
| `catalog/catalog.json` | Machine-readable rules; `externalDecisions` points at historic ADRs |
| `adr/` | Decisions local to this handbook |
| `skills/__NAME__/` | Agent skill and references |
| `templates/` | Templates specific to this domain (shared ones live in the marketplace) |

Validation: `py ../standards-marketplace/tooling/validate.py --root .`. License: [MIT](LICENSE).

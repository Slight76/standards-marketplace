# Consumer kit: use the handbooks from any application repo

Copy these files into each application repo so Copilot, Claude Code, and Codex all find the handbooks at the pinned commits.

| Kit file | Copy to | Used by |
| --- | --- | --- |
| `AGENTS.md.snippet` | append to `AGENTS.md` | Codex, Copilot, Claude Code (via import), others |
| `CLAUDE.md` | `CLAUDE.md` | Claude Code (`@AGENTS.md` import) |
| `copilot-instructions.md` | `.github/copilot-instructions.md` | Copilot |
| `copilot-setup-steps.yml` | `.github/workflows/copilot-setup-steps.yml` | Copilot cloud agent (materializes `.standards/` and `.agents/skills/`) |
| `.github/copilot/settings.json` | `.github/copilot/settings.json` | Copilot CLI (enables the handbook plugins for everyone in the repo) |

Also commit `architecture-baseline.json` from the [baseline template](../templates/architecture-baseline.json) (schema v2, one `standards[]` entry per handbook with a 40-character `revision`) and `implementation-evidence.json` from the [evidence template](../templates/implementation-evidence.json). See [adoption process](https://github.com/Slight76/engineering-standards/blob/main/docs/adoption-process.md).

## Getting the handbooks locally

Install the skills once per machine, or materialize a pinned checkout per repo:

| Agent | Command |
| --- | --- |
| Copilot CLI | `copilot plugin marketplace add Slight76/standards-marketplace` then `copilot plugin install <name>@slight76-standards` |
| GitHub CLI (any agent) | `gh skill install Slight76/<repo> <repo> --scope user --pin v1.0.1` |
| Claude Code | `/plugin marketplace add Slight76/standards-marketplace` then `/plugin install <name>@slight76-standards` |
| Pinned checkout | `python3 .standards/standards-marketplace/tooling/fetch_standards.py --baseline architecture-baseline.json` |

`<repo>`/`<name>` is one of `architecture-standards`, `engineering-standards`, `operations-standards`, `data-standards`, `security-standards`.

Keep `.standards/` in `.gitignore` (or use submodules) and keep it in sync with `architecture-baseline.json`; the pin must never track `main`.

## Agent notes

- **Codex** reads `AGENTS.md` from the repo root to the working directory within a 32 KiB budget; keep the snippet short. Cloud environments need a setup script that provides `.standards/`.
- **Claude Code** keeps files under about 200 lines; imports do not reduce context cost.
- **Copilot** does not reliably follow prose asking it to fetch other repositories; the setup-steps workflow materializes `.standards/` and copies each handbook's skill into `.agents/skills/` instead. All handbook repos are public, so no token is needed.
- **Windows:** avoid symlinks for these files. With `core.symlinks` off, git writes a tiny text file and agents silently get no instructions.

## Optional: autonomous loop with Noodle

[`noodle/`](noodle/README.md) holds a [Noodle](https://github.com/poteto/noodle) template: a `.noodle.toml`, the default `todos.md` backlog adapters, and `schedule`/`execute` skills that make every autonomous order read the pinned handbook skills first and finish with the baseline revision, rule IDs, and verification results the PR rules require. Adopt it only after the files above are in place.

## Smoke checks

- Codex: `codex "Summarize the current instructions."`
- Claude Code: `/context` shows `AGENTS.md` and `CLAUDE.md` loaded.
- Copilot CLI: `/skills list` shows the installed handbook skills.
- Ask any agent for the pinned revisions and the first document it will read.

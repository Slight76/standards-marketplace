# Noodle: an autonomous loop that follows the handbooks

[Noodle](https://github.com/poteto/noodle) is a skill-based agent orchestration loop. A scheduler
agent reads your backlog, writes orders, and the loop runs each order in an isolated git worktree
with a skill loaded as the agent's instructions. This template adds two skills (`schedule`,
`execute`) that make every order read the pinned standards handbooks first and leave the evidence
the code review rules expect.

## What is in this folder

| Path | Copy to (project root) | Purpose |
| --- | --- | --- |
| `.noodle.toml` | `.noodle.toml` | Supervised mode, Claude by default (Codex block commented), two concurrent sessions, todos.md adapters |
| `adapters/backlog-*` | `adapters/` | Noodle's default POSIX `sh` backlog adapters for `todos.md`, copied verbatim (must be executable) |
| `.agents/skills/noodle/` | `.agents/skills/noodle/` | Noodle's own CLI/skill-authoring skill, copied verbatim |
| `.agents/skills/schedule/SKILL.md` | `.agents/skills/schedule/` | Writes orders; every order names the handbook skills to read and carries acceptance criteria |
| `.agents/skills/execute/SKILL.md` | `.agents/skills/execute/` | How work is done: worktree, pinned handbooks, verification, Conventional Commits, evidence, REV-002 summary |
| `todos.md` | `todos.md` | Seed backlog in the default adapter format |
| `gitignore.snippet` | append to `.gitignore` | Ignores `.noodle/` runtime state and `.worktrees/` |

## Prerequisites

- The `noodle` binary (v0.1.5 or later): `brew install poteto/tap/noodle` on macOS; on Windows and
  Linux download the archive for your platform from
  [the latest release](https://github.com/poteto/noodle/releases/latest) and put the binary on
  `PATH`. Check with `noodle --version`.
- Claude Code or the Codex CLI installed and authenticated; Noodle spawns them as child processes.
- On Windows, the backlog adapters are POSIX `sh` scripts and Noodle runs them with `sh -c`, so
  Git for Windows' `usr\bin` directory (`sh`, `sed`, `grep`, `awk`; normally
  `C:\Program Files\Git\usr\bin`) must be on `PATH` for the process that runs `noodle start`.
  Check with `sh adapters/backlog-sync` from the project root; it prints one JSON line per item.
- The repository already uses the [consumer kit](../README.md): `AGENTS.md` snippet,
  `architecture-baseline.json` with pinned revisions, `implementation-evidence.json`, and the
  handbook skills available at `.agents/skills/<handbook>-standards/` (the
  `copilot-setup-steps.yml` workflow does this in CI; locally use `gh skill install` or
  `fetch_standards.py` and copy `.standards/*/skills/*` into `.agents/skills/`).

## Adopt it in a repository

1. Copy `.noodle.toml`, `adapters/`, `.agents/skills/noodle/`, `.agents/skills/schedule/`,
   `.agents/skills/execute/`, and `todos.md` to the project root, keeping the paths.
2. Pick a provider in `.noodle.toml`: keep the Claude block or swap in the commented Codex block.
3. Make the adapters executable and keep them that way in git:

   ```sh
   chmod +x adapters/backlog-*
   git add adapters && git update-index --chmod=+x adapters/backlog-*
   ```

4. Append `gitignore.snippet` to `.gitignore`.
5. Replace the first line of `todos.md` under `## Inbox` with a real task (`<!-- next-id -->`
   must stay one above the highest item number; `backlog-add` uses it for the next ID). Give each
   item acceptance criteria (in the title or a linked plan); the schedule skill carries them into
   the order prompt.
6. Verify discovery: `noodle skills` must list `noodle`, `schedule`, `execute`, and the handbook
   skills; `noodle status` must report no config diagnostics.
7. Check out the integration branch you want worktrees merged into (not `main`; see "Do not"),
   then run `noodle start` (or `noodle start --once` for a single cycle). The first run scaffolds
   `.noodle/`.

## How the skills use the handbooks

- **schedule** reads `.noodle/mise.json`, picks one backlog item per order, routes to
  `routing.defaults`, and writes `.noodle/orders-next.json`. Every order prompt must name the
  handbook skills that govern the change (always `engineering-standards`, plus
  `architecture-standards`, `operations-standards`, `data-standards`, or `security-standards` by
  domain) and carry the item's acceptance criteria. The routing table mirrors the
  [marketplace README](../../README.md#read-by-task).
- **execute** creates a prefixed worktree branch (SCM-001), reads the named handbook skills and
  their `references/read-by-task.md` at the revisions pinned in `architecture-baseline.json`
  (AGT-001), stays within scope, runs the commands the repository's `AGENTS.md` documents, updates
  `implementation-evidence.json` and runs `check_adoption.py`, commits with Conventional Commits
  (SCM-002), and ends with a summary stating the baseline revision, rule IDs applied, and
  verification commands with results so the merge-back PR satisfies REV-002.
- **noodle** is Noodle's own skill: CLI reference, `.noodle.toml` options, and how to write more
  task-type skills (for example a review stage that follows `execute`).

Noodle merges finished worktrees into the integration branch; the pull request from that branch
to `main` still needs a human approval (REV-001) and a reviewer who re-runs at least one evidence
claim (REV-003). `mode = "supervised"` keeps a human in that merge step.

## Switching the backlog to GitHub Issues later

The backlog is whatever the four adapter scripts say it is. `sync` prints one JSON object per
item (`id`, `title`, `status`, optional extra fields), `add` reads a JSON payload and prints the
new ID, `done <id>` closes an item, and `edit <id>` retitles it. To use GitHub Issues, write four
scripts around `gh issue list --json`, `gh issue create`, `gh issue close`, and `gh issue edit`,
point `[adapters.backlog.scripts]` at them, and delete `todos.md`. Contract and examples:
[Noodle adapters](https://poteto.github.io/noodle/concepts/adapters). Issue text is untrusted
input to the agents; the skills already say so.

## Do not

- Do not run the loop with the root checkout on `main`. Worktrees merge into the branch that is
  checked out; keep `main` behind a pull request and branch protection (SCM-001, SCM-003).
- Do not switch to `mode = "auto"` until several supervised cycles have merged cleanly and
  reviewers have found the summaries accurate (REV-003).
- Do not raise `max_concurrency` above the number of worktrees you are willing to review at once.
- Do not bake task details into `schedule` or `execute`. Skills describe process; the order prompt
  carries the task. Add a new task-type skill instead of special-casing a feature.
- Do not run `noodle start` from CI or on a shared machine without a spend limit; each stage is a
  billable agent session.

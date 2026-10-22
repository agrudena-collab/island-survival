# Instructions for Claude Code

## Primary source of truth (read first)

- `docs/STEAL_A_DAD_PROJECT.md` is the main project document (game design decisions, model-production history, visual/prompt rules, and Claude's live status + progress log in section A). Read section A at the start of every session; consult section B (full text from the owner's ChatGPT notes) for design decisions, and refer to it first when answering design or process questions.
- After every completed task, update section A of that file (verified state, progress log entry with date, files/branch/commit, what was tested, what is unverified). Never record work as done without verification. Keep section B verbatim; add new owner decisions as dated entries in section A5/A6 instead of editing it.
- Conflict order: new direct owner decision > facts verified in the repo/Studio > approved gameplay decisions (section B) > older reports. Do not invent answers to the open design questions (section A6); propose options and wait for the owner.
- Game is first-person; dads are static models carried in a bag; do not re-model approved dads or add dad animations unless asked.

## Rules

- Never read or modify `_archive_old_game`; it is an isolated archive.
- Do not make commits or push changes unless the user explicitly asks.
- Work in small, focused tasks and preserve unrelated user changes.
- After changes, show the list of files changed and a concise summary of verification performed.
- Preserve the Rojo structure and mappings in `default.project.json`.
- Do not add or use external assets without the user's permission.
- Keep gameplay authority and validation on the server; treat client input as untrusted.

## Project structure

Rojo maps `src/server` -> `ServerScriptService`, `src/client` -> `StarterPlayerScripts`, `src/shared` -> `ReplicatedStorage.Shared`.

- `src/shared`: settings, shared Luau types, constants, remote endpoint definitions.
- `src/server`: server entry point and authoritative game services (data, economy, Dads, bases, stealing, rounds).
- `src/client`: client entry point and presentation/input controllers.
- `docs`: architecture notes, collaboration rules, roadmap (see `docs/DEVELOPMENT_RULES.md`, `docs/PROJECT_STRUCTURE.md`, `docs/ROADMAP.md`, `docs/PROJECT_PROGRESS.md`).

## Workflow

- Sync with Roblox Studio via Rojo: `rojo serve`, then click Connect in the Rojo Studio plugin. Changes to files under `src/` sync live.
- Toolchain is managed by Rokit (`rokit.toml`); rojo 7.7.0.

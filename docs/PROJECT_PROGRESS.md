# Project progress and architecture

Last updated: 2026-09-26 18:08 MSK  
Project: Steal a Dad  
Repository: agrudena-collab/island-survival  
Project owner: Yaroslav

This file is the project's living source of truth for verified progress, active work, architecture decisions, dependencies, and the transition to the next tasks.

## Update rules

Only the project owner updates this file after reviewing evidence or merging a Pull Request. Partners report results through their feature branches and Pull Requests but do not edit this tracker in parallel.

Status values:

- `PLANNED` - accepted task that has not started.
- `IN PROGRESS` - work is currently being performed.
- `READY FOR REVIEW` - implementation is pushed and awaits review.
- `BLOCKED` - work cannot continue until the stated dependency is resolved.
- `DONE` - the result was verified and merged into `main`.

For every status change, record the branch, Pull Request, verification evidence, and next action. Do not mark a task `DONE` only because code was written.

## Current verified state

| Item | Status | Evidence | Next action |
| --- | --- | --- | --- |
| Repository structure and development rules | DONE | `AGENTS.md`, `docs/DEVELOPMENT_RULES.md` | Preserve existing Rojo mappings and server authority |
| Session player profile and Cash API | DONE | Pull Request 2 merged into `main`; main commit `22fd210` | Keep API compatible |
| Cash persistence through DataStore | READY FOR REVIEW | Branch `feature/player-data-persistence-m2`; commit `dbf66fe`; Studio reload retained `Cash = 400`; no DataStore error was visible in the supplied Output | Create and review the Pull Request into `main` |
| Partner Cash HUD | PLANNED | Assigned two-day partner plan | Implement in `feature/ui-cash-hud-m1` |
| Partner map blockout | PLANNED | Assigned two-day partner plan | Implement in `feature/map-blockout-m1` |
| Server base assignment | PLANNED | Owner two-day plan | Start after persistence is merged |

## Architecture snapshot

### Rojo mapping

| Roblox container | Repository path | Responsibility |
| --- | --- | --- |
| `ServerScriptService` | `src/server` | Authoritative gameplay services and validation |
| `StarterPlayerScripts` | `src/client` | Player UI, input, prompts, and camera behavior |
| `ReplicatedStorage.Shared` | `src/shared` | Shared definitions, configuration, and Remote declarations |
| Project documentation | `docs` | Rules, progress, decisions, and technical notes |

The mappings in `default.project.json` must not be changed without a separate architecture decision.

### Server service startup order

The current startup order in `src/server/Main.server.lua` is:

1. `PlayerDataService`
2. `EconomyService`
3. `DadService`
4. `BaseService`
5. `StealService`
6. `RoundService`

All purchases, ownership changes, Cash changes, base assignment, and steal validation remain server-authoritative. Client requests are treated as untrusted input.

### Player data

| Field | Current role | Persistence |
| --- | --- | --- |
| `Version` | Saved-data schema version | Saved |
| `Cash` | Player currency | Saved |
| `OwnedDads` | Future owned Dad records | Not saved yet |
| `BaseId` | Base assigned in the current server | Session only |

Current DataStore: `StealADad_PlayerData_v1`

Current persisted payload:

```lua
{
    Version = 1,
    Cash = number,
}
```

Do not add fields to the persisted payload without an explicit schema decision and a migration plan.

### Base and map contract for the MVP

The MVP is configured for eight players, so the blockout contains eight bases.

| Required object | Required name |
| --- | --- |
| Root map model | `MapBlockout` |
| Bases folder | `Bases` |
| Base models | `Base_01` through `Base_08` |
| Spawn inside each base | `PlayerSpawn` |
| Dad slot folder inside each base | `DadSlots` |
| Dad slots inside each base | `Slot_01` through `Slot_06` |
| Shared center | `Center` |
| Future Dad spawn area | `DadSpawnZone` |

`BaseService` must fail safely and use `warn` when required map objects are absent. It must not trust the client to select or claim a base.

## Active two-day sprint

### Owner tasks

| ID | Day | Task | Branch | Allowed files | Status | Depends on |
| --- | --- | --- | --- | --- | --- | --- |
| OWNER-01 | 1 | Create, review, and merge the Cash persistence Pull Request | `feature/player-data-persistence-m2` | `src/server/Services/PlayerDataService.lua` | READY FOR REVIEW | None |
| OWNER-02 | 1 | Implement server base assignment and release | `feature/base-assignment-m3` | `BaseService.lua`, required BaseId methods in `PlayerDataService.lua` | PLANNED | OWNER-01 |
| OWNER-03 | 2 | Review partner Cash HUD | Partner Pull Request | Review only | PLANNED | PARTNER-01 |
| OWNER-04 | 2 | Validate the map naming contract | Partner Pull Request | Review only | PLANNED | PARTNER-02 |
| OWNER-05 | 2 | Test unique base assignment with at least two players | `feature/base-assignment-m3` | Server files only | PLANNED | OWNER-02 and map contract |
| OWNER-06 | 2 | Push BaseService and open a Pull Request | `feature/base-assignment-m3` | Server files only | PLANNED | OWNER-05 |

### Partner tasks

| ID | Day | Task | Branch | Allowed files | Status | Deliverable |
| --- | --- | --- | --- | --- | --- | --- |
| PARTNER-01 | 1 | Implement responsive Cash HUD | `feature/ui-cash-hud-m1` | `src/client/Controllers/UIController.lua` | PLANNED | Pull Request, HUD screenshot, Output screenshot |
| PARTNER-02 | 2 | Create the eight-base map blockout | `feature/map-blockout-m1` | `assets/map/StealADadMap_Blockout.rbxmx`, `docs/MAP_BLOCKOUT.md` | PLANNED | Pull Request, top-view screenshot, player-view screenshot |

### BaseService acceptance criteria

- Each connected player receives one free base.
- Two players cannot own the same base.
- The base receives `OwnerUserId` and `OwnerName` attributes.
- The player is moved to the assigned base's `PlayerSpawn`.
- Respawning keeps the same base during the server session.
- Leaving releases the base and clears its owner attributes.
- A newly joined player can receive a released base.
- Missing map objects generate a clear warning instead of crashing the server.
- The client cannot select or assign a base.
- A two-player Studio test completes without critical BaseService errors.

## Pull Request gates

A task can move to `DONE` only when all applicable checks pass:

- The Pull Request contains one focused task.
- Only allowed files changed.
- `git diff --check` passes.
- `rojo build default.project.json` succeeds for code changes.
- Roblox Studio Play Mode verifies the changed behavior.
- Multiplayer behavior is tested when the task involves player interaction.
- Output contains no critical error caused by the change.
- The owner reviewed and merged the Pull Request.
- This tracker was updated after the merge.

A successful Rojo build confirms project construction but does not replace Roblox Studio runtime testing.

## Preliminary milestone queue

The order below is provisional. A milestone starts only after dependencies and acceptance criteria are confirmed.

| Milestone | Purpose | Dependency | Status |
| --- | --- | --- | --- |
| M1 | Session profile and Cash API | Project bootstrap | DONE |
| M2 | Persistent Cash | M1 | READY FOR REVIEW |
| M3 | Server base assignment | M2 and map contract | PLANNED |
| M4 | Dad catalog and server spawning | M3 | PLANNED |
| M5 | Server-validated Dad purchase and Cash spending | M4 | PLANNED |
| M6 | Dad placement and passive income | M5 | PLANNED |
| M7 | Server-validated stealing and protection rules | M6 | PLANNED |
| M8 | Persist `OwnedDads` with a versioned migration | Stable Dad record schema | PLANNED |
| M9 | Complete MVP UI and interaction feedback | Stable server events | PLANNED |
| M10 | Multiplayer balance, exploit checks, and release testing | Complete MVP loop | PLANNED |

## Decision log

| Date | Decision | Reason |
| --- | --- | --- |
| 2026-09-26 | Work only through feature branches and Pull Requests | Protect `main` and separate two developers' changes |
| 2026-09-26 | Keep gameplay authority on the server | Prevent clients from granting Cash, ownership, bases, or successful steals |
| 2026-09-26 | Use separate owner and partner file areas during the two-day sprint | Avoid merge conflicts |
| 2026-09-26 | Keep `BaseId` session-only | A base belongs to one running server and can be reassigned in another session |
| 2026-09-26 | Use eight base models for the MVP | `Config.MaxPlayersPerServer` is currently 8 |
| 2026-09-26 | Use standard Roblox parts for the first map blockout | Validate layout before spending time on final art |

## Progress update template

Copy this section when a task changes status:

```markdown
### YYYY-MM-DD TASK-ID

- Status:
- Owner:
- Branch:
- Pull Request:
- Files changed:
- Verification performed:
- Evidence:
- Known limitations:
- Architecture decision:
- Next action:
```

## Immediate next actions

1. Open and review the Pull Request for `feature/player-data-persistence-m2`.
2. Merge it only after confirming the diff and completed Studio test.
3. Update local `main`.
4. Start `feature/base-assignment-m3`.
5. Receive the partner's PARTNER-01 evidence and review the HUD Pull Request.
6. Update this tracker after every reviewed merge.

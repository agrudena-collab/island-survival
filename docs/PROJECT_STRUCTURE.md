# Project structure

The Rojo project maps `src/server` to `ServerScriptService`, `src/client` to `StarterPlayerScripts`, and `src/shared` to `ReplicatedStorage.Shared`.

- `src/shared`: settings, shared Luau types, constants, and remote endpoint definitions.
- `src/server`: server entry point and authoritative game services for data, economy, Dads, bases, stealing, and rounds.
- `src/client`: client entry point and presentation/input controllers.
- `docs`: architecture notes, collaboration rules, and roadmap.

Keep gameplay decisions and validation on the server. Client modules should request actions through remotes and render server-confirmed state.

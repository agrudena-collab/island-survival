# Development rules

- Make small, reviewable changes focused on one feature or bug.
- Keep the Rojo mappings in `default.project.json` intact unless a structural change is required.
- Put shared definitions in `src/shared`, authoritative logic in `src/server`, and UI/input behavior in `src/client`.
- Validate all purchases, ownership changes, and steal requests on the server.
- Never commit or push without an explicit user request.
- Do not modify `_archive_old_game` or add external assets without permission.
- After each change, report the files changed and the verification performed.

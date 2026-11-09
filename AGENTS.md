# Instructions for AI coding agents

- Never read or modify `_archive_old_game`; it is an isolated archive.
- Do not make commits or push changes unless the user explicitly asks.
- Work in small, focused tasks and preserve unrelated user changes.
- After changes, show the list of files changed and a concise summary.
- Preserve the Rojo structure and mappings in `default.project.json`.
- Do not add or use external assets without the user's permission.
- Keep gameplay authority and validation on the server; treat client input as untrusted.
- Follow `docs/DEVELOPMENT_RULES.md` for project-specific conventions.

## Хитбоксы биомов и зданий (правило на будущее)

- **Здания на биомах: камера не должна залетать внутрь.** У каждого здания без интерьера (соседские дома, магазины-декорации, прочие декоративные строения) обязателен сплошной коллайдер на весь объём с `CanCollide=true` и `CanQuery=true`; меши стен и крыш — `CanQuery=true`. Внутри такого здания всегда должна быть модель/закрытый объём — никаких пустот, в которые проваливается камера или игрок. У зданий с интерьером (в которые входят) камера допускается внутрь, но меши стен/крыш всё равно `CanQuery=true`.
- **Деревья:** у стволов и у крон есть коллайдеры (крону — по bbox, чуть меньше визуала). Низкие кусты/декор ниже ~2.5 студов можно оставлять проходимыми.
- **Камни и крупный декор:** мелкие (высота < ~2.5) — `CanCollide=false`; крупные — коллайдер по форме и не выше камня, чтобы можно было перешагнуть/запрыгнуть, а не упираться как в стену.
- **После каждого импорта биома/района — аудит хитбоксов:** проходимость дверей и проёмов (капсула r≈1.25, h≈5), лестницы/выходы на твёрдый настил; видимые меши без коллайдера там, где надо упираться (стены, заборы, крупная мебель); коллайдеры без визуала (невидимые стены вне Bounds); коплонарные видимые поверхности (мерцание); детали под землёй/в воздухе; стандартный Baseplate на уровне земли (убрать или сделать невидимым полом).

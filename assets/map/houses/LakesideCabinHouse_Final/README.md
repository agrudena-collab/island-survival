# LakesideCabinHouse_Final

Working asset name only — "LakesideCabinHouse" does not create or rename a
"Fisherman Dad" character, change rarity, or edit the Dad catalog. This is
the owner-accepted final version of the lakeside fisherman's-cabin house
for "Steal a Dad!", superseding `LakesideCabinHouse` (baseline) and
`LakesideCabinHouse_Refined_v01` (the repair pass this was built from).

## Build

```
blender -b --factory-startup --python build_lakeside_cabin_house_final.py -- <output_dir>
```

Outputs: `LakesideCabinHouse.blend`, `LakesideCabinHouse.fbx`, `manifest.json`,
`apply_lakeside_cabin_house_colors.luau`, `previews/{front,lake_side,interior,top}.png`.

Import: ribbon **Import** (or `Ctrl+M`), uncheck **Upload to Roblox**. Then
paste `apply_lakeside_cabin_house_colors.luau` into the Studio command bar
(`Ctrl+Return` to run).

## Lineage and fixes applied in this pass (relative to the baseline)

Starting from `LakesideCabinHouse_Refined_v01/build_lakeside_cabin_house.py`
(itself a copy of the original baseline build script), the following
defects were found and corrected, each verified numerically and/or by
re-rendering before moving on:

- **Fix A** — the lake was built but completely hidden: `Yard_Ground` was a
  single slab covering the whole property, including the water footprint,
  at the exact same top height as the water surface. Split into four
  pieces that leave the lake/shore/bed exposed.
- **Fix B** — roof seams were tall vertical "fin" plates that stood up
  through the roof surface regardless of slope. Rebuilt as shallow strips
  that follow the roof's own slope normal.
- **Fix C** — the three fishing rods (and the pier's propped rod) were two
  disconnected pieces (a lone shaft and a lone grip, 1.1-1.9 studs apart).
  Rebuilt as single connected, tapered, slightly bent assemblies. The door
  threshold also silently ate 0.05 studs of clear height; now flush.
- **Fix D** — window casings (sill/head/jambs) overhang the bare glass by
  a fixed margin; the wall cutouts were sized to the glass only, so the
  casing was partly embedded in — and z-fought against — solid wall board.
  Cutouts now match the casing's true footprint.
- **Fix E** — one leaf of every door used a broken angle formula (an
  `abs()` evaluated before applying a sign), landing its centre on the
  interior side of the hinge instead of swinging outward. Both leaves of
  both doors now use one shared, sign-free swing angle.
- **Fix F** — the wall-mounted story props (tiny-fish portrait, dream-catch
  fish, and the new trophy fish) were positioned using the wall's
  centreline instead of its inner face, so they sat inside the solid board
  and were invisible from indoors. Repositioned proud of the inner face.
- **Fix G** — the kitchen counter top was one solid slab at the same Z
  band as the drop-in sink rim, burying the sink; only the free-standing
  faucet was visible. Counter top now has a rim-sized cutout.
- **Fix H/I/J** — the "fish on a cutting board" prop (owner-requested
  addition) went through several structural passes: disconnected knife
  stack → crooked rotated fish segments → a real gap between box
  segments → finally a single continuous Skin-modifier body (flat-shaded,
  no Subsurf) for a gap-free, low-poly-faceted silhouette, with the knife
  rebuilt end-to-end from shared points.
- **Fix K/L** — the fish's two-tone colour (per an owner reference photo)
  needed real geometry, not a material trick on a single-material tube; a
  second, smaller cream "belly" tube was added. The head originally
  tapered to a sharp point with a separate floating "lower jaw" box next
  to it; the chain now ends blunt and the jaw/mouth-notch is one
  physically touching assembly. Two eyes (mirrored) were added.
- **Fix M** — the family bench's two cushions and its blanket were three
  flat, equal-thickness, same-tone slabs (the blanket was literally the
  same colour and thickness as the blue cushion, reading as a third
  cushion). Rebuilt as bevelled two-layer cushions and a multi-layer
  folded blanket with a rolled edge and stripe accents; added a seat
  support rail and bevelled the frame.
- **Fix N** — `Yard_Ground` still extended under the ENTIRE lake-facing
  deck (and, in a smaller leftover corner, under the pier platform too),
  coplanar with the deck's own top surface at Z=0 — visible board
  z-fighting/crosshatching. Ground pieces now stop at the deck's edges;
  the deck's own surface provides the walking surface there.

- **Fix O** (2026-10-11, owner report of overlaps on the rear/kitchen walls):
  wall board courses now share one global grid (no stepped seams between
  segments); wall segments stop at the door jambs instead of running behind
  them; the kitchen wall cupboard no longer hangs in the left window and is
  flush on the wall; the tiny-fish portrait and dream-catch fish moved above
  that window (they overlapped the corner post and each other); the coat
  pegs/coats were floating 1.5 studs off the front wall in front of the
  front-right window and now hang on the wall between door and window.
  The pre-fix files are kept in `../LakesideCabinHouse_Final_prev_before_overlap_fix/`.
  **The .rbxm and the Studio review .rbxlx predate Fix O until re-imported.**

All fixes were applied directly in the procedural Blender builder (not as
Studio-only edits), re-verified after each change via fresh renders and,
for the structural ones, numeric bounding-box/overlap checks run against
the rebuilt `.blend`.

## Known gaps (carried over / still open)

- Continuous Play-mode walking (character controller, not point sampling)
  has not been performed on this Final build specifically.
- Carried-Dad clearance and live family/NPC pathfinding remain unverified
  — no carry gameplay or NPC AI exists to test against.
- Water/swim/fall behaviour: `Lake_Water_Surface` is a decorative,
  non-collide visual plane only.
- See `LakesideCabinHouse/DETAIL_CHECKLIST.md` (baseline folder) for the
  full per-item inventory table; the item set is unchanged by this pass
  except where noted above.

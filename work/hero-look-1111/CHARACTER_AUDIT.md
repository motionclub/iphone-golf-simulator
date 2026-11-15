# Character audit and before/after — 2026-11-11

The hero model is sound. What holds it back is what the game does to it at render time, how heavy it is, and that customisation is colour-only. The example below fixes the first and prototypes the third, with no mesh or texture changes.

Everything here ran in a throwaway copy of the project. Nothing in `Unity/` changed; the two code changes are saved as `tools/clone_changes.patch`.

## The example

![menu before/after](evidence/01_menu_before_after.jpg)
![close-ups](evidence/02_closeups_before_after.jpg)
![customise](evidence/03_customise.jpg)
![female and proportions](evidence/04_female_and_proportions.jpg)

Same hero, same backdrop, same camera, rendered by the game's menu with its post-processing on.

| Change | What it is | Status |
|---|---|---|
| Calmer menu grade | The menu keeps the plaza's golden-hour grade (contrast 22, saturation +26, temperature +6) on every venue backdrop. I set saturation 14, contrast 20, temperature +1. | Real code, 15 lines in `MenuBackdrop.cs` (clone) |
| Hero lighting on | The project already has a hero-only light model that caps coloured venue light and adds a fill and rim. It is off unless `VISUAL_HERO_LIGHTING=1`. I switched it on and halved its fill (0.95 → 0.5) so limbs keep their shading. | Real code, existing system plus one value |
| Head turns to the viewer | The idle looks over the viewer's head. I rotate the head toward the camera, clamped to 35°. | Prototype in the capture only |
| Cap follows the kit | `HeroAccessories.SetColours` exists and nothing calls it. One call recolours the cap. | Prototype wiring of an existing hook |
| Matte finish | Three cloth material values (smoothness, specular, reflection). | Prototype |
| Head 113 %, hands 107 % | Bone scale, for a slightly more stylised read. | Prototype, your call |

In the female pair the kit colours also differ between before and after; the skin change is the point of that pair.

Court check with hero lighting on (`review/court_ba.jpg`): on the volcano court the rival goes from solid orange to correctly lit and the player's whites turn white. It then reads a little bright for a dark venue and needs a per-venue tune.

## Audit

Effort: S is hours, M is about a day, L is several days.

### Looks

| Finding | Evidence | What I can do | Effort |
|---|---|---|---|
| Menu grade turns skin yellow and clips saturated shirts to a flat colour | Board 1 | Menu grade as in the example | S |
| Coloured venue light tints skin and whites; the fix exists but is switched off | `HeroLightingProfile.cs:21`, `review/court_ba.jpg` | Turn it on, tune per venue, check cost on a phone | S–M |
| The hero looks over the viewer; no eye look, no expressions | Board 2. Rig has blink shapes only; shader `_Gaze` is never set | Head and eye look-at, relaxed idle hands. Expressions need new face shapes | S for look-at, L for expressions |
| Bald under a forced cap | `HeroGolfer.cs:299`: "Hair is temporarily disabled" | A default hair asset exists per sex but is not fitted to the current head (my two attempts landed at the feet). Fitting one style is M; new styles are sculpting, my slow area | M–L |
| Male face is semi-realistic (small eyes, heavy brow); female is big-eyed cartoon. They do not match each other or the tier1 targets | `review/before_menu.jpg`, turnarounds | A face restyle is sculpting. A cheaper lever is the proportion scale in board 4 | L |
| The FN7 gloss reads inflated up close; a matte option reads more like cloth | Board 3 | Offer finish as a choice | S |
| Hands rest in a claw curl | Board 2 | Idle hand pose | S |

### Functions

| Finding | Evidence | What I can do | Effort |
|---|---|---|---|
| The male hero is 227,907 triangles at full detail; the female 205,999. The project's own budget is 35–50k | Capture dump: body 65.7k, shirt 41.8k, shorts 35.5k, each shoe 24.5k, cap 10.6k | Decimate offline to about 60k with no visible change at menu size. Runtime LODs already reduce this at distance, so the cost is in menus, intros and close-ups | M |
| 13 renderers and 24 material draws per hero | Capture dump | Merge sock and shoe pairs and face layers | M |
| About 40 runtime patches rebuild the mesh at load (weights, normals, hide lists, correctives, clearance solver) behind about 20 environment flags | Agent read of `Scripts/Tennis/` | Bake the stable ones into the assets once, leaving the game to load a finished mesh. Removes a class of bugs like the wrist snaps and shortens loads | L |
| 144 bones on the male at runtime (53 authored plus support bones); 81 on the female | Capture dump | Falls out of the bake above | — |
| Finger bones exist; no face bones | Prefab | Fine for a phone game | — |

### Customisable

| Slot today | State |
|---|---|
| Sex, skin (7 presets plus custom) | Works |
| Shirt, shorts or skirt, shoes, racket colour (12 swatches plus custom) | Works; trims are derived automatically |
| Cap | Forced on, fixed colours, cannot be removed |
| Glove, bag | Fixed colours |
| Garment styles | One mesh set per sport; the catalog has one item per slot |
| Hair, glasses, facial hair, headwear style | Profile fields exist and are ignored |
| Pattern, number, crest | Not supported |
| Finish | Hard-coded |

Against the Rocket League model (body, primary paint, accent paint, finish, decal, topper, wheels) the hero has primary paint and wheels.

## What I would build

1. **Look baseline (S–M).** Menu grade, hero lighting on with a per-venue tune, a brightness cap on cloth so saturated picks keep their shape. Verify on a phone.
2. **Paint zones (M).** Accent as its own pick, cap colour and cap on/off, finish (matte, satin, gloss), sock colour. These are all material values on existing meshes, plus locker rows and profile fields.
3. **Decals (M).** Stripes, halves, a chest number and a crest. The garment meshes already carry their rest-pose positions in a second UV set, so a pattern can be projected in the shader without touching the UVs. Not prototyped yet.
4. **Alive (S–M).** Head and eye look-at, idle hands, a reaction on a won point.
5. **Weight (M, then L).** Decimate first, then bake the runtime patches.
6. **Hair and face (M–L).** Fit the existing hair, then decide whether the male face gets restyled.

## Files
- `evidence/` — the four boards.
- `review/` — working sheets, including `court_ba.jpg`.
- `shots/` — every render, by job; `*_scene.txt` lists lights, volumes, materials and triangle counts.
- `tools/HeroLookCapture.cs` — the capture (copy into a clone's `Assets/Tests/PlayMode`); `tools/clone_changes.patch` — the two game-code changes.
- `jobs*.txt`, `run_stream.sh` — how each render was launched.

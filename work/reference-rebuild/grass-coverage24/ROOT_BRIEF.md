# Grass coverage24: bounded source candidate

GATE: source inventory PASS. All requested number slots 1–24 were checked. Current source defines 19 holes: 16 authored FBX holes and three procedural Meadow holes. Slots 4, 5, 6, 11 and 24 have no hole definition or FBX. `Course.All()` contains four course entries and excludes `Meadow()`; this is not a catalogue of 24 defined courses.

GATE: candidate compile PASS. Bundled Roslyn compiled 223 current runtime sources with the two work-only candidates substituted. The sole warning is the existing `TennisGame.audio` member warning. No Unity process or Assets edit was performed. Actual candidate render, collision and latency gates remain pending root's serialized captures.

| Hole | Current grass system | Candidate / blocker |
|---|---|---|
| 1, 2, 3 | Flat procedural Meadow ribbons/discs, managed ground textures | Separate analytic adapter required. No course ground MeshColliders; no `GolfCoastalTurf.Apply` call in `DressProcedural`. Do not add physics colliders to make the existing adapter work. |
| 4, 5, 6 | No source slot | No terrain to extend. |
| 7, 8, 9 | Accepted moving Dense15 turf | Preserved. |
| 10 | Managed flat coastal cut turf on Crater's rim | Candidate; existing coastal blade palette and height retained. Actual lava, basalt, stone path and sand excluded. |
| 11 | No source slot | No terrain to extend. |
| 12, 13, 14, 15 | Accepted moving Dense15 turf | Preserved. |
| 16 | Flat cut turf; native Ash/Basalt terrain | Candidate cut slots only; 0.75 blade height, existing volcanic palette. |
| 17 | Flat cleared cut turf; native Snow/Ice/Cliff | Candidate cut slots only; 0.65 blade height, existing cold palette. Ice lie and ice colliders excluded. |
| 18 | Flat tee and green apron; native Desert/Sandstone, no fairway mesh | Candidate tee and actual apron only; 0.55 blade height, existing dry palette. Do not invent a fairway or cover native desert. |
| 19, 20 | Newly promoted accepted moving Dense15 turf | Root-promoted list and water guard preserved. |
| 21, 22, 23 | Flat cut turf; native Ash/Basalt, lava sea | Candidate cut slots only; 0.75 blade height, existing volcanic palette. Lava and native ash remain bare. |
| 24 | No source slot | No terrain to extend. |

The source builder explicitly separates native terrain from cut grass. `course_extras.py` assigns Ash, Snow or Desert to island terrain, while `course_builder.py` authors `TEE_BOX`, `FAIRWAY`, `FAIRWAY_FIRSTCUT` and `GREEN_APRON_*` separately. Actual material audit records confirm these roles. The candidate admits an explicit `GREEN_APRON` name only on the seven omissions and only for authored role 1 (Fairway) or 4 (Fringe); the putting `GREEN` remains excluded. Existing nine-hole admission and grass heights are unchanged.

The accepted near tile's maximum blade height is 0.0848867 m. Candidate maxima are 0.063665 m for volcanic grass, 0.055176 m for cold grass and 0.046688 m for dry grass. These are bounded art choices awaiting actual ball/club readability review. Ground and blade colours reuse `GolfTurfPalette` exactly; no shader, texture, palette or FBX changes are staged. Role names are read from the actual collision material, so an analytic Rough lie on native snow, ash or desert cannot turn it into grass.

## Root integration and proof

Apply `GolfCoastalTurf.patch` and `GolfMovingTurfProofRunner.patch` to the current files. Full work-only candidate sources are supplied for inspection. Prefer the patches if another lane changes source after the snapshot. The candidate includes root's promoted 19/20 moving list, `_PatchCenter` / `_PatchFade`, exact windmill checks and full flight audits.

Set `VISUAL_GRASS_COVERAGE24=1`. For the moving trial set `VISUAL_MOVING_TURF=all` and point `GOLF_MOVING_TURF_CONFIG` to the absolute `proof-pilot-config.json`. For the static control retain the coverage flag, set `VISUAL_MOVING_TURF=0`, and use `proof-control-config.json`. Entry remains `GolfArcade.EditorTools.GolfMovingTurfProof.Run`. The flag creates turf only on 10, 16, 17, 18, 21, 22 and 23; it does not promote their default moving list.

The proof runner changes only candidate collider admission and adds actual rendered lava sheets to its water-height exclusion mask. It still drives real `DropBall` / `Aim` / `StrikeToward`, production `LateUpdate`, and one normal camera capture per actual frame. No manual refresh, draw or camera render was added. Strict positive resident/submitted cells, exact retained matrices, positive retired-cell regeneration, same-station query counts, stable materials, no-flight rebuilds and full physics audits remain required.

Hole 18's requested centreline midpoint lies over the canyon. Selection must report its actual supported apron/collar point accurately and retain 2 m clearance and 30 m separation. If the authored apron cannot supply two separate valid stations, record that exact source constraint; do not lower the positive regeneration gate or scatter grass on Desert to force a pass.

Review actual grass/native edges on 16/17/18/21–23, the lava and decorative path edge on 10, and putting boundaries on all seven. Existing reviewed screenshots show flat grass at their tees, plus native bare ground that must stay distinct; they are baseline evidence, not candidate acceptance. The current pool remains bounded at 48 near / 96 mid / 640 total cells, at most 542720 added triangles and three instanced submissions, with no grass shadows or colliders. Rebuilds remain deterministic, use a 4 m settled-address station, and never follow flight. Material clones are allocated once per eligible source role at build and destroyed by their owner; movement creates no materials. Measure actual desktop rebuild latency and do not infer phone FPS.

`inventory.json` records all 24 slots and historical actual physics/material evidence. `candidate-manifest.json` records hashes, bounds and integration settings. The separate Meadow lane must use the original rendered ribbon/disc heights and `Hole.LieAt`/analytic region roles without changing flat gameplay physics, then receive its own actual proof.

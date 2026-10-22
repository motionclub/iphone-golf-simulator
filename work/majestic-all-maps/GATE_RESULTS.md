# GATE_RESULTS — Majestic on every golf map (chat 10), final 2026-10-18

Scope: 16 golf holes, three courses (Cliffside 7 8 9 12 15, Wild Isles 13 14 17 18 19 20, Magma 10 16 21 22 23). Weather is chat W (`work/majestic-weather/GATE_RESULTS.md`); this file covers maps.
State: built and verified in `~/majestic-all-maps-UnityClone`; **not installed** in Unity/ (install script below); nothing staged or committed.
Final sheets: `g2/final37_{cliffside,wildisles,magma}.jpg` (game above target, 16 holes x 5 reference views).

## Gates (PLAN.md definitions)
| gate | result | measured | reason |
|---|---|---|---|
| G0_MEDIAN_VIEW (median static view <= 0.8 M tris) | **PASS** | 0.791 M (r37, 316 views; r1 0.62 M) | scatter thinning 35-100 yd, far tree cells (130 yd, palms 195 yd), shadow proxies, shore tiles LOD1 |
| G0_ALL_VIEWS (every static view <= 1.0 M) | **FAIL** | 115 / 316 over (r1: 101) | fixed costs in every tee/close view: characters ~0.6 M, turf blades ~0.48 M, shadows ~0.4 M (not this layer's) |
| PERF_WORST_VIEW (worst camera per hole: <= 1.0 M tris, <= 250 draws; Editor >= 58 fps; device GPU <= 11 ms) | **FAIL** (tris/draws); fps + device **NOT RUN** | worst = tee on every hole: 1.89-3.97 M, 273-518 draws (today 1.45-3.80 M); table `g0/budget_final_r37/WORST_PER_HOLE.md` | fixed costs above + this layer's tee beds (+0.2-0.8 M at the tee); h12's 3.97 M is the course's own coastal instancer (1.66 M). Device/fps runs belong to integration testing |
| REF_MATCH (in-game vs ref, Adnan signs) | **PENDING Adnan** | objective histogram match 2-5 / 40 (FAIL); structural checklist **444 / 640** (`g2/SCORE_r32.md`) | landmarks, skylines, sky hour, sea, Magma caldera/volcano/lava ground, layered beds are in; open: Wild Isles hero assets (gnarled trees 14, snow pines + peaks 17, mesa walls 18), golden upper sky on Wild Isles (chat 2's RenderedSky), near-corner density |
| NO_EMPTY_VIEW (every sampled camera: no flat area > 25 % width) | **FAIL** (improved) | 185 / 444 sampled cameras fail (42 %); today 203 / 332 (61 %); `g1/final_all_r38/no_empty_view.jsonl` | remaining fails are mostly 360 pans (56), late flyover shots (36) and green-back views (15, the putting green itself is the flat area by design); 23 are live-drive frames |
| NO_VOID (magenta clear, 0 void pixels) | **NOT RUN** | — | the magenta-clear render was never built; no void or sea-plane edge seen in any captured frame (h21-23 lava-disc rim hidden by the caldera ring) |
| POP_IN (flyover at 60 fps, nothing appears/vanishes) | **PASS (accepted by Adnan 10-18)** | far tree cell swaps: 98 in view on 7/13/17/19, median 1/255, 3 at 20-23/255 (`g1/pop_r36/POP_RESULTS.md`) | per-swap log from replicated LOD selection; camera cuts excluded. Scatter thinning drops single small plants past 35 yd (each well under the 0.2 %-of-frame blob limit) |
| READABILITY (ball/flag contrast >= 3:1 ...) | **NOT RUN here** for clear weather; weather views: chat W | — | the layer keeps everything out of play lies (lie filter; tee-side beds only within 12 yd of the tee or 9+ yd off the line within 22 yd) |
| WEATHER_COST | chat W | — | |

## Decisions recorded
- Holes 7 and 15: the pine walls stay as they are (Adnan, 10-18). Not a gate item any more.
- Far tree swaps accepted as they are (Adnan, 10-18).
- One signature hour per course; holes 10 and 16 get ash weather; tennis weather goes round play (Adnan, PLAN go-ahead).

## Install (`tools/install_majestic.sh {dry-run|install|rollback} [Unity dir] [--tools]`)
Verified on a scratch project: install adds 76 files and patches/replaces 5; rollback restores the 5 originals byte-for-byte and removes the 76. The patches apply cleanly to today's Unity/ sources and produce exactly the files the clone compiled and ran.
- **Added (76):** `Assets/Scripts/Majestic/` MajesticBudget, MajesticCoastKit, MajesticCourseKit, MajesticCourses, MajesticHoleKit, MajesticKit, MajesticLavaGround, MajesticScatter, MajesticShore (.cs); `Assets/Resources/Majestic/` MajesticFX, MajesticFoam, MajesticImpostor, MajesticLavaGround, MajesticShadowOnly (.shader); `Assets/Resources/Majestic/Kit/` 61 files (34 landmark FBX + impostor PNG from `work/majestic-landmarks`); `Assets/Editor/MajesticKitImport.cs` (Read/Write on 5 recoloured kit FBX). `--tools` adds the proof tooling (MajesticHoleViews, MajesticGolfBudget, MajesticKitShots).
- **Patched (backed up to `install_backup/`):** `Scripts/Majestic/MajesticLook.cs` + `MajesticVenue.cs` (`tools/patch_majestic_hooks.py`: golf look -> MajesticCourses.For, golf Kit -> MajesticCourseKit), `Scripts/Course/GolfCoastalInstances.cs` (`tools/patch_g0_instancers.py`: tree shadow proxies).
- **Replaced:** `Resources/Course/Resort/BotanicalKit.fbx`, `CoastalBotany.fbx` (lite versions, same object names, ~50 % triangles; `g0/blender/lite/`).
- **Kill switches:** `MAJESTIC=0` (whole layer, chat 9), `MAJESTIC_BUDGET=0` (make-room proxies + far tree cells).
- **With weather (chat W):** no shared file overlaps (chat W patches shaders, EnvironmentSurface.hlsl, RoundEvents.cs). Order-independent.

## Combined test: maps + weather in one project (`tools/combined_test.sh`, 10-18 15:30)
Chat W's dormant files + harness copied into the maps clone, its shared patch applied (`patch_shared.py check` OK), maps layer on. Compiles and runs with no errors or exceptions.
| slot | hole | ball contrast (>= 3:1) | today | corridor | fog on ball |
|---|---|---|---|---|---|
| W09 ashfall | 22 | **3.22 PASS** | 1.35 | PASS (0 drops) | PASS (0.0) |
| X16 rain -> ash | 16 | **3.44 PASS** | 1.17 | PASS (0 drops) | PASS (0.0) |
Frames: `g3/combined_sheet.jpg` (clear / legacy / majestic). The maps' AshOvercast and chat W's ash stack without hurting readability. Under ash the caldera walls take the ash cover and read tan-grey; that is a look call for REF_MATCH, not a gate. Clear-weather maps views with the weather patch applied (`g3/combined_clear/`): the look is unchanged; h16 mean frame difference 0.8/255 vs the final run, h22 differs only by the game's tee-camera framing and lava/plume animation phase.

## Game issues seen (for their owners, not maps gates)
h18 flyover camera starts inside the mesa; large floating gameplay labels (h19 "Temple aperture", h20 "Petal cut"); h16 off-line view filled by a black hazard block.

## 10-18 evening: shore-tile bug found in the share-video review
The share video's moving cameras (ball-follow on hole 8, flyover) showed the coast kit tiles as flat pale walls in front of the course's own cliffs and white shards at the cliff foot (`work/share-videos-1018/golf_take1.mp4`, frames ~5 s and ~17 s; gone with the tiles off: `golf_take3_h08.mp4`). The 5 reference views per hole never framed them, so the gates missed it. Fix: `MajesticCoastKit` builds no shore tiles unless `MAJESTIC_COAST=1` (the lie-placed set pieces, hut on 17 and bridges on 20, stay); the MajesticShore shallows + foam band is unchanged. Integration needs the updated `Scripts/Majestic/MajesticCoastKit.cs`.

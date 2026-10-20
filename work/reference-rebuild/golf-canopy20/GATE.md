# Temple19 canopy candidate20

GATE: SOURCE CANDIDATE READY FOR UNITY PILOT.
GATE: ACTUAL GAME APPEARANCE / PERFORMANCE PENDING.

The single candidate replaces the palm prototype with fuller coconut arches derived from the existing TennisCoconutPalm authoring code. Source geometry contains curved folded leaf surfaces and a closed trunk. Thin leaves intentionally have open rims and rely on the existing GolfBotanical two-sided shading. No alpha foliage texture is required. An early overly simplified leaflet draft was rejected in `rejected-coarse-subdivision` before integration.

Final source counts:
- Near:11,396 triangles,10,398 vertices; old golf near12,380tri (−7.9%).
- Far:2,316 triangles,2,444 vertices; old golf far4,104tri (−43.6%).
- Temple19:46 tree markers among90 plant markers. Names, world matrices, heights and radii are recorded verbatim in `temple-marker-identity.json`; no new tree roots, collider edits or placements.
- All46 near envelope524,216tri; all46 far106,536tri. Example8 near +38 far179,176tri. These are geometry counts, not measured GPU submissions or phone performance.

`canopy-source-comparison.jpg` shows matched Blender renders at original median temple proportions (height18.3m, crown-radius scale10.04m), using the same palette, lighting and camera. It demonstrates the prototype shape change, not the final Unity scene. Actual daylight/shadow/LOD on the course still requires root review.

Integration package:
- `GolfTempleCanopy20.fbx` and editable `.blend`.
- `canopy-runtime.patch` is a work-only suggested diff against GolfResortDress.cs. It loads `Course/Resort/GolfTempleCanopy20` only on hole19 with `VISUAL_GOLF_CANOPY=1`. Existing source marker order, RNG, transforms and obstacle extraction remain unchanged.
- Preserve imported authored normals when changing crown proportions: the patch inverse-transpose transforms normals and avoids merging distinct leaf rims. This prevents former hard-edge smoothing artifacts.
- Import readable meshes, material names intact, global scale1 with file scale as existing BotanicalKit. Resource roles are exact `PALM` / `PALM_FAR`; no replacement shared golf kit is needed.

Root's next capture: ordinary gameplay, preview, approach and one closer foliage view on19. Require46 original tree placements, unchanged obstacleCount171/hash9ba786d215253716d82aacf300ac6f6efe27cec0ed0164851997994ea99a7d52 and14 colliders, exact saved ground contract, retained grass palette, and actual rendered costs. Review near/far canopy changes for visible popping before default promotion. No broad catalog rollout is implied.

All work remains in this work directory; this agent made no Unity Assets edits or Unity runs.

# Character LOD (2026-10-17, character-lod chat)

Goal: hold 60 fps at ≥ 1920×1080 without changing how the heroes look up close.
Measured by chat 10 (`work/majestic-all-maps/g0/budget_before`): in every golf tee view the skinned characters cost a fixed
~0.61 M triangles / 67 draws, and 211 of 443 golf views exceed the 1.0 M per-view cap (`work/frame-rate-60b/BUDGET.md`).

## What the 0.61 M is
- The "characters" figure in `MajesticGolfBudget` switches off **skinned** renderers only, so it is the golfer alone. The golf
  gallery fans are rigid `MeshRenderer`s with their own LODGroup (`GolfGalleryPresentation`, ≤ 8 k far triangles).
- One golfer is ~200 k triangles of meshes: garments 132,826 (golf male: Top 39,144, two shoes 27,664 + 27,658, Bottom 15,200,
  gloves 8,040 + 8,020, belt 7,100; `tools/unity_mesh.py`), body ~49 k, plus face, club(s) and accessories. Each mesh is drawn
  in the main pass(es) and in every shadow cascade that contains it, which multiplies it to ~0.6 M per frame.
- Tennis stands, the Majestic crowd and the golf gallery are already rigid + instanced or LOD-grouped: not the problem.

## Approach (why not Blender)
The hero meshes that render are produced **at runtime**: cover masks hide body triangles under garments, `FinishFootwear`,
`HeroGolfSkirtFit`, `HeroSkinNormals` / `HeroBlinkNormalField` / hand and shoulder weight passes, the rigid face's eye rims and lid
geometry, garment corrective blendshapes. A Blender-made LOD of the source FBX would not match any of that, and it would need
re-exporting every time chat 5 / male-garments reinstall garments (they are mid-redesign today).

So the LODs are made from the **final runtime meshes**, index-only:
- `HeroLodSimplifier` (pure C#): half-edge collapse with quadric error (area-weighted face planes plus constraint planes on borders
  and UV/normal/submesh seams), meshoptimizer-style vertex kinds, link-condition and flip tests, and a penalty on skin weights (skin
  centroid), normals and blendshape deltas. Every LOD triangle references an original vertex, so skin weights, bind poses,
  blendshapes, normals and UVs are exactly LOD0's ("same skin weights" by construction).
- `HeroLod` (self-attaching through `HeroLodBoot`, no prefab/scene/shared-script edits): once a hero's meshes have settled it
  makes compacted LOD1–LOD4 copies of each drawn renderer's mesh (≥ 4,000 triangles), keeping only used vertices, byte for byte.
  **The original renderers are never modified** (sharedMesh, bones, materials, enabled stay what their owners set). At LOD0 they
  draw as before: close-ups and the locker are untouched. At LOD>0 an original gets `forceRenderingOff` (and stops skinning)
  and a child proxy renderer `HeroLod <name>` draws the copy, with bones, materials, shadow/layer/probe settings, property block
  and blendshape weights synced every frame. An earlier design swapped `sharedMesh`. It was dropped because
  `HeroAccessories.ApplyCover` (golf bag between shots) would have derived the body cover from a LOD copy.
- Cache: `Resources/CharacterLOD/HeroLodCache.bytes` (uint16 lists), keyed by a hash of the final runtime mesh. A miss computes
  on a worker thread and the hero stays at LOD0 until then: a stale cache costs time, never looks.

Levels (screen height of a 1.75 m hero / view height, relative hysteresis ±7 %):

| level | from | triangles | max error | golfer (male) |
|---|---|---|---|---|
| LOD0 | ≥ 0.60 (close-ups) | original | 0 | 198,356 |
| LOD1 | 0.46–0.60 | 50 % | 2.0 mm | 95,813 |
| LOD2 | 0.16–0.46 (golf tee ≈ 0.39, near tennis player ≈ 0.42) | 30 % | 3.5 mm | 57,483 |
| LOD3 | 0.04–0.16 (far tennis player ≈ 0.07) | 12 % | 8 mm | 22,987 |
| LOD4 | < 0.04 | 10 % | 12 mm | 19,156 |

Env: `CHARACTER_LOD=0` off, `CHARACTER_LOD_FORCE=0..4`. Results: `GATE_RESULTS.md`.

## Garment chats (coordination)
Messages sent 2026-10-17 ~19:50 to garment-pipeline (chat 5) and male-garments-refpack. Nothing in their pipeline changes; after
their final installs the cache is re-baked with `tools/run_probe.sh` (step `bake`), or the runtime computes it.

## Files
- `src/HeroLodSimplifier.cs`, `src/HeroLod.cs` → `Unity/Assets/Scripts/CharacterLod/` (new folder, owned here); `install/install.sh install|remove`, `install/HeroLodCache.bytes`
- `unity/Assets/Editor/CharacterLodProbe.cs` (golf: measure / identity / pop / film / perf / gpu / bake; `CharacterLodTennisProbe`), `tools/run_probe.sh`, `tools/run_tests.sh`, `unity/Assets/Tests/EditMode/CharacterLodTests.cs`
- `tools/gate_views.py` (tee gate table), `tools/film_pop.py` (pop check on the film), `tools/recode_cache.py` (uint16 cache)
- `tools/unity_mesh.py` (YAML mesh reader), `test/LodHarness.cs` + `tools/preview.py` (offline simplifier test + preview)
- `tools/compile_check.sh` (type-check against Unity DLLs + the project's compiled GolfArcade.dll, no Editor)

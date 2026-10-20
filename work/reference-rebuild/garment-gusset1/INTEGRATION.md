# Underarm gusset integration candidate

Opt-in review candidate, not a whole-character art pass. Preserve Body mask2 and the original tennis outfit. No Assets were changed by this authoring task.

## Install and final-pose hook

1. Copy `HeroGarmentGusset.cs` to the Tennis scripts directory.
2. Copy `UnderarmGusset_Female_Full.json` and `lod/UnderarmGusset_Female_LOD.json` into `Resources/Tennis/Correctives/`, preserving those filenames.
3. In `HeroGarmentPoseCorrectives.Apply`, call `HeroGarmentGusset.Apply(look.female, look.transform, top);` **after** the loop setting `TailoredSleeve_` blendshape weights. The existing final-pose hook already runs after IK. Do not add another Update/LateUpdate component.
4. For capture, set `VISUAL_UNDERARM_GUSSET=1`, `VISUAL_UNDERARM_FIT=0`, and retain normal Back culling and coverage mask2. Both candidate and prior single-pose UnderarmTrace must not run together.

The helper installs a private mesh for each renderer on first use and preserves all original shape frames, UV channels, tangents, colors, source vertex positions, and source bone bindings. New vertices use barycentric attributes and anatomical source bindings. Physical UV edge copies receive identical subdivisions and identical weights. The outer patch boundary is pinned. A source basis or topology mismatch throws an explicit capture error; the helper never substitutes full detail for an unsupported LOD or quietly falls back to the old torn surface. Full/LOD source counts are 13,932 and 11,533 respectively.

The source shapes continue to interpolate as before. The solver calculates the current posed garment, resolves the local contact field, then writes only its inverse-LBS delta into the unshaped mesh input. GPU skinning and original blendshapes remain active. There is no time integration or previous-frame state, so manual sampling and capture are deterministic. Vertex normals receive the geometric normal difference through the same inverse linear transform.

## Bounded collision contract

The exact proxy contains 104 canonical Body vertices and 135 unmasked underarm triangles. Each point stores four original weights plus a bone-local bind point for each influence. This avoids Body mesh baking, Body blendshape reads, renderer-space assumptions, or a full Body search. The proxy follows the existing bones directly. The BVH has fixed topology, spatially ordered once at installation, and only updates its node bounds each pose. No per-frame allocations or sorting are required by the solver. Unity mesh buffer upload and platform performance still require measurement.

At each final pose:

- Interpolate the original active sleeve shape deltas onto the gusset mesh and evaluate LBS.
- Compute geometric garment normals; query the nearest absolute outward Body exit along each free vertex normal, in the range −12 to +50 mm. Move outward by exit distance +3 mm, capped at 40 mm total.
- Synchronize every physical UV alias and pin the outer boundary.
- Perform six triangle-centroid contact passes. Each positive contact contributes up to 8 mm along the triangle normal, scaled by 3 / movable corner count. Average positive incident pushes at each vertex; clamp total displacement to 40 mm and synchronize aliases after each pass.
- Write the inverse-LBS position and normal corrections to the renderer-owned mesh.

`check_patch_contact.py`, `clearance.c`, and the serialized profile reproduce this contract. A small proxy avoids a full-body collision system; this remains a runtime deformation candidate, not an exported static FBX claim. A later native pipeline must preserve the same subdivided topology, bindings, source shapes, and local contact behavior or prove equivalent poses.

## Validation and capture

The standalone C# compilation uses the installed Unity 6000.3.24f1 CoreModule and JSONSerializeModule assemblies (`compile.rsp`); it passes. This does not substitute for Unity execution.

Run `capture-targeted.json` first. It includes Forehand, EmoteSpike, Serve, CelebratePoint, IntroPushups, IntroWave, MatchLose, VolleyBackhand, and EmoteScuba in full and LOD, with five samples and both views. It covers the original target and all source-raster flagged cases. After that visual gate, `capture-motion-after-targeted.json` provides dense 25-sample all-clip full/LOD review. These configs use the parent task's existing character capture entry point and intentionally leave renderer/Assets integration to the root task.

For numerical parity, the `female_Forehand_1-oracle.json` and `female_EmoteSpike_1-oracle.json` files in each detail folder contain exact source posed and uncorrected positions in hero-root metres, plus the posed proxy. Pose times/bone matrices are the canonical `character-motion-matrices17` snapshots. The candidate's geometry is shader-independent; minor float and antialiasing differences should be adjudicated from actual pixels. A substantial matrix/mesh mismatch must be corrected before visual acceptance.

Physical-phone profiling and whole-character visual approval remain deferred. The source all-pose reports and explicit flagged views are in `SOURCE_GATE.md` and `source-motion-contact-report.json` for each detail variant.

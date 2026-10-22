# Golf look — P0 audit (2026-10-05)

GATE: PRECONDITIONS WAITING. HEAD is `2225264c`; no later course-only P8 commit exists in the inspected local history. `work/postcard-look/RESUME.md` still describes an unfinished/paused foundation. Current v3 evidence is newer than that resume, so the resume is stale, not a completion certificate. `work/cloth-overhaul/` exists and is active in Codex, but has no REPORT, gates report, or final `ArtDir/hero/kit/GARMENT_SPEC.md` at this audit.

## Corrections to the supplied inventory

- MatchHeroKit is an **Editor builder** at `Unity/Assets/Editor/MatchHeroKit.cs`, not a runtime class in Scripts/Tennis. MatchHeroLook clones/recolours its six bound kit renderers at runtime.
- GolfLook creates LK surfaces on URP Lit, with dedicated GolfPlants, GolfSurf and GolfLava plus reused TennisWater/TennisSky. Albedo alpha is smoothness for fairway and green only; fallback smoothness .10/.12. Other bands retain their own constants. Runtime materials, not authored .mat appearance, are authoritative.
- Hole 7 uses the legacy palette path; GolfLook.IsPostcard covers only 8–10. G3 for hole 7 needs a deliberate mapping when integration is unlocked.
- GolferView still loads StandardCharacters and StandardGolfDrive with top/impact/end at 1.77/2.40/3.00 s. Commit 2225264c did not install the match skeleton on the tee. Gameplay swing replacement remains out of scope.
- GolfFigureExposure multiplies `_BaseColor` in MaterialPropertyBlocks; holes 8/9 use white, hole 10 (.76,.90,1.20). Values in comments (Needle 2%, Split 3.5%, Crater 17.9% clipping; adjusted Crater ~1.5%) are **historical V4 measurements**, not this task's new evidence.
- The isolated dressed source female includes optional Hair_F. It must remain unchanged; use a visor above its perimeter or prove cap clearance. Never modify hair/scalp to fit headwear.
- Source rig: 53 bones; no new bones needed. Headwear can use rigid Head weighting, avoiding a new socket.
- Seven postcard guards pass (`logs/guards_before.txt`). Hole.cs is dirty relative to Git but matches the upstream guard hash and design data. This is not a frozen-geometry failure.
- LOOK_CONTRACT has qualitative stripe requirements and a historical ~250k source-triangle budget, but no numeric luma-contrast interval or 250-draw-call number. This prompt specifies 300k/250 for G11; report both budgets and resolve the contrast interval against the owner before certifying G3.

## Current light values (sRGB authored)

| Hole | Key / strength | Elevation / azimuth | Sky ambient | Equator | Ground ambient | Figure MPB |
|---|---|---|---|---|---|---|
| 7 legacy | (1,1,1), 1.1 | Rotation Euler (50,-30,0) | Flat ambient (.55,.60,.65) | Same | Same | (1,1,1) |
| 8 Needle | (1,.86,.66), 2.3 | 30° / -50° | (.42,.58,.86) | (.68,.60,.52) | (.20,.30,.34) | (1,1,1) |
| 9 Split | (1,.95,.86), 2.3 | 42° / -75° | (.42,.58,.86) | (.62,.64,.60) | (.20,.28,.26) | (1,1,1) |
| 10 Crater | (1,.80,.58), 2.3 | 32° / 40° | (.34,.24,.40), plus folded fill | (.33,.36,.31) | (.48,.34,.18) | (.76,.90,1.20) |

Azimuths are relative to tee-to-pin heading. Holes 8/9 fills are .8; rims .5/.3. Crater fill .55 is folded into ambient and has no directional rim. No tone mapper or post: highlight shoulder must be inside the shared shader core when G0 unlocks.

## Source material and texture evidence

Full per-hole mesh/material inventory: `data/course_mesh_audit.json` (source objects, source triangle counts, material-slot upper bounds). These are **not measured GPU draw calls or visible triangles**. Source stability is checked around each read. Full runtime specs: `data/course_material_table.txt`. Texture sizes/formats: `data/course_texture_inventory.json`.

| Texture | Pixels | Channels | PNG bytes |
|---|---|---|---|
| Basalt_C.png | 1024×1024 | RGB | 739570 |
| Basalt_E.png | 1024×1024 | RGB | 308000 |
| Basalt_N.png | 1024×1024 | RGB | 785834 |
| CliffDark_C.png | 512×512 | RGB | 213318 |
| CliffDark_N.png | 512×512 | RGB | 194678 |
| Cliff_C.png | 1024×1024 | RGB | 658657 |
| Cliff_N.png | 1024×1024 | RGB | 610693 |
| Fairway_C.png | 1024×1024 | RGBA | 2002658 |
| Fairway_N.png | 1024×1024 | RGB | 2086989 |
| Fall_C.png | 256×512 | RGBA | 100514 |
| Green_C.png | 1024×1024 | RGBA | 2056786 |
| Green_N.png | 1024×1024 | RGB | 2117796 |
| Lava_C.png | 1024×1024 | RGB | 925328 |
| Lava_E.png | 1024×1024 | RGB | 1182768 |
| Lava_N.png | 1024×1024 | RGB | 507533 |
| Masonry_C.png | 512×512 | RGB | 229561 |
| Masonry_N.png | 512×512 | RGB | 270585 |
| Path_C.png | 512×512 | RGB | 305848 |
| Path_N.png | 512×512 | RGB | 351117 |
| Plants_C.png | 256×256 | RGB | 71283 |
| Rock_C.png | 512×512 | RGB | 250791 |
| Rock_N.png | 512×512 | RGB | 307663 |
| Rough_C.png | 1024×1024 | RGB | 1277911 |
| Rough_N.png | 1024×1024 | RGB | 1995667 |
| Sand_C.png | 512×512 | RGB | 238925 |
| Sand_N.png | 512×512 | RGB | 344761 |
| Scrub_C.png | 1024×1024 | RGB | 1802219 |
| Scrub_N.png | 1024×1024 | RGB | 2093369 |
| Sky_Crater_C.png | 2048×880 | RGB | 660659 |
| Smoke_C.png | 512×512 | RGBA | 113012 |
| Surf_C.png | 512×512 | RGBA | 366822 |

## Shader names and variants

The exact pragma/include lists are in `data/shader_inventory.json`. No shaders have been edited or added to Unity at this stage; no variant count is claimed from a pragma count. Metal compile statistics require the later serialized Unity run.

- `Hidden/GolfArcade/KitRecolor` — `Unity/Assets/Resources/Tennis/Shaders/KitRecolor.shader`
- `GolfArcade/TennisCharacter` — `Unity/Assets/Resources/Tennis/Shaders/TennisCharacter.shader`
- `GolfArcade/TennisCloth` — `Unity/Assets/Resources/Tennis/Shaders/TennisCloth.shader`
- `GolfArcade/TennisFace` — `Unity/Assets/Resources/Tennis/Shaders/TennisFace.shader`
- `GolfArcade/TennisFxAdditive` — `Unity/Assets/Resources/Tennis/Shaders/TennisFxAdditive.shader`
- `GolfArcade/TennisFxAlpha` — `Unity/Assets/Resources/Tennis/Shaders/TennisFxAlpha.shader`
- `GolfArcade/TennisShadowBlob` — `Unity/Assets/Resources/Tennis/Shaders/TennisShadowBlob.shader`
- `GolfArcade/TennisSky` — `Unity/Assets/Resources/Tennis/Shaders/TennisSky.shader`
- `GolfArcade/TennisWater` — `Unity/Assets/Resources/Tennis/Shaders/TennisWater.shader`
- `GolfArcade/GolfLava` — `Unity/Assets/Resources/Course/Shaders/GolfLava.shader`
- `GolfArcade/GolfPlants` — `Unity/Assets/Resources/Course/Shaders/GolfPlants.shader`
- `GolfArcade/GolfSurf` — `Unity/Assets/Resources/Course/Shaders/GolfSurf.shader`

## Pending measured evidence

P0 Unity captures, per-hole skin clipping %, white/black L*, actual GPU draw calls, visible tris, variants after stripping, shader ALU/fetches, frame time, 3-second temporal videos, shadow directions, and tennis match/locker comparison are UNMEASURED. The work-folder proof rig is a draft pending isolated Unity compilation; it is not installed and no screenshot is fabricated. Current active ownership prevents replacing or importing the dependency assets into the shared project.

`data/baseline_files.json` records 244 protected input hashes/mtimes. `inputs/SOURCE_MANIFEST.json` freezes both dressed input blends. Read-only audit and Blender outputs do not substitute for Unity proofs.

## Dependency recheck after preparation

15's `work/postcard-look/v3/PHASE_STATUS.md` explicitly says P8 NOT RUN (P2 in progress); no course-only commit. The newer `v3/THRESHOLDS.md` supplies fairway relative luma-gap upper bound .12, green .08, >=512 valid pixels per plateau, tee draw calls <=250 and hole triangles <=300,000 while retaining the existing 250,000 source cap. Those supplement the older LOOK_CONTRACT; use the delivered final version for G3.

29 has since written `ArtDir/hero/kit/GARMENT_SPEC.md` during active work, copied read-only to `inputs/GARMENT_SPEC_in_progress.md`. There is still no completion report or released finished state. The draft uses N +Y, M.R AO / G cavity / B trim / A ID÷5, six IDs (bytes 0,51,102,153,204,255), and 2048² top maps. New golf IDs cannot silently change the tennis decoder or its old A bytes. The golf texture plan's UV density and shared atlas allocation still need measurement and reconciliation. G0 remains WAITING.

Concurrent changes since snapshot: TennisCloth.shader, MatchHeroLook.cs and CharacterModelPreview.swift. This task did not edit these files. Fresh pre-change tennis baselines must be captured after 29 releases them.


## Second goal-turn isolated stress checkpoint

G0 remains WAITING: HEAD 2225264c, postcard P3 in progress / P8 not run; cloth owner active with no final completion report. Exact observation is in data/dependency_swing_checkpoint.json. No Unity or xcodebuild process was launched by this task. Seven scoring/source guards pass in logs/guards_swing_checkpoint.txt.

Both frozen match rigs now have proof-only V4 top/impact/finish retargets plus mirrored left-hand poses and mirrored ReadyIdle. The two SwingProof blends and 16 full-body pose frames are isolated under work/golf-look/. V4 has no finger bones; ReadyIdle-derived fingers cannot certify grip. No gameplay animation was replaced.

A read-only independent input-vs-output check (scripts/verify_identity.py, data/identity_swing_checkpoint.json, logs/identity_swing_checkpoint.log) confirms exact body/face geometry and weights, female hair geometry, and all 53 rest bones with unchanged names/parents/matrices in both draft and proof copies. Draft kit triangles are now 70,891 male and 50,546 female, within the OLD pre-29 allowances only. Recalculate after 29 delivers its kit.

Garment repair: source tops are already closed (source_shell_topology.json); duplicate solidification was removed and inner/outer walls eased together. Existing garment weights are preserved; gloves/trousers retain body-vertex lineage; shoe saddle trim is cut overlay geometry. The erroneous arm-to-skirt tethers are removed.

G7 FAIL: new measurements cover 5,851 male and 2,282 female polo bind samples instead of only 41/63 from the doubled shell. Candidate maxima reach 30.316 mm male / 30.018 mm female across sampled pieces, exceeding 3 mm. Counts and lost correspondences are reported per garment; samples never certify complete collision. Rigid headwear drift is below 0.000285 mm, verifying attachment only. Contrasting-body renders confirm hip/underarm poke-through. Belt fit, skort coverage, wrist edges and trouser crease need further modelling. Posed hair clearance remains unverified. Nothing here qualifies as a Unity skin/exposure or phone-performance proof.

## Third goal-turn isolated construction checkpoint

G0 WAITING, observed HEAD 23cbedab (online lobby), course P4 FAIL / P8 NOT RUN and cloth owner still active (live revision 7). Full observation is data/dependency_construction3_checkpoint.json. The prompt's section 0 requires stopping after allowed isolated preparation. No dependency-owned integration file was edited; no Unity or xcodebuild process was launched by this task.

Added actual male pocket openings, inset bags and lips, replaced floating crease tubes with vertex ridges, introduced separate female inner shorts and 16 geometric skirt pleats, and plane-cut the glove wrists. Polo/button/placket weights now transfer barycentrically from relevant body triangles with four influences. The skort support field now uses existing body skinning weights, with inverse bind-position recovery error 0.000331 mm; this repairs the earlier oversized silhouette, without certifying swing clearance. Current draft triangles: 74,231 male / 43,108 female, against pre-29 budgets only.

Both-handed proof blends and all 16 full-body pose images were refreshed. Independent exact body/face/hair/weights/rest-rig verification passes in logs/identity_construction3_checkpoint.log. Seven guards pass in logs/guards_construction3_checkpoint.txt. G6/G7 remain FAIL: own-eye contrasting-body review shows residual hip/underarm penetration, flaring male pocket lips and broken female hip pleats in the swing. Belt, collar, vents, cuffs, perforations, soles and grip still require completion/proof.

Read-only diagnostics now exclude irrelevant nearby anatomy by dominant bind bone and garment region: 131 hand/arm samples were excluded from the skort, avoiding a misleading distant-hand warning. Full per-piece counts, home-plane warnings, nearest bind-classified outer-face warnings and lost correspondences remain in data/deform_draft_<Sex>.json. Worst home-plane warnings are 34.942 mm male polo and 44.429 mm female skort; nearest outer-face warnings still exceed 3 mm. They are sampled diagnostics, not certified penetration maxima. The source body and garments all use linear armature skinning; hip-selection diagnostics reject none of 2,070 candidate male hip vertices.

New models/maps remain isolated, staged preparation only. Other chats have staged files; this task preserves their index entries and stages its explicit paths. G1–G12 are not passed by these drafts.

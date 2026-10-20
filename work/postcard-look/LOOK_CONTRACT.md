# POSTCARD_LOOK — contract between the parallel workstreams

Authority: `ArtDir/environments/14_POSTCARD_LOOK.txt` (the user's brief, GATE lines authoritative; the stills
`ArtDir/environments/refs/{needle,split,crater}.jpg` are the LOOK target). This file only fixes INTERFACES so that
texture, Unity-runtime, Blender-lib, props-lib and per-hole agents can work in parallel. Read-only for everybody
except the lead. If you need a change, write it in your own notes file and say so in your final report.

Repo root: `/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator` (all paths below are relative to it).
Job folder: `work/postcard-look/` (baseline backups in `baseline/`, `heavy.sh`, `guards.sh`, per-agent notes).

## 0. Ground rules (every agent)

* No `git add / commit / stash / checkout / reset / clean`. The tree is dirty with OTHER chats' work (tennis, heroes, menus):
  never revert or reformat a file you do not own, never run repo-wide formatters.
* Do not touch: `blender/hole_07.blend`, `Unity/Assets/Resources/Course/hole_07.fbx(.meta)`, `blender/scripts/hole07_*.py`, `phase*.py`,
  `Unity/Assets/Scripts/Course/Hole.cs` (scoring: LieAt, shores, centerlines, pins, hazards, par), anything under `Unity/Assets/Scripts/Tennis/`,
  `Unity/Assets/Resources/Tennis/` (incl. `TennisWater.shader`, `TennisSky.shader`, `TennisPost.asset`, `TennisURP*`), `Tennis.unity`, hero/character files, Swift/menu files.
  READ them freely; reuse them by reference (`Resources.Load`, `Shader.Find`), never edit them.
  `work/postcard-look/guards.sh` prints the unchanged-gates; run it before you report.
* Unity runs ONLY through `work/postcard-look/heavy.sh <label> <unity command...>` (Unity batch runs and xcodebuild must never overlap).
  Binary: `/Applications/Unity/Hub/Editor/6000.3.24f1/Unity.app/Contents/MacOS/Unity -batchmode -projectPath Unity -executeMethod <Type.Method> -logFile <abs log>`; run long ones with `run_in_background`.
  Only agents whose role says "owns Unity" run Unity. Everyone else works Blender-only.
* Blender: headless only — `/Applications/Blender.app/Contents/MacOS/Blender -b --factory-startup --python <script> -- <args>` (Blender 5.2). Do NOT use the Blender MCP / the GUI session
  (another chat may be using it). numpy exists only in Blender's python (`/Applications/Blender.app/Contents/Resources/5.2/python/bin/python3.13`); system `python3` has Pillow but no numpy/bpy.
* The existing hole 8/9/10 files are untracked (not in git): `work/postcard-look/baseline/` holds the originals. Restore from there if you wreck something.
* Every claim is a binary `GATE: <what> PASS|FAIL` with the measured numbers. Screenshots/renders are proof; a Blender render is NOT proof for the Game view.
* Scoring is frozen: no changes to `LieAt`, shore polygons, centerlines, pin positions, `PLAY_Z` (6 m), par, hazard counts/positions. The top surfaces of TERRAIN/FAIRWAY/GREEN/TEE_BOX/BUNKER must keep their
  exact outlines and heights (z offsets as built today). One play height, no slope the ball rolls on.
* Style: Switch Sports / Wii clarity, soft + readable on a phone. Not photoreal, not grim, not flat-colour Roblox. Silhouette, colour blocks and landmarks from the stills win over photo detail.

## 1. Where things live

| what | path | owner |
|---|---|---|
| generated textures (PNG) | `Unity/Assets/Resources/Course/Look/*.png` | textures agent (A1); plant palette atlas by props agent (A4) |
| texture generator | `blender/scripts/golf_look_textures.py` | A1 |
| runtime look kit / atmosphere | `Unity/Assets/Scripts/Course/GolfLook.cs`, `GolfAtmosphere.cs` | A2 |
| HoleView override fix | `Unity/Assets/Scripts/Course/HoleView.cs` | A2 |
| golf scene light/sky/post hook | `Unity/Assets/Scripts/Game/GolfGame.cs` (minimal edit), `CameraRig.cs` (near plane only) | A2 |
| surf/waterfall shader | `Unity/Assets/Resources/Course/Shaders/GolfSurf.shader` (`GolfArcade/GolfSurf`) | A2 |
| texture import settings | `Unity/Assets/Editor/GolfLookTextureImporter.cs` | A2 |
| Blender ground/water/wall/path/lava lib | `blender/scripts/postcard_look_lib.py` | A3 |
| Blender props lib (rocks, masonry, plants, scatter) | `blender/scripts/postcard_props_lib.py` | A4 |
| Blender mesh gates | `blender/scripts/postcard_look_verify.py` | A5 |
| per-hole Blender build | `blender/scripts/hole08|09|10_build.py` (+ `holeNN_look.py` if wanted), `blender/hole_NN.blend`, `Unity/Assets/Resources/Course/hole_NN.fbx` | hole agents |
| proof screenshots | `ArtDir/screenshots/golf_postcards/look/` | integrator |

`postcard_lib.py` stays the verified flat-geometry builder (play surfaces, terrain, shore). New look code is a POST-PASS / add-on in the new libs; if a lib change is unavoidable keep every existing function signature and result identical for the geometry (top surfaces bit-identical) — A3 is the only one who may edit `postcard_lib.py`.

## 2. Collision / naming rule (HoleView.GroundPrefixes)

`HoleView` builds a MeshCollider ONLY for mesh names starting with `TERRAIN`, `FAIRWAY`, `GREEN`, `TEE_BOX`, `BUNKER`, `CART_PATH`. Everything new must use another prefix:

| prefix | use |
|---|---|
| `ROCK_` | every rock: loose rocks, ledge rocks, sea stacks, basalt column clusters/walls, cliff skin cladding (`ROCK_SKIN_*`) |
| `PLANT_` | tufts, shrubs, flowers, vines, trees/agave/palms |
| `DRESS_` | stone path overlay (`DRESS_PATH_*`), arch/ruin masonry (`DRESS_ARCH_*`, `DRESS_RUIN_*`), waterfall sheet frame pieces, background cone `DRESS_CONE`, smoke cards `DRESS_SMOKE_*`, visual sand patches `DRESS_SAND_*` (never `BUNKER*`) |
| `WATER_` | `WATER_OCEAN`, `WATER_SHELF`, `WATER_SURF_nn`, `WATER_FALL_nn` (waterfall sheet + whitewater), `WATER_LAVA` |
| `LAVA_` | `LAVA_LIGHT_nn` EMPTY objects (positions for static orange point lights), `LAVA_GLOW_*` visual meshes |

Do not start any visible new object with `FLAG`, `HOLE_CUP`, `BALL_START`, `MARKER_` (HoleView hides those names). Gameplay placeholders (`FLAG, FLAG_POLE, HOLE_CUP, BALL_START, MARKER_TEE/PIN/UP`) and `TEE_MARKER_1/2` stay exactly as built.
Objects whose name starts `WATER` cast no shadow in Unity (HoleView) — fine for water; the waterfall sheet is `WATER_FALL_*` for the same reason.

## 3. Material names the FBX carries → what Unity renders

Blender materials are named exactly these (Principled BSDF with Image Texture nodes pointing at the PNGs in `Resources/Course/Look/`, so Blender previews show the real look).
At runtime `HoleView` asks `GolfLook.Get(name)` for every renderer material whose name starts `LK_`; those come out as real textured URP materials.
Old `MAT_*` names (hole 7, gameplay parts like `MAT_FLAG`, `MAT_POLE`, `MAT_CUP`, `MAT_BALL`) keep going through `HoleView.Palette` unchanged. A material that already carries a base map / normal map / emission map is never replaced by a flat colour.

`tile` = metres of terrain per texture repeat (UV 0..1). ALL UVs are authored in tile units = metres / tile. Unity materials keep tiling (1,1). `S` = URP `_Smoothness`.

| material | surface | textures (suffix `_C` albedo sRGB, `_N` tangent-space normal OpenGL +Y, `_E` emission sRGB) | tile (m) | S | notes |
|---|---|---|---|---|---|
| `LK_FAIRWAY` | fairway, first cut, apron | `Fairway_C`, `Fairway_N` (1024) | 10 | .10 | emerald, soft mottle, LENGTHWISE mow stripes in the albedo (2 bands per tile). UV: u = signed lateral offset from the centerline, v = arc length along it, so stripes follow the line of play. Replaces MAT_FAIRWAY, MAT_FAIRWAY_STRIPE, MAT_FIRSTCUT |
| `LK_GREEN` | green, tee box, bunker lip | `Green_C`, `Green_N` (1024) | 6 | .12 | brighter, finer, very subtle mow rings/stripes. Planar UV |
| `LK_ROUGH` | terrain top outside the play surfaces, lip band | `Rough_C`, `Rough_N` (1024) | 12 | .08 | darker, varied, tufty. Planar UV |
| `LK_SCRUB` | Split's left ridge top (a material only: the lie stays Rough) | `Scrub_C`, `Scrub_N` (1024) | 12 | .08 | olive / khaki / dry-brown mottle |
| `LK_SAND` | bunker sand | `Sand_C`, `Sand_N` (512) | 6 | .12 | warm sand, soft ripples; reads as sand, not a disc |
| `LK_CLIFF` | terrain walls (Needle, Split) | `Cliff_C`, `Cliff_N` (1024) | 12 | .12 | DARK stratified layers (horizontal bands), moss/green hints. UV: u = metres around the wall loop, v = z |
| `LK_CLIFF_DARK` | lowest wall bands near/below the waterline | `CliffDark_C`, `CliffDark_N` (512) | 12 | .35 | wet, darker, algae tint (wet rock near water may be glossier) |
| `LK_ROCK` | loose rocks, ledge rocks, sea stacks | `Rock_C`, `Rock_N` (512) | 4 | .12 | grey-brown, chipped planes, a little moss. Object-space box UV in tile units |
| `LK_ROCK_WET` | rocks standing in/at the water | same maps as LK_ROCK | 4 | .35 | darker tint + glossier |
| `LK_PATH` | Needle stone path | `Path_C`, `Path_N` (512) | 5 | .10 | pale flagstones with grass joints |
| `LK_MASONRY` | arch / ruin blocks | `Masonry_C`, `Masonry_N` (512) | 4 | .10 | warm grey cut stone, mortar lines, moss patches |
| `LK_BASALT` | crater walls, columns, pillar sides, pillar/tee underside | `Basalt_C`, `Basalt_N`, `Basalt_E` (1024) | 8 | .15 | near-black columnar basalt: vertical hex-column facets, chipped edges; `_E` = crack glow mask (orange on dark; emission is black almost everywhere) |
| `LK_LAVA` | crater lava | `Lava_C`, `Lava_N`, `Lava_E` (1024) | 24 | .30 | STATIC: dark crust plates (near-black) with glowing orange/yellow fissures; `_E` carries the glow. Reads as lava, not an orange plane |
| `LK_PLANTS` | tufts, shrubs, flowers, vines, agave, small trees | `Plants_C` (256 palette atlas, no tiling) | n/a | .10 | ONE shared palette: greens x6, olive x3, dry straw, purple + white + yellow flower, vine green, trunk brown, agave blue-green; UV islands sit on swatch centres, tiny gradient/noise inside each swatch. GPU instancing on |
| `LK_WATER` | `WATER_OCEAN` | none (shader `GolfArcade/TennisWater`) | n/a | n/a | deep ocean. Per-material colours set by `GolfLook` |
| `LK_WATER_SHALLOW` | `WATER_SHELF` | none (`GolfArcade/TennisWater`) | n/a | n/a | turquoise shelf around the islands, ragged outer edge |
| `LK_SURF` | `WATER_SURF_nn` | `Surf_C` (RGBA noise foam, 512, tiling) | 8 | n/a | shader `GolfArcade/GolfSurf`: noise-broken whitewater, vertex-colour A = shoreline closeness. STATIC. (TennisWater has NO foam and tennis files are frozen, so whitewater is a golf-owned shader on a ragged overlay mesh; the OCEAN stays TennisWater) |
| `LK_FALL` | `WATER_FALL_nn` waterfall sheet | `Fall_C` (RGBA streaks, 256x512) | n/a | n/a | `GolfArcade/GolfSurf`, UV v runs down the sheet. STATIC |
| `LK_SMOKE` | `DRESS_SMOKE_nn` cards | `Smoke_C` (RGBA, 512) | n/a | n/a | `GolfArcade/GolfSurf` |

Sky textures (A1): `Sky_Crater_C.png` (2048x880, same projection as `Tennis/Environment/SkyPanorama.png`: smoky orange-to-aubergine dusk with dark smoke billows). Needle and Split reuse `Tennis/Environment/SkyPanorama` (bright blue + warm cumulus) with `TennisSky` tint properties.

Texture import (A2's `GolfLookTextureImporter`): files under `Assets/Resources/Course/Look/` — `*_N.png` NormalMap; `*_E.png`, `*_C.png` sRGB colour; wrap Repeat (except `Plants_C`, `Sky_*`: Clamp / sky default), mipmaps on, aniso 4, max 1024 (512 for 512s), compressed (no crunch). Total Look/ folder ≤ 25 MB on disk.

## 4. Vertex data conventions (Blender → FBX → Unity)

* UV0 only, in tile units as above. No UV1.
* `WATER_SURF_nn`: vertex colour attribute (FBX colours, linear) A = shoreline closeness (1 at the island base/wet line, 0 at the open edge), R = random phase 0..1; UV0 = world (x, y) / 8 m.
* `WATER_FALL_nn`: UV0 u across (0..1), v down the sheet (0 top .. 1 foot, repeat allowed); the whitewater at the foot is a `WATER_SURF_nn` patch.
* `LAVA_LIGHT_nn`: EMPTY objects at the positions where Unity places static orange point lights (hole 10: 3 to 5 of them, above the lava near the walls/pillar).
* No animation, no armatures. Export recipe as in `blender/scripts/POSTCARDS_README.md` (axis -Z/Y, FBX_SCALE_ALL, no leaf bones) with textures NOT embedded (`path_mode='STRIP'`, `embed_textures=False`); keep `isReadable: 1` and `tangentImportMode: 3` in the `.meta` files of hole_08/09/10.fbx.

## 5. Unity API surface (A2 implements; others/gates call it)

```csharp
namespace GolfArcade.Course {
  public static class GolfLook {
    public static bool Handles(string materialName);          // name starts with "LK_"
    public static Material Get(string materialName);          // cached; textured URP Lit / TennisWater / lava / GolfSurf
    public static void DressModel(GameObject model, int holeNumber); // swap LK_ materials, shadows, LAVA_LIGHT_nn -> point lights, enableInstancing
  }
  public static class GolfAtmosphere {
    public static void Apply(Light sun, Camera camera, int holeNumber);  // Golf scene only: painted sky, key/fill/rim, trilight, softer fog, TennisPost profile on the golf camera
  }
}
```
`HoleView.BuildFromModel` order per material: LK_ → `GolfLook.Get`; has base/normal/emission map already → keep; `Palette` name → flat colour (hole 7 + gameplay parts); otherwise untouched. Water names go to TennisWater, never to a flat `_BaseColor`.
`GolfGame.Awake` replaces its light/fog block with the atmosphere call; `StartHole` re-applies per hole (heading / palette per hole). One Golf-scene directional key (warm, about 2.3), one cool fill (about 0.8, no shadows), one rim, `AmbientMode.Trilight`, linear fog softer than the old 250-700 grey wash, painted sky via `GolfArcade/TennisSky`, post = the existing `Tennis/Rendering/TennisPost` profile loaded on the golf camera (cloned Volume, shared asset untouched; no new post stack).

## 6. Budgets and gates the build must satisfy

* Props (rocks, tufts, shrubs, flowers, vines, trees, agave): each library mesh <= 500 faces, tufts <= ~120; ONE shared `LK_PLANTS` material; instanced = linked duplicates of the same library mesh (shared mesh data); scattered (Poisson-ish), never on the green in a way that hides the pin, never on the line of play surfaces inside Fairway/Green/Bunker/Tee outlines unless it is the DRESS overlay.
* >= 4 unique rock meshes per hole, none a 12-vertex icosahedron (target >= 60 verts each), at least 3 of them instanced >= 2 times. Crater: `ROCK_WALL_BLUNT` / `ROCK_WALL_FLAT` (or whatever replaces them) are basalt column clusters (hex prisms), visibly columns.
* Per hole: <= ~250k triangles visible, FBX <= ~20 MB.
* `WATER_OCEAN` stays one big plane (TennisWater is world-space); `WATER_LAVA` is a subdivided mesh (not 1 polygon) with `LK_LAVA`. NO `MAT_FOAM` anywhere on holes 8-10; no white-strip foam.
* HoleView/GolfLook: no postcard material is forced to `_BaseColor` only; fairway/green/rough/cliff/rock materials render with a base map AND a normal map in the Game view.
* New objects use only the §2 prefixes. `PostcardImportCheck` ground-height/lie/marker gates stay PASS (3000 samples, play band 6 m).
* Proof shots (integrator): 9 PNG/JPG in `ArtDir/screenshots/golf_postcards/look/` — tee + green per hole at the phone camera (900x1600 via `CameraRig.FrameAddress`), plus close shots: Needle arch, Split scrub ridge, Crater lava-meets-basalt.

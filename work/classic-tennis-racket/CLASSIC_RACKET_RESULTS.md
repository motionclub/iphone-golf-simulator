# Classic tennis racket — results (staged, hero untouched)

`GATE: CLASSIC_RACKET PASS` — all nine gates pass on the definitions below (`checks.json`, `proof/checks.json`).
Nothing was installed: no ArtDir hero blend, no hero FBX, no clothes kit and no Unity project file was written. Hero blends were only read (`bpy.data.libraries.load`) and their SHA-256 is identical before and after.

## Gates

| Gate | Result | Evidence |
|---|---|---|
| LOOK_CLASSIC | PASS | matte white frame (#EEEDEA, roughness 0.50), white strings (#E8E7E3), black wrapped grip + flared black butt cap (#1C1C1F); oval egg-shaped head, open Y throat with a rounded triangular window (frame is one manifold surface, genus 2 = string opening + throat window), diamond string lattice with grommet collars, as in the chosen pick. `proof/01_turnaround.png`, `proof/02_look_vs_chosen_ref.png` |
| NO_LOGOS | PASS | no text/curve objects, no images, no image-texture nodes, no UV layers, FBX has 0 Texture/Video objects, materials are flat colours |
| SCALE_HERO | PASS | length **0.688 m** (0.68–0.70), head **0.348 m** tall × 0.285 m wide (0.32–0.35), = 0.404 × hero height (1.702 / 1.704 m); FBX scale 1, verified in Unity (file scale 1, longest bounds extent 0.688 m). `proof/07_scale_lineup.png` |
| GRIP_DIAMETER | PASS | usable grip **Ø 0.0342 m** mean (slices 0.0328–0.0346), length **0.198 m**, centred on the origin; butt cap Ø 0.038 m (slightly larger, separate mesh) |
| HAND_FIT | PASS | exact BVH triangle–triangle tests, see below |
| SOCKET_HAND_RACKET | PASS | `Hand_Racket` EMPTY created per body, parented to the (copied) hand/body; racket parents to it with an identity local transform; unparent / delete leaves the body vertex data bit-identical; Unity placement reproduces Blender to < 0.01 mm. `proof/06_socket_diagram.png` |
| BODY_SHA_UNCHANGED | PASS | male `fd04bc286f68…2347`, female `200dc3b93e65…85cd` identical before/after (also the two hero FBXs and file mtimes) |
| EXPORT | PASS | `export/Racket_Classic.blend`, `export/Racket_Classic.fbx` (+ `Racket_Classic_Collider.fbx`); FBX re-import error 0.0001 mm; Unity 6000.3.24f1 import: file scale 1, global scale 1, 10,760 tris, 3 named materials |
| PROOFS | PASS | `proof/01…07`, raw renders in `proof/raw/`, `checks.json` |

### HAND_FIT numbers (racket vs mesh, exact tri–tri overlap + nearest-distance clearance)

| Pose | racket vs hand | racket vs whole body | min clearance |
|---|---|---|---|
| male A-pose (locked, unposed) | 0 overlapping triangles | 0 | 0.50 mm |
| male ready stance (proof pose) | 0 | 0 | 0.50 mm; finger-to-grip gaps pinky 1.5 / ring 0.4 / middle 0.5 / index 0.4 mm |
| female A-pose (locked, unposed) | 0 | **561 + 500 + 62 triangles** (frame/strings/grip cross the thigh) | n/a — see disclosure 2 |
| female ready stance (proof pose) | 0 | 0 | 0.21 mm |

## What was built

`export/Racket_Classic.blend` — `Hand_Racket` (EMPTY, socket template) → `Racket_Classic` (frame: head loop + throat arms + stem as one smooth-blended SDF surface) with children `StringBed` (40 string tubes + 80 grommet collars), `Grip` (wrapped tape bands, Ø 0.034), `ButtCap` (Ø 0.038, recessed disc end), `Collider_Racket` (hidden, 120 tris: shaft capsule + head prism).

* Racket local frame: **origin = centre of the usable grip**, **+Y = shaft towards the head**, **+Z = hitting-face normal** (palm side), +X = Y × Z.
* Triangles (disclosed): frame 6,000 + strings/grommets 1,976 + grip 2,304 + butt cap 480 = **10,760 visual**; collider 120 (separate FBX). Verts 2,998 / 1,368 / 1,154 / 242 in Blender (Unity counts split verts at hard normals: 1,442 / 314 for grip / cap).
* Materials (URP Lit equivalents staged in `export/unity_stage/Materials/*.mat`, built from the project's `Base_Grey.mat`): `White_Frame` smoothness 0.50, `White_Strings` 0.45, `Black_Grip` 0.22, metallic 0, opaque.
* Frame normals are analytic SDF-gradient normals (smooth regardless of triangulation). Mirror symmetry of the frame (surface distance) 1.4 mm max — decimation, not a design asymmetry.

## Socket and Unity install note (`export/racket_classic_socket.json` has every number)

Per body: the grip sits in the **right-hand frame** (u along the fingers, v towards the thumb, w = palm normal): handle axis = (sin φ, cos φ, 0) with **φ = 52°**, face normal = palm normal rolled **45°** about the shaft, grip centre at (U, V, W) = male (−0.020, 0, +0.0287) m, female (−0.020, 0, +0.0402) m. Hand frames came from the meshes (PCA + palm-plane refit). Bind-pose world pose of `Hand_Racket`:

| | Blender (m) | Unity (m) |
|---|---|---|
| male | (−0.5786, −0.1144, 0.8598) | (0.5786, 0.8598, 0.1144) |
| female | (−0.2327, 0.0344, 0.7613) | (0.2327, 0.7613, −0.0344) |

Unity steps (nothing was copied into the project):
1. Import `export/Racket_Classic.fbx` with the project's usual model settings. It imports with **prefab-root Euler (270, 0, 0)**, scale 1, file scale 1 — the same Blender→Unity conversion as the HeroBase FBXs, i.e. `(x, y, z)_Blender → (−x, z, −y)_Unity`. Keep that local rotation.
2. Remap its three slots to `White_Frame`, `White_Strings`, `Black_Grip` (`export/unity_stage/Materials`).
3. Under the right-hand transform create an empty `Hand_Racket`; set `position`/`rotation = Quaternion.LookRotation(forward, up)` to the bind-pose values in the JSON (`apose_world_unity`), then parent it to the hand bone keeping world pose.
4. `Instantiate(racketPrefab).transform.SetParent(handRacket, false)` — local position 0, imported local rotation kept.
5. Optional: `Racket_Classic_Collider.fbx` → delete its renderer and use it as a convex MeshCollider (or use a capsule r 0.019 from y −0.111 to 0.236 plus a 0.285 × 0.348 × 0.034 oval).

Verified in a throwaway Unity project outside the repo (hero FBX copies + racket FBX, no project file touched): min vertex distance racket↔body = male 1.7634 mm / female 0.6753 mm in Unity vs 1.7635 / 0.6753 mm in Blender, same vertex pairs (`data/unity_check_socket.json`, `data/vertex_dist_blender.json`).

## Disclosures

1. **Proof poses are proof-only.** The locked hero hands have straight fingers and no rig. The "ready stance" images pose a **duplicate** of the body: fingers are bent along a path that hugs the grip (copy of the mesh, no skeleton), the arm is skinned (male elbow 95° + shoulder adduction 16°; female elbow 95° + forearm supinated 90°) and the racket follows the hand rigidly through the same `Hand_Racket` socket. The thumbs stay in their locked pose. The staged `*_ReadyStance_PROOFPOSE.blend` files are labelled accordingly; the hero blends are not modified.
2. **Female A-pose.** The ArtDir female hand is a placeholder (palm ball + sausage fingers, pronated palm-back, ~45 % of the male hand) and her arm hangs flush against the thigh, so the static A-pose racket clears her hand but crosses the thigh; any right-hand grip would. The ready-stance proof is clean (0 overlaps). Her fingers are short sausages, so only three of the four reach the grip. Recompute the female socket (`scripts/run_onhand.py female …`, needs the finger model updated) once the finished hands (08c) are installed; the grip diameter does not change.
3. The male A-pose grip rests across the palm on straight fingers (locked pose) with 0.5 mm clearance; the racket hangs head-forward-down.
4. Colliders are a separate 120-tri FBX so the visual FBX stays 4 meshes / 3 materials.
5. Throwaway Unity project and all scratch files live in the session scratchpad / `work/classic-tennis-racket/` only. The live Blender GUI (MCP) was not used or modified; all builds ran headless.

## Files

```
CLASSIC_RACKET_RESULTS.md   checks.json
export/  Racket_Classic.blend  Racket_Classic.fbx  Racket_Classic_Collider.fbx  export_report.json  racket_classic_socket.json
         RacketOnHero_Male_APose.blend  RacketOnHero_Female_APose.blend
         RacketOnHero_Male_ReadyStance_PROOFPOSE.blend  RacketOnHero_Female_ReadyStance_PROOFPOSE.blend
         unity_stage/Materials/{White_Frame,White_Strings,Black_Grip}.mat
proof/   01_turnaround  02_look_vs_chosen_ref  03_male_apose  04_male_ready  05_female_ready  06_socket_diagram  07_scale_lineup  checks.json  raw/
data/    onhand_run/onhand_{male,female}.json  measure_final.json  unity_check_{racket,socket}.json  vertex_dist_blender.json
scripts/ (see scripts/README.md)
```

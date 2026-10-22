# Standard tennis kit - WORN (untucked polo, contrasting waistband, mid-thigh skirt)

Staged only. Nothing under `ArtDir` is written, the HeroBase bodies are read-only (SHA verified before/after), the racket is untouched.
Result and evidence: `GATE_RESULTS.md`, numbers: `proof/checks.json`, pictures: `proof/*.png`, files: `export/`.

## Deliverables (`export/`)
| file | content |
|---|---|
| `StandardKit_Male.blend`, `StandardKit_Female.blend` | `Kit_White` / `Kit_Black` collections (same geometry, swapped material slots), `FitRef` collection = reference body copy (never exported) |
| `StdKit_{Male,Female}_{White,Black}.fbx` | scale 1, metres, -Z forward / Y up (same flags as the body FBX); 6 meshes parented under 4 socket empties |
| `StdKit_Female_{White,Black}_ArmsCandFit.fbx` | female polo + skort with the socks/sneakers fit to the arms-candidate feet |
| `manifest_*.json`, `fbx_verify.json` | per-piece TRI / bounds / topology, FBX round-trip (vertex, normal, UV, material, parent) |

Pieces (separate closed meshes, identity world transform, parent = socket empty):
`Kit_Top_Polo_*` -> `Chest_Top`, `Kit_Bottom_Shorts_M` / `Kit_Bottom_Skort_F` -> `Hip_Bottom`, `Kit_Sock_L/R` + `Kit_Shoe_L/R` -> `Foot_L_Shoe` / `Foot_R_Shoe`.
Meshes are authored in body space; swapping a piece = replace the one child mesh under its socket.
Material slots: 0 fabric, 1 piping, 2 waistband (bottoms only, the CONTRAST colour: black on the white kit, white on the black kit). Unity materials `Std_White_Lit` / `Std_Black_Lit` (URP Lit stand-ins, no textures).

## What changed vs `work/standard-tennis-kit-wb`
* every piece is a closed double-walled shell (outer + inner wall + rolled rims, welded, per-corner custom normals): polo/bottom 3 mm, socks 2 mm, shoes 3.6 mm, waistband 4.5 mm
* polo UNTUCKED: hem 15.8-20 mm below the band top (lap), inner wall >= 1.5 mm outside the band; clearance off the skin ~8-16 mm on the waist/hips (was ~3 mm)
* waistband = lofted closed ring (40 mm, 6.5..11 mm off the skin, square bottom, rolled top) inside the bottom mesh; fabric/skirt top laps its bottom edge 5.5 mm
* male shorts: two separate leg tubes; female: A-line skirt to mid-thigh (hem z 0.629, crotch 0.80, knee 0.49) over a hidden liner (hem z 0.729), wrap flap kept

## Rebuild
```
scripts/run_all.sh          # parts -> assemble -> FBX -> checks -> proofs -> sheets   (~10 min, headless Blender 5.2)
scripts/unity_check.sh <scratch_unity_project>   # Unity 6000.3 batch import of the FBXs in a scratch project OUTSIDE the repo -> proof/unity_import_report.json
python3 scripts/final_report.py   # evaluates the gates -> proof/checks.json + GATE_RESULTS.md
```
Order inside `build_parts.sh` matters: shorts, skort (write `data/band_*.npz`) -> polos (built against the band) -> socks -> shoes (clear the socks).
Single parts: `scripts/build_parts.sh polo_f skort ...`; quick look: `scripts/kv.sh female polo_female,skort_female full white,black`.

## Code map (`scripts/`)
`kitlib.py` numpy/BVH helpers - `sdf.py` SDF grid, surface nets, clip, sheet cleaning (despike, sliver merge, non-manifold split) - `shell.py` garment shell from the body SDF (+ obstacles) -
`kit_common.py` closed shells, rims, ribbons/buttons (closed islands), weld, topology, enforcement helpers - `band.py` waistband loft -
`polo.py` `shorts.py` `skort.py` `sock.py` `shoe.py` builders - `assemble.py` blends - `export_fbx.py` - `checks.py` measured gates (exact ray-triangle confirmation) -
`render_proofs.py` `compose_proofs.py` proofs - `final_report.py` - `KitImportCheck.cs.txt` + `unity_check.sh` Unity scratch-project import check.

Measurement notes: wall thickness is measured per part (the wrap flap sits 0.4 mm above the skirt, so comparing against every inner wall would report that gap); liner visibility and skin flash use a 1 mm beam of exact ray-triangle tests (Blender's BVH ray_cast has false negatives on edge-crossing rays); proof-render shadows of the hanging HeroBase hand on the shorts are the body's shadow, not mesh (render with `nobody` to confirm).

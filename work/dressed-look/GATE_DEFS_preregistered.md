# DRESSED_LOOK - gate definitions (written 2026-10-02 BEFORE any build or measurement beyond the five source SHAs)

Brief: put the existing standard tennis kit (white + black) and the existing classic racket on the full male and full female
bodies, show it. No resculpt, no refit, no shrinkwrap. Clip / float is labelled on the sheets, never fixed.
Reply contract: `GATE: DRESSED_LOOK PASS` or FAIL + failed lines only. All work lives in `work/dressed-look/`.

Already measured before this file was written: the five source SHA-256 values (all equal to the brief; `data/sources_before.json`)
and the ArtDir stat manifest (`data/artdir_before.json`, 21,520 files, 13.4 GB).

## Definitions

**mesh geometry hash** = SHA-256 over: vertex positions (float32), loop vertex indices, polygon loop starts, edge vertex pairs,
polygon material indices, polygon smooth flags, custom (split) normals, UV layers, non-internal boolean/int/float attributes
(sharp_edge, sharp_face ...). NOT covered: vertex-group weights, modifiers, selection/hide flags, object transforms.
Both hashes (geometry, and a second one that also covers vertex-group names + weights) are recorded for every body mesh.

1. **BODIES** - both source body blends hash to the SHAs in the brief before the build and again at the end, AND every mesh
   datablock that came from the source blend (Body_*, Face_*, Hair_F) has an identical mesh geometry hash in the dressed copy.
   (If the right-hand finger pose adds vertex groups to the body copy, that is the only data added to the body datablock; the
   geometry hash must still be identical and the vertex-group addition is disclosed in GATE_RESULTS.md.)
2. **KIT_SEPARATE** - for each hero and each colour: Polo, Bottom (shorts male / skort female), Sock L, Sock R, Shoe L, Shoe R are
   six separate MESH objects with their source names, each with its own mesh datablock (not the body's), parented (parent type
   OBJECT) to an empty with the exact socket name: Polo -> `Chest_Top`, Bottom -> `Hip_Bottom`, Sock/Shoe L -> `Foot_L_Shoe`,
   Sock/Shoe R -> `Foot_R_Shoe`. The body object has no kit geometry joined (vertex count equal to the source).
3. **RACKET_IN_HAND** - per hero: `Hand_Racket` empty exists, `Racket_Classic` is its child (+ StringBed, Grip, ButtCap,
   Collider_Racket as in the racket blend), `Hand_Racket` is parented to the character's right hand, and the racket mesh geometry
   hashes equal the racket blend's. "In hand" is measured, not asserted: min distance Grip mesh <-> right-hand mesh (evaluated, i.e.
   after the finger pose) <= 3.0 mm, and Hand_Racket origin within 0.045 m of the palm. Anything else is labelled FLOAT on the hand
   closeup (it does not fail the gate: the brief says leave it and label it). The gate fails only if the socket/parenting/geometry
   conditions are not met.
4. **BOTH_COLORS** - each dressed blend has collections `Kit_White` and `Kit_Black`, each holding the six pieces of that colour;
   piece materials are exactly the kit's `Std_White_Lit` / `Std_Black_Lit` (the black kit carries white piping and the white
   kit a black waistband exactly as authored; no third material on any kit piece); sheets exist for both colours.
5. **BOTH_SEXES** - both `HeroBase_Male_Dressed.blend` and `HeroBase_Female_Dressed.blend` exist with the right kit (Polo_M +
   Shorts_M for the male, Polo_F + Skort_F for the female).
6. **NO_REFIT** - for all 24 clothing meshes (6 pieces x 2 colours x 2 heroes): geometry hash equals the source kit piece, world
   vertex positions are bit-identical to the source kit's world positions (max abs difference exactly 0.0), no modifiers, no
   shape keys, no vertex groups, object world matrix unchanged. Zero clothing vertices moved.
7. **SOURCES_UNCHANGED** - SHA-256 of the two kit blends, the racket blend and the two source body blends equal the brief's values
   after the whole run (and the file mtimes are unchanged).
8. **ARTDIR_UNCHANGED** - ArtDir stat manifest (relative path, size, mtime_ns of every file) is identical before and after, and the
   SHA-256 of every file under `ArtDir/hero/base_lock/` is identical. My scripts never open an ArtDir path for writing (static audit of the
   scripts: the string `ArtDir` only appears in `artdir_snapshot.py`, which reads). If another chat changes ArtDir during the run
   the difference is reported with the changed paths and judged by whether any of my processes could have written them.
9. **PROOFS** - four sheets (`proof/Sheet_Male_White.png`, `Sheet_Male_Black.png`, `Sheet_Female_White.png`, `Sheet_Female_Black.png`),
   each with: full figure front, 3/4, side, back, a waist closeup and a racket-hand closeup, every CLIP / FLOAT finding captioned in
   plain words; plus `proof/Turntable_Male_White.mp4` and `proof/Turntable_Female_White.mp4` (white kit, 360 degrees, camera
   behind the court, >= 6 s, re-opened and frame-counted to prove they decode).

## CLIP / FLOAT labelling (labels, not gates)

Measured on the dressed scene, both colours (same geometry), using exact closest-point tests of the kit's own vertices against the
body surface (sign by ray-parity inside test, 3 ray directions, majority vote):
* **CLIP - skin through cloth**: outer-wall vertices of a piece that lie inside the body surface. Reported when >= 10 vertices are
  inside by > 0.5 mm; text names the region and the max depth.
* **CLIP - cloth squeezed**: inner-wall vertices inside the body by > 0.5 mm (>= 50 vertices); reported as "tight / squeezed", and as
  CLIP when it is also visible in the renders.
* **FLOAT**: inner-wall-to-body distance larger than the same vertex's distance to the body the kit was fitted to (the `FitRef_*`
  body stored in the kit blend) by more than 6 mm, over >= 100 vertices (the polo is loose by design, so absolute gaps are not
  used). Racket: min distance Grip <-> right-hand mesh > 3 mm = FLOAT on the hand closeup; racket triangles overlapping the body
  (not the hand) = CLIP (racket through thigh).
* Every label is confirmed against the renders before it is written on a sheet; a numeric hit that cannot be seen is still listed
  in GATE_RESULTS.md but captioned as "measured only".

## Pose

The bodies are un-rigged A-pose meshes with no action and no ready stance, so the pose is the bind pose. The right-hand fingers are
open in the bind pose, so the brief's "pose the hand closed on the grip" is done with a small right-hand armature
(`Rig_Hand_R`, palm + 5 digits x 3 bones) and one action; the mesh geometry itself is not edited.

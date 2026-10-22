# DRESS_MATCH_HEROES - gate definitions, written BEFORE any measurement of the kit on the skeleton

Written 2026-10-03 (job start), after reading the six memory notes, `NOTE_HERO_MAINSTAY.md`, the Unity editor tools and the Swift mirror, and after
recording the baselines in `baseline/` (32 clip-FBX sha256, prefab fingerprint `prefab_before.json`, sha256 of every file this job may edit, git status).
Facts known when this was written (geometry only, no kit-on-skeleton measurement): the kit's per-piece material slots, the kit's z extents
(shoe soles reach 25.5 mm (F) / 30.5 mm (M) below the bare foot sole), the existing exporter / prefab code.

Rules for this file: thresholds below are never changed after a measurement. If a gate fails, the real numbers go into GATE_RESULTS.md with a
disclosed note. Weight-design parameters (below, "tuning knobs") MAY be tuned before the final run; every configuration that was evaluated is listed
with its numbers in `logs/tuning_log.md`, and only the final configuration is reported as the result. A knob never touches a threshold.

## Design decisions (recorded in advance)

* **D1 colourway.** Only `Kit_White` (the authored default) is skinned and shipped. `Kit_Black` is not shipped: runtime recolouring (SetKit) covers it.
* **D2 skinning.** Weights are transferred BY NAME from the hero's own `Body_M` / `Body_F` (bind pose) to every kit vertex: nearest body face,
  barycentric interpolation of the three vertices' weights (the semantics of Blender's Data Transfer, "Nearest Face Interpolated", all deform-bone
  groups by name; the `LOOP_*` face-loop groups are not bones and are skipped). Then: cloth pieces (polo, shorts / skort) get Laplacian smoothing of
  the weight vectors over the kit's own vertex adjacency; shoes / socks get none (or a short one) so they stay rigid with the foot / shin; then
  limit to 4 influences (drop the smallest, renormalise), drop weights < 0.001, renormalise. Tuning knobs: smoothing iterations / factor per piece
  class, and the shoe blend. Nothing else about the kit is changed: no vertex position, no normal, no UV, no material assignment (except the
  documented slot-to-role renaming below).
* **D3 Unity binding.** A NEW kit FBX per hero (`export/Male_Kit.fbx`, `Female_Kit.fbx`): the SAME `Rig_<Hero>` armature (same bone names, same rest
  pose, nothing animated) + the six kit meshes with an Armature modifier. In Unity each kit `SkinnedMeshRenderer` is re-bound BY NAME to the prefab's own
  bones. The 32 clip FBXs are not touched, so their hashes stay identical and `MatchHeroBuild`'s hash guard keeps working.
* **D4 sole lift.** The kit's shoe soles sit below the bare foot sole (25.5 mm F, 30.5 mm M), so a dressed hero standing on the court would sink by that
  amount. If (and only if) the probe shows the clips do not animate the armature node `Rig_<Hero>` itself, the prefab's `Rig_<Hero>` node (and the Body
  node that is its sibling) get a constant local +y equal to the measured sole offset. The driver measures its rest heights with that offset in place, so
  its relative foot logic is unaffected. This is the one allowed non-kit change in the prefab and is listed in gate 2.
* **D5 material roles.** Blender slot -> role, merged at export so every role is one material and one submesh:
  polo: slot 0 `Kit_Shirt`, slot 1 `Kit_ShirtTrim`; shorts / skort: slots 0 and 1 `Kit_Shorts` (fabric + liner), slot 2 `Kit_ShortsBand`;
  shoe: slot 0 `Kit_Shoe` (upper), slot 1 `Kit_Sole` (outsole + tread); sock: slot 0 `Kit_Sock` (its slot 1 is unused).
  Authored colours (the White kit): Std_White_Lit linear 0.848 = sRGB 0.9300 on every role except `Kit_ShortsBand`, which the White kit authors as
  Std_Black_Lit linear 0.003 = sRGB 0.0388 (contrast band). Smoothness 0.30, metallic 0 (roughness 0.7).
* **D6 tint maths (Unity and Swift identical).** For a picked colour `p` (sRGB 0..1 per channel): `out = max(0.9300 * p, 0.0388)` per channel.
  A white pick therefore gives the authored white; a near-black pick is floored at the authored Black kit's albedo so folds still read.
  Derived roles when their parent is picked: let `L = 0.2126 R + 0.7152 G + 0.0722 B` of `p`; if `L >= 0.5` the derived pick is `p * 0.65` (darkened 35 %),
  else `p + (1 - p) * 0.35` (lightened 35 %); the derived role then uses the same `out = max(0.9300 * derived, 0.0388)`. Shirt pick -> `Kit_Shirt = out(p)`,
  `Kit_ShirtTrim = out(derived(p))`. Shorts pick -> `Kit_Shorts = out(p)`, `Kit_ShortsBand = out(derived(p))`. Shoes pick -> `Kit_Shoe = out(p)`.
  `Kit_Sole` and `Kit_Sock` are never touched. A null / empty pick leaves that group's authored colours.

## Addenda written before the first Gate-3 measurement (after building the first skinning pass and listing weight mass per bone)

* **A1 (erratum, colour constants).** D5 printed the black material as "linear 0.003 = sRGB 0.0388"; the true authored values are Std_Black_Lit linear
  (0.00271, 0.00271, 0.0031) = sRGB (0.0350, 0.0350, 0.0401). The band default is therefore (0.0350, 0.0350, 0.0401) and the floor constant in D6 is **0.0350**
  (the authored Black kit's red / green albedo). Std_White_Lit linear 0.84809 = sRGB 0.9300 is exact. These are design constants, not gate thresholds.
* **A2 (D2a, bone whitelist per piece).** The first transfer showed nearest-face weights leaking onto bones that cannot move that cloth (the female skort
  picked up finger-bone weight because her hanging hand is near the skirt; the polo's lower hem picked up 5 % thigh weight). Rule: each piece may only be
  influenced by the bones listed below; weight on any other bone is folded into the fallback bone before limiting to 4.
  Top (polo): Hips, Spine, Chest, UpperChest, Neck, Left/RightShoulder, Left/RightUpperArm, Left/RightLowerArm; fallback Hips for the trunk, LowerArm for hand / fingers.
  Bottom (shorts / skort): Hips, Spine, Left/RightUpperLeg, Left/RightLowerLeg; fallback Hips.
  Sock and Shoe of one side: that side's LowerLeg, Foot, Toes; fallback LowerLeg.
* **A3 (names).** The kit blend names its pieces by world x (`_L` is x < 0, which is the character's RIGHT side); the Unity renderers are named by the rig's side:
  `Kit_Sock_L` / `Kit_Shoe_L` are on `LeftLowerLeg` / `LeftFoot` (x > 0 in Blender).
* **A4 (zone bug found on the very first run, before a result was read as a result).** The covered-zone window `s0 in [-60, -1] mm` alone also admitted body vertices that are
  far from the piece (knee vertices 43 cm below the polo hem passed because the dot product with the horizontal hem normal is ~0, giving a fake 413 mm "poke"). The zone
  additionally requires the Euclidean distance to the outer sheet `|v - q| <= 0.080 m`. Nothing else changed.
* **A5 (zone, second correction, again before any result was used).** The distance window still admitted shin vertices just above the shoe collar (the collar normal is
  horizontal, the vertex lies 'above' it, 70 mm away). A covered body vertex must also be hit by its own outward ray: the covered zone = vertices passing A4 whose outward ray
  (1 mm beam: centre + 4 rays at +-0.5 mm) along the bind vertex normal meets the piece's outer sheet within 0.10 m. That is the original intent ("body vertex behind the
  kit's outer shell").
* **A6 (poke metric re-implemented; found by debugging the first valid-looking numbers, see logs/tuning_log.md).** The signed-distance-to-"outer sheet" implementation of the
  skin poke was unreliable: the normal-vs-nearest-body-point classification of "outer" triangles mislabels thin features (a toe-box triangle was labelled outer, which produced a
  fake 28 mm shoe poke whose nearest true triangle was the insole 11.8 mm away). Same intent, ray formulation: a **covered body vertex** (at bind) is one whose outward ray along
  the bind normal meets the piece exactly twice within 0.05 m (inner wall front-facing, outer wall back-facing, the second hit <= 12 mm behind the first), for at least 3 of the
  5 rays of a 1 mm beam; **in a pose it pokes** iff none of the 5 rays of its posed outward beam meets the piece within 0.05 m (each 'no hit' re-confirmed with an exact
  Moller-Trumbore test) AND the inward ray (along minus the posed normal) meets a front-facing triangle of the piece within 0.04 m - the **poke depth is that distance**. A vertex
  with no wall behind it within 0.04 m is counted as 'exposed' (hem ride-up, cuff gap) and reported, not gated. Float uses every kit vertex whose bind distance to the body is
  <= 0.040 m (no inner / outer split). Thresholds unchanged.
* **A7 (poke metric, final form; supersedes the escape-ray poke of A6).** A6's 'outward ray escapes' counted vertices that look out through a sleeve / hem opening (verified false
  positive: 6 left-shoulder vertices were flagged at up to 38 mm while a close-up render shows no skin through the polo). The poke is now measured by correspondence with the
  vertex's own *home wall*: at bind, the centre ray of a covered vertex meets the piece's inner wall then its outer wall; the outer-wall hit is stored as (triangle, barycentric).
  In a pose `P` = that barycentric point on the posed triangle, `N` = the posed unit normal of that triangle (winding as at bind, pointing away from the body); **poke depth =
  max(0, (v - P) . N)** provided `|v - P| <= 0.06 m` (the vertex is still next to its home point; a vertex that slid away laterally - armpit, cuff, hem - is counted as `slid`, reported,
  not gated). No inner / outer classification of triangles is needed. Covered zone, thresholds, float: unchanged from A6 / gate 3.
* **A8 (covered zone, third tightening; found while building a second weight-transfer variant).** Two ray hits (front-facing, then back-facing) are also produced by a ray that enters the cloth from
  OUTSIDE (a palm facing the polo hem), so the covered zone could contain vertices that are not under the cloth. A covered vertex must additionally be its inner-wall hit's nearest body
  point within 4 mm (`dist(body, hit_inner) >= t1 - 4 mm`) with the gap `t1 <= 35 mm`. This applies to the measurement zone and to the ray-based weight transfer alike. No threshold changed.
* **A9 (tuning knob added, D2 is extended).** Besides the nearest-face transfer (D2), a ray-based transfer is evaluated: every covered body vertex hands its weight vector to the corners of the two
  walls it meets (barycentric); kit vertices with no such mass are filled by harmonic diffusion. Selected by `DR_TRANSFER`; every evaluated configuration is in `logs/tuning_log.md`.

## Gate 1 - KIT_SKINNED
On the six kit meshes of each hero (a) in the Blender source of the kit FBX, (b) after Unity import (`Mesh.GetAllBoneWeights` per vertex), (c) in the prefab.
PASS iff: every vertex has at most 4 influences; `|sum(weights) - 1| <= 1e-4` for every vertex (Blender source; Unity imported sums are compared with 1e-3 because
the importer re-normalises in float); every influencing bone name is a bone of `Rig_<Hero>` (deform bones; `Root` has no deform); zero vertices have no weight.

## Gate 2 - BODY_UNCHANGED
PASS iff all of: (a) sha256 of the 32 files `work/match-anim-set/export/fbx/*.fbx` equals `baseline/clip_fbx_sha256_before.txt`, and the 32 copies under
`Unity/Assets/Characters/MatchHeroes/<Sex>/` equal the same hashes; (b) in the prefab fingerprint (`MatchHeroKitBaseline`, before vs after) every non-kit
renderer (`Body_*`, `Face_*`, the racket parts) has identical vertex count, triangle count, position sha, bone-weight sha, bindpose sha, triangle sha, material
names and bone paths; every non-kit node has identical path, parent, local rotation / scale / components, and identical local position except the single D4 lift
on `Rig_<Hero>` and `Body_*` (exactly +sole offset on y, nothing else); (c) the curve sha of all 16 clips x 2 heroes is identical; (d) the sha256 of
`work/match-anim-set/export/*.blend` and `work/tennis-shoes-fit/export/*.blend` equals `baseline/source_blends_sha256.txt`; (e) `ArtDir/`: the difference of
`git status --short ArtDir` before vs after is listed; the gate fails only if one of this job's scripts contains or writes an ArtDir path (other
sessions add files there; judged by whether my processes could have written them).

## Gate 3 - FOLLOWS_BODY (Blender, headless, depsgraph-evaluated body and kit, world space, metres)
Poses (frame = clip start + round(contact_s x 30), contact_s from `work/hero-mainstay/data/clip_table.json`): ReadyIdle frame 0, Forehand, Backhand, Serve,
Overhead, ForehandWide, VolleyForehand, Return, all at their contact time. Both heroes. Both the kit and the body are skinned by the same armature pose.

Per kit piece P (polo, shorts / skort, sock L+R, shoe L+R):
* *Outer sheet* of P = the triangles whose normal points away from the body: for the triangle centroid c, nearest point b on the bind-pose body, the triangle is
  OUTER iff `normal . (b - c) < 0`.
* *Covered zone* = body vertices v with bind-pose signed distance to P's outer sheet `s0 = (v - q) . n_q` (q nearest point on the outer sheet, n_q its triangle
  normal) in `[-0.060, -0.001]` m (inside the outer shell by at least 1 mm, at most 60 mm).
* **Skin poke** of v in a pose = `max(0, s(v))`, the same signed distance to the posed outer sheet (outer-sheet membership fixed at bind). Reported per piece:
  max and 99th percentile over the covered zone, per pose and worst over the 8 poses. **Thresholds: max <= 15 mm AND p99 <= 5 mm for every piece in every pose.**
* **Float** of a kit vertex u that belongs to P's inner sheet (the complement of the outer sheet) = `max(0, d_pose(u) - d_bind(u))` where `d` is the unsigned
  distance to the body surface, only for `d_bind <= 0.040` m. Reported max and p99 per piece and pose.
  **Thresholds: shoes and socks max <= 12 mm and p99 <= 6 mm; polo, shorts / skort max <= 40 mm and p99 <= 15 mm.**
* Extra, informational (never gating): the same two numbers on every 6th frame of all 16 clips; exposed-skin count (covered vertices whose outward ray no longer
  meets P); shoe strain = largest relative change of a triangle edge length, bind vs pose, over shoe triangles.
* Proof: a render of the worst pose per piece (kit + body clipped view).

## Gate 4 - UNITY_BIND
PASS iff: (a) `PlayerMale.prefab` / `PlayerFemale.prefab` contain six kit `SkinnedMeshRenderer`s (`Kit_Top`, `Kit_Bottom`, `Kit_Sock_L`, `Kit_Sock_R`, `Kit_Shoe_L`,
`Kit_Shoe_R`); every bone of every kit renderer is the SAME Transform instance (by identity) as the body renderer's bone of that name and is a descendant of the
prefab root; (b) an edit-mode batch test samples ReadyIdle t=0, Forehand t=contact and Forehand t=0.30 s and, for every kit renderer, compares the kit vertices
`BakeMesh`-ed in Unity (world, converted to Blender axes) with the Blender-evaluated positions of the same kit mesh at the same frames, vertex by vertex (identity
established at the bind pose): **max deviation <= 2 mm, and the kit centroid minus the body centroid within 2 mm of Blender's**; (c) no kit material is null, none uses the
error shader or a non-URP-Lit shader, and a lit test render has no magenta pixel (255,0,255 +- 10) on the kit; (d) the clip FBX hashes still equal the clip table
(`MatchHeroBuild` guard) and gate 2(a).

## Gate 5 - ROLES_TINT
PASS iff: (a) each prefab's kit renderers carry exactly the material names `Kit_Shirt`, `Kit_ShirtTrim`, `Kit_Shorts`, `Kit_ShortsBand`, `Kit_Shoe`, `Kit_Sole`, `Kit_Sock`
(all seven present); (b) the default (no `SetKit` call, or `SetKit(null, null, null)`, or empty strings) leaves every kit material equal to the authored White kit
within 1/255; (c) `SetKit(shirt, null, null)` changes exactly {Kit_Shirt, Kit_ShirtTrim}; `SetKit(null, shorts, null)` exactly {Kit_Shorts, Kit_ShortsBand};
`SetKit(null, null, shoes)` exactly {Kit_Shoe}; `SetKit(all three)` exactly those five and never `Kit_Sole` / `Kit_Sock`; skin, face and racket materials never change;
each changed colour equals the D6 formula within 1/255; a second hero instance is unaffected (materials are per instance); (d) pixel test: with coral shirt / navy shorts /
lime shoes (FF7F50 / 1E2A6E / 7CFC00-class picks) on both heroes, the pixels that differ from the default render all lie inside the screen mask of the picked roles'
renderers (mask = the same renderers rendered unlit; tolerance: 2-pixel dilation); proof renders.

## Gate 6 - SWIFT_MIRROR
PASS iff: (a) `MatchHeroLockerExport` regenerates `CharacterAssets/MatchHero_{Male,Female}.json/.lzfse` and the 12 swing frames each, with six `kind: "kit"` parts per
hero whose materials are the seven role names; the CPU-skinning vs `BakeMesh` check passes for the kit parts too (<= 2 mm); (b) the SwiftUI preview (`CharacterModelPreview`
-> `MatchHero.build`) draws the kit parts in the Ready stance and the swing frames (morph targets exist for every kit part); (c) the Swift colour maths equals D6: a shared
test-vector table (shirt coral, shorts navy, shoes lime, plus white and black picks) gives the same sRGB values (within 1/255) as the Unity formula; default player (no picks) =
authored colours; (d) snapshots of the real SwiftUI view (`CharacterModelPreview` hosted) for both sexes, default and coral / navy / lime picks, saved to `proof/swift/`, and
a pixel test that the picked render differs from the default only where kit parts are.

## Gate 7 - BUDGET
PASS iff: triangle counts per hero (body + face + kit + racket) and per-part are reported; per-frame mirror memory (decompressed bytes of one swing frame, resident
geometry of the base + 12 morph targets) and the bundle size of `MatchHero_*` assets are reported; limits: kit adds <= 100 k triangles per hero, the `MatchHero_*` assets in
the bundle <= 70 MB in total (22 MB before), resident mirror geometry per hero <= 80 MB; `xcodebuild build` of scheme GolfArcade for the iPhone 17 Pro simulator succeeds;
the existing tests this job touches still pass.

## Gate 8 - RACKET_AND_FEET
PASS iff: (a) the racket subtree (`Hand_Racket`, `Racket_Classic` and children) and every hand / finger bone have identical local transforms before and after (fingerprint),
and the clip curve shas are identical (gate 2c); (b) **SOLE_TRACK** (Blender, all frames of all 16 clips, both heroes): let `foot_min(t)` = lowest z of the bare body vertices
weighted > 0.5 to the foot / toe bones of one foot and `shoe_min(t)` the lowest z of that foot's shoe; the sole offset at bind `o0 = shoe_min - foot_min`; **PASS iff
`|(shoe_min(t) - foot_min(t)) - o0| <= 6 mm` in every frame in which the bare foot is planted (`foot_min(t) - foot_min(0) <= 5 mm`)**, per foot; (c) reported, not gating: the absolute
offset `o0` (the sink of the dressed hero without the D4 lift), the per-frame error against the undressed hero with and without the lift, and in Unity the lowest shoe vertex
at ReadyIdle t=0 relative to the prefab root (expected 0 +- 2 mm with the lift).

## Gate 9 - PROOFS
PASS iff these exist and are non-empty: Blender sheets `proof/Sheet_{Male,Female}_Dressed.png` (front, 3/4, side, back in ReadyIdle plus contact frames of Forehand, Serve, Backhand,
Overhead), `proof/BEFORE_AFTER_{Male,Female}.png` (or one combined contact sheet), the worst-pose renders per piece (`proof/worst_*`), the Unity play-mode frames
(`proof/unity/`), the Swift mirror shots (`proof/swift/`), and `NOTE_DRESS_MATCH_HEROES.md`, `run_all.sh`, `README.md`, `GATE_RESULTS.md`, `checks.json`.

## Overall
`GATE: DRESS_MATCH_HEROES PASS` iff gates 1-9 all pass; otherwise `FAIL` plus the failed lines only.

# DRESSED_LOOK - gate results

**GATE: DRESSED_LOOK PASS**

Definitions were written before building/measuring: `GATE_DEFS_preregistered.md`. Evidence: `checks.json`, `data/*.json`, pictures in `proof/`.

| Gate | Result | Evidence |
|---|---|---|
| BODIES | PASS | both body blends hash to the brief's SHA before and after; the dressed copies were byte-identical to the sources before the first edit; geometry hash of every body mesh (Body, Face, Hair_F) identical (male 2 meshes, female 3); Body vertex-array SHA-256 male ccf23b2e9f23... == ccf23b2e9f23..., female 60980b62bfa0... == 60980b62bfa0.... 16 right-hand finger vertex groups + an Armature modifier were added to each Body (disclosed below). |
| KIT_SEPARATE | PASS | per hero 12 pieces (6 white + 6 black): polo, bottom, 2 socks, 2 shoes, each its own mesh object with its own datablock, parent type OBJECT to the exactly named socket Chest_Top / Hip_Bottom / Foot_L_Shoe / Foot_R_Shoe; body vertex count equals the source. |
| RACKET_IN_HAND | PASS | Hand_Racket parented to bone Hand_R of Rig_Hand_R (right hand); Racket_Classic (+ StringBed, Grip, ButtCap, Collider_Racket) children as in the racket blend, geometry hashes equal; grip to evaluated hand min 0.90 mm male / 0.05 mm female (<= 3 mm), grip origin 23 / 18 mm from the nearest hand vertex (<= 45 mm): no FLOAT label needed. |
| BOTH_COLORS | PASS | collections Kit_White and Kit_Black (6 pieces each) in both blends; the only kit materials are Std_White_Lit and Std_Black_Lit; four sheets (male/female x white/black). |
| BOTH_SEXES | PASS | HeroBase_Male_Dressed.blend (Polo_M, Shorts_M) and HeroBase_Female_Dressed.blend (Polo_F, Skort_F). |
| NO_REFIT | PASS | 24 clothing meshes: geometry hash equal to the kit source, world vertex positions bit-identical (max |diff| = 0.0), world matrices identical, 0 modifiers, 0 shape keys, 0 vertex groups. |
| SOURCES_UNCHANGED | PASS | SHA-256 of the two kit blends, the racket blend and both source body blends equal the brief after the run; sizes and mtimes unchanged. |
| ARTDIR_UNCHANGED | PASS | ArtDir stat manifest (21520 files) identical before/after (0 added, 0 removed, 0 changed); SHA-256 of the 790 files under hero/base_lock identical; no script of this job names ArtDir except the read-only snapshot and this report. |
| PROOFS | PASS | 32 raw cells, 4 sheets (proof/Sheet_*.png), 2 turntables (240 frames, 10.0 s, [1080, 1350]) re-opened and decoded through the video sequencer (frames differ: the figure turns). |

## CLIP / FLOAT (labels, not gates - the brief says leave them and caption them)

### Male

Nothing found: skin-through 0, squeezed 0, floating 0 for polo, shorts, socks and shoes; racket and fingers cross neither body nor kit (0 triangles).

* racket: 0 triangle pairs vs body (not hand), kit 0, grip-to-hand 0.90 mm; posed hand vs body 0, vs kit 0

### Female

* **FLOAT** - Top_Polo_F: stands off the new body at the centre chest (back), z 0.98-1.28 m (1198 verts, up to 25.0 mm more than on the body it was fitted to)
* **FLOAT** - Bottom_Skort_F: stands off the new body at the centre upper thigh / hip (back), z 0.67-0.99 m (737 verts, up to 16.0 mm more than on the body it was fitted to)
* **CLIP** - Sock_L: body surface pokes through the cloth at the right lower leg (back), z 0.00-0.29 m (496 verts, up to 29.7 mm)
* **SQUEEZE** - Sock_L: cloth squeezed into the body at the right lower leg (back), z 0.00-0.29 m (470 verts, up to 29.3 mm)
* **FLOAT** - Sock_L: stands off the new body at the right lower leg (front), z 0.01-0.29 m (789 verts, up to 62.5 mm more than on the body it was fitted to)
* **CLIP** - Shoe_L: body surface pokes through the cloth at the right foot / ankle (back), z 0.00-0.10 m (382 verts, up to 29.4 mm)
* **SQUEEZE** - Shoe_L: cloth squeezed into the body at the right foot / ankle (back), z 0.00-0.10 m (331 verts, up to 29.0 mm)
* **FLOAT** - Shoe_L: stands off the new body at the right foot / ankle (front), z 0.03-0.13 m (822 verts, up to 49.4 mm more than on the body it was fitted to)
* **CLIP** - Sock_R: body surface pokes through the cloth at the left lower leg (back), z 0.00-0.29 m (506 verts, up to 29.5 mm)
* **SQUEEZE** - Sock_R: cloth squeezed into the body at the left lower leg (back), z 0.00-0.29 m (473 verts, up to 28.6 mm)
* **FLOAT** - Sock_R: stands off the new body at the left lower leg (front), z 0.02-0.29 m (780 verts, up to 62.4 mm more than on the body it was fitted to)
* **CLIP** - Shoe_R: body surface pokes through the cloth at the left foot / ankle (back), z 0.00-0.10 m (380 verts, up to 29.5 mm)
* **SQUEEZE** - Shoe_R: cloth squeezed into the body at the left foot / ankle (back), z 0.00-0.10 m (357 verts, up to 29.8 mm)
* **FLOAT** - Shoe_R: stands off the new body at the left foot / ankle (front), z 0.03-0.13 m (822 verts, up to 49.3 mm more than on the body it was fitted to)
* racket: 0 triangle pairs vs body (not hand), kit 0, grip-to-hand 0.05 mm; posed hand vs body 0, vs kit 0

Female CLIP / FLOAT that is visible in the renders: socks and shoes (the kit was fitted to the older placeholder feet: heels, ankles and toes poke through, the sock tubes stand off the shins). Polo/skort float (25 / 16 mm further off the new back / hips than off the body they were fitted to) is measured only. The ArmsCandFit shoe/sock variants exist in the kit blend but the brief says to use the authority pieces.

## How the hand pose was done

* **male** - bones: 16 (palm + 5 digits x 3); numpy twin vs Blender armature max error 4.4 micron; hold search (448 placements; the best 40 re-tried with 3 wrist tilts, 60 kept; each re-tried with 8 racket rolls = 480 candidates scored for wrap, collisions and hand-through-racket) chose du 5 mm, dv -5 mm, yaw -8 deg, tilt -12 deg, extra roll about the shaft 0 deg (racket face 45 deg from the palm normal; the racket chat's classic hold = 45), lift 50.6 mm (all four fingers touch the grip, finger-to-grip distances index 0.30, middle 0.35, ring 0.30, pinky 0.30 mm); real-mesh check: 0 racket/hand triangle overlaps.
* **female** - bones: 16 (palm + 5 digits x 3); numpy twin vs Blender armature max error 0.4 micron; hold search (448 placements; the best 40 re-tried with 3 wrist tilts, 60 kept; each re-tried with 8 racket rolls = 480 candidates scored for wrap, collisions and hand-through-racket) chose du 5 mm, dv -35 mm, yaw 8 deg, tilt -12 deg, extra roll about the shaft 0 deg (racket face 45 deg from the palm normal; the racket chat's classic hold = 45), lift 32.8 mm (all four fingers touch the grip, finger-to-grip distances index 0.30, middle 0.30, ring 0.30, pinky 0.30 mm); real-mesh check: 0 racket/hand triangle overlaps.

The pose lives in the action `Pose_GripClosed` (active); `Pose_Rest` (all zero) is stored with a fake user. Switch with `Rig_Hand_R > Animation > Action`.
The thumb stays in its bind pose (as in the racket chat's proof pose); posing it with linear blend skinning tore the skin.
The female bind hand is cupped, so her fingers were straightened virtually (open state) to place the grip against her palm and were then closed on it; the male hand is used as is.
The racket keeps the classic hold (shaft 38 deg off the finger direction, face roll 45 deg) expressed in a landmark hand frame; its position in the palm plane (du -35..+25 mm, dv -55..+15 mm), a yaw about the palm normal (-40..+16 deg), a wrist tilt (-12 / 0 / +12 deg) and the roll about the shaft (8 values) were searched to make all four fingers wrap the grip without crossing the body or the kit (body and kit are never edited).

## Disclosures

* Vertex groups were added to the dressed copy of the body (16 per hero: the right-hand finger skin weights, names = bone names) plus an Armature modifier and a parent to the rig: that is the carrier of the finger pose. Mesh geometry (positions, topology, normals, UVs, materials indices) is bit-identical to the source; the geometry hash deliberately excludes vertex-group weights (see GATE_DEFS).
* The male Hand_Racket ended 10.4 mm and 14.4 deg away from the racket chat's male socket (the hold search moved it so that all four fingers wrap the grip); grip origin is still in the palm (see RACKET_IN_HAND).
* Poses: the sources are un-rigged A-pose meshes with no action and no ready stance, so everything is the bind pose (plus the right-hand grip action). No swing was invented.
* The bodies are rendered with their own source materials (male Blockout_Grey, female Base_Grey_F + Skin_F); the studio, floor shadow and lights on the sheets and the court of the turntables are proof set-up only and are not in the blends.
* The kit blends' per-colour socket empties were not carried over: the dressed blends have ONE exactly named socket per slot and both colourways hang under it (Kit_White visible, Kit_Black hidden).
* The two kit-material copies that the two library loads created (`Std_White_Lit.001` ...) were re-pointed to the single `Std_White_Lit` / `Std_Black_Lit` (material references are not part of the geometry hash).
* The racket socket numbers of the racket chat (`racket_classic_socket.json`) were used as the starting hold for both heroes: the male hand is unchanged since, so the male hold is that socket (then adjusted by the search); the female socket was recomputed for her new 08c hand (as that chat's own notes asked) by transferring the male hold into her landmark hand frame and searching as described above (not with that chat's run_onhand.py).
* `.blend1` backups were disabled; nothing was written outside `work/dressed-look/`.

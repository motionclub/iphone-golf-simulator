# MATCH_ANIM_BUILD - gate definitions (written 2026-10-03 08:10, BEFORE any rig, skin weight or animation was built or measured)

Brief: build the 16-clip match animation set from `work/match-anim-set/WATCH.md` only, on the two staged heroes, in place, 30 fps.
Reply contract: `GATE: MATCH_ANIM_BUILD PASS` or `FAIL` + failed lines only. Everything lives in `work/match-anim-set/`.

Measured before this file was written: the two source SHA-256 values (both equal to the brief), the ArtDir stat manifest
(`data/artdir_before.json`), `git status` (`data/git_status_before.txt`), the media-file listing of the repo (`data/media_before_*.txt`),
and the structure of the two sources (below).

## Fact found before the build (changes how "actions only" can be met)

Neither source blend has an armature, a skeleton or an action (`bpy.data.armatures` = [], `bpy.data.actions` = []; only Body_*, Face_*,
Hair_F, cameras/lights/empties). The brief says "keep their bone lengths", which assumes bones exist. They do not, so a clip can only be
"on the hero" if a skeleton **fitted to that hero's own mesh** is added to the copy. I do that (landmarks measured from the mesh; no borrowed
skeleton, no mesh edit). What is added to the copy of each blend, and nothing else:
* one armature `Rig_<Hero>` (identity transform), bones placed from cross-sections of the hero's own body mesh;
* vertex groups named after the deform bones on `Body_*` and one Armature modifier on `Body_*` (skin weights);
* `Face_*` / `Hair_F` parented to the head bone (no data added to those meshes);
* the classic racket (`work/classic-tennis-racket/export/Racket_Classic.blend`, read via library-load) on a `Hand_Racket` socket parented to the right-hand bone;
* the 16 actions per hero.
The brief's own wording for the mesh check is "mesh SHA of each copy must match the source". I read "mesh SHA" exactly as the dressed-look job did.

## Definitions

**mesh geometry hash** = SHA-256 over vertex positions (float32), loop vertex indices, polygon loop starts, edge pairs, polygon material indices,
smooth flags, custom (split) normals, UV layers, and every non-internal boolean/int/float attribute (`mesh_geometry_hash` in
`work/dressed-look/scripts/dl_common.py`, copied unchanged into `scripts/common.py`). Not covered: vertex-group weights, modifiers,
parenting, selection/hide flags, object transforms. A second hash covers the ORIGINAL vertex groups (the 17 / 21 `LOOP_*` groups): names + weights.

**clip** = one of the 16 names in the brief, exactly spelled. **length** = (frame_end - frame_start) / 30 s, frames start at 0.
**contact time** = seconds from clip start at which the racket sweet spot is at the contact pose that the section names.
**THIN** = the section's own "Could not see" text (or its header) says an element this clip must contain was not observed, or was
inferred / bracketed without the ball on the strings. Where an element is THIN the clip contains no invented motion for it: the pose
stays at the READY value for that element (or follows the borrowing the section itself instructs), and `checks.json` states which
element. The THIN set is fixed here, before authoring, from the text of WATCH.md:

| clip | section | THIN? | why (quoted from the section's own text) |
|---|---|---|---|
| ReadyIdle | 1 | no | stance seen; loop is sway only (limit: idle longer than ~1.4 s not seen) |
| SplitToForehand | 2 | no | first stride, widening, trailing leg, racket back seen; hop NOT seen -> not authored |
| SplitToBackhand | 3 | no | feet seen at 0.05 s steps; shadow swing; hop NOT seen -> not authored |
| RecoverCenter | 4 | no | strides and short steps seen |
| Forehand | 5 | no | feet and ball-on-strings seen |
| ForehandOpen | 6 | **yes** | take-back / unit turn not in clip (section: use S5 whole-swing shape), L-foot landing not seen |
| ForehandWide | 7 | **yes** | "exact order of the last two steps could not be read" |
| ForehandShort | **18** | **yes** | take-back hidden, strides before the cut not in frame; contact IS in frame |
| Backhand | 9 | no | |
| BackhandWide | 10 | no | L-foot landing frame bracketed to 0.28 s (interpolated, disclosed) |
| SliceApproach | **17** | **yes (required)** | contact not in frame; strings / racket face / cut not seen |
| Serve | 12 | **yes** | ball on the strings not seen in any serve; contact time inferred from the racket apex |
| Return | 13 | **yes** | strings-contact frame not seen, two hands assumed |
| VolleyForehand | 14 | **yes** | foot order in the last 0.3 s before contact not seen |
| VolleyBackhand | 15 | **yes** | foot-by-foot order not seen |
| Overhead | 16 | **yes** | ball hidden behind the arm at the contact frame |

## Gates

1. **FROM_WATCH** - `checks.json` has, for each of the 16 clips and each hero, `watch_section` (int), the section's primary URL id/time range,
   and every key of the clip definition carries a `src` string whose first token is `S<section>` of its own section, a section the own section
   explicitly tells to borrow from (S6 -> S5 whole-swing shape), `READY` (anchor pose) or `LOCK` (a brief lock such as the 0.16 s blend).
   A script parses the `## <n>.` headings of WATCH.md and confirms the cited section exists and names the clip.
2. **SHORT_IS_18** - ForehandShort: `watch_section == 18`, the source URL id is `WBfw9nFojHc`, no key cites `S8`; the action's custom property says 18.
3. **SLICE_IS_17** - SliceApproach: `watch_section == 17`, source id `ebS3Lf25hZ0`, `thin == true` in `checks.json`, the contact racket face is not
   authored (the racket orientation is interpolated between the keys on either side of the contact window; no key inside the window has a
   face-angle `src`), one-handed through the swing (left hand released at forward-swing start).
4. **ALL_CLIPS** - both blends hold exactly the 16 actions named in the brief; `export/fbx/<Hero>_<Clip>.fbx` exists for all 32; each action
   length <= its cap (ReadyIdle in [2.0, 2.4]); all at 30 fps; every FBX re-imports (Blender importer) with one armature whose bone names and
   rest positions equal the blend's rig (<= 0.1 mm) and an animation whose frame count equals the action's.
5. **CONTACT_NAMED** - the 12 hit clips (Forehand, ForehandOpen, ForehandWide, ForehandShort, Backhand, BackhandWide, SliceApproach, Serve, Return,
   VolleyForehand, VolleyBackhand, Overhead) have `contact_time_s` in `checks.json` and on the action, in (0.15 L, 0.92 L); the 4 movement clips
   (ReadyIdle, SplitToForehand, SplitToBackhand, RecoverCenter) have `contact_time_s: null`. Measured: at the named time the sweet spot of the
   racket (point 0.5 head-length up the shaft from the throat, on the string plane) is reachable (shoulder->sweet spot <= arm length + 0.45 x racket
   length) and lies in front of the pelvis along the facing direction (>= 0.05 m), and the racket-head speed within +-0.12 s of the contact is
   >= 60 % of the clip's peak racket-head speed.
6. **IN_PLACE** - the `Root` bone and the armature object carry no translation (|loc| <= 1e-6 m on every frame); first-to-last-frame hips horizontal
   displacement <= 0.03 m; max horizontal pelvis excursion from its start <= 0.55 m; a foot flagged planted in the clip definition moves
   <= 5 mm per frame on those frames (no skating) and its ball joint is within 5 mm of the floor; sampled meshes (contact, finish, mid) have no
   vertex lower than -3 mm.
7. **RACKET_HELD** - `Hand_Racket` is a child of the right-hand bone in the blend and keeps one fixed matrix over all frames of every clip; the
   right-hand fingers are in the closed grip pose on every frame; measured on the evaluated meshes at the contact frame, the finish frame and
   every 4th frame: min distance right-hand mesh to the grip <= 3.0 mm, hand-vs-racket overlapping triangle pairs <= the baseline of the grip pose.
   Two-hand backhands (Backhand, BackhandWide, Return, VolleyBackhand): the left hand is on the grip (min distance <= 3 mm) from before the
   take-back peak through the contact frame, and opens on the finish (a release time is stored). SliceApproach: left hand released at the start
   of the forward swing and never back on the racket within the clip. One-handed clips: the left hand is not on the grip after the take-back.
   The ready pose keeps the left hand on the racket throat; ReadyIdle holds it for the whole loop.
8. **READS_FROM_BEHIND** - proof sheets exist from the camera behind the court (and from the side) at contact and at the finish for both heroes;
   measured: the peak shoulder-line yaw of the clip meets the section's number (Forehand/ForehandWide/Backhand/BackhandWide/SliceApproach/Return >= 60 deg
   from the net-facing direction; ForehandShort/ForehandOpen >= 40 deg; Serve/Overhead >= 70 deg; volleys >= 20 deg); at the contact frame >= 50 % of
   sampled points on the racket head are unoccluded from the behind-the-court camera (ray test against the evaluated body); the finish is held:
   racket-head speed stays <= 12 % of the clip's peak for >= 3 consecutive frames after the finish peak and before the recovery. `proof/Review_<Hero>.mp4`
   renders from that camera and decodes with the expected frame count.
9. **READY_LOOP** - ReadyIdle has length in [2.0, 2.4] s; its last frame equals its first (every bone rotation <= 0.05 deg, hips location <= 0.1 mm);
   the step across the seam is not larger than 2 x the median per-frame step. For every clip, first and last pose are blendable to ReadyIdle[0] in
   0.16 s: every bone's local rotation <= 25 deg from the ReadyIdle rotation, hips <= 0.05 m, both ball-of-foot points <= 0.10 m (relative to the
   root), racket head <= 0.30 m.
10. **BODY_UNCHANGED** - both source SHA-256 values are the brief's before AND after; for every mesh datablock copied from the source (Body_*, Face_*,
    Hair_F) the mesh geometry hash of the copy equals the source's; the original vertex groups hash equal; the Body mesh data has gained only vertex groups named
    after bones; no shape keys; the object transforms are unchanged. (The skeleton, bone weights, parenting and actions are the additions listed above.)
11. **ON_HERO** - each blend has `Rig_<Hero>` as the only armature; `Body_*` is skinned to it (Armature modifier targets it); each bone head lies inside the
    body mesh (ray-parity test) except the `Root`; limb joints (elbow, knee, wrist, ankle) lie within 20 mm of the local cross-section centroid of the
    limb; the rig's measured shoulder width, arm length and leg length are written to `checks.json` and are not copied from another file; all 16 actions
    drive that armature; the FBX rig equals the blend rig (gate 4). At the named frames (contact, finish, take-back peak) no triangle of the evaluated
    arms/racket passes through the torso triangle set deeper than 15 mm; any pose that did is listed as "fitted to the hero".
12. **NO_FOOTAGE_IN_REPO** - no new media file (mp4/mov/webm/mkv/m4a/part) exists in the repo except my two `proof/Review_<Hero>.mp4` renders; no script of
    mine contains a network call or a YouTube URL except the id strings in `checks.json`; `git status` differs from the baseline only under
    `work/match-anim-set/`; the ArtDir stat manifest equals the baseline (differences, if another chat wrote them, are listed and judged by whether my
    processes could have written them: none of my scripts opens an ArtDir path for writing).

## Reply
Only the line `GATE: MATCH_ANIM_BUILD PASS`, or `FAIL` followed by the failed gate names / lines.

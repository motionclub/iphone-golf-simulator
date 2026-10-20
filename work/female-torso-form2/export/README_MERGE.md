# Merging the female torso FORM2 zone

Delta is relative to the ORIGINAL start `HeroBase_Female.blend` SHA `200dc3b93e65491a8a7c3a8220c76cde5ca02ec7d1279e339f154005b22685cd` (22,444 verts). It **supersedes** chat 7's `torso_delta.npz` — do not apply both.

`torso_form2_delta.npz` (SHA `f76a2974…912db10d`): `moved_idx` (3,082), `start_co` (original float32), `new_co`, `zone_mask` (chat 7's 3,320-vertex torso mask), `vertex_count`.
The 238 zone border vertices are NOT in the delta (they stay bit-identical to the start: neck/arm-junction/leg-top seams are untouched, which the arms chat relies on).

```bash
B=/Applications/Blender.app/Contents/MacOS/Blender
# same vertex order as ArtDir (22,444): tested, 3,082 applied / 0 conflicts / bit-identical to export/HeroBase_Female_torso_form2_candidate.blend
$B -b <target.blend> --python export/merge_torso_delta.py -- export/torso_form2_delta.npz <out>.blend
# limbs-chat vertex order (22,419):
$B -b <limbs-order.blend> --python export/merge_torso_delta.py -- export/torso_form2_delta.npz <out>.blend \
   --vmap work/female-parallel-limbs/data/HeroBase_Female_limbs_vertex_map.npz
# a target that already carries chat 7's torso (e.g. the arms candidate) needs --force (its torso verts are not at the start positions)
```
* Each delta vertex must still be at its start position in the target (float32 exact); otherwise the vertex is reported and skipped (`--force` overwrites).
* Never run "clear custom split normals" on `Body_F`; positions only, the authored normal codes follow the geometry.
* Install rule: only one chat writes ArtDir at a time; ArtDir female blend is still `200dc3b9…` — nothing was installed by this chat. After installing re-run the other chats' outside-zone audits and `tools/make_final.py`-style audit.

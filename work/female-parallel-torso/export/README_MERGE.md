# Merging the female torso zone

Start blend SHA: `200dc3b93e65491a8a7c3a8220c76cde5ca02ec7d1279e339f154005b22685cd`

The torso chat only writes **vertex positions** of 3,317 vertices (zone mask in `torso_delta.npz`). Nothing else in the file changes, so merging with the head (chat 6) and limbs (chat 8) results is a per-vertex union.

```bash
/Applications/Blender.app/Contents/MacOS/Blender -b <merged-or-target>.blend \
  --python work/female-parallel-torso/export/merge_torso_delta.py -- \
  work/female-parallel-torso/export/torso_delta.npz <out>.blend
```

* Needs the same vertex count/order (22,444 verts in `Body_F`).
* Each torso vertex must still be at its **start** position in the target. If another chat moved any of them the script lists the conflicting indices and skips them (`--force` overwrites).
* Custom normals are not touched by the merge (they follow the geometry). Do **not** run "clear custom split normals" on `Body_F`: that changes head/arm shading.
* Order does not matter: head zone z ≥ 1.37, arms (beyond shoulder ball), legs z < 0.795 are disjoint from the torso zone (z 0.795–1.37, weight > 0 only for z 0.795–1.34).
* After merging, re-run the other chats' own outside-zone audits plus `audit_zone.py` here (point it at the merged blend) before installing into ArtDir.

## Merging into the limbs chat's blend (different vertex count) — tested

```bash
blender -b work/female-parallel-limbs/HeroBase_Female_limbs.blend \
  --python work/female-parallel-torso/export/merge_torso_delta.py -- \
  work/female-parallel-torso/export/torso_delta.npz <out>.blend \
  --vmap work/female-parallel-limbs/data/HeroBase_Female_limbs_vertex_map.npz      # uses its `base_to_final`
```

Tested 2026-10-01 against `HeroBase_Female_limbs.blend` (sha256 `5ff76a9b…58ec`): **3,317 / 3,317 torso vertices applied, 0 conflicts, 0 missing** — the torso and limbs zones are disjoint. Result kept as `PREVIEW_torso_plus_limbs_UNOFFICIAL.blend` (preview only; nothing was written into chat 8's folder, nothing installed in ArtDir).

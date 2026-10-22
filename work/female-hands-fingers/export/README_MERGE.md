# Female hands + fingers - staged candidate and how to merge it

Staged only. `ArtDir/hero/base_lock/blender/HeroBase_Female.blend` is still SHA `200dc3b93e65491a8a7c3a8220c76cde5ca02ec7d1279e339f154005b22685cd` (nothing installed).

| file | SHA-256 |
|---|---|
| start (arms candidate, limbs vertex order, 22,419 verts) `start/start_arms_candidate.blend` | `573ab4431d83f8651936f0081ad3bda9c6890c56ee5dce3061140198c9455f0e` |
| candidate `HeroBase_Female_hands_candidate.blend` (23,247 verts, 46,402 tris) | `1149e620985248e546e2fab93eb19f447f1a5ae673d50a2525fcae5769529ff4` |
| `HeroBase_Female_Body_hands.fbx` (body only, re-import verified: 23,247 verts / 46,402 tris / 1.7040 m) | `962828dadc0207a5918d9f31ecb0b55d8f6d8593f79dd9b912c58f54248bab13` |
| `hands_delta.npz` (portable delta) | `28a2914543b619aa54f172c6a6b246a89e371f4ae59cbe834ba3a22e2d6c719a` |

Lineage of the start: ArtDir `HeroBase_Female.blend` (200dc3b9...) + chat 7 torso (3,317 verts) + chat 8 limbs (22,419 verts, `work/female-parallel-limbs`) + arms FORM (`work/female-arms-form2`, 1,592 verts).
Index sets used for the hand shells (valid for any Body_F that still has the limbs SDF hands in the limbs vertex order): `data/start_hand_ring_{1,-1}.npy` (2 x 18 wrist-ring vertices, never moved), `data/start_hand_verts_{1,-1}.npy` (654 + 672 old hand-shell vertices, reused as slots), `data/start_hand_faces_{1,-1}.npy` (the 1,332 + 1,368 old triangles).

## A. Apply the delta (fast, guarded)
```
/Applications/Blender.app/Contents/MacOS/Blender -b <target.blend> --python work/female-hands-fingers/merge_hands_delta.py -- work/female-hands-fingers/export/hands_delta.npz <out.blend>
```
Target must be in the limbs vertex order (22,419 verts) and still carry the old SDF hands. The script STOPS if the 36 wrist-ring vertices or the hand-shell slots differ from the recorded start (someone moved the wrist: use B). Tested: delta on the start blend reproduces the candidate vertex-for-vertex (max diff 0.000 mm) and polygon-for-polygon (same multiset); `cmp_dumps.py`.
Nothing outside the two hand shells is touched; custom normals of every loop away from the change stay bit-identical (only the 36 ring vertices' 74 loops are recomputed).

## B. Rebuild on a newer base (when the rings moved)
```
/Applications/Blender.app/Contents/MacOS/Blender -b <base.blend> --python dump_mesh.py -- data/mesh_base.npz          # Body_F dump
BASE_MESH=data/mesh_base.npz ./py.sh build_hands_on_base.py export/hands_params_final.json myhands                  # -> data/cand_myhands.npz
/Applications/Blender.app/Contents/MacOS/Blender -b <base.blend> --python write_blend_f.py -- data/cand_myhands.npz <out.blend>
```
(`py.sh` = Blender's bundled Python 3.13 with numpy + Pillow; `blend.sh` runs a script in a given blend.)

## C. Install (NOT done - needs the SHA guard and Adnan's OK)
ArtDir `HeroBase_Female.blend` is in the pre-limbs 22,444-vertex order, so neither A nor B applies to it directly: first apply the limbs vertex map (`work/female-parallel-limbs/data/HeroBase_Female_limbs_vertex_map.npz`) and `work/female-arms-form2/export/merge_arms_delta.py`, as documented in the arms README, then A. Check the ArtDir SHA is still `200dc3b9...` (or re-lineage) before writing.

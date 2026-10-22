# Phase3 opt-in masonry batching

Production change: only an appended `merge_static_masonry` function in hole09_masonry.py. All original constructors, stone generation calls and defaults remain unchanged. Source and original-prefix SHA256 values are in source_sha.json. No shared library, PNG, design, verifier, Unity source or installed asset was edited.

```python
ruin_batch = HM.merge_static_masonry(D, ruin_objs, max_faces=3000, max_span_m=12.0)
arch_batch = HM.merge_static_masonry(D, arch_objs, max_faces=3000, max_span_m=12.0)
ruin_objs = ruin_batch['objects']
arch_objs = arch_batch['objects']
```

The helper keeps ARCH/RUIN categories separate even when given both. Each new mesh holds whole disconnected stones, original n-gons, every loop UV layer, flat shading flags, edge seam/sharp flags and original material references. It never welds different stones or splits their rock tops into separate meshes. `pieces` records original object/component identity and exact target vertex/polygon ranges; face attribute h9_piece_id identifies components within each call. `replacements` maps old names to actual new object lists. Sources are removed only after packing and geometry creation succeed; the caller must replace its own lists.

World bounds use the full3D AABB diagonal<=12m, not just plan width. Every batch keeps LK_MASONRY>=50% and LK_ROCK<=36% by measured world area. Default max_faces490 is conservative. A3000-face cap is legitimate for genuine masonry: postcard_look_verify.g_prop_budget covers PLANT_/loose ROCK names, and hole09_qa.group_of/g_budget classify these as masonry rather than plant/rock/stack. The unchanged whole-hole250000-triangle and20MB FBX limits still apply.

Custom-normal meshes remain unchanged. Two float setter attempts changed decoded split normals by6.4075e-7, so that idea was stopped and documented in v3/DECISIONS.md. The final architecture retains opaque custom data exactly; it does not reduce those meshes' renderer count. Their existing face/span/material bounds are checked before returning them. The final custom-normal control reports exact delta0 with two original meshes retained. This is not a relaxed tolerance.

Meshes with children, modifiers, constraints, shape keys or color attributes are rejected before source mutation. Sources must share a parent and UV-layer set and use the permitted masonry materials. This helper is scoped to static DRESS_RUIN/ARCH masonry; it does not batch plants or loose rocks.

## Measured fixture

The actual source is v3/lib/masonry/after/fixture.blend. All286 whole stones remain present:6446 vertices,3795 n-gons and11748 triangles before/after. Every polygon's world coordinates, loop UVs, material identity, smooth flag and edge seam/sharp flag compares exactly; corner-normal maximum difference is0. The inherited masonry_blocks count remains269 (it counts eligible connected masonry-face patches, not all physical stones).

| Batch cap | Renderer count | Ruin / arch | Maximum span | Maximum rock share |
|---|---|---|---|---|
|490|14 to11|10 to8 /4 to3|11.999007m|35.4900%|
|3000|14 to7|10 to6 /4 to1|11.999309m|31.8872%|

These are renderer counts. Native Game render batches remain a separate measurement.

The unchanged ruin_check passes13/13 and independent cuboid census passes0/286 on both blend and FBX at each cap. Exact signed thresholds and classifier controls remain unchanged. final_fixture.log records the final source's preservation checks and exact custom-normal control; final_qa.log/qa_results.json record the final original gate runs. Positive FBX exports use export_look_fbx(LINEAR).

## Preserved failed attempts

- fixture_attempt1.log: material-naive packing exhausted companions and left a71% rock tail; stopped before source mutation. The next allocator reserves enough actual masonry area for remaining stones.
- qa_attempt1.log: blend13/13 PASS; exported fixture omitted neutral support ground because it was outside an exportable collection. FBX support/burial checks failed and arch measurement raised an exception. Only the scratch support ground's collection was corrected; masonry geometry and gate thresholds were unchanged.
- custom_normals_attempt1.log/attempt2.log: both exact-zero controls FAIL at6.4075e-7. No third float setter attempt was made; custom source data now stays on its original mesh.

All generated Blender/FBX fixtures, optional meta files and logs remain under this v3 directory. No full-hole build, Unity run or installation was performed by this subtask.

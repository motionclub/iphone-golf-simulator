"""merge_full_delta.py - hands base  ->  FEMALE FULL staged body (torso FORM5 + head MicroF3 on the arms+hands base).

    blender -b <HeroBase_Female_hands_candidate.blend> --python merge_full_delta.py -- <full_merge_delta.npz> <HeroBase_Female_MicroF3_head_STAGED.blend> <out.blend> [report.json]

Needs: the hands base blend (SHA in the delta), this delta, and the F3 head blend (SHA in the delta; only its Face_F object + materials are read from it).
Nothing outside the three steps below is touched (hands, arms, legs, Hair_F, plates, lights, UVs of retained faces, material indices of retained faces, custom-normal raw codes of retained loops
except the FORM5 rescale, all bit-kept).

  1 RETIRE   chat 7's superseded torso: its 3,317 vertices must sit exactly at chat 7's positions in the base (bit-exact guard) and are set back to the ArtDir original.
  2 TORSO    FORM5 delta in base order: every vertex must now sit at the delta start position (0 conflicts guard); positions set; authored custom-normal code0 scaled by (1-w) on the corners of the
             weighted vertices (same arithmetic as merge_torso_delta.py: int32 raw * (1 - w[loop vertex]) rounded; code1 untouched).  Writes NOTHING to the 828 appended hand vertices (guard).
  3 HEAD     zone graft: faces that touch the old head (base vertices above the collar ring) are removed together with those vertices; F3's head-zone faces (and its 9,359 head vertices, UVs,
             raw custom normals, materials, 21 LOOP_* vertex groups) are added and welded to the 30 collar-ring vertices that already exist in the base (exact positions).  Body_F keeps the
             base's vertex order for retained vertices (new index = old index minus removed vertices below it); F3's head vertices are appended in F3 order.  Face_F (F3's face paint object + its
             materials) is appended unchanged from the F3 blend.
Never clears or recomputes custom normals; raw INT16 codes are copied."""
import bpy, sys, json, hashlib, numpy as np

argv = sys.argv[sys.argv.index('--') + 1:]
delta_path, f3_path, out_path = argv[:3]
report_path = argv[3] if len(argv) > 3 else None


def sha256(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for ch in iter(lambda: f.read(1 << 20), b''):
            h.update(ch)
    return h.hexdigest()


D = np.load(delta_path)
rep = {}
# ------------------------------------------------------------------ guards
base_sha = sha256(bpy.data.filepath)
assert base_sha == str(D['base_sha256']), f"base blend SHA differs: {base_sha} vs {D['base_sha256']}"
assert sha256(f3_path) == str(D['f3_sha256']), 'F3 blend SHA differs'
rep['base_sha256'] = base_sha; rep['f3_sha256'] = str(D['f3_sha256']); rep['form5_delta_sha256'] = str(D['form5_delta_sha256'])
o = bpy.data.objects['Body_F']; src = o.data
n = len(src.vertices); assert n == int(D['base_vertex_count']) == 23247
nl = len(src.loops); nf = len(src.polygons)
V = np.empty(n * 3, np.float32); src.vertices.foreach_get('co', V); V = V.reshape(-1, 3)
cv = np.empty(nl, np.int32); src.loops.foreach_get('vertex_index', cv)
ls = np.empty(nf, np.int32); src.polygons.foreach_get('loop_start', ls)
lt = np.empty(nf, np.int32); src.polygons.foreach_get('loop_total', lt)
assert ls[0] == 0 and (np.diff(ls) == lt[:-1]).all(), 'loops are not contiguous in face order'
mat = np.empty(nf, np.int32); src.polygons.foreach_get('material_index', mat)
smooth = np.empty(nf, bool); src.polygons.foreach_get('use_smooth', smooth); assert smooth.all()
uv = np.empty(nl * 2, np.float32); src.uv_layers[0].data.foreach_get('uv', uv); uv = uv.reshape(-1, 2)
raw = np.empty(nl * 2, np.int32); src.attributes['custom_normal'].data.foreach_get('value', raw); raw = raw.reshape(-1, 2)
assert [m.name for m in src.materials][:2] == ['Base_Grey_F', 'Skin_F']
V0 = V.copy()

# ------------------------------------------------------------------ 1 RETIRE chat 7
c7 = D['c7_idx'].astype(np.int64)
assert (V[c7] == D['c7_co_in_base']).all(), 'base is not at chat-7 positions (guard)'
V[c7] = D['c7_co_original']
rep['retire_c7_verts'] = int(len(c7))

# ------------------------------------------------------------------ 2 TORSO FORM5
t = D['t_idx'].astype(np.int64)
assert t.max() < 22419, 'delta would write an appended hand vertex'
assert (V[t] == D['t_start']).all(), 'conflict: a delta vertex is not at its start position'
V[t] = D['t_new']
wt = D['cn_weight']
scaled = raw.copy(); scaled[:, 0] = np.round(raw[:, 0] * (1.0 - wt[cv])).astype(np.int32)
rep['torso_verts_applied'] = int(len(t)); rep['torso_conflicts'] = 0
rep['custom_normal_corners_rescaled'] = int((scaled != raw).any(1).sum())
raw = scaled
assert (np.abs(raw) < 32768).all()

# ------------------------------------------------------------------ 3 HEAD graft
old = D['old_head_idx'].astype(np.int64)
keep_v = np.ones(n, bool); keep_v[old] = False
assert np.array_equal(np.sort(old), old) and (V[old, 2] > float(D['cut_z'])).all() and (V[keep_v, 2] < float(D['cut_z'])).all()
newidx = np.cumsum(keep_v) - 1
nkeep = int(keep_v.sum())
face_old = np.add.reduceat((~keep_v[cv]).astype(np.int64), ls) > 0
keep_f = ~face_old
lmask = np.repeat(keep_f, lt)
ring_found = np.unique(cv[(~lmask) & keep_v[cv]])
ring_base = D['ring_base_idx'].astype(np.int64)
assert set(ring_found.tolist()) == set(ring_base.tolist()) and len(ring_base) == 30, 'open boundary of the lower body is not the 30-vertex collar ring'
assert (V[ring_base] == D['ring_pos']).all(), 'collar ring positions differ from F3 ring positions'
assert keep_v[cv[lmask]].all()
ref = D['head_corner_ref'].astype(np.int64)
fin = np.empty(len(ref), np.int64)
pos_m = ref >= 0
fin[pos_m] = nkeep + ref[pos_m]
fin[~pos_m] = newidx[ring_base[-ref[~pos_m] - 1]]
head_V = D['head_V']
V_final = np.concatenate([V[keep_v], head_V], 0)
cv_final = np.concatenate([newidx[cv[lmask]], fin]).astype(np.int32)
lt_final = np.concatenate([lt[keep_f], D['head_loop_total']]).astype(np.int32)
ls_final = np.concatenate([[0], np.cumsum(lt_final)[:-1]]).astype(np.int32)
assert (np.diff(D['head_loop_start']) == D['head_loop_total'][:-1]).all()
assert set(np.unique(mat[keep_f]).tolist()) <= {0, 1}, 'retained faces use a head-only material'
mat_final = np.concatenate([mat[keep_f], D['head_face_mat'].astype(np.int32)]).astype(np.int32)
uv_final = np.concatenate([uv[lmask], D['head_uv']], 0).astype(np.float32)
raw_final = np.concatenate([raw[lmask], D['head_cn_raw'].astype(np.int32)], 0).astype(np.int32)
nv, nL, nF = len(V_final), len(cv_final), len(lt_final)
rep.update(orphan_F3_vertices_not_carried=int(len(D['orphans_dropped_f3_idx'])), removed_vertices=int(len(old)), removed_faces=int(face_old.sum()), retained_vertices=nkeep, head_vertices_added=int(len(head_V)),
           head_faces_added=int(len(D['head_loop_total'])), final_vertices=nv, final_faces=nF, final_loops=nL, final_tris=int((lt_final - 2).sum()))

# ------------------------------------------------------------------ build the new Body_F mesh
new = bpy.data.meshes.new('Body_F_FULL')
new.vertices.add(nv); new.vertices.foreach_set('co', V_final.ravel())
new.loops.add(nL); new.loops.foreach_set('vertex_index', cv_final)
new.polygons.add(nF); new.polygons.foreach_set('loop_start', ls_final); new.polygons.foreach_set('loop_total', lt_final)
new.update(calc_edges=True)
new.polygons.foreach_set('use_smooth', np.ones(nF, bool)); new.polygons.foreach_set('material_index', mat_final)
new.uv_layers.new(name='UVMap').data.foreach_set('uv', uv_final.ravel())
a = new.attributes.new('custom_normal', 'INT16_2D', 'CORNER'); a.data.foreach_set('value', raw_final.ravel())
new.materials.append(bpy.data.materials['Base_Grey_F']); new.materials.append(bpy.data.materials['Skin_F'])
new.update()
assert new.validate(verbose=True) is False, 'mesh validation changed something'
old_mesh = o.data
o.data = new
bpy.data.meshes.remove(old_mesh)
new.name = 'Body_F'
# vertex groups (F3's 21 LOOP_* landmark loops, indices re-based to the final head vertex block)
names = [str(x) for x in D['vg_names']]; off = D['vg_offsets']
for g, name in enumerate(names):
    vg = o.vertex_groups.new(name=name)
    idx = D['vg_head_local_idx'][off[g]:off[g + 1]] + nkeep; w = D['vg_weights'][off[g]:off[g + 1]]
    for wv in np.unique(w):
        vg.add([int(i) for i in idx[w == wv]], float(wv), 'REPLACE')
rep['vertex_groups'] = len(names)

# ------------------------------------------------------------------ Face_F appended unchanged from the F3 blend
with bpy.data.libraries.load(f3_path, link=False) as (data_from, data_to):
    data_to.objects = ['Face_F']
face = data_to.objects[0]
coll = o.users_collection[0] if o.users_collection else bpy.context.scene.collection
coll.objects.link(face)
rep['Face_F'] = {'verts': len(face.data.vertices), 'tris': int(sum(len(p.vertices) - 2 for p in face.data.polygons)), 'materials': [m.name for m in face.data.materials]}
bpy.ops.wm.save_as_mainfile(filepath=out_path, copy=False)
rep['saved'] = out_path
print('FULL_MERGE_REPORT', json.dumps(rep))
if report_path:
    json.dump(rep, open(report_path, 'w'), indent=1)

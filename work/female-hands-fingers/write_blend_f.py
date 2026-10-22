"""Write a hand candidate into a copy of the start blend with bmesh (keeps UV / material / custom-normal data of every untouched loop bit-for-bit).
blender -b start.blend --python write_blend_f.py -- <cand.npz> <out.blend>

The candidate is Mesh(V, polys): polys = kept original polygons (original order) + new hand polygons; vertex indices < N0 never change meaning
(the freed hand-shell slots are reused for new hand vertices, extra vertices are appended).
Protocol for custom normals (same as work/female-parallel-limbs/make_limbs.py): loops at vertices that changed (position) or share a face with
a changed / new vertex get the smooth vertex normal; every other loop keeps its stored raw INT16 data exactly.
New hand faces: material Base_Grey_F, smooth, all corner UVs on the flat grey patch (0.93, 0.10) of the albedo atlas (same as the limbs hands)."""
import bpy, bmesh, sys, numpy as np, json
a = sys.argv[sys.argv.index('--') + 1:]
cand, out = a[0], a[1]
HAND_UV = (0.93, 0.10)
D = np.load(cand); V = D['V'].astype(np.float32); cv = D['corner_verts']; ls = D['loop_start']; lt = D['loop_total']
removed = D['removed_faces']
polys = [tuple(int(x) for x in cv[s:s + t]) for s, t in zip(ls, lt)]
o = bpy.data.objects['Body_F']; me = o.data
mat_idx = {m.name: i for i, m in enumerate(me.materials)}
n0 = len(me.vertices); f0 = len(me.polygons)
V_start = np.zeros(n0 * 3, np.float32); me.vertices.foreach_get('co', V_start); V_start = V_start.reshape(-1, 3)
bm = bmesh.new(); bm.from_mesh(me)
bm.verts.ensure_lookup_table(); bm.faces.ensure_lookup_table()
assert len(bm.faces) == f0
uvl = bm.loops.layers.uv.verify()
# --- delete the old hand shell faces (vertices are kept: they are reused as slots)
rem_faces = [bm.faces[int(i)] for i in removed]
rem_edges = set()
for f in rem_faces:
    for e in f.edges: rem_edges.add(e)
bmesh.ops.delete(bm, geom=rem_faces, context='FACES_ONLY')
for e in [e for e in rem_edges if e.is_valid and len(e.link_faces) == 0]:
    bm.edges.remove(e)
bm.verts.ensure_lookup_table()
assert len(bm.verts) == n0
changed_slot = np.zeros(n0, bool)
for i in range(n0):
    c = bm.verts[i].co
    if (c.x != V[i, 0]) or (c.y != V[i, 1]) or (c.z != V[i, 2]):
        bm.verts[i].co = (float(V[i, 0]), float(V[i, 1]), float(V[i, 2])); changed_slot[i] = True
for i in range(n0, len(V)):
    bm.verts.new((float(V[i, 0]), float(V[i, 1]), float(V[i, 2])))
bm.verts.ensure_lookup_table()
nkept = f0 - len(removed)
new_polys = polys[nkept:]
for p in new_polys:
    f = bm.faces.new([bm.verts[i] for i in p])
    f.smooth = True; f.material_index = mat_idx['Base_Grey_F']
    for l in f.loops: l[uvl].uv = HAND_UV
    for e in f.edges: e.smooth = True
bm.faces.ensure_lookup_table()
assert len(bm.faces) == len(polys), (len(bm.faces), len(polys))
bm.normal_update()
bm.to_mesh(me); bm.free(); me.update()
# ------------------------------------------------------------------ custom normals
nvf = len(me.vertices)
changed = np.zeros(nvf, bool); changed[:n0] = changed_slot; changed[n0:] = True
affected = changed.copy()
for p in me.polygons:
    vs = list(p.vertices)
    if changed[vs].any(): affected[vs] = True
lv = np.array([l.vertex_index for l in me.loops])
raw_before = np.empty(len(me.loops) * 2, np.int16); me.attributes['custom_normal'].data.foreach_get('value', raw_before)
vn = np.array([tuple(v.normal) for v in me.vertices], np.float32)
cn = np.array([tuple(n.vector) for n in me.corner_normals], np.float32)
selL = affected[lv]; cn[selL] = vn[lv[selL]]
me.normals_split_custom_set([tuple(x) for x in cn]); me.update()
raw_after = np.empty(len(me.loops) * 2, np.int16); me.attributes['custom_normal'].data.foreach_get('value', raw_after)
keep = ~np.repeat(selL, 2)
raw_after[keep] = raw_before[keep]
me.attributes['custom_normal'].data.foreach_set('value', raw_after); me.update()
print('WROTE verts', len(me.vertices), 'polys', len(me.polygons), 'loops', len(me.loops), 'tris', sum(len(p.vertices) - 2 for p in me.polygons),
      'affected verts', int(affected.sum()), 'recomputed loops', int(selL.sum()), 'kept raw loops', int((~selL).sum()))
bpy.ops.wm.save_as_mainfile(filepath=out, copy=False)

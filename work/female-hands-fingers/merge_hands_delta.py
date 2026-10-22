"""merge_hands_delta.py - apply the female hands delta onto a Body_F blend that has the LIMBS vertex order (22,419 verts) and the limbs SDF hands.
    blender -b <target.blend> --python merge_hands_delta.py -- <hands_delta.npz> <out.blend>

What it does (same protocol as write_blend_f.py):
  1. guard: the 36 wrist-ring vertices and the 1,326 hand-shell slot vertices of the target must be where the delta expects them (ring bit-identical;
     slot positions equal to the recorded start positions) - otherwise it STOPS (another chat moved the wrist: rebuild with build_hands_on_base.py instead);
  2. deletes every face that touches a hand-shell slot vertex (= the old SDF hand faces), keeps all vertices (slots are reused);
  3. sets the slot positions, appends the extra vertices, creates the new hand faces (Base_Grey_F, smooth, UV on the flat grey patch (0.93, 0.10));
  4. custom normals: loops at changed / new vertices and their face neighbours get the smooth vertex normal, every other loop keeps its raw INT16 data.
Nothing outside the two hand shells is touched; vertex indices < 22,419 keep their meaning."""
import bpy, bmesh, sys, numpy as np, json
a = sys.argv[sys.argv.index('--') + 1:]
D = np.load(a[0]); out = a[1]
HAND_UV = (0.93, 0.10)
o = bpy.data.objects['Body_F']; me = o.data
n0 = len(me.vertices); assert n0 == int(D['n_base']), ('target is not in the limbs vertex order', n0)
V_start = np.zeros(n0 * 3, np.float32); me.vertices.foreach_get('co', V_start); V_start = V_start.reshape(-1, 3)
slots = D['slots'].astype(np.int64); ring = D['ring'].astype(np.int64)
# ---- guard
assert np.array_equal(V_start[ring], D['ring_pos_start']), 'wrist ring moved in the target: rebuild the hands on it instead (build_hands_on_base.py)'
assert np.array_equal(V_start[slots], D['slot_pos_start']), 'hand shell of the target differs from the recorded start'
mat_idx = {m.name: i for i, m in enumerate(me.materials)}
bm = bmesh.new(); bm.from_mesh(me); bm.verts.ensure_lookup_table(); bm.faces.ensure_lookup_table()
uvl = bm.loops.layers.uv.verify()
slot_set = set(int(i) for i in slots)
rem_faces = [f for f in bm.faces if any(v.index in slot_set for v in f.verts)]
rem_edges = set(e for f in rem_faces for e in f.edges)
bmesh.ops.delete(bm, geom=rem_faces, context='FACES_ONLY')
for e in [e for e in rem_edges if e.is_valid and len(e.link_faces) == 0]: bm.edges.remove(e)
bm.verts.ensure_lookup_table(); assert len(bm.verts) == n0
changed_slot = np.zeros(n0, bool)
for k, i in enumerate(slots):
    p = D['slot_pos'][k]; c = bm.verts[int(i)].co
    if (c.x != p[0]) or (c.y != p[1]) or (c.z != p[2]):
        bm.verts[int(i)].co = (float(p[0]), float(p[1]), float(p[2])); changed_slot[int(i)] = True
for p in D['appended_pos']: bm.verts.new((float(p[0]), float(p[1]), float(p[2])))
bm.verts.ensure_lookup_table()
cv, ls, lt = D['new_corner_verts'], D['new_loop_start'], D['new_loop_total']
for s, t in zip(ls, lt):
    f = bm.faces.new([bm.verts[int(i)] for i in cv[s:s + t]])
    f.smooth = True; f.material_index = mat_idx['Base_Grey_F']
    for l in f.loops: l[uvl].uv = HAND_UV
    for e in f.edges: e.smooth = True
bm.normal_update(); bm.to_mesh(me); bm.free(); me.update()
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
keep = ~np.repeat(selL, 2); raw_after[keep] = raw_before[keep]
me.attributes['custom_normal'].data.foreach_set('value', raw_after); me.update()
print('MERGED verts', len(me.vertices), 'polys', len(me.polygons), 'tris', sum(len(p.vertices) - 2 for p in me.polygons), 'faces removed', len(rem_faces), 'new faces', len(ls))
bpy.ops.wm.save_as_mainfile(filepath=out, copy=False)

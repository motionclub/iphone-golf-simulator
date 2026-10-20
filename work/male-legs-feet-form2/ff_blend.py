"""blender -b --factory-startup --python ff_blend.py -- <in.blend> <V.npy> <F.pkl> <out.blend>
Replace Body_M geometry with the assembled arrays.  Keeps: material, smooth shading, vertex-group weights (old vertex indices are unchanged),
and the raw 'custom_normal' INT16_2D corner attribute for every kept (unchanged) face; new faces get raw (0,0) = plain smooth normal."""
import sys, pickle, hashlib, numpy as np, bpy
src, vp, fp, out = sys.argv[sys.argv.index('--') + 1:][:4]
bpy.ops.wm.open_mainfile(filepath=src)
ob = bpy.data.objects['Body_M']; me = ob.data
n_old = len(me.vertices)
# --- snapshot
raw_old = np.zeros(len(me.loops) * 2, np.int32)
me.attributes['custom_normal'].data.foreach_get('value', raw_old)
raw_old = raw_old.reshape(-1, 2)
loop_start = np.array([p.loop_start for p in me.polygons]); loop_total = np.array([p.loop_total for p in me.polygons])
mats = [m for m in me.materials]
groups = {}
for v in me.vertices:
    for g in v.groups:
        groups.setdefault(g.group, []).append((v.index, g.weight))
vgnames = {vg.index: vg.name for vg in ob.vertex_groups}
vg_order = [vg.name for vg in sorted(ob.vertex_groups, key=lambda g: g.index)]
vg_lock = {vg.name: vg.lock_weight for vg in ob.vertex_groups}
V = np.load(vp)
D = pickle.load(open(fp, 'rb'))
faces = D['faces']; kept_idx = D['kept_idx']
assert len(kept_idx) <= len(loop_start)
# freed vertices must not carry group weights
vg_members = set(v for lst in groups.values() for v, w in lst)
# --- rebuild
me.clear_geometry()
me.from_pydata([tuple(v) for v in V.tolist()], [], [tuple(int(i) for i in f) for f in faces])
me.polygons.foreach_set('use_smooth', [True] * len(me.polygons))
for m in mats:
    if m not in list(me.materials): me.materials.append(m)
me.update()
bad = me.validate(verbose=True)
# --- vertex groups (clear_geometry drops the group list as well)
if [vg.name for vg in ob.vertex_groups] != vg_order:
    for vg in list(ob.vertex_groups): ob.vertex_groups.remove(vg)
    for nm in vg_order:
        g_ = ob.vertex_groups.new(name=nm); g_.lock_weight = vg_lock[nm]
for gi, lst in groups.items():
    vg = ob.vertex_groups[vgnames[gi]]
    for vi, w in lst:
        if vi < len(me.vertices):
            vg.add([vi], w, 'REPLACE')
# --- custom normals: kept faces copy raw, new faces zeros
raw_new = np.zeros((len(me.loops), 2), np.int32)
new_start = np.array([p.loop_start for p in me.polygons]); new_total = np.array([p.loop_total for p in me.polygons])
assert len(me.polygons) == len(faces)
for k, fi in enumerate(kept_idx):
    s_old, n_old_l = loop_start[fi], loop_total[fi]
    s_new, n_new_l = new_start[k], new_total[k]
    assert n_old_l == n_new_l
    raw_new[s_new:s_new + n_new_l] = raw_old[s_old:s_old + n_old_l]
attr = me.attributes.new('custom_normal', 'INT16_2D', 'CORNER')
attr.data.foreach_set('value', raw_new.reshape(-1))
me.update()
print('has_custom_normals', me.has_custom_normals, 'verts', len(me.vertices), 'faces', len(me.polygons), 'loops', len(me.loops), 'validate_changed', bad)
tri = sum(p.loop_total - 2 for p in me.polygons)
print('tris', tri)
bpy.ops.wm.save_as_mainfile(filepath=out)
print('SAVED', out)

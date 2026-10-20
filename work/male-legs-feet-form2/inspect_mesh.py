"""Dump facts about Body_M in a blend: objects, attributes, UVs, groups, materials, vertex index layout of the feet."""
import sys, pickle, numpy as np, bpy
W = '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/male-legs-feet-form2'
src = sys.argv[sys.argv.index('--') + 1]
bpy.ops.wm.open_mainfile(filepath=src)
for o in bpy.data.objects:
    print('OBJ', o.name, o.type, [round(x, 3) for x in o.location], o.parent.name if o.parent else None,
          len(o.data.vertices) if o.type == 'MESH' else '', [m.type for m in o.modifiers])
b = bpy.data.objects['Body_M']; me = b.data
n = len(me.vertices)
print('verts', n, 'faces', len(me.polygons), 'loops', len(me.loops), 'edges', len(me.edges))
print('attributes', [(a.name, a.domain, a.data_type) for a in me.attributes])
print('uv_layers', [u.name for u in me.uv_layers])
print('materials', [m.name if m else None for m in me.materials])
print('vgroups', [vg.name for vg in b.vertex_groups])
print('has_custom_normals', me.has_custom_normals)
print('shape keys', me.shape_keys)
print('matrix_world', [list(r) for r in b.matrix_world])
V = np.empty(n * 3); me.vertices.foreach_get('co', V); V = V.reshape(-1, 3)
print('bbox', V.min(0), V.max(0))
F = [list(p.vertices) for p in me.polygons]
np.save(W + '/data/V_start.npy', V)
pickle.dump(F, open(W + '/data/F.pkl', 'wb'))
mat_idx = np.array([p.material_index for p in me.polygons])
print('material index counts', np.bincount(mat_idx))
sharp = np.array([p.use_smooth for p in me.polygons])
print('smooth faces', sharp.sum(), 'of', len(sharp))
# vertex index layout of feet
ZONE = (V[:, 2] < 0.765) & (np.abs(V[:, 0]) < 0.27)
print('zone verts', ZONE.sum())
foot = (V[:, 2] < 0.10) & (np.abs(V[:, 0]) < 0.27)
idx = np.where(foot)[0]
print('foot(z<0.10) verts', len(idx), 'index range', idx.min(), idx.max())
# contiguity of index runs for the zone / foot
def runs(ix):
    ix = np.sort(ix); br = np.where(np.diff(ix) > 1)[0]
    st = np.r_[ix[0], ix[br + 1]]; en = np.r_[ix[br], ix[-1]]
    return list(zip(st.tolist(), en.tolist()))
r = runs(np.where(ZONE)[0])
print('zone index runs', len(r), r[:20])
r = runs(idx)
print('foot index runs', len(r), r[:20])
# vertex groups membership on foot
for vg in b.vertex_groups:
    cnt = 0
    for v in me.vertices:
        pass
# UV island info
if me.uv_layers:
    uv = me.uv_layers.active.data
    uvs = np.empty(len(me.loops) * 2); uv.foreach_get('uv', uvs); uvs = uvs.reshape(-1, 2)
    print('uv bbox', uvs.min(0), uvs.max(0))
# edge length stats in foot region
E = set()
for p in F:
    for k in range(len(p)):
        a, c = p[k], p[(k + 1) % len(p)]
        E.add((min(a, c), max(a, c)))
E = np.array(sorted(E))
for zlo, zhi in [(0, 0.03), (0.03, 0.06), (0.06, 0.10), (0.10, 0.2), (0.2, 0.4), (0.4, 0.765)]:
    m = (V[E[:, 0], 2] >= zlo) & (V[E[:, 0], 2] < zhi) & (np.abs(V[E[:, 0], 0]) < 0.27)
    l = np.linalg.norm(V[E[m, 0]] - V[E[m, 1]], axis=1)
    print(f'edges z[{zlo},{zhi}) n={m.sum()} mean={l.mean()*1000:.2f}mm med={np.median(l)*1000:.2f} p10={np.percentile(l,10)*1000:.2f} p90={np.percentile(l,90)*1000:.2f} max={l.max()*1000:.2f}')
# toe-region edges: y < min y + 0.08
toe = (V[:, 2] < 0.05) & (np.abs(V[:, 0]) < 0.27) & (V[:, 1] < -0.10)
print('y range foot', V[foot, 1].min(), V[foot, 1].max(), 'x range', V[foot, 0].min(), V[foot, 0].max())

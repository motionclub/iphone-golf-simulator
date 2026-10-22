"""blender -b --factory-startup --python check_normals.py -- <base.blend> <new.blend>
Compare the DECODED corner normals of every unchanged face (same vertex ids, vertices not moved) and report sharp edge/face attribute counts."""
import sys, numpy as np, bpy
base, new = sys.argv[sys.argv.index('--') + 1:][:2]
def load(path):
    bpy.ops.wm.open_mainfile(filepath=path)
    me = bpy.data.objects['Body_M'].data
    me.update()                      # fresh decode on both sides (the cached normals of a loaded file differ from a recompute by up to 0.05 deg)
    n = len(me.vertices)
    V = np.empty(n * 3); me.vertices.foreach_get('co', V); V = V.reshape(-1, 3).astype(np.float32)
    F = [tuple(p.vertices) for p in me.polygons]
    cn = np.empty(len(me.loops) * 3); me.corner_normals.foreach_get('vector', cn); cn = cn.reshape(-1, 3)
    ls = np.array([p.loop_start for p in me.polygons]); lt = np.array([p.loop_total for p in me.polygons])
    se = me.attributes.get('sharp_edge'); sf = me.attributes.get('sharp_face')
    nse = int(sum(1 for d in se.data if d.value)) if se else None
    nsf = int(sum(1 for d in sf.data if d.value)) if sf else None
    return V, F, cn, ls, lt, nse, nsf, me.has_custom_normals
Vb, Fb, cnb, lsb, ltb, nseb, nsfb, hcb = load(base)
Vn, Fn, cnn, lsn, ltn, nsen, nsfn, hcn = load(new)
print('sharp_edge count base/new', nseb, nsen, '| sharp_face count base/new', nsfb, nsfn, '| has_custom_normals', hcb, hcn)
oldmap = {tuple(f): i for i, f in enumerate(Fb)}
moved = np.any(Vb != Vn[:len(Vb)], axis=1)
worst = 0.0; n_cmp = 0; n_far = 0; worst_far = 0.0; far_bad = 0
for k, f in enumerate(Fn):
    i = oldmap.get(f)
    if i is None: continue
    a = cnb[lsb[i]:lsb[i] + ltb[i]]; b = cnn[lsn[k]:lsn[k] + ltn[k]]
    ang = np.degrees(np.arccos(np.clip((a * b).sum(1), -1, 1)))
    n_cmp += len(ang); worst = max(worst, float(ang.max()))
    if not any(moved[v] for v in f):
        n_far += len(ang); worst_far = max(worst_far, float(ang.max())); far_bad += int((ang > 0.01).sum())
print(f'unchanged faces: corners compared {n_cmp}, worst decoded-normal difference {worst:.4f} deg; faces with NO moved vertex: corners {n_far}, worst {worst_far:.5f} deg, corners >0.01 deg: {far_bad}')

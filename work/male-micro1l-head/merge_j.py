"""Apply the Micro1j head/neck displacement D (by vertex index, relative to the START blend 68de53ca) onto ANY base blend whose Body_M is identical to START
in the zone (z_start >= 1.40) and wherever D != 0; rotates the base blend's own stored custom normals around the edit.
blender -b --factory-startup --python merge_j.py -- <base.blend> <D.npy> <out.blend> [start_V.npy]
Fails (exit 1) if the base differs from START at any vertex with z_start >= 1.40."""
import sys, json
import numpy as np
import bpy
W = '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/male-micro1l-head'
argv = sys.argv[sys.argv.index('--') + 1:]
base, dpath, out = argv[0], argv[1], argv[2]
V_start = np.load(argv[3] if len(argv) > 3 else W + '/data/V_start.npy')
D = np.load(dpath)
bpy.ops.wm.open_mainfile(filepath=base)
body = bpy.data.objects['Body_M']; me = body.data; n = len(me.vertices)
assert n == len(D) == len(V_start), 'vertex count mismatch'
Vb = np.empty(n * 3, np.float32); me.vertices.foreach_get('co', Vb); Vb = Vb.reshape(-1, 3)
zone = V_start[:, 2] >= 1.40; hasD = np.linalg.norm(D, axis=1) > 0
diff = np.any(Vb != V_start.astype(np.float32), axis=1)
bad = diff & (zone | hasD)
if bad.any():
    print('MERGE_CONFLICT', int(bad.sum()), 'base differs from START inside the head/neck zone or under D'); sys.exit(1)
print('MERGE_CHECK base differs from START at %d verts, none in zone/under D' % int(diff.sum()))
F = [list(p.vertices) for p in me.polygons]


def vertex_normals(V, F):
    nrm = np.zeros_like(V)
    for f in F:
        a = V[f[0]]; fn = np.zeros(3)
        for k in range(1, len(f) - 1): fn += np.cross(V[f[k]] - a, V[f[k + 1]] - a)
        for i in f: nrm[i] += fn
    return nrm / np.maximum(np.linalg.norm(nrm, axis=1, keepdims=True), 1e-12)


def rotate_normals(stored, G0, G1):
    out = stored.copy(); c = np.clip((G0 * G1).sum(1), -1, 1); ang = np.arccos(c); ax = np.cross(G0, G1); an = np.linalg.norm(ax, axis=1)
    sel = np.where((an > 1e-9) & (ang > 1e-9))[0]
    k = ax[sel] / an[sel, None]; v = stored[sel]; a = ang[sel, None]
    out[sel] = v * np.cos(a) + np.cross(k, v) * np.sin(a) + k * (k * v).sum(1, keepdims=True) * (1 - np.cos(a))
    return out / np.maximum(np.linalg.norm(out, axis=1, keepdims=True), 1e-12)


# stored vertex normals of the base (all corners of a vertex agree within 0.03 deg)
cn = np.empty(len(me.loops) * 3, np.float32); me.corner_normals.foreach_get('vector', cn); cn = cn.reshape(-1, 3)
lv = np.empty(len(me.loops), np.int64); me.loops.foreach_get('vertex_index', lv)
s = np.zeros((n, 3)); np.add.at(s, lv, cn); stored = s / np.maximum(np.bincount(lv, minlength=n), 1)[:, None]; stored /= np.maximum(np.linalg.norm(stored, axis=1, keepdims=True), 1e-12)
Vb64 = Vb.astype(np.float64); Vn64 = Vb64 + D
Vn = Vn64.astype(np.float32)
G0 = vertex_normals(Vb64, F); G1 = vertex_normals(Vn.astype(np.float64), F)
Nn = rotate_normals(stored, G0, G1)
me.vertices.foreach_set('co', Vn.ravel()); me.update()
me.normals_split_custom_set_from_vertices([tuple(x) for x in Nn]); me.update()
bpy.ops.wm.save_as_mainfile(filepath=out)
moved = np.any(Vn != Vb, axis=1)
print('MERGE_DONE', json.dumps(dict(out=out, moved=int(moved.sum()), max_move_mm=float(np.linalg.norm(Vn64 - Vb64, axis=1).max() * 1000))))

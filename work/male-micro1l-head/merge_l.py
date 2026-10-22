"""Apply the Micro1l head/neck/lip delta onto ANY base blend whose Body_M is identical to the START blend (9bfd788a) in the head zone (start z >= 1.40) and wherever D != 0.
Positions: V_new = V_base + D (vertex-index patch).  Custom normals: base stored vertex normals rotated by the geometric change (Rodrigues, like merge_j) + the Micro1l shading boost dN (= N_final - N_rot of the start state).
Face_M is NOT touched here (facem_lips.py rebuilds the lip + seam paint strips afterwards).
blender -b --factory-startup --python merge_l.py -- <base.blend> <out.blend> [tag=l2] [from_tag]
from_tag (optional): the base is an already-installed Micro1l state (e.g. `l2`) instead of the 9bfd788a start: the expected zone state is data/V_<from_tag>.npy, the delta is V_<tag> - V_<from_tag>,
and the shading boost dN is taken relative to the rotated installed normals N_<from_tag>.
Aborts (exit 1) if the base differs from the expected state at any vertex with z_start >= 1.40 or under D."""
import sys, json
import numpy as np
import bpy
W = '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/male-micro1l-head'
argv = sys.argv[sys.argv.index('--') + 1:]
base, out = argv[0], argv[1]; tag = argv[2] if len(argv) > 2 else 'l2'
from_tag = argv[3] if len(argv) > 3 else None
V_z0 = np.load(W + '/data/V_start.npy')                      # start z (zone definition) always the 9bfd788a positions
if from_tag is None:
    V_start = V_z0; D = np.load(W + f'/data/D_{tag}.npy'); Nrot_s = np.load(W + f'/data/Nrot_{tag}.npy')
else:
    V_start = np.load(W + f'/data/V_{from_tag}.npy'); D = np.load(W + f'/data/V_{tag}.npy') - V_start; Nrot_s = None
Nfin = np.load(W + f'/data/N_{tag}.npy')
bpy.ops.wm.open_mainfile(filepath=base)
body = bpy.data.objects['Body_M']; me = body.data; n = len(me.vertices)
assert n == len(D) == len(V_start), 'vertex count mismatch'
Vb = np.empty(n * 3, np.float32); me.vertices.foreach_get('co', Vb); Vb = Vb.reshape(-1, 3)
zone = V_z0[:, 2] >= 1.40; hasD = np.linalg.norm(D, axis=1) > 0
diff = np.any(np.abs(Vb.astype(np.float64) - V_start) > (1e-9 if from_tag is None else 2e-7), axis=1); bad = diff & (zone | hasD)
if bad.any():
    print('MERGE_CONFLICT', int(bad.sum()), 'base differs from START inside the head/neck zone or under D'); sys.exit(1)
print('MERGE_CHECK base differs from the expected state at %d verts, none in the head zone / under D' % int(diff.sum()))
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


cn = np.empty(len(me.loops) * 3, np.float32); me.corner_normals.foreach_get('vector', cn); cn = cn.reshape(-1, 3)
lv = np.empty(len(me.loops), np.int64); me.loops.foreach_get('vertex_index', lv)
s = np.zeros((n, 3)); np.add.at(s, lv, cn); stored = s / np.maximum(np.bincount(lv, minlength=n), 1)[:, None]; stored /= np.maximum(np.linalg.norm(stored, axis=1, keepdims=True), 1e-12)
Vb64 = Vb.astype(np.float64); Vn = (Vb64 + D).astype(np.float32)
G0 = vertex_normals(Vb64, F); G1 = vertex_normals(Vn.astype(np.float64), F)
Nrot = rotate_normals(stored, G0, G1)
if Nrot_s is None:
    Nfrom = np.load(W + f'/data/N_{from_tag}.npy'); Gf0 = vertex_normals(V_start, F); Gf1 = vertex_normals(V_start + D, F); Nrot_s = rotate_normals(Nfrom, Gf0, Gf1)
dN = Nfin - Nrot_s                                    # shading boost of the start state (0 outside the jaw band)
Nn = Nrot + dN; Nn /= np.maximum(np.linalg.norm(Nn, axis=1, keepdims=True), 1e-12)
me.vertices.foreach_set('co', Vn.ravel()); me.update()
me.normals_split_custom_set_from_vertices([tuple(x) for x in Nn]); me.update()
bpy.ops.wm.save_as_mainfile(filepath=out)
moved = np.any(Vn != Vb, axis=1)
print('MERGE_DONE', json.dumps(dict(out=out, moved=int(moved.sum()), max_move_mm=float(np.linalg.norm(Vn.astype(np.float64) - Vb64, axis=1).max() * 1000), normals_vs_final_max_deg=float(np.degrees(np.arccos(np.clip((Nn * Nfin).sum(1), -1, 1))).max()))))

"""Quality metrics (same definitions as the earlier legs chat, position-based): banding, normal roughness, plate-consensus edge deviation, kneecap relief, foot placement table."""
import sys, json, pickle
sys.path.insert(0, '.')
import numpy as np
from ff_common import *
from edges_ref import spans
from PIL import Image

def umbrella_aniso(M, V, axis=(0, 0, 1.0), p=2.0, eps=0.05):
    ax = np.asarray(axis, float)
    d = V[M.Ej] - V[M.Ei]
    l = np.maximum(np.linalg.norm(d, axis=1), 1e-12)
    a = (np.abs(d @ ax) / l) ** p
    acc = np.zeros_like(V); den = np.full(len(V), eps)
    np.add.at(acc, M.Ei, a[:, None] * (V[M.Ej] - V[M.Ei])); np.add.at(acc, M.Ej, a[:, None] * (V[M.Ei] - V[M.Ej]))
    np.add.at(den, M.Ei, a); np.add.at(den, M.Ej, a)
    return acc / den[:, None]

def banding(V, F, sel):
    M = Mesh(V, F); w = np.zeros(len(V)); w[sel] = 1
    S = V.copy()
    for _ in range(40):
        S += 0.5 * w[:, None] * umbrella_aniso(M, S)
        S += -0.53 * w[:, None] * umbrella_aniso(M, S)
    n = vertex_normals(V, F)
    d = ((S - V) * n).sum(1)
    return float(np.sqrt((d[sel] ** 2).mean()) * 1e6)

def roughness(V, F, sel):
    M = Mesh(V, F); w = np.zeros(len(V)); w[sel] = 1
    S = M.taubin(V, w, iters=25)
    n = vertex_normals(V, F)
    d = ((S - V) * n).sum(1)
    return float(np.sqrt((d[sel] ** 2).mean()) * 1e6)

def consensus_dev(V, side=+1):
    dx = []; dy = []
    for z in np.arange(0.18, 0.70, 0.02):
        ins = []; outs = []
        for v, w in (('bald_front', 2), ('sheet_front', 1), ('bald_back', 2), ('sheet_back', 1)):
            sp = [s for s in spans(v, z) if s[0] >= 0.0 and s[1] > 0.05]
            if sp: ins += [sp[0][0]] * w; outs += [sp[0][1]] * w
        s = (V[:, 0] > 0.0) & (np.abs(V[:, 2] - z) < 0.006) & (V[:, 0] < 0.30) & (V[:, 1] > -0.17)
        s2 = (V[:, 0] < 0.0) & (np.abs(V[:, 2] - z) < 0.006) & (V[:, 0] > -0.30) & (V[:, 1] > -0.17)
        if not s.any() or not s2.any() or not ins: continue
        mi = 0.5 * (V[s, 0].min() + (-V[s2, 0].max())); mo = 0.5 * (V[s, 0].max() + (-V[s2, 0].min()))
        dx += [abs(mi - np.mean(ins)), abs(mo - np.mean(outs))]
        yf = []; yb = []
        for v in ('left', 'right'):
            sp = spans(v, z); yf.append(sp[0][0]); yb.append(sp[-1][1])
        sy = s
        dy += [abs(V[sy, 1].min() - np.mean(yf)), abs(V[sy, 1].max() - np.mean(yb))]
    return dict(x_edge_mean_abs_mm=float(np.mean(dx) * 1000), y_edge_mean_abs_mm=float(np.mean(dy) * 1000))

def knee_relief(V):
    out = []
    for side in (1, -1):
        def fy(z):
            s = (side * V[:, 0] > 0) & (np.abs(V[:, 2] - z) < 0.006) & (np.abs(V[:, 0] - side * 0.136) < 0.02)
            return V[s, 1].min()
        out.append((np.mean([fy(0.47), fy(0.58)]) - fy(0.52)) * 1000)
    return float(np.mean(out))

def placement(V):
    rows = {}
    for z in (0.015, 0.025, 0.035, 0.045, 0.055):
        s = (np.abs(V[:, 2] - z) < 0.006) & (V[:, 0] > 0.10) & (V[:, 0] < 0.30) & (V[:, 1] > -0.26)
        pl = []; ph = []
        for v in ('left', 'right'):
            sp = spans(v, z); pl.append(sp[0][0] * 1000); ph.append(sp[-1][1] * 1000)
        rows[f'{z:.3f}'] = dict(mesh_toe=float(V[s, 1].min() * 1000), mesh_heel=float(V[s, 1].max() * 1000), plate_toe=float(np.mean(pl)), plate_heel=float(np.mean(ph)))
    return rows

def ankle(V):
    out = {}
    for z in (0.16, 0.19, 0.22):
        s = (np.abs(V[:, 2] - z) < 0.006) & (V[:, 0] > 0.10) & (V[:, 0] < 0.30)
        a = float(V[s, 1].min()); b = float(V[s, 1].max())
        pa = []; pb = []
        for v in ('left', 'right'):
            sp = spans(v, z); pa.append(sp[0][0]); pb.append(sp[-1][1])
        out[f'{z:.2f}'] = dict(mesh_centre_mm=0.5 * (a + b) * 1000, plate_centre_mm=0.5 * (np.mean(pa) + np.mean(pb)) * 1000)
    return out

if __name__ == '__main__':
    name = sys.argv[1]
    V0, F0 = load_base()
    V1 = np.load(f'tmp/V_{name}.npy'); F1 = pickle.load(open(f'tmp/F_{name}.pkl', 'rb'))['faces']
    n0 = len(V0)
    res = {}
    for tag, V, F in (('base', V0, F0), ('new', V1, F1)):
        sel = (np.abs(V[:, 0]) > 0.02) & (np.abs(V[:, 0]) < 0.27) & (V[:, 2] > 0.2) & (V[:, 2] < 0.7)
        sel[n0:] = False
        res[tag] = dict(banding_um=banding(V, F, sel), roughness_um=roughness(V, F, sel), consensus=consensus_dev(V), knee_relief_mm=knee_relief(V), placement=placement(V), ankle=ankle(V))
    json.dump(res, open(f'tmp/quality_{name}.json', 'w'), indent=1)
    for tag in ('base', 'new'):
        r = res[tag]
        print(tag, '| banding %.0f um  roughness %.0f um | edge dev x %.2f y %.2f mm | knee relief %.1f mm' % (r['banding_um'], r['roughness_um'], r['consensus']['x_edge_mean_abs_mm'], r['consensus']['y_edge_mean_abs_mm'], r['knee_relief_mm']))
    print('placement (mm)  z: plate toe/heel | base toe/heel | new toe/heel')
    for z in res['base']['placement']:
        p = res['base']['placement'][z]; q = res['new']['placement'][z]
        print(f"  {z}: {p['plate_toe']:7.1f}/{p['plate_heel']:5.1f} | {p['mesh_toe']:7.1f}/{p['mesh_heel']:5.1f} | {q['mesh_toe']:7.1f}/{q['mesh_heel']:5.1f}")
    print('ankle centre (mm): plate | base | new')
    for z in res['base']['ankle']:
        print(f"  z {z}: {res['base']['ankle'][z]['plate_centre_mm']:6.1f} | {res['base']['ankle'][z]['mesh_centre_mm']:6.1f} | {res['new']['ankle'][z]['mesh_centre_mm']:6.1f}")

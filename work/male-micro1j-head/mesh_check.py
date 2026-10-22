"""Mesh sanity of a variant vs START: flipped/folded faces, edge-length change, worst displacement gradient.  python3.13 mesh_check.py <tag>"""
import sys; sys.path.insert(0, '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/male-micro1j-head')
from j_edit import *
def face_normals(V, F):
    out = []
    for f in F:
        a = V[f[0]]; n = np.zeros(3)
        for k in range(1, len(f) - 1): n += np.cross(V[f[k]] - a, V[f[k + 1]] - a)
        l = np.linalg.norm(n); out.append(n / l if l > 0 else n)
    return np.array(out)
if __name__ == '__main__':
    tag = sys.argv[1]; ctx = Ctx(); V1 = np.load(W / f'data/V_{tag}.npy'); V0 = ctx.V0
    n0 = face_normals(V0, ctx.F); n1 = face_normals(V1, ctx.F)
    dot = (n0 * n1).sum(1)
    moved_f = np.array([np.any(np.linalg.norm(V1[f] - V0[f], axis=1) > 0) for f in ctx.F])
    ang = np.degrees(np.arccos(np.clip(dot, -1, 1)))
    print('faces with moved verts: %d | face-normal rotation: mean %.2f deg  max %.1f deg | flipped (dot<0.2): %d' % (moved_f.sum(), ang[moved_f].mean(), ang.max(), (dot < 0.2).sum()))
    for i in np.where(ang > 25)[0][:12]:
        c = V1[ctx.F[i]].mean(axis=0) * 1000; print('   face %d rotated %.1f deg at (%.0f,%.0f,%.0f) mm' % (i, ang[i], *c))
    E = ctx.E; l0 = np.linalg.norm(V0[E[:, 0]] - V0[E[:, 1]], axis=1); l1 = np.linalg.norm(V1[E[:, 0]] - V1[E[:, 1]], axis=1)
    mv = (l1 != l0); r = l1[mv] / np.maximum(l0[mv], 1e-9)
    print('edges changed: %d | length ratio min %.2f max %.2f | edges <0.8 mm now: %d' % (mv.sum(), r.min(), r.max(), (l1 < 0.0008).sum()))
    # displacement gradient: |dV(a)-dV(b)| / |V(a)-V(b)|  (>0.8 means local compression/stretch near folding)
    dV = V1 - V0; g = np.linalg.norm(dV[E[:, 0]] - dV[E[:, 1]], axis=1) / np.maximum(l0, 1e-9)
    print('displacement gradient: max %.2f, edges >0.5: %d' % (g.max(), (g > 0.5).sum()))
    for i in np.argsort(-g)[:5]:
        a, b = E[i]; c = 0.5 * (V0[a] + V0[b]) * 1000; print('   edge (%d,%d) grad %.2f at (%.0f,%.0f,%.0f)' % (a, b, g[i], *c))

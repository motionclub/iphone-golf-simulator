"""analytic surface normals of the F2/F3 head at the staged vertices (finite differences of Phi on the ray chart). python3 analytic_normals.py -> data/anorm_S.npz (assembled order, zeros outside the zone)"""
import sys
sys.path.insert(0, '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/female-micro-f3-head/tools')
import numpy as np, exp, make_final as mf, geo, meshlib as ml


def head_final():
    H = exp.build(under=mf.PARAMS['under'], prof=exp.prof_nochin(mf.PARAMS['prof_zcut'])); exp.apply_a_smooth(H, sig=mf.PARAMS['rows_smooth']['sig'], rows=tuple(mf.PARAMS['rows_smooth']['rows'])); H.bumps = mf.PARAMS['bumps']
    return H


def surf_normals(H, P, eps=3e-4):
    """normals of the analytic surface at points P (assumed on/near it): tangents from Phi evaluated at neighbouring chart directions"""
    u = P - geo.C[None, :]; u /= np.linalg.norm(u, axis=1, keepdims=True)
    a = np.where(np.abs(u[:, 2:3]) < 0.9, np.array([[0.0, 0.0, 1.0]]), np.array([[1.0, 0.0, 0.0]]))
    t1 = np.cross(u, a); t1 /= np.linalg.norm(t1, axis=1, keepdims=True); t2 = np.cross(u, t1)
    S0 = H.phi(u)
    S1 = H.phi((u + eps * t1) / np.linalg.norm(u + eps * t1, axis=1, keepdims=True)); S2 = H.phi((u + eps * t2) / np.linalg.norm(u + eps * t2, axis=1, keepdims=True))
    n = np.cross(S1 - S0, S2 - S0); n /= np.maximum(np.linalg.norm(n, axis=1, keepdims=True), 1e-30)
    s = np.where((n * u).sum(1, keepdims=True) < 0, -1.0, 1.0)
    return n * s


if __name__ == '__main__':
    ctx = exp.Ctx(); H = head_final()
    V = np.load('data/S.npz')['V'].astype(np.float64)
    zone = (V[:, 2] > 1.4225) & (V[:, 2] < 1.56) & (V[:, 1] < 0.04) & (np.abs(V[:, 0]) < 0.10)
    idx = np.where(zone)[0]
    N = surf_normals(H, V[idx])
    Nd, _, _ = ml.vertex_normals(V, ctx.F)
    ang = np.degrees(np.arccos(np.clip((N * Nd[idx]).sum(1), -1, 1)))
    print('zone verts', len(idx), ' analytic vs mesh vertex normal angle: mean %.2f p90 %.2f p99 %.2f max %.1f deg' % (ang.mean(), np.percentile(ang, 90), np.percentile(ang, 99), ang.max()))
    full = np.zeros_like(V); full[idx] = N
    np.savez('data/anorm_S.npz', N=full, idx=idx)

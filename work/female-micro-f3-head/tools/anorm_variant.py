"""analytic normals for a trial variant: python3 anorm_variant.py name key=value ...  (same keys as trial.py) -> data/anorm_<name>.npz (N full (n,3), w full (n,)) and a 3-view render with them (renders/trial/<name>N_*.png)"""
import sys
sys.path.insert(0, '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/female-micro-f3-head/tools')
import numpy as np, subprocess
import trial, exp, fl, geo, meshlib as ml
from fl import sstep
from analytic_normals import surf_normals

def normals_for(name, Vn, ctx, H, wide=0.010):
    V = Vn.astype(np.float64)
    P0 = ctx.Pold; nb = trial.mf.PARAMS['zone']['neck_blend']
    g = 1.0 - sstep(1.447, 1.462, P0[:, 2])
    wm = (1.0 - sstep(nb[0], nb[1], P0[:, 1]) * g) * sstep(1.4225, 1.4265, P0[:, 2]) * exp.lower_zone(P0) * ctx.chain_fade
    n = len(V); w = np.zeros(n); w[ctx.ids] = wm
    idx = np.where(w > 0)[0]
    N = np.zeros_like(V)
    N[idx] = surf_normals(H, V[idx])
    Nd, _, _ = ml.vertex_normals(V, ctx.F)
    ang = np.degrees(np.arccos(np.clip((N[idx] * Nd[idx]).sum(1), -1, 1)))
    print('analytic-normal verts', len(idx), ' angle to mesh vertex normal: mean %.2f p90 %.2f max %.1f' % (ang.mean(), np.percentile(ang, 90), ang.max()))
    np.savez(trial.W3 + f'data/anorm_{name}.npz', N=N, w=w)
    return N, w

if __name__ == '__main__':
    name = sys.argv[1]; kw = {}
    for a in sys.argv[2:]:
        k, v = a.split('='); kw[k] = float(v)
    Vn, ctx, H = trial.build_variant(name, **kw)
    normals_for(name, Vn, ctx, H)
    subprocess.run([trial.B, '-b', '--factory-startup', '--python', trial.W3 + 'tools/ul.py', '--', trial.W3 + f'data/var_{name}.npz', trial.W3 + 'renders/trial', trial.VIEWS, name + 'N', trial.W3 + f'data/anorm_{name}.npz'], check=True, capture_output=True)
    print('rendered', name + 'N')

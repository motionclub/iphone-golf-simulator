import sys, time
sys.path.insert(0, '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/female-micro-f1-head')
import numpy as np
import fl, geo, build, feats, feat_f, carve, loftf
t0 = time.time()
H, U, F, P, info = build.build(tag='b2', verbose=False)
adj = carve.edge_adj(F, len(P))
loops = {}
eye = feat_f.eye_poly(6)
for side, nm in ((-1, 'L'), (+1, 'R')):
    F, lp, nrem, rms = feats.carve_hole(H, U, P, F, eye, side, 'eye' + nm)
    loops['eye' + nm] = lp; print('eye', nm, 'removed faces', nrem, 'loop', len(lp), 'snap rms mm', rms * 1000)
    feats.relax_chart(H, U, P, carve.edge_adj(F, len(P)), lp, rings=2, iters=3)
nos = feat_f.NOSTRIL
for side, nm in ((-1, 'L'), (+1, 'R')):
    t = np.linspace(0, 2 * np.pi, 24, endpoint=False)
    poly = np.column_stack([nos['cx'] + nos['rx'] * np.cos(t), nos['cz'] + nos['rz'] * np.sin(t)])
    F, lp, nrem, rms = feats.carve_hole(H, U, P, F, poly, side, 'nos' + nm, shrink=-0.0005, ycut=-0.09)
    loops['nos' + nm] = lp; print('nostril', nm, 'removed', nrem, 'loop', len(lp), 'rms mm', rms * 1000)
print('time', time.time() - t0, 'tris', sum(len(f) - 2 for f in F))
loftf.save_npz(str(fl.W / 'data/b2.npz'), P, F)

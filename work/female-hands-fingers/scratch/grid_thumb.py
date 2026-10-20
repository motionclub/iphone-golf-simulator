import json, numpy as np, itertools, sys
import fit_f, asm_f, sil_f
from femlib import face_normals
x = json.load(open('data/fit_best_s9_ckpt.json'))['params']
base_pts = [(0.026, 0.004, 0.030), (0.036, 0.011, 0.050), (0.040, 0.016, 0.076), (0.040, 0.021, 0.104)]
def ev(extra):
    y = dict(x); par, pose = fit_f.split({**fit_f.DEFAULT, **y}); par.update(extra); par.setdefault('sm_iters', 60)
    Vn, polys, si, removed = asm_f.assemble(par, pose, verbose=False)
    hm = sil_f.hand_flag(len(Vn), {s: np.load(asm_f.W / f'data/start_hand_verts_{s}.npy') for s in (1, -1)}, asm_f.N0)
    roi = sil_f.evaluate(Vn, polys, hm)['total']
    s = si[1]; mp = s['mapping']; info = s['info']
    t_ids = [mp[v] for row in info['thumb_rows'] for v in row]; i_ids = [mp[v] for row in info['fin_rows'][0][0] for v in row]
    over = (Vn[i_ids, 1].min() - Vn[t_ids, 1].min()) * 1000
    nkept = len(asm_f.POLYS0) - int(removed.sum()); hf = polys[nkept:nkept + len(s['faces'])]
    ef = {}
    for fi, f in enumerate(hf):
        for k in range(len(f)):
            a_, b_ = f[k], f[(k + 1) % len(f)]; ef.setdefault((min(a_, b_), max(a_, b_)), []).append(fi)
    FN = face_normals(Vn, hf); lc = Vn[[mp[v] for v in info['thumb_loop']]].mean(0); dih = 0
    for e, fl in ef.items():
        if len(fl) == 2 and np.linalg.norm(0.5 * (Vn[e[0]] + Vn[e[1]]) - lc) < 0.025: dih = max(dih, float(np.degrees(np.arccos(np.clip(np.dot(FN[fl[0]], FN[fl[1]]), -1, 1)))))
    # clearance
    hr1 = info['hole'][1]; other = [mp[v] for r, row in info['ring'].items() if r >= hr1 for v in row if v in mp]
    for k in (0, 1): other += [mp[v] for row in info['fin_rows'][k][0] for v in row]
    Oth = Vn[other]; mc = 1e9
    for j, row in enumerate(info['thumb_rows']):
        if j < 4: continue
        P_ = Vn[[mp[v] for v in row]]; c = P_.mean(0); r_ = np.linalg.norm(P_ - c, axis=1).mean(); mc = min(mc, np.linalg.norm(Oth - c, axis=1).min() - r_)
    return roi, over, dih, mc * 1000, Vn[mp[info['thumb_tip']]] * 1000
res = []
for cols, ash, nsh, lift in itertools.product(((0.85, 0.975), (0.80, 0.92), (0.76, 0.88)), (-0.012, -0.006, 0.0), (0.0, 0.006), (0.0, 0.010)):
    pts = [base_pts[0]] + [(p[0] + ash, p[1] + nsh, p[2]) for p in base_pts[1:]]
    r = ev(dict(hole_cols_frac=cols, thumb_pts=pts, thumb_a_shift=0.0, thumb_n_shift=0.0, root_lift=lift, thumb_first=0.012))
    res.append((cols, ash, nsh, lift) + r[:4])
    print('cols %s a%+.3f n%+.3f lift %.3f | ROI %.0f over %.1f dih %.0f clear %.1f' % ((cols, ash, nsh, lift) + r[:4]), flush=True)

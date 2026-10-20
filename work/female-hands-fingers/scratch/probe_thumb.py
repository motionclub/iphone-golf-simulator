import json, numpy as np, sys
import fit_f, asm_f, metrics_f
x = json.load(open('data/fit_best_s9_ckpt.json'))['params']
def run(tag, extra, xo=None):
    y = dict(x); 
    if xo: y.update(xo)
    r = fit_f.evaluate({**y, **{}}) if not extra else None
    par, pose = fit_f.split({**fit_f.DEFAULT, **y}); par.update(extra); par.setdefault('sm_iters', 40)
    Vn, polys, si, removed = asm_f.assemble(par, pose, verbose=False)
    import sil_f
    hm = sil_f.hand_flag(len(Vn), {s: np.load(asm_f.W / f'data/start_hand_verts_{s}.npy') for s in (1, -1)}, asm_f.N0)
    ev = sil_f.evaluate(Vn, polys, hm)
    s = si[1]; mp = s['mapping']; info = s['info']
    thumb_ids = [mp[v] for row in info['thumb_rows'] for v in row]; idx_ids = [mp[v] for row in info['fin_rows'][0][0] for v in row]
    over = (Vn[idx_ids, 1].min() - Vn[thumb_ids, 1].min()) * 1000
    # dihedral over hand faces near the loop
    nkept = len(asm_f.POLYS0) - int(removed.sum()); hf = polys[nkept:nkept + len(s['faces'])]
    from femlib import face_normals
    ef = {}
    for fi, f in enumerate(hf):
        for k in range(len(f)):
            a_, b_ = f[k], f[(k + 1) % len(f)]; ef.setdefault((min(a_, b_), max(a_, b_)), []).append(fi)
    FN = face_normals(Vn, hf); lc = Vn[[mp[v] for v in info['thumb_loop']]].mean(0); dih = 0
    for e, fl in ef.items():
        if len(fl) == 2 and np.linalg.norm(0.5 * (Vn[e[0]] + Vn[e[1]]) - lc) < 0.025: dih = max(dih, float(np.degrees(np.arccos(np.clip(np.dot(FN[fl[0]], FN[fl[1]]), -1, 1)))))
    print('%-40s ROI %.0f  thumb front over index %.1f mm  web dih %.0f  thumb tip xyz %s' % (tag, ev['total'], over, dih, np.round(Vn[mp[info['thumb_tip']]] * 1000, 0)))
    return Vn, polys, si, removed
base_pts = [(0.026, 0.004, 0.030), (0.036, 0.011, 0.050), (0.040, 0.016, 0.076), (0.040, 0.021, 0.104)]
run('current radial-flank hole', {})
for cols in ((0.735, 0.85), (0.70, 0.82), (0.76, 0.88)):
    for pts in ([(0.012, 0.004, 0.030), (0.014, 0.014, 0.052), (0.016, 0.021, 0.078), (0.016, 0.025, 0.104)], ):
        run(f'palmar hole {cols} lift', dict(hole_cols_frac=cols, thumb_pts=pts, thumb_a_shift=0.0, thumb_n_shift=0.0, root_lift=0.006))
print('--- tuning the palmar-hole root')
pts0 = [(0.012, 0.004, 0.030), (0.014, 0.014, 0.052), (0.016, 0.021, 0.078), (0.016, 0.025, 0.104)]
cols = (0.76, 0.88)
for lift, first, nsh in ((0.010, 0.010, 0.0), (0.014, 0.010, 0.0), (0.014, 0.014, 0.004), (0.018, 0.012, 0.004), (0.014, 0.010, 0.008)):
    pts = [pts0[0]] + [(p[0], p[1] + nsh, p[2]) for p in pts0[1:]]
    run(f'lift {lift} first {first} n+{nsh}', dict(hole_cols_frac=cols, thumb_pts=pts, thumb_a_shift=0.0, thumb_n_shift=0.0, root_lift=lift, thumb_first=first))
print('--- web fillet strength with the palmar hole (lift .014 first .014 n+.004)')
pts = [pts0[0]] + [(p[0], p[1] + 0.004, p[2]) for p in pts0[1:]]
common = dict(hole_cols_frac=cols, thumb_pts=pts, thumb_a_shift=0.0, thumb_n_shift=0.0, root_lift=0.014, thumb_first=0.014)
for wk, wa, smr, it in ((0.030, 1.4, 0.09, 120), (0.040, 1.6, 0.09, 120), (0.040, 2.0, 0.11, 160), (0.050, 2.0, 0.11, 160), (0.050, 2.4, 0.12, 200)):
    run(f'web_k {wk} amp {wa} smR {smr} it {it}', dict(common, web_k=wk, web_amp=wa, sm_thumb_R=smr, sm_iters=it))

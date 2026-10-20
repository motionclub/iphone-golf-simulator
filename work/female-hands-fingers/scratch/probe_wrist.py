import json, numpy as np
import fit_f, checks_f, asm_f
from femlib import *
x = json.load(open('data/fit_best_s9_ckpt.json'))['params']
def show(tag, par=None):
    y = dict(x); 
    if par: y['extra'] = par
    p_, pose = fit_f.split({**fit_f.DEFAULT, **{k: v for k, v in y.items() if k != 'extra'}})
    if par: p_.update(par)
    p_.setdefault('sm_iters', 40)
    Vn, polys, si, removed = asm_f.assemble(p_, pose, verbose=False)
    info = si[1]['info']; Bd = si[1]['B']; Nn = asm_f.N0
    npal = []; ndor = []; wm = []
    for r in sorted(info['ring']):
        if info['w_rows'][r - 1] > 0.062: continue
        pts = np.array([Bd.pos[v - Nn] for v in info['ring'][r]])
        npal.append(pts[:, 1].max()); ndor.append(pts[:, 1].min()); wm.append(pts[:, 2].mean())
    npal, ndor, wm = map(np.array, (npal, ndor, wm))
    sp = np.abs(np.diff(npal) / np.diff(wm)); sd = np.abs(np.diff(ndor) / np.diff(wm))
    wd = checks_f.weld_dihedral(Vn, polys, np.load(asm_f.W / 'data/start_hand_ring_1.npy'))
    print('%-34s shelfP max %.2f  D max %.2f   weld dihedral %.1f   palmar n(w): %s' % (tag, sp.max(), sd.max(), wd, np.round(npal * 1000, 1)[:7]))
show('current')
show('taper -0.14', dict(forearm_taper=-0.14))
show('taper -0.18', dict(forearm_taper=-0.18))
show('sm_rows .6 .6 .5 .4', dict(sm_rows=[0.6, 0.6, 0.5, 0.4]))
show('sm_rows .8 .8 .7 .6 .5', dict(sm_rows=[0.8, 0.8, 0.7, 0.6, 0.5]))
show('taper -.14 + sm_rows', dict(forearm_taper=-0.14, sm_rows=[0.8, 0.8, 0.7, 0.6, 0.5]))
show('B_tab slower', dict(B_tab=([0.0, 0.02, 0.04, 0.06, 0.0806], [0.0285, 0.0250, 0.0190, 0.0130, 0.0092])))
show('B_tab slower + sm_rows + taper', dict(B_tab=([0.0, 0.02, 0.04, 0.06, 0.0806], [0.0285, 0.0250, 0.0190, 0.0130, 0.0092]), forearm_taper=-0.14, sm_rows=[0.8, 0.8, 0.7, 0.6, 0.5]))

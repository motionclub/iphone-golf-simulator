import json, sys, numpy as np
import fit_f, asm_f
from femlib import *
def mirror_report(x, verbose=True):
    par, pose = fit_f.split({**fit_f.DEFAULT, **x})
    Vn, polys, si, removed = asm_f.assemble(par, pose, verbose=False)
    R, L = si[1], si[-1]
    def pos(s, ids): return np.array([Vn[s['mapping'][i]] for i in ids])
    res = {}
    def cmp(name, idsR, idsL, w=None):
        pairs = [(i, j) for i, j in zip(idsR, idsL) if i in R['mapping'] and j in L['mapping']]
        a = pos(R, [p[0] for p in pairs]); b = pos(L, [p[1] for p in pairs]); b = b.copy(); b[:, 0] = -b[:, 0]
        d = np.linalg.norm(a - b, axis=1)
        res[name] = (float(d.max()) * 1000, float(d.mean()) * 1000, len(d))
    # fingers
    for k in range(4):
        rR = [v for row in R['info']['fin_rows'][k][0] for v in row] + [R['info']['fin_rows'][k][1]]
        rL = [v for row in L['info']['fin_rows'][k][0] for v in row] + [L['info']['fin_rows'][k][1]]
        cmp(f'finger{k}', rR, rL)
    cmp('thumb', [v for row in R['info']['thumb_rows'] for v in row] + [R['info']['thumb_tip']], [v for row in L['info']['thumb_rows'] for v in row] + [L['info']['thumb_tip']])
    # palm rows by w
    nR = len(R['info']['w_rows']); nL = len(L['info']['w_rows']); off = nL - nR
    for lo, hi in ((0.0, 0.03), (0.03, 0.2)):
        idsR = []; idsL = []
        for r in range(1, nR + 1):
            w = R['info']['w_rows'][r - 1]
            if lo <= w < hi:
                idsR += R['info']['ring'][r]; idsL += L['info']['ring'][r + off]
        cmp(f'palm_w{lo:.2f}-{hi:.2f}', idsR, idsL)
    if verbose:
        for k, v in res.items(): print('%-18s max %.4f mm mean %.4f mm  n %d' % (k, *v))
    return res
if __name__ == '__main__':
    x = json.load(open(sys.argv[1]))['params'] if sys.argv[1].endswith('.json') else json.loads(sys.argv[1])
    mirror_report(x)

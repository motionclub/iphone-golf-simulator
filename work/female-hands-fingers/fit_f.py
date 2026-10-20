"""Bounded random-search fit of the hand pose / shape parameters to the plate hand silhouettes (anatomy-first bounds).
python fit_f.py <iters> <seed> [start.json]  -> data/fit_best.json ; importable: evaluate(x_dict)"""
import sys, json, time, copy
from pathlib import Path
import numpy as np
W = Path(__file__).resolve().parent; sys.path.insert(0, str(W))
import asm_f, sil_f, fhand
from femlib import *

# name: (lo, hi, kind)  kind 'p' -> hand param, 'o' -> pose param
SPACE = {
    'out_deg': (-10.0, 14.0, 'o'), 'shear_L': (0.070, 0.115, 'o'), 'lean_deg': (-6.0, 10.0, 'o'), 'psi_deg': (-25.0, 20.0, 'o'), 'shear_y': (0.020, 0.034, 'o'),
    'curl': (0.35, 1.6, 'p'), 'B_gain': (0.85, 1.6, 'p'), 'A_gain': (0.80, 1.18, 'p'), 'NC_gain': (0.0, 1.2, 'p'), 'span': (0.040, 0.095, 'p'),
    'thumb_r_scale': (0.90, 1.12, 'p'), 'fing_scale': (0.96, 1.08, 'p'), 'splay_scale': (0.0, 1.1, 'p'), 'thumb_a_shift': (-0.003, 0.003, 'p'), 'thumb_n_shift': (-0.003, 0.004, 'p'), 'thumb_len_scale': (0.90, 1.20, 'p'),
    'mid_tip': (0.145, 0.168, 'p'),
}
import os
FIXED = json.loads(os.environ.get('FIX', '{}'))
KEYS = [k for k in SPACE if k not in FIXED]
DEFAULT = dict(shear_L=0.100, splay_scale=1.0, out_deg=3.8, lean_deg=0.0, psi_deg=0.0, shear_y=0.028, curl=0.6, B_gain=1.0, A_gain=1.0, NC_gain=1.0, span=0.045, thumb_r_scale=1.0, fing_scale=1.0, thumb_a_shift=0.0, thumb_n_shift=0.0, thumb_len_scale=1.0, mid_tip=0.1537)
# plate landmarks in the left profile (+x hand, y in metres): finger centre y of index .. pinky at tip level
LM_Y = dict(index=-0.055, pinky=-0.003)
SHELF_MAX = 0.85

def split(x):
    pose = {k: v for k, v in x.items() if SPACE.get(k, (0, 0, ''))[2] == 'o'}
    par = {k: v for k, v in x.items() if SPACE.get(k, (0, 0, ''))[2] == 'p'}
    return par, pose

_HM = None
def hand_mask(V):
    return sil_f.hand_mask_for(V)

def evaluate(x, want_masks=False):
    par, pose = split({**DEFAULT, **x})
    par.setdefault('sm_iters', 40)                         # faster smoothing inside the search; final builds use the full default
    Vn, polys, si, removed = asm_f.assemble(par, pose, verbose=False)
    hm = sil_f.hand_flag(len(Vn), {s: np.load(W / f'data/start_hand_verts_{s}.npy') for s in (1, -1)}, asm_f.N0)
    out = sil_f.evaluate(Vn, polys, hm, return_masks=want_masks)
    if want_masks: out, masks = out
    # profile landmark penalty (+x hand, side=+1): y of the fingertip pole of index and pinky
    info = si[+1]['info']; mp = si[+1]['mapping']
    Cidx = {k: info['fin_rows'][k][1] for k in (0, 3)}
    yi = Vn[mp[Cidx[0]], 1]; yp = Vn[mp[Cidx[3]], 1]
    lm = abs(yi - LM_Y['index']) + abs(yp - LM_Y['pinky'])
    thumb_ids = [mp[v] for row in info['thumb_rows'] for v in row]
    idx_ids = [mp[v] for row in info['fin_rows'][0][0] for v in row]
    over = max(0.0, (Vn[idx_ids, 1].min() - Vn[thumb_ids, 1].min()) - 0.004)       # thumb must not stick out in front of the index finger (lateral profile)
    out['thumb_front_over_mm'] = round(over * 1000, 2)
    out['lm_err_mm'] = round(lm * 1000, 2); out['tip_y_mm'] = [round(yi * 1000, 1), round(yp * 1000, 1)]
    hid = sorted(set(mp.values())); zz = Vn[hid, 2]; yy = Vn[hid, 1][zz <= 0.80]
    edge_err = max(0.0, abs(yy.max() * 1000 - 5.0) - 9.0) + max(0.0, abs(yy.min() * 1000 + 60.0) - 9.0)
    out['band_back_front_mm'] = [round(float(yy.max() * 1000), 1), round(float(yy.min() * 1000), 1)]
    # wrist shelf: maximum slope of the palm's palmar / dorsal surface (local n vs w) over the first rows next to the weld
    Bd = si[+1]['B']; Nn = asm_f.N0
    ringd = info['ring']; wr = info['w_rows']
    npal = []; ndor = []; wm = []
    for r in sorted(ringd):
        if wr[r - 1] > 0.062: continue
        pts = np.array([Bd.pos[v - Nn] for v in ringd[r] if (v - Nn) < len(Bd.pos)])
        npal.append(pts[:, 1].max()); ndor.append(pts[:, 1].min()); wm.append(pts[:, 2].mean())
    npal = np.array(npal); ndor = np.array(ndor); wm = np.array(wm)
    sp = np.abs(np.diff(npal) / np.diff(wm)).max(); sd = np.abs(np.diff(ndor) / np.diff(wm)).max()
    out['shelf_slope_palmar'] = round(float(sp), 3); out['shelf_slope_dorsal'] = round(float(sd), 3)
    shelf = max(0.0, sp - SHELF_MAX) + max(0.0, sd - SHELF_MAX)
    # thumb sanity: web dihedral (hand faces only) and clearance between the thumb tube and the palm / index+middle finger surfaces
    nkept = len(asm_f.POLYS0) - int(removed.sum())
    hand_faces = polys[nkept:nkept + len(si[+1]['faces'])]
    ef = {}
    for fi, f in enumerate(hand_faces):
        for k in range(len(f)):
            a_, b_ = f[k], f[(k + 1) % len(f)]; ef.setdefault((min(a_, b_), max(a_, b_)), []).append(fi)
    FNh = face_normals(Vn, hand_faces)
    loopc = Vn[[mp[v] for v in info['thumb_loop']]].mean(0)
    dih = 0.0
    for e, fl in ef.items():
        if len(fl) == 2 and np.linalg.norm(0.5 * (Vn[e[0]] + Vn[e[1]]) - loopc) < 0.025:
            dih = max(dih, float(np.degrees(np.arccos(np.clip(np.dot(FNh[fl[0]], FNh[fl[1]]), -1, 1)))))
    out['web_dihedral_deg'] = round(dih, 1)
    hr1 = info['hole'][1]
    other = [mp[v] for r, row in info['ring'].items() if r >= hr1 for v in row if v in mp]
    for k in (0, 1):
        other += [mp[v] for row in info['fin_rows'][k][0] for v in row]
    Oth = Vn[other]
    clear_pen = 0.0; min_clear = 1e9
    for j, row in enumerate(info['thumb_rows']):
        if j < 4: continue
        P_ = Vn[[mp[v] for v in row]]; c = P_.mean(0); r_ = np.linalg.norm(P_ - c, axis=1).mean()
        d = np.linalg.norm(Oth - c, axis=1).min() - r_
        min_clear = min(min_clear, d); clear_pen += max(0.0, 0.0025 - d) * 1000
    out['thumb_min_clear_mm'] = round(min_clear * 1000, 2)
    out['cost'] = out['total'] + 9000.0 * lm + 25000.0 * over + 6000.0 * shelf + 1500.0 * clear_pen + 40.0 * max(0.0, dih - 70.0) + 50.0 * edge_err
    return (out, masks, (Vn, polys, si)) if want_masks else out

def encode(x):
    return np.array([np.clip((x.get(k, DEFAULT[k]) - SPACE[k][0]) / (SPACE[k][1] - SPACE[k][0]), 0, 1) for k in KEYS])
def decode(u):
    d = {k: float(SPACE[k][0] + u[i] * (SPACE[k][1] - SPACE[k][0])) for i, k in enumerate(KEYS)}
    d.update(FIXED); return d

if __name__ == '__main__':
    iters = int(sys.argv[1]); seed = int(sys.argv[2]); rng = np.random.default_rng(seed)
    start = json.load(open(sys.argv[3])) if len(sys.argv) > 3 else {}
    u = encode(start); r0 = evaluate(decode(u)); best = (r0['cost'], u.copy(), r0)
    print('start cost %.0f roi %.0f lm %.1f mm' % (r0['cost'], r0['total'], r0['lm_err_mm']), flush=True)
    sigma = 0.15; succ = 0; tries = 0; t = time.time()
    for it in range(iters):
        un = np.clip(best[1] + rng.normal(0, sigma, len(KEYS)) * (rng.random(len(KEYS)) < 0.45), 0, 1)
        try: r = evaluate(decode(un))
        except Exception as e:
            print('eval error', repr(e)[:200]); continue
        tries += 1
        if r['cost'] < best[0]: best = (r['cost'], un, r); succ += 1
        if tries % 20 == 0:
            sigma = float(np.clip(sigma * (1.25 if succ / 20 > 0.2 else 0.8), 0.02, 0.3)); succ = 0
        if it % 25 == 0:
            json.dump(dict(params=decode(best[1]), cost=best[0], result={k: v for k, v in best[2].items() if k != 'per'}, per=best[2]['per']), open(W / 'data/fit_best.json', 'w'), indent=1)
        if it % 25 == 0: print(it, 'cost %.0f roi %.0f lm %.1f' % (best[0], best[2]['total'], best[2]['lm_err_mm']), 'sigma %.3f' % sigma, '%.0fs' % (time.time() - t), flush=True)
    P = decode(best[1]); json.dump(dict(params=P, cost=best[0], result={k: v for k, v in best[2].items() if k != 'per'}, per=best[2]['per']), open(W / 'data/fit_best.json', 'w'), indent=1)
    print('BEST', round(best[0]), best[2]['total'], best[2]['lm_err_mm']); print(json.dumps(P))

"""rampfit8.py: round-5 underbutt search IN THE RENDER DOMAIN.  Candidates are built with pelvis5 (numpy), screened with the numpy constraints (envelope, dihedral, slope change) and then
rendered in ONE Blender session per generation (soft matcap, the same pipeline as proof/06z); the fold line is traced in the panel (what the eye / the critics see).
cost = rms error of the left/right-averaged fold-line rows vs the plate panel (px) + 0.8 * max(0, 10 - lateral rise px) [+ small penalties]
python3 tools/rampfit8.py NAME generations seed [start.json] [pop]"""
import sys, os, json, copy, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import rampfit6 as rf
import rampfit7 as r7
import pelvis5 as pv, benv5
import foldx5 as fx
import blbatch6 as bb
import cnweight5 as cnw
from torso4 import CO0, T, BORDER
HERE = fx.HERE; FB = fx.FB
ZG2 = np.arange(0.70, 0.881, 0.02)
ENV_CAP = float(os.environ.get('ENV_CAP', '3.8'))
SPACE = dict(r7.SPACE)
ABS_OPT = (45, 60, 75, 90)
_PR = bb.fold_rows(bb.plate_panel())
PLATE_ROWS = np.array([0.5 * (_PR[-a] + _PR[a]) for a in ABS_OPT])

def sag(c_, xc, zr=np.arange(0.66, 0.90, 0.01)):
    ys = []
    for z in zr:
        m = (np.abs(c_[:, 2] - z) < 0.0056) & (np.abs(c_[:, 0] - xc) < 0.012) & (c_[:, 1] > 0.0)
        ys.append(c_[m, 1].max() if m.any() else np.nan)
    return zr, np.array(ys)

def gauss1d(a, s, step):
    k = np.arange(-int(3 * s / step), int(3 * s / step) + 1) * step
    w = np.exp(-0.5 * (k / s) ** 2); w /= w.sum(); pad = len(k) // 2
    return np.convolve(np.pad(a, pad, mode='edge'), w, mode='valid')

def max_slope_change(c_):
    out = []
    for xc in (0.065, 0.09):
        zr, y = sag(c_, xc); good = np.isfinite(y)
        yy = np.interp(zr, zr[good], y[good]); yy = gauss1d(np.interp(np.arange(0.66, 0.90, 0.002), zr, yy), 0.008, 0.002)
        ang = np.degrees(np.arctan(np.gradient(yy, 0.002)))
        zz = np.arange(0.66, 0.90, 0.002); m = (zz >= 0.74) & (zz <= 0.86)
        out.append(float(np.abs(np.diff(ang[m][::5])).max()))
    return max(out)

def screen(co):
    e = 1000 * (benv5.env(co, ZG2) - np.interp(ZG2, FB[0], FB[1]))
    dm, di, du = rf.dih_stats(co)
    ms = max_slope_change(co)
    ok = (np.abs(e).max() <= ENV_CAP) and dm <= 29.5 and di <= 24.8 and du <= 26.0 and ms <= 18.0
    return ok, dict(env=float(np.abs(e).max()), dm=dm, di=di, du=du, ms=ms)

def jb(rows):
    """render-domain cost on the ROBUST fixed-window trace (round-5 fix: the first trace flipped between features at the faint outer columns and the search exploited it).
    err = rms of the left/right-averaged rows (dx 45..90) vs the plate; rise = row(45) - row(90) (plate ~8 px); penalties: jaggedness (second difference > 3 px) and outer column (105) off by > 15 px."""
    r = np.array([0.5 * (rows[-a] + rows[a]) for a in ABS_OPT])
    err = float(np.sqrt(((r - PLATE_ROWS) ** 2).mean())); rise = float(r[0] - r[-1])
    jag = 0.0
    for sgn in (-1, 1):
        v = [rows[sgn * a] for a in (45, 60, 75, 90, 105)]
        for i in range(1, 4):
            jag += max(0.0, abs(v[i] - 0.5 * (v[i - 1] + v[i + 1])) - 3.0)
    outer = sum(max(0.0, abs(rows[sgn * 105] - _PR[sgn * 105]) - 15.0) for sgn in (-1, 1))
    return err + 1.0 * max(0.0, 8.0 - rise) + 0.5 * jag + 0.5 * outer, err, rise

def perturb(PP, rng, scale):
    Q = copy.deepcopy(PP)
    keys = list(SPACE)
    for k in rng.choice(keys, int(rng.integers(1, 5)), replace=False):
        lo, hi, st = SPACE[k]
        Q[k] = float(np.clip(Q.get(k, 0.5 * (lo + hi)) + rng.normal() * st * scale * (1 if rng.random() < .7 else 2.5), lo, hi))
    return Q

def valid(Q):
    return not (Q.get('c_x1', 0.07) <= Q.get('c_x0', 0.03) + 0.01 or Q.get('ds_x1', 0.12) <= Q.get('ds_x0', 0.07) + 0.02 or Q.get('rl1', 0.16) <= Q.get('rl0', 0.11) + 0.02
                or Q.get('rx1', 0.13) <= Q.get('rx0', 0.06) + 0.03 or Q.get('rz3', 0.84) <= Q.get('rz2', 0.78) + 0.03)

if __name__ == '__main__':
    name, gens, seed = sys.argv[1], int(sys.argv[2]), int(sys.argv[3])
    start = sys.argv[4] if len(sys.argv) > 4 else HERE + '/data/PP5_final.json'
    pop = int(sys.argv[5]) if len(sys.argv) > 5 else 40
    rng = np.random.default_rng(seed)
    PP = json.load(open(start)); PP['rl0'] = 0.075; PP['rl1'] = 0.2
    co0 = pv.build_pelvis(rf.CO_MIX, PP); ok0, st0 = screen(co0)
    tmp = f'{HERE}/scratch/r/q8_{name}_cur.npy'; np.save(tmp, co0)
    tmpw = f'{HERE}/scratch/r/q8_{name}_curw.npy'; np.save(tmpw, cnw.cn_weight(co0))
    pan = bb.render_panels({'cur': (tmp, tmpw)}, prefix=f'q8_{name}')
    bestJ, berr, brise = jb(bb.fold_rows(pan['cur']))
    print(f'start J {bestJ:.2f} err {berr:.1f} rise {brise:.1f} | screen ok={ok0} {st0}', flush=True)
    t0 = time.time()
    for g in range(gens):
        scale = 1.0 if g < gens * 0.6 else 0.5
        cands = {}
        tries = 0
        while len(cands) < pop and tries < pop * 6:
            tries += 1
            Q = perturb(PP, rng, scale)
            if not valid(Q): continue
            co = pv.build_pelvis(rf.CO_MIX, Q)
            ok, st = screen(co)
            if not ok: continue
            tag = f'c{len(cands)}'; path = f'{HERE}/scratch/r/q8_{name}_{tag}.npy'; np.save(path, co)
            np.save(f'{HERE}/scratch/r/q8_{name}_{tag}_w.npy', cnw.cn_weight(co))
            cands[tag] = (Q, st)
        if not cands: continue
        pans = bb.render_panels({t: (f'{HERE}/scratch/r/q8_{name}_{t}.npy', f'{HERE}/scratch/r/q8_{name}_{t}_w.npy') for t in cands}, prefix=f'q8_{name}')
        res = {t: jb(bb.fold_rows(p)) for t, p in pans.items()}
        tb = min(res, key=lambda t: res[t][0])
        if res[tb][0] < bestJ - 0.25:
            bestJ, berr, brise = res[tb]; PP = cands[tb][0]
            json.dump(PP, open(HERE + f'/data/PP5_{name}.json', 'w'), indent=1)
            print(f'gen {g:3d} ({time.time()-t0:5.0f}s) J {bestJ:.2f} err {berr:.1f} rise {brise:.1f} | {cands[tb][1]}', flush=True)
    json.dump(PP, open(HERE + f'/data/PP5_{name}.json', 'w'), indent=1)
    print('done', name, 'J', bestJ, 'err', berr, 'rise', brise)

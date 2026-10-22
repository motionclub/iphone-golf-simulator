"""bx5.py: fast chest variant sweeps with metrics.  python3 tools/bx5.py name:'{overrides}' ... ; prints envelope errors, crescent line, seams, band-pass costs, dihedral max; saves coords co5_<name>.npy"""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import chestx5, costb5, cres5, seam
from torso4 import section_extents, fillnan, ZG
HERE = chestx5.HERE
FF = chestx5.FF
BASE = os.environ.get('BX_BASE', HERE + '/data/P5_final.json')
CONC = {"conc_post": {"mode": "land", "zs": 1.262, "ze": 1.355}}


def valley_mm(co):
    from footprint import grid_surface
    xs_ = np.arange(-0.14, 0.1401, 0.002); zs_ = np.arange(1.10, 1.34, 0.002)
    Gf = grid_surface(co, 'front', xs_, zs_)
    ix = lambda x: int(round((x - xs_[0]) / 0.002)); iz = lambda z: int(round((z - zs_[0]) / 0.002))
    res = {}
    for side, sg in (('R', 1), ('L', -1)):
        cols = np.where((sg * xs_ >= 0.03) & (sg * xs_ <= 0.125))[0]; rows = np.where((zs_ >= 1.17) & (zs_ <= 1.29))[0]
        sub = Gf[np.ix_(rows, cols)]; i, j = np.unravel_index(np.argmin(sub), sub.shape)
        res[side] = (float(xs_[cols[j]]), float(zs_[rows[i]]))
    zc_ = 0.5 * (res['R'][1] + res['L'][1]); apx_y = 0.5 * sum(Gf[iz(res[s][1]), ix(res[s][0])] for s in 'RL')
    return 1000 * (Gf[iz(zc_), np.abs(xs_) < 0.006].mean() - apx_y)


def summarize(name, co):
    fe, be = section_extents(co); fe = fillnan(fe)
    zs = (1.16, 1.20, 1.22, 1.24, 1.26, 1.28, 1.30, 1.32)
    env = ' '.join(f'{z:.2f}:{1000*(np.interp(z, ZG, fe)-np.interp(z, FF[0], FF[1])):+5.1f}' for z in zs)
    bs = seam.border_steps(co)[0]
    m = costb5.metrics(co, 1.5)
    st = cres5.stats(co, 1.5)
    cr = ' '.join(f'{x:.3f}:{v[2]:.3f}({v[0]:.3f}) {v[3]:+.0f}({v[1]:+.0f})' for x, v in st.items())
    a1 = seam.dihedral(co)
    from torso4 import T, BORDER
    mid = 0.5 * (co[seam.PAIR_E[:, 0]] + co[seam.PAIR_E[:, 1]])
    zp = T[seam.PAIR_E[:, 0]] & T[seam.PAIR_E[:, 1]]
    cen = zp & (mid[:, 2] >= 1.15) & (mid[:, 2] <= 1.30) & (np.abs(mid[:, 0]) < 0.022) & (mid[:, 1] < 0)
    a0 = seam.dihedral(np.load(HERE + '/data/orig_co.npy').astype(np.float64))
    nb_ = ~(BORDER[seam.PAIR_E[:, 0]] | BORDER[seam.PAIR_E[:, 1]]) & (a0 <= 15.0)
    bust = zp & nb_ & (mid[:, 2] >= 1.14) & (mid[:, 2] <= 1.32) & (np.abs(mid[:, 0]) <= 0.115) & (mid[:, 1] < 0)
    dd = f'dih sternum {a1[cen].max():.1f} bust {a1[bust].max():.1f}'
    return (f'{name}: env {env} | seams arm {bs["arm"]["max_mm"]:.1f} top {bs["top"]["max_mm"]:.2f} | bp rms {m["rms"]:.2f} ncc {m["ncc"]:.3f} L{m["rms_Lmound"]:.1f} R{m["rms_Rmound"]:.1f} val{m["rms_valley"]:.1f} up{m["rms_upper"]:.1f} lo{m["rms_lower"]:.1f} Lfl{m["rms_Lflank"]:.1f} Rcr{m["rms_Rcres"]:.1f} g{m["g"]:.2f} valley {valley_mm(co):.1f}mm {dd}\n'
            f'      crescent z(plate) dip(plate): {cr}')


if __name__ == '__main__':
    for a in sys.argv[1:]:
        name, _, js = a.partition(':')
        ov = json.loads(js) if js else {}
        ov = {**CONC, **ov}
        co, P = chestx5.run(name, ov, base=BASE)
        print(summarize(name, co))

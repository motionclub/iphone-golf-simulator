"""FORM4 try-runner:  python3 tools/run4.py <tag> <params.json> [--board soft|clay|both] [--sec]
 builds co = build3(P, fit_walls(P)) with tools/torso4.py, saves data/co_try_<tag>.npy, prints the numbers that matter
 (front envelope vs sub-pixel plate contour, bust relief, seam steps, glute drift vs FORM3) and renders the chest boards."""
import sys, os, json, subprocess
sys.path.insert(0, os.path.dirname(__file__))
import numpy as np
import torso4 as t4
from torso4 import *
import seam

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CO3 = np.load(HERE + '/data/co_FORM3_final.npy').astype(np.float64)
FF = np.load(HERE + '/data/plate_front_fine4.npy')
SOFT = 'matcap:' + HERE + '/tools/matcap_platefit_g22.png'


def env_front(co, z0, w=0.0055):
    """front-most y of zone verts in a thin band (use edge crossings for exactness)"""
    fe, be = section_extents(co)
    fe, be = fillnan(fe), fillnan(be)
    return np.interp(z0, ZG, fe), np.interp(z0, ZG, be)


def build(P, iters=4):
    dF, dB = t4.fit_walls(P, iters=iters, verbose=False, zlo=0.82, zhi=1.30, fz=(0.82, 1.12), bz=(0.82, 1.30))
    co = t4.build3(P, dF, dB)
    return co, dF, dB


def report(co, tag):
    print(f'--- {tag}')
    print(' z     plate(fine)  model   diff(model-plate) mm   | FORM3 diff')
    for z in (1.10, 1.14, 1.17, 1.19, 1.20, 1.21, 1.22, 1.23, 1.24, 1.25, 1.26, 1.27, 1.28, 1.30, 1.32, 1.34, 1.36):
        pf = np.interp(z, FF[0], FF[1])
        m, _ = env_front(co, z)
        m3, _ = env_front(CO3, z)
        print(f' {z:.2f}  {1000*pf:+8.1f}  {1000*m:+8.1f}  {1000*(m-pf):+7.1f}     | {1000*(m3-pf):+7.1f}')
    bs = seam.border_steps(co)[0]
    print(' border steps max mm (legs<=8, arm<=10, top<=1):', {k: round(v['max_mm'], 2) for k, v in bs.items()})
    mv = np.linalg.norm(co - CO0, axis=1)
    print(' max vertex move vs original (mm): %.1f   zone verts moved: %d   outside moved: %d' % (1000 * mv.max(), int((mv > 1e-9).sum()), int(((mv > 1e-9) & ~T).sum())))
    d = np.linalg.norm(co - CO3, axis=1)
    g = (CO0[:, 2] < 1.0)
    print(' drift vs FORM3: z<1.0 (glute/pelvis) max %.2f mm   z<1.06 max %.2f mm   z>1.10 max %.2f mm' % (1000 * d[g].max(), 1000 * d[CO0[:, 2] < 1.06].max(), 1000 * d[CO0[:, 2] > 1.10].max()))


def boards(tag, looks=('soft',)):
    import board3
    outs = []
    for look in looks:
        lk = SOFT if look == 'soft' else 'matcap:clay_studio.exr'
        out = f'{HERE}/scratch/bd_{tag}_{look}.png'
        board3.board('chest', out, [('f3', 'data/co_FORM3_final.npy'), (tag, f'data/co_try_{tag}.npy')], look=lk)
        outs.append(out)
    return outs


if __name__ == '__main__':
    tag, pj = sys.argv[1], sys.argv[2]
    P = json.load(open(pj))
    co, dF, dB = build(P)
    assert np.isfinite(co).all()
    np.save(f'{HERE}/data/co_try_{tag}.npy', co)
    np.save(f'{HERE}/data/wc_try_{tag}.npy', np.stack([dF, dB]))
    report(co, tag)
    if '--board' in sys.argv:
        k = sys.argv[sys.argv.index('--board') + 1]
        print(boards(tag, ('soft', 'clay') if k == 'both' else (k,)))
    if '--sec' in sys.argv:
        os.system(f'python3 {HERE}/tools/section.py front scratch/sec_{tag}.png 1.14,1.18,1.21,1.24,1.27,1.31 data/orig_co.npy:orig data/co_FORM3_final.npy:f3 data/co_try_{tag}.npy:{tag}')

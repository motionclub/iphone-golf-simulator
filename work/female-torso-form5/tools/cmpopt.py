"""cmpopt.py : quick visual check of optimiser outputs.
python3 tools/cmpopt.py bust|glute out.png tag=P.json ...   (builds coords from the full param json with the stored wall corrections)"""
import sys, os, json
sys.path.insert(0, os.path.dirname(__file__))
import numpy as np
from torso3 import *
import quickgate
from big3 import big
from photo3 import *
HERE = str(WD)


def build_from_json(pj):
    P = json.load(open(pj if pj.startswith('/') else f'{HERE}/{pj}'))
    P = {**DEFAULT3, **P}
    dF, dB = fit_walls(P, iters=4, verbose=False, zlo=0.82, zhi=1.30, fz=(0.82, 1.12), bz=(0.82, 1.30))
    return P, build3(P, dF, dB)


if __name__ == '__main__':
    part, out = sys.argv[1], sys.argv[2]
    items = []
    for a in sys.argv[3:]:
        tag, pj = a.split('=', 1)
        P, co = build_from_json(pj)
        np.save(f'{HERE}/data/co_cmp_{tag}.npy', co)
        r = quickgate.quick(co, verbose=False)
        lt = np.array(LIGHT); lt[1:] *= 2.5 if part == 'bust' else 2.0
        view, box = ('front', roi_box('front', -0.115, 0.115, 1.14, 1.30)) if part == 'bust' else ('back', roi_box('back', -0.14, 0.14, 0.80, 0.97))
        c = compare(co, view, box, light=lt)
        print(tag, 'quick', r['QUICK_PASS'], 'arm', r['step_arm_mm'], 'legs', r['step_legs_mm'], 'dih40', r['dih_gt40'], 'contour F/B mean', r['contour_front_mean_mm'], r['contour_back_mean_mm'], 'max', r['contour_front_max_mm'], r['contour_back_max_mm'], '| NCC', round(c['ncc'], 3), 'amp', round(c['amp_ratio'], 2))
        items.append((tag, f'data/co_cmp_{tag}.npy'))
    chestlook = 'matcap:' + HERE + '/tools/matcap_platefit_g22.png'
    big('chest' if part == 'bust' else 'pelvis', out, items, enh=1.0, px=480, look=chestlook)
    big('chest' if part == 'bust' else 'pelvis', out.replace('.png', '_clay.png'), items, enh=1.0, px=480, look='matcap:clay_studio.exr')

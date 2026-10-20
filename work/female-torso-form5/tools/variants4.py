"""variants4.py: build several param variants (overrides of a base json) and render ONE contact sheet: rows = views, cols = plate | variants.
python3 tools/variants4.py out.png base.json look(soft|clay) name:'{"bm_H":0.03}' name2:'{...}' ...   (overrides can reach into bm_list[0] via "bm0.H": value)"""
import sys, os, json, copy
sys.path.insert(0, os.path.dirname(__file__))
import numpy as np
import run4, board3
from run4 import *

def apply(P, ov):
    P = copy.deepcopy(P)
    for k, v in ov.items():
        if k.startswith('bm0.'):
            P['bm_list'][0][k[4:]] = v
        elif k.startswith('bm1.'):
            P['bm_list'][1][k[4:]] = v
        else:
            P[k] = v
    return P

if __name__ == '__main__':
    out, base, look = sys.argv[1], sys.argv[2], sys.argv[3]
    P0 = json.load(open(base))
    items = []
    for a in sys.argv[4:]:
        name, _, js = a.partition(':')
        ov = json.loads(js) if js else {}
        P = apply(P0, ov)
        co, dF, dB = build(P)
        np.save(f'{HERE}/data/co_try_{name}.npy', co)
        json.dump(P, open(f'{HERE}/data/P_try_{name}.json', 'w'), indent=1)
        r = report.__wrapped__(co, name) if hasattr(report, '__wrapped__') else None
        items.append((name, f'data/co_try_{name}.npy'))
        bs = seam.border_steps(co)[0]
        fe = env_front(co, 1.22)[0]; 
        print(f'{name}: apex(1.22) {1000*fe:+.1f} mm | steps legs {bs["legs"]["max_mm"]:.2f} arm {bs["arm"]["max_mm"]:.2f} top {bs["top"]["max_mm"]:.2f}')
    lk = SOFT if look == 'soft' else 'matcap:clay_studio.exr'
    board3.board('chest', out, items, look=lk)

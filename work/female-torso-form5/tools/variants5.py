"""variants5.py: build chest variants with the FORM5 bust field and render a zoom contact sheet (plate | variants; rows front, 3/4 L, 3/4 R, side).
python3 tools/variants5.py out.png base.json soft|clay name:'{"b5.H":0.02}' name2:'{...}' ...      (a leading '@' in a name = reuse data/co5_<name>.npy)"""
import sys, os, json, time
sys.path.insert(0, os.path.dirname(__file__))
import numpy as np
import torso5 as t5
import torso4 as t4
import zoom4
from run4 import HERE, env_front, FF
import seam
import cres5


def report(co, name):
    fe = lambda z: env_front(co, z)[0]
    pf = lambda z: float(np.interp(z, FF[0], FF[1]))
    s = ' '.join(f'{z:.2f}:{1000*(fe(z)-pf(z)):+5.1f}' for z in (1.16, 1.18, 1.20, 1.22, 1.24, 1.26, 1.28, 1.30))
    bs = seam.border_steps(co)[0]
    print('   ', cres5.line(co))
    print(f'{name}: apex(1.22) {1000*fe(1.22):+.1f} (plate {1000*pf(1.22):+.1f}) | env-plate mm  {s} | steps legs {bs["legs"]["max_mm"]:.1f} arm {bs["arm"]["max_mm"]:.1f} top {bs["top"]["max_mm"]:.2f}')


def build_variant(P0, name, ov, save=True):
    P = t5.apply_ov(P0, ov)
    t0 = time.time()
    co, dF, dB = t5.build_chest(P)
    if save:
        np.save(f'{HERE}/data/co5_{name}.npy', co)
        json.dump(P, open(f'{HERE}/data/P5_{name}.json', 'w'), indent=1)
    report(co, name)
    return co


if __name__ == '__main__':
    out, base, look = sys.argv[1], sys.argv[2], sys.argv[3]
    P0 = json.load(open(base))
    items = []
    for a in sys.argv[4:]:
        name, _, js = a.partition(':')
        ov = json.loads(js) if js else {}
        build_variant(P0, name, ov)
        items.append((name, f'data/co5_{name}.npy'))
    zoom4.main(out, look, items)

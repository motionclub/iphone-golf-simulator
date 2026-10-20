"""scan6b.py: like scan6 but reports the HIGH-PASS fold trace (bandtrace5) centre z (cm) per column + hp depth. python3 tools/scan6b.py '{"rza":[.85,.87]}' ['{fixed}']"""
import sys, os, json, itertools
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import foldx5 as fx
import bandtrace5 as bt
from fplate import BALD
XS = (0.03, 0.045, 0.06, 0.075, 0.09, 0.105, 0.12, 0.135)
box = fx.BOX; c0, r0, c1, r1 = box
plate = np.asarray(BALD[r0:r1, c0:c1], dtype=np.float32)
TP = bt.trace(plate, box, XS)
def tr(co, gain=1.5):
    img, _ = fx.render(co, gain, box); return bt.trace(np.asarray(img, dtype=np.float32), box, XS)
def row(tag, t, extra=''):
    print(f'{tag:34s} z ' + ' '.join(f'{100*v[0]:5.1f}' for v in t) + ' | dep ' + ' '.join(f'{v[1]:4.1f}' for v in t) + extra)
if __name__ == '__main__':
    grid = json.loads(sys.argv[1]); fixed = json.loads(sys.argv[2]) if len(sys.argv) > 2 else {}
    keys = list(grid.keys())
    row('PLATE', TP)
    for combo in itertools.product(*[grid[k] for k in keys]):
        over = dict(fixed); over.update(dict(zip(keys, combo)))
        co, PP = fx.build(over)
        zu = np.arange(0.70, 0.881, 0.02)
        dev = 1000 * (fx.benv5.env(co, zu) - np.interp(zu, fx.FB[0], fx.FB[1]))
        row(' '.join(f'{k}={v}' for k, v in zip(keys, combo)), tr(co), f' | env {np.abs(dev).max():.1f}')

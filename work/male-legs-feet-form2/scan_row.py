import sys, json, copy
sys.path.insert(0, '.')
import numpy as np
from ff_common import *
from ff_build import DEFAULT, ToeRow
import ff_assemble as A
from ff_slopes import slopes_fn
import metrics_ff as M
d = json.load(open('design_v11.json')); d.pop('relief')
base = dict(DEFAULT); base.update(d)
V1 = np.load('tmp/V1_b15.npy'); V0, F = load_base()
rows = []
def run(tag, **ov):
    P = copy.deepcopy(base); P.update(ov)
    set_origin(P['L'][0], lc_big=float(ToeRow(P).lc[0]))
    f_cut = float(to_local(np.array([[FRAME_ORIGIN[0], -0.095, 0.0]]), +1)[0, 0])
    Vn, Fn, meta, cuts, builds = A.assemble(V1, F, P=P, f_cut=f_cut, slopes_fn=slopes_fn, verbose=False)
    s = M.silhouettes(Vn, Fn, views=('bald_front', 'bald_back', 'sheet_front', 'sheet_back'))
    c = M.contour_error(Vn, Fn)
    tot = s['bald_front']['total'] + s['bald_back']['total']
    print(f"{tag:28s} front {s['bald_front']['total']:.2f} back {s['bald_back']['total']:.2f} sum {tot:.2f} | sheet f {s['sheet_front']['total']:.2f} b {s['sheet_back']['total']:.2f} | contour mean {c['mean_mm']:.3f} cap {c['cap_mean_mm']:.2f}")
W0 = base['W']
run('base (shift 0, W x1.0)')
for sh in (-0.003, -0.006):
    run(f'shift {sh*1000:+.0f}mm', row_shift=sh)
for sc in (0.94,):
    run(f'W x{sc}', W=[w*sc for w in W0])
run('shift -4mm W x0.95', row_shift=-0.004, W=[w*0.95 for w in W0])
run('shift -6mm W x0.92', row_shift=-0.006, W=[w*0.92 for w in W0])
run('T5 splay 3 shift -3', row_shift=-0.003, splay_deg=[-2, 0.5, 2, 3, 3])

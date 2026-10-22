"""Micro1i edit chain: Micro1h start (h0) -> V_final.   python3.13 chain.py <out_tag> [stage1]
 e1 chin 3/4-tangent shave -> e2n nose (narrow bridge, wide wings) -> [PMO broad relief, contour-constrained: pmo_run3.py c2 c3 10 8 80 4.5 30 8]
 -> e3 lower-face fairing -> e3b chin-band fairing -> e4 interior relief -> e5 cheek/smile modelling -> e8 mouth on the carved loops -> e7 alar fairing
 -> e2v ear rebuilt from scratch (clean skull base, rolled helix rim, absolute crest targets).   Every step keeps topology; z<1.444 untouched (bit-identical)."""
import sys, json, subprocess, time
sys.path.insert(0, '.')
import numpy as np
out = sys.argv[1] if len(sys.argv) > 1 else 'i2'
W = '.'
t0 = time.time()
from edlib import *
V0, F, loops = load('h0'); M = Mesh(V0, F)
import ed1, ed2, ed3, ed4, ed5
V = ed1.e1_shave(V0, M); np.save('data/V_c1.npy', V); print('e1 done', round(time.time() - t0))
import ed2n
V = ed2n.e2n_nose(V); np.save('data/V_c2.npy', V); print('e2+e2n done', round(time.time() - t0))
if len(sys.argv) > 2 and sys.argv[2] == 'stage1': sys.exit(0)

# ---- stage 2 (after the PMO run: python3.13 pmo_run3.py c2 c3 10 8 80 4.5 30 8)
if len(sys.argv) > 2 and sys.argv[2] == 'stage1': sys.exit(0)
V = np.load('data/V_c3.npy')
V = ed3.e3_clean(V, M, iters=14); np.save('data/V_c4.npy', V); print('e3 done', round(time.time() - t0))
V = ed3.e3b_chinband(V, M, 25); np.save('data/V_c5.npy', V); print('e3b done', round(time.time() - t0))
V, _ = ed4.e4(V, F, M, loops, prm={'jaw_groove': {'depth': 1.2, 'sigma': 5.5}}); np.save('data/V_c6.npy', V); print('e4 done', round(time.time() - t0))
V, _ = ed5.e5(V, F, M, prm={'apple': {'amp': 2.2, 'cx': 43, 'rx': 12, 'rz': 9.5}, 'bunch': {'amp': 1.4}, 'lidpuff': {'amp': 1.0}, 'cheek_soft': {'amp': 1.0}}); np.save(f'data/V_{out}.npy', V); print('e6 done', round(time.time() - t0))

import ed8
V, _ = ed8.e8_mouth(V, F, M, loops); print('e8 mouth done', round(time.time() - t0))
import ed7
V = ed7.e7_nose_fair(V, M); print('e7 nose fair done', round(time.time() - t0))
import ed2v
V = ed2v.e2v_ear(V, M, loops=loops); np.save(f'data/V_{out}.npy', V); print('ear rebuild done', round(time.time() - t0))

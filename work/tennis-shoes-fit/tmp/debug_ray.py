import sys, os, json
sys.path.insert(0, '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/tennis-shoes-fit/scripts')
import numpy as np, bpy, math
from kitlib import *
from checklib import *
z = np.load(f'{WORK}/data/body_female_a1d73a33.npz'); VB, FB = z['V'], z['F']
sk = np.load(f'{WORK}/data/sockR_female.npz'); Vk, Fk = sk['V'], sk['F']
print('sock top', Vk[:, 2].max())
tree_sk = bvh(Vk, Fk, 2e-4)
s = np.array([0.0604, 0.0252, 0.2739])
for el, az in ((45, 0.0), (45, 225.0), (45, 195.0)):
    a = math.radians(az); ce, se = math.cos(math.radians(el)), math.sin(math.radians(el))
    d = np.array([math.sin(a) * ce, -math.cos(a) * ce, se])
    far = s + d * 3
    h = tree_sk.ray_cast(far.tolist(), (-d).tolist())
    t_exact = mt_first(Vk, Fk, far, -d)
    print('el', el, 'az', az, 'dir', d.round(3), 'bvh hit', None if h[2] is None else (round(h[3], 4), np.round(h[0], 4).tolist()), 'exact first t', t_exact, ' (R - t = distance from s)', None if t_exact is None else round(3 - t_exact, 4))
# distance of the sock surfaces to the skin point
loc, n, idx, dist = tree_sk.find_nearest(s.tolist())
print('nearest sock surface to s', dist, np.round(loc, 4).tolist())
# horizontal profile of the sock around s at this height: slice z=0.2739 and z=0.2867
from slicer import slice_loops
for zz in (0.274, 0.280, 0.285, 0.2865):
    ls = [L for L in slice_loops(Vk, Fk, zz) if len(L) > 6]
    print('z', zz, 'sock loops', [(len(L), L[:, 0].min().round(4), L[:, 0].max().round(4), L[:, 1].min().round(4), L[:, 1].max().round(4)) for L in ls])
    ls = [L for L in slice_loops(VB, FB, zz) if len(L) > 6 and L[:, 0].mean() > 0.02]
    print('   body loops', [(len(L), L[:, 0].min().round(4), L[:, 0].max().round(4), L[:, 1].min().round(4), L[:, 1].max().round(4)) for L in ls])

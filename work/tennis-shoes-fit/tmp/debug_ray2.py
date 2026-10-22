import sys, os, json
sys.path.insert(0, '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/tennis-shoes-fit/scripts')
import numpy as np, bpy, math
from kitlib import *
from checklib import *
z = np.load(f'{WORK}/data/body_female_a1d73a33.npz'); VB, FB = z['V'], z['F']
sk = np.load(f'{WORK}/data/sockR_female.npz'); Vk, Fk = sk['V'], sk['F']

def all_hits(V, F, o, d):
    a, b, c = V[F[:, 0]], V[F[:, 1]], V[F[:, 2]]
    e1, e2 = b - a, c - a
    h = np.cross(d[None, :], e2)
    det = np.einsum('ij,ij->i', e1, h)
    ok = np.abs(det) > 1e-14
    f = np.where(ok, 1.0 / np.where(ok, det, 1.0), 0)
    s = o[None, :] - a
    u = f * np.einsum('ij,ij->i', s, h)
    q = np.cross(s, e1)
    v = f * (q @ d)
    t = f * np.einsum('ij,ij->i', e2, q)
    hit = ok & (u >= -1e-9) & (v >= -1e-9) & (u + v <= 1 + 1e-9)
    return np.sort(t[hit])
s = np.array([0.0604, 0.0252, 0.2739])
for el, az in ((45, 0.0),):
    a = math.radians(az); ce, se = math.cos(math.radians(el)), math.sin(math.radians(el))
    d = np.array([math.sin(a) * ce, -math.cos(a) * ce, se])
    print('hits of the line s + t*d on the sock (t>0 = toward the camera):', np.round(all_hits(Vk, Fk, s, d), 4).tolist())
    print('hits on the body:', np.round(all_hits(VB, FB, s, d), 4).tolist()[:10])
# which body triangle contains s? normal there
tree = bvh(VB, FB)
loc, n, idx, dist = tree.find_nearest(s.tolist())
print('nearest body point', np.round(loc, 4).tolist(), 'normal', np.round(n, 3).tolist(), 'dist', dist)
print('n.d', float(np.dot(n, d)))

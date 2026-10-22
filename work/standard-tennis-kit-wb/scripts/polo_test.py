"""First rough male polo shell: constant ease, SDF surface nets, clips.  (exploration)"""
import sys, time, json
sys.path.insert(0, '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/standard-tennis-kit-wb/scripts')
import numpy as np, bpy
from kitlib import *
from sdf import *
from fitbody import *
import scene_utils as su

t00 = time.time()
bodies = load_set('male')
auth = bodies[0]
V, F = auth['V'], auth['F']

# ---- arm axes (right arm; left = mirror)
C0, d0 = arm_axis(V, (0.25, -0.04, 1.30), (0.72, -0.03, -0.69), s_range=(0.04, 0.30))
print("right arm axis C0", C0.round(4), "dir", d0.round(4), "angle from vertical deg", np.degrees(np.arccos(-d0[2])).round(1))

lo, hi = (-0.52, -0.30, 0.80), (0.52, 0.22, 1.60)
g, S = cached_sdf('male', bodies, lo, hi, 0.006, 'polo')
X, Y, Z = g.coords()

ease = 0.015
Sg = gauss3(S - ease, 2.5)
Sg = np.minimum(Sg, S - 0.0025)
Vq, Q = surface_nets(Sg, g)
T = quads_to_tris(Vq, Q)
print("raw shell tris", len(T), "verts", len(Vq), f"{time.time()-t00:.1f}s")

# ---- clips
x, y, z = Vq[:, 0], Vq[:, 1], Vq[:, 2]
c_hem = 0.95 - z
c_neck = np.minimum(0.095 - np.sqrt((x / 0.088 * 0.095) ** 2 + ((y + 0.02) / 0.095 * 0.095) ** 2), z - (1.43 + 0.30 * (y + 0.02)))
sleeve_end = 0.13
def sleeve_c(P, sign):
    Cc = C0 * np.array([sign, 1, 1])
    dd = d0 * np.array([sign, 1, 1])
    return (P - Cc) @ dd - sleeve_end
c = np.maximum.reduce([c_hem * 0 + c_hem, ])  # placeholder to keep shape
# combine: remove if any cut says so  -> c_any = max over cuts of "outside" functions, each positive means remove
c_any = np.maximum.reduce([c_hem, c_neck, sleeve_c(Vq, +1), sleeve_c(Vq, -1)])
V2, F2, _, _ = clip_mesh(Vq, T, c_any)
V2, F2 = keep_largest(V2, F2)
print("after clips tris", len(F2), "loops", [len(l) for l in boundary_loops(F2)])
np.savez(f'{WORK}/tmp/polo_male_test.npz', V=V2, F=F2)

out = su.preview((V, F), [('Polo', V2, F2, (0.95, 0.95, 0.95))], f'{WORK}/tmp/polo_male_test', views=(('front', 0, 3), ('q3', 38, 4), ('side', 90, 3)), res=(520, 760))
print(out, f"{time.time()-t00:.1f}s total")

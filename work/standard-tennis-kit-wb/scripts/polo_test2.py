"""Male polo v1: ease taper, arm/torso split sleeve cut, 12 mm grid."""
import sys, time, json
sys.path.insert(0, '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/standard-tennis-kit-wb/scripts')
import numpy as np, bpy
from kitlib import *
from sdf import *
from fitbody import *
import scene_utils as su

t00 = time.time()
H = float(sys.argv[sys.argv.index('--')+1]) if '--' in sys.argv else 0.012
bodies = load_set('male')
auth = bodies[0]
V, F = auth['V'], auth['F']
C0, d0 = arm_axis(V, (0.25, -0.04, 1.30), (0.72, -0.03, -0.69), s_range=(0.04, 0.30))
axR = (C0, d0); axL = mirror_axis(C0, d0)
sleeve_end = 0.135

lo, hi = (-0.52, -0.30, 0.80), (0.52, 0.22, 1.60)
g, S = cached_sdf('male', bodies, lo, hi, H, 'polo')
X, Y, Z = g.coords()
ease = 0.005 + 0.011 * smoothstep(0.98, 1.10, Z)          # taper to the waist (tucked into the shorts)
Sg = gauss3(S - ease, 15e-3 / H)
Sg = np.minimum(Sg, S - 0.0025)
Vq, Q = surface_nets(Sg, g)
T = quads_to_tris(Vq, Q)
print("raw shell tris", len(T), f"{time.time()-t00:.1f}s")

# group trees for the sleeve cut (union over body variants: compute per variant and take min distance)
dA = np.full(len(Vq), 1e3); dT = np.full(len(Vq), 1e3)
for b in bodies:
    m = arm_vertex_mask(b['V'], [axR, axL], 0.075, sleeve_end - 0.065)
    ta, tt = split_trees(b['V'], b['F'], m)
    dA = np.minimum(dA, tree_dist(ta, Vq)); dT = np.minimum(dT, tree_dist(tt, Vq))
x, y, z = Vq[:, 0], Vq[:, 1], Vq[:, 2]
def beyond(P, ax):
    return (P - ax[0]) @ ax[1] - sleeve_end
c_sleeve = np.minimum(np.maximum(beyond(Vq, axR), beyond(Vq, axL)), dT - dA)
c_hem = 0.93 - z
c_neck = np.minimum(0.095 - np.sqrt((x / 0.088 * 0.095) ** 2 + ((y + 0.02) / 0.095 * 0.095) ** 2), z - (1.43 + 0.30 * (y + 0.02)))
c_any = np.maximum.reduce([c_hem, c_neck, c_sleeve])
V2, F2, _, _ = clip_mesh(Vq, T, c_any)
V2, F2 = keep_largest(V2, F2)
print("after clips tris", len(F2), "loops", [len(l) for l in boundary_loops(F2)], f"{time.time()-t00:.1f}s")
np.savez(f'{WORK}/tmp/polo_male_v1.npz', V=V2, F=F2)
bpy.ops.wm.read_factory_settings(use_empty=True)
out = su.preview((V, F), [('Polo', V2, F2, (0.95, 0.95, 0.95))], f'{WORK}/tmp/polo_male_v1', views=(('front', 0, 3), ('q3', 38, 4), ('side', 90, 3), ('back', 180, 3)), res=(520, 760))

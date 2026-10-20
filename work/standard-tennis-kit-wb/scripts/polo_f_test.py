"""Female polo v1 (exploration): hanging arms, arm/torso split sleeve cut."""
import sys, time
sys.path.insert(0, '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/standard-tennis-kit-wb/scripts')
import numpy as np, bpy
from kitlib import *
from sdf import *
from fitbody import *
from shell import build_shell
import scene_utils as su

H = 0.012
bodies = load_set('female')
for b in bodies:
    C, d = arm_axis(b['V'], (0.17, -0.0, 1.25), (0.06, 0.0, -1.0), s_range=(0.04, 0.26), r=0.05)
    b['axR'] = (C, d); b['axL'] = mirror_axis(C, d)
    print(b['name'], "arm axis C", C.round(3), "d", d.round(3), "angle", np.degrees(np.arccos(-d[2])).round(1))
auth = bodies[0]
sleeve_end = 0.115     # from C along the axis (C is near z~1.27 -> end ~1.16)
R_ARM = 0.047

lo, hi = (-0.40, -0.25, 0.80), (0.40, 0.22, 1.60)
def ease_fn(X, Y, Z):
    return 0.004 + 0.008 * smoothstep(0.95, 1.12, Z)

def cut_fn(P):
    x, y, z = P[:, 0], P[:, 1], P[:, 2]
    # per-variant sleeve cut: remove (beyond that variant's plane) AND (closer to that variant's arm than to its torso); union over variants
    c_sleeve = np.full(len(P), -1e3)
    for b in bodies:
        m = arm_vertex_mask(b['V'], [b['axR'], b['axL']], R_ARM, sleeve_end - 0.06)
        ta, tt = split_trees(b['V'], b['F'], m)
        dA = tree_dist(ta, P); dT = tree_dist(tt, P)
        bey = np.maximum((P - b['axR'][0]) @ b['axR'][1], (P - b['axL'][0]) @ b['axL'][1]) - sleeve_end
        c_sleeve = np.maximum(c_sleeve, np.minimum(bey, dT - dA))
    c_hem = 0.93 - z
    c_neck = np.minimum(0.078 - np.sqrt(x ** 2 + (y + 0.005) ** 2), z - (1.375 + 0.25 * (y + 0.005)))
    return np.maximum.reduce([c_hem, c_neck, c_sleeve])

sh = build_shell(bodies, 'female', 'polo', lo, hi, H, ease_fn, blur_mm=14, cut_fn=cut_fn)
np.savez(f'{WORK}/tmp/polo_female_v1.npz', V=sh.V, F=sh.F)
bpy.ops.wm.open_mainfile(filepath=FEMALE_BLEND)
Vb, Fb = mesh_arrays(bpy.data.objects['Body_F'])
bpy.ops.wm.read_factory_settings(use_empty=True)
su.preview((Vb, Fb), [('Polo', sh.V, sh.F, (0.95, 0.95, 0.95))], f'{WORK}/tmp/polo_female_v1', views=(('front', 0, 3), ('q3', 38, 4), ('side', 90, 3), ('back', 180, 3)), res=(520, 760))

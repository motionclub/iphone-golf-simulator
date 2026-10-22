"""Male shorts v1 (exploration)."""
import sys, time
sys.path.insert(0, '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/standard-tennis-kit-wb/scripts')
import numpy as np, bpy
from kitlib import *
from sdf import *
from fitbody import *
from shell import build_shell
import scene_utils as su

H = 0.010
bodies = load_set('male')
V, F = bodies[0]['V'], bodies[0]['F']
Z_WT, Z_WB = 1.015, 0.972           # waistband top / bottom


def ease_fn(X, Y, Z):
    e_hip = 0.015 + 0.0 * Z
    leg = 0.015 + 0.012 * smoothstep(0.80, 0.60, Z)
    e = np.where(Z > 0.85, e_hip, leg)
    e = 0.015 + 0.0 * Z + 0.012 * smoothstep(0.80, 0.58, Z)
    band = 0.003 * smoothstep(Z_WB - 0.004, Z_WB + 0.004, Z)
    return e + band


def cut_fn(P):
    x, y, z = P[:, 0], P[:, 1], P[:, 2]
    c_top = z - Z_WT
    z_hem = 0.575 + 0.02 * smoothstep(0.10, 0.21, np.abs(x))
    c_hem = z_hem - z
    return np.maximum(c_top, c_hem)


sh = build_shell(bodies, 'male', 'shorts', (-0.34, -0.28, 0.46), (0.34, 0.20, 1.10), H, ease_fn, blur_mm=14, cut_fn=cut_fn)
np.savez(f'{WORK}/tmp/shorts_male_v1.npz', V=sh.V, F=sh.F)
bpy.ops.wm.read_factory_settings(use_empty=True)
poloz = np.load(f'{WORK}/tmp/polo_male_v1.npz')
su.preview((V, F), [('Shorts', sh.V, sh.F, (0.95, 0.95, 0.95)), ('Polo', poloz['V'], poloz['F'], (0.9, 0.9, 0.95))], f'{WORK}/tmp/shorts_male_v1',
           views=(('front', 0, 3), ('q3', 38, 4), ('side', 90, 3), ('back', 180, 3)), res=(520, 760))

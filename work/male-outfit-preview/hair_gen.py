"""Procedural opaque hairstyles for the preview (solid shells over the scalp, art-bible: sculpted opaque clumps)."""
import math, random
import numpy as np
import bpy
from mathutils import Vector
from preview_common import get_collection, clear_collection, make_mesh_obj
import outfit as of
import shader_zones as sz

YC = -0.045
STYLES = ['buzz', 'quiff', 'curly', 'mohawk', 'side_part', 'slick_back']


def sm(a, b, x):
    return of.sm01(a, b, x)


def phi_of(P):
    """0 at the forehead, 90 at the sides, 180 at the back"""
    return np.degrees(np.arctan2(np.abs(P[:, 0]), -(P[:, 1] - YC)))


def hairline(P, front=1.640, side=0.012, back=0.075, nape=None):
    ph = phi_of(P)
    hl = front - side * sm(35, 85, ph) - back * sm(100, 160, ph)
    return hl


def noise(P, f=90.0, seed=0):
    x, y, z = P[:, 0] + seed, P[:, 1], P[:, 2]
    return (np.sin(f * x + 1.3) * np.sin(f * 0.8 * y + 0.4) * np.sin(f * 1.1 * z + 2.1) + 0.5 * np.sin(f * 2.3 * x - f * 1.7 * z)) / 1.5


def make_style(B, coll, mat, style, seed=0):
    rnd = random.Random(seed)
    if style == 'buzz':
        hl = lambda P: hairline(P, 1.638, 0.012, 0.070)
        d = lambda P0, idx: 0.0045 + 0.0 * P0[:, 2]
        thick = 0.0035
    elif style == 'quiff':
        hl = lambda P: hairline(P, 1.646, 0.010, 0.068)

        def d(P0, idx):
            ph = phi_of(P0); z = P0[:, 2]
            base = 0.009 + 0.004 * sm(1.60, 1.69, z)
            front = 0.028 * (1 - sm(0, 55, ph)) * sm(1.62, 1.66, z)           # swept-up front mass
            return base + front
        thick = 0.006
    elif style == 'curly':
        hl = lambda P: hairline(P, 1.640, 0.014, 0.060)

        def d(P0, idx):
            n = noise(P0, 110.0, seed * 0.01)
            return 0.014 + 0.0055 * n + 0.004 * sm(1.60, 1.70, P0[:, 2])
        thick = 0.007
    elif style == 'mohawk':
        hl = lambda P: hairline(P, 1.636, 0.010, 0.062)

        def d(P0, idx):
            ax = np.abs(P0[:, 0]); ph = phi_of(P0)
            strip = (1 - sm(0.016, 0.034, ax)) * (1 - sm(150, 175, ph))
            return 0.003 + 0.042 * strip * (0.85 + 0.15 * np.sin(60 * P0[:, 1]))
        thick = 0.004
    elif style == 'side_part':
        hl = lambda P: hairline(P, 1.645, 0.006, 0.058)

        def d(P0, idx):
            x = P0[:, 0]; z = P0[:, 2]; ph = phi_of(P0)
            part = 1 - 0.55 * np.exp(-((x - 0.028) / 0.006) ** 2) * (1 - sm(60, 110, ph))
            vol = 0.011 + 0.012 * sm(1.60, 1.68, z) * (1 - sm(-0.02, 0.07, x)) * (1 - sm(40, 120, ph))
            return vol * part
        thick = 0.006
    else:  # slick_back
        hl = lambda P: hairline(P, 1.650, 0.004, 0.050)

        def d(P0, idx):
            ph = phi_of(P0); z = P0[:, 2]
            return 0.009 + 0.010 * sm(1.60, 1.70, z) + 0.006 * sm(90, 150, ph) * sm(1.56, 1.66, z)
        thick = 0.006
    obj, info = of.build_shell(B, 'Hair_' + style,
                               lambda V: (V[:, 2] >= hl(V)) & (V[:, 2] > 1.48) & (np.abs(V[:, 0]) < 0.13),
                               d, None, [mat], coll,
                               snaps=[of.func_snap(lambda P: P[:, 2] < hl(P) + 0.03, lambda P: hl(P))],
                               thickness=thick, min_gap=0.003, smooth_iters=9 if style != 'curly' else 3, pin_boundary=True)
    return obj, info


def random_hair(B, coll, colorway_hex='#241810', seed=None):
    seed = random.randrange(10 ** 6) if seed is None else seed
    rnd = random.Random(seed)
    style = rnd.choice(STYLES)
    colors = ['#241810', '#3A2414', '#6B4A2B', '#1A1A1E', '#B5753A', '#C9A36B', '#8C2F1F']
    hx = rnd.choice(colors)
    mat = sz.build_material('Outfit_Hair', hx, [('fade', '#7A5340', lambda Z: Z.inv(Z.up(Z.z, 1.574, 0.035)))], rough=.55, spec=.35)
    obj, info = make_style(B, coll, mat, style, seed)
    return dict(style=style, color=hx, seed=seed, object=obj.name)

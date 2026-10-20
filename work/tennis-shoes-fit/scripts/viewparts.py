"""Render the staged npz parts (data/shoe{R,L}_<g>.npz, sock{R,L}_<g>.npz) on the SHA-verified body dump.
blender -b --factory-startup --python viewparts.py -- <male|female> <White|Black> <out_prefix> <preset> [feet=R,L] [parts=shoe,sock] [body=1|0]
Env: VDIST VLENS VRES VTZ (see below).  Presets: foot (4 views of one foot), both (front/back/side of both feet), sheet = everything."""
import sys, os, math, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import bpy
from kitlib import *
import render_setup as rs
from preview_common import material

WHITE = (0.93, 0.93, 0.93)
BLACK = (0.035, 0.035, 0.04)
SKIN = (0.80, 0.60, 0.46)
BODY_NPZ = {'male': f'{WORK}/data/body_male_d6c4dcfb.npz', 'female': f'{WORK}/data/body_female_a1d73a33.npz'}


def kit_mats(cw):
    w = material('Std_White_Lit', WHITE, .62, .25)
    b = material('Std_Black_Lit', BLACK, .55, .25)
    return [w, w] if cw == 'White' else [b, w]


def mesh_obj(name, V, F, mats, M=None, LN=None):
    me = bpy.data.meshes.new(name)
    me.from_pydata(np.asarray(V, float).tolist(), [], np.asarray(F, int).tolist())
    me.update()
    for m in mats:
        me.materials.append(m)
    if M is not None:
        me.polygons.foreach_set('material_index', np.minimum(np.asarray(M, np.int32), len(mats) - 1))
    me.polygons.foreach_set('use_smooth', np.ones(len(me.polygons), bool))
    if LN is not None:
        try:
            me.normals_split_custom_set(np.asarray(LN, float).reshape(-1, 3).tolist())
        except Exception as e:
            print('custom normals failed', name, e)
    o = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(o)
    return o


def load_part(path):
    z = np.load(path)
    return {k: z[k] for k in z.files}


def clip_part(d, c_fn, has_normals=True):
    """exact plane clip of a part (c > 0 removed); per-corner normals follow the triangles (corner values re-used for the kept triangles; cut triangles use face normals)."""
    from sdf import clip_mesh
    V, F, M = d['V'], d['F'], d['M']
    c = c_fn(V)
    out = c > 0
    nout = out[F].sum(1)
    keep = nout == 0
    mixed = (nout == 1) | (nout == 2)
    # fully kept triangles keep their normals; mixed ones are re-triangulated by clip_mesh (flat normals)
    Vk, Fk, _, _ = clip_mesh(V, F[mixed], c)
    Fa = F[keep]
    LNa = d['LN'].reshape(-1, 3, 3)[keep].reshape(-1, 3) if 'LN' in d else None
    Ma = M[keep]
    # cut part: material of the source triangle is lost by clip_mesh; use slot of the nearest kept face (0)
    Vall = np.concatenate([V, Vk])
    Fall = np.concatenate([Fa, Fk + len(V)])
    Mall = np.concatenate([Ma, np.zeros(len(Fk), int)])
    return dict(V=Vall, F=Fall, M=Mall, LN=None)


def build_scene(gender, cw, feet=('R', 'L'), parts=('shoe', 'sock'), body=True, clip=None, skin=SKIN):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    mats = kit_mats(cw)
    zmin = 0.0
    objs = {}
    z = np.load(BODY_NPZ[gender])
    VB, FB = z['V'], z['F']
    if body:
        bm = material('Body_skin', skin, .55, .3)
        if clip:
            d = clip_part(dict(V=VB, F=FB, M=np.zeros(len(FB), int)), clip['fn'])
            ob = mesh_obj('Body', d['V'], d['F'], [bm], d['M'])
        else:
            ob = mesh_obj('Body', VB, FB, [bm], None)
        objs['Body'] = ob
    for kind in parts:
        for f in feet:
            d = load_part(f'{WORK}/data/{kind}{f}_{gender}{os.environ.get("PART_TAG", "") if kind == "shoe" else ""}.npz')
            if kind == 'shoe':
                zmin = min(zmin, float(d['V'][:, 2].min()))
            if clip:
                dd = clip_part(d, clip['fn'])
                o = mesh_obj(f'{kind}{f}', dd['V'], dd['F'], mats, dd['M'], dd['LN'])
            else:
                o = mesh_obj(f'{kind}{f}', d['V'], d['F'], mats, d['M'], d['LN'])
            objs[f'{kind}{f}'] = o
    return objs, VB, FB, zmin


def foot_center(VB, side):
    m = (VB[:, 0] * side > 0.02) & (VB[:, 2] < 0.035)
    P = VB[m]
    return np.array([P[:, 0].mean(), 0.5 * (P[:, 1].min() + P[:, 1].max()), 0.07])


if __name__ == '__main__':
    args = sys.argv[sys.argv.index('--') + 1:]
    gender, cw, prefix, preset = args[:4]
    kv = dict(a.split('=') for a in args[4:] if '=' in a)
    feet = tuple(kv.get('feet', 'R,L').split(','))
    parts = tuple(kv.get('parts', 'shoe,sock').split(','))
    body = kv.get('body', '1') == '1'
    objs, VB, FB, zmin = build_scene(gender, cw, feet, parts, body)
    rs.setup(samples=int(os.environ.get('VSAMPLES', 48)))
    rs.set_floor_z(zmin)
    dist = float(os.environ.get('VDIST', 0.95))
    lens = float(os.environ.get('VLENS', 85))
    res = tuple(int(x) for x in os.environ.get('VRES', '640,640').split(','))
    tz = float(os.environ.get('VTZ', 0.095))
    if preset == 'foot':
        side = +1 if feet[0] == 'R' else -1
        c = foot_center(VB, side)
        views = [('side', 90 * side, 6), ('front', 0, 8), ('heel', 180, 8), ('q3', 38 * side, 14)]
        for nm, az, el in views:
            rs.shot(f'{prefix}_{nm}.png', (c[0], c[1], tz), az, el, dist=dist, lens=lens, res=res)
    elif preset == 'both':
        for nm, az, el in (('front', 0, 8), ('back', 180, 8), ('side', 90, 6), ('q3', 35, 14)):
            rs.shot(f'{prefix}_{nm}.png', (0, float(os.environ.get('VCY', -0.02)), tz), az, el, dist=dist, lens=lens, res=res)
    print('done', prefix, 'floor', zmin)

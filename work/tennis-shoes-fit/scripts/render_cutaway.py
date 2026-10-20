"""Cutaway renders of the DELIVERABLE blend: the foot, the sock and the shoe cut by a plane, cut faces capped and coloured by layer
(skin = brown, sock = blue, shoe = orange).   blender -b --factory-startup --python render_cutaway.py -- <male|female> <White|Black> <out_prefix>
Views: sagittal (plane through the foot axis), coronal (through the ankle), axial at the collar, axial through the toe box."""
import sys, os, math, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import bpy
from mathutils import Vector
from mathutils.geometry import tessellate_polygon
from kitlib import *
from sdf import clip_mesh, boundary_loops
import render_setup as rs
from preview_common import material

gender, cw, prefix = sys.argv[sys.argv.index('--') + 1:][:3]
NAME = 'Male' if gender == 'male' else 'Female'
bpy.ops.wm.open_mainfile(filepath=f'{WORK}/export/StandardKit_{NAME}.blend')
fit = [o for o in bpy.data.objects if o.name.startswith('FitRef_Body')][0]
VB, FB = mesh_arrays(fit)
shoe = bpy.data.objects[f'Kit_Shoe_R_{cw}']
sock = bpy.data.objects[f'Kit_Sock_R_{cw}']
Vs, Fs = mesh_arrays(shoe)
Vk, Fk = mesh_arrays(sock)


def point_in_poly(pt, poly):
    x, y = pt
    xs, ys = poly[:, 0], poly[:, 1]
    x2, y2 = np.roll(xs, -1), np.roll(ys, -1)
    cond = ((ys > y) != (y2 > y)) & (x < (x2 - xs) * (y - ys) / np.where(y2 - ys == 0, 1e-30, y2 - ys) + xs)
    return bool(cond.sum() % 2)


def cap(V, F, axis, value, toward, weld=False):
    """cap faces (new vertices, flat) for the boundary loops of a mesh clipped at the plane V[:, axis] == value; normals face `toward` (+1/-1 along axis)."""
    loops = [l for l in boundary_loops(F) if len(l) >= 3 and np.abs(V[l][:, axis] - value).max() < 2e-5]
    keep = [a for a in range(3) if a != axis]
    polys = [V[l][:, keep] for l in loops]
    area = [0.5 * np.sum(p[:, 0] * np.roll(p[:, 1], -1) - np.roll(p[:, 0], -1) * p[:, 1]) for p in polys]
    depth = [sum(point_in_poly(polys[i][0], polys[j]) for j in range(len(polys)) if j != i) for i in range(len(polys))]
    outs, holes = [], {}
    for i in range(len(polys)):
        if depth[i] % 2 == 0:
            outs.append(i)
            holes[i] = []
    for i in range(len(polys)):
        if depth[i] % 2 == 1:
            cands = [j for j in outs if point_in_poly(polys[i][0], polys[j])]
            if cands:
                holes[min(cands, key=lambda j: abs(area[j]))].append(i)
    CV, CF = [], []
    for o in outs:
        rings = [o] + holes[o]
        veclist = []
        idx = []
        for r_i, r in enumerate(rings):
            p = polys[r]
            ccw = area[r] > 0
            order = np.arange(len(p)) if (ccw == (r_i == 0)) else np.arange(len(p))[::-1]          # outer CCW, holes CW
            veclist.append([Vector((p[k, 0], p[k, 1], 0.0)) for k in order])
            idx.append([loops[r][k] for k in order])
        try:
            tris = tessellate_polygon(veclist)
        except Exception as e:
            print('tessellate failed', e)
            continue
        flat = [v for ring in idx for v in ring]
        if weld:                                                    # faces use the existing loop vertices -> the capped mesh is watertight
            for t in tris:
                a, b, c = flat[t[0]], flat[t[1]], flat[t[2]]
                n = np.cross(V[b] - V[a], V[c] - V[a])
                if n[axis] * toward < 0:
                    b, c = c, b
                CF.append((a, b, c))
            continue
        base = len(CV)
        pts = V[np.array(flat)]
        CV.extend(pts.tolist())
        for t in tris:
            a, b, c = (base + t[0], base + t[1], base + t[2])
            n = np.cross(np.array(CV[b]) - np.array(CV[a]), np.array(CV[c]) - np.array(CV[a]))
            if n[axis] * toward < 0:
                b, c = c, b
            CF.append((a, b, c))
    return np.array(CV).reshape(-1, 3), np.array(CF, int).reshape(-1, 3)


def clipped(V, F, axis, value, keep_sign):
    """keep the part with keep_sign*(V[:, axis] - value) >= 0."""
    c = -keep_sign * (V[:, axis] - value)
    V2, F2, _, _ = clip_mesh(V, F, c)
    return V2, F2


def leg_part(axis, value, keep_sign, zmax=0.40):
    """right leg of the body below zmax as a closed solid (clipped at z = zmax, capped), then clipped by the section plane."""
    sel = (VB[FB].mean(1)[:, 0] > 0.0) & (VB[FB].mean(1)[:, 2] < zmax + 0.05)
    Fl = FB[sel]
    used = np.unique(Fl)
    remap = -np.ones(len(VB), int)
    remap[used] = np.arange(len(used))
    V, F = VB[used], remap[Fl]
    V, F, _, _ = clip_mesh(V, F, V[:, 2] - zmax)
    from sdf import keep_largest
    V, F = keep_largest(V, F)
    Cv, Cf = cap(V, F, 2, zmax, +1, weld=True)
    F = np.concatenate([F, Cf])
    return V, F


def build(axis, value, keep_sign, zmax=0.40):
    """meshes of the three layers clipped by the plane; returns dict name -> (V, F, capV, capF)"""
    out = {}
    toward = -keep_sign
    for name, (V, F) in (('shoe', (Vs, Fs)), ('sock', (Vk, Fk)), ('leg', leg_part(axis, value, keep_sign, zmax))):
        V2, F2 = clipped(V, F, axis, value, keep_sign)
        # fill: the clipped open surface keeps the section loops as boundaries
        Cv, Cf = cap(V2, F2, axis, value, toward)
        out[name] = (V2, F2, Cv, Cf)
    return out


def mesh(name, V, F, mat, smooth=True):
    me = bpy.data.meshes.new(name)
    me.from_pydata(np.asarray(V, float).tolist(), [], np.asarray(F, int).tolist())
    me.update()
    me.materials.append(mat)
    for p in me.polygons:
        p.use_smooth = smooth
    o = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(o)
    return o


def scene_for(axis, value, keep_sign, zmax=0.40):
    for nm in ORIG:
        if nm in bpy.data.objects:
            bpy.data.objects[nm].hide_render = True
    # fresh render world and materials
    mats = dict(skin=material('Cut_skin', (0.80, 0.60, 0.46), .55, .3), kit=material('Cut_kit', (0.93, 0.93, 0.93) if cw == 'White' else (0.07, 0.07, 0.08), .6, .25),
                kit_w=material('Cut_kit_w', (0.93, 0.93, 0.93), .6, .25),
                c_skin=material('Cap_skin', (0.45, 0.22, 0.12), .9, .0), c_sock=material('Cap_sock', (0.18, 0.55, 1.0), .9, .0), c_shoe=material('Cap_shoe', (1.0, 0.45, 0.05), .9, .0))
    d = build(axis, value, keep_sign, zmax)
    objs = []
    objs.append(mesh('leg', d['leg'][0], d['leg'][1], mats['skin']))
    objs.append(mesh('sock', d['sock'][0], d['sock'][1], mats['kit_w'] if cw == 'White' else mats['kit']))
    objs.append(mesh('shoe', d['shoe'][0], d['shoe'][1], mats['kit']))
    for nm, mkey in (('leg', 'c_skin'), ('sock', 'c_sock'), ('shoe', 'c_shoe')):
        Cv, Cf = d[nm][2], d[nm][3]
        if len(Cf):
            objs.append(mesh(nm + '_cap', Cv, Cf, mats[mkey], smooth=False))
    return objs, d


ORIG = set(bpy.data.objects.keys())            # kit + body objects of the deliverable: hidden for these renders (never modified / saved)
rs.setup(samples=48)
zmin_shoe = float(Vs[:, 2].min())
rs.set_floor_z(zmin_shoe)
bpy.data.objects['Studio_Cyc'].hide_render = True
bpy.data.worlds['Studio_World'].node_tree.nodes['Background'].inputs[0].default_value = (0.36, 0.37, 0.40, 1)
bpy.data.worlds['Studio_World'].node_tree.nodes['Background'].inputs[1].default_value = 1.0
LM = json.load(open(f'{WORK}/proof/raw/checks_{gender}.json'))['foot_landmarks']['R']
c_xy = np.array(LM['ankle_centre_xy'])
rim_min = json.load(open(f'{WORK}/proof/raw/checks_{gender}.json'))['foot_inside']['R']['collar_rim_z_min']
cx_foot = float(np.mean([LM['longest_toe_tip'][0], LM['heel_point'][0]]))
cy_foot = float(0.5 * (LM['longest_toe_tip'][1] + LM['heel_point'][1]))
tz = 0.09
dist = float(os.environ.get('VDIST', 1.1))
res = (900, 900)
views = [
    ('sagittal', 0, cx_foot, +1, dict(az=-90, el=0, ortho={'female': 0.42, 'male': 0.47}[gender])),        # plane x = foot axis, keep the lateral half (x >= value), camera at -x sees the cut face
    ('coronal', 1, float(c_xy[1]), +1, dict(az=0, el=0, ortho={'female': 0.40, 'male': 0.44}[gender])),          # plane y = ankle centre, keep the rear half (y >= value), camera in front
    ('axial_collar', 2, rim_min - 0.006, -1, dict(az=0, el=89, ortho={'female': 0.31, 'male': 0.40}[gender])),   # plane z just under the lowest collar point, keep below, camera above
    ('axial_toes', 2, {'female': 0.012, 'male': 0.020}[gender], -1, dict(az=0, el=89, ortho={'female': 0.31, 'male': 0.40}[gender])),
]
for name, axis, value, keep_sign, cam in views:
    # clipped(): keep_sign=+1 keeps the HIGH side (V >= value), keep_sign=-1 keeps the LOW side; the cap faces look toward the removed side
    for o in list(bpy.data.objects):
        if o.name in ('leg', 'sock', 'shoe', 'leg_cap', 'sock_cap', 'shoe_cap'):
            bpy.data.objects.remove(o, do_unlink=True)
    objs, d = scene_for(axis, value, keep_sign)
    tgt = [cx_foot, cy_foot, tz]
    if name == 'coronal':
        tgt = [cx_foot, value, tz]
    if name.startswith('axial'):
        tgt = [cx_foot, cy_foot, value - 0.01]
    ortho = cam['ortho']
    rs.shot(f'{prefix}_{name}.png', tuple(tgt), cam['az'], cam['el'], dist=dist, lens=85, res=res, ortho=ortho)
    print('done', name, 'caps', {k: len(v[3]) for k, v in d.items()})

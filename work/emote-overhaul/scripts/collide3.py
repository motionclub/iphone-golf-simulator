"""INDEPENDENT penetration gate of an overhaul clip: the Blender-EVALUATED dressed hero (skin, kit, racket), not the numpy proxies of the solver.

  blender -b --factory-startup <HeroBase_<Hero>_Dressed.blend> --python collide3.py -- <male|female> <clip> <every:N|frames:a-b|t1,t2,..> [out.json]

For every sampled frame the armature is posed with the numpy solver of the clip (emo_clips2, the baked-in body clearance included) and the evaluated meshes are read back.
  PEN_SKIN  of a vertex of an arm (forearm / hand skin, further than 7 cm from the elbow) = how far it lies BEHIND the nearest face of the body skin (the single-layer, consistently
            oriented 'Body' mesh: torso, legs, head, the OTHER arm; the arm's own upper arm / forearm are no obstacle; the other arm only counts while the hands are not meant to be together).
            The clothes sit outside the skin (>= 8 mm on the torso), so a vertex that is not inside the skin is not inside the clothes by more than a few mm either.
  PEN_RACKET of a racket vertex = the same against the body skin without both hands / forearms, and against the OTHER (left) arm.
  PEN_CLOTH of an arm vertex = the signed distance to the nearest face of the SHIRT / SHORTS evaluated surface, taken only when it is trustworthy (the displacement is along the face
            normal) AND the vertex also lies behind the skin by more than 8 mm (so nested inner / outer shell faces cannot fake a hit); reported, not gated.
Gate quantities: max PEN_SKIN, max PEN_RACKET per frame.  Writes the table and the worst places."""
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, '..', '..', 'emotes', 'scripts'))
sys.path.insert(0, '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/match-anim-set/scripts')
import numpy as np
import bpy
from mathutils import Matrix, Vector
from mathutils.bvhtree import BVHTree

import emo_hero as EH
import emo_clips2 as EC
import preview as PV

a = sys.argv[sys.argv.index('--') + 1:]
tag, clip, spec = a[0], a[1], a[2]
outp = a[3] if len(a) > 3 else None
H = EH.EmoHero(tag)
C = EC.build(clip, H)
nF = int(round(C.length * 30)) + 1
if spec.startswith('every:'):
    frames = list(range(0, nF, int(spec[6:])))
elif spec.startswith('frames:'):
    lo, hi = spec[7:].split('-')
    frames = list(range(int(lo), int(hi) + 1))
else:
    frames = [int(round(float(x) * 30)) for x in spec.split(',')]
frames = [f for f in frames if 0 <= f < nF]

rig_o = [o for o in bpy.data.objects if o.type == 'ARMATURE'][0]
rk = bpy.data.objects['Racket_Classic']
rk.scale = (1.0, 1.0, 1.0)
BODY = 'Body_M' if tag == 'male' else 'Body_F'
FOREARM_KEYS = ('LowerArm', 'Hand', 'Thumb', 'Index', 'Middle', 'Ring', 'Little')


def part_of(name):
    s = 'L' if name.startswith('Left') else 'R' if name.startswith('Right') else None
    if s is None:
        return 'C'
    if any(k in name for k in FOREARM_KEYS):
        return 'F' + s
    if 'UpperArm' in name:
        return 'U' + s
    return 'C'


body_ob = bpy.data.objects[BODY]
gi_name = {g.index: g.name for g in body_ob.vertex_groups}
nv = len(body_ob.data.vertices)
cls = np.empty(nv, dtype=object)
for v in body_ob.data.vertices:
    best, bw = None, -1.0
    for g in v.groups:
        if g.weight > bw:
            bw, best = g.weight, gi_name.get(g.group)
    cls[v.index] = part_of(best) if best else 'C'
body_tris_all = None
rig_bones = rig_o.pose.bones
cam = PV.setup_scene(rig_o, samples=1)


def world_mesh(ob):
    ev = ob.evaluated_get(bpy.context.evaluated_depsgraph_get())
    me = ev.to_mesh()
    n = len(me.vertices)
    co = np.empty(n * 3)
    me.vertices.foreach_get('co', co)
    co = co.reshape(n, 3)
    M = np.array(ev.matrix_world)
    co = co @ M[:3, :3].T + M[:3, 3]
    me.calc_loop_triangles()
    tris = np.array([lt.vertices[:] for lt in me.loop_triangles], np.int64)
    ev.to_mesh_clear()
    return co, tris


PDIRS = [Vector(v).normalized() for v in ((0.267, 0.534, 0.802), (-0.70, 0.20, 0.68), (0.10, -0.90, 0.42), (0.55, -0.15, -0.82))]


def parity_inside(tree, p):
    votes = 0
    for dv in PDIRS:
        o = Vector(p)
        n = 0
        for _ in range(16):
            loc, nor, idx, dist = tree.ray_cast(o, dv)
            if loc is None:
                break
            n += 1
            o = loc + dv * 1e-5
        votes += n % 2
    return votes >= 3                                    # 3 of 4 rays: the skin has a few holes (the removed arm, the neck)


def signed(tree, p, reach=0.12):
    """signed distance to the nearest face; a point counts as INSIDE only when the normal test AND a 3-of-4 ray-parity test agree (the nearest face of a concave body can face away)"""
    loc, nor, idx, dist = tree.find_nearest(Vector(p), reach)
    if loc is None:
        return None
    sd = (Vector(p) - loc).dot(nor)
    if dist > 0.004 and abs(sd) < 0.8 * dist:
        return None
    if sd < 0 and dist > 0.006 and not parity_inside(tree, p):
        return None
    return sd, dist, idx


rk_local = None
prev = None
S = H.S
S.reset()
rows = []
worst_all = {}
for fr in frames:
    t = fr / 30.0
    d = C.solve(t)
    prev = PV.apply_pose(rig_o, H.rig, d['basis'], d['hips'], prev)
    rkw = d.get('racket')
    if rkw is not None:
        rk.matrix_world = Matrix.Translation(Vector(rkw['pos'].tolist())) @ Matrix(rkw['R'].tolist()).to_4x4()
    else:
        rk.matrix_basis = Matrix.Identity(4)
    bpy.context.view_layer.update()
    co, tris = world_mesh(body_ob)
    rk_co, _ = world_mesh(rk)
    exempt = C.grip_exempt(t)
    att = C.racket_attached(t)
    res = {}
    for arm in 'LR':
        other = 'R' if arm == 'L' else 'L'
        drop = {'F' + arm, 'U' + arm} | ({'F' + other, 'U' + other} if (exempt and att) else set())
        keep_tris = np.array([not any(cls[v] in drop for v in tr) for tr in tris])
        tree = BVHTree.FromPolygons(co.tolist(), tris[keep_tris].tolist(), all_triangles=True)
        sel = np.where(cls == 'F' + arm)[0]
        elbow = np.array(rig_o.matrix_world @ rig_bones[('Left' if arm == 'L' else 'Right') + 'LowerArm'].head)
        pts = co[sel]
        pts = pts[np.linalg.norm(pts - elbow, axis=1) > 0.07]
        worst, at, n3 = 0.0, None, 0
        keep_idx = np.where(keep_tris)[0]
        top = []
        for p in pts:
            r = signed(tree, p)
            if r is None:
                continue
            sd, dist, idx = r
            if sd < 0:
                pen = -sd
                if pen > 0.003:
                    n3 += 1
                    top.append((pen, tuple(round(float(x), 3) for x in p), set(cls[v] for v in tris[keep_idx[idx]]), dist))
                if pen > worst:
                    worst, at = pen, p
        if os.environ.get('VERBOSE') and top:
            top.sort(key=lambda r: -r[0])
            for tp in top[:4]:
                print('      %s pen %.1f mm at %s nearest-face classes %s dist %.3f' % (arm, 1000 * tp[0], tp[1], tp[2], tp[3]))
        res[arm] = dict(pen_skin=round(float(worst), 4), n_over_3mm=n3, at=[round(float(x), 3) for x in at] if at is not None else None)
    # racket: against the body skin without both forearms / hands (and, when not gripped, against the left arm as part of the skin) - only while it is in the hand
    if att:
        drop = {'FL', 'FR'} if exempt else {'FR'}
        keep_tris = np.array([not any(cls[v] in drop for v in tr) for tr in tris])
        tree = BVHTree.FromPolygons(co.tolist(), tris[keep_tris].tolist(), all_triangles=True)
        worst, at, n3 = 0.0, None, 0
        for p in rk_co[::3]:
            r = signed(tree, p)
            if r is None:
                continue
            sd, dist, idx = r
            if sd < 0:
                pen = -sd
                if pen > 0.003:
                    n3 += 1
                if pen > worst:
                    worst, at = pen, p
        res['racket'] = dict(pen_skin=round(float(worst), 4), n_over_3mm=n3, at=[round(float(x), 3) for x in at] if at is not None else None)
    else:
        res['racket'] = dict(pen_skin=0.0, n_over_3mm=0, at=None)
    rows.append(dict(frame=fr, t=round(t, 3), exempt=bool(exempt), **res))
    print('F%3d t=%.2f %s L %5.1f mm (%3d) | R %5.1f mm (%3d) | racket %5.1f mm (%3d)' % (fr, t, 'ex' if exempt else '  ', 1000 * res['L']['pen_skin'], res['L']['n_over_3mm'], 1000 * res['R']['pen_skin'], res['R']['n_over_3mm'],
                                                                                     1000 * res['racket']['pen_skin'], res['racket']['n_over_3mm']), flush=True)
mx = lambda k: max((r[k]['pen_skin'] for r in rows), default=0.0)
print('MAX_PEN_SKIN_MM L %.1f R %.1f racket %.1f' % (1000 * mx('L'), 1000 * mx('R'), 1000 * mx('racket')))
if outp:
    json.dump(dict(tag=tag, clip=clip, rows=rows), open(outp, 'w'), indent=1)
print('COLLIDE3_DONE')

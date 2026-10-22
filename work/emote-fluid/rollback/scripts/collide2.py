"""Penetration DEPTH check of an overhaul clip on the DRESSED hero (Blender, headless).

  blender -b --factory-startup <HeroBase_<Hero>_Dressed.blend> --python collide2.py -- <male|female> <clip> <every:N|frames:a-b|t1,t2,..> [out.json]

Per sampled frame the armature is posed with the numpy solver (emo_clips2) and the EVALUATED meshes of body skin, shirt, shorts, face (and the racket) are used.
A vertex of a forearm / hand (skin vertices whose dominant bone is LowerArm / Hand / finger, further than 7 cm from the elbow joint) is INSIDE an obstacle GROUP when a majority of three
ray-parity tests on that group alone says so (nested shells such as skin + shirt must not be mixed in one parity test); its penetration depth is the distance to the nearest surface point of
that group.  Groups per arm: SKIN (every body-skin polygon except the arm's own forearm / hand: torso, legs, head, the arm's own upper arm, the OTHER arm), SHIRT (without the arm's own sleeve),
SHORTS, FACE.  The racket is tested the same way (a sample of its vertices) against SKIN-without-both-forearms / SHIRT / SHORTS / FACE.  A vertex only counts when it is nearer than 0.15 m to the group.
Result per frame: for L, R and the racket the number of inside vertices, the maximum depth (m), the position of the deepest one and the obstacle that owns the nearest surface point."""
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
KIT = ['Kit_Top', 'Kit_Bottom']
face_name = 'Face_M' if tag == 'male' else 'Face_F'
FOREARM_KEYS = ('LowerArm', 'Hand', 'Thumb', 'Index', 'Middle', 'Ring', 'Little')
DIRS = [Vector(v).normalized() for v in ((0.267, 0.534, 0.802), (-0.70, 0.20, 0.68), (0.10, -0.90, 0.42))]
NEAR = 0.15


def part_of(name):
    s = 'L' if name.startswith('Left') else 'R' if name.startswith('Right') else None
    if s is None:
        return 'C'
    if any(k in name for k in FOREARM_KEYS):
        return 'F' + s
    if 'UpperArm' in name:
        return 'U' + s
    return 'C'


def islands_of(me):
    n = len(me.vertices)
    parent = list(range(n))

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x
    for p_ in me.polygons:
        vs = list(p_.vertices)
        for v in vs[1:]:
            a_, b_ = find(vs[0]), find(v)
            if a_ != b_:
                parent[a_] = b_
    return np.array([find(i) for i in range(n)])


def classify(ob, kit):
    me = ob.data
    gi_name = {g.index: g.name for g in ob.vertex_groups}
    n = len(me.vertices)
    cls = np.empty(n, dtype=object)
    for v in me.vertices:
        best, bw = None, -1.0
        for g in v.groups:
            if g.weight > bw:
                bw, best = g.weight, gi_name.get(g.group)
        cls[v.index] = part_of(best) if best else 'C'
    if kit:                                   # closed shells: an island takes the arm class of its majority
        isl = islands_of(me)
        for r in np.unique(isl):
            m = isl == r
            vals, cnt = np.unique(cls[m], return_counts=True)
            top = vals[np.argmax(cnt)]
            cls[m] = top if top != 'C' and cnt.max() > 0.5 * m.sum() else 'C'
    return cls


objs = {}
for nm in [BODY] + KIT:
    ob = bpy.data.objects.get(nm)
    if ob is None:
        continue
    objs[nm] = dict(ob=ob, cls=classify(ob, nm in KIT), polys=[list(p.vertices) for p in ob.data.polygons], kit=nm in KIT)
face_ob = bpy.data.objects.get(face_name)
face_polys = [list(p.vertices) for p in face_ob.data.polygons] if face_ob else []
rk_polys = [list(p.vertices) for p in rk.data.polygons]

cam = PV.setup_scene(rig_o, samples=1)


def world_verts(ob):
    ev = ob.evaluated_get(bpy.context.evaluated_depsgraph_get())
    me = ev.to_mesh()
    n = len(me.vertices)
    co = np.empty(n * 3)
    me.vertices.foreach_get('co', co)
    co = co.reshape(n, 3)
    M = np.array(ev.matrix_world)
    out = co @ M[:3, :3].T + M[:3, 3]
    ev.to_mesh_clear()
    return out


def collect_group(frame_pts, group, drop):
    """polygons of one obstacle group; `drop` = set of polygon classes that exclude a polygon (it touches the tested forearm / the arm's own sleeve)
    group: 'skin' (body skin), 'shirt' (Kit_Top), 'shorts' (Kit_Bottom), 'face' -> (vertices, polys)"""
    if group == 'face':
        if face_ob is None:
            return None
        return frame_pts['__face'], [list(p) for p in face_polys], ['C'] * len(face_polys)
    nm = dict(skin=BODY, shirt='Kit_Top', shorts='Kit_Bottom')[group]
    if nm not in objs:
        return None
    io = objs[nm]
    cls = io['cls']
    polys, labels = [], []
    for pi in io['polys']:
        cs_ = set(cls[v] for v in pi)
        if cs_ & drop:
            continue
        polys.append(pi)
        labels.append('/'.join(sorted(cs_)))
    return frame_pts[nm], polys, labels


def make_tree(verts, polys):
    return BVHTree.FromPolygons([tuple(map(float, p)) for p in verts], polys, all_triangles=False)


def parity_inside(tree, p):
    votes = 0
    for d in DIRS:
        o = Vector(p)
        n = 0
        for _ in range(16):
            loc, nor, idx, dist = tree.ray_cast(o, d)
            if loc is None:
                break
            n += 1
            o = loc + d * 1e-5
        votes += n % 2
    return votes >= 2


def depth_report(points, trees, labels):
    """inside test of the given world points against each group tree: -> dict(n_inside, max_depth, at, where, near, groups={group: [n, max depth]}, by_label={group:label: [n, max depth]})"""
    best, bat, bwhere, bnear, n_in = 0.0, None, '', None, 0
    groups, bylab = {}, {}
    inside_pts = []
    for p in points:
        vin = False
        for gname, tr in trees.items():
            loc, nor, idx, dist = tr.find_nearest(Vector(p), NEAR)
            if loc is None:
                continue
            if not parity_inside(tr, p):
                continue
            vin = True
            g = groups.setdefault(gname, [0, 0.0])
            g[0] += 1
            g[1] = max(g[1], float(dist))
            lb = gname + ':' + labels[gname][idx]
            b = bylab.setdefault(lb, [0, 0.0])
            b[0] += 1
            b[1] = max(b[1], float(dist))
            if dist > best:
                best, bat, bwhere, bnear = dist, p, lb, loc
        n_in += 1 if vin else 0
        if vin:
            inside_pts.append(p)
    return dict(n_inside=n_in, max_depth=round(float(best), 4), at=[round(float(x), 3) for x in bat] if bat is not None else None, where=bwhere,
                near=[round(float(x), 3) for x in bnear] if bnear is not None else None,
                groups={k: [v[0], round(v[1], 4)] for k, v in sorted(groups.items(), key=lambda kv: -kv[1][1])},
                by_label={k: [v[0], round(v[1], 4)] for k, v in sorted(bylab.items(), key=lambda kv: -kv[1][1])}, _pts=inside_pts)


def build_trees(pts, drop_by_group):
    trees, labels = {}, {}
    for g in ('skin', 'shirt', 'shorts', 'face'):
        r = collect_group(pts, g, drop_by_group.get(g, set()))
        if r is None or not r[1]:
            continue
        trees[g] = make_tree(r[0], r[1])
        labels[g] = r[2]
    return trees, labels



DBG = os.environ.get('DBG')
if DBG:
    import studio
    os.makedirs(DBG, exist_ok=True)
    for nm_ in ('Kit_Top', 'Kit_Bottom'):
        if os.environ.get('DBG_HIDE_KIT', '1') == '1' and bpy.data.objects.get(nm_):
            bpy.data.objects[nm_].hide_render = True


def debug_render(fr, res):
    marks = []
    for arm, col in (('L', (1.0, 0.1, 0.1)), ('R', (0.1, 0.3, 1.0)), ('racket', (0.1, 0.9, 0.2))):
        pts_ = res[arm].get('_pts', [])
        for q in pts_[::max(1, len(pts_) // 150)]:
            bpy.ops.mesh.primitive_uv_sphere_add(radius=0.006, location=tuple(float(x) for x in q), segments=8, ring_count=6)
            ob = bpy.context.active_object
            m = bpy.data.materials.new('dbg')
            m.use_nodes = True
            m.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value = (col[0], col[1], col[2], 1.0)
            m.node_tree.nodes['Principled BSDF'].inputs['Emission Color'].default_value = (col[0], col[1], col[2], 1.0)
            m.node_tree.nodes['Principled BSDF'].inputs['Emission Strength'].default_value = 3.0
            ob.data.materials.append(m)
            marks.append(ob)
    for v, (az, el, dist, lens, tz) in (('side', (90.0, 6.0, 3.0, 50, 0.95)), ('front', (0.0, 6.0, 3.0, 50, 0.95)), ('q_front', (35.0, 10.0, 3.0, 50, 0.95)), ('top', (0.0, 70.0, 3.0, 50, 0.9))):
        studio.shot(f'{DBG}/{clip}_{tag}_{fr:03d}_{v}.png', (H.O[0], H.O[1] - 0.05, tz), az=az, el=el, dist=dist, lens=lens, res=(420, 560), turn_lights=True)
    for ob in marks:
        bpy.data.objects.remove(ob, do_unlink=True)

prev = None
S = H.S
S.reset()
rows = []
rk_idx_all = np.arange(len(rk.data.vertices))
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
    pts = {nm: world_verts(io['ob']) for nm, io in objs.items()}
    if face_ob is not None:
        pts['__face'] = world_verts(face_ob)
    rk_w = world_verts(rk)
    res = {}
    for arm in 'LR':
        # SKIN: everything but the arm's own forearm / hand (its upper arm plugs the shoulder hole); SHIRT: without the arm's own sleeve island
        trees, labels = build_trees(pts, dict(skin={'F' + arm}, shirt={'U' + arm, 'F' + arm}))
        cls = objs[BODY]['cls']
        sel = np.where(cls == 'F' + arm)[0]
        pts_arm = pts[BODY][sel]
        elbow = np.array(rig_o.matrix_world @ rig_o.pose.bones[('Left' if arm == 'L' else 'Right') + 'LowerArm'].head)
        pts_arm = pts_arm[np.linalg.norm(pts_arm - elbow, axis=1) > 0.07]
        res[arm] = depth_report(pts_arm, trees, labels)
    # the racket (a sample of its vertices) against everything but the hands / forearms and the arm skins
    trees, labels = build_trees(pts, dict(skin={'FL', 'FR'}, shirt={'FL', 'FR'}, shorts={'FL', 'FR'}))
    res['racket'] = depth_report(rk_w[::2], trees, labels)
    if DBG and (res['L']['n_inside'] or res['R']['n_inside'] or res['racket']['n_inside']):
        debug_render(fr, res)
    for k_ in ('L', 'R', 'racket'):
        res[k_].pop('_pts', None)
    rows.append(dict(frame=fr, t=round(t, 3), L=res['L'], R=res['R'], racket=res['racket']))
    print('F%3d t=%.2f  L n=%-4d d=%5.1f mm %-14s | R n=%-4d d=%5.1f mm %-14s | racket n=%-4d d=%5.1f mm %-14s' % (
        fr, t, res['L']['n_inside'], 1000 * res['L']['max_depth'], res['L']['where'], res['R']['n_inside'], 1000 * res['R']['max_depth'], res['R']['where'],
        res['racket']['n_inside'], 1000 * res['racket']['max_depth'], res['racket']['where']), flush=True)
mx = lambda key: max((r[key]['max_depth'] for r in rows), default=0.0)
print('MAXDEPTH_MM L %.1f R %.1f racket %.1f  (READY frame 0: L %.1f R %.1f racket %.1f)' % (1000 * mx('L'), 1000 * mx('R'), 1000 * mx('racket'),
      1000 * rows[0]['L']['max_depth'], 1000 * rows[0]['R']['max_depth'], 1000 * rows[0]['racket']['max_depth']))
if outp:
    json.dump(dict(tag=tag, clip=clip, rows=rows), open(outp, 'w'), indent=1)
print('COLLIDE2_DONE')

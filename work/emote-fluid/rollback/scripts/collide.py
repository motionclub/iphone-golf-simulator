"""Penetration check of an overhaul clip on the DRESSED hero (Blender, headless).

  blender -b --factory-startup <HeroBase_<Hero>_Dressed.blend> --python collide.py -- <male|female> <clip> <every:N|frames:a-b|t1,t2,..> [out.json]

For every sampled frame the armature is posed with the numpy solver (emo_clips2) and the EVALUATED meshes of the body skin, shirt and shorts (+ the face mesh) are used.
SURFACE CROSSING test (BVHTree.overlap, triangle-triangle): an arm "passes through the body" when the surface of the forearm / hand (skin, vertices dominated by LowerArm / Hand /
finger bones) or of the upper arm beyond the shoulder blend crosses the surface of anything that is not that arm: torso, legs, head (body skin), shirt, shorts, the OTHER arm (skin).
The racket (closed solid) is tested against everything except the hand that holds it.  No signed-distance or normal test (the body skin is not a closed solid).
Result per frame and limb: the number of crossing triangle pairs and the world position / obstacle of the deepest-looking pair (largest vertex distance of the arm triangle from the obstacle plane).
Writes a table and prints the frames that cross."""
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


def side_of(name):
    return 'L' if name.startswith('Left') else 'R' if name.startswith('Right') else None


def part_of(name):
    s = side_of(name)
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


def tree(points, polys):
    return BVHTree.FromPolygons([tuple(map(float, p)) for p in points], polys, all_triangles=False)


def collect(frame_pts, sel_fn):
    """polygons (with global vertex offsets) of all objects for which sel_fn(obj_name, polygon_class_set) is True; returns (all vertices, polys, owner list)"""
    verts, polys, owner, off = [], [], [], 0
    for nm, io in objs.items():
        P_ = frame_pts[nm]
        verts.append(P_)
        cls = io['cls']
        for k, pi in enumerate(io['polys']):
            cs_ = set(cls[v] for v in pi)
            if sel_fn(nm, cs_):
                polys.append([off + v for v in pi])
                owner.append((nm, k, '/'.join(sorted(cs_))))
        off += len(P_)
    if face_ob is not None:
        verts.append(frame_pts['__face'])
        for k, pi in enumerate(face_polys):
            if sel_fn('face', {'C'}):
                polys.append([off + v for v in pi])
                owner.append(('face', k, 'C'))
        off += len(frame_pts['__face'])
    return np.vstack(verts), polys, owner


prev = None
S = H.S
S.reset()
rows = []
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
        other = 'R' if arm == 'L' else 'L'
        mine = {'F' + arm, 'U' + arm}
        # test set: forearm / hand skin triangles of this arm (all vertices forearm-class) + the kit sleeve of this arm is NOT tested (it merges with the shirt by construction)
        v_t, p_t, o_t = collect(pts, lambda nm, cs, arm=arm: (nm == BODY and cs == {'F' + arm}))
        # obstacles: everything except this arm (both of its bone groups) and its sleeve island; the OTHER arm is an obstacle
        v_o, p_o, o_o = collect(pts, lambda nm, cs, mine=mine: not (cs & mine))
        if not p_t:
            res[arm] = dict(pairs=0)
            continue
        ta = tree(v_t, p_t)
        to = tree(v_o, p_o)
        ov = ta.overlap(to)
        info = dict(pairs=len(ov))
        if ov:
            # deepest-looking pair: the arm triangle vertex farthest behind the obstacle triangle plane
            best, bi = -1.0, None
            for (ia, io_) in ov[:400]:
                tri_a = [v_t[v] for v in p_t[ia]]
                tri_o = [v_o[v] for v in p_o[io_]]
                no = np.cross(tri_o[1] - tri_o[0], tri_o[2] - tri_o[0])
                ln = np.linalg.norm(no)
                if ln < 1e-12:
                    continue
                no = no / ln
                dd = max(abs(float(np.dot(q - tri_o[0], no))) for q in tri_a)
                if dd > best:
                    best, bi = dd, (ia, io_)
            ia, io_ = bi if bi else ov[0]
            c = np.mean([v_t[v] for v in p_t[ia]], axis=0)
            hist = {}
            for (ia2, io2) in ov:
                key = o_o[io2][0] + ':' + o_o[io2][2]
                hist[key] = hist.get(key, 0) + 1
            info.update(depth_proxy=round(float(best), 4), where=o_o[io_][0], at=[round(float(x), 3) for x in c], obstacles=dict(sorted(hist.items(), key=lambda kv: -kv[1])[:5]))
        res[arm] = info
    # the racket against everything but the hand that holds it
    v_o, p_o, o_o = collect(pts, lambda nm, cs: 'FR' not in cs)
    tr = BVHTree.FromPolygons([tuple(map(float, p)) for p in rk_w], rk_polys, all_triangles=False)
    to = tree(v_o, p_o)
    ovr = tr.overlap(to)
    rinfo = dict(pairs=len(ovr))
    if ovr:
        rinfo.update(where=o_o[ovr[0][1]][0] + ':' + o_o[ovr[0][1]][2], at=[round(float(x), 3) for x in np.mean([rk_w[v] for v in rk_polys[ovr[0][0]]], axis=0)])
    res['racket'] = rinfo
    rows.append(dict(frame=fr, t=round(t, 3), L=res['L'], R=res['R'], racket=res['racket']))
    flag = ' <-- CROSS' if (res['L']['pairs'] or res['R']['pairs'] or res['racket']['pairs']) else ''
    print('F%3d t=%.2f  L %4d d=%.3f %-9s R %4d d=%.3f %-9s racket %3d %s%s' % (fr, t, res['L']['pairs'], res['L'].get('depth_proxy', 0), res['L'].get('where', ''), res['R']['pairs'], res['R'].get('depth_proxy', 0), res['R'].get('where', ''), res['racket']['pairs'], res['racket'].get('where', ''), flag), flush=True)
bad = [r for r in rows if r['L']['pairs'] or r['R']['pairs'] or r['racket']['pairs']]
print('FRAMES', len(rows), 'CROSSING', len(bad), [r['frame'] for r in bad][:60])
if outp:
    json.dump(dict(tag=tag, clip=clip, rows=rows), open(outp, 'w'), indent=1)
print('COLLIDE_DONE')

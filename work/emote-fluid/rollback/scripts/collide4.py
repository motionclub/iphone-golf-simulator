"""CLOTH check (independent of the solver's cloth model): is any forearm / hand vertex ENCLOSED by the shirt or the shorts?

  blender -b --factory-startup <HeroBase_<Hero>_Dressed.blend> --python collide4.py -- <male|female> <clip> <every:N|frames:a-b|t1,t2,..> [out.json]

The kit meshes are thick closed shells, so a normal or parity test cannot tell 'in the cavity' from 'outside'.  Enclosure can: a point inside a garment hits the garment in (nearly) every direction, a point beside it
in about half of them.  For every arm vertex (forearm + hand skin, further than 7 cm from the elbow, within 12 cm of a garment) 16 directions are cast against the EVALUATED garment (the shirt without the arm's own
sleeve island, and the shorts); the vertex counts as enclosed when >= 15 of 16 rays hit within 0.6 m.  The garment openings (neck, hem, sleeves) leave a few directions free, hence not 16 of 16."""
import json, math, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, '..', '..', 'emotes', 'scripts')); sys.path.insert(0, '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/match-anim-set/scripts')
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
H = EH.EmoHero(tag); C = EC.build(clip, H)
nF = int(round(C.length * 30)) + 1
if spec.startswith('every:'): frames = list(range(0, nF, int(spec[6:])))
elif spec.startswith('frames:'):
    lo, hi = spec[7:].split('-'); frames = list(range(int(lo), int(hi) + 1))
else: frames = [int(round(float(x) * 30)) for x in spec.split(',')]
frames = [f for f in frames if 0 <= f < nF]
rig_o = [o for o in bpy.data.objects if o.type == 'ARMATURE'][0]
rk = bpy.data.objects['Racket_Classic']; rk.scale = (1, 1, 1)
BODY = 'Body_M' if tag == 'male' else 'Body_F'
FOREARM_KEYS = ('LowerArm', 'Hand', 'Thumb', 'Index', 'Middle', 'Ring', 'Little')
def part_of(name):
    s = 'L' if name.startswith('Left') else 'R' if name.startswith('Right') else None
    if s is None: return 'C'
    if any(k in name for k in FOREARM_KEYS): return 'F' + s
    if 'UpperArm' in name: return 'U' + s
    return 'C'
def classify(ob):
    gi = {g.index: g.name for g in ob.vertex_groups}; n = len(ob.data.vertices); cls = np.empty(n, dtype=object)
    for v in ob.data.vertices:
        best, bw = None, -1.0
        for g in v.groups:
            if g.weight > bw: bw, best = g.weight, gi.get(g.group)
        cls[v.index] = part_of(best) if best else 'C'
    return cls
def islands(me):
    n = len(me.vertices); parent = list(range(n))
    def find(x):
        while parent[x] != x: parent[x] = parent[parent[x]]; x = parent[x]
        return x
    for p_ in me.polygons:
        vs = list(p_.vertices)
        for v in vs[1:]:
            a_, b_ = find(vs[0]), find(v)
            if a_ != b_: parent[a_] = b_
    return np.array([find(i) for i in range(n)])
body = bpy.data.objects[BODY]; cls_body = classify(body)
shirt = bpy.data.objects['Kit_Top']; shorts = bpy.data.objects['Kit_Bottom']
cls_shirt = classify(shirt)                                   # per vertex (dominant bone): the sleeve is welded to the torso island, so islands cannot tell it apart
cam = PV.setup_scene(rig_o, samples=1)
def world(ob):
    ev = ob.evaluated_get(bpy.context.evaluated_depsgraph_get()); me = ev.to_mesh(); n = len(me.vertices)
    co = np.empty(n * 3); me.vertices.foreach_get('co', co); co = co.reshape(n, 3)
    M = np.array(ev.matrix_world); co = co @ M[:3, :3].T + M[:3, 3]
    me.calc_loop_triangles(); tris = np.array([lt.vertices[:] for lt in me.loop_triangles], np.int64); ev.to_mesh_clear()
    return co, tris
k = 16; gold = math.pi * (3 - math.sqrt(5)); DIRS = []
for i in range(k):
    y = 1 - 2 * (i + 0.5) / k; r = math.sqrt(1 - y * y); th = gold * i
    DIRS.append(Vector((math.cos(th) * r, y, math.sin(th) * r)))
prev = None; rows = []; allenc = {}
DBG = os.environ.get('DBG')
if DBG:
    import studio
    os.makedirs(DBG, exist_ok=True)
for fr in frames:
    t = fr / 30.0
    d = C.solve(t)
    prev = PV.apply_pose(rig_o, H.rig, d['basis'], d['hips'], prev)
    bpy.context.view_layer.update()
    co_b, _ = world(body); co_s, tr_s = world(shirt); co_p, tr_p = world(shorts)
    res = {}
    for arm in 'LR':
        own = {'U' + arm, 'F' + arm}
        keep = np.array([not (cls_shirt[tr[0]] in own or cls_shirt[tr[1]] in own or cls_shirt[tr[2]] in own) for tr in tr_s])
        t_sh = BVHTree.FromPolygons(co_s.tolist(), tr_s[keep].tolist(), all_triangles=True)
        t_sp = BVHTree.FromPolygons(co_p.tolist(), tr_p.tolist(), all_triangles=True)
        sel = np.where(cls_body == 'F' + arm)[0]
        elbow = np.array(rig_o.matrix_world @ rig_o.pose.bones[('Left' if arm == 'L' else 'Right') + 'LowerArm'].head)
        pts = co_b[sel]; pts = pts[np.linalg.norm(pts - elbow, axis=1) > 0.07]
        n_enc = 0; worst = None; enc_pts = []
        for p in pts[::2]:
            pv = Vector(p)
            for nm, tr in (('shirt', t_sh), ('shorts', t_sp)):
                loc, nor, idx, dist = tr.find_nearest(pv, 0.12)
                if loc is None: continue
                hits = 0
                for dv in DIRS:
                    l2, n2, i2, d2 = tr.ray_cast(pv, dv, 0.6)
                    if l2 is not None: hits += 1
                if hits >= 15:
                    n_enc += 1; enc_pts.append(p)
                    if worst is None: worst = (nm, [round(float(x), 3) for x in p], round(dist, 3))
                    break
        res[arm] = dict(enclosed=n_enc, first=worst)
        allenc.setdefault(fr, []).extend([(arm, q) for q in enc_pts])
    rows.append(dict(frame=fr, t=round(t, 3), L=res['L'], R=res['R']))
    if DBG and allenc.get(fr):
        marks = []
        for arm, q in allenc[fr][::3]:
            bpy.ops.mesh.primitive_uv_sphere_add(radius=0.007, location=tuple(float(x) for x in q), segments=8, ring_count=6)
            ob = bpy.context.active_object; m = bpy.data.materials.new('dbg'); m.use_nodes = True
            bs = m.node_tree.nodes['Principled BSDF']; col = (1.0, 0.1, 0.1) if arm == 'L' else (0.1, 0.3, 1.0)
            bs.inputs['Base Color'].default_value = (*col, 1.0); bs.inputs['Emission Color'].default_value = (*col, 1.0); bs.inputs['Emission Strength'].default_value = 4.0
            ob.data.materials.append(m); marks.append(ob)
        for v, (az, el, dist, lens, tz) in (('front', (0.0, 6.0, 2.4, 50, 1.0)), ('q_front', (35.0, 10.0, 2.4, 50, 1.0)), ('side', (90.0, 6.0, 2.4, 50, 1.0)), ('behind', (180.0, 8.0, 2.4, 50, 1.0))):
            studio.shot(f'{DBG}/{clip}_{tag}_{fr:03d}_{v}.png', (H.O[0], H.O[1] - 0.05, tz), az=az, el=el, dist=dist, lens=lens, res=(420, 520), turn_lights=True)
        for ob in marks: bpy.data.objects.remove(ob, do_unlink=True)
    print('F%3d t=%.2f  L enclosed %3d | R enclosed %3d  %s' % (fr, t, res['L']['enclosed'], res['R']['enclosed'], res['L']['first'] or res['R']['first'] or ''), flush=True)
mx = max([r['L']['enclosed'] for r in rows] + [r['R']['enclosed'] for r in rows])
print('MAX_ENCLOSED', mx, 'frames_with_any', sum(1 for r in rows if r['L']['enclosed'] or r['R']['enclosed']), 'of', len(rows))
if outp: json.dump(dict(tag=tag, clip=clip, rows=rows), open(outp, 'w'), indent=1)
print('COLLIDE4_DONE')

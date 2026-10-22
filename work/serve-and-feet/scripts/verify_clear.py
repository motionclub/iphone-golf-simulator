"""Body clearance of the five new clips (Blender headless, evaluated deformed meshes): does the racket or a forearm / hand pass through the body?

  blender -b export/HeroBase_<Hero>_MatchAnims.blend --python scripts/verify_clear.py -- <male|female> [clip ...]

Racket: every vertex of the racket objects more than 0.22 m from the grip centre (the held part is inside the hand by design) is tested against the body + face + hair surface
(nearest point + face-normal sign = penetration depth).  Arms: forearm / hand vertices against the torso + head + legs surface.  The READY frame of ReadyIdle is measured the same way
(the baseline of the existing, accepted clips).  Writes data/verify_clear_<hero>.json."""
import json
import sys

import numpy as np
import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree

REPO = '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator'
sys.path.insert(0, REPO + '/work/serve-and-feet/scripts')
import loco

a_ = sys.argv[sys.argv.index('--') + 1:]
tag = a_[0]
names = a_[1:] or ['Walk', 'RunForward', 'RunRight', 'RunLeft', 'Serve', 'ReadyIdle']
H = dict(male=dict(body='Body_M', face='Face_M', hair=None, rig='Rig_Male'), female=dict(body='Body_F', face='Face_F', hair='Hair_F', rig='Rig_Female'))[tag]
sc = bpy.context.scene
rig = bpy.data.objects[H['rig']]
hero = loco.Hero(tag)
ix = hero.rig.idx
sk = np.load(f'{loco.DATA}/skin_{tag}.npz')
dom = sk['dom']
def _arm(side):
    return np.isin(dom, [ix[n] for n in hero.rig.names if n.startswith(side) and ('LowerArm' in n or n.endswith('Hand') or 'Thumb' in n or 'Index' in n or 'Middle' in n or 'Ring' in n or 'Little' in n)])
ARM_L, ARM_R = _arm('Left'), _arm('Right')
ARM = ARM_L | ARM_R
UPPER = np.isin(dom, [ix[n] for n in ('Hips', 'Spine', 'Chest', 'UpperChest', 'Neck', 'Head', 'LeftUpperLeg', 'RightUpperLeg', 'LeftLowerLeg', 'RightLowerLeg')])
body = bpy.data.objects[H['body']]
face = bpy.data.objects[H['face']]
hair = bpy.data.objects[H['hair']] if H['hair'] else None
racket_objs = [bpy.data.objects[n] for n in ('Racket_Classic', 'Grip', 'ButtCap', 'StringBed')]


def ev(obj):
    dg = bpy.context.evaluated_depsgraph_get()
    eo = obj.evaluated_get(dg)
    me = eo.to_mesh()
    co = np.empty(len(me.vertices) * 3)
    me.vertices.foreach_get('co', co)
    co = co.reshape(-1, 3)
    M = np.array(eo.matrix_world)
    co = co @ M[:3, :3].T + M[:3, 3]
    me.calc_loop_triangles()
    tr = np.empty(len(me.loop_triangles) * 3, np.int32)
    me.loop_triangles.foreach_get('vertices', tr)
    eo.to_mesh_clear()
    return co, tr.reshape(-1, 3)


def bvh(co, tr):
    return BVHTree.FromPolygons([tuple(map(float, v)) for v in co], [tuple(map(int, t)) for t in tr])


DIRS = [Vector((1, 0.0137, 0.0071)), Vector((-0.0091, 1, 0.0113)), Vector((0.0063, -0.0127, 1))]


def crossings(tree, p, d):
    n = 0
    o = Vector(p.tolist())
    for _ in range(12):
        loc, nor, idx, dist = tree.ray_cast(o, d)
        if loc is None:
            break
        n += 1
        o = loc + d * 1e-5
    return n


def depth(tree, pts):
    """inside test by ray parity along three axes (inside when at least two of the three give an odd number of surface crossings); returns the nearest-surface distance for inside points
    (the depth to get out), -1 for outside points.  Open meshes give a few false positives near the openings: the READY frame of ReadyIdle is the reference."""
    out = np.full(len(pts), -1.0)
    for i, p in enumerate(pts):
        odd = sum(crossings(tree, p, d) % 2 for d in DIRS)
        if odd >= 2:
            r = tree.find_nearest(Vector(p.tolist()))
            out[i] = r[3] if r[0] is not None else 0.0
    return out


R = {}
for clip in names:
    act = bpy.data.actions[clip]
    rig.animation_data_create()
    rig.animation_data.action = act
    try:
        rig.animation_data.action_slot = act.slots[0]
    except Exception:
        pass
    nF = int(act.frame_end) + 1
    rk_worst, arm_worst, rk_frames, arm_frames = 0.0, 0.0, [], []
    per = []
    for f in range(nF):
        sc.frame_set(f)
        bpy.context.view_layer.update()
        cb, tb = ev(body)
        cf, tf = ev(face)
        cs = [cb, cf]
        ts = [tb, tf + len(cb)]
        if hair is not None:
            ch, th = ev(hair)
            cs.append(ch)
            ts.append(th + len(cb) + len(cf))
        allco = np.vstack(cs)
        alltr = np.vstack(ts)
        tree_all = bvh(allco, alltr)
        # torso + head + legs surface (triangles whose three vertices are all upper-body vertices) + the face mesh
        keep = UPPER[tb].all(axis=1)
        tree_up = bvh(np.vstack([cb, cf]), np.vstack([tb[keep], tf + len(cb)]))
        grip = np.mean(ev(bpy.data.objects['Grip'])[0], axis=0)
        rk = np.vstack([ev(o)[0] for o in racket_objs])
        far = np.linalg.norm(rk - grip, axis=1) > 0.22
        d_rk = depth(tree_all, rk[far][::2])
        d_aL = depth(tree_up, cb[ARM_L][::4])
        d_aR = depth(tree_up, cb[ARM_R][::4])
        per.append((float(d_rk.max()), float(max(d_aL.max(), d_aR.max())), float(d_aL.max()), float(d_aR.max())))
    per = np.array(per)
    R[clip] = dict(racket_depth_mm=(per[:, 0] * 1000).round(1).tolist(), arm_depth_mm=(per[:, 1] * 1000).round(1).tolist(), armL_depth_mm=(per[:, 2] * 1000).round(1).tolist(), armR_depth_mm=(per[:, 3] * 1000).round(1).tolist(), racket_max_mm=float(per[:, 0].max() * 1000), arm_max_mm=float(per[:, 1].max() * 1000),
                   racket_frames_over_8mm=[int(i) for i in np.where(per[:, 0] > 0.008)[0]], arm_frames_over_10mm=[int(i) for i in np.where(per[:, 1] > 0.010)[0]])
    print('CLEAR', tag, clip, 'racket max %.1f mm (frames>8: %s)' % (R[clip]['racket_max_mm'], R[clip]['racket_frames_over_8mm'][:12]), ' arm max %.1f mm (L %.1f R %.1f) (frames>10: %s)' % (R[clip]['arm_max_mm'], per[:, 2].max() * 1000, per[:, 3].max() * 1000, R[clip]['arm_frames_over_10mm'][:14]))
json.dump(R, open(f'{loco.DATA}/verify_clear_{tag}.json', 'w'), indent=1)

"""Move bone heads that the landmark fit left OUTSIDE the hand mesh to the medial axis of the hand (rig-only edit, mesh-neutral).

  blender -b export/_stage/<Hero>_rig.blend --python fix_bones.py -- <male|female>

ON_HERO requires every bone head inside the body mesh.  The thumb chain (all three thumb bones are never rotated by any clip: grip angles are 0.0) and a few
finger heads sit on or outside the skin.  Because those bones are leaves with an identity pose in every frame, their rest position does not change the skinned
mesh at all; the heads / tails are moved to the middle of the local thickness, `data/rig_<hero>.json` is updated to match and the stage blend is saved.
A report is written to data/fix_bones_<hero>.json."""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree

from common import *

tag = args_after_dashes()[0]
H = HERO[tag]
rig = [o for o in bpy.data.objects if o.type == 'ARMATURE'][0]
body = bpy.data.objects[H['body']]
me = body.data
co = np.empty(len(me.vertices) * 3)
me.vertices.foreach_get('co', co)
co = co.reshape(-1, 3)
me.calc_loop_triangles()
tri = np.empty(len(me.loop_triangles) * 3, np.int32)
me.loop_triangles.foreach_get('vertices', tri)
tri = tri.reshape(-1, 3)
bv = BVHTree.FromPolygons([tuple(v) for v in co], [tuple(t) for t in tri], all_triangles=True)


def inside(p):
    votes = 0
    for dvec in (Vector((0, 0, 1)), Vector((1, 0.13, 0.07)).normalized(), Vector((-0.11, 1, 0.17)).normalized()):
        n, pos = 0, Vector(p)
        for _ in range(40):
            hit = bv.ray_cast(pos, dvec)
            if hit[0] is None:
                break
            n += 1
            pos = hit[0] + dvec * 1e-5
        votes += (n % 2)
    return votes >= 2


def medial(p, margin=0.0):
    """nearest skin point s with outward normal n; the point half way through the local thickness along -n"""
    loc = bv.find_nearest(Vector(p))
    s, n = loc[0], loc[1]
    nin = -n                                                    # towards the inside, from the nearest skin point
    ray = bv.ray_cast(s + nin * 1e-4, nin)
    t = ray[3] if ray[0] is not None else 0.012
    return s + nin * min(0.5 * t, 0.010), float(loc[3]), float(t)          # at most 10 mm under the skin (the thumb base is ~25 mm thick)


bones = {b.name: b for b in rig.data.bones}
rep = {}
chain = []
for sd in ('Left', 'Right'):
    outside = [b.name for b in rig.data.bones if b.name.startswith(sd) and b.name != 'Root' and not inside(rig.matrix_world @ b.head_local)]
    chain += outside
rep['outside_before'] = chain
if chain:
    bpy.context.view_layer.objects.active = rig
    bpy.ops.object.mode_set(mode='EDIT')
    eb = rig.data.edit_bones
    newpos = {}
    for n in chain:
        h = eb[n].head.copy()
        q, d0, t = medial(h)
        newpos[n] = (q, d0, t)
    # a bone's head is moved; its parent's tail follows when the pair is connected; the tail of a leaf stays unless it is outside as well
    for n, (q, d0, t) in newpos.items():
        e = eb[n]
        old_head = e.head.copy()
        e.head = q
        if e.parent is not None and (e.parent.tail - old_head).length < 1e-6:
            e.parent.tail = q
    for n in chain:
        e = eb[n]
        if not inside(e.tail):
            q, d0, t = medial(e.tail)
            e.tail = q
            for c in e.children:
                if (c.head - e.tail).length < 1e-3:
                    c.head = q
    bpy.ops.object.mode_set(mode='OBJECT')
    rep['moves_mm'] = {}
bpy.context.view_layer.update()
rep['outside_after'] = [b.name for b in rig.data.bones if b.name != 'Root' and not inside(rig.matrix_world @ b.head_local)]
rep['tails_outside_after'] = [b.name for b in rig.data.bones if b.name != 'Root' and not inside(rig.matrix_world @ b.tail_local)]
# update the JSON (head / tail / length / matrix_local of the bones that changed)
rj = json.load(open(f'{DATA}/rig_{tag}.json'))
changed = []
for b in rj['bones']:
    bb = rig.data.bones[b['name']]
    h, t = list(map(float, bb.head_local)), list(map(float, bb.tail_local))
    if np.abs(np.array(h) - np.array(b['head'])).max() > 1e-7 or np.abs(np.array(t) - np.array(b['tail'])).max() > 1e-7:
        b['head'], b['tail'] = h, t
        b['length'] = float(bb.length)
        b['matrix_local'] = [list(map(float, r)) for r in bb.matrix_local]
        changed.append(b['name'])
rep['json_changed'] = changed
json.dump(rj, open(f'{DATA}/rig_{tag}.json', 'w'), indent=1)
bpy.context.preferences.filepaths.save_version = 0
bpy.ops.wm.save_as_mainfile(filepath=bpy.data.filepath)
json.dump(rep, open(f'{DATA}/fix_bones_{tag}.json', 'w'), indent=1)
print('FIX_BONES_DONE', tag, json.dumps({k: (v if not isinstance(v, dict) else {a: round(b, 1) for a, b in v.items()}) for k, v in rep.items()}))

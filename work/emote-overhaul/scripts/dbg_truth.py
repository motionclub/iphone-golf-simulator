"""dbg_truth.py <tag> <clip> <t> x y z : with the Blender-EVALUATED meshes of the dressed hero at time t, print what lies around the world point (x,y,z): ray hits along +-y and the nearest face of each mesh."""
import sys, os
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, '..', '..', 'emotes', 'scripts')); sys.path.insert(0, '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/match-anim-set/scripts')
import bpy
from mathutils import Vector, Matrix
from mathutils.bvhtree import BVHTree
import emo_hero as EH
import emo_clips2 as EC
import preview as PV
a_ = sys.argv[sys.argv.index('--') + 1:]
tag, clip, t = a_[0], a_[1], float(a_[2])
p = Vector([float(a_[3]), float(a_[4]), float(a_[5])])
H = EH.EmoHero(tag); C = EC.build(clip, H)
rig_o = [o for o in bpy.data.objects if o.type == 'ARMATURE'][0]
PV.setup_scene(rig_o, samples=1)
d = C.solve(t)
PV.apply_pose(rig_o, H.rig, d['basis'], d['hips'], None)
bpy.context.view_layer.update()
dg = bpy.context.evaluated_depsgraph_get()
BODY = 'Body_M' if tag == 'male' else 'Body_F'
for nm in (BODY, 'Kit_Top', 'Kit_Bottom'):
    ob = bpy.data.objects[nm].evaluated_get(dg)
    me = ob.to_mesh()
    co = np.empty(len(me.vertices) * 3); me.vertices.foreach_get('co', co); co = co.reshape(-1, 3)
    M = np.array(ob.matrix_world); co = co @ M[:3, :3].T + M[:3, 3]
    tris = [tuple(lt.vertices) for lt in me.loop_triangles] if me.loop_triangles else None
    me.calc_loop_triangles()
    tris = [tuple(lt.vertices) for lt in me.loop_triangles]
    tr = BVHTree.FromPolygons(co.tolist(), tris, all_triangles=True)
    loc, nor, idx, dist = tr.find_nearest(p)
    sd = (p - loc).dot(nor) if loc is not None else None
    hits = []
    for dirv in (Vector((0, -1, 0)), Vector((0, 1, 0))):
        o = Vector(p); hh = []
        for _ in range(6):
            l2, n2, i2, d2 = tr.ray_cast(o, dirv)
            if l2 is None: break
            hh.append(round(d2 * 1000 + (hh[-1] if hh else 0), 1)); o = l2 + dirv * 1e-5
        hits.append(hh)
    print(nm, 'nearest dist %.3f sd %.3f nrm %s | ray +f(-y) hits mm: %s | ray back(+y) hits mm: %s' % (dist, sd, tuple(round(x, 2) for x in nor), hits[0], hits[1]))
    ob.to_mesh_clear()

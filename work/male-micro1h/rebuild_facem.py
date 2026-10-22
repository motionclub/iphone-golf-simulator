"""Rebuild only Face_M (paint layer: eyes, brows, lids, lips, seam, nostrils) on an existing final blend.
blender -b --factory-startup --python rebuild_facem.py -- <src.blend> <dst.blend>"""
import sys, importlib
import numpy as np
import bpy
sys.path.insert(0, '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/male-micro1h')
sys.path.insert(0, '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/male-micro1e')
import h1lib as H, sculpt as S, finalize as FZ, faceparts as FP
argv = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=argv[0])
body = bpy.data.objects['Body_M']; me = body.data
old = bpy.data.objects.get('Face_M')
if old: bpy.data.objects.remove(old, do_unlink=True)
for m in list(bpy.data.materials):
    if m.name.startswith('Face_') or m.name.startswith('eye_mat') or m.name.startswith('brow_mat'):
        bpy.data.materials.remove(m)
n = len(me.vertices)
P = np.empty(n * 3); me.vertices.foreach_get('co', P); P = P.reshape(-1, 3)
F = [[v for v in p.vertices] for p in me.polygons]
def grp(nm):
    vg = body.vertex_groups[nm]
    return [v.index for v in me.vertices if any(g.group == vg.index for g in v.groups)]
face_o, parts = FP.build_face_m(P, F, margin={-1: grp('LOOP_lid_margin_L'), 1: grp('LOOP_lid_margin_R')})
face_o.parent = None
print('Face_M verts', len(face_o.data.vertices), 'tris', sum(len(p.vertices) - 2 for p in face_o.data.polygons))
bpy.ops.wm.save_as_mainfile(filepath=argv[1])
print('saved', argv[1])

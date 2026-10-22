"""Blender-evaluated kit (and body) vertex positions at the Unity test poses -> data/kitpose_<hero>.npz   (blender -b export/HeroBase_<Hero>_Dressed.blend --python dump_kit_poses.py -- <male|female>)
Poses (clip, frame): ReadyIdle 0, Forehand 20 (contact 0.667 s), Forehand 9 (0.30 s).  Keys: <Piece>_<pose> in the kit mesh's own vertex order, body_<pose> (full), centroid arrays."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy
import numpy as np

from dcommon import *

tag = args_after_dashes()[0]
H = HERO[tag]
sc = bpy.context.scene
rig = bpy.data.objects[H['rig']]
body = bpy.data.objects[H['body']]
out = {}
POSES = [('ReadyIdle', 0), ('Forehand', 20), ('Forehand', 9)]
rig.animation_data.action = None
for pb in rig.pose.bones:
    pb.location = (0, 0, 0)
    pb.rotation_quaternion = (1, 0, 0, 0)
    pb.rotation_euler = (0, 0, 0)
    pb.scale = (1, 1, 1)
sc.frame_set(0)
bpy.context.view_layer.update()
dg = bpy.context.evaluated_depsgraph_get()
out['body_bind'] = evaluated_co(body, dg)
for p in PIECES:
    out[f'{p}_bind'] = evaluated_co(bpy.data.objects[KIT_NAME[p]], dg)
for clip, f in POSES:
    activate_clip(rig, clip)
    sc.frame_set(f)
    bpy.context.view_layer.update()
    dg = bpy.context.evaluated_depsgraph_get()
    out[f'body_{clip}_{f}'] = evaluated_co(body, dg)
    for p in PIECES:
        out[f'{p}_{clip}_{f}'] = evaluated_co(bpy.data.objects[KIT_NAME[p]], dg)
np.savez(f'{DATA}/kitpose_{tag}.npz', **out)
import json
d = f'{DATA}/kitpose_{tag}'
os.makedirs(d, exist_ok=True)
for k, v in out.items():
    np.asarray(v, np.float32).tofile(f'{d}/{k}.f32')
json.dump({k: int(len(v)) for k, v in out.items()}, open(f'{d}/index.json', 'w'))
print('KITPOSE', tag, len(out))

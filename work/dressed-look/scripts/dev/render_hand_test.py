"""Scratch: render hand closeups of a test blend.  blender -b <blend> --python render_hand_test.py -- <tag> <out_prefix> [action]"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from dl_common import *
import render_setup_dl as RS
tag, out = args_after_dashes()[:2]
act = args_after_dashes()[2] if len(args_after_dashes()) > 2 else None
rig = bpy.data.objects['Rig_Hand_R']
if act:
    rig.animation_data.action = bpy.data.actions[act]
bpy.context.scene.frame_set(1)
bpy.context.view_layer.update()
# hide original lights / cameras, white kit off for the hand test
for o in bpy.data.objects:
    if o.type in ('LIGHT', 'CAMERA'):
        o.hide_render = True
for c in bpy.data.collections:
    if c.name.startswith('Kit_'):
        c.hide_render = True
body = bpy.data.objects['Body_M' if tag == 'male' else 'Body_F']
mat = bpy.data.materials.new('Proof_Grey'); mat.use_nodes = True
mat.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value = (0.62, 0.55, 0.52, 1)
body.data.materials.clear(); body.data.materials.append(mat)
RS.studio(bg=(0.36, 0.37, 0.39), samples=24)
ctr = tuple(bpy.data.objects['Hand_Racket'].matrix_world.translation)
views = tuple((v[0], v[1], v[2]) for v in ((('a', -55, 10), ('b', -120, 25), ('c', 0, 5), ('d', -90, 5), ('e', 180, 10), ('f', 0, 70)) + ((('g', 60, -35), ('h', 120, -35), ('i', 20, -60), ('j', -30, -45)) if tag == 'male' else (('g', 90, -20), ('h', 150, 0), ('i', 20, -50), ('j', -60, -30)))))
for nm, az, el in views:
    RS.shot(f'{out}_{nm}.png', ctr, az=az, el=el, dist=0.5, lens=70, res=(800, 800))
print('HANDTEST_DONE')

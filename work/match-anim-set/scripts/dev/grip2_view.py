"""debug: both hands on the racket (right grip + left HANDLE or THROAT) - hand-only close-up.  blender -b <stage> --python grip2_view.py -- <tag> <mode> <out>"""
import sys, json, math
sys.path.insert(0, '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/match-anim-set/scripts')
import numpy as np, bpy
from mathutils import Vector, Quaternion, Matrix
from common import *
tag, mode, outp = args_after_dashes()[:3]
hj = json.load(open(f'{DATA}/hands_{tag}.json'))
rinfo = json.load(open(f'{DATA}/racket_{tag}.json'))
rig = [o for o in bpy.data.objects if o.type == 'ARMATURE'][0]
for n, a in hj['right_grip'].items():
    rig.pose.bones[n].rotation_quaternion = Quaternion((1, 0, 0), math.radians(a))
Lg = hj['left_handle' if mode == 'handle' else 'left_throat']
for n, a in Lg['angles'].items():
    rig.pose.bones[n].rotation_quaternion = Quaternion((1, 0, 0), math.radians(a))
bpy.context.view_layer.update()
Mrk = np.array(rinfo['racket_world_bind']); T = np.array(Lg['T_hand_in_racket'])
rig.pose.bones['LeftHand'].matrix = Matrix((Mrk @ T).tolist())
bpy.context.view_layer.update()
sc = bpy.context.scene
for o in bpy.data.objects:
    if o.type in ('CAMERA', 'LIGHT'): o.hide_render = True
sc.render.engine = 'BLENDER_WORKBENCH'
sh = sc.display.shading; sh.light = 'STUDIO'; sh.color_type = 'MATERIAL'; sh.show_xray = False
sc.world = bpy.data.worlds.new('w'); sc.world.color = (0.25, 0.25, 0.28)
cam_d = bpy.data.cameras.new('c'); cam = bpy.data.objects.new('c', cam_d); sc.collection.objects.link(cam); sc.camera = cam
cam_d.type = 'ORTHO'
c = np.array(Mrk[:3, 3]) + np.array(Mrk[:3, 1]) * 0.07
for nm, az, el in (('a', 0, 25), ('b', 90, 25), ('c', 200, 40), ('d', 300, 10)):
    a = math.radians(az); e = math.radians(el)
    cc = Vector(c.tolist())
    cam.location = cc + Vector((math.sin(a) * math.cos(e), -math.cos(a) * math.cos(e), math.sin(e))) * 4
    cam.rotation_euler = (cc - cam.location).to_track_quat('-Z', 'Y').to_euler()
    cam_d.ortho_scale = 0.5; cam_d.clip_start = 0.1; cam_d.clip_end = 30
    sc.render.resolution_x, sc.render.resolution_y = 700, 700
    sc.render.filepath = f'{outp}_{nm}.png'
    bpy.ops.render.render(write_still=True)

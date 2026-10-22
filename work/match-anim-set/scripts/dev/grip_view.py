"""debug: apply the stored right-hand grip angles on the stage rig and render the hand + racket close-up.
blender -b <stage.blend> --python grip_view.py -- <tag> <out_prefix>"""
import sys, json, math
sys.path.insert(0, '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/match-anim-set/scripts')
import bpy
from mathutils import Vector, Quaternion
from common import *
tag, outp = args_after_dashes()[:2]
rep = json.load(open(f'{DATA}/build_rig_{tag}.json'))
rig = [o for o in bpy.data.objects if o.type == 'ARMATURE'][0]
for n, a in rep['right_grip_angles_deg'].items():
    rig.pose.bones[n].rotation_quaternion = Quaternion((1, 0, 0), math.radians(a))
bpy.context.view_layer.update()
sc = bpy.context.scene
for o in bpy.data.objects:
    if o.type in ('CAMERA', 'LIGHT'): o.hide_render = True
sc.render.engine = 'BLENDER_WORKBENCH'
sh = sc.display.shading; sh.light = 'STUDIO'; sh.color_type = 'MATERIAL'; sh.show_xray = False
sc.world = bpy.data.worlds.new('w'); sc.world.color = (0.25, 0.25, 0.28)
cam_d = bpy.data.cameras.new('c'); cam = bpy.data.objects.new('c', cam_d); sc.collection.objects.link(cam); sc.camera = cam
cam_d.type = 'ORTHO'
hp = rig.pose.bones['RightHand'].matrix.translation
for nm, az, el in (('a', 0, 20), ('b', 90, 20), ('c', 200, 35)):
    a = math.radians(az); e = math.radians(el)
    c = Vector(hp) + Vector((0.0, -0.05, 0.0))
    cam.location = c + Vector((math.sin(a) * math.cos(e), -math.cos(a) * math.cos(e), math.sin(e))) * 4
    cam.rotation_euler = (c - cam.location).to_track_quat('-Z', 'Y').to_euler()
    cam_d.ortho_scale = 0.55; cam_d.clip_start = 0.1; cam_d.clip_end = 30
    sc.render.resolution_x, sc.render.resolution_y = 800, 800
    sc.render.filepath = f'{outp}_{nm}.png'
    bpy.ops.render.render(write_still=True)

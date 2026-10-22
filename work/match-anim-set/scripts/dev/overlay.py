"""debug: render the hero body (X-ray) with the rig drawn on top.  blender -b <source.blend> --python overlay.py -- <tag> <spec.json> <out_prefix> [views]"""
import sys, json, math
sys.path.insert(0, '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/match-anim-set/scripts')
import bpy
from mathutils import Vector
from common import *
from rigbuild import *

tag, specp, outp = args_after_dashes()[:3]
views = args_after_dashes()[3:] or ['front', 'side']
spec = json.load(open(specp))
body = bpy.data.objects[HERO[tag]['body']]
rig = build_armature(spec, 'Rig_' + HERO[tag]['label'])
viz = bone_viz(rig, radius=0.005)
sc = bpy.context.scene
for o in bpy.data.objects:
    if o.type in ('CAMERA', 'LIGHT', 'EMPTY'):
        o.hide_render = True
    if o.name.startswith(('Face', 'Hair')):
        o.hide_render = True
rig.hide_render = True
sc.render.engine = 'BLENDER_WORKBENCH'
sh = sc.display.shading
sh.light = 'FLAT'; sh.color_type = 'OBJECT'; sh.show_xray = True; sh.xray_alpha = 0.22; sh.show_shadows = False
body.color = (0.75, 0.78, 0.85, 1); viz.color = (1.0, 0.1, 0.1, 1); viz.show_in_front = True
sc.world = bpy.data.worlds.new('w'); sc.world.use_nodes = False; sc.world.color = (0.12, 0.12, 0.14)
sc.render.image_settings.file_format = 'PNG'
cam_d = bpy.data.cameras.new('c'); cam = bpy.data.objects.new('c', cam_d); sc.collection.objects.link(cam); sc.camera = cam
cam_d.type = 'ORTHO'
def shoot(name, center, az, scale, res=(900, 1100), el=0):
    a = math.radians(az); e = math.radians(el)
    cam.location = Vector(center) + Vector((math.sin(a) * math.cos(e), -math.cos(a) * math.cos(e), math.sin(e))) * 6
    cam.rotation_euler = (Vector(center) - cam.location).to_track_quat('-Z', 'Y').to_euler()
    cam_d.ortho_scale = scale
    cam_d.clip_start = 0.1; cam_d.clip_end = 30
    sc.render.resolution_x, sc.render.resolution_y = res
    sc.render.filepath = f'{outp}_{name}.png'
    bpy.ops.render.render(write_still=True)
H = spec['height']
for v in views:
    if v == 'front': shoot('front', (0, 0, H * 0.5), 0, 2.0 if tag == 'male' else 1.2 + 0.0, res=(1000, 1000) if False else (700, 1000))
    if v == 'side': shoot('side', (0, 0, H * 0.5), 90, 2.0, res=(700, 1000))
    if v == 'upper': shoot('upper_front', (0.0, 0, 1.15), 0, 1.4, res=(1000, 800))
    if v == 'upper_side': shoot('upper_side', (0.0, 0, 1.15), 90, 1.4, res=(1000, 800))
    if v == 'arm': shoot('arm_front', (0.35 if tag == 'male' else 0.18, 0, 1.1), 0, 0.9, res=(900, 900))
    if v == 'arm_side': shoot('arm_side', (0.0, -0.05, 1.1), 90, 0.9, res=(900, 900))
    if v == 'leg': shoot('leg_front', (0.1, 0, 0.45), 0, 1.0, res=(800, 1000))
    if v == 'leg_side': shoot('leg_side', (0.0, 0, 0.45), 90, 1.0, res=(800, 1000))
    if v == 'head': shoot('head_side', (0.0, -0.03, 1.5), 90, 0.6, res=(800, 800))

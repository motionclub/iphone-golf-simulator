"""debug: Blender automatic weights on the fitted rig, then stress poses rendered (Workbench solid).
blender -b <source.blend> --python skin_test.py -- <tag> <spec.json> <out_prefix>"""
import sys, json, math
sys.path.insert(0, '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/match-anim-set/scripts')
import bpy
from mathutils import Vector, Quaternion, Matrix
from common import *
from rigbuild import *

tag, specp, outp = args_after_dashes()[:3]
spec = json.load(open(specp))
body = bpy.data.objects[HERO[tag]['body']]
rig = build_armature(spec, 'Rig_' + HERO[tag]['label'])
bpy.context.view_layer.update()
for o in bpy.context.view_layer.objects: o.select_set(False)
body.select_set(True); rig.select_set(True)
bpy.context.view_layer.objects.active = rig
bpy.ops.object.parent_set(type='ARMATURE_AUTO')
print('auto weights done; groups', len(body.vertex_groups))

def rot_world(name, axis, deg):
    """rotate bone `name` about world axis through its head by deg, on top of the current pose of its parents."""
    pb = rig.pose.bones[name]
    bpy.context.view_layer.update()
    R = Quaternion(Vector(axis).normalized(), math.radians(deg)).to_matrix().to_4x4()
    # current armature-space matrix of the bone, rotate about its head
    M = pb.matrix.copy()
    h = M.translation.copy()
    Mn = Matrix.Translation(h) @ R @ Matrix.Translation(-h) @ M
    pb.matrix = Mn
    bpy.context.view_layer.update()

def reset():
    for pb in rig.pose.bones:
        pb.rotation_quaternion = (1, 0, 0, 0); pb.location = (0, 0, 0)
    bpy.context.view_layer.update()

sc = bpy.context.scene
for o in bpy.data.objects:
    if o.type in ('CAMERA', 'LIGHT', 'EMPTY'): o.hide_render = True
rig.hide_render = True
sc.render.engine = 'BLENDER_WORKBENCH'
sh = sc.display.shading
sh.light = 'STUDIO'; sh.color_type = 'SINGLE'; sh.single_color = (0.8, 0.8, 0.82); sh.show_xray = False
sc.world = bpy.data.worlds.new('w'); sc.world.color = (0.2, 0.2, 0.22)
sc.render.image_settings.file_format = 'PNG'
cam_d = bpy.data.cameras.new('c'); cam = bpy.data.objects.new('c', cam_d); sc.collection.objects.link(cam); sc.camera = cam
cam_d.type = 'ORTHO'
def shoot(name, center, az, scale, res=(800, 800)):
    a = math.radians(az)
    cam.location = Vector(center) + Vector((math.sin(a), -math.cos(a), 0.15)) * 6
    cam.rotation_euler = (Vector(center) - cam.location).to_track_quat('-Z', 'Y').to_euler()
    cam_d.ortho_scale = scale; cam_d.clip_start = 0.1; cam_d.clip_end = 30
    sc.render.resolution_x, sc.render.resolution_y = res
    sc.render.filepath = f'{outp}_{name}.png'
    bpy.ops.render.render(write_still=True)

H = spec['height']
# 1 arms raised forward 100 deg (rotate about the world X axis: hero faces -Y; raising forward = rotating arm tip toward -Y)
reset()
for sd, sgn in (('Left', 1), ('Right', -1)):
    rot_world(f'{sd}UpperArm', (1, 0, 0), 100)   # tip (down) -> toward -Y  (rotation about +X moves -Z toward -Y... check in image)
shoot('t1_armsfwd_front', (0, 0, 1.2), 0, 1.6); shoot('t1_armsfwd_side', (0, 0, 1.2), 90, 1.6)
# 2 arm out/up to 150 deg abduction
reset()
for sd, sgn in (('Left', 1), ('Right', -1)):
    rot_world(f'{sd}UpperArm', (0, 1, 0), -sgn * 110)
shoot('t2_armsup_front', (0, 0, 1.2), 0, 1.6)
# 3 elbow bend 110
reset()
for sd in ('Left', 'Right'):
    rot_world(f'{sd}LowerArm', (1, 0, 0), 110)
shoot('t3_elbow_front', (0, 0, 1.1), 0, 1.6); shoot('t3_elbow_side', (0.0, 0, 1.1), 90, 1.6)
# 4 knee bend 90 + hip flexion 50
reset()
for sd in ('Left', 'Right'):
    rot_world(f'{sd}UpperLeg', (-1, 0, 0), 50)
    rot_world(f'{sd}LowerLeg', (1, 0, 0), 90)
shoot('t4_squat_side', (0, 0, 0.8), 90, 2.0, res=(800, 1000)); shoot('t4_squat_front', (0, 0, 0.8), 0, 2.0, res=(800, 1000))
# 5 spine twist 80 (about world Z) distributed + forward lean
reset()
for n in ('Spine', 'Chest', 'UpperChest'):
    rot_world(n, (0, 0, 1), 28)
shoot('t5_twist_front', (0, 0, 1.2), 0, 1.6); shoot('t5_twist_top', (0, 0, 1.2), 35, 1.6)
reset()
for n in ('Spine', 'Chest', 'UpperChest'):
    rot_world(n, (-1, 0, 0), 18)   # lean forward
shoot('t6_lean_side', (0, 0, 1.0), 90, 2.0, res=(800, 1000))
reset()
rot_world('Head', (0, 0, 1), 50); rot_world('Neck', (0, 0, 1), 20)
shoot('t7_head_front', (0, -0.02, 1.5), 0, 0.7, res=(800, 800))
reset()

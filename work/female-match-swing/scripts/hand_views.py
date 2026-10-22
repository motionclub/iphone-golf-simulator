"""Render the RIGHT hand of a body FBX from 12 reference-sheet-like angles (workbench, smooth, studio light).
args: --in fbx --out dir --tag t [--mesh Body] [--pose rest|relaxed]  (relaxed = the game's soft finger curl applied on the armature)"""
import bpy, sys, os, math
from mathutils import Vector, Quaternion, Matrix
A = sys.argv[sys.argv.index("--")+1:]
def arg(n, d=None): return A[A.index(n)+1] if n in A else d
IN, OUT, TAG, MESH = arg("--in"), arg("--out"), arg("--tag"), arg("--mesh", "Body")
os.makedirs(OUT, exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True); bpy.ops.import_scene.fbx(filepath=IN)
rig = next(o for o in bpy.data.objects if o.type == 'ARMATURE')
for o in bpy.data.objects:
    if o.type == 'MESH':
        if o.name != MESH: o.hide_render = True
        else:
            for p in o.data.polygons: p.use_smooth = True
if rig.animation_data: rig.animation_data.action = None
for pb in rig.pose.bones: pb.rotation_mode = 'QUATERNION'; pb.matrix_basis.identity()
bpy.context.view_layer.update()
sc = bpy.context.scene; sc.render.engine = 'BLENDER_WORKBENCH'
sh = sc.display.shading; sh.light = 'MATCAP'; sh.studio_light = 'basic_side.exr' if False else sh.studio_light
sh.color_type = 'SINGLE'; sh.single_color = (0.86, 0.62, 0.45); sh.show_cavity = False
sc.render.resolution_x = sc.render.resolution_y = 520
sc.world = bpy.data.worlds.new("w"); sc.world.color = (0.85, 0.85, 0.85)
cam = bpy.data.objects.new("C", bpy.data.cameras.new("C")); sc.collection.objects.link(cam); sc.camera = cam; cam.data.lens = 85
side = "Right"
b = rig.pose.bones
hand = b[side + "Hand"]; mid = b[side + "MiddleIntermediate"]
c = rig.matrix_world @ ((hand.head + mid.tail) / 2 + (hand.head - hand.head) )
# hand frame from the rest pose
fwd = (rig.matrix_world @ mid.tail - rig.matrix_world @ hand.head).normalized()   # along the fingers
lat = (rig.matrix_world @ b[side + "IndexProximal"].head - rig.matrix_world @ b[side + "LittleProximal"].head).normalized()
nrm = fwd.cross(lat).normalized()    # palm/back axis
views = {"dorsal": nrm, "palm": -nrm, "thumb": lat, "pinky": -lat, "front": fwd, "rear": -fwd,
         "q_dorsal": (nrm + fwd * .6).normalized(), "q_palm": (-nrm + fwd * .6).normalized(),
         "q_thumb_back": (lat - fwd * .6).normalized(), "q_pinky_back": (-lat - fwd * .6).normalized()}
dist = 0.55
for name, d in views.items():
    cam.location = c + d * dist
    up = Vector((0, 0, 1)) if abs(d.z) < .9 else Vector((0, 1, 0))
    cam.rotation_euler = (c - cam.location).to_track_quat('-Z', 'Y').to_euler()
    sc.render.filepath = os.path.join(OUT, f"{TAG}_{name}.png"); bpy.ops.render.render(write_still=True)
print("DONE", c, fwd, lat, nrm)

"""Close-up renders of a hero's hands at a given frame of each action (workbench). args: --in fbx --out dir --tag t --frames a,b [--rest]"""
import bpy, sys, os, math
from mathutils import Vector
A = sys.argv[sys.argv.index("--")+1:]
def arg(n, d=None): return A[A.index(n)+1] if n in A else d
IN, OUT, TAG = arg("--in"), arg("--out"), arg("--tag")
FR = [int(x) for x in arg("--frames", "1").split(",")]
ACT = arg("--action")
os.makedirs(OUT, exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=IN)
rig = next(o for o in bpy.data.objects if o.type == 'ARMATURE')
for o in bpy.data.objects:
    if o.type == 'MESH' and (o.name.startswith("Hair") or o.name.startswith("CLUB") or o.name.startswith("Kit_")): o.hide_render = True
sc = bpy.context.scene
sc.render.engine = 'BLENDER_WORKBENCH'; sc.display.shading.light = 'STUDIO'; sc.display.shading.color_type = 'SINGLE'
sc.display.shading.single_color = (0.85, 0.6, 0.4); sc.render.resolution_x = sc.render.resolution_y = 500
cam = bpy.data.objects.new("C", bpy.data.cameras.new("C")); sc.collection.objects.link(cam); sc.camera = cam; cam.data.lens = 50
if ACT:
    act = next(a for a in bpy.data.actions if a.name.endswith(ACT) and a.name.startswith("Rig_"))
    rig.animation_data_create(); rig.animation_data.action = act
elif "--rest" in A:
    if rig.animation_data: rig.animation_data.action = None
    for pb in rig.pose.bones: pb.matrix_basis.identity()
for f in FR:
    sc.frame_set(f); bpy.context.view_layer.update()
    for side in ("Left", "Right"):
        hb = rig.pose.bones[side + "Hand"]; mid = rig.pose.bones[side + "MiddleProximal"]
        c = rig.matrix_world @ ((hb.head + rig.pose.bones[side+"MiddleIntermediate"].head) / 2)
        for vi, d in enumerate([Vector((0, -1, 0)), Vector((1 if side=="Left" else -1, 0, 0)), Vector((0, 1, 0))]):
            cam.location = c - d * -0.32 if False else c + (-d) * -0.32
            cam.location = c + d * 0.32 * -1
            look = (c - cam.location).normalized()
            cam.rotation_euler = look.to_track_quat('-Z', 'Y').to_euler()
            sc.render.filepath = os.path.join(OUT, f"{TAG}_{ACT or 'rest'}_{f:03d}_{side}_{vi}.png")
            bpy.ops.render.render(write_still=True)

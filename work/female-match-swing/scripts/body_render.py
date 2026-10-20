"""Full-body workbench renders of a clip at evenly spaced frames, 2 views. args: --in fbx --action suffix --out dir --tag t --n 8 [--views front,side]"""
import bpy, sys, os
from mathutils import Vector
A = sys.argv[sys.argv.index("--")+1:]
def arg(n, d=None): return A[A.index(n)+1] if n in A else d
IN, OUT, TAG, ACT = arg("--in"), arg("--out"), arg("--tag"), arg("--action", "Scene")
N = int(arg("--n", "8")); os.makedirs(OUT, exist_ok=True)
CLUB = arg("--club")
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=IN)
rig = next(o for o in bpy.data.objects if o.type == 'ARMATURE')
for o in bpy.data.objects:
    if o.type == 'MESH' and (o.name.startswith("Hair") or (o.name.startswith("CLUB") and o.name != CLUB)): o.hide_render = True
act = next(a for a in bpy.data.actions if a.name.startswith("Rig_") and a.name.split("|")[-1] == ACT)
rig.animation_data_create(); rig.animation_data.action = act
f0, f1 = [int(x) for x in act.frame_range]
FR = [int(x) for x in arg("--frames").split(",")] if arg("--frames") else [round(f0 + (f1 - f0) * i / (N - 1)) for i in range(N)]
sc = bpy.context.scene
sc.render.engine = 'BLENDER_WORKBENCH'; sc.display.shading.light = 'STUDIO'; sc.display.shading.color_type = 'OBJECT'
for o in bpy.data.objects:
    if o.type == 'MESH': o.color = (0.25, 0.25, 0.28, 1) if (o.name.startswith("CLUB") or o.name in ("Grip","ButtCap","Racket_Classic","StringBed")) else (0.85, 0.62, 0.45, 1)
sc.render.resolution_x, sc.render.resolution_y = 400, 520
cam = bpy.data.objects.new("C", bpy.data.cameras.new("C")); sc.collection.objects.link(cam); sc.camera = cam
cam.data.type = 'ORTHO'; cam.data.ortho_scale = 2.3
VIEWS = {"front": Vector((-1, 0, 0)), "side": Vector((0, 1, 0)), "back": Vector((1, 0, 0)), "tgt": Vector((0, -1, 0))}
views = arg("--views", "front,side").split(",")
for f in FR:
    sc.frame_set(f)
    for v in views:
        d = VIEWS[v]; c = Vector((0, 0, 0.95))
        cam.location = c + d * 5; cam.rotation_euler = (c - cam.location).to_track_quat('-Z', 'Y').to_euler()
        sc.render.filepath = os.path.join(OUT, f"{TAG}_{ACT}_{f:03d}_{v}.png"); bpy.ops.render.render(write_still=True)
print("FRAMES", FR)

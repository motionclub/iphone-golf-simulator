"""Scratch: import the EnvV4 shrubs/trees read-only and render them for style reference (role A4)."""
import bpy, os, math
from mathutils import Vector
REPO = "/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator"
SRC = os.path.join(REPO, "Unity/Assets/Resources/Tennis/EnvV4")
OUT = os.path.join(REPO, "work/postcard-look/lib_props/envv4_ref.png")
bpy.ops.wm.read_factory_settings(use_empty=True)
pal = bpy.data.images.load(os.path.join(SRC, "EnvV4_Palette.png"))
x = 0.0
for n in ["EnvV4_ShrubA", "EnvV4_ShrubB", "EnvV4_ShrubC", "EnvV4_TreeBroadleafA", "EnvV4_TreeFlowering"]:
    before = set(bpy.data.objects)
    bpy.ops.import_scene.fbx(filepath=os.path.join(SRC, n + ".fbx"))
    new = [o for o in bpy.data.objects if o not in before and o.type == 'MESH']
    for o in new:
        me = o.data
        print(n, o.name, "verts", len(me.vertices), "faces", len(me.polygons), "tris", sum(len(p.vertices) - 2 for p in me.polygons),
              "dims", tuple(round(d, 2) for d in o.dimensions), "uv", [l.name for l in me.uv_layers], "mats", [m.name for m in me.materials])
        mm = bpy.data.materials.new("pal"); me.materials.append(mm)
        for m in me.materials:
            nt = m.node_tree
            tex = nt.nodes.new("ShaderNodeTexImage"); tex.image = pal
            bsdf = next(nd for nd in nt.nodes if nd.type == 'BSDF_PRINCIPLED')
            nt.links.new(tex.outputs[0], bsdf.inputs["Base Color"])
    roots = [o for o in bpy.data.objects if o not in before and o.parent is None]
    mx = max(max(o.dimensions) for o in new)
    for r in roots:
        r.location.x += x
    x += 4.0
sc = bpy.context.scene
sc.render.engine = 'BLENDER_EEVEE'
sc.render.resolution_x, sc.render.resolution_y = 1600, 600
cam = bpy.data.objects.new("cam", bpy.data.cameras.new("cam")); sc.collection.objects.link(cam); sc.camera = cam
cam.location = (8, -14, 4); cam.rotation_euler = (math.radians(78), 0, 0)
cam.data.type = 'ORTHO'; cam.data.ortho_scale = 22
sun = bpy.data.objects.new("sun", bpy.data.lights.new("sun", 'SUN')); sc.collection.objects.link(sun)
sun.rotation_euler = (math.radians(50), 0, math.radians(30)); sun.data.energy = 3
w = bpy.data.worlds.new("w"); sc.world = w
w.color = (0.5, 0.6, 0.7)
try:
    w.node_tree.nodes["Background"].inputs[0].default_value = (0.6, 0.7, 0.85, 1); w.node_tree.nodes["Background"].inputs[1].default_value = 0.8
except Exception as e:
    print(e)
sc.view_settings.view_transform = 'Standard'
sc.render.filepath = OUT
bpy.ops.render.render(write_still=True)
print("wrote", OUT)

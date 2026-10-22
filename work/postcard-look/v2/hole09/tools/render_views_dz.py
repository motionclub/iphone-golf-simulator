"""render_views.py - Blender EEVEE previews of a hole 9 blend from the Game-view cameras of landmarks.json (NOT Game-view proof).

  Blender -b --factory-startup --python render_views.py -- --blend X.blend --json landmarks.json --out DIR [--only a,b] [--samples 24] [--scale 1.0]

Unity world yards (x right, y up, z down the hole; tee marker at the origin; y = model z * 1.0936) <-> Blender metres (x, y down the hole, z up):
x_b = x_yd * 0.9144, y_b = z_yd * 0.9144, z_b = y_yd * 0.9144. The address camera is CameraRig.FrameAddress: 4.5 yd behind the ball, 2.4 yd up, looking
1.5 yd ahead of it, ball = ground + 0.06 yd. 60 degree vertical FOV, 900x1600.
"""
import bpy, sys, json, math, os
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree

YD = 0.9144
A = sys.argv[sys.argv.index("--") + 1:]
def opt(n, d=None): return A[A.index(n) + 1] if n in A else d
BLEND, JS, OUT = opt("--blend"), opt("--json"), opt("--out")
ONLY = opt("--only"); SAMPLES = int(opt("--samples", "24")); SCALE = float(opt("--scale", "1.0"))
os.makedirs(OUT, exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=BLEND)
if os.environ.get("TEE_DZ"):
    _t = bpy.data.objects["TEE_BOX"]
    _t.location.z += float(os.environ["TEE_DZ"])
if os.environ.get("TEE_HIDE_SIDES"):
    pass
sc = bpy.context.scene
try: sc.view_settings.view_transform = 'AgX'
except Exception: pass
bg = sc.world.node_tree.nodes.get("Background")
bg.inputs[0].default_value = (0.30, 0.55, 0.90, 1.0); bg.inputs[1].default_value = 1.0
for nm in ("BALL_START", "HOLE_CUP", "MARKER_TEE", "MARKER_PIN", "MARKER_UP"):
    o = bpy.data.objects.get(nm)
    if o is not None: o.hide_render = True
# ground BVH (tops of the collision meshes) for the ball height
dg = bpy.context.evaluated_depsgraph_get()
V, F = [], []
for o in bpy.data.objects:
    if o.type == 'MESH' and o.name.startswith(("TERRAIN", "FAIRWAY", "GREEN", "TEE_BOX", "BUNKER")):
        me = o.data; me.calc_loop_triangles(); mw = o.matrix_world
        b = len(V); V += [tuple(mw @ v.co) for v in me.vertices]
        F += [[b + i for i in t.vertices] for t in me.loop_triangles]
bvh = BVHTree.FromPolygons(V, F)
def ground(x, y):
    h = bvh.ray_cast((x, y, 60.0), (0, 0, -1), 200.0)
    return h[0].z if h[0] is not None else 0.0
def cam_obj(name, loc, look, fov):
    c = bpy.data.cameras.new(name); ob = bpy.data.objects.new(name, c); sc.collection.objects.link(ob)
    ob.location = loc; ob.rotation_euler = (Vector(look) - Vector(loc)).to_track_quat('-Z', 'Y').to_euler()
    c.sensor_fit = 'VERTICAL'; c.angle_y = math.radians(fov); c.clip_start = 0.27; c.clip_end = 6000
    return ob
def blender_cam(shot):
    if shot.get("kind") == "address":
        bx, by = shot["ball"][0] * YD, shot["ball"][1] * YD
        ax, ay = shot["aim"][0] * YD, shot["aim"][1] * YD
        d = Vector((ax - bx, ay - by, 0)).normalized()
        ball = Vector((bx, by, ground(bx, by) + 0.06 * YD))
        back, up, ahead = (3.2, 1.4, 2.5) if shot.get("putting") else (4.5, 2.4, 1.5)
        return ball - d * (back * YD) + Vector((0, 0, up * YD)), ball + d * (ahead * YD), 60.0
    p, l = shot["pos"], shot["look"]
    return Vector((p[0] * YD, p[2] * YD, p[1] * YD)), Vector((l[0] * YD, l[2] * YD, l[1] * YD)), float(shot.get("fov", 60))
cfg = json.load(open(JS))
shots = cfg["shots"] + cfg.get("extra_previews", [])
for s in shots:
    if ONLY and s["name"] not in ONLY.split(","): continue
    loc, look, fov = blender_cam(s)
    ob = cam_obj("CAM_" + s["name"], loc, look, fov)
    sc.camera = ob
    res = tuple(int(v * SCALE) for v in s.get("preview_res", (900, 1600)))      # Game-view shots are 900x1600; extra previews carry their own size
    sc.render.resolution_x, sc.render.resolution_y = res; sc.render.resolution_percentage = 100
    sc.render.filepath = os.path.join(OUT, s["name"] + ".png"); sc.render.image_settings.file_format = 'PNG'
    try: sc.eevee.taa_render_samples = SAMPLES
    except Exception: pass
    bpy.ops.render.render(write_still=True)
    print("RENDERED", s["name"], res, "cam", tuple(round(v, 2) for v in loc), flush=True)

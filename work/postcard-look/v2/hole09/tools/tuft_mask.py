"""tuft_mask.py - BLENDER-SIDE PROXY for GRASS_STILL_ALIVE (NOT a Game-view measure): the share of each still frame that is covered by tuft silhouettes, from a flat Workbench mask render.

    Blender -b --factory-startup --python tuft_mask.py -- --blend X.blend --json landmarks.json --out DIR [--label NAME]

Every PLANT_TUFT* object is painted white, every other mesh black (Workbench, flat lighting, object colours, no anti-aliasing, sky = the world colour 0.5 grey so it is excluded), from the three Game-view cameras of
landmarks.json (the address camera = CameraRig.FrameAddress: 4.5 yd behind the ball, 2.4 yd up, 60 deg vertical FOV, 900 x 1600; the landmark camera with its own fov). Prints, per still, the tuft share of the whole frame
and of the lower 60 % (excluding sky), and the share of 16 x 16 px cells that contain at least one tuft pixel. Writes DIR/<still>_mask.png. The Game-view number is the integrator's (PostcardLookStills).
"""
import bpy, sys, json, math, os
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree

YD = 0.9144
A = sys.argv[sys.argv.index("--") + 1:]
def opt(n, d=None): return A[A.index(n) + 1] if n in A else d
BLEND, JS, OUT, LABEL = opt("--blend"), opt("--json"), opt("--out"), opt("--label", "")
os.makedirs(OUT, exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=BLEND)
sc = bpy.context.scene
sc.render.engine = 'BLENDER_WORKBENCH'
sh = sc.display.shading
sh.light = 'FLAT'; sh.color_type = 'OBJECT'; sh.show_cavity = False; sh.show_shadows = False; sh.show_object_outline = False; sh.show_specular_highlight = False
sc.render.film_transparent = False
sc.display.render_aa = 'OFF'
sc.view_settings.view_transform = 'Standard'
try: sc.view_settings.look = 'None'
except Exception: pass
bg = sc.world.node_tree.nodes.get("Background")
for sock in (bg.inputs[0],): sock.default_value = (0.5, 0.5, 0.5, 1.0)
bg.inputs[1].default_value = 1.0
for nm in ("BALL_START", "HOLE_CUP", "MARKER_TEE", "MARKER_PIN", "MARKER_UP"):
    o = bpy.data.objects.get(nm)
    if o is not None: o.hide_render = True
n_t = 0
for o in bpy.data.objects:
    if o.type != 'MESH': continue
    if all(c.name == "ASSET_LIBRARY" for c in o.users_collection) and o.users_collection: continue
    if o.name.startswith("PLANT_TUFT"):
        o.color = (1.0, 1.0, 1.0, 1.0); n_t += 1
    else:
        o.color = (0.0, 0.0, 0.0, 1.0)
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
res_all = {}
for s in cfg["shots"]:
    loc, look, fov = blender_cam(s)
    ob = cam_obj("CAM_" + s["name"], loc, look, fov)
    sc.camera = ob
    sc.render.resolution_x, sc.render.resolution_y = 900, 1600; sc.render.resolution_percentage = 100
    path = os.path.join(OUT, f"{s['name']}_mask{LABEL}.png")
    sc.render.filepath = path; sc.render.image_settings.file_format = 'PNG'; sc.render.image_settings.color_mode = 'RGB'
    bpy.ops.render.render(write_still=True)
    img = bpy.data.images.load(path)
    a = np.empty(900 * 1600 * 4, np.float32); img.pixels.foreach_get(a); a = a.reshape(1600, 900, 4)[::-1, :, :3]
    bpy.data.images.remove(img)
    lum = a.mean(-1)
    tuft = lum > 0.75                                    # white
    sky = np.abs(lum - 0.5) < 0.04                       # the world colour (sRGB 0.5 grey = linear .214 -> Standard view transform shows 0.5)
    ground_px = ~sky
    lower = slice(int(1600 * 0.40), 1600)
    share_all = float(tuft.sum() / max(ground_px.sum(), 1))
    share_low = float(tuft[lower].sum() / max(ground_px[lower].sum(), 1))
    cells = tuft[:1600 // 16 * 16, :896].reshape(100, 16, 56, 16).any(axis=(1, 3))
    cell_share = float(cells.mean())
    cell_low = float(cells[int(100 * 0.40):].mean())
    res_all[s["name"]] = dict(tuft_px_share_nonsky=share_all, tuft_px_share_lower60=share_low, cells16_with_tuft=cell_share, cells16_with_tuft_lower60=cell_low)
    print(f"TUFTMASK {s['name']}{LABEL}: tufts {n_t}; tuft pixels {share_all:.4%} of the non-sky frame, {share_low:.4%} of the lower 60 %; 16 px cells with a tuft pixel {cell_share:.2%} (lower 60 %: {cell_low:.2%})", flush=True)
json.dump(res_all, open(os.path.join(OUT, f"tuft_mask{LABEL}.json"), "w"), indent=1)

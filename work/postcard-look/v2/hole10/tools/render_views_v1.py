"""Blender EEVEE previews of a staged hole 10 blend from the SAME camera rigs the Game view uses (NOT Game-view proof).

  Blender -b STAGED.blend --python render_views.py -- --shots landmarks.json --out DIR [--only tee,approach] [--res 900x1600] [--samples 24] [--prefix p_]

shots JSON = the stills schema of work/postcard-look/RUNTIME.md v2.8 (address: ball/aim in course yards; landmark: pos/look in Unity WORLD
YARDS, fov vertical degrees) plus an optional "aerial" kind: {"kind": "aerial", "pos": [x, y, z], "look": [x, y, z], "fov": 40} in the same
world yards. Mapping (HoleView.BuildFromModel): course x = Blender x / 0.9144, course d (= Unity z) = Blender y / 0.9144, Unity y = Blender z x 1.0936.
CameraRig.FrameAddress: camera = ball - aim x 4.5 yd + 2.4 yd up, looks at ball + aim x 1.5 yd, fov 60 (vertical), 900 x 1600.
Lighting imitates GolfAtmosphere.Holes[10] (key 2.3 at az heading+40 / el 32, warm (1,.80,.58); trilight-ish dusk world); there is no fog and no
GolfLava shader here: the lava is the Principled preview of LK_LAVA. These are shape / scale previews only.
"""
import sys
import os
import json
import math

import bpy
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree

YD = 0.9144
args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []


def opt(n, d=None):
    return args[args.index(n) + 1] if n in args else d


SHOTS = json.load(open(opt("--shots")))["shots"]
OUT = opt("--out")
ONLY = opt("--only")
PREFIX = opt("--prefix", "")
RES = tuple(int(v) for v in opt("--res", "900x1600").split("x"))
SAMPLES = int(opt("--samples", "24"))
EXPOSURE = float(opt("--exposure", "0.0"))
os.makedirs(OUT, exist_ok=True)
GROUND = ("TERRAIN", "FAIRWAY", "GREEN", "TEE_BOX", "BUNKER", "CART_PATH")


def ground_bvh():
    V, F = [], []
    for ob in bpy.data.objects:
        if ob.type != 'MESH' or not ob.name.startswith(GROUND):
            continue
        me = ob.data
        mw = ob.matrix_world
        base = len(V)
        V += [tuple(mw @ v.co) for v in me.vertices]
        for p in me.polygons:
            F.append(tuple(base + i for i in p.vertices))
    return BVHTree.FromPolygons(V, F)


BVH = ground_bvh()


def ground_z(x, y):
    hit = BVH.ray_cast(Vector((x, y, 60.0)), Vector((0, 0, -1)), 200.0)
    return None if hit[0] is None else hit[0].z


def setup_light(heading_deg=57.7):
    sc = bpy.context.scene
    for o in list(bpy.data.objects):
        if o.type == 'LIGHT':
            bpy.data.objects.remove(o, do_unlink=True)
    az, el = math.radians(heading_deg + 40.0), math.radians(32.0)
    to_sun = Vector((math.sin(az) * math.cos(el), math.cos(az) * math.cos(el), math.sin(el)))
    ld = bpy.data.lights.new("PV_SUN", 'SUN')
    ld.energy = 2.3 * math.pi * 0.9
    ld.color = (1.0, 0.80, 0.58)
    ld.angle = math.radians(3.0)
    so = bpy.data.objects.new("PV_SUN", ld)
    sc.collection.objects.link(so)
    so.rotation_euler = to_sun.to_track_quat('Z', 'Y').to_euler()
    # world: ember horizon -> aubergine zenith (Sky_Crater_C is a painted panorama in Unity; this is only a stand-in)
    w = bpy.data.worlds.new("PV_WORLD")
    w.use_nodes = True
    nt = w.node_tree
    nt.nodes.clear()
    tc = nt.nodes.new("ShaderNodeTexCoord")
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    bg = nt.nodes.new("ShaderNodeBackground")
    outn = nt.nodes.new("ShaderNodeOutputWorld")
    nt.links.new(tc.outputs["Generated"], sep.inputs[0])
    mp = nt.nodes.new("ShaderNodeMapRange")
    mp.inputs[1].default_value, mp.inputs[2].default_value = 0.45, 0.95
    nt.links.new(sep.outputs["Z"], mp.inputs[0])
    nt.links.new(mp.outputs[0], ramp.inputs[0])
    cr = ramp.color_ramp
    cr.elements[0].position, cr.elements[0].color = 0.0, (0.80, 0.30, 0.10, 1)
    cr.elements[1].position, cr.elements[1].color = 1.0, (0.10, 0.06, 0.12, 1)
    nt.links.new(ramp.outputs[0], bg.inputs[0])
    bg.inputs[1].default_value = 1.0
    nt.links.new(bg.outputs[0], outn.inputs[0])
    sc.world = w
    try:
        sc.view_settings.view_transform = 'Standard'
        sc.view_settings.exposure = EXPOSURE
    except Exception:
        pass
    sc.render.engine = 'BLENDER_EEVEE'
    for nm in ("BALL_START", "HOLE_CUP", "MARKER_TEE", "MARKER_PIN", "MARKER_UP"):
        o = bpy.data.objects.get(nm)
        if o is not None:
            o.hide_render = True


def make_cam(name, loc, look, fov_deg):
    cd = bpy.data.cameras.new(name)
    ob = bpy.data.objects.new(name, cd)
    bpy.context.scene.collection.objects.link(ob)
    ob.location = loc
    ob.rotation_euler = (Vector(look) - Vector(loc)).to_track_quat('-Z', 'Y').to_euler()
    cd.sensor_fit = 'VERTICAL'
    cd.angle_y = math.radians(fov_deg)
    cd.clip_start = 0.27
    cd.clip_end = 3000.0
    return ob


def world_to_blender(p):
    return Vector((p[0] * YD, p[2] * YD, p[1] / 1.0936))


def render(cam, path):
    sc = bpy.context.scene
    sc.camera = cam
    sc.render.resolution_x, sc.render.resolution_y = RES
    sc.render.resolution_percentage = 100
    sc.render.filepath = path
    sc.render.image_settings.file_format = 'PNG'
    try:
        sc.eevee.taa_render_samples = SAMPLES
    except Exception:
        pass
    bpy.ops.render.render(write_still=True)


setup_light()
for sh in SHOTS:
    if sh.get("hole", 10) != 10:
        continue
    if ONLY and sh["name"].split("_")[-1] not in ONLY.split(",") and sh["name"] not in ONLY.split(","):
        continue
    kind = sh.get("kind", "landmark" if "pos" in sh else "address")
    ball_obj = None
    if kind == "address":
        bx, by = sh["ball"][0] * YD, sh["ball"][1] * YD
        gz = ground_z(bx, by)
        ball = Vector((bx, by, gz + 0.055))
        ax, ay = sh["aim"][0] * YD - bx, sh["aim"][1] * YD - by
        aim = Vector((ax, ay, 0)).normalized()
        back, up, ahead = (3.2, 1.4, 2.5) if sh.get("putting") else (4.5, 2.4, 1.5)
        loc = ball - aim * back * YD + Vector((0, 0, up * YD))
        look = ball + aim * ahead * YD
        fov = 60.0
    else:
        loc, look = world_to_blender(sh["pos"]), world_to_blender(sh["look"])
        fov = float(sh.get("fov", 60.0))
        ball = None
        if "ball" in sh:
            bx, by = sh["ball"][0] * YD, sh["ball"][1] * YD
            ball = Vector((bx, by, ground_z(bx, by) + 0.055))
    if ball is not None:
        me = bpy.data.meshes.new("PV_BALL")
        import bmesh
        bm = bmesh.new()
        bmesh.ops.create_icosphere(bm, subdivisions=2, radius=0.055)
        bm.to_mesh(me)
        bm.free()
        ball_obj = bpy.data.objects.new("PV_BALL", me)
        bpy.context.scene.collection.objects.link(ball_obj)
        ball_obj.location = ball
        m = bpy.data.materials.new("PV_BALLMAT")
        m.use_nodes = True
        m.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (1, 1, 1, 1)
        me.materials.append(m)
        for p in me.polygons:
            p.use_smooth = True
    cam = make_cam("PV_" + sh["name"], loc, look, fov)
    path = os.path.join(OUT, f"{PREFIX}{sh['name']}.png")
    render(cam, path)
    print(f"[render_views] {sh['name']} cam ({loc.x:.1f}, {loc.y:.1f}, {loc.z:.1f}) m look ({look.x:.1f}, {look.y:.1f}, {look.z:.1f}) fov {fov} -> {path}", flush=True)
    if ball_obj is not None:
        bpy.data.objects.remove(ball_obj, do_unlink=True)

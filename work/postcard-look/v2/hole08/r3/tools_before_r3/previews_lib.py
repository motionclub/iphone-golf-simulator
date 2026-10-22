"""Blender EEVEE previews of hole 8 (NOT Game view). Works on the open scene."""
import math, os
import bpy
from mathutils import Vector
import postcard_lib as P

YD = P.YD


def setup_scene(sky=(150, 196, 240), exposure=0.0):
    sc = bpy.context.scene
    sc.render.engine = 'BLENDER_EEVEE'
    try:
        sc.view_settings.view_transform = 'AgX'
    except Exception:
        pass
    sc.view_settings.exposure = exposure
    world = sc.world
    if world is None:
        world = bpy.data.worlds.new("World"); sc.world = world
    bg = world.node_tree.nodes.get("Background")
    bg.inputs[0].default_value = P.rgb(*sky)
    bg.inputs[1].default_value = 1.0
    for nm_ in ("BALL_START", "HOLE_CUP", "MARKER_TEE", "MARKER_PIN", "MARKER_UP"):   # Unity hides these placeholders
        ob = bpy.data.objects.get(nm_)
        if ob is not None:
            ob.hide_render = True


def cam(name, loc, target, fov_v=60.0, ortho=None):
    P.remove_object(name)
    c = bpy.data.cameras.new(name)
    ob = bpy.data.objects.new(name, c)
    bpy.context.scene.collection.objects.link(ob)
    ob.location = loc
    ob.rotation_euler = (Vector(target) - Vector(loc)).to_track_quat('-Z', 'Y').to_euler()
    c.clip_start = 0.27
    c.clip_end = 6000
    if ortho:
        c.type = 'ORTHO'; c.ortho_scale = ortho
    else:
        c.sensor_fit = 'VERTICAL'
        c.angle_y = math.radians(fov_v)
    return ob


def render(ob, path, res, samples=24):
    P.render_camera(ob.name, path, res, samples)
    return path


def address_cam(name, ball_yd, aim_yd, D, putting=False):
    """CameraRig.FrameAddress: 4.5 yd behind the ball, 2.4 yd up, looking 1.5 yd ahead of the ball (Blender metres)."""
    bx, by = P.m(*ball_yd)
    ax, ay = P.m(*aim_yd)
    # ball rests on the ground: find ground z by ray cast at the ball (top of TERRAIN/FAIRWAY/...)
    z = ground_z(bx, by, D.play_z + 5.0)
    d = Vector((ax - bx, ay - by, 0.0)).normalized()
    ball = Vector((bx, by, z))
    loc = ball - d * 4.5 * YD + Vector((0, 0, 2.4 * YD))
    look = ball + d * 1.5 * YD
    return cam(name, loc, look, 60.0)


def ground_z(x, y, ztop=40.0):
    sc = bpy.context.scene
    dg = bpy.context.evaluated_depsgraph_get()
    best = None
    for pref in ("TEE_BOX", "BUNKER", "GREEN", "FAIRWAY", "TERRAIN"):
        for ob in bpy.data.objects:
            if ob.type == 'MESH' and ob.name.startswith(pref):
                pass
    hit = sc.ray_cast(dg, Vector((x, y, ztop)), Vector((0, 0, -1)), distance=80.0)
    # first hit may be a prop; walk down until a ground-prefixed object is hit
    o = Vector((x, y, ztop))
    for _ in range(12):
        ok, loc, nrm, idx, ob, mw = sc.ray_cast(dg, o, Vector((0, 0, -1)), distance=80.0)
        if not ok:
            return 0.0
        if ob.name.startswith(("TERRAIN", "FAIRWAY", "GREEN", "TEE_BOX", "BUNKER", "CART_PATH")):
            return loc.z
        o = loc + Vector((0, 0, -1e-3))
    return 0.0


def quick(out):
    D = P._ST["D"]
    setup_scene()
    pz = D.play_z
    renders = []
    bx0, by0, bx1, by1 = P._shore_bbox_m(D)
    cx, cy = (bx0 + bx1) / 2, (by0 + by1) / 2
    span = max(bx1 - bx0, by1 - by0) * 1.12
    top = cam("CAM_P_TOP", (cx, cy, 800.0), (cx, cy, 0.0), ortho=span)
    renders.append(render(top, os.path.join(out, "q_top.png"), (700, 1700), 16))
    ov = bpy.data.objects.get("CAM_HOLE_OVERVIEW")
    if ov is not None:
        renders.append(render(ov, os.path.join(out, "q_oblique.png"), (900, 1500), 20))
    c = address_cam("CAM_P_TEE", (0, 0), (19, 178), D)
    renders.append(render(c, os.path.join(out, "q_tee.png"), (900, 1600), 24))
    c = address_cam("CAM_P_APP", (14, 200), (-6, 340), D)
    renders.append(render(c, os.path.join(out, "q_app.png"), (900, 1600), 24))
    return renders

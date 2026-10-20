"""Neutral grey studio render helper (art bible: soft key + fill + rim on grey), headless Eevee.
Lights ride with the camera so every angle is lit like the front. Used for every proof image."""
import math
import bpy
from mathutils import Vector, Quaternion

from common import lin

LIGHTS = [  # name, base location relative to the target (front = -Y), power W, size m
    ('Studio_Key', (-1.3, -1.8, 1.8), 150, 1.6),
    ('Studio_Fill', (1.6, -1.3, 0.9), 80, 1.8),
    ('Studio_Rim', (0.3, 1.6, 1.6), 130, 1.2),
    ('Studio_Top', (0.0, -0.3, 2.1), 45, 1.5),
]


def studio(bg=(0.30, 0.31, 0.33), samples=48, engine='BLENDER_EEVEE', floor=True):
    sc = bpy.context.scene
    sc.render.engine = engine
    try:
        sc.eevee.taa_render_samples = samples
        sc.eevee.use_shadows = True
        sc.eevee.use_raytracing = True
    except Exception:
        pass
    sc.render.image_settings.file_format = 'PNG'
    sc.render.image_settings.color_mode = 'RGB'
    sc.render.film_transparent = False
    sc.view_settings.view_transform = 'AgX'
    sc.view_settings.look = 'None'
    w = bpy.data.worlds.get('Studio_World') or bpy.data.worlds.new('Studio_World')
    sc.world = w
    w.use_nodes = True
    bgn = w.node_tree.nodes['Background']
    bgn.inputs[0].default_value = (*lin(bg), 1)
    bgn.inputs[1].default_value = 0.6
    for name, loc, power, size in LIGHTS:
        if bpy.data.objects.get(name) is None:
            data = bpy.data.lights.new(name, 'AREA')
            data.shape = 'DISK'
            o = bpy.data.objects.new(name, data)
            sc.collection.objects.link(o)
        o = bpy.data.objects[name]
        o.data.energy = power
        o.data.size = size
    cam = bpy.data.objects.get('Studio_Camera')
    if cam is None:
        cd = bpy.data.cameras.new('Studio_Camera')
        cam = bpy.data.objects.new('Studio_Camera', cd)
        sc.collection.objects.link(cam)
    sc.camera = cam
    return cam


def shot(path, target, az=0, el=0, dist=2.0, lens=70, res=(1200, 1200), ortho=None, light_scale=1.0):
    """az 0 = camera on -Y looking +Y; az +90 = camera on +X. el = elevation degrees."""
    sc = bpy.context.scene
    cam = bpy.data.objects['Studio_Camera']
    sc.camera = cam
    a, e = math.radians(az), math.radians(el)
    t = Vector(target)
    cam.location = t + Vector((math.sin(a) * math.cos(e), -math.cos(a) * math.cos(e), math.sin(e))) * dist
    cam.rotation_euler = (t - cam.location).to_track_quat('-Z', 'Y').to_euler()
    cd = cam.data
    cd.clip_start, cd.clip_end = 0.01, 100
    if ortho:
        cd.type, cd.ortho_scale = 'ORTHO', ortho
    else:
        cd.type, cd.lens, cd.sensor_width = 'PERSP', lens, 36
    sc.render.resolution_x, sc.render.resolution_y = res
    sc.render.resolution_percentage = 100
    # lights follow the camera azimuth, scaled with the subject distance
    q = Quaternion((0, 0, 1), a)
    k = max(0.35, dist / 2.0) * light_scale
    for name, loc, power, size in LIGHTS:
        o = bpy.data.objects[name]
        o.location = t + q @ (Vector(loc) * k)
        o.rotation_euler = (t - o.location).to_track_quat('-Z', 'Y').to_euler()
        o.data.energy = power * k * k
        o.data.size = size * k
    sc.render.filepath = str(path)
    bpy.ops.render.render(write_still=True)

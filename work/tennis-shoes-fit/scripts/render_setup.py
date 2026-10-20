"""Neutral grey studio (art bible: soft key + fill + rim) and camera helper for the outfit preview."""
import math
import bpy
from mathutils import Vector, Quaternion
from preview_common import *

LIGHTS = [  # name, base location (front = -Y), power W, size m
    ('Studio_Key', (-2.6, -3.6, 3.6), 330, 3.2),
    ('Studio_Fill', (3.2, -2.6, 1.8), 170, 3.6),
    ('Studio_Rim', (0.6, 3.2, 3.2), 280, 2.4),
    ('Studio_Top', (0.0, -0.6, 4.2), 100, 3.0),
]


def setup(bg=(0.30, 0.31, 0.33), engine='BLENDER_EEVEE', samples=64, cyc_rgb=(0.50, 0.52, 0.56)):
    sc = bpy.context.scene
    sc.render.engine = engine
    try:
        sc.eevee.taa_render_samples = samples
        sc.eevee.use_shadows = True
        sc.eevee.use_raytracing = True
    except Exception:
        pass
    sc.render.image_settings.file_format = 'PNG'
    sc.render.image_settings.color_mode = 'RGBA'
    sc.render.film_transparent = False
    sc.view_settings.view_transform = 'AgX'
    sc.view_settings.look = 'None'
    sc.view_settings.exposure = 0.0
    sc.view_settings.gamma = 1.0
    w = bpy.data.worlds.get('Studio_World') or bpy.data.worlds.new('Studio_World')
    sc.world = w
    w.use_nodes = True
    bgn = w.node_tree.nodes['Background']
    bgn.inputs[0].default_value = (*lin(bg), 1)
    bgn.inputs[1].default_value = 0.5
    # cyclorama (floor + curved wall) on a pivot that turns with the camera azimuth
    piv = bpy.data.objects.get('Cyc_Pivot')
    if piv is None:
        piv = bpy.data.objects.new('Cyc_Pivot', None)
        sc.collection.objects.link(piv)
    cyc = bpy.data.objects.get('Studio_Cyc')
    if cyc is None:
        R = 2.4
        prof = [(-14.0, 0.0), (2.2, 0.0)]
        for k in range(1, 13):
            a = math.radians(90 * k / 12)
            prof.append((2.2 + R * math.sin(a), R - R * math.cos(a)))
        prof.append((2.2 + R, 12.0))
        verts = []
        faces = []
        xs = (-16.0, 16.0)
        for (y, z) in prof:
            verts.append((xs[0], y, z))
            verts.append((xs[1], y, z))
        for i in range(len(prof) - 1):
            a = 2 * i
            faces.append((a, a + 1, a + 3, a + 2))
        me = bpy.data.meshes.new('Studio_Cyc')
        me.from_pydata(verts, [], faces)
        me.update()
        for f in me.polygons:
            f.use_smooth = True
        cyc = bpy.data.objects.new('Studio_Cyc', me)
        sc.collection.objects.link(cyc)
        cyc.parent = piv
        cyc.data.materials.append(material('Studio_Cyc_Grey', cyc_rgb, .9, .05))
    else:
        cyc.data.materials[0].node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value = (*lin(cyc_rgb), 1)
    # lights
    for name, loc, power, size in LIGHTS:
        o = bpy.data.objects.get(name)
        if o is None:
            data = bpy.data.lights.new(name, 'AREA')
            data.shape = 'DISK'
            o = bpy.data.objects.new(name, data)
            sc.collection.objects.link(o)
        o.data.energy = power
        o.data.size = size
        o.location = loc
    # camera
    cam = bpy.data.objects.get('Studio_Camera')
    if cam is None:
        cd = bpy.data.cameras.new('Studio_Camera')
        cam = bpy.data.objects.new('Studio_Camera', cd)
        sc.collection.objects.link(cam)
    sc.camera = cam
    return cam


def set_floor_z(z):
    piv = bpy.data.objects['Cyc_Pivot']
    piv.location.z = z


def shot(path, target, az=0, el=0, dist=6.0, lens=85, res=(1000, 1400), ortho=None, turn_lights=True):
    sc = bpy.context.scene
    cam = bpy.data.objects['Studio_Camera']
    sc.camera = cam
    a = math.radians(az)
    e = math.radians(el)
    t = Vector(target)
    cam.location = t + Vector((math.sin(a) * math.cos(e), -math.cos(a) * math.cos(e), math.sin(e))) * dist
    cam.rotation_euler = (t - cam.location).to_track_quat('-Z', 'Y').to_euler()
    cd = cam.data
    cd.clip_start = .05
    cd.clip_end = 100
    if ortho:
        cd.type = 'ORTHO'
        cd.ortho_scale = ortho
    else:
        cd.type = 'PERSP'
        cd.lens = lens
        cd.sensor_width = 36
    sc.render.resolution_x, sc.render.resolution_y = res
    sc.render.resolution_percentage = 100
    bpy.data.objects['Cyc_Pivot'].rotation_euler.z = a
    if turn_lights:       # lights ride with the camera so every angle is lit like the front
        q = Quaternion((0, 0, 1), a)
        for name, loc, power, size in LIGHTS:
            o = bpy.data.objects[name]
            o.location = q @ Vector(loc)
            o.rotation_euler = (Vector((0, 0, 1.1)) - o.location).to_track_quat('-Z', 'Y').to_euler()
    sc.render.filepath = str(path)
    bpy.ops.render.render(write_still=True)

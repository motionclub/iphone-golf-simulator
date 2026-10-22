"""FORM3 renderer.   blender -b START.blend --python tools/render3.py -- <json-spec>

spec = {"coords": "data/xxx.npy" | null,        # (22444,3) float positions applied to Body_F in memory (no save)
        "out": "prefix",                         # writes prefix_<name>.png
        "shots": [ {"name":"chest_front","yaw":0,"xc":0,"zc":1.20,"w":0.40,"res":[750,900]}, ... ],
        "look": "matcap:<path or builtin .exr>" | "cycles" | "eevee" | "studio",
        "cavity": 0.0}
yaw: 0 = front (camera on -y looking +y), 180 = back, positive yaw rotates the camera toward -x?  (same convention as render_views.py:
     camera position = (5 sin(th)+xc, -5 cos(th), zc) with th = radians(-yaw_user)... we use `yaw` = the render_views angle value directly)
w = orthographic frame width in metres (height = w * res_y / res_x).
"""
import bpy, sys, math, json
import numpy as np
from mathutils import Vector

spec = json.loads(sys.argv[sys.argv.index('--') + 1])
sc = bpy.context.scene
for o in bpy.data.objects:
    if o.type == 'MESH' and o.name != 'Body_F':
        o.hide_render = True
    if o.type in ('EMPTY', 'LIGHT'):
        o.hide_render = True
        if o.type == 'LIGHT':
            o.hide_viewport = True

body = bpy.data.objects['Body_F']


def set_coords(path):
    co = np.load(path).astype(np.float32)
    assert co.shape == (len(body.data.vertices), 3), co.shape
    body.data.vertices.foreach_set('co', co.ravel())
    body.data.update()


variants = spec.get('variants') or [{'tag': None, 'coords': spec.get('coords')}]

look = spec.get('look', 'matcap:soft')
res0 = spec['shots'][0].get('res', [750, 900])
# ------------------------------------------------------------------ shading setup
if look == 'sil':
    sc.render.engine = 'BLENDER_WORKBENCH'
    sh = sc.display.shading
    sh.light = 'FLAT'
    sh.color_type = 'SINGLE'
    sh.single_color = (1, 1, 1)
    sh.show_cavity = False
    sh.show_shadows = False
    sc.render.film_transparent = True
    sc.render.image_settings.color_mode = 'RGBA'
elif look.startswith('matcap') or look == 'studio':
    sc.render.engine = 'BLENDER_WORKBENCH'
    sh = sc.display.shading
    sh.color_type = 'SINGLE'
    sh.single_color = (0.80, 0.80, 0.82)
    sh.show_shadows = False
    cav = float(spec.get('cavity', 0.0))
    sh.show_cavity = cav > 0
    if cav > 0:
        sh.cavity_type = 'BOTH'
        sh.cavity_ridge_factor = cav * 0.5
        sh.cavity_valley_factor = cav
    if look == 'studio':
        sh.light = 'STUDIO'
    else:
        sh.light = 'MATCAP'
        mc = look.split(':', 1)[1]
        if mc == 'soft':
            mc = '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/female-torso-form4/tools/soft_plate_matcap.png'
        if mc.endswith('.png') and '/' in mc:
            sl = bpy.context.preferences.studio_lights.load(mc, 'MATCAP')
            sh.studio_light = sl.name
        else:
            sh.studio_light = mc
    sc.render.film_transparent = False
    w = bpy.data.worlds.new('w')
    sc.world = w
    w.use_nodes = False
    w.color = (0.88, 0.88, 0.89)
else:
    # physically based soft look: big softbox upper-left-front + dim sky; grey diffuse body
    sc.render.engine = 'CYCLES' if look == 'cycles' else 'BLENDER_EEVEE'
    if look == 'cycles':
        sc.cycles.samples = int(spec.get('samples', 48))
        sc.cycles.use_denoising = True
        sc.cycles.device = 'CPU'
    mat = bpy.data.materials.new('plateGrey')
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes['Principled BSDF']
    bsdf.inputs['Base Color'].default_value = (0.62, 0.62, 0.64, 1)
    bsdf.inputs['Roughness'].default_value = 0.85
    for i, s in enumerate(list(body.data.materials)):
        body.data.materials[i] = mat
    w = bpy.data.worlds.new('w')
    sc.world = w
    w.use_nodes = True
    bgn = w.node_tree.nodes['Background']
    bgn.inputs['Color'].default_value = (0.9, 0.9, 0.92, 1)
    bgn.inputs['Strength'].default_value = float(spec.get('sky', 0.30))
    for nm, loc, energy, size in (('key', (-2.2, -2.6, 2.6), float(spec.get('key', 90)), 2.2), ('fill', (2.4, -2.0, 0.8), float(spec.get('fill', 25)), 3.0)):
        ld = bpy.data.lights.new(nm, 'AREA')
        ld.energy = energy
        ld.size = size
        lo = bpy.data.objects.new(nm, ld)
        sc.collection.objects.link(lo)
        lo.location = loc + (0,) if False else loc
        lo.rotation_euler = (Vector((0, 0, 1.15)) - Vector(loc)).to_track_quat('-Z', 'Y').to_euler()
sc.view_settings.view_transform = 'Standard'
sc.view_settings.look = 'None'
sc.render.resolution_x = int(res0[0])
sc.render.resolution_y = int(res0[1])
sc.render.image_settings.file_format = 'PNG'
cam = bpy.data.objects.new('c', bpy.data.cameras.new('c'))
sc.collection.objects.link(cam)
sc.camera = cam
cam.data.type = 'ORTHO'
cam.data.clip_end = 50
for var in variants:
    if var.get('coords'):
        set_coords(var['coords'])
    for shot in spec['shots']:
        res = shot.get('res', res0)
        sc.render.resolution_x, sc.render.resolution_y = int(res[0]), int(res[1])
        cam.data.ortho_scale = float(shot['w']) * max(1.0, res[1] / res[0])   # ortho_scale spans the LONGER image side
        th = math.radians(-float(shot.get('yaw', 0)))
        xc, zc = float(shot.get('xc', 0.0)), float(shot['zc'])
        pos = Vector((5 * math.sin(th) + xc, -5 * math.cos(th), zc))
        d = (Vector((xc, 0, zc)) - pos).normalized()
        cam.location = pos
        cam.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()
        tg = ('_' + var['tag']) if var.get('tag') else ''
        sc.render.filepath = f"{spec['out']}{tg}_{shot['name']}.png"
        bpy.ops.render.render(write_still=True)
print('RENDER_OK')

"""render Body_F from an npz with a per-vertex scalar as colour (diverging blue-white-red) under the Unity-like rig.
blender -b --factory-startup --python scalar_render.py -- <mesh.npz> <scalar.npz> <key> <vlim> <outdir> <views comma> <tag> [mix 0..1 shading-vs-colour]
views use the ul.py 'c:az:el:tx:ty:tz:scale:res' syntax. scalar key 'k1'/'k2' ... ; vlim = value mapped to full colour."""
import sys, math, json, os
sys.path.insert(0, '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/female-micro-f3-head/tools')
import numpy as np, bpy
from mathutils import Vector
import fl
argv = sys.argv[sys.argv.index('--') + 1:]
meshp, scp, key, vlim, outdir, views, tag = argv[0], argv[1], argv[2], float(argv[3]), argv[4], argv[5].split(','), argv[6]
mix = float(argv[7]) if len(argv) > 7 else 0.85
os.makedirs(outdir, exist_ok=True)
d = np.load(meshp, allow_pickle=True); V = d['V']; Fo = d['F']; off = d['Foff']
F = [Fo[off[i]:off[i + 1]] for i in range(len(off) - 1)]
s = np.load(scp, allow_pickle=True)[key].astype(float)
for o in list(bpy.data.objects): bpy.data.objects.remove(o, do_unlink=True)
body = fl.make_mesh_object('Body_F', V, F)
me = body.data
# colour attribute (per vertex, FLOAT_COLOR POINT)
t = np.clip(s / vlim, -1, 1)
col = np.zeros((len(V), 4)); col[:, 3] = 1
base = np.array([0.80, 0.78, 0.76])
pos = np.clip(t, 0, 1)[:, None]; neg = np.clip(-t, 0, 1)[:, None]
red = np.array([0.95, 0.10, 0.05]); blue = np.array([0.05, 0.25, 0.95])
c = base[None, :] * (1 - pos - neg) + red[None, :] * pos + blue[None, :] * neg
col[:, :3] = c
ca = me.color_attributes.new('curv', 'FLOAT_COLOR', 'POINT')
ca.data.foreach_set('color', col.ravel().astype(np.float32))
m = bpy.data.materials.new('curv'); m.use_nodes = True
nt = m.node_tree; b = nt.nodes['Principled BSDF']
an = nt.nodes.new('ShaderNodeAttribute'); an.attribute_name = 'curv'; an.attribute_type = 'GEOMETRY'
nt.links.new(an.outputs['Color'], b.inputs['Base Color'])
b.inputs['Roughness'].default_value = 0.6
me.materials.append(m)
sc = bpy.context.scene
sc.render.engine = 'BLENDER_EEVEE'; sc.render.film_transparent = True
sc.render.image_settings.file_format = 'PNG'; sc.render.image_settings.color_mode = 'RGBA'
sc.view_settings.view_transform = 'Standard'; sc.view_settings.look = 'None'
try:
    sc.eevee.taa_render_samples = 24; sc.eevee.use_shadows = True; sc.eevee.use_gtao = True; sc.eevee.gtao_distance = 0.06
except Exception: pass
def lin(c): return ((c + 0.055) / 1.055) ** 2.4 if c > 0.04045 else c / 12.92
def srgb(c): return tuple(lin(v) for v in c)
w = bpy.data.worlds.new('w_u'); sc.world = w; w.use_nodes = True; nt2 = w.node_tree; nt2.nodes.clear()
bg = nt2.nodes.new('ShaderNodeBackground'); outn = nt2.nodes.new('ShaderNodeOutputWorld')
bg.inputs['Color'].default_value = srgb((.40, .40, .42)) + (1,); nt2.links.new(bg.outputs['Background'], outn.inputs['Surface'])
cd = bpy.data.cameras.new('c'); cd.type = 'ORTHO'; cd.clip_start = 0.01; cd.clip_end = 50
cam = bpy.data.objects.new('c', cd); sc.collection.objects.link(cam); sc.camera = cam
def sun(nm, pos_u, inten, angle=4):
    rel = Vector((pos_u[0], pos_u[1] - 1.0, -pos_u[2])); direction = -rel
    dd = bpy.data.lights.new(nm, 'SUN'); dd.energy = inten * math.pi; dd.angle = math.radians(angle)
    ob = bpy.data.objects.new(nm, dd); sc.collection.objects.link(ob)
    ob.parent = cam; ob.rotation_mode = 'QUATERNION'; ob.rotation_quaternion = direction.normalized().to_track_quat('-Z', 'Y')
sun('u_key', (-2.8, 2.6, -3.8), 1.0 * 0.8); sun('u_fill', (2.6, 1.4, -2.4), .48 * 0.8); sun('u_back', (0, 3, 2.6), .55 * 0.8); sun('u_bounce', (0, -1, -3), .30 * 0.8)
def shoot(path, target, az, el, scale, res):
    a = math.radians(az); e = math.radians(el); tv = Vector(target)
    cam.location = tv + Vector((math.sin(a) * math.cos(e), -math.cos(a) * math.cos(e), math.sin(e))) * 3.0
    cam.rotation_euler = (tv - cam.location).to_track_quat('-Z', 'Y').to_euler()
    cd.ortho_scale = scale; sc.render.resolution_x, sc.render.resolution_y = res
    sc.render.filepath = path; bpy.ops.render.render(write_still=True)
for v in views:
    a_ = v.split(':'); az_, el_, tx_, ty_, tz_, sc_ = map(float, a_[1:7]); rs_ = int(a_[7]) if len(a_) > 7 else 1000
    path = os.path.join(outdir, f'{tag}_' + v.replace(':', '_') + '.png'); shoot(path, (tx_, ty_, tz_), az_, el_, sc_, (rs_, rs_))
print('scalar_render done')

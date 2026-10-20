"""Unity-like (EEVEE) renders of a blend WITH ITS OWN MATERIALS (rig copied from work/female-micro-f3-head/tools/ul.py, which does not keep the blend's materials).
    blender -b --factory-startup --python tools/render_color.py -- <blend> <outdir> <tag> <view>[,<view>...]
views: front | left | right | q3L | q3R   = plate-aligned head panels (F3's calibrated cameras, 3x the plate panel size)
       b:<az>:<el>:<tx>:<ty>:<tz>:<scale>:<resx>:<resy>   = free orthographic camera (az 0: camera at -Y, 90: +X, -90: -X; scale = metres across the larger image side)
Rig: 4 camera-relative suns (Key(-2.8,2.6,-3.8) 1.0, Fill(2.6,1.4,-2.4) .48, Back(0,3,2.6) .55, Bounce(0,-1,-3) .30), trilight ambient sky .46 .48 .54 / equator .38 .38 .40 / ground .26 .23 .21.
Transparent background (composited later). Hair_F / plates / old lights / cameras are removed from the OPENED copy only; nothing is saved."""
import sys, math, json, os
sys.path.insert(0, '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/female-micro-f3-head/tools')
import numpy as np, bpy
from mathutils import Vector
import fl
argv = sys.argv[sys.argv.index('--') + 1:]
blend, outdir, tag, views = argv[0], argv[1], argv[2], argv[3].split(',')
os.makedirs(outdir, exist_ok=True)
def lin(c): return ((c + 0.055) / 1.055) ** 2.4 if c > 0.04045 else c / 12.92
def srgb(c): return tuple(lin(v) for v in c)
bpy.ops.wm.open_mainfile(filepath=blend)
for o in list(bpy.data.objects):
    if o.type == 'EMPTY' or o.name == 'Hair_F' or o.type in ('LIGHT', 'CAMERA'): bpy.data.objects.remove(o, do_unlink=True)
s = bpy.context.scene
s.render.engine = 'BLENDER_EEVEE'; s.render.film_transparent = True
s.render.image_settings.file_format = 'PNG'; s.render.image_settings.color_mode = 'RGBA'
s.view_settings.view_transform = 'Standard'; s.view_settings.look = 'None'
try:
    s.eevee.taa_render_samples = 32; s.eevee.use_shadows = True; s.eevee.use_gtao = True; s.eevee.gtao_distance = 0.06
except Exception: pass
w = bpy.data.worlds.new('w_u'); s.world = w; w.use_nodes = True; nt = w.node_tree; nt.nodes.clear()
tc = nt.nodes.new('ShaderNodeTexCoord'); sep = nt.nodes.new('ShaderNodeSeparateXYZ'); nt.links.new(tc.outputs['Generated'], sep.inputs['Vector'])
mad = nt.nodes.new('ShaderNodeMath'); mad.operation = 'MULTIPLY_ADD'; mad.inputs[1].default_value = 0.5; mad.inputs[2].default_value = 0.5
nt.links.new(sep.outputs['Z'], mad.inputs[0])
ramp = nt.nodes.new('ShaderNodeValToRGB'); cr = ramp.color_ramp
while len(cr.elements) < 3: cr.elements.new(0.5)
for el, (pos, col) in zip(cr.elements, ((0.0, (.26, .23, .21)), (0.5, (.38, .38, .40)), (1.0, (.46, .48, .54)))):
    el.position = pos; el.color = srgb(col) + (1,)
nt.links.new(mad.outputs[0], ramp.inputs['Fac'])
bg = nt.nodes.new('ShaderNodeBackground'); outn = nt.nodes.new('ShaderNodeOutputWorld')
nt.links.new(ramp.outputs['Color'], bg.inputs['Color']); nt.links.new(bg.outputs['Background'], outn.inputs['Surface'])
# Unity proof studio: RenderSettings.reflectionIntensity = .15 (ambient trilight is the full diffuse ambient; only the REFLECTED environment is scaled).  Emulated: world strength = 1 - (1-R) * IsGlossyRay
REFL = float(os.environ.get('REFLECTION_INTENSITY', '0.15'))
if REFL < 1.0:
    lp = nt.nodes.new('ShaderNodeLightPath'); gm = nt.nodes.new('ShaderNodeMath'); gm.operation = 'MULTIPLY_ADD'; gm.inputs[1].default_value = -(1.0 - REFL); gm.inputs[2].default_value = 1.0
    nt.links.new(lp.outputs['Is Glossy Ray'], gm.inputs[0]); nt.links.new(gm.outputs[0], bg.inputs['Strength'])
cd = bpy.data.cameras.new('c'); cd.type = 'ORTHO'; cd.clip_start = 0.01; cd.clip_end = 50
cam = bpy.data.objects.new('c', cd); s.collection.objects.link(cam); s.camera = cam
def sun(nm, pos_u, inten, angle=4):
    rel = Vector((pos_u[0], pos_u[1] - 1.0, -pos_u[2])); direction = -rel
    dd = bpy.data.lights.new(nm, 'SUN'); dd.energy = inten * math.pi; dd.angle = math.radians(angle)
    ob = bpy.data.objects.new(nm, dd); s.collection.objects.link(ob)
    ob.parent = cam; ob.rotation_mode = 'QUATERNION'; ob.rotation_quaternion = direction.normalized().to_track_quat('-Z', 'Y')
sun('u_key', (-2.8, 2.6, -3.8), 1.0); sun('u_fill', (2.6, 1.4, -2.4), .48); sun('u_back', (0, 3, 2.6), .55); sun('u_bounce', (0, -1, -3), .30)
q3path = fl.W / 'data/q3.json'; q3 = json.load(open(q3path)) if q3path.exists() else {}
def shoot(path, target, az, el, scale, res):
    a = math.radians(az); e = math.radians(el); t = Vector(target)
    cam.location = t + Vector((math.sin(a) * math.cos(e), -math.cos(a) * math.cos(e), math.sin(e))) * 3.0
    cam.rotation_euler = (t - cam.location).to_track_quat('-Z', 'Y').to_euler()
    cd.ortho_scale = scale; s.render.resolution_x, s.render.resolution_y = int(res[0]), int(res[1])
    s.render.filepath = path; bpy.ops.render.render(write_still=True)
done = {}
for v in views:
    if v in ('front', 'left', 'right'):
        path = os.path.join(outdir, f'{tag}_{v}.png'); c = fl.panel_cam(v); shoot(path, c['target'], c['az'], 0.0, c['scale'], c['res'])
    elif v in ('q3L', 'q3R'):
        path = os.path.join(outdir, f'{tag}_{v}.png'); p = q3.get(v, fl.Q3[v]); x0, y0, x1, y1 = fl.PANELS[v]['box']; w_, h_ = x1 - x0, y1 - y0
        shoot(path, (p.get('tx', 0.0), p.get('ty', -0.03), p.get('tz', 1.55)), p['yaw'], p.get('el', 0.0), p.get('ortho', w_ * fl.K), (w_ * 3, h_ * 3))
    elif v.startswith('b:'):
        a_ = v.split(':'); az_, el_, tx_, ty_, tz_, sc_ = map(float, a_[1:7]); rx_, ry_ = int(a_[7]), int(a_[8])
        path = os.path.join(outdir, f'{tag}_' + v.replace(':', '_') + '.png'); shoot(path, (tx_, ty_, tz_), az_, el_, sc_, (rx_, ry_))
    else: raise SystemExit('unknown view ' + v)
    done[v] = path
json.dump(done, open(os.path.join(outdir, f'{tag}_views.json'), 'w'), indent=1); print('RENDER_COLOR_DONE', len(done))

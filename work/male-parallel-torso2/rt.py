"""Torso renderer: unity-like lighting, locked-camera plate registration.
blender -b --factory-startup --python rt.py -- <blend|npy> <outdir> [views] [clay]
views: front,back (Locked_bald_*), left,right (Locked_left/right), sheet_front, sheet_back, q3 (yaw views of the body)
If first arg is .npy it is applied to Body_M of the baseline blend."""
import sys, math
from pathlib import Path
import numpy as np, bpy
from mathutils import Vector
W = Path('/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/male-parallel-torso2')
argv = sys.argv[sys.argv.index('--') + 1:]
src = argv[0]; out = Path(argv[1]); out.mkdir(parents=True, exist_ok=True)
views = (argv[2] if len(argv) > 2 else 'front,back').split(',')
if src.endswith('.npy'):
    bpy.ops.wm.open_mainfile(filepath=str(W / 'baseline/HeroBase_Male_Silhouette.blend'))
    V = np.load(src); me = bpy.data.objects['Body_M'].data; assert len(V) == len(me.vertices)
    me.vertices.foreach_set('co', V.astype(np.float64).ravel()); me.update()
else:
    bpy.ops.wm.open_mainfile(filepath=src)
def lin(c): return ((c + 0.055) / 1.055) ** 2.4 if c > 0.04045 else c / 12.92
def srgb(c): return tuple(lin(v) for v in c)
def mat(name, col, smooth):
    m = bpy.data.materials.new(name); m.use_nodes = True; b = m.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = srgb(col) + (1,); b.inputs['Roughness'].default_value = 1.0 - smooth
    for k, v in (('Specular IOR Level', 0.5), ('Metallic', 0.0)):
        try: b.inputs[k].default_value = v
        except Exception: pass
    return m
for o in bpy.data.objects:
    if o.type == 'EMPTY': o.hide_render = True
body = bpy.data.objects['Body_M']; face = bpy.data.objects.get('Face_M')
body.data.materials.clear(); body.data.materials.append(mat('u_skin', (.74, .555, .435), .40))
# grey mannequin tint is the plate's torso colour; the Unity build uses the skin material for everything, we render the same way
FACE = {'Brow': ((.17, .14, .115), .34), 'Sclera': ((.80, .77, .72), .62), 'Iris': ((.30, .17, .085), .20), 'Pupil': ((.025, .018, .012), .25), 'Limbal': ((.09, .045, .025), .22), 'Catch': ((1, 1, 1), .9), 'LidLine': ((.115, .07, .05), .40), 'Lip': ((.76, .52, .43), .42), 'LipUp': ((.60, .38, .31), .40), 'Seam': ((.30, .15, .11), .30), 'Nostril': ((.26, .13, .09), .25), 'BrowSoft': ((.22, .175, .14), .30), 'LidCrease': ((.34, .20, .14), .30)}
if face:
    for i, slot in enumerate(face.material_slots):
        nm = slot.material.name.replace('Face_', '')
        if nm in FACE: face.material_slots[i].material = mat('u_' + nm, FACE[nm][0], FACE[nm][1])
CLAY = len(argv) > 3 and argv[3] == 'clay'
if CLAY:
    body.data.materials.clear(); body.data.materials.append(mat('u_clay', (.62, .62, .62), .30))
    if face: face.hide_render = True
s = bpy.context.scene
s.render.engine = 'BLENDER_EEVEE'; s.render.resolution_x, s.render.resolution_y = 1280, 720; s.render.film_transparent = False
s.render.image_settings.file_format = 'PNG'; s.render.image_settings.color_mode = 'RGB'; s.view_settings.view_transform = 'Standard'; s.view_settings.look = 'None'
try: s.eevee.taa_render_samples = 32; s.eevee.use_shadows = True; s.eevee.use_gtao = True; s.eevee.gtao_distance = 0.06
except Exception: pass
w = bpy.data.worlds.new('w_u'); s.world = w; w.use_nodes = True; nt = w.node_tree; nt.nodes.clear()
tc = nt.nodes.new('ShaderNodeTexCoord'); sep = nt.nodes.new('ShaderNodeSeparateXYZ'); nt.links.new(tc.outputs['Generated'], sep.inputs['Vector'])
mad = nt.nodes.new('ShaderNodeMath'); mad.operation = 'MULTIPLY_ADD'; mad.inputs[1].default_value = 0.5; mad.inputs[2].default_value = 0.5
nt.links.new(sep.outputs['Z'], mad.inputs[0])
ramp = nt.nodes.new('ShaderNodeValToRGB'); cr = ramp.color_ramp
while len(cr.elements) < 3: cr.elements.new(0.5)
for el, (pos, col) in zip(cr.elements, ((0.0, (.26, .23, .21)), (0.5, (.38, .38, .40)), (1.0, (.46, .48, .54)))): el.position = pos; el.color = srgb(col) + (1,)
nt.links.new(mad.outputs[0], ramp.inputs['Fac'])
bg = nt.nodes.new('ShaderNodeBackground'); outn = nt.nodes.new('ShaderNodeOutputWorld'); nt.links.new(ramp.outputs['Color'], bg.inputs['Color']); nt.links.new(bg.outputs['Background'], outn.inputs['Surface'])
cd = bpy.data.cameras.new('rcam'); cd.type = 'ORTHO'; cd.clip_start = 0.01; cd.clip_end = 50
cam = bpy.data.objects.new('rcam', cd); s.collection.objects.link(cam)
def sun(nm, pos_u, inten, angle=4):
    rel = Vector((pos_u[0], pos_u[1] - 1.0, -pos_u[2])); d = bpy.data.lights.new(nm, 'SUN'); d.energy = inten * math.pi; d.angle = math.radians(angle)
    ob = bpy.data.objects.new(nm, d); s.collection.objects.link(ob); ob.parent = cam; ob.rotation_mode = 'QUATERNION'; ob.rotation_quaternion = (-rel).normalized().to_track_quat('-Z', 'Y')
sun('u_key', (-2.8, 2.6, -3.8), 1.0); sun('u_fill', (2.6, 1.4, -2.4), .48); sun('u_back', (0, 3, 2.6), .55); sun('u_bounce', (0, -1, -3), .30)
LOCK = {'front': 'Locked_bald_front', 'back': 'Locked_bald_back', 'left': 'Locked_left', 'right': 'Locked_right', 'sheet_front': 'Locked_sheet_front', 'sheet_back': 'Locked_sheet_back'}
def yaw_cam(az_deg, tz=1.05, scale=2.2, tx=0.0, ty=-0.05, res=(1000, 1000)):
    t = Vector((tx, ty, tz)); a = math.radians(az_deg)
    cam.location = t + Vector((math.sin(a), -math.cos(a), 0.0)) * 5.0
    cam.rotation_euler = (t - cam.location).to_track_quat('-Z', 'Y').to_euler(); cam.data.ortho_scale = scale
    s.render.resolution_x, s.render.resolution_y = res
for v in views:
    if v in LOCK:
        lc = bpy.data.objects[LOCK[v]]; cam.location = lc.location; cam.rotation_euler = lc.rotation_euler; cam.data.ortho_scale = lc.data.ortho_scale
        s.render.resolution_x, s.render.resolution_y = 1280, 720
    elif v.startswith('yaw'):                       # yaw<deg>_<scale>_<tz>
        p = v[3:].split('_'); yaw_cam(float(p[0]), tz=float(p[2]) if len(p) > 2 else 1.05, scale=float(p[1]) if len(p) > 1 else 2.2)
    else: raise SystemExit('bad view ' + v)
    s.camera = cam; s.render.filepath = str((out / f'{v}.png').resolve()); bpy.ops.render.render(write_still=True)
print('RT_DONE', views)

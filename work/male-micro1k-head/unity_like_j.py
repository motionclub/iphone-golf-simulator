"""Blender preview that mimics the Unity HeroBaseMaleFormProof captures: 4 directional lights (camera-relative), trilight ambient, URP-ish skin + face slot colours.
blender -b --factory-startup --python unity_like.py -- <blend> <outdir> [views comma list] [res]
Views (Unity proof framing): head_front, head_threequarter, head_profile, face_front, face_threequarter, face_profile, ear_side, eye_front"""
import sys, math
sys.path.insert(0, '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/male-micro1k-head/pylib')
from pathlib import Path
import numpy as np
import bpy
from mathutils import Vector
sys.path.insert(0, '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/male-micro1h')
import h1lib as H
argv = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=argv[0]); out = Path(argv[1]); out.mkdir(parents=True, exist_ok=True)
views = argv[2].split(',') if len(argv) > 2 and argv[2] else ['head_front', 'head_threequarter', 'head_profile', 'face_front', 'face_threequarter', 'face_profile']
RES = int(argv[3]) if len(argv) > 3 else 900


def lin(c): return ((c + 0.055) / 1.055) ** 2.4 if c > 0.04045 else c / 12.92
def srgb(c): return tuple(lin(v) for v in c)


def mat(name, col, smooth, emis=None):
    m = bpy.data.materials.new(name); m.use_nodes = True
    b = m.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = srgb(col) + (1,)
    b.inputs['Roughness'].default_value = 1.0 - smooth
    for k, v in (('Specular IOR Level', 0.5), ('Metallic', 0.0), ('Subsurface Weight', 0.0)):
        try: b.inputs[k].default_value = v
        except Exception: pass
    if emis is not None:
        try:
            b.inputs['Emission Color'].default_value = srgb(emis) + (1,); b.inputs['Emission Strength'].default_value = 1.0
        except Exception: pass
    return m


SKIN = ((.74, .555, .435), .40)
FACE = {'Brow': ((.17, .14, .115), .34), 'Sclera': ((.80, .77, .72), .62), 'Iris': ((.30, .17, .085), .20), 'Pupil': ((.025, .018, .012), .25), 'Limbal': ((.09, .045, .025), .22),
        'Catch': ((1, 1, 1), .9), 'LidLine': ((.115, .07, .05), .40), 'Lip': ((.76, .52, .43), .42), 'LipUp': ((.60, .38, .31), .40), 'Seam': ((.30, .15, .11), .30), 'Nostril': ((.26, .13, .09), .25), 'BrowSoft': ((.22, .175, .14), .30), 'LidCrease': ((.34, .20, .14), .30)}
if len(argv) > 4:
    import json
    FACE.update({k: (tuple(v[0]), v[1]) for k, v in json.load(open(argv[4])).items()})          # optional colour overrides
for o in bpy.data.objects:
    if o.type == 'EMPTY': o.hide_render = True
body = bpy.data.objects['Body_M']; face = bpy.data.objects.get('Face_M')
body.data.materials.clear(); body.data.materials.append(mat('u_skin', *SKIN))
if face:
    for i, slot in enumerate(face.material_slots):
        nm = slot.material.name.replace('Face_', '')
        if nm in FACE: face.material_slots[i].material = mat('u_' + nm, FACE[nm][0], FACE[nm][1], emis=(.10, .095, .085) if nm == 'Sclera' else None)
s = bpy.context.scene
s.render.engine = 'BLENDER_EEVEE'; s.render.resolution_x = s.render.resolution_y = RES; s.render.film_transparent = False
s.render.image_settings.file_format = 'PNG'; s.render.image_settings.color_mode = 'RGB'
s.view_settings.view_transform = 'Standard'; s.view_settings.look = 'None'
try:
    s.eevee.taa_render_samples = 32; s.eevee.use_shadows = True; s.eevee.use_gtao = True; s.eevee.gtao_distance = 0.06
except Exception: pass
# trilight ambient world
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
cam = H.camera(); cam.data.clip_start = 0.01
# camera-relative lights (Unity: Key(-2.8,2.6,-3.8) 1.0, Fill(2.6,1.4,-2.4) .48, Back(0,3,2.6) .55, Bounce(0,-1,-3) .30 ; look-at (0,1,0)); camera frame: x right, y up, z toward camera
for nm in ('u_key', 'u_fill', 'u_back', 'u_bounce'):
    if nm in bpy.data.objects: bpy.data.objects.remove(bpy.data.objects[nm], do_unlink=True)
def sun(nm, pos_u, inten, angle=4):
    # Unity position relative to the look-at point -> camera-local position (x right, y up, z toward camera)
    rel = Vector((pos_u[0], pos_u[1] - 1.0, -pos_u[2]))
    direction = -rel                                     # light travels from its position to the subject
    d = bpy.data.lights.new(nm, 'SUN'); d.energy = inten * math.pi; d.angle = math.radians(angle)
    ob = bpy.data.objects.new(nm, d); bpy.context.scene.collection.objects.link(ob)
    ob.parent = cam; ob.rotation_mode = 'QUATERNION'; ob.rotation_quaternion = direction.normalized().to_track_quat('-Z', 'Y')
sun('u_key', (-2.8, 2.6, -3.8), 1.0); sun('u_fill', (2.6, 1.4, -2.4), .48); sun('u_back', (0, 3, 2.6), .55); sun('u_bounce', (0, -1, -3), .30)
# Unity close-up table: name -> (yaw, pitch, target(unity: x, y=blender z, z=blender y), ortho half-height)
CLOSE = {'head_front': (0, 0, (0, 1.58, -0.05), .30), 'head_threequarter': (32.5, 0, (0, 1.58, -0.05), .30), 'head_profile': (90, 0, (0, 1.58, -0.05), .30),
         'face_front': (0, 0, (0, 1.565, -0.05), .16), 'face_threequarter': (38, 2, (0, 1.565, -0.05), .16), 'face_profile': (90, 0, (0, 1.565, -0.03), .16),
         'face_threequarter_back': (140, 4, (0, 1.565, -0.03), .16), 'ear_side': (90, 0, (0.09, 1.5628, -0.0115), .11), 'ear_back': (150, 8, (0.09, 1.5628, -0.0115), .12),
         'eye_front': (0, 0, (0.036, 1.585, -0.10), .07), 'ear_f': (25, 0, (0.09, 1.5628, -0.0115), .12), 'ear_f0': (0, 0, (0.09, 1.5628, -0.0115), .075), 'ear_top': (0, 38, (0.09, 1.575, -0.0115), .075), 'ear_f2': (55, 0, (0.09, 1.5628, -0.0115), .12), 'nose_front': (0, 0, (0, 1.565, -0.10), .09), 'nose_q': (38, 0, (0, 1.565, -0.10), .09), 'chin_front': (0, 0, (0, 1.50, -0.05), .19), 'chin_threequarter': (35, -4, (0, 1.49, -0.05), .19)}
CLOSE.update({'neck_side': (90, 0, (0, 1.44, -0.02), .15), 'neck_back': (180, 0, (0, 1.44, -0.02), .15), 'neck_qback': (140, 5, (0, 1.44, -0.02), .15), 'neck_front': (0, 0, (0, 1.44, -0.05), .15),
              'neck_q': (38, 2, (0, 1.44, -0.05), .15), 'neck_q_lo': (38, -14, (0, 1.44, -0.05), .15), 'jaw_side': (90, 0, (0, 1.50, -0.07), .13), 'jaw_q': (62, 0, (0, 1.50, -0.07), .13), 'jaw_side_hi': (90, 12, (0, 1.50, -0.07), .13),
              'head_side_far': (90, 0, (0, 1.50, -0.02), .26), 'head_back': (180, 0, (0, 1.50, -0.02), .26)})
import h1render as HR
K_ = H.K
PUP_MID = {'q3L': 176.5, 'q3R': 589.5}; Q3_YAW = {'q3L': 41.0, 'q3R': 36.0}
def plate_cam(name, up=2):
    if name == 'right':
        x0, y0, x1, y1 = 834, 62, 1271, 352; w, h = x1 - x0, y1 - y0; cyp = (y0 + y1) / 2; cxp = (x0 + x1) / 2
        return (0.0, 0.065 - (1123.0 - cxp) * K_, float(H.zrow(cyp))), 90.0, w * K_, (w * up, h * up)
    c = HR.cam_for(name, up); tgt, az, sc, res = c['target'], c['az'], c['scale'], c['res']
    if name in PUP_MID:
        x0_, y0_, x1_, y1_ = HR.SETS[name]['box']; cxp = (x0_ + x1_) / 2; a_ = math.radians(Q3_YAW[name])
        ty = -0.1254 - ((PUP_MID[name] - cxp) * K_) / math.sin(a_); tgt = (0.0, ty, c['target'][2]); az = Q3_YAW[name]
    return tgt, az, sc, res
for v in views:
    if v.startswith('plate_'):
        tgt, az, sc, res = plate_cam(v[6:])
        t = Vector(tgt); a = math.radians(az)
        cam.location = t + Vector((math.sin(a), -math.cos(a), 0.0)) * 5.0
        cam.rotation_euler = (t - cam.location).to_track_quat('-Z', 'Y').to_euler(); cam.data.type = 'ORTHO'; cam.data.ortho_scale = sc
        s.render.resolution_x, s.render.resolution_y = res
        s.camera = cam; s.render.filepath = str((out / f'{v}.png').resolve()); bpy.ops.render.render(write_still=True)
        s.render.resolution_x = s.render.resolution_y = RES
        continue
    yaw, pitch, tu, size = CLOSE[v]
    t = Vector((tu[0], tu[2], tu[1]))                 # unity (x,y,z) -> blender (x, z->y ... ) : blender y = unity z, blender z = unity y
    a = math.radians(yaw); e = math.radians(pitch)
    cam.location = t + Vector((math.sin(a) * math.cos(e), -math.cos(a) * math.cos(e), math.sin(e))) * 5.0
    cam.rotation_euler = (t - cam.location).to_track_quat('-Z', 'Y').to_euler(); cam.data.type = 'ORTHO'; cam.data.ortho_scale = size * 2
    s.camera = cam; s.render.filepath = str((out / f'{v}.png').resolve()); bpy.ops.render.render(write_still=True)
print('unity-like done', views)

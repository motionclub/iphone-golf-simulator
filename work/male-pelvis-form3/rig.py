"""Unity-like render rig (port of male-parallel-torso3/rt.py) with a JSON view spec.
blender -b --factory-startup --python rig.py -- <blend|npy> <outdir> <spec.json|view,view,...> [clay|skin|grey] [skin_rgb r,g,b]
Views: 'front','back','left','right' (locked plate cameras @1280x720, optional '@N' = N x resolution, e.g. back@4),
       'yawDEG_SCALE_TZ_TX_W_H_PITCH' orthographic yaw view (DEG: 0 front, 90 = Locked_left side, 180 back, 270 right).
If the first arg is .npy it is applied to Body_M of the baseline blend."""
import sys, math, json, os
from pathlib import Path
import numpy as np, bpy
from mathutils import Vector
W = Path('/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/male-pelvis-form3')
argv = sys.argv[sys.argv.index('--') + 1:]
src = argv[0]; out = Path(argv[1]); out.mkdir(parents=True, exist_ok=True)
views = argv[2].split(',')
look = argv[3] if len(argv) > 3 else 'clay'
skin_rgb = tuple(float(x) for x in argv[4].split(',')) if len(argv) > 4 else (.74, .555, .435)
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
body.data.materials.clear()
if look == 'clay':
    body.data.materials.append(mat('u_clay', (.62, .62, .62), .30))
    if face: face.hide_render = True
elif look == 'grey':      # plate-like grey mannequin (plate torso ~ (99,98,96)/255 lit)
    body.data.materials.append(mat('u_grey', (.50, .50, .50), .38))
    if face: face.hide_render = True
elif look == 'manneq':     # grey mannequin body + skin head/neck (world z >= 1.405, smooth 5 mm transition) + face layers: the look of the user's REF/NOW sheet
    m_ = mat('u_manneq', (.50, .50, .50), .39); nt_ = m_.node_tree; bsdf_ = nt_.nodes['Principled BSDF']
    geo_ = nt_.nodes.new('ShaderNodeNewGeometry'); sep_ = nt_.nodes.new('ShaderNodeSeparateXYZ'); nt_.links.new(geo_.outputs['Position'], sep_.inputs['Vector'])
    mr_ = nt_.nodes.new('ShaderNodeMapRange'); mr_.inputs['From Min'].default_value = 1.402; mr_.inputs['From Max'].default_value = 1.408; nt_.links.new(sep_.outputs['Z'], mr_.inputs['Value'])
    mx_ = nt_.nodes.new('ShaderNodeMix'); mx_.data_type = 'RGBA'; mx_.inputs['A'].default_value = srgb((.50, .50, .50)) + (1,); mx_.inputs['B'].default_value = srgb(skin_rgb) + (1,)
    nt_.links.new(mr_.outputs['Result'], mx_.inputs['Factor']); nt_.links.new(mx_.outputs['Result'], bsdf_.inputs['Base Color'])
    body.data.materials.append(m_)
elif look == 'sil':
    m_ = bpy.data.materials.new('u_sil'); m_.use_nodes = True; nt_ = m_.node_tree; nt_.nodes.clear(); em_ = nt_.nodes.new('ShaderNodeEmission'); em_.inputs['Color'].default_value = (1, 1, 1, 1); o_ = nt_.nodes.new('ShaderNodeOutputMaterial'); nt_.links.new(em_.outputs[0], o_.inputs['Surface'])
    body.data.materials.append(m_)
    if face: face.hide_render = True
else:
    body.data.materials.append(mat('u_skin', skin_rgb, .40))
FACE = {'Brow': ((.17, .14, .115), .34), 'Sclera': ((.80, .77, .72), .62), 'Iris': ((.30, .17, .085), .20), 'Pupil': ((.025, .018, .012), .25), 'Limbal': ((.09, .045, .025), .22), 'Catch': ((1, 1, 1), .9), 'LidLine': ((.115, .07, .05), .40), 'Lip': ((.76, .52, .43), .42), 'LipUp': ((.60, .38, .31), .40), 'Seam': ((.30, .15, .11), .30), 'Nostril': ((.26, .13, .09), .25), 'BrowSoft': ((.22, .175, .14), .30), 'LidCrease': ((.34, .20, .14), .30)}
if face and look in ('skin', 'manneq'):
    for i, slot in enumerate(face.material_slots):
        nm = slot.material.name.replace('Face_', '')
        if nm in FACE: face.material_slots[i].material = mat('u_' + nm, FACE[nm][0], FACE[nm][1])
        elif nm == 'Skin' or slot.material.name == 'Face_Skin': face.material_slots[i].material = mat('u_fskin', skin_rgb, .40)
s = bpy.context.scene
s.render.engine = 'BLENDER_EEVEE'; s.render.resolution_x, s.render.resolution_y = 1280, 720; s.render.film_transparent = (look == 'sil')
s.render.image_settings.file_format = 'PNG'; s.render.image_settings.color_mode = ('RGBA' if look == 'sil' else 'RGB'); s.view_settings.view_transform = 'Standard'; s.view_settings.look = 'None'
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
import os
if os.environ.get('GRAZE'):                  # relief inspection: one hard sun from direction x,y,z (world) + dim ambient
    gx, gy, gz = [float(v) for v in os.environ['GRAZE'].split(',')]
    for ob in list(s.objects):
        if ob.type == 'LIGHT': bpy.data.objects.remove(ob, do_unlink=True)
    wnt = s.world.node_tree
    for nd in wnt.nodes:
        if nd.type == 'BACKGROUND': nd.inputs['Strength'].default_value = 0.25
    sd = bpy.data.lights.new('graze', 'SUN'); sd.energy = 3.2; sd.angle = math.radians(2)
    go = bpy.data.objects.new('graze', sd); s.collection.objects.link(go); d_ = Vector((gx, gy, gz)).normalized()
    go.rotation_mode = 'QUATERNION'; go.rotation_quaternion = (-d_).to_track_quat('-Z', 'Y')
LOCK = {'front': 'Locked_bald_front', 'back': 'Locked_bald_back', 'left': 'Locked_left', 'right': 'Locked_right', 'sheet_front': 'Locked_sheet_front', 'sheet_back': 'Locked_sheet_back'}
def yaw_cam(az_deg, tz=1.05, scale=2.2, tx=0.0, ty=-0.05, res=(1000, 1000), pitch=0.0):
    t = Vector((tx, ty, tz)); a = math.radians(az_deg); pr = math.radians(pitch)
    # camera right axis = (cos a, sin a, 0); tx shifts the target along it
    right = Vector((math.cos(a), math.sin(a), 0.0)); t = Vector((0, ty, tz)) + right * tx
    cam.location = t + Vector((math.sin(a) * math.cos(pr), -math.cos(a) * math.cos(pr), math.sin(pr))) * 5.0
    cam.rotation_euler = (t - cam.location).to_track_quat('-Z', 'Y').to_euler(); cam.data.ortho_scale = scale
    s.render.resolution_x, s.render.resolution_y = res; s.render.resolution_percentage = 100
# sheet-panel registrations of the multi-angle plate (yaw, col0, mpp, sole_row, zmin) -- from work/male-parallel-torso3/data/q3_calib2.json
SHEETREG = {'q3BL': (146.0, 794.4566521263387, 0.00588, 673), 'q3BR': (-147.5, 1072.7706942572954, 0.00584, 674),
            'q3FL': (20.0, 185.3449344808188, 0.00572, 673), 'q3FR': (-22.0, 477.7293057427045, 0.00572, 676)}
def reg_cam(panel, c0, c1, r0, r1, mag):
    """camera registered to sheet pixels [c0,c1]x[r0,r1] of a 3/4 panel, rendered at mag x the sheet resolution"""
    yaw, col0, mpp, sole = SHEETREG[panel]; yaw += float(os.environ.get('YAWOFF', 0.0)); col0 += float(os.environ.get('COLOFF', 0.0)); mpp *= float(os.environ.get('MPPF', 1.0)); a = math.radians(yaw); right = Vector((math.cos(a), math.sin(a), 0.0))
    cc, rr = 0.5 * (c0 + c1), 0.5 * (r0 + r1); zmin = 0.00247
    t = right * ((cc - col0) * mpp) + Vector((0, 0, zmin + (sole - rr) * mpp))
    cam.location = t + Vector((math.sin(a), -math.cos(a), 0.0)) * 5.0
    cam.rotation_euler = (t - cam.location).to_track_quat('-Z', 'Y').to_euler(); cam.data.sensor_fit = 'HORIZONTAL'; cam.data.ortho_scale = (c1 - c0) * mpp
    s.render.resolution_x, s.render.resolution_y = int((c1 - c0) * mag), int((r1 - r0) * mag); s.render.resolution_percentage = 100
for v in views:
    name = v; s.render.use_border = False; s.render.use_crop_to_border = False
    if v.startswith('reg_'):                       # reg_<panel>_<c0>_<c1>_<r0>_<r1>_<mag>
        p = v[4:].split('_'); reg_cam(p[0], float(p[1]), float(p[2]), float(p[3]), float(p[4]), float(p[5]))
    elif v.split('@')[0] in LOCK:
        base, _, rp = v.partition('@'); brd = None
        if ':' in rp: rp, _, brd = rp.partition(':')            # 'back@4:846_287_985_416' = x0_y0_x1_y1 border in the 1280x720 plate frame
        rp = int(rp) if rp else 1
        lc = bpy.data.objects[LOCK[base]]; cam.location = lc.location; cam.rotation_euler = lc.rotation_euler; cam.data.ortho_scale = lc.data.ortho_scale
        s.render.resolution_x, s.render.resolution_y = 1280, 720; s.render.resolution_percentage = 100 * rp
        if brd:
            bx0, by0, bx1, by1 = [float(q) for q in brd.split('_')]
            s.render.use_border = True; s.render.use_crop_to_border = True
            s.render.border_min_x = bx0 / 1280.0; s.render.border_max_x = bx1 / 1280.0; s.render.border_min_y = 1 - by1 / 720.0; s.render.border_max_y = 1 - by0 / 720.0
        else: s.render.use_border = False
    elif v.startswith('yaw'):                       # yaw<deg>_<scale>_<tz>_<tx>_<w>_<h>
        p = v[3:].split('_'); az = float(p[0]); sc = float(p[1]) if len(p) > 1 else 2.2; tz = float(p[2]) if len(p) > 2 else 1.05
        tx = float(p[3]) if len(p) > 3 else 0.0; ww = int(p[4]) if len(p) > 4 else 1000; hh = int(p[5]) if len(p) > 5 else 1000
        pit = float(p[6]) if len(p) > 6 else 0.0
        yaw_cam(az, tz=tz, scale=sc, tx=tx, res=(ww, hh), pitch=pit)
    else: raise SystemExit('bad view ' + v)
    s.camera = cam; s.render.filepath = str((out / f'{name}.png').resolve()); bpy.ops.render.render(write_still=True)
print('RIG_DONE', views)

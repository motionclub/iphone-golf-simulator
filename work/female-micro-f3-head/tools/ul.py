"""Unity-like (EEVEE) plate-aligned renders of the head.  
blender -b --factory-startup --python ul.py -- <src.npz|blend> <outdir> <views comma> <tag> [colors.json]
Unity proof rig: 4 directional lights relative to the camera (Key(-2.8,2.6,-3.8) 1.0, Fill(2.6,1.4,-2.4) .48, Back(0,3,2.6) .55, Bounce(0,-1,-3) .30),
trilight ambient (sky .46 .48 .54 / equator .38 .38 .40 / ground .26 .23 .21), URP-ish Lit skin (smoothness .40)."""
import sys, math, json, os
sys.path.insert(0, '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/female-micro-f3-head/tools')
import numpy as np, bpy
from mathutils import Vector
import fl
argv = sys.argv[sys.argv.index('--') + 1:]
src, outdir, views, tag = argv[0], argv[1], argv[2].split(','), argv[3]
os.makedirs(outdir, exist_ok=True)
def lin(c): return ((c + 0.055) / 1.055) ** 2.4 if c > 0.04045 else c / 12.92
def srgb(c): return tuple(lin(v) for v in c)
def mat(name, col, smooth, emis=None):
    m = bpy.data.materials.new(name); m.use_nodes = True
    b = m.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = srgb(col) + (1,); b.inputs['Roughness'].default_value = 1.0 - smooth
    for k, v in (('Specular IOR Level', 0.5), ('Metallic', 0.0)):
        try: b.inputs[k].default_value = v
        except Exception: pass
    if emis is not None:
        try: b.inputs['Emission Color'].default_value = srgb(emis) + (1,); b.inputs['Emission Strength'].default_value = 1.0
        except Exception: pass
    return m
SKIN = ((0.90, 0.70, 0.585), 0.40)
if src.endswith('.blend'):
    bpy.ops.wm.open_mainfile(filepath=src)
    for o in list(bpy.data.objects):
        if o.type == 'EMPTY' or o.name == 'Hair_F' or o.type in ('LIGHT', 'CAMERA'): bpy.data.objects.remove(o, do_unlink=True)
    body = bpy.data.objects['Body_F']
    names = [m.name if m else '' for m in body.data.materials]
    if 'Base_Grey_F' in names and len(names) == 2:
        for i, n_ in enumerate(names): body.material_slots[i].material = mat('u_grey', (0.80, 0.80, 0.82), 0.30) if n_ == 'Base_Grey_F' else mat('u_skin', *SKIN)
    else:
        body.data.materials.clear(); body.data.materials.append(mat('u_skin', *SKIN))
    face = bpy.data.objects.get('Face_F')
    FACE = {'Brow': ((.20, .135, .095), .34), 'BrowSoft': ((.33, .23, .17), .30), 'Sclera': ((.86, .85, .84), .62), 'IrisIn': ((.37, .21, .105), .20), 'Iris': ((.30, .17, .085), .20),
            'Limbal': ((.12, .06, .03), .22), 'Pupil': ((.02, .015, .012), .25), 'Catch': ((1, 1, 1), .9), 'LidLine': ((.07, .05, .04), .40), 'LidLower': ((.30, .17, .13), .35),
            'Lip': ((.93, .66, .55), .42), 'LipUp': ((.80, .51, .41), .40), 'Seam': ((.50, .25, .19), .30), 'Nostril': ((.33, .15, .11), .15)}
    if os.environ.get('FACE_PALETTE', 'new') == 'new':          # MicroF3 lip palette (plate-measured tone ratios): rosier lower lip, deeper upper lip, darker seam;  FACE_PALETTE=old -> MicroF1/F2 colours
        FACE.update({k: (tuple(v[0]), v[1]) for k, v in json.load(open(os.environ.get('LIP_PALETTE_JSON', str(fl.W / 'data/lip_palette_f3.json')))).items()})
    if face:
        for i, slot in enumerate(face.material_slots):
            nm = slot.material.name.replace('Face_', '')
            if nm in FACE: face.material_slots[i].material = mat('u_' + nm, FACE[nm][0], FACE[nm][1], emis=(.10, .095, .085) if nm == 'Sclera' else None)
else:
    d = np.load(src, allow_pickle=True); V = d['V']; Fo = d['F']; off = d['Foff']
    F = [Fo[off[i]:off[i + 1]] for i in range(len(off) - 1)]
    for o in list(bpy.data.objects): bpy.data.objects.remove(o, do_unlink=True)
    body = fl.make_mesh_object('Body_F', V, F); body.data.materials.append(mat('u_skin', *SKIN)); face = None
    if len(argv) > 4 and argv[4].endswith('.npz'):            # optional per-vertex custom normals (analytic surface normals blended in by weight w)
        an = np.load(argv[4]); me_ = body.data; n_ = len(me_.vertices)
        Nd_ = np.empty(n_ * 3); me_.vertices.foreach_get('normal', Nd_); Nd_ = Nd_.reshape(-1, 3)
        w_ = an['w'][:, None]; mix_ = w_ * an['N'] + (1 - w_) * Nd_; mix_ /= np.maximum(np.linalg.norm(mix_, axis=1, keepdims=True), 1e-12)
        me_.normals_split_custom_set_from_vertices([tuple(x) for x in mix_]); print('custom normals set from', argv[4])
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
cd = bpy.data.cameras.new('c'); cd.type = 'ORTHO'; cd.clip_start = 0.01; cd.clip_end = 50
cam = bpy.data.objects.new('c', cd); s.collection.objects.link(cam); s.camera = cam
def sun(nm, pos_u, inten, angle=4):
    rel = Vector((pos_u[0], pos_u[1] - 1.0, -pos_u[2])); direction = -rel
    dd = bpy.data.lights.new(nm, 'SUN'); dd.energy = inten * math.pi; dd.angle = math.radians(angle)
    ob = bpy.data.objects.new(nm, dd); s.collection.objects.link(ob)
    ob.parent = cam; ob.rotation_mode = 'QUATERNION'; ob.rotation_quaternion = direction.normalized().to_track_quat('-Z', 'Y')
sun('u_key', (-2.8, 2.6, -3.8), 1.0); sun('u_fill', (2.6, 1.4, -2.4), .48); sun('u_back', (0, 3, 2.6), .55); sun('u_bounce', (0, -1, -3), .30)
q3 = json.load(open(fl.W / 'data/q3.json')) if (fl.W / 'data/q3.json').exists() else {}
def shoot(path, target, az, el, scale, res):
    a = math.radians(az); e = math.radians(el); t = Vector(target)
    cam.location = t + Vector((math.sin(a) * math.cos(e), -math.cos(a) * math.cos(e), math.sin(e))) * 3.0
    if abs(el) > 89.0: cam.rotation_euler = (0.0, 0.0, 0.0)
    else: cam.rotation_euler = (t - cam.location).to_track_quat('-Z', 'Y').to_euler()
    cd.ortho_scale = scale; s.render.resolution_x, s.render.resolution_y = res
    s.render.filepath = path; bpy.ops.render.render(write_still=True)
for v in views:
    path = os.path.join(outdir, f'{tag}_{v}.png')
    if v in ('front', 'left', 'right'):
        c = fl.panel_cam(v); shoot(path, c['target'], c['az'], 0.0, c['scale'], c['res'])
    elif v in ('q3L', 'q3R'):
        p = q3.get(v, fl.Q3[v]); x0, y0, x1, y1 = fl.PANELS[v]['box']; w_, h_ = x1 - x0, y1 - y0
        shoot(path, (p.get('tx', 0.0), p.get('ty', -0.03), p.get('tz', 1.55)), p['yaw'], p.get('el', 0.0), p.get('ortho', w_ * fl.K), (w_ * 3, h_ * 3))
    elif v == 'top':
        p = q3.get('top', dict(tx=0.0, ty=-0.0277, tz=1.6, ortho=0.518)); x0, y0, x1, y1 = fl.PANELS['top']['box']
        shoot(path, (p['tx'], p['ty'], p['tz']), 0.0, 90.0, p['ortho'], ((x1 - x0) * 3, (y1 - y0) * 3))
    elif v.startswith('c:'):
        a_ = v.split(':'); az_, el_, tx_, ty_, tz_, sc_ = map(float, a_[1:7]); rs_ = int(a_[7]) if len(a_) > 7 else 1000
        path = os.path.join(outdir, f'{tag}_' + v.replace(':', '_') + '.png'); shoot(path, (tx_, ty_, tz_), az_, el_, sc_, (rs_, rs_))
print('ul done')

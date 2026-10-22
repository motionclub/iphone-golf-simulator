"""Blender -b --factory-startup --python render_npz.py -- <out_prefix> <unity_dir> <Piece[:Tag]>... [key=val]
Renders exported pieces (final npz = what Unity gets) with their baked N/M maps. Colours: base_<role>=hex, trim_<role>=hex.
mode=shoe (6 product views of the first piece) | views=az:el,... with target/dist."""
import sys, os, math
sys.path.insert(0, '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/clothing-v2/py')
import numpy as np, bpy
def _footprint_gb():
    try:
        import ctypes, struct
        buf = ctypes.create_string_buffer(512)
        if ctypes.CDLL('/usr/lib/libproc.dylib').proc_pid_rusage(ctypes.c_int(os.getpid()), ctypes.c_int(0), buf) == 0:
            return struct.unpack_from('<Q', buf.raw, 72)[0] / 1e9
    except Exception: pass
    return 0.0
from mathutils import Vector
import bl
a = sys.argv[sys.argv.index('--') + 1:]
out, udir = a[0], a[1]
pieces = [x for x in a[2:] if '=' not in x]; kv = dict(x.split('=', 1) for x in a[2:] if '=' in x)
bl.reset() if hasattr(bl, 'reset') else None
for o in list(bpy.data.objects): bpy.data.objects.remove(o)
COL = {'Kit_Shoe': ('F4F4F2', '22305A'), 'Kit_Sole': ('F2F2F0', 'F2F2F0'), 'Kit_Buckle': ('B8BCC2', 'B8BCC2'),
       'Kit_Shirt': ('F4F4F2', '22305A'), 'Kit_Shorts': ('22305A', '1A2648'), 'Kit_Sock': ('F4F4F2', 'E0E0E0'), 'Kit_Belt': ('5C3A22', '5C3A22')}
def mapmat(name, imN, imM, base, trim, rough=.55):
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; bsdf = nt.nodes['Principled BSDF']; bsdf.inputs['Roughness'].default_value = rough
    tN = nt.nodes.new('ShaderNodeTexImage'); tN.image = imN; tM = nt.nodes.new('ShaderNodeTexImage'); tM.image = imM
    nm = nt.nodes.new('ShaderNodeNormalMap'); nt.links.new(tN.outputs['Color'], nm.inputs['Color']); nt.links.new(nm.outputs['Normal'], bsdf.inputs['Normal'])
    sep = nt.nodes.new('ShaderNodeSeparateColor'); nt.links.new(tM.outputs['Color'], sep.inputs['Color'])
    mix = nt.nodes.new('ShaderNodeMix'); mix.data_type = 'RGBA'; mix.inputs[6].default_value = (*bl.srgb(base), 1); mix.inputs[7].default_value = (*bl.srgb(trim), 1)
    nt.links.new(sep.outputs['Blue'], mix.inputs['Factor'])
    cav = nt.nodes.new('ShaderNodeMath'); cav.operation = 'MULTIPLY_ADD'; cav.inputs[1].default_value = .6; cav.inputs[2].default_value = .4; nt.links.new(sep.outputs['Green'], cav.inputs[0])
    cv2 = nt.nodes.new('ShaderNodeMath'); cv2.operation = 'MULTIPLY_ADD'; cv2.inputs[1].default_value = .25; cv2.inputs[2].default_value = .75; nt.links.new(sep.outputs['Green'], cv2.inputs[0])
    cav3 = nt.nodes.new('ShaderNodeMath'); cav3.operation = 'MULTIPLY'; nt.links.new(cav.outputs[0], cav3.inputs[0]); nt.links.new(cv2.outputs[0], cav3.inputs[1]); cav = cav3
    aom = nt.nodes.new('ShaderNodeMath'); aom.operation = 'MAXIMUM'; aom.inputs[1].default_value = .70; nt.links.new(sep.outputs['Red'], aom.inputs[0])
    ao = nt.nodes.new('ShaderNodeMath'); ao.operation = 'MULTIPLY_ADD'; ao.inputs[1].default_value = .32; ao.inputs[2].default_value = .68; nt.links.new(aom.outputs[0], ao.inputs[0])
    m1 = nt.nodes.new('ShaderNodeMix'); m1.data_type = 'RGBA'; m1.blend_type = 'MULTIPLY'; m1.inputs['Factor'].default_value = 1; nt.links.new(mix.outputs[2], m1.inputs[6]); nt.links.new(cav.outputs[0], m1.inputs[7])
    m2 = nt.nodes.new('ShaderNodeMix'); m2.data_type = 'RGBA'; m2.blend_type = 'MULTIPLY'; m2.inputs['Factor'].default_value = 1; nt.links.new(m1.outputs[2], m2.inputs[6]); nt.links.new(ao.outputs[0], m2.inputs[7])
    nt.links.new(m2.outputs[2], bsdf.inputs['Base Color'])
    return m
objs = []
for pc in pieces:
    pdir = udir
    if '|' in pc: pdir, pc = pc.split('|')
    name, tag = (pc.split(':') + [None])[:2]
    g = np.load(os.path.join(pdir, name + '_final.npz'))
    tag = tag or name[4:].replace('_', '')
    P, T, uv = g['pos'], g['tri'], g['uv']
    me = bpy.data.meshes.new(name); me.from_pydata(P.tolist(), [], T.tolist()); me.update()
    ul = me.uv_layers.new(name='UVMap'); li = np.zeros(len(me.loops), np.int32); me.loops.foreach_get('vertex_index', li); ul.data.foreach_set('uv', uv[li].astype(np.float32).ravel())
    me.shade_smooth()
    ob = bpy.data.objects.new(name, me); bpy.context.scene.collection.objects.link(ob); objs.append(ob)
    imN = bpy.data.images.load(os.path.join(pdir, tag + '_N.png')); imN.colorspace_settings.name = 'Non-Color'
    imM = bpy.data.images.load(os.path.join(pdir, tag + '_M.png')); imM.colorspace_settings.name = 'Non-Color'; imM.alpha_mode = 'CHANNEL_PACKED'
    roles = [str(r) for r in g['roles']] if 'roles' in g.files else [{'Top': 'Kit_Shirt', 'Bottom': 'Kit_Shorts', 'SockL': 'Kit_Sock', 'SockR': 'Kit_Sock'}.get(tag, 'Kit_Shirt')]
    mat = g['mat'] if 'mat' in g.files else np.zeros(len(T), np.int32)
    for ri, r in enumerate(roles):
        b, t = COL.get(r, ('CCCCCC', '22305A'))
        b = kv.get('base_' + r, b); t = kv.get('trim_' + r, t)
        me.materials.append(mapmat(r, imN, imM, b, t, .45 if r == 'Kit_Buckle' else .6))
    me.polygons.foreach_set('material_index', np.asarray(mat, np.int32))
    me.update()
if kv.get('body'):
    bd = kv['body']; Pb = np.fromfile(bd + '/body_pos.f32', np.float32).reshape(-1, 3); Tb = np.fromfile(bd + '/body_tri.i32', np.int32).reshape(-1, 3)
    if kv.get('hide'):                                   # a hide list (body triangle ids not drawn), e.g. a pipeline cover
        hid = np.load(kv['hide'])['hide'] if kv['hide'].endswith('.npz') else np.fromfile(kv['hide'], np.int32)
        keep = np.ones(len(Tb), bool); keep[hid[hid < len(Tb)]] = False; Tb = Tb[keep]
    me = bpy.data.meshes.new('Body'); me.from_pydata(Pb.tolist(), [], Tb.tolist()); me.update(); me.shade_smooth()
    ob = bpy.data.objects.new('Body', me); bpy.context.scene.collection.objects.link(ob)
    me.materials.append(bl.material('skin', bl.srgb(kv.get('skin', 'C98D66')), .55))
bl.studio(res=(int(kv.get('w', 760)), int(kv.get('h', 520))), samples=int(kv.get('samples', 48)))
sc = bpy.context.scene
for o in sc.objects:
    if o.type == 'LIGHT': o.data.energy *= float(kv.get('light', 1.0))
sc.world.node_tree.nodes['Background'].inputs['Color'].default_value = (*bl.srgb(kv.get('bg', 'D6D4D0')), 1)
cd = bpy.data.cameras.new('Cam'); cam = bpy.data.objects.new('Cam', cd); sc.collection.objects.link(cam); sc.camera = cam
P0 = np.vstack([np.array([o.matrix_world @ Vector(c) for c in o.bound_box]) for o in objs[:1]])
ctr = Vector(P0.mean(0)) if 'target' not in kv else Vector(tuple(float(v) for v in kv['target'].split(',')))
side = 1 if ctr.x > 0 else -1
dist = float(kv.get('dist', 1.1)); cam.data.lens = float(kv.get('lens', 85))
if kv.get('ortho'): cam.data.type = 'ORTHO'; cam.data.ortho_scale = float(kv['ortho'])
OS = {k_[3:]: float(v_) for k_, v_ in kv.items() if k_.startswith('os_')}
if kv.get('mode', 'shoe') == 'shoe':
    views = [('lateral', Vector((side, 0, .10))), ('medial', Vector((-side, 0, .10))), ('front', Vector((0, -1, .22))),
             ('back', Vector((0, 1, .22))), ('top', Vector((0, -.0001, 1))), ('sole', Vector((0, -.0001, -1)))]
else:
    views = []
    for v in kv['views'].split(','):
        nm, az, el = v.split(':'); az = math.radians(float(az)); el = math.radians(float(el))
        views.append((nm, Vector((math.sin(az) * math.cos(el), -math.cos(az) * math.cos(el), math.sin(el)))))
files = []
for nm, d in views:
    d = d.normalized(); cam.location = ctr + d * dist
    up = Vector((0, -1, 0)) if abs(d.z) > .9 else Vector((0, 0, 1))
    rot = (ctr - cam.location).to_track_quat('-Z', 'Y')
    if abs(d.z) > .9:
        cam.rotation_euler = (0, 0, math.radians(-90 * side)) if d.z > 0 else (math.radians(180), 0, math.radians(90 * side))
    else: cam.rotation_euler = rot.to_euler()
    if nm in OS: cam.data.ortho_scale = OS[nm]
    if os.path.exists(fp_ := '%s_%s.png' % (out, nm)) and kv.get('resume') == '1': files.append(fp_); continue
    fp = fp_; sc.render.filepath = fp; bpy.ops.render.render(write_still=True); files.append(fp)
    # 10-18 memory cap (chat 5's gp/render.footprint_gb: background Blender keeps per-draw GPU memory; RSS hides it): stop before the OOM pop-up
    if _footprint_gb() > float(os.environ.get('GP_MEM_GB', 4)): print('RENDER_NPZ memory cap hit after', nm, '- rerun with resume=1'); sys.stdout.flush(); os._exit(3)
print('RENDERED', ' '.join(files))

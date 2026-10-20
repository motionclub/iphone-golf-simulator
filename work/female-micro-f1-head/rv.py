"""Plate-aligned Workbench renders of a mesh (npz with V, F-flat/F-offsets) or of Body_F inside a blend.
blender -b --factory-startup --python rv.py -- <src.npz|blend> <outdir> [views comma] [tag] [wire]
views: front,left,right,top,q3L,q3R  (q3 use data/q3.json)"""
import sys, math, json
sys.path.insert(0, '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/female-micro-f1-head')
import numpy as np, bpy
from mathutils import Vector
import fl
argv = sys.argv[sys.argv.index('--') + 1:]
src, outdir = argv[0], argv[1]
views = (argv[2] if len(argv) > 2 and argv[2] else 'front,left,right,q3L,q3R,top').split(',')
tag = argv[3] if len(argv) > 3 else 'm'
wire = len(argv) > 4 and argv[4] == 'wire'
import os; os.makedirs(outdir, exist_ok=True)
if src.endswith('.blend'):
    bpy.ops.wm.open_mainfile(filepath=src)
    for o in list(bpy.data.objects):
        if o.type != 'MESH' or o.name == 'Hair_F': o.hide_render = True
        if o.name == 'Face_F' and os.environ.get('HIDE_FACE'): o.hide_render = True
else:
    d = np.load(src, allow_pickle=True); V = d['V']; Fo = d['F']
    F = [Fo[i] for i in range(len(Fo))] if Fo.dtype == object else None
    if F is None:
        off = d['Foff']; F = [Fo[off[i]:off[i + 1]] for i in range(len(off) - 1)]
    for o in list(bpy.data.objects): bpy.data.objects.remove(o, do_unlink=True)
    ob = fl.make_mesh_object('preview', V, F)
    if 'Fmat' in d.files:
        pass
s = bpy.context.scene
s.render.engine = 'BLENDER_WORKBENCH'
sh = s.display.shading; sh.light = 'STUDIO'; sh.color_type = 'SINGLE'; sh.single_color = (0.93, 0.74, 0.62); sh.show_cavity = False
sh.show_specular_highlight = True
s.display.render_aa = '8'; s.view_settings.view_transform = 'Standard'
s.world = bpy.data.worlds.new('w'); s.world.color = (0.84, 0.84, 0.85)
s.render.image_settings.file_format = 'PNG'; s.render.film_transparent = False
if wire:
    for o in bpy.data.objects:
        if o.type == 'MESH' and not o.hide_render:
            md = o.modifiers.new('w', 'WIREFRAME'); md.thickness = 0.0002; md.use_replace = False
cd = bpy.data.cameras.new('c'); cd.type = 'ORTHO'; cd.clip_start = 0.01; cd.clip_end = 50
cam = bpy.data.objects.new('c', cd); s.collection.objects.link(cam); s.camera = cam
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
        p = q3.get(v, fl.Q3[v]); x0, y0, x1, y1 = fl.PANELS[v]['box']; w, h = x1 - x0, y1 - y0
        tgt = (p.get('tx', 0.0), p.get('ty', -0.03), p.get('tz', 1.55))
        shoot(path, tgt, p['yaw'], p.get('el', 0.0), p.get('ortho', w * fl.K), (w * 3, h * 3))
    elif v.startswith('c:'):
        # c:az:el:tx:ty:tz:scale[:res]
        a_ = v.split(':'); az_, el_, tx_, ty_, tz_, sc_ = map(float, a_[1:7]); rs_ = int(a_[7]) if len(a_) > 7 else 1000
        path = os.path.join(outdir, f'{tag}_' + v.replace(':', '_') + '.png')
        shoot(path, (tx_, ty_, tz_), az_, el_, sc_, (rs_, rs_))
    elif v == 'top':
        p = q3.get('top', dict(tx=0.0, ty=-0.0, tz=1.6, ortho=365 * fl.K * 1.0, el=90.0)); x0, y0, x1, y1 = fl.PANELS['top']['box']
        shoot(path, (p['tx'], p['ty'], p['tz']), 0.0, 90.0, p['ortho'], ((x1 - x0) * 3, (y1 - y0) * 3))
print('rv done', views)

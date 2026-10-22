"""Live-Blender driver: apply head sculpt + layers to live_m1g.blend's Body_M, render plate panels.
exec(open(...).read()) with globals: TAG, PARAMS (dict), LAYERS (bool)"""
import sys, importlib, json
import numpy as np, bpy
W = '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/male-micro1g'
E = '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/male-micro1e'
for p in (W, E):
    if p not in sys.path: sys.path.insert(0, p)
import head_lock as hl, face_layers as fl, plate_match as pm, lib
for m in (hl, fl, pm, lib): importlib.reload(m)
TAG = globals().get('TAG', 'h1'); PARAMS = globals().get('PARAMS', {}); LAYERS = globals().get('LAYERS', True)
body = bpy.data.objects['Body_M']
BASE = np.load('/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/male-micro1f/final/k5_verts.npy')
moved, V = hl.sculpt(body, BASE, PARAMS)
np.save(f'{W}/final/{TAG}_verts.npy', V)
# skin material for the preview renders
skin = fl.material('Skin_Preview', fl.SKIN_HEX, .62)
body.data.materials.clear(); body.data.materials.append(skin)
if LAYERS:
    fl.Layers(body).build()
else:
    o = bpy.data.objects.get('Face_M')
    if o: bpy.data.objects.remove(o, do_unlink=True)
lib._cam = None
lib.clay_setup(); sc = bpy.context.scene; sc.render.film_transparent = False
sh = sc.display.shading; sh.color_type = 'MATERIAL'; sh.show_cavity = True
for o in bpy.data.objects:
    if o.type == 'EMPTY': o.hide_render = True
fm = bpy.data.objects.get('Face_M')
if fm: fm.hide_render = False
for name in pm.PANELS:
    pm.panel_shot(lib, name, f'{W}/r/{TAG}_{name}.png')
RESULT = dict(tag=TAG, moved=moved, face_tris=(sum(len(p.vertices) - 2 for p in bpy.data.objects['Face_M'].data.polygons) if LAYERS else 0))

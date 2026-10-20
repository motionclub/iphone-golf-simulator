"""live helpers: apply a verts npy to Body_M and render quick hand views (uses male-micro1e lib)."""
import sys, importlib, numpy as np, bpy
from pathlib import Path
W = Path('/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/male-micro1f')
E1 = W.parent / 'male-micro1e'
for p in (str(W), str(E1)):
    if p not in sys.path: sys.path.insert(0, p)
import lib
importlib.reload(lib)

def apply(tag):
    v = np.load(W / f'final/{tag}_verts.npy')
    me = bpy.data.objects['Body_M'].data
    assert len(me.vertices) == len(v)
    me.vertices.foreach_set('co', v.astype(np.float32).ravel()); me.update()

def hand_views(prefix, sides=(+1, -1), scale=0.26):
    lib._cam = None
    lib.clay_setup(); s = bpy.context.scene; s.render.film_transparent = False
    body = bpy.data.objects['Body_M']; me = body.data
    co = np.array([v.co[:] for v in me.vertices]); polys = [list(p.vertices) for p in me.polygons]
    tmp = []
    for sign in sides:
        mask = (sign * co[:, 0] > 0.40) & (co[:, 2] < 1.20)
        keep = [p for p in polys if all(mask[i] for i in p)]
        idx = sorted(set(i for p in keep for i in p)); remap = {v: i for i, v in enumerate(idx)}
        m = bpy.data.meshes.new('Tmp_hand'); m.from_pydata([tuple(co[i]) for i in idx], [], [[remap[i] for i in p] for p in keep])
        m.polygons.foreach_set('use_smooth', [True] * len(m.polygons)); m.update()
        o = bpy.data.objects.new('Tmp_hand_' + ('R' if sign > 0 else 'L'), m); s.collection.objects.link(o); tmp.append((sign, o))
    body.hide_render = True
    for sign, o in tmp:
        for s2, o2 in tmp: o2.hide_render = (o2 is not o)
        c = (sign * 0.605, -0.105, 0.875)
        tag = 'R' if sign > 0 else 'L'
        for k, (az, el) in {'palm': (-90 * sign, -40), 'back': (90 * sign, 40), 'front': (0, 0), 'side': (90 * sign, 0), 'q3': (35 * sign, 20)}.items():
            lib.shot(str(W / f'r/{prefix}_hand{tag}_{k}.png'), c, az, el, scale, (640, 640))
    body.hide_render = False
    for sign, o in tmp:
        m = o.data; bpy.data.objects.remove(o, do_unlink=True); bpy.data.meshes.remove(m)
    for o in list(bpy.data.objects):
        if o.name.startswith('Tmp_'): bpy.data.objects.remove(o, do_unlink=True)
    lib._cam = None

def sheet(prefix):
    from PIL import Image  # not available in Blender python -> done outside

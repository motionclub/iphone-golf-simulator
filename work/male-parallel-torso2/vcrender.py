"""Render Body_M with per-vertex luminance (emission-like flat vertex colours) through the locked plate cameras.
blender -b --factory-startup --python vcrender.py -- <coords.npy> <lum.npz (front, back arrays, 0..255 per vertex)> <outdir>"""
import sys, numpy as np, bpy
from pathlib import Path
W = Path('/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/male-parallel-torso2')
a = sys.argv[sys.argv.index('--') + 1:]; V = np.load(a[0]); L = np.load(a[1]); out = Path(a[2]); out.mkdir(parents=True, exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(W / 'baseline/HeroBase_Male_Silhouette.blend'))
b = bpy.data.objects['Body_M']; me = b.data
me.vertices.foreach_set('co', V.astype(np.float64).ravel()); me.update()
for o in bpy.data.objects:
    if o.type == 'EMPTY' or o.name == 'Face_M': o.hide_render = True
s = bpy.context.scene; s.render.engine = 'BLENDER_WORKBENCH'; sh = s.display.shading
sh.light = 'FLAT'; sh.color_type = 'VERTEX'; sh.show_object_outline = False; sh.show_specular_highlight = False
s.render.film_transparent = False; s.view_settings.view_transform = 'Standard'; s.view_settings.look = 'None'; s.render.resolution_x, s.render.resolution_y = 1280, 720
s.world = bpy.data.worlds.new('w'); s.world.use_nodes = True; s.world.node_tree.nodes['Background'].inputs['Color'].default_value = (0.0, 0.0, 0.0, 1)
def srgb_to_lin(c): c = np.asarray(c, float); return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)
for view, cam in (('front', 'Locked_bald_front'), ('back', 'Locked_bald_back')):
    lum = np.clip(L[view] / 255.0, 0, 1); lin = srgb_to_lin(lum)
    col = np.zeros((len(V), 4)); col[:, 0] = col[:, 1] = col[:, 2] = lin; col[:, 3] = 1
    if 'lc' in me.color_attributes: me.color_attributes.remove(me.color_attributes['lc'])
    ca = me.color_attributes.new('lc', 'FLOAT_COLOR', 'POINT'); ca.data.foreach_set('color', col.ravel()); me.color_attributes.active_color = ca
    s.camera = bpy.data.objects[cam]; s.render.filepath = str((out / f'{view}.png').resolve()); bpy.ops.render.render(write_still=True)
print('VCRENDER_DONE')

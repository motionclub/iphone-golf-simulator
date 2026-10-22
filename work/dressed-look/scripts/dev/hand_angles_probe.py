import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from dl_common import *
import studio as ST
tag = args_after_dashes()[0]; out = args_after_dashes()[1]
for o in bpy.data.objects:
    if o.type in ('LIGHT', 'CAMERA'): o.hide_render = True
bpy.data.collections['Kit_Black'].hide_render = True
bpy.data.collections['Kit_Black'].hide_viewport = True
for lc in bpy.context.view_layer.layer_collection.children:
    if lc.name == 'Kit_Black': lc.hide_viewport = True
bpy.context.scene.frame_set(1); bpy.context.view_layer.update()
shoe_min = min(mesh_co(o, world=True)[:, 2].min() for o in bpy.data.objects if o.type == 'MESH' and o.name.startswith('Kit_Shoe') and 'White' in o.name)
ST.setup(samples=24); ST.set_floor_z(shoe_min)
hr = tuple(bpy.data.objects['Hand_Racket'].matrix_world.translation)
for nm, az, el in (('p1', -55, 12), ('p2', -125, 20), ('p3', -140, -25), ('p4', -95, 5), ('p5', -160, 10), ('p6', -20, 25)):
    ST.shot(f'{out}_{nm}.png', hr, az=az, el=el, dist=0.62, lens=70, res=(500, 500))
print('PROBE_DONE')

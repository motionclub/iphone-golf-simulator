"""blender -b --factory-startup --python make_merged.py -- <base.blend> <V_final.npy> <out.blend>
Take the shared base blend as it is NOW, replace ONLY the leg-zone vertices (indices z<0.765,|x|<0.27 of the start coordinates) by the chain result, save."""
import sys; sys.path.insert(0,'/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/male-parallel-legs')
import numpy as np, bpy
from leglib import ZONE
a=sys.argv[sys.argv.index('--')+1:]
base,vf,out=a
bpy.ops.wm.open_mainfile(filepath=base)
me=bpy.data.objects['Body_M'].data; n=len(me.vertices); assert n==len(ZONE)
cur=np.empty(n*3); me.vertices.foreach_get('co',cur); cur=cur.reshape(-1,3)
V0=np.load('/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/male-parallel-legs/data/V_start_orig.npy')
assert np.all(cur[ZONE].astype(np.float32)==V0[ZONE].astype(np.float32)), 'zone vertices of the base differ from the start - STOP'
new=np.load(vf)
cur[ZONE]=new[ZONE]
me.vertices.foreach_set('co',cur.reshape(-1)); me.update()
bpy.ops.wm.save_as_mainfile(filepath=out,compress=True); print('MERGED',out)

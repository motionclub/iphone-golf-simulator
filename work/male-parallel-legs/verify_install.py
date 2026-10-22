import sys, numpy as np, bpy
sys.path.insert(0,'/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/male-parallel-legs')
from leglib import ZONE
V0=np.load('/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/male-parallel-legs/data/V_start_orig.npy').astype(np.float32)
bpy.ops.wm.open_mainfile(filepath=sys.argv[sys.argv.index('--')+1])
me=bpy.data.objects['Body_M'].data; n=len(me.vertices); V=np.empty(n*3); me.vertices.foreach_get('co',V); V=V.reshape(-1,3).astype(np.float32)
m=np.any(V!=V0,axis=1); z=V0[:,2]; x=V0[:,0]
print('moved vs ORIGINAL start: total',int(m.sum()))
print('  legs zone (z<0.765,|x|<0.27):',int((m&ZONE).sum()),'of',int(ZONE.sum()))
print('  torso (0.765<=z<1.40,|x|<0.27):',int((m&(z>=0.765)&(z<1.40)&(np.abs(x)<0.27)).sum()))
print('  arms/hands (|x|>=0.27):',int((m&(np.abs(x)>=0.27)).sum()))
print('  head (z>=1.40):',int((m&(z>=1.40)).sum()))

import bpy, sys, math, collections, numpy as np
sys.path.insert(0,'/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/blender/scripts')
import hole08_design as D, postcard_check as PC
from mathutils import Vector
from mathutils.bvhtree import BVHTree
H=PC.Hole(D); YD=0.9144
def wv(o):
    M=np.array(o.matrix_world); V=np.array([v.co[:] for v in o.data.vertices]).reshape(-1,3); return (np.c_[V,np.ones(len(V))]@M.T)[:,:3]
print('--- sea stacks')
for o in bpy.data.objects:
    if o.type=='MESH' and o.name.startswith(('ROCK_SPIRE','ROCK_SEASTACK','ROCK_OUTCROP')):
        V=wv(o); c=V.mean(0)
        far=min(H.dist_center((v[0]/YD,v[1]/YD)) for v in V)
        # lie of center
        print(f"{o.name:22s} top {V[:,2].max():6.2f} base {V[:,2].min():6.2f} ctr yd ({c[0]/YD:7.1f},{c[1]/YD:7.1f}) min dist to centerline yd {far:5.1f} lie {H.lie_at((c[0]/YD,c[1]/YD))}")
# flat-top check: crown width at top relative to base (taper)
print('--- cliff-foot boulders: heights above water, hovering?')
bv=[]
for o in bpy.data.objects:
    if o.type=='MESH' and o.name.startswith(('ROCK_BOULDER','ROCK_SLAB','ROCK_STONE','ROCK_BLOCK','ROCK_CAIRN')):
        V=wv(o); bv.append((o.name,round(V[:,2].min(),2),round(V[:,2].max(),2)))
print(len(bv),'min base',min(b for _,b,_ in bv),'max base',max(b for _,b,_ in bv))
hov=[x for x in bv if x[1]>0.8 ]
print('base > 0.8 m (on land presumably)',len(hov))

import bpy, sys, collections, numpy as np
sys.path.insert(0,'/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/blender/scripts')
import hole08_design as D, postcard_check as PC
H=PC.Hole(D); YD=0.9144
def wv(o):
    M=np.array(o.matrix_world); V=np.array([v.co[:] for v in o.data.vertices]).reshape(-1,3); return (np.c_[V,np.ones(len(V))]@M.T)[:,:3]
tot=collections.Counter(); ex={}
for o in bpy.data.objects:
    if o.type!='MESH' or not o.name.startswith(('ROCK_','PLANT_','DRESS_','WATER_FALL')): continue
    t=o.matrix_world.translation
    if abs(t.x)<1e-6 and abs(t.y)<1e-6: continue
    V=wv(o)
    for v in V:
        if v[2]>0.3 and any(H.in_ellipse(h,(v[0]/YD,v[1]/YD)) for h in H.hazards if h[0]=='water'):
            k=o.name.split('.')[0]; tot[k]+=1; ex.setdefault(k,(o.name,(v/YD).round(1)))
print(dict(tot)); print(ex)

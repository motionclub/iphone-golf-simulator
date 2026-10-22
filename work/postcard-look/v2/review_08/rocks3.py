import bpy, sys, math, collections, numpy as np
sys.path.insert(0,'/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/blender/scripts')
import hole08_design as D, postcard_check as PC
H=PC.Hole(D); YD=0.9144
def wv(o):
    M=np.array(o.matrix_world); V=np.array([v.co[:] for v in o.data.vertices]).reshape(-1,3); return (np.c_[V,np.ones(len(V))]@M.T)[:,:3]
pin=np.array(H.pin); tee=np.array(H.tee)
bad=[]; n=0; mind=1e9
pts=[]
for o in bpy.data.objects:
    if o.type!='MESH' or not o.name.startswith(('ROCK_','DRESS_BLOCK','DRESS_ARCH','PLANT_')): continue
    if o.name.startswith('ROCK_SKIN'): continue
    V=wv(o)
    if abs(o.matrix_world.translation.x)<1e-6 and abs(o.matrix_world.translation.y)<1e-6: continue
    n+=1
    # any vertex on a play lie surface (fairway/green/tee/bunker) at height above play?
    lies=collections.Counter()
    for v in V[::1]:
        l=H.lie_at((v[0]/YD,v[1]/YD))
        if l in (PC.FAIRWAY,PC.GREEN,PC.TEE,PC.BUNKER) and v[2]>5.9: lies[l]+=1
    if lies: bad.append((o.name,dict(lies)))
    # distance of any vertex (z>5.5) to pin/tee marker in m
    pm=np.linalg.norm(V[:,:2]-pin*YD,axis=1).min(); tm=np.linalg.norm(V[:,:2]-tee*YD,axis=1).min()
    mind=min(mind,pm,tm)
    if pm<1.5 or tm<1.5: bad.append((o.name,'near marker',pm,tm))
print('objects checked',n,'with vertices over play lie (above 5.9m)',len(bad),bad[:20],'min dist to pin/tee',mind)
# fairway-edge distance for plants/rocks: nearest offset from centerline of any object vertex above 5.9
mn=1e9; who=None
for o in bpy.data.objects:
    if o.type!='MESH' or not o.name.startswith(('ROCK_','PLANT_','DRESS_BLOCK')) or o.name.startswith('ROCK_SKIN'): continue
    if abs(o.matrix_world.translation.x)<1e-6 and abs(o.matrix_world.translation.y)<1e-6: continue
    V=wv(o); V=V[V[:,2]>5.5]
    for v in V:
        d=H.dist_center((v[0]/YD,v[1]/YD))
        if d<mn: mn=d; who=o.name
print('closest prop vertex to centerline (yd)',mn,who)

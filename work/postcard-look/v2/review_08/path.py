import bpy, sys, math, collections, numpy as np
sys.path.insert(0,'/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/blender/scripts')
import hole08_design as D, postcard_check as PC
from mathutils import Vector
from mathutils.bvhtree import BVHTree
H=PC.Hole(D); YD=0.9144
def wv(o):
    M=np.array(o.matrix_world); V=np.array([v.co[:] for v in o.data.vertices]).reshape(-1,3); return (np.c_[V,np.ones(len(V))]@M.T)[:,:3]
def mk(objs):
    vs=[];fs=[];off=0
    for o in objs:
        V=wv(o); vs+=V.tolist(); fs+=[[i+off for i in p.vertices] for p in o.data.polygons]; off+=len(V)
    return BVHTree.FromPolygons(vs,fs)
gr=[o for o in bpy.data.objects if o.type=='MESH' and o.name.startswith(('TERRAIN','FAIRWAY','GREEN','TEE_BOX','BUNKER'))]
bvh=mk(gr)
def top(x,y):
    # highest hit
    best=None; p=Vector((x,y,40))
    while True:
        r=bvh.ray_cast(p,Vector((0,0,-1)))
        if r[0] is None: break
        if best is None: best=r[0].z
        break
    return best
paths=[o for o in bpy.data.objects if o.name.startswith('DRESS_PATH')]
allz=[]
for o in paths:
    me=o.data; V=wv(o); print(o.name,len(V),'faces',len(me.polygons),'mats',[m.name for m in me.materials])
    # samples: verts + face centroids + random barycentric
    rng=np.random.default_rng(1); pts=[]
    for p in me.polygons:
        vv=V[list(p.vertices)]; pts.append(vv.mean(0))
        for k in range(3):
            w=rng.dirichlet(np.ones(len(vv))); pts.append((vv*w[:,None]).sum(0))
    pts+=list(V)
    d=[]
    for q in pts:
        t=top(q[0],q[1])
        if t is None: d.append(None); continue
        d.append(q[2]-t)
    dn=np.array([x for x in d if x is not None])
    nn=sum(1 for x in d if x is None)
    print(' samples',len(pts),'no ground',nn,'dz min %.4f max %.4f mean %.4f p95 %.4f'%(dn.min(),dn.max(),dn.mean(),np.percentile(dn,95)), 'count>1.2cm',int((dn>0.012).sum()), 'count>0.5cm', int((dn>0.005).sum()), 'z-range',V[:,2].min(),V[:,2].max())
    # surface lie of verts
    c=collections.Counter(H.lie_at((v[0]/YD,v[1]/YD)) for v in V); print(' lie of verts',dict(c))
    # extent in yards
    print(' bbox yd',(V[:,:2].min(0)/YD).round(1),(V[:,:2].max(0)/YD).round(1))
# ball start
bs=bpy.data.objects['BALL_START']; print('BALL_START',tuple(bs.matrix_world.translation), 'pin', tuple(bpy.data.objects['MARKER_PIN'].matrix_world.translation),'tee',tuple(bpy.data.objects['MARKER_TEE'].matrix_world.translation))
print('--- outliers')
for o in paths:
    me=o.data; V=wv(o)
    out=[]
    for i,q in enumerate(V):
        t=top(q[0],q[1]); 
        if t is not None and (q[2]-t>0.012 or q[2]-t<-0.03): out.append((i,(q[:2]/YD).round(2).tolist(),round(q[2]-t,4)))
    print(o.name,len(out),out[:8])
    # per-face: max dz at face centroid
    bad=[]
    for p in me.polygons:
        c=V[list(p.vertices)].mean(0); t=top(c[0],c[1])
        if t is not None and c[2]-t>0.012: bad.append(((c[:2]/YD).round(2).tolist(),round(c[2]-t,4)))
    print(' bad centroids',len(bad),bad[:5])
print('--- locate')
o=bpy.data.objects['DRESS_PATH_02']; me=o.data; V=wv(o)
rng=np.random.default_rng(1); pts=[]
for p in me.polygons:
    vv=V[list(p.vertices)]; pts.append(vv.mean(0))
    for k in range(3):
        w=rng.dirichlet(np.ones(len(vv))); pts.append((vv*w[:,None]).sum(0))
for q in pts:
    t=top(q[0],q[1])
    if t is not None and q[2]-t>0.012:
        print((q[:2]/YD).round(3),q[2],t)
        for g in gr:
            r=BVHTree.FromPolygons(wv(g).tolist(),[list(p.vertices) for p in g.data.polygons]).ray_cast(Vector((q[0],q[1],40)),Vector((0,0,-1)))
            print(g.name,r[0] and r[0].z)

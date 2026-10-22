import bpy, sys, numpy as np, math
from collections import defaultdict
from mathutils import Vector
from mathutils.bvhtree import BVHTree
bpy.ops.wm.open_mainfile(filepath=sys.argv[sys.argv.index("--")+1])
def bvh(pred):
    V=[];F=[]
    for o in bpy.data.objects:
        if o.type!='MESH' or not pred(o.name): continue
        M=o.matrix_world;b=len(V);V+=[tuple(M@v.co) for v in o.data.vertices]
        for p in o.data.polygons:
            vs=[b+i for i in p.vertices]
            for k in range(1,len(vs)-1): F.append((vs[0],vs[k],vs[k+1]))
    return BVHTree.FromPolygons(V,F)
ter=bvh(lambda n:n.startswith('TERRAIN')); both=bvh(lambda n:n.startswith(('TERRAIN','ROCK_SKIN')))
T=[o for o in bpy.data.objects if o.name.startswith('TERRAIN')][0]; me=T.data; M=T.matrix_world
V=np.array([tuple(M@v.co) for v in me.vertices])
cnt=defaultdict(int)
for p in me.polygons:
    if (M.to_3x3()@p.normal).z<=0.5: continue
    vs=list(p.vertices)
    for a,b in zip(vs,vs[1:]+vs[:1]): cnt[(min(a,b),max(a,b))]+=1
adj=defaultdict(list)
for (a,b),c in cnt.items():
    if c==1: adj[a].append(b); adj[b].append(a)
seen=set();loops=[]
for a in list(adj):
    if a in seen: continue
    l=[a];seen.add(a);cur=a;prev=None
    while True:
        nx=[x for x in adj[cur] if x!=prev and x not in seen]
        if not nx: break
        prev=cur;cur=nx[0];seen.add(cur);l.append(cur)
    if len(l)>8: loops.append(l)
dn=Vector((0,0,-1))
for l in loops:
    P=V[l][:,:2];P=np.vstack([P,P[:1]])
    seg=np.hypot(*np.diff(P,axis=0).T);s=np.concatenate([[0],np.cumsum(seg)]);L=s[-1]
    ss=np.arange(0,L,1.0);x=np.interp(ss,s,P[:,0]);y=np.interp(ss,s,P[:,1])
    tx=np.gradient(x);ty=np.gradient(y);tn=np.hypot(tx,ty);tx/=tn;ty/=tn
    off=[];pts=[]
    for k in range(len(ss)):
        n=np.array([ty[k],-tx[k]])
        # choose outward: 3 m out has no terrain below
        h=ter.ray_cast(Vector((x[k]+n[0]*4,y[k]+n[1]*4,30)),dn)
        if h[0] is not None and h[0].z>0.5:
            n=-n
            h=ter.ray_cast(Vector((x[k]+n[0]*4,y[k]+n[1]*4,30)),dn)
            if h[0] is not None and h[0].z>0.5: off.append(np.nan);pts.append((np.nan,np.nan));continue
        o=Vector((x[k]+n[0]*10,y[k]+n[1]*10,3.0)); d=Vector((-n[0],-n[1],0))
        hit=both.ray_cast(o,d,20)
        if hit[0] is None: off.append(np.nan);pts.append((np.nan,np.nan));continue
        off.append(10-hit[3]); pts.append((hit[0].x,hit[0].y))
    off=np.array(off);pts=np.array(pts)
    ok=np.isfinite(off)
    st=np.abs(np.diff(off)); st=st[np.isfinite(st)]
    # plan tortuosity of the footprint curve
    q=pts[ok]; seglen=np.hypot(*np.diff(q,axis=0).T); seglen=seglen[seglen<5]
    chord=np.hypot(*(q[10:]-q[:-10]).T); path10=np.array([seglen[i:i+10].sum() for i in range(len(seglen)-9)])
    m=min(len(chord),len(path10))
    tort=np.median(path10[:m]/np.maximum(chord[:m],1e-6))
    print("loop L=%.0f: valid %d/%d  offset mean %.2f std %.2f min %.2f max %.2f ; |step|>0.2 m: %.0f%% ; >0.5 m: %.0f%% ; local tortuosity (10 m) median %.3f"%(L,ok.sum(),len(ok),np.nanmean(off),np.nanstd(off),np.nanmin(off),np.nanmax(off),100*(st>0.2).mean(),100*(st>0.5).mean(),tort))

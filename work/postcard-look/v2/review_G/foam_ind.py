import bpy, sys, numpy as np, math
from collections import defaultdict
bpy.ops.wm.open_mainfile(filepath=sys.argv[sys.argv.index("--")+1])
ter=[o for o in bpy.data.objects if o.name.startswith('TERRAIN')][0]
me=ter.data; M=ter.matrix_world
V=np.array([tuple(M@v.co) for v in me.vertices])
cnt=defaultdict(int); dirs={}
for p in me.polygons:
    n=M.to_3x3()@p.normal
    if n.z<=0.5: continue
    vs=list(p.vertices)
    for a,b in zip(vs,vs[1:]+vs[:1]):
        k=(min(a,b),max(a,b)); cnt[k]+=1; dirs[k]=(a,b)
edges=[k for k,c in cnt.items() if c==1]
adj=defaultdict(list)
for a,b in edges: adj[a].append(b); adj[b].append(a)
seen=set(); loops=[]
for a,b in edges:
    if a in seen: continue
    loop=[a]; seen.add(a); cur=a; prev=None
    while True:
        nxt=[x for x in adj[cur] if x!=prev and x not in seen]
        if not nxt: break
        prev=cur; cur=nxt[0]; seen.add(cur); loop.append(cur)
    loops.append(loop)
loops=[l for l in loops if len(l)>8]
# resample each loop every 0.5 m
S=[]
tot=0
for l in loops:
    P=V[l][:,:2]; P=np.vstack([P,P[:1]])
    seg=np.hypot(*np.diff(P,axis=0).T); s=np.concatenate([[0],np.cumsum(seg)]); L=s[-1]
    ss=np.arange(0,L,0.5)
    x=np.interp(ss,s,P[:,0]); y=np.interp(ss,s,P[:,1])
    S.append(np.stack([x,y],1)); tot+=L
print("terrain top boundary loops",len(loops),"lengths",[round(float(np.hypot(*np.diff(np.vstack([V[l][:,:2],V[l][:1,:2]]),axis=0).T).sum()),0) for l in loops],"total %.0f m"%tot)
# surf objects
surf=[o for o in bpy.data.objects if o.name.startswith('WATER_SURF')]
print("WATER_SURF objects",len(surf), "any WATER_FOAM:",[o.name for o in bpy.data.objects if 'FOAM' in o.name.upper()], "MAT_FOAM users", [m.name for m in bpy.data.materials if 'FOAM' in m.name.upper()])
pts=[];A=[];stats=[]
for o in surf:
    me=o.data; Mw=o.matrix_world
    Wv=np.array([tuple(Mw@v.co) for v in me.vertices])
    ca=me.color_attributes.get('Col') or (me.color_attributes[0] if me.color_attributes else None)
    if ca is None: print("no colour",o.name); continue
    a=np.array([c.color[3] for c in ca.data]) if ca.domain=='POINT' else None
    if a is None:
        # corner domain: map to vertex
        a=np.zeros(len(Wv))
        for li,l in enumerate(me.loops): a[l.vertex_index]=max(a[l.vertex_index],ca.data[li].color[3])
    xy=Wv[:,:2]; c=xy.mean(0); u,s_,vt=np.linalg.svd(xy-c,full_matrices=False); asp=s_[0]/max(s_[1],1e-6)
    ext=(xy-c)@vt.T; L1=np.ptp(ext[:,0]); L2=np.ptp(ext[:,1])
    # area weighted alpha
    tri_a=0;tot_a=0
    for p in me.polygons:
        vs=p.vertices; ar=p.area; tot_a+=ar; tri_a+=ar*np.mean([a[v] for v in vs])
    stats.append((o.name,L1,L2,asp,a.max(),tri_a/tot_a,Wv[:,2].mean()))
    sel=a>0.15
    pts.append(Wv[sel,:2]); A.append(a[sel])
st=np.array([s[1:] for s in stats])
print("patch long-extent m: median %.1f max %.1f ; short extent median %.1f max %.1f ; PCA aspect max %.2f ; peak alpha min %.2f max %.2f ; area-mean alpha mean %.2f ; z %.3f"%(np.median(st[:,0]),st[:,0].max(),np.median(st[:,1]),st[:,1].max(),st[:,2].max(),st[:,3].min(),st[:,3].max(),st[:,4].mean(),st[:,5].mean()))
pts=np.vstack(pts)
# coverage along shoreline: a shore sample is covered if surf (alpha>.15) within 3.0 m
res=[]
for loop in S:
    d=np.array([np.hypot(*(pts-q).T).min() for q in loop])
    cov=d<3.0
    # runs, circular
    n=len(cov)
    if cov.all(): runs=[(0,n)]; gaps=[]
    elif not cov.any(): runs=[];gaps=[]
    else:
        k0=int(np.argmin(cov)) # start at an uncovered sample
        c=np.roll(cov,-k0); runs=[];i=0
        while i<n:
            if c[i]:
                j=i
                while j<n and c[j]: j+=1
                runs.append((i,j-i)); i=j
            else: i+=1
        gaps=[(runs[(r+1)%len(runs)][0]-(runs[r][0]+runs[r][1]))%n for r in range(len(runs))] if len(runs)>1 else []
    res.append((n*0.5,cov.mean(),[r[1]*0.5 for r in runs],[g*0.5 for g in gaps]))
    print("loop L=%.0f m covered %.1f%% runs %d longest %.1f m  shortest gap %s"%(n*0.5,100*cov.mean(),len(runs),max([r[1]*0.5 for r in runs],default=0),min([g*0.5 for g in gaps],default='-')))
allruns=sum([r[2] for r in res],[]); allgaps=sum([r[3] for r in res],[])
cov_all=sum(r[0]*r[1] for r in res)/sum(r[0] for r in res)
print("TOTAL coverage %.1f%%, runs %d, longest %.1f, shortest gap %.1f, gaps<8 m: %d"%(100*cov_all,len(allruns),max(allruns,default=0),min(allgaps,default=0),sum(1 for g in allgaps if g<8)))

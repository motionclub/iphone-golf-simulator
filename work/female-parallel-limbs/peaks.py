"""blender -b final.blend --python peaks.py -- vertex_map.npz out.json
Persistent geodesic extremities of each new hand/foot (distance over mesh edges from the weld seam)."""
import bpy, numpy as np, json, sys, heapq
a=sys.argv[sys.argv.index('--')+1:]; vm=np.load(a[0]); out=a[1]
me=bpy.data.objects['Body_F'].data
mat={m.name:i for i,m in enumerate(me.materials)}
n=len(me.vertices); co=np.empty(n*3,np.float32); me.vertices.foreach_get('co',co); V=co.reshape(-1,3).astype(np.float64)
new=vm['final_to_base']<0
nbr=[[] for _ in range(n)]
for e in me.edges:
    p,q=e.vertices; d=float(np.linalg.norm(V[p]-V[q])); nbr[p].append((q,d)); nbr[q].append((p,d))
fm=np.zeros(n,bool); hm=np.zeros(n,bool)
for p in me.polygons:
    vs=list(p.vertices)
    if p.material_index==mat['Skin_F']: fm[vs]=True
    elif p.material_index==mat['Base_Grey_F']: hm[vs]=True
def region(kind,sd):
    base=(new&(fm if kind=='foot' else hm&~fm))&(np.sign(V[:,0])==sd)
    return base
def persistence(mask,seeds):
    idx=np.where(mask)[0]; ms=set(idx.tolist()); dist={}
    pq=[(0.0,s) for s in seeds]; 
    for s in seeds: dist[s]=0.0
    while pq:
        d,u=heapq.heappop(pq)
        if d>dist.get(u,1e9): continue
        for v,w in nbr[u]:
            if v in ms or v in seeds:
                nd=d+w
                if nd<dist.get(v,1e9): dist[v]=nd; heapq.heappush(pq,(nd,v))
    order=sorted([v for v in dist if v in ms],key=lambda v:-dist[v])
    parent={}; birth={}; peaks=[]
    def find(x):
        while parent[x]!=x: parent[x]=parent[parent[x]]; x=parent[x]
        return x
    for v in order:
        ns=[u for u,_ in nbr[v] if u in parent]
        if not ns:
            parent[v]=v; birth[v]=dist[v]; peaks.append([v,dist[v],None])
        else:
            roots={find(u) for u in ns}
            r=max(roots,key=lambda x:birth[x]); parent[v]=r
            for o in roots:
                if o!=r:
                    # younger (lower birth) dies at current level
                    for pk in peaks:
                        if pk[0]==o and pk[2] is None: pk[2]=birth[o]-dist[v]
                    parent[o]=r
    for pk in peaks:
        if pk[2] is None: pk[2]=pk[1]
    return peaks,dist
res={}
for kind in ('foot','hand'):
    for sd,name in ((1,'R'),(-1,'L')):
        mask=region(kind,sd)
        seeds=set()
        # seam vertices: new-region vertices adjacent to baseline (non-new) vertices
        for v in np.where(mask)[0]:
            if any(not new[u] for u,_ in nbr[v]): seeds.add(int(v))
        # also use the welded ring vertices themselves as zero-distance seeds
        ring=set()
        for v in np.where(mask)[0]:
            for u,_ in nbr[v]:
                if not new[u]: ring.add(int(u))
        peaks,dist=persistence(mask|np.isin(np.arange(n),list(ring)),ring if ring else seeds)
        pk=[(int(v),float(d),float(p)) for v,d,p in peaks if p>=0.006]
        pk.sort(key=lambda t:-t[2])
        res[f'{kind}_{name}']={'ring_verts':len(ring),'peaks_persistence_ge_6mm':[{'z':round(float(V[v][2]),4),'y':round(float(V[v][1]),4),'x':round(float(V[v][0]),4),'dist_from_seam_mm':round(d*1000,1),'persistence_mm':round(p*1000,1)} for v,d,p in pk]}
        print(kind,name,'peaks>=6mm:',len(pk),[ (round(V[v][1],3),round(V[v][2],3),round(p*1000,1)) for v,d,p in pk])
json.dump(res,open(out,'w'),indent=1)

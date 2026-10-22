import bpy, sys, numpy as np
bpy.ops.wm.open_mainfile(filepath=sys.argv[sys.argv.index("--")+1])
rows=[]
for o in bpy.data.objects:
    if o.type!='MESH' or not o.name.startswith(("DRESS_RUIN","DRESS_ARCH")): continue
    me=o.data; mw=np.array(o.matrix_world)
    co=np.array([tuple(v.co) for v in me.vertices]); W=co@mw[:3,:3].T+mw[:3,3]
    parent=list(range(len(W)))
    def find(a):
        while parent[a]!=a: parent[a]=parent[parent[a]]; a=parent[a]
        return a
    for p in me.polygons:
        vs=list(p.vertices)
        for k in range(1,len(vs)):
            a,b=find(vs[0]),find(vs[k])
            if a!=b: parent[a]=b
    comp={}
    for i in range(len(W)): comp.setdefault(find(i),[]).append(i)
    for vs in comp.values():
        P=W[vs]; ext=P.max(0)-P.min(0); c=P[:,:2].mean(0)
        w,v=np.linalg.eigh(np.cov((P[:,:2]-c).T)+1e-9*np.eye(2))
        L=float(np.ptp((P[:,:2]-c)@v[:,1])); bb=float(max(ext[0],ext[1]))
        rows.append((o.name[:11],L,bb,float(ext[2])))
L=np.array([r[1] for r in rows]); B=np.array([r[2] for r in rows]); H=np.array([r[3] for r in rows])
def cv(x): return x.std()/x.mean()
print("all",len(L),"CV axis",round(cv(L),3),"CV bbox",round(cv(B),3),"mean L",round(L.mean(),2),"mean bb",round(B.mean(),2))
for cut in (0.6,0.8):
    m=H>cut
    print("height >",cut,"n",m.sum(),"CV axis",round(cv(L[m]),3),"bbox",round(cv(B[m]),3))
m=H<=0.8
print("small stones (h<=0.8) n",m.sum(),"CV axis",round(cv(L[m]),3),"CV bbox",round(cv(B[m]),3))
print("hist L:",np.histogram(L,bins=[0,0.4,0.6,0.8,1.0,1.2,1.5,2.0,4.0])[0].tolist())
print("hist bbox:",np.histogram(B,bins=[0,0.4,0.6,0.8,1.0,1.2,1.5,2.0,4.0])[0].tolist())

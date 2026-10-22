import bpy, sys, numpy as np
bpy.ops.wm.open_mainfile(filepath=sys.argv[sys.argv.index("--")+1])
c=np.array([-59.11,101.8]); ax=np.array([-0.956,-0.292]); nrm=np.array([-ax[1],ax[0]])
rows=[]
for o in bpy.data.objects:
    if o.type!='MESH' or not o.name.startswith("DRESS_RUIN"): continue
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
        P=W[vs]
        s=(P[:,:2]-c)@ax; n=(P[:,:2]-c)@nrm
        if abs(n.mean())<1.0 and abs(s.mean())<4 and P[:,2].min()>6.5:
            rows.append((round(P[:,2].min(),2),round(P[:,2].max(),2),round(s.min(),2),round(s.max(),2),round(n.min(),2),round(n.max(),2)))
for r in sorted(rows): print("S",r)

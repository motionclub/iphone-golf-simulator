import bpy, sys, numpy as np
bpy.ops.wm.open_mainfile(filepath=sys.argv[sys.argv.index("--")+1])
cx,cy,cz=[float(x) for x in sys.argv[sys.argv.index("--")+2:sys.argv.index("--")+5]]
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
        P=W[vs]; c=P.mean(0)
        if abs(c[0]-cx)<3 and abs(c[1]-cy)<3 and abs(c[2]-cz)<1.2:
            rows.append((round(c[2],2),o.name,c.round(2).tolist(),P.min(0).round(2).tolist(),P.max(0).round(2).tolist()))
for r in sorted(rows): print("STONE",r)

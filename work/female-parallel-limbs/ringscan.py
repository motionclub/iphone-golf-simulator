import bpy, bmesh, numpy as np
me=bpy.data.objects['Body_F'].data
mat={m.name:i for i,m in enumerate(me.materials)}
def comps(edges):
    seen=set(); out=[]; vmap={}
    for e in edges:
        for v in e.verts: vmap.setdefault(v,[]).append(e)
    for e in edges:
        if e in seen: continue
        comp=[];st=[e];seen.add(e)
        while st:
            x=st.pop();comp.append(x)
            for v in x.verts:
                for y in vmap[v]:
                    if y not in seen: seen.add(y);st.append(y)
        out.append(comp)
    return out
for lev in (0.84559,0.85913,0.87263,0.88613,0.89963,0.91313,0.92663):
    bm=bmesh.new(); bm.from_mesh(me)
    dl=[]
    for f in bm.faces:
        zs=[v.co.z for v in f.verts]; xs=[v.co.x for v in f.verts]
        if f.material_index==mat['Base_Grey_F'] and min(abs(x) for x in xs)>0.195 and 0.60<min(zs) and max(zs)<=lev+1e-4: dl.append(f)
    bmesh.ops.delete(bm,geom=dl,context='FACES')
    res=[]
    for c in comps([e for e in bm.edges if len(e.link_faces)==1]):
        vs={v for e in c for v in e.verts}; P=np.array([v.co[:] for v in vs]); cc=P.mean(0)
        if cc[2]<0.5: continue
        ext=P.max(0)-P.min(0)
        res.append((int(np.sign(cc[0])),len(c),round(P[:,2].max()-P[:,2].min(),4),tuple(np.round(ext[:2],4)),tuple(np.round(cc[:2],4))))
    print(round(lev,5),sorted(res))
    bm.free()

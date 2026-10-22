import bpy, bmesh, numpy as np
me=bpy.data.objects['Body_F'].data
mat={m.name:i for i,m in enumerate(me.materials)}
bm=bmesh.new(); bm.from_mesh(me)
ZA=0.15728244185447693
dl=[]
for f in bm.faces:
    zs=[v.co.z for v in f.verts]; xs=[abs(v.co.x) for v in f.verts]
    if f.material_index==mat['Skin_F'] and max(zs)<=ZA+1e-6: dl.append(f)
    elif f.material_index==mat['Base_Grey_F'] and min(xs)>0.195 and 0.60<min(zs) and max(zs)<=0.8457: dl.append(f)
bmesh.ops.delete(bm,geom=dl,context='FACES')
es=[e for e in bm.edges if len(e.link_faces)==1]
print('boundary edges',len(es))
vm={}
for e in es:
    for v in e.verts: vm.setdefault(v,[]).append(e)
seen=set()
for e in es:
    if e in seen: continue
    comp=[];st=[e];seen.add(e)
    while st:
        x=st.pop();comp.append(x)
        for v in x.verts:
            for y in vm[v]:
                if y not in seen: seen.add(y);st.append(y)
    vs=sorted({v for x in comp for v in x.verts},key=lambda v:v.index)
    P=np.array([v.co[:] for v in vs])
    print('loop edges',len(comp),'verts',len(vs),'centre',P.mean(0).round(4),'z min/max',P[:,2].min().round(5),P[:,2].max().round(5),'x range',P[:,0].min().round(4),P[:,0].max().round(4),'y range',P[:,1].min().round(4),P[:,1].max().round(4))
    zs=np.round(P[:,2],5); import collections; print('   z levels',dict(collections.Counter(zs)))
print('---- right ankle notch')
for v in bm.verts:
    if v.co.x>0.07 and abs(v.co.z-0.14379)<1e-4 and v.is_boundary:
        print('vert',v.index,np.round(v.co[:],4),'faces',[(f.material_index,np.round([u.co.z for u in f.verts],4).tolist()) for f in v.link_faces])
# also what is above ring on right side near x=0.079
for v in bm.verts:
    if 0.07<v.co.x<0.085 and 0.1575<v.co.z<0.176 and abs(v.co.y)<0.04:
        print('bump vert',v.index,np.round(v.co[:],4),'valence',len(v.link_faces),[f.material_index for f in v.link_faces])

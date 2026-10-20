import bpy, bmesh, numpy as np, collections
me=bpy.data.objects['Body_F'].data
bm=bmesh.new(); bm.from_mesh(me); bm.verts.ensure_lookup_table()
sel=[v.index for v in bm.verts if v.co.x>0.15 and v.co.z<1.10 and v.co.z>0.55]
S=set(sel); comp={}; cid=0
for s in sel:
    if s in comp: continue
    st=[s]; comp[s]=cid
    while st:
        a=st.pop()
        for e in bm.verts[a].link_edges:
            o=e.other_vert(bm.verts[a]).index
            if o in S and o not in comp: comp[o]=cid; st.append(o)
    cid+=1
cnt=collections.Counter(comp.values()); print('components',cnt)
big=max(cnt,key=lambda k:cnt[k]); arm=[i for i in sel if comp[i]==big]
v=np.array([tuple(bm.verts[i].co) for i in arm]); print('arm comp',len(arm),v.min(0).round(3),v.max(0).round(3))
# distinct z levels with >=8 verts
z=np.round(v[:,2],3); 
for zz in sorted(set(z),reverse=True):
    m=z==zz
    if m.sum()>=6: print(zz,m.sum(),v[m].mean(0).round(4),(v[m].max(0)-v[m].min(0)).round(4))
# also count faces & tris in hand region z<0.84
hv=set(i for i in arm if bm.verts[i].co.z<0.832)
print('hand verts',len(hv), 'faces fully in hand', sum(1 for f in bm.faces if all(x.index in hv for x in f.verts)))

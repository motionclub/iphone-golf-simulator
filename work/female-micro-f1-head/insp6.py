import bpy, numpy as np, collections
o = bpy.data.objects['Body_F']; me = o.data
V = np.empty(len(me.vertices)*3); me.vertices.foreach_get('co', V); V = V.reshape(-1,3)
nl=len(me.loops); cv=np.empty(nl,np.int64); me.loops.foreach_get('vertex_index',cv)
ls=np.empty(len(me.polygons),np.int64); me.polygons.foreach_get('loop_start',ls)
lt=np.empty(len(me.polygons),np.int64); me.polygons.foreach_get('loop_total',lt)
mi=np.empty(len(me.polygons),np.int32); me.polygons.foreach_get('material_index',mi)
F=[cv[a:a+b] for a,b in zip(ls,lt)]
names=[m.name for m in me.materials]
grey=names.index('Base_Grey_F')
# union-find over vertices through non-grey faces
par=list(range(len(V)))
def find(a):
    while par[a]!=a:
        par[a]=par[par[a]]; a=par[a]
    return a
for f,m in zip(F,mi):
    if m==grey: continue
    for v in f[1:]:
        ra,rb=find(f[0]),find(v)
        if ra!=rb: par[ra]=rb
comp=collections.defaultdict(list)
for fi,(f,m) in enumerate(zip(F,mi)):
    if m!=grey: comp[find(f[0])].append(fi)
print('non-grey components:',len(comp))
for r,fl in sorted(comp.items(), key=lambda kv:-len(kv[1])):
    vs=sorted({int(v) for fi in fl for v in F[fi]})
    zz=V[vs,2]
    print('comp faces',len(fl),'verts',len(vs),'z %.3f..%.3f'%(zz.min(),zz.max()),'idx %d..%d'%(min(vs),max(vs)), {names[k]:int((mi[fl]==k).sum()) for k in set(mi[fl])})
# grey/skin boundary edges near neck
em=collections.defaultdict(set)
for fi,f in enumerate(F):
    for i in range(len(f)):
        a,b=int(f[i]),int(f[(i+1)%len(f)])
        em[(min(a,b),max(a,b))].add(fi)
skin=names.index('Skin_F')
bv=set()
for (a,b),fs in em.items():
    ms={int(mi[fi]) for fi in fs}
    if grey in ms and skin in ms:
        bv.add(a); bv.add(b)
bv=sorted(bv)
print('grey/skin boundary verts',len(bv))
zb=V[bv,2]
sel=[v for v in bv if V[v,2]>1.3]
print('neck boundary verts', len(sel), 'z range', V[sel,2].min(), V[sel,2].max())
for v in sel: print(v, np.round(V[v],4))

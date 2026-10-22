import bpy, numpy as np, collections
o = bpy.data.objects['Body_F']; me = o.data
V = np.empty(len(me.vertices)*3); me.vertices.foreach_get('co', V); V = V.reshape(-1,3)
n=len(V)
E=np.empty(len(me.edges)*2,np.int64); me.edges.foreach_get('vertices',E); E=E.reshape(-1,2)
nb=collections.defaultdict(set)
for a,b in E: nb[a].add(b); nb[b].add(a)
z=V[:,2]
# index ranges by z band
def rng(mask): 
    i=np.where(mask)[0]; return (i.min(), i.max(), len(i)) if len(i) else None
print('verts z>1.44:', rng(z>1.44))
print('verts z in 1.40..1.44', rng((z>1.40)&(z<1.44)))
print('verts z<1.40', rng(z<1.40))
# index histogram per 1000 for z>1.40
idx=np.arange(n)
for k in range(0,n,1000):
    m=(idx>=k)&(idx<k+1000)
    print(k, 'zmin %.3f zmax %.3f'%(z[m].min(), z[m].max()))

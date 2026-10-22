import bpy, numpy as np, sys
vm=np.load('data/final10_vertex_map.npz'); me=bpy.data.objects['Body_F'].data
n=len(me.vertices); co=np.empty(n*3,np.float32); me.vertices.foreach_get('co',co); V=co.reshape(-1,3)
new=vm['final_to_base']<0
P=V[new&(V[:,0]>0)&(V[:,2]<0.05)&(V[:,1]<0.0)]
xs=P[:,0]; bins=np.arange(xs.min(),xs.max()+0.003,0.003)
row=[]
for i in range(len(bins)-1):
    m=(xs>=bins[i])&(xs<bins[i+1])
    if m.any(): row.append((round(float(bins[i]),3),round(float(P[m][:,1].min()),3)))
print(row)

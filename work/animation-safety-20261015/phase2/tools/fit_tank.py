"""Fit a bounded, pose-space tank corrective to a Unity-evaluated shoulder pose.
Blender --background --python fit_tank.py -- <dump directory> <output .bytes>
The garment's rest positions, topology, UVs and thickness are retained.
"""
import sys,os,struct
sys.path.insert(0,os.path.dirname(__file__))
from deformation_mesh import read
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
root,out=sys.argv[sys.argv.index('--')+1:]
bp,bq,bt,bw,bn=read(root+'/IntroWave_body');gp,gq,gt,gw,gn=read(root+'/IntroWave_Kit_Top')
M=np.fromfile(root+'/IntroWave_Kit_Top-matrices.bin','f4').reshape(-1,4,4).transpose(0,2,1)
weighted=sum(gw['bw'][:,k,None,None]*M[gw['bi'][:,k],:3,:3]for k in range(4))
tree=BVHTree.FromPolygons([tuple(p)for p in bq],[tuple(t)for t in bt],all_triangles=True)
# Use radial cloth normals to treat inner/outer walls identically.
radial=np.column_stack([gp[:,0],gp[:,1]+.015,np.zeros(len(gp))]);radial/=np.maximum(np.linalg.norm(radial,axis=1,keepdims=True),1e-12)
normal=np.einsum('nij,nj->ni',weighted,radial);normal/=np.maximum(np.linalg.norm(normal,axis=1,keepdims=True),1e-12)
lift=np.zeros(len(gp));mask=(gp[:,0]<-.055)&(gp[:,2]>1.12)&(gp[:,2]<1.34)
for i in np.where(mask)[0]:
 hit=tree.ray_cast(Vector(gq[i]),Vector(normal[i]),.045)
 if hit[0] is not None and np.dot(hit[1],normal[i])>0:lift[i]=min(.03,hit[3]+.004)
# Weld equal/similar garment positions before spreading the correction. Both
# walls and trim keep the same displacement, instead of collapsing thickness.
from mathutils.kdtree import KDTree
kd=KDTree(len(gp))
for i,p in enumerate(gp):kd.insert(p,i)
kd.balance()
for _ in range(3):
 new=lift.copy()
 for i in np.where(mask)[0]:
  for _,j,d in kd.find_range(gp[i],.009):new[i]=max(new[i],lift[j]*max(0,1-d/.025))
 lift=new
for _ in range(3):
 new=lift.copy()
 for i in np.where(mask)[0]:
  near=kd.find_range(gp[i],.009);new[i]=.5*lift[i]+.5*sum(lift[j]for _,j,_ in near)/max(1,len(near))
 lift=new
left=np.linalg.solve(weighted,(normal*lift[:,None])[:,:,None])[:,:,0]*1.3
# Right-side counterpart is transferred in garment rest space, preserving the
# asymmetric fitted garment instead of replacing it with mirrored geometry.
right=np.zeros_like(left)
for i,p in enumerate(gp):
 if p[0]<=.04:continue
 mirror=p.copy();mirror[0]*=-1
 _,j,_=kd.find(mirror);right[i]=left[j];right[i,0]*=-1
with open(out,'wb')as f:
 f.write(struct.pack('<i',len(gp)));f.write(left.astype('<f4').tobytes());f.write(right.astype('<f4').tobytes())
print('Tank pose corrective: vertices',len(gp),'left affected',int((lift>1e-4).sum()),'max mm',float(lift.max()*1000))

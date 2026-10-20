import bpy,sys,math,numpy as np,bmesh
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from pathlib import Path
R=Path(sys.argv[sys.argv.index('--')+1]);W=R/'work/cloth-overhaul'
for sex in ['Male','Female']:
 bpy.ops.wm.open_mainfile(filepath=str(W/f'export/Cloth_{sex}.blend'))
 for o in bpy.data.objects:
  if o.type!='MESH' or o.name.endswith('_High'):continue
  m=o.data;bm=bmesh.new();bm.from_mesh(m);tree=BVHTree.FromBMesh(bm);N=np.array([v.normal[:] for v in m.vertices]);P=np.array([v.co[:] for v in m.vertices]);ao=np.zeros(len(P));reach=.022 if o.name=='Kit_Top' else .014
  # Deterministic cosine hemisphere, no randomized frame-to-frame shading.
  dirs=[]
  for i in range(24):
   u=(i+.5)/24;angle=i*math.pi*(3-math.sqrt(5));rad=math.sqrt(u);dirs.append((rad*math.cos(angle),rad*math.sin(angle),math.sqrt(1-u)))
  for i,(p,n) in enumerate(zip(P,N)):
   n=Vector(n).normalized();t=n.cross(Vector((1,0,0)) if abs(n.x)<.9 else Vector((0,1,0))).normalized();b=n.cross(t);origin=Vector(p)+n*.0004
   for dx,dy,dz in dirs:
    hit=tree.ray_cast(origin,t*dx+b*dy+n*dz,reach)
    if hit[0] is not None:ao[i]+=(1-hit[3]/reach)/24
  path=W/f'export/{sex}_{o.name}.npz';x=np.load(path);data={k:x[k] for k in x.files};data['ao']=ao;np.savez(path,**data);bm.free();print(sex,o.name,'AOmean',float(ao.mean()),flush=True)

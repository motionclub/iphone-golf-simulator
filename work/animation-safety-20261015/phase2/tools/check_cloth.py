"""Triangle/triangle intersection audit of Unity-baked skirt and full body.
Blender --background --python check_cloth.py -- <live dumps> <full-body reference dump> <npz garment> <output json>
"""
import sys,os,json,glob,collections
sys.path.insert(0,os.path.dirname(__file__))
from deformation_mesh import read
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from mathutils.geometry import intersect_ray_tri
root,reference,garment,out=sys.argv[sys.argv.index('--')+1:]
rp,rq,rt,rw,rn=read(reference);g=np.load(garment);outer=g['tri'][(g['kind']==11)&(g['part']==0)]
results=[]
for body_path in sorted(glob.glob(root+'/*_body.bin')):
 clip=os.path.basename(body_path).removesuffix('_body.bin')
 bp,bq,bt,bw,bn=read(root+'/'+clip+'_body');gp,gq,gt,gw,gn=read(root+'/'+clip+'_Kit_Bottom')
 assert np.array_equal(bp,rp),'Full-body triangle reference no longer matches current rest positions'
 assert np.allclose(gp,g['pos'],atol=1e-7),'Skirt topology no longer matches metadata'
 bt=rt
 body=BVHTree.FromPolygons([tuple(p)for p in bq],[tuple(t)for t in bt],all_triangles=True)
 cloth=BVHTree.FromPolygons([tuple(p)for p in gq],[tuple(t)for t in outer],all_triangles=True)
 pairs=body.overlap(cloth);cross=[]
 for bi,gi in pairs:
  a=[Vector(p)for p in bq[bt[bi]]];b=[Vector(p)for p in gq[outer[gi]]];hits=[]
  for source,target in [(a,b),(b,a)]:
   for j in range(3):
    x=source[j];d=source[(j+1)%3]-x;length=d.length
    if length<1e-8:continue
    h=intersect_ray_tri(*target,d.normalized(),x,True)
    if h is not None and (h-x).dot(d)>0 and (h-x).length<length-1e-6 and (h-x).length>1e-6:hits.append(np.array(h))
  if len(hits)>=2 and max(np.linalg.norm(x-y)for x in hits for y in hits)>.001:cross.append((int(bi),int(gi),float(max(np.linalg.norm(x-y)for x in hits for y in hits))))
 body_parts=collections.Counter()
 for bi,gi,length in cross:
  mass=collections.Counter()
  for v in bt[bi]:
   for bone,weight in zip(bw['bi'][v],bw['bw'][v]):mass[bn[bone]]+=float(weight)
  body_parts[mass.most_common(1)[0][0]]+=1
 probe={}
 joint_file=root+'/'+clip+'_body-joints.tsv'
 if os.path.exists(joint_file) and cross:
  joints={a[0]:np.array(list(map(float,a[1:])))for a in [line.split('\t')for line in open(joint_file)]}
  centers=np.array([gq[outer[gi]].mean(0)for bi,gi,length in cross])
  for start,end,radius in [('RightLowerArm','RightHand',.09),('RightHand','RightMiddleProximal',.095)]:
   a=joints[start];b=joints[end];axis=b-a;t=np.clip((centers-a)@axis/np.dot(axis,axis),0,1)
   depth=radius-np.linalg.norm(centers-a-t[:,None]*axis,axis=1);probe[start+'MaxDepth']=float(depth.max())
 results.append(dict(proxyProbe=probe,bodyParts=dict(body_parts),clip=clip,candidatePairs=len(pairs),crossingPairsOver1mm=len(cross),maxCrossingLength=max([x[2]for x in cross],default=0),garmentRestRegions=[gp[outer[x[1]]].mean(0).tolist()for x in sorted(cross,key=lambda x:-x[2])[:8]]))
print(json.dumps(results,indent=2));json.dump(results,open(out,'w'),indent=2)

import json,numpy as np
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from mathutils.geometry import barycentric_transform
w=Path('work/character-female33');get=lambda file:next(p for p in json.loads((w/file).read_text())['parts'] if p['name']=='Kit_Top');f=get('cuff-fit-source/poses/female_intro.json');d=get('distance-source/poses/female_intro.json');P=np.array(f['vertices']).reshape(-1,3);F=np.array(f['triangles']).reshape(-1,3);D=np.array(d['vertices']).reshape(-1,3);z=np.load(w/'male-template-correspondence.npz');MP=z['P'];MN=z['N'];tree=BVHTree.FromPolygons([Vector(p) for p in P],F.tolist(),all_triangles=True);outP=[];outN=[]
for p in D:
 hit,n,fi,dist=tree.find_nearest(Vector(p));ids=F[fi];bc=np.array(barycentric_transform(hit,*[Vector(P[j]) for j in ids],Vector((1,0,0)),Vector((0,1,0)),Vector((0,0,1))));
 if not np.isfinite(bc).all():
  near=int(np.argmin(np.linalg.norm(P[ids]-p,axis=1)));bc=np.eye(3)[near]
 bc=np.clip(bc,0,1);bc/=bc.sum();outP.append(bc@MP[ids]);n=bc@MN[ids];outN.append(n/max(np.linalg.norm(n),1e-8))
assert np.isfinite(outP).all() and np.isfinite(outN).all()
np.savez_compressed(w/'male-template-distance-correspondence.npz',P=outP,N=outN);print('DONE',len(D))

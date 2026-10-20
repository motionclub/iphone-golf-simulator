import json,numpy as np
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from mathutils.geometry import barycentric_transform
w=Path('work/character-female33');source=json.loads((w/'baseline/poses/female_intro.json').read_text());old=next(p for p in source['parts'] if p['name']=='Kit_Top');data=json.loads((w/'distance-source/poses/female_intro.json').read_text());top=next(p for p in data['parts'] if p['name']=='Kit_Top');P=np.array(top['vertices']).reshape(-1,3);N=np.array(top['normals']).reshape(-1,3);OP=np.array(old['vertices']).reshape(-1,3);F=np.array(old['triangles']).reshape(-1,3);W=np.array(old['weights']).reshape(-1,4);I=np.array(old['indices']).reshape(-1,4);names=old['bones'];OW=np.array([(W*(I==j)).sum(1) for j in range(len(names))]).T
bvh=BVHTree.FromPolygons([Vector(p) for p in OP],F.tolist(),all_triangles=True);dense=[];distances=[]
for p in P:
 hit,n,fi,dist=bvh.find_nearest(Vector(p));ids=F[fi];bc=barycentric_transform(hit,*[Vector(OP[j]) for j in ids],Vector((1,0,0)),Vector((0,1,0)),Vector((0,0,1)));bc=np.clip(np.array(bc),0,1);bc/=bc.sum();dense.append(bc@OW[ids]);distances.append(dist)
dense=np.array(dense);control=json.loads((w/'matrix-cuff-fit-profile.json').read_text().split(',"anchors":',1)[0]+'}');allowed={x['bone'].removeprefix('Swing_') for x in control['controls']}|{'Chest'}
for j,name in enumerate(names):
 if name not in allowed:dense[:,names.index('Chest')]+=dense[:,j];dense[:,j]=0
np.savez_compressed(w/'female-garment-distance-bindings.npz',weights=dense,boneNames=np.array(names));print('Transferred female garment weights',dense.shape,'maxdist',max(distances))

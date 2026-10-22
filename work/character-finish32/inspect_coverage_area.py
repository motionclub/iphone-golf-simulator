import json,numpy as np
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
w=Path('work/character-finish32');b=json.loads((w/'refined/poses/male_intro.json').read_text())['parts'][0];P=np.array(b['vertices']).reshape(-1,3);M=np.array(b['rendererToRoot']).reshape(4,4);P=P@M[:3,:3].T+M[:3,3];T=np.array(b['triangles']).reshape(-1,3);tree=BVHTree.FromPolygons([Vector(p) for p in P],T.tolist(),all_triangles=True);missing=json.loads((w/'coverage-reconciliation.json').read_text())['obsoleteFaces']
for f in missing:
 f=np.array(f);mid=f.mean(0);hit,n,i,dist=tree.find_nearest(Vector(mid));area=np.linalg.norm(np.cross(f[1]-f[0],f[2]-f[0]))*.5;print('OLD',f.tolist(),'area_mm2',area*1e6,'distance_mm',dist*1000,'actual',P[T[i]].tolist(),flush=True)

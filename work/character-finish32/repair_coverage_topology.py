import json,numpy as np
from pathlib import Path
from collections import Counter
from mathutils import Vector
from mathutils.kdtree import KDTree
w=Path('work/character-finish32');b=json.loads((w/'refined/poses/male_intro.json').read_text())['parts'][0];P=np.array(b['vertices']).reshape(-1,3);M=np.array(b['rendererToRoot']).reshape(4,4);P=P@M[:3,:3].T+M[:3,3];T=np.array(b['triangles']).reshape(-1,3);U,alias=np.unique(np.round(P,6),axis=0,return_inverse=True);tree=KDTree(len(U))
for i,p in enumerate(U):tree.insert(Vector(p),i)
tree.balance();source=Path('Unity/Assets/Resources/Tennis/GarmentCoverage/Tennis_Male.json');profile=json.loads(source.read_text());oldPoints=np.array(profile['removedTriangleRootPositions']).reshape(-1,3,3);old=[]
for face in oldPoints:
 rows=[tree.find(Vector(p)) for p in face]
 if max(row[2] for row in rows)>.000001:raise ValueError('Coverage boundary vertex moved')
 old.append(tuple(sorted(row[1] for row in rows)))
old=set(old)
def boundary(faces):
 count=Counter(e for f in faces for e in [tuple(sorted((f[0],f[1]))),tuple(sorted((f[1],f[2]))),tuple(sorted((f[2],f[0])))])
 return {e for e,n in count.items() if n==1}
border=boundary(old);borderVertices=set(i for edge in border for i in edge);inside=set(i for f in old for i in f)-borderVertices;result={};added=[]
for tri in T:
 key=tuple(sorted(alias[tri]));existing=key in old
 if existing or all(i in inside for i in key):
  result[key]=P[tri]
  if not existing:added.append(key)
new=set(result);after=boundary(new);missing=old-new
if after!=border:raise ValueError(f'Coverage boundary changed: old{len(border)} new{len(after)} added{len(after-border)} missing{len(border-after)}')
def area(points):return sum(np.linalg.norm(np.cross(f[1]-f[0],f[2]-f[0]))*.5 for f in points)
report={'oldFaces':len(old),'newFaces':len(new),'replacedOldFaces':len(missing),'newInteriorTriangles':len(set(added)),'identicalBoundaryEdges':len(border),'boundaryChanged':False,'oldAreaSquareMetres':area(oldPoints),'newAreaSquareMetres':area(result.values()),'bodySourceChanged':False}
profile['garmentVertexCount']=22883;profile['expectedRemovedFaceCount']=len(result);profile['removedTriangleRootPositions']=np.array(list(result.values())).ravel().tolist();(w/'coverage-topology-profile.json').write_text(json.dumps(profile,separators=(',',':')));(w/'coverage-topology-report.json').write_text(json.dumps(report,indent=2));print(report,flush=True)

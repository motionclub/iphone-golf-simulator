import json,numpy as np
from pathlib import Path
from mathutils import Vector
from mathutils.kdtree import KDTree
w=Path('work/character-finish32');data=json.loads((w/'refined/poses/male_intro.json').read_text());body=data['parts'][0];top=next(p for p in data['parts'] if p['name']=='Kit_Top');P=np.array(body['vertices']).reshape(-1,3);M=np.array(body['rendererToRoot']).reshape(4,4);P=P@M[:3,:3].T+M[:3,3];T=np.array(body['triangles']).reshape(-1,3);uni,alias=np.unique(np.round(P,6),axis=0,return_inverse=True);faces={tuple(sorted(alias[t])) for t in T};tree=KDTree(len(uni))
for j,p in enumerate(uni):tree.insert(Vector(p),j)
tree.balance();source=Path('Unity/Assets/Resources/Tennis/GarmentCoverage/Tennis_Male.json');d=json.loads(source.read_text());coords=np.array(d['removedTriangleRootPositions']).reshape(-1,3,3);kept=[];missing=[]
for f in coords:
 rows=[tree.find(Vector(p)) for p in f];key=tuple(sorted(row[1] for row in rows))
 if max(row[2] for row in rows)<.00004 and key in faces:kept.extend(f.ravel().tolist())
 else:missing.append(f.tolist())
d['garmentVertexCount']=len(top['vertices'])//3;d['expectedRemovedFaceCount']=len(kept)//9;d['removedTriangleRootPositions']=kept;(w/'review-project/Unity/Assets/Resources/Tennis/GarmentCoverage/Tennis_Male.json').write_text(json.dumps(d,separators=(',',':')));(w/'coverage-reconciliation.json').write_text(json.dumps({'originalFaceCount':len(coords),'retainedFaceCount':len(kept)//9,'newCoverageFaces':0,'obsoleteFaces':missing},indent=2));print('RECONCILED',len(coords),len(kept)//9,'obsolete',len(missing),flush=True)
q=json.loads((w/'production-coverage-queue.json').read_text());q[0]['name']='character-finish32-coverage-reconciled';q[0]['env']['VISUAL_CHARACTER_OUT']=str(w.resolve()/'coverage-reconciled');(w/'coverage-reconciled-queue.json').write_text(json.dumps(q,indent=2))

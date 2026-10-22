import sys,json,hashlib,numpy as np
from pathlib import Path
sys.path.insert(0,'work/reference-rebuild/golf-garment-panel1');from common import *
W=R/'work/reference-rebuild/golf-garment-mask1';loops=json.loads((W/'open-loop-audit.json').read_text());report={}
for sex in ('Male','Female'):
 body,top,raw=source(sex);base=arr(top,'vertices',3);rt=np.array(top['rendererToRoot']).reshape(4,4);rest=xf(rt,base);tri=arr(top,'triangles',3).astype(int);lookup={};weld=np.array([lookup.setdefault(tuple(np.round(q*1e5).astype(int)),len(lookup)) for q in base]);parent=np.arange(len(lookup))
 def find(i):
  while parent[i]!=i:parent[i]=parent[parent[i]];i=parent[i]
  return i
 def join(a,b):
  a=find(a);b=find(b)
  if a!=b:parent[b]=a
 for a,b,c in weld[tri]:join(int(a),int(b));join(int(a),int(c))
 component=np.array([find(i) for i in weld]);faceComponents=component[tri[:,0]];roots=set();selections=[]
 cb=rt[None]@np.linalg.inv(arr(top,'bindposes',16).reshape(-1,4,4))
 for loop in loops[sex]['axillaBoundaryComponents']:
  if loop['connectedGarmentFaceCount']>64:continue
  comp=int(component[loop['orderedSourceIndices'][0]])
  if comp in roots:continue
  faces=np.where(faceComponents==comp)[0];vertices=np.unique(tri[faces]);q=rest[vertices];side='Left' if q[:,0].mean()<0 else 'Right';a=cb[top['bones'].index(side+'UpperArm'),:3,3];b=cb[top['bones'].index(side+'LowerArm'),:3,3];along=(q-a)@(b-a)/sum((b-a)**2)
  # Hard region guard: far from collar/placket and .09+ upper-arm length above the true .75 cuff.
  safe=(len(faces)<=64 and np.min(abs(q[:,0]))>.105 and q[:,1].min()>1.095 and q[:,1].max()<(1.385 if sex=='Male' else 1.345) and along.max()<.66)
  if not safe:continue
  roots.add(comp);selections.append({'componentId':comp,'faceIds':faces.tolist(),'vertexIds':vertices.tolist(),'faceCount':len(faces),'rootBoundsMetres':[q.min(0).tolist(),q.max(0).tolist()],'upperArmFractionRange':[float(along.min()),float(along.max())],'submeshId':0,'materialSlot':0,'reason':'Detached1–44face proximal axilla fragment; not connected to main polo. Outside centralcollar/placket, wellproximal to sourcecuff. No mainshirttriangle removed.'})
 faceIds=sorted(f for p in selections for f in p['faceIds']);keys=rest[tri[faceIds]];asset=R/f'Unity/Assets/Resources/Golf/Fitted_{sex}_Top.asset';snap=D/f'poses/{sex.lower()}_Driver_top.json'
 profile={'sex':sex,'sport':'Golf','part':'Kit_Top','sourceResource':f'Golf/Fitted_{sex}_Top','sourceGarmentSha256':hashlib.sha256(asset.read_bytes()).hexdigest(),'sourcePoseSha256':hashlib.sha256(snap.read_bytes()).hexdigest(),'sourceAuthorSha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'sourceGarmentVertexCount':len(base),'sourceGarmentTriangleCount':len(tri),'sourceShapeNames':[str(n) for n in raw['shapeNames']],'expectedRemovedFaceCount':len(faceIds),'removedTriangleIds':faceIds,'removedTriangleRootPositions':keys.reshape(-1).tolist(),'submeshIds':[0]*len(faceIds),'materialSlotIds':[0]*len(faceIds),'components':selections,'coordinateBasis':'Canonical hero rootspace metres; apply rendererToRoot to exact prepared bindmesh positions, unorderedtriangle matching1e-5metres','contract':'OPTIONAL UNRENDERED source candidate only. Main polo/collar/placket/cuff and all vertexattributes/UV/weights/bindposes/7morphs exact. Omit only identified tiny detached proximalaxilla fragments; zero newvertices/triangles. Test only if combinedmask+twosided actual stillshowswhiteedges. No sourcepromotion.'}
 (W/f'Fragments_{sex}_Runtime.json').write_text(json.dumps(profile,separators=(',',':')));report[sex]={'removedFaceCount':len(faceIds),'components':selections};print(sex,len(faceIds),'faces',len(selections),'components',flush=True)
(W/'fragment-report.json').write_text(json.dumps(report,indent=2)+'\n')

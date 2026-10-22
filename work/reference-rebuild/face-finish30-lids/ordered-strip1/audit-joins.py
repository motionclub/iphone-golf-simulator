import bpy,numpy as np,json,collections
from pathlib import Path
O=Path.cwd()/'work/reference-rebuild/face-finish30-lids/ordered-strip1';report={}
for sex in ['Male','Female']:
 bpy.ops.wm.open_mainfile(filepath=str(O/f'{sex}_Face30OrderedLids.blend'));me=bpy.data.objects['Body'].data;p=np.array([v.co[:]for v in me.vertices]);T=np.array([q.vertices[:]for q in me.polygons]);prefix=43900 if sex=='Male'else 34366;newmask=np.any(T>=prefix,axis=1);edge=collections.defaultdict(list)
 for fi,t in enumerate(T):
  for a,b in zip(t,np.roll(t,-1)):edge[tuple(sorted((int(a),int(b))))].append((fi,int(a)<int(b)))
 same=[(e,v)for e,v in edge.items()if len(v)==2 and v[0][1]==v[1][1]and any(newmask[q[0]]for q in v)];extra=[(e,v)for e,v in edge.items()if len(v)>2 and any(newmask[q[0]]for q in v)];report[sex]={'newTriangles':int(newmask.sum()),'sameDirectedSharedEdges':len(same),'nonManifoldEdges':len(extra),'badEdges':[e for e,v in same[:30]]}
(O/'JOIN_AUDIT.json').write_text(json.dumps(report,indent=2));print(report)

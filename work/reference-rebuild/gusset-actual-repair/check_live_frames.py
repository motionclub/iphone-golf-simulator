from pathlib import Path
import json,numpy as np
R=Path.cwd();O=R/'work/reference-rebuild/gusset-actual-repair';p=json.loads((O/'UnderarmGusset_Female_Full.json').read_text());q=json.loads((R/'Unity/Assets/Resources/Tennis/Correctives/SleeveFit_Female.json').read_text());src=np.array(p['sourceVertices']).reshape(-1,3);ids=np.array(p['sourceIndices']).reshape(-1,3);sw=np.array(p['sourceWeights']).reshape(-1,3);bi=np.array(p['boneIndices']).reshape(-1,4);bw=np.array(p['weights']).reshape(-1,4);free=np.array(p['freeVertices']);isfree=np.zeros(p['vertexCount'],bool);isfree[free]=True;tri=np.array(p['triangles']).reshape(-1,3);solve=set(tri[isfree[tri].any(1)].ravel().tolist());boundary=set(p['panelBoundaryIndices'])|set(p['panelBoundaryEdges']);report={'originalMissingBoundaryRepresentatives':len(boundary-solve),'fixedMissingBoundaryRepresentatives':len(boundary-(solve|boundary)),'rows':[]}
for label in ['female_Forehand_0','female_Forehand_1','female_Forehand_2','female_EmoteSpike_1']:
 snap=json.loads((R/'proof/reference-rebuild/character-motion-matrices17/matrices'/f'{label}.json').read_text());part=next(x for x in snap['parts'] if x['name']=='Kit_Top');shaped=src.copy()
 for a in q['anchors']:
  name='TailoredSleeve_'+a['shape'];weight=part['shapeWeights'][part['shapeNames'].index(name)]/100;shaped+=np.array(a['deltas']).reshape(-1,3)*weight
 shaped=(shaped[ids]*sw[...,None]).sum(1);matrix=np.array(part['rendererToRoot']).reshape(4,4)[None]@np.array(part['skinMatrices']).reshape(-1,4,4);raw=np.zeros_like(shaped)
 for k in range(4):raw+=(np.einsum('nij,nj->ni',matrix[bi[:,k],:3,:3],shaped)+matrix[bi[:,k],:3,3])*bw[:,k,None]
 frames=[]
 for c in range(p['panelCount']):
  origin=raw[p['panelFrameA'][c]];n=np.zeros(3)
  for e in range(p['panelEdgeStarts'][c],p['panelEdgeStarts'][c+1],2):n+=np.cross(raw[p['panelBoundaryEdges'][e]]-origin,raw[p['panelBoundaryEdges'][e+1]]-origin)
  area=float(np.linalg.norm(n));n/=max(area,1e-12);x=raw[p['panelFrameB'][c]]-origin;x-=n*(n@x);length=float(np.linalg.norm(x));x/=max(length,1e-12);frames.append({'panel':c,'boundaryAreaVectorLength':area,'tangentSpanMetres':length,'passed':bool(area>1e-12 and length>1e-12)})
 report['rows'].append({'sample':label,'time':snap['time'],'frames':frames})
report['passed']=report['fixedMissingBoundaryRepresentatives']==0 and all(f['passed'] for r in report['rows'] for f in r['frames']);(O/'live-frame-check.json').write_text(json.dumps(report,indent=2));print(json.dumps({'passed':report['passed'],'originalMissingBoundaryRepresentatives':report['originalMissingBoundaryRepresentatives'],'samples':len(report['rows']),'panelsPerSample':p['panelCount'],'minimumAreaVectorLength':min(f['boundaryAreaVectorLength'] for r in report['rows'] for f in r['frames']),'minimumTangentSpanMetres':min(f['tangentSpanMetres'] for r in report['rows'] for f in r['frames'])},indent=2))

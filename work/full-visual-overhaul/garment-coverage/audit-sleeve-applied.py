import json,pathlib,numpy as np
R=pathlib.Path(__file__).resolve().parents[3]
for sex in ['female','male']:
 old=json.loads((R/f'proof/full-visual-overhaul/character-pose-data-1/poses/{sex}_intro.json').read_text())
 new=json.loads((R/f'proof/full-visual-overhaul/character-pass-29-art6-crafted/poses/{sex}_intro.json').read_text())
 sculpt=json.loads((R/f'work/full-visual-overhaul/garment-coverage/axilla-field-3/{sex}_intro.json').read_text())
 p=json.loads((R/f'Unity/Assets/Resources/Tennis/Correctives/SleeveFit_{sex.title()}.json').read_text())
 report={'sex':sex}
 for name in ['Body','Top']:
  i=0 if name=='Body' else 1;a=old['parts'][i];b=new['parts'][i]
  A=lambda k,n:np.array(a[k]).reshape(-1,n)
  B=lambda k,n:np.array(b[k]).reshape(-1,n)
  rec={'verticesMax':float(np.linalg.norm(A('vertices',3)-B('vertices',3),axis=1).max()),'weightsMax':float(abs(A('weights',4)-B('weights',4)).max()),'oldNewPoseMax':float(np.linalg.norm(A('posedVertices',3)-B('posedVertices',3),axis=1).max())}
  if name=='Top':
   v=A('vertices',3)+np.array(sculpt['deltas']).reshape(-1,3);w=np.array(sculpt['parts'][1]['weights']).reshape(-1,4);ids=A('indices',4).astype(int)
   skin=np.array(b['skinMatrices']).reshape(-1,4,4);mix=np.sum(skin[ids]*w[:,:,None,None],axis=1)
   pred=np.einsum('nij,nj->ni',mix,np.column_stack([v,np.ones(len(v))]))[:,:3]
   d=np.linalg.norm(pred-B('posedVertices',3),axis=1)
   rec.update({'targetActualMax':float(d.max()),'targetActualMean':float(d.mean()),'targetWeightMax':float(abs(w-B('weights',4)).max()),'profileSourceVertsMax':float(np.linalg.norm(np.array(p['vertices']).reshape(-1,3)-B('vertices',3),axis=1).max())})
  report[name]=rec
 print(json.dumps(report))

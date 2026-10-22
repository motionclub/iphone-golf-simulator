import json,numpy as np
from pathlib import Path
w=Path('work/character-female33');text=(w/'matrix-cuff-fit-profile.json').read_text();head,tail=text.split(',"anchors":',1);d=json.loads(head+'}');controls=d['controls'];k=len(d['projection'])//len(controls);M=np.array(d['projection']).reshape(k,-1);z=np.load(w/'matrix-cuff-fit-profile-basis.npz');E=z['B'];C=z['C'];shapes=z['V']*z['scale'][:,None]
for side in ['Left','Right']:
 for row in range(3):
  for col in range(4):
   oi=next(i for i,c in enumerate(controls) if c=={'bone':side+'UpperArm','row':row,'column':col});si=next(i for i,c in enumerate(controls) if c=={'bone':'Swing_'+side+'UpperArm','row':row,'column':col});M[:,si]+=M[:,oi];M[:,oi]=0;E[si]+=E[oi];E[oi]=0
E-=M.T@shapes;nv=d['vertexCount'];pos=normal=0
for i in range(0,len(C),12):
 e=C[i:i+12]@E;pos=max(pos,float(np.linalg.norm(e[:,:nv*3].reshape(-1,nv,3),axis=2).max()));normal=max(normal,float(np.linalg.norm(e[:,nv*3:].reshape(-1,nv,3),axis=2).max()/.02))
d['projection']=M.ravel().tolist();(w/'matrix-full-swing-profile.json').write_text(json.dumps(d,separators=(',',':'))[:-1]+',"anchors":'+tail);report={'maxErrorMm':pos*1000,'maxNormalError':normal,'sameFixedShapes':True,'method':'Both female upper arm contribution channels use swing-only matrices'};(w/'matrix-full-swing-report.json').write_text(json.dumps(report,indent=2));print(report,flush=True)

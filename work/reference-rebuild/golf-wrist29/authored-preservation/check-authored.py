import numpy as np,json
from pathlib import Path
R=Path.cwd();W=R/'work/reference-rebuild/golf-wrist29/authored-preservation';curl={'Index':(50,70,40),'Middle':(55,75,45),'Ring':(62,80,45),'Little':(68,82,45)}
def rx(a):
 c=np.cos(np.radians(a));s=np.sin(np.radians(a));return np.array([[1,0,0],[0,c,-s],[0,s,c]])
def rz(a):
 c=np.cos(np.radians(a));s=np.sin(np.radians(a));return np.array([[c,-s,0],[s,c,0],[0,0,1]])
def angle(M):
 u,_,v=np.linalg.svd(M);return float(np.degrees(np.arccos(np.clip((np.trace(u@v)-1)/2,-1,1))))
rows=[]
for sex in ('male','female'):
 d=json.loads((R/f'proof/reference-rebuild/golf-wrist29-tiny-control/poses/{sex}_Driver_address.json').read_text());p=next(v for v in d['parts'] if v['name']=='Body');names=p['bones'];rest=np.linalg.inv(np.array(p['bindposes']).reshape(-1,4,4));world=np.array(p['skinMatrices']).reshape(-1,4,4)@rest
 for side in ('Left','Right'):
  for digit,values in curl.items():
   parent=names.index(side+'Hand')
   for j,joint in enumerate(('Proximal','Intermediate','Distal')):
    i=names.index(side+digit+joint);raw=np.linalg.inv(np.linalg.inv(rest[parent])@rest[i])@(np.linalg.inv(world[parent])@world[i]);fan=np.degrees(np.arctan2(raw[1,0],raw[0,0])) if j==0 else 0.;expected=rz(fan)@rx(values[j]);res=angle(raw[:3,:3]@expected.T);rows.append({'sex':sex,'bone':names[i],'authoredFanDegrees':float(fan),'authoredCurlDegrees':values[j],'residualDegrees':res});parent=i
report={'status':'ACTUAL_ADDRESS_CONTROL_IS_AUTHORED_SOURCE_FAN_CURL','rows':rows,'maximumResidualDegrees':max(v['residualDegrees'] for v in rows),'contract':'matchhero_golf.py finger_pose gamma fan then original localX curl; wrist-only path must carry existing sampled locals without canonicalization','limitation':'Does not validate all recorded raw finger frames or art quality; preserves current source values and relies on actual root check after continuous wrist math'}
(W/'authored-source-proof.json').write_text(json.dumps(report,indent=2)+'\n');print('rows',len(rows),'maxresidualdegrees',report['maximumResidualDegrees']);print([(v['sex'],v['bone'],round(v['authoredFanDegrees'],3),round(v['residualDegrees'],6)) for v in rows if v['bone'].endswith('Proximal')])

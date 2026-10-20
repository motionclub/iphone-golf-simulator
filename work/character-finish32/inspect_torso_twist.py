import json,numpy as np
from pathlib import Path
from mathutils.kdtree import KDTree
from mathutils import Vector
w=Path('work/character-finish32');a=json.loads((w/'twist-field-profile.json').read_text());z=json.loads((w/'twist-torso-profile.json').read_text());old=next(p for p in json.loads((w/'refined/poses/male_intro.json').read_text())['parts'] if p['name']=='Kit_Top');P=np.array(a['vertices']).reshape(-1,3);OP=np.array(old['vertices']).reshape(-1,3);WI=np.array(old['indices']).reshape(-1,4);W=np.array(old['weights']).reshape(-1,4);kd=KDTree(len(OP))
for i,p in enumerate(OP):kd.insert(Vector(p),i)
kd.balance();oid=np.array([kd.find(Vector(p))[1] for p in P]);mass=(W*np.isin(WI,[old['bones'].index(n) for n in ['LeftUpperArm','RightUpperArm']])).sum(1)[oid]
for aa,zz in zip(a['anchors'],z['anchors']):
 error=np.linalg.norm((np.array(aa['deltas'])-np.array(zz['deltas'])).reshape(-1,3),axis=1);use=error>.002;print(aa['shape'],'adjusted',sum(use),'mass',np.quantile(mass[use],[0,.25,.5,.75,1]),'restRange',P[use].min(0),P[use].max(0),flush=True)

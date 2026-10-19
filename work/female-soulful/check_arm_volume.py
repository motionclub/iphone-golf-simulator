"""Measure upper-arm and forearm surface sections across every current female clip.
These geometric probes detect collapse; user review still owns appearance.
"""
from pathlib import Path
import json,numpy as np
r=Path(__file__).resolve().parent

def frame(axis):
 axis=axis/np.linalg.norm(axis);up=np.array([0.,1.,0.])
 if abs(axis@up)>.9:up=np.array([1.,0.,0.])
 x=np.cross(axis,up);x/=np.linalg.norm(x);return np.stack([x,np.cross(axis,x)],axis=1)
def area(points,basis):
 q=points@basis;q-=q.mean(0);return float(np.sqrt(max(np.linalg.det(q.T@q/len(q)),0)))
rows=[];baseline=[];neutral=[]
for hid in ['MatchHero_Female','GolfKitHero_Female']:
 p=r/'dump-arm-final'/hid;m=json.loads((p/'hero.json').read_text());body=m['parts'][0];names=body['bones'];nb=len(names)
 v=np.fromfile(p/'body_pos.f32',np.float32).reshape(-1,3)
 rest=np.fromfile(p/'rest_body_world.f32',np.float32).reshape(-1,3)
 rb=np.fromfile(p/'rest_bones.f32',np.float32).reshape(-1,4,4).transpose(0,2,1)
 bi=np.fromfile(p/'body_bi.i32',np.int32).reshape(-1,4);bw=np.fromfile(p/'body_bw.f32',np.float32).reshape(-1,4)
 arm=np.array([n.endswith(('UpperArm','LowerArm','Hand')) or n.startswith('ArmBlend_') for n in names]);mass=(arm[bi]*bw).sum(1)
 old=r/'dump-current'/hid/'body_pos.f32'
 if old.exists():neutral.append({'hero':hid,'maxRestVertexChangeMm':float(np.max(np.linalg.norm(v-np.fromfile(old,np.float32).reshape(-1,3),axis=1))*1000)})
 probes=[]
 for side in ['Left','Right']:
  for seg,end,fractions in [('UpperArm','LowerArm',[.32,.52,.72]),('LowerArm','Hand',[.25,.45,.65])]:
   a,b=names.index(side+seg),names.index(side+end);axis=rb[b,:3,3]-rb[a,:3,3];length=np.linalg.norm(axis);direction=axis/length
   along=(rest-rb[a,:3,3])@direction;radial=np.linalg.norm(rest-rb[a,:3,3]-along[:,None]*direction,axis=1)
   for frac in fractions:
    mask=(np.abs(along-length*frac)<.009)&(radial<.065)&(mass>.85)
    ids=np.flatnonzero(mask)
    if len(ids)<10:raise ValueError(('Insufficient arm probe',hid,side,seg,frac,len(ids)))
    probes.append((side,seg,frac,a,b,ids,area(rest[ids],frame(axis))))
 for clip in m['clips']:
  posed=np.fromfile(p/('clip_'+clip['file']+'_body.f32'),np.float32).reshape(clip['frames'],-1,3)
  bones=np.fromfile(p/('clip_'+clip['file']+'_bones.f32'),np.float32).reshape(clip['frames'],nb,4,4).transpose(0,1,3,2)
  for side,seg,frac,a,b,ids,ref in probes:
   ratios=np.array([area(q[ids],frame(bn[b,:3,3]-bn[a,:3,3]))/ref for q,bn in zip(posed,bones)])
   rows.append({'hero':hid,'clip':clip['name'],'side':side,'section':seg,'fraction':frac,'frames':clip['frames'],'minimumAreaRatio':float(ratios.min()),'maximumAreaRatio':float(ratios.max())})
  if hid.startswith('Golf') and clip['name']=='Cheer':
   oldp=r/'proof/arm-volume-diagnostic/golf_Cheer_before';q=np.fromfile(str(oldp)+'.f32',np.float32).reshape(-1,3);bn={x['name']:np.array(x['position'])for x in json.loads(Path(str(oldp)+'.json').read_text())['bones']}
   for side,seg,frac,a,b,ids,ref in probes:
    if seg=='UpperArm':baseline.append({'side':side,'fraction':frac,'beforeAreaRatio':area(q[ids],frame(bn[names[b]]-bn[names[a]]))/ref})
failed=[x for x in rows if x['minimumAreaRatio']<.8 or x['maximumAreaRatio']>1.25]
report={'gate':'PASS'if not failed else 'FAIL','method':'Covariance area of fixed narrow surface rings, measured perpendicular to each live bone; 0.8–1.25 of neutral required. This is geometric evidence, not visual acceptance.','clipCount':len(set((x['hero'],x['clip'])for x in rows)),'minimumAreaRatio':min(x['minimumAreaRatio']for x in rows),'maximumAreaRatio':max(x['maximumAreaRatio']for x in rows),'neutral':neutral,'overheadBefore':baseline,'failed':failed,'sections':rows}
(r/'proof/arm-volume-measurements.json').write_text(json.dumps(report,indent=2));print(json.dumps({k:v for k,v in report.items()if k not in ['sections','failed']},indent=2));print('Failed sections',len(failed));print(json.dumps(failed[:6],indent=2))

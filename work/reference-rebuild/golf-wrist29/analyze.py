import json,numpy as np
from pathlib import Path
R=Path.cwd();W=R/'work/reference-rebuild/golf-wrist29'
def qmat(q):
 x,y,z,w=q; return np.array([[1-2*(y*y+z*z),2*(x*y-z*w),2*(x*z+y*w)],[2*(x*y+z*w),1-2*(x*x+z*z),2*(y*z-x*w)],[2*(x*z-y*w),2*(y*z+x*w),1-2*(x*x+y*y)]])
report={}
for sex in ('Male','Female'):
 d=json.loads((R/f'work/reference-rebuild/original-native-adoption1/export/GolfKitHero_{sex}.json').read_text()); rig=d['rig'];names=rig['bones'];p=next(p for p in rig['parts'] if p['part']=='Body');raw=(W/f'{sex}.rig.raw').read_bytes();v=p['vertexCount']
 def F(off,n):return np.frombuffer(raw,dtype='<f4',count=n,offset=off).copy()
 V=F(p['bindPositionOffset'],v*3).reshape(v,3);weights=F(p['weightOffset'],v*4).reshape(v,4);indices=np.frombuffer(raw,dtype='u1',count=v*4,offset=p['indexOffset']).reshape(v,4);bind=F(p['inverseBindOffset'],len(p['bones'])*16).reshape(-1,4,4);rest=np.linalg.inv(bind);dense=np.zeros((v,len(names)))
 for k in range(4):dense[np.arange(v),np.asarray(p['bones'])[indices[:,k]]]+=weights[:,k]
 report[sex]={};np.savez_compressed(W/f'{sex}-source.npz',vertices=V,weights=weights,indices=indices,bindposes=bind,boneMap=np.array(p['bones']),bones=np.array(names))
 for side in ('Left','Right'):
  h=names.index(side+'Hand');l=names.index(side+'LowerArm');m=names.index(side+'MiddleProximal');loc=p['bones'].index(h);lo=p['bones'].index(l);ml=p['bones'].index(m);axis=rest[loc,:3,3]-rest[lo,:3,3];axis/=np.linalg.norm(axis);delta=V-rest[loc,:3,3];along=delta@axis;radius=np.linalg.norm(delta-along[:,None]*axis,axis=1);mask=(along>-.18)&(along<.09)&(radius<.065)&(dense[:,h]+dense[:,l]>.5)
  buckets=[]
  for a in np.arange(-.16,.071,.01):
   ids=np.where(mask&(along>=a)&(along<a+.01))[0]
   if len(ids):buckets.append(dict(mm=round(a*1000),n=len(ids),hand=float(dense[ids,h].mean()),lower=float(dense[ids,l].mean()),minHand=float(dense[ids,h].min()),maxHand=float(dense[ids,h].max()),radialMm=float(radius[ids].mean()*1000)))
  samples=[]
  for ci in rig['clips']:
   if ci['id'] not in ['golfDrive','golfIron','golfHalf','golfChip','golfPutt']:continue
   tracks=F(ci['offset'],ci['frames']*rig['trackCount']*10).reshape(ci['frames'],rig['trackCount'],10);times=ci.get('times');marks=[0,np.argmin(abs(np.array(times)-ci['contact'])) if times else int(ci['contact']/ci['length']*(ci['frames']-1)),ci['frames']-1]
   for frame in marks:
    tr=tracks[frame];bone=np.repeat(np.eye(4)[None,:,:],rig['trackCount'],axis=0)
    for i,t in enumerate(tr):bone[i,:3,:3]=qmat(t[3:7])@np.diag(t[7:10]);bone[i,:3,3]=t[:3]
    arm=bone[h,:3,3]-bone[l,:3,3];palm=bone[m,:3,3]-bone[h,:3,3];angle=np.degrees(np.arccos(np.clip(arm@palm/np.linalg.norm(arm)/np.linalg.norm(palm),-1,1)))
    skin=bone[np.array(p['bones'])]@bind;pred=np.zeros_like(V)
    for k in range(4):pred+=weights[:,k,None]*(np.einsum('nij,nj->ni',skin[indices[:,k],:3,:3],V)+skin[indices[:,k],:3,3])
    rings=[]
    for a in np.arange(-.15,.071,.01):
     ids=np.where(mask&(along>=a)&(along<a+.01))[0]
     if len(ids)>5:rings.append([round(a*1000),*pred[ids].mean(0).tolist()])
    samples.append(dict(clip=ci['id'],frame=int(frame),time=float(times[frame]) if times else frame*ci['length']/(ci['frames']-1),wristAngle=float(angle),rings=rings))
  report[sex][side]={'restWrist':rest[loc,:3,3].tolist(),'restElbow':rest[lo,:3,3].tolist(),'weightBuckets':buckets,'samples':samples}
(W/'wrist-analysis.json').write_text(json.dumps(report,indent=2)+'\n')
for sex,sides in report.items():
 for side,a in sides.items():
  print(sex,side,'weights',[(b['mm'],round(b['hand'],2),b['n']) for b in a['weightBuckets']]);print('angles',[(s['clip'],round(s['time'],2),round(s['wristAngle'],1)) for s in a['samples']])

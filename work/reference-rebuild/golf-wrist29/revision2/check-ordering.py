import json,re,numpy as np
from pathlib import Path
R=Path.cwd();W=R/'work/reference-rebuild/golf-wrist29/revision2'
def qmat(q):
 x,y,z,w=q;return np.array([[1-2*(y*y+z*z),2*(x*y-z*w),2*(x*z+y*w)],[2*(x*y+z*w),1-2*(x*x+z*z),2*(y*z-x*w)],[2*(x*z-y*w),2*(y*z+x*w),1-2*(x*x+y*y)]])
def turn(axis,angle):
 x,y,z=axis;a=np.radians(angle);K=np.array([[0,-z,y],[z,0,-x],[-y,x,0]]);return np.eye(3)+np.sin(a)*K+(1-np.cos(a))*(K@K)
audit={}
for line in (R/'proof/reference-rebuild/golf-wrist29-tiny-control/audit.txt').read_text().splitlines():
 if ' after: ' not in line:continue
 label=line.split(' after: ')[0];audit[label]={}
 for name,p,q in re.findall(r'(\w+) p=\(([^)]+)\) q=\(([^)]+)\)',line):audit[label][name]=(np.array([float(v) for v in p.split(',')]),np.array([float(v) for v in q.split(',')]))
rows=[]
for path in sorted((R/'proof/reference-rebuild/golf-wrist29-tiny-control/poses').glob('*.json')):
 d=json.loads(path.read_text());p=next(x for x in d['parts'] if x['name']=='Body');label=d['label'];names=p['bones'];bind=np.array(p['bindposes']).reshape(-1,4,4);skin=np.array(p['skinMatrices']).reshape(-1,4,4);world=skin@np.linalg.inv(bind);V=np.array(p['vertices']).reshape(-1,3);weights=np.array(p['weights']).reshape(-1,4);weights/=weights.sum(1)[:,None];indices=np.array(p['indices']).reshape(-1,4);dense=np.zeros((len(V),len(names)))
 for k in range(4):dense[np.arange(len(V)),indices[:,k]]+=weights[:,k]
 H=names.index('RightHand');aH,aQ=audit[label]['RightHand'];actual=np.eye(4);actual[:3,:3]=qmat(aQ)*1.0936;actual[:3,3]=aH;root=actual@np.linalg.inv(world[H]);C,Cq=audit[label]['Club'];origin=(np.linalg.inv(root)@np.r_[C,1])[:3];axis=np.linalg.inv(root[:3,:3])@qmat(Cq)@np.array([0,0,1]);axis/=np.linalg.norm(axis)
 old=np.zeros_like(V)
 for k in range(4):old+=weights[:,k,None]*(np.einsum('nij,nj->ni',skin[indices[:,k],:3,:3],V)+skin[indices[:,k],:3,3])
 for side in ['Left','Right']:
  ids=[i for i,n in enumerate(names) if n.startswith(side) and (n.endswith('Hand') or any(v in n for v in ['Index','Middle','Ring','Little','Thumb']))];mask=dense[:,ids].sum(1)>1-1e-8;tipIds=[i for i,n in enumerate(names) if n.startswith(side) and n.endswith('Distal')];tips=(dense[:,tipIds].sum(1)>.4)&mask
  shoulder=world[names.index(side+'UpperArm'),:3,3];elbow=world[names.index(side+'LowerArm'),:3,3];wrist=world[names.index(side+'Hand'),:3,3];palm=world[names.index(side+'MiddleProximal'),:3,3]-wrist;palm/=np.linalg.norm(palm);a=np.linalg.norm(elbow-shoulder);b=np.linalg.norm(wrist-elbow);original=float(np.degrees(np.arccos(np.clip((wrist-elbow)@palm/b,-1,1))));best=original*original;selected=0
  if original>35:
   for degrees in range(-45,46):
    T=turn(axis,degrees);target=origin+T@(wrist-origin)
    if np.linalg.norm(target-wrist)>.04:continue
    forward=target-shoulder;distance=np.linalg.norm(forward);forward/=distance
    if distance>=a+b-.00001 or distance<=abs(a-b)+.00001:continue
    along=(a*a-b*b+distance*distance)/(2*distance);centre=shoulder+forward*along;radius=np.sqrt(max(0,a*a-along*along));pole=elbow-centre;pole-=forward*(pole@forward)
    if np.linalg.norm(pole)<1e-5:continue
    E=centre+pole/np.linalg.norm(pole)*radius;shift=np.linalg.norm(E-elbow)
    if shift>.04:continue
    angle=np.degrees(np.arccos(np.clip((target-E)@(T@palm)/b,-1,1)));cost=angle*angle+.12*degrees*degrees+50000*shift*shift
    if cost<best:best=cost;selected=degrees
  u=np.clip((original-35)/15,0,1);selected*=u*u*(3-2*u);T=turn(axis,selected);M=np.eye(4);M[:3,:3]=T;M[:3,3]=origin-T@origin;newSkin=skin.copy();newSkin[ids]=M@skin[ids];new=np.zeros_like(V)
  for k in range(4):new+=weights[:,k,None]*(np.einsum('nij,nj->ni',newSkin[indices[:,k],:3,:3],V)+newSkin[indices[:,k],:3,3])
  rigid=(old-origin)@T.T+origin
  def cylinder(X):
   delta=X-origin;along=delta@axis;return along,np.linalg.norm(delta-along[:,None]*axis,axis=1)
  stations,radii=cylinder(old[mask]);stations2,radii2=cylinder(new[mask]);tp,tr=cylinder(old[tips]);tp2,tr2=cylinder(new[tips]);rows.append({'label':label,'side':side,'roll':float(selected),'fullyHandBoundVertices':int(mask.sum()),'trueDistalSkinVertices':int(tips.sum()),'maxRigidCarryErrorMm':float(np.linalg.norm(new[mask]-rigid[mask],axis=1).max()*1000),'maxCylinderRadiusChangeMm':float(abs(radii-radii2).max()*1000),'maxShaftStationChangeMm':float(abs(stations-stations2).max()*1000),'maxDistalPadRadiusChangeMm':float(abs(tr-tr2).max()*1000),'baselinePadRadiusRangeMm':[float(tr.min()*1000),float(tr.max()*1000)]})
report={'status':'SOURCE_RIGID_GRIP_PRESERVATION_PASS_ACTUAL_PENDING','source':'actual tiny control Body vertices/weights/skinMatrices after existing canonical+FitDigits closure; finite shaft from exact club grip resource/PCA','parts':rows,'maximumPadRadiusChangeMm':max(r['maxDistalPadRadiusChangeMm'] for r in rows),'maximumSkinCarryErrorMm':max(r['maxRigidCarryErrorMm'] for r in rows),'note':'Preserves existing grip contact/error; does not claim to improve baseline digit closure. Original mixed forearm/wrist transition legitimately deforms under changed arm pose; actual approval still required.'}
(W/'ordering-source-proof.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items() if k!='parts'},indent=2))
for r in rows:print(r['label'],r['side'],'roll',round(r['roll'],2),'distaltips',r['trueDistalSkinVertices'],'radialchange',r['maxDistalPadRadiusChangeMm'])

import json,re,numpy as np
from pathlib import Path
R=Path.cwd();W=R/'work/reference-rebuild/golf-wrist29/revision1'
def norm(v):return v/np.linalg.norm(v)
def rot(axis,degrees):
 axis=norm(axis);a=np.radians(degrees);x,y,z=axis;K=np.array([[0,-z,y],[z,0,-x],[-y,x,0]]);return np.eye(3)+np.sin(a)*K+(1-np.cos(a))*(K@K)
def qmat(q):
 x,y,z,w=q;return np.array([[1-2*(y*y+z*z),2*(x*y-z*w),2*(x*z+y*w)],[2*(x*y+z*w),1-2*(x*x+z*z),2*(y*z-x*w)],[2*(x*z-y*w),2*(y*z+x*w),1-2*(x*x+y*y)]])
audit={}
for line in (R/'proof/reference-rebuild/golf-wrist29-tiny-candidate/audit.txt').read_text().splitlines():
 if ' after: ' not in line:continue
 label=line.split(' after: ')[0];audit[label]={}
 for name,p,q in re.findall(r'(\w+) p=\(([^)]+)\) q=\(([^)]+)\)',line):audit[label][name]=(np.array([float(v) for v in p.split(',')]),np.array([float(v) for v in q.split(',')]))
rows=[]
for path in sorted((R/'proof/reference-rebuild/golf-wrist29-tiny-candidate/poses').glob('*.json')):
 d=json.loads(path.read_text());label=d['label'];p=next(p for p in d['parts'] if p['name']=='Body');names=p['bones'];bind=np.array(p['bindposes']).reshape(-1,4,4);rest=np.linalg.inv(bind);world=np.array(p['skinMatrices']).reshape(-1,4,4)@rest;V=np.array(p['vertices']).reshape(-1,3);weights=np.array(p['weights']).reshape(-1,4);indices=np.array(p['indices']).reshape(-1,4);dense=np.zeros((len(V),len(names)))
 for k in range(4):dense[np.arange(len(V)),indices[:,k]]+=weights[:,k]
 H=names.index('RightHand');aH,aQ=audit[label]['RightHand'];actual=np.eye(4);actual[:3,:3]=qmat(aQ)*1.0936;actual[:3,3]=aH;root=actual@np.linalg.inv(world[H]);C,Cq=audit[label]['Club'];origin=(np.linalg.inv(root)@np.r_[C,1])[:3];axis=norm(np.linalg.inv(root[:3,:3])@qmat(Cq)@np.array([0,0,1]))
 for side in ['Left','Right']:
  h=names.index(side+'Hand');toHand=bind[h]
  def Hpoint(name):return (toHand@rest[names.index(name)])[:3,3]
  palm=norm(np.cross(norm(Hpoint(side+'IndexProximal')-Hpoint(side+'LittleProximal')),norm(Hpoint(side+'MiddleProximal'))))
  for digit,canonical in zip(['Index','Middle','Ring','Little'],[[50,70,40],[55,75,45],[62,80,45],[68,82,45]]):
   chain=[names.index(side+digit+j) for j in ['Proximal','Intermediate','Distal']];parent=[h,chain[0],chain[1]];local=[np.linalg.inv(world[parent[j]])@world[chain[j]] for j in range(3)];restLocal=[bind[parent[j]]@rest[chain[j]] for j in range(3)];hinges=[]
   for j in range(3):
    f=toHand@rest[chain[j]];direction=(Hpoint(names[chain[j+1]])-Hpoint(names[chain[j]])) if j<2 else f[:3,:3]@np.array([0,1,0]);hinge=norm(np.linalg.inv(f[:3,:3])@norm(np.cross(norm(direction),palm)));hinges.append(hinge)
   distal=chain[-1];ids=np.where(dense[:,distal]>=.4)[0];points=V[ids]@bind[distal,:3,:3].T+bind[distal,:3,3];length=np.linalg.norm(points,axis=1);tipLocal=points[length>length.max()*.8].mean(0)
   def update():
    for j in range(3):world[chain[j]]=world[parent[j]]@local[j]
   angles=np.array(canonical,dtype=float)
   def Set(j,a):angles[j]=a;local[j][:3,:3]=restLocal[j][:3,:3]@rot(hinges[j],a);update()
   for j,a in enumerate(canonical):Set(j,a)
   def Tip():return (world[distal]@np.r_[tipLocal,1])[:3]
   tip=Tip();along=np.clip((tip-origin)@axis,-.065,.155);radial=tip-origin-axis*((tip-origin)@axis);target=origin+axis*along+norm(radial)*.017
   def cost():return float(np.sum((Tip()-target)**2))
   before=np.sqrt(cost());limits=[110,140,95]
   for _ in range(3):
    for j in [2,1,0]:
     best=angles[j];bestcost=cost()
     for degree in range(0,limits[j]+1,5):
      Set(j,degree);trial=cost()
      if trial<bestcost:best=degree;bestcost=trial
     Set(j,best)
   for _ in range(2):
    for j in [2,1,0]:
     best=angles[j];bestcost=cost();lo=max(0,best-5);hi=min(limits[j],best+5)
     for degree in np.arange(lo,hi+.01,1):
      Set(j,degree);trial=cost()
      if trial<bestcost:best=degree;bestcost=trial
     Set(j,best)
   after=np.sqrt(cost());rad=np.linalg.norm(Tip()-origin-axis*((Tip()-origin)@axis));rows.append({'label':label,'side':side,'digit':digit,'beforeTargetErrorMm':before*1000,'afterTargetErrorMm':after*1000,'tipRadialMm':rad*1000,'angles':angles.tolist()})
(W/'skin-tip-source-check.json').write_text(json.dumps(rows,indent=2)+'\n')
for label in audit:
 x=[r for r in rows if r['label']==label];print(label,'worsttiperrormm',round(max(r['afterTargetErrorMm'] for r in x),2),'mean',round(np.mean([r['afterTargetErrorMm'] for r in x]),2),'tipradmm',round(max(r['tipRadialMm'] for r in x),2))

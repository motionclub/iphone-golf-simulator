from pathlib import Path
exec((Path(__file__).parent/'diagnose.py').read_text().split("bp,tp=replay('female_Forehand_1')")[0])
import copy,heapq
from PIL import ImageDraw
O=W/'local-cloth-focused';O.mkdir(exist_ok=True)
tr=xf(arr(top,'rendererToRoot',4),arr(profile,'vertices',3));ti=arr(top,'indices',4).astype(int);tw=arr(top,'weights',4)
segments=[('Spine','Chest'),('Chest','Neck'),('LeftShoulder','LeftUpperArm'),('LeftUpperArm','LeftLowerArm'),('LeftLowerArm','LeftHand'),('RightShoulder','RightUpperArm'),('RightUpperArm','RightLowerArm'),('RightLowerArm','RightHand')]
def feature(part):
 bone=arr(part,'rendererToRoot',4)[None]@arr(part,'skinMatrices',16).reshape(-1,4,4)@np.linalg.inv(arr(top,'bindposes',16).reshape(-1,4,4));dirs=[]
 for a,b in segments:
  v=bone[top['bones'].index(b),:3,3]-bone[top['bones'].index(a),:3,3];dirs.append(v/np.linalg.norm(v))
 return np.array([dirs[i]@dirs[j] for i in range(8) for j in range(i+1,8)])
def image(v,t):
 z=np.full((1200,900),np.inf);ids=np.full((1200,900),-1,np.int32);ts=np.ascontiguousarray(t,np.int32);lib.draw(project(v).ctypes.data,ts.ctypes.data,len(ts),900,1200,z.ctypes.data,ids.ctypes.data,0);return z,ids
# Spatial field shares displacement with shell aliases and lining. Smooth compact
# kernel protects all vertices beyond45mm of the exact cloth faces behind streak.
def field(seeds,vectors):
 change=np.zeros_like(tr);best=np.zeros(len(tr))
 for i,vec in zip(seeds,vectors):
  dist=np.linalg.norm(tr-tr[i],axis=1);r=np.clip(dist/.065,0,1);w=(1-r)**4*(1+4*r);strength=np.linalg.norm(vec)*w;sel=strength>best;change[sel]=w[sel,None]*vec;best[sel]=strength[sel]
 return change
normals=arr(profile,'normals',3);base=arr(profile,'vertices',3)
def mesh_normals(v):
 n=np.zeros_like(v);f=np.cross(v[tt[:,1]]-v[tt[:,0]],v[tt[:,2]]-v[tt[:,0]])
 for k in range(3):np.add.at(n,tt[:,k],f)
 return n/np.maximum(np.linalg.norm(n,axis=1)[:,None],1e-12)
regions=np.array([15921,15924,15925,15926,15927,19358,6681,6357,6376]);report={};anchors=[]
for label in ['female_Forehand_1']:
 snap=json.loads((D/'matrices'/f'{label}.json').read_text());mp=next(p for p in snap['parts'] if p['name']==top['name']);rt=arr(mp,'rendererToRoot',4);sm=arr(mp,'skinMatrices',16).reshape(-1,4,4);mix=(sm[ti]*tw[:,:,None,None]).sum(1);rootLinear=np.einsum('ij,njk->nik',rt[:3,:3],mix[:,:3,:3]);bp,tp=replay(label);after=tp.copy();delta=np.zeros_like(tp);stats=[]
 for view in ['front']:
  cam=np.array([2.4,1.3,4.1]) if view=='front' else np.array([-2.4,1.3,-4.1]);fw=target-cam;fw/=np.linalg.norm(fw);camRight=np.cross([0,1,0],fw);camRight/=np.linalg.norm(camRight);camUp=np.cross(fw,camRight)
  bz,bid=image(bp,bt[keep]);physical=np.full_like(bid,-1);hit=bid>=0;physical[hit]=np.where(keep)[0][bid[hit]];region=np.isin(physical,regions);initial=0
  for iteration in range(2):
   tz,tid=image(after,tt);bad=region&(tid>=0)&(bz<tz-.0005);count=int(bad.sum())
   if iteration==0:initial=count
   if count==0:break
   faces=np.unique(tid[bad]);seedval={}
   for f in faces:
    px=bad&(tid==f);amount=min(.024,float(np.max((tz-bz)[px]))+.002)
    for i in tt[f]:seedval[int(i)]=max(seedval.get(int(i),0),amount)
   seeds=list(seedval);vecs=[-fw*seedval[i] for i in seeds];new=field(seeds,vecs);delta+=new;length=np.linalg.norm(delta,axis=1);delta*=np.minimum(1,.028/np.maximum(length,1e-12))[:,None];after=tp+delta
  tz,tid=image(after,tt);bad=region&(tid>=0)&(bz<tz-.0005);stats.append(dict(view=view,initialSkinPixels=initial,remainingSkinPixels=int(bad.sum())))
  # Same-camera source plate, original mask2 retained in both panels.
  def color(p):
   out=render(bp,p,bt[keep]);a=np.full((1200,900,3),218,np.uint8);a[(out>=0)&(out<100000)]=[220,155,100];a[out>=100000]=[162,191,73];return Image.fromarray(a)
  box=(250,340,590,580);panels=[color(tp).crop(box),color(after).crop(box)];plate=Image.new('RGB',(680,266),(24,24,24));dr=ImageDraw.Draw(plate)
  for n,(im,lab) in enumerate(zip(panels,['BEFORE','LOCAL CLOTH'])):plate.paste(im,(n*340,26));dr.text((n*340+6,7),label+' '+view+' '+lab,fill='white')
  plate.save(O/(label+'_'+view+'.png'))
 # Local line search only for the two triangles whose normals turn past90deg.
 oldArea=np.cross(tp[tt[:,1]]-tp[tt[:,0]],tp[tt[:,2]]-tp[tt[:,0]])
 for rollback in range(12):
  newArea=np.cross(after[tt[:,1]]-after[tt[:,0]],after[tt[:,2]]-after[tt[:,0]]);flipped=(np.einsum('ij,ij->i',oldArea,newArea)<0)&(np.linalg.norm(oldArea,axis=1)>1e-8)
  if not flipped.any():break
  vertices=np.unique(tt[flipped]);dist=np.linalg.norm(tr[:,None]-tr[vertices][None],axis=2).min(1);r=np.clip(dist/.012,0,1);delta*= (1-.25*(1-r)**2)[:,None];after=tp+delta
 tz,tid=image(after,tt);bad=region&(tid>=0)&(bz<tz-.0005);stats[-1]['remainingSkinPixelsAfterLocalFoldGuard']=int(bad.sum())
 # Exact inverse linear LBS for additive corrective. Preserve every index/UV/weight.
 restdelta=np.linalg.solve(rootLinear,delta[...,None])[...,0]
 # Recompute geometric normal DIFFERENCE, then map back through original normal
 # LBS. Keep source authored normals outside affected local incident faces.
 n0=mesh_normals(tp);n1=mesh_normals(after);ndposed=n1-n0;nd=np.linalg.solve(rootLinear,ndposed[...,None])[...,0]
 changed=np.linalg.norm(delta,axis=1)>1e-7;oldArea=np.cross(tp[tt[:,1]]-tp[tt[:,0]],tp[tt[:,2]]-tp[tt[:,0]]);newArea=np.cross(after[tt[:,1]]-after[tt[:,0]],after[tt[:,2]]-after[tt[:,0]]);reversals=int(((np.einsum('ij,ij->i',oldArea,newArea)<0)&(np.linalg.norm(oldArea,axis=1)>1e-8)).sum())
 anchors.append(dict(shape=label+'_UnderarmTrace',feature=feature(mp).tolist(),deltas=restdelta.ravel().tolist(),normalDeltas=nd.ravel().tolist()));report[label]={'changedVertices':int(changed.sum()),'maxPosedDisplacementMm':float(np.linalg.norm(delta,axis=1).max()*1000),'maxRestDisplacementMm':float(np.linalg.norm(restdelta,axis=1).max()*1000),'restBounds':{'min':tr[changed].min(0).tolist(),'max':tr[changed].max(0).tolist()},'triangleReversals':reversals,'views':stats};np.savez_compressed(O/(label+'.npz'),body=bp,before=tp,after=after,bodyTriangles=bt[keep],topTriangles=tt,delta=restdelta);print(label,report[label],flush=True)
out={'vertexCount':len(base),'vertices':profile['vertices'],'normals':profile['normals'],'anchors':anchors};(O/'UnderarmTrace_Female.json').write_text(json.dumps(out,separators=(',',':')));(O/'source-report.json').write_text(json.dumps(report,indent=2));print('done',flush=True)

from pathlib import Path
import json,ctypes
import numpy as np
from PIL import Image,ImageDraw
R=Path.cwd();O=R/'work/reference-rebuild/gusset-actual-repair';D=R/'proof/reference-rebuild/character-motion-matrices17';p=json.loads((R/'work/reference-rebuild/garment-gusset1/runtime-reviewed/UnderarmGusset_Female_Full.json').read_text());sleeve=json.loads((R/'Unity/Assets/Resources/Tennis/Correctives/SleeveFit_Female.json').read_text());snap=json.loads((D/'poses/female_intro.json').read_text());body,top=snap['parts'][:2]
def arr(x,k,n):return np.array(x[k]).reshape(-1,n)
def rootmat(x):return arr(x,'rendererToRoot',4)[None]@arr(x,'skinMatrices',16).reshape(-1,4,4)
def skin(v,bi,bw,m):
 out=np.zeros_like(v)
 for k in range(4):out+=(np.einsum('nij,nj->ni',m[bi[:,k],:3,:3],v)+m[bi[:,k],:3,3])*bw[:,k,None]
 return out
def qm(a,b):return np.concatenate([a[...,:3]*b[...,3:]+b[...,:3]*a[...,3:]+np.cross(a[...,:3],b[...,:3]),(a[...,3]*b[...,3]-(a[...,:3]*b[...,:3]).sum(-1))[...,None]],axis=-1)
def quat(m):
 out=[]
 for r in m[:,:3,:3]:
  tr=np.trace(r)
  if tr>0:
   s=np.sqrt(tr+1)*2;q=[(r[2,1]-r[1,2])/s,(r[0,2]-r[2,0])/s,(r[1,0]-r[0,1])/s,s/4]
  else:
   i=np.diag(r).argmax();j=(i+1)%3;k=(j+1)%3;s=np.sqrt(1+r[i,i]-r[j,j]-r[k,k])*2;q=np.zeros(4);q[i]=s/4;q[j]=(r[j,i]+r[i,j])/s;q[k]=(r[k,i]+r[i,k])/s;q[3]=(r[k,j]-r[j,k])/s
  q=np.array(q);out.append(q/np.linalg.norm(q))
 return np.array(out)
def dq(v,bi,bw,m):
 qr=quat(m);tq=np.concatenate([m[:,:3,3],np.zeros((len(m),1))],1);qd=.5*qm(tq,qr);r=qr[bi];d=qd[bi];sign=np.where((r*r[:,0,None]).sum(2)<0,-1,1);r=(r*(bw*sign)[...,None]).sum(1);d=(d*(bw*sign)[...,None]).sum(1);length=np.linalg.norm(r,axis=1)[:,None];r/=length;d/=length;d-=r*(r*d).sum(1)[:,None];conj=r.copy();conj[:,:3]*=-1;translation=2*qm(d,conj)[:,:3];return v+2*np.cross(r[:,:3],np.cross(r[:,:3],v)+r[:,3,None]*v)+translation
src=arr(p,'sourceVertices',3);oi=arr(p,'sourceIndices',3).astype(int);ow=arr(p,'sourceWeights',3);bi=arr(p,'boneIndices',4).astype(int);bw=arr(p,'weights',4);oldbi=arr(top,'indices',4).astype(int);oldbw=arr(top,'weights',4);bt=arr(body,'triangles',3).astype(np.int32);tt=arr(p,'triangles',3).astype(np.int32);oldtt=arr(p,'sourceTriangles',3).astype(np.int32);bbi=arr(body,'indices',4).astype(int);bbw=arr(body,'weights',4);basis=arr(body,'vertices',3);free=np.array(p['freeVertices']);alias=np.array(p['aliases'])
# Exact recorded intro has no separate weight-channel dump. Fit its 10 known
# linear single-frame shape contributions to the recorded baked positions.
deltas=np.array([a['deltas'] for a in sleeve['anchors']]).reshape(-1,len(src),3);introM=rootmat(top);rawintro=skin(src,oldbi,oldbw,introM);rt=arr(top,'rendererToRoot',4);expected=arr(top,'posedVertices',3)@rt[:3,:3].T+rt[:3,3];cols=[]
for delta in deltas:
 linear=np.zeros_like(delta)
 for k in range(4):linear+=np.einsum('nij,nj->ni',introM[oldbi[:,k],:3,:3],delta)*oldbw[:,k,None]
 cols.append(linear.ravel())
introWeights=np.linalg.lstsq(np.array(cols).T,(expected-rawintro).ravel(),rcond=None)[0];introError=np.linalg.norm(rawintro+np.einsum('k,kni->ni',introWeights,np.array(cols).reshape(-1,len(src),3))-expected,axis=1).max()
# Build only the authored pinned-boundary fade used by DQ. Existing cage author
# provides it without changing any positions or role bindings.
# author_cage.py was run separately to create the fixed seam fade.
cage=json.loads((O/'UnderarmGusset_Female_Full.json').read_text());strength=np.zeros(p['vertexCount']);strength[:]=1;mask=json.loads((R/'work/reference-rebuild/garment-weight-transition/mask-cuff2/BodyMask_female-current-matrix-canonical.json').read_text());keep=np.ones(len(bt),bool);keep[mask['alwaysCoveredFaceIndices']]=False
lib=ctypes.CDLL(str(R/'work/reference-rebuild/garment-weight-transition/mask3/raster-front.dylib'));lib.draw.argtypes=[ctypes.c_void_p,ctypes.c_void_p,ctypes.c_int,ctypes.c_int,ctypes.c_int,ctypes.c_void_p,ctypes.c_void_p,ctypes.c_int]
def raster(bv,tv,faces,view):
 cam=np.array([2.4,1.3,4.1])*(1 if view=='front' else np.array([-1,1,-1]));target=np.array([0,.83,.1]);fw=target-cam;fw/=np.linalg.norm(fw);right=np.cross([0,1,0],fw);right/=np.linalg.norm(right);up=np.cross(fw,right);z=np.full((1200,900),np.inf);ids=np.full((1200,900),-1,np.int32)
 for v,t,offset in [(bv,bt[keep],0),(tv,faces,100000)]:
  d=v-cam;depth=d@fw;scale=600/np.tan(np.deg2rad(17));xy=np.ascontiguousarray(np.column_stack([450+d@right/depth*scale,600-d@up/depth*scale,depth]));t=np.ascontiguousarray(t,np.int32);lib.draw(xy.ctypes.data,t.ctypes.data,len(t),900,1200,z.ctypes.data,ids.ctypes.data,offset)
 return ids
def picture(ids):
 a=np.full((*ids.shape,3),218,np.uint8);a[(ids>=0)&(ids<100000)]=[220,155,100];a[ids>=100000]=[162,191,73];return Image.fromarray(a)
rows=[]
for label in ['female_intro','female_Forehand_1','female_Forehand_2','female_EmoteSpike_1']:
 if label=='female_intro':tm=introM;bm=rootmat(body);weights=introWeights
 else:
  parts=json.loads((D/'matrices'/f'{label}.json').read_text())['parts'];tp=next(x for x in parts if x['name']=='Kit_Top');bp=next(x for x in parts if x['name']=='Body_F');tm=rootmat(tp);bm=rootmat(bp);weights=np.array([tp['shapeWeights'][tp['shapeNames'].index('TailoredSleeve_'+a['shape'])]/100 for a in sleeve['anchors']])
 shaped=src+np.einsum('k,kni->ni',weights,deltas);newv=(shaped[oi]*ow[...,None]).sum(1);before=skin(shaped,oldbi,oldbw,tm);raw=skin(newv,bi,bw,tm);deformed=dq(newv,bi,bw,tm);after=raw*(1-strength[:,None])+deformed*strength[:,None];bv=skin(basis,bbi,bbw,bm);row={'sample':label,'maximumDQMoveMetres':float(np.linalg.norm(after-raw,axis=1).max()),'views':[]}
 for view in ['front','rear']:
  old=raster(bv,before,oldtt,view);new=raster(bv,after,tt,view);newskin=(old>=100000)&(new>=0)&(new<100000);removedskin=(new>=100000)&(old>=0)&(old<100000);newbackground=(old>=0)&(new<0);row['views'].append({'view':view,'newSkinPixels':int(newskin.sum()),'coveredSkinPixels':int(removedskin.sum()),'newBackgroundPixels':int(newbackground.sum())});plate=Image.new('RGB',(900,476),(24,24,24));draw=ImageDraw.Draw(plate)
  for j,(pix,title) in enumerate([(old,'BASELINE'),(new,'FULL TOP DQ')]):plate.paste(picture(pix).crop((200,250,650,700)),(450*j,26));draw.text((450*j+5,7),label+' '+view+' '+title,fill='white')
  plate.save(O/f'dq_full_{label}_{view}.png')
 rows.append(row)
report={'introShapeFitMaxErrorMetres':float(introError),'rows':rows};(O/'dq-full-targeted.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))

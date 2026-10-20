"""Exact geometric registration on the shared frozen course; no optical flow."""
from pathlib import Path
import os,sys,json,numpy as np
os.environ['OPENCV_IO_ENABLE_OPENEXR']='1'
w=Path(__file__).resolve().parents[1];sys.path.insert(0,str(w/'python-deps'));import cv2
cv2.setNumThreads(4)
H,W=2532,1170;yy,xx=np.mgrid[:H,:W].astype(np.float32)
def mat(q):return np.array([[q[f'e{i}{j}'] for j in range(4)] for i in range(4)],np.float64)
def world(p):
 a=cv2.imread(str(p),cv2.IMREAD_UNCHANGED)
 assert a is not None and a.shape==(H,W,4)
 # Explicit Metal render-target row convention, independently checked against
 # each frame's camera. Raw capture bypasses URP's half-float intermediate.
 a=np.ascontiguousarray(a[::-1]);return np.ascontiguousarray(a[:,:,:3][:,:,::-1]),a[:,:,3]
def luma(p):
 a=cv2.imread(str(p)).astype(np.float32);return a[:,:,2]*.2126+a[:,:,1]*.7152+a[:,:,0]*.0722
rows=[]
for hole in [7,8,9,10]:
 roots=[w/f'proof/films_{s}/film_hole{hole:02}' for s in ['before_r22','after_r28']];wr=w/f'proof/film_world_r27/film_hole{hole:02}';ms=[json.loads((r/'manifest.json').read_text()) for r in roots+[wr]]
 for m in ms:assert m['width']==W and m['height']==H and len(m['frames'])==90
 for fs in zip(*[m['frames'] for m in ms]):
  for f in fs[1:]:assert np.allclose(mat(f['view']),mat(fs[0]['view']),atol=1e-5) and np.allclose(mat(f['projection']),mat(fs[0]['projection']),atol=1e-5)
 stats={n:[[],[]] for n in ['grass','rock']};selfErrors=[];P,C=world(wr/'w_000.exr');previous=[luma(r/'f_000.png') for r in roots]
 for f in range(1,90):
  VP=mat(ms[2]['frames'][f-1]['projection'])@mat(ms[2]['frames'][f-1]['view']);proj=P@VP[:,:3].T+VP[:,3];ndc=proj[:,:,:2]/np.where(np.abs(proj[:,:,3,None])<1e-10,1,proj[:,:,3,None]);sx=(ndc[:,:,0]+1)*W/2-.5;sy=(1-ndc[:,:,1])*H/2-.5;err=np.sqrt((sx-xx)**2+(sy-yy)**2);selfErrors.append(float(np.percentile(err[C>0],99.9)));assert selfErrors[-1]<.01,'World capture projection mismatch'
  Q,D=world(wr/f'w_{f:03}.exr');VP=mat(ms[2]['frames'][f]['projection'])@mat(ms[2]['frames'][f]['view']);proj=P@VP[:,:3].T+VP[:,3];ndc=proj[:,:,:2]/np.where(np.abs(proj[:,:,3,None])<1e-10,1,proj[:,:,3,None]);x=np.ascontiguousarray(((ndc[:,:,0]+1)*W/2-.5).astype(np.float32));y=np.ascontiguousarray(((1-ndc[:,:,1])*H/2-.5).astype(np.float32));nextP=cv2.remap(Q,x,y,cv2.INTER_LINEAR);nextC=cv2.remap(D,x,y,cv2.INTER_NEAREST);difference=np.linalg.norm(nextP-P,axis=2)
  valid=(x>8)&(x<W-9)&(y>8)&(y<H-9)&(difference<.05)&(C==nextC)&(proj[:,:,3]>0)
  following=[luma(r/f'f_{f:03}.png') for r in roots]
  residuals=[np.abs(a-cv2.remap(b,x,y,cv2.INTER_LINEAR)) for a,b in zip(previous,following)]
  for name,k in [('grass',1),('rock',2)]:
   mask=cv2.erode(((C==k)&valid).astype(np.uint8),np.ones((7,7),np.uint8))>0
   assert mask.sum()>1000,(hole,f,name,'insufficient physical samples')
   for j,delta in enumerate(residuals):stats[name][j].append(dict(frame=f,pixels=int(mask.sum()),mean=float(delta[mask].mean()),p95=float(np.percentile(delta[mask],95))))
  P,C=Q,D;previous=following
 metrics=[{name:dict(intervals=len(v[j]),mean=float(np.mean([q['mean'] for q in v[j]])),p95=float(np.mean([q['p95'] for q in v[j]])),raw=v[j]) for name,v in stats.items()} for j in [0,1]]
 row=dict(hole=hole,before=metrics[0],after=metrics[1],worldSelfReprojectionP999MaxPx=max(selfErrors));row['status']='PASS' if all(metrics[1][n]['mean']<=metrics[0][n]['mean'] and metrics[1][n]['p95']<=metrics[0][n]['p95'] for n in ['grass','rock']) else 'FAIL';rows.append(row);print(hole,row['status'],[(n,metrics[0][n]['mean'],metrics[1][n]['mean'],metrics[0][n]['p95'],metrics[1][n]['p95']) for n in ['grass','rock']],flush=True)
 (w/'data/film_temporal_world_r28.partial.json').write_text(json.dumps(rows,indent=2))
(w/'data/film_temporal_world_r28.json').write_text(json.dumps(dict(protocol='89 original-phone-resolution intervals; same physical grass/rock masks on before and after; full-float frozen world positions and exact view/projection registration; independently validated self projection <.01px; disocclusion rejected by <5cm world agreement; 7px contour erosion; Rec709 byte luminance with float bilinear resampling; no optical flow or colour-dependent sample selection',holes=rows),indent=2))

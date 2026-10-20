"""Motion-compensated temporal residual on all 89 intervals of each 3s film."""
from pathlib import Path
import sys,json,numpy as np
W=Path(__file__).resolve().parents[1];sys.path.insert(0,str(W/'python-deps'));import cv2
cv2.setNumThreads(4)
rows=[]
for hole in [7,8,9,10]:
 roots=[W/f'proof/films_{s}/film_hole{hole:02}' for s in ['before_r4','after_r17']]
 manifests=[json.loads((p/'manifest.json').read_text()) for p in roots]
 for m in manifests:assert m['width']==1170 and m['height']==2532 and len(m['frames'])==90 and m['seconds']==3
 for a,b in zip(*[m['frames'] for m in manifests]):
  assert np.allclose(list(a['view'].values()),list(b['view'].values()),atol=1e-5),'Camera drift'
 metrics=[]
 for root in roots:
  stats={s:[] for s in ['grass','rock']};flow=cv2.DISOpticalFlow_create(cv2.DISOPTICAL_FLOW_PRESET_MEDIUM)
  previous=cv2.imread(str(root/'f_000.png'))
  for f in range(1,90):
   following=cv2.imread(str(root/f'f_{f:03}.png'));a=cv2.cvtColor(previous,cv2.COLOR_BGR2GRAY);b=cv2.cvtColor(following,cv2.COLOR_BGR2GRAY)
   # Register at half resolution, then evaluate luminance residuals at the
   # original phone resolution. The same protocol is used on both films.
   small=cv2.resize(a,None,fx=.5,fy=.5);small_b=cv2.resize(b,small.shape[::-1]);vel=flow.calc(small,small_b,None);vel=cv2.resize(vel,(1170,2532))*2
   yy,xx=np.mgrid[:2532,:1170].astype(np.float32);x=xx+vel[:,:,0];y=yy+vel[:,:,1]
   warped=cv2.remap(following,x,y,cv2.INTER_LINEAR);delta=np.abs(cv2.cvtColor(previous,cv2.COLOR_BGR2GRAY).astype(float)-cv2.cvtColor(warped,cv2.COLOR_BGR2GRAY))
   valid=(x>8)&(x<1161)&(y>8)&(y<2523)
   rgb=previous[:,:,::-1].astype(float);r,g,bl=np.moveaxis(rgb,-1,0);mx=rgb.max(2);mn=rgb.min(2)
   grass=(g>r*1.07)&(g>bl*1.10)&(mx<248)&(mn>5)
   rock=((mx-mn)<48)&(mx<175)&(mn>20)&(~grass)
   # Fixed central field excludes sky and the near golfer; reject contour
   # boundaries where disocclusion is scene motion rather than shimmer.
   roi=(yy>700)&(yy<2200)&~((xx>420)&(xx<750)&(yy>1600))
   for name,mask in [('grass',grass),('rock',rock)]:
    mask=cv2.erode((mask&roi&valid).astype(np.uint8),np.ones((9,9),np.uint8))>0
    if mask.sum()>1000:stats[name].append(dict(frame=f,pixels=int(mask.sum()),mean=float(delta[mask].mean()),p95=float(np.percentile(delta[mask],95))))
   previous=following
  metrics.append({name:dict(intervals=len(v),mean=float(np.mean([s['mean'] for s in v])) if v else None,p95=float(np.mean([s['p95'] for s in v])) if v else None,raw=v) for name,v in stats.items()})
 row=dict(hole=hole,before=metrics[0],after=metrics[1]);row['status']='PASS' if all(metrics[1][n]['mean'] is not None and metrics[1][n]['mean']<=metrics[0][n]['mean'] and metrics[1][n]['p95']<=metrics[0][n]['p95'] for n in ['grass','rock']) else 'FAIL';rows.append(row);print(hole,row['status'],[(n,metrics[0][n]['mean'],metrics[1][n]['mean']) for n in ['grass','rock']],flush=True)
(W/'data/film_temporal_metrics_r17.json').write_text(json.dumps(dict(protocol='89 phone-resolution intervals; identical camera matrices, DIS half-resolution motion registration; original-resolution residual; colour-defined eroded grass/rock samples, fixed ROI; no unavailable value passes',holes=rows),indent=2)+'\n')

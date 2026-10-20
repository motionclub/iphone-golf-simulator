from pathlib import Path
from PIL import Image
import numpy as np,json
W=Path(__file__).resolve().parent; S=W.parents[1]/'work/male-silhouette'; rows=np.arange(61,98.0)
profiles=[]
for name,cx,sole,h,sign in [('bald_front',353,654,593,1),('bald_back',915.75,651,589,-1)]:
 m=np.array(Image.open(S/(name+'_target.png')).convert('L'))>127; a=[]
 for r in rows:
  py=round(sole-(654-r)/593*h); x=np.where(m[py])[0]; p=sign*(x-cx)*593/h;a.append([min(p)-.5,max(p)+.5])
 profiles.append(a)
target=np.mean(profiles,axis=0); widths=(target[:,1]-target[:,0])/2; cx=float(np.mean(np.mean(target,axis=1)))
best=(1e9,None)
for top in np.arange(58.8,60.01,.05):
 for centre in np.arange(93,103,.1):
  shape=np.sqrt(np.maximum(0,1-((centre-rows)/(centre-top))**2)); rx=np.sum(shape*widths)/np.sum(shape**2)
  loss=np.mean((shape*rx-widths)**2)
  if loss<best[0]:best=(loss,(top,centre,rx))
print(best,'cx',cx)
(W/'crown-fit.json').write_text(json.dumps({'top':best[1][0],'centre':best[1][1],'radius_x':best[1][2],'centre_x':cx,'profile_rms_pixels':best[0]**.5},indent=2))

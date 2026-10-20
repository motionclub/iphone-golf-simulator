import numpy as np,json
from PIL import Image
from pathlib import Path
W=Path(__file__).resolve().parent;S=W.parents[1]/'work/male-silhouette'
c=np.load(W/'earvolume.npy');s=1.7/593;row=654-c[:,2]/s;xx=c[:,0]/s
rows=np.arange(60,162);delta=[];widths=[]
def smooth(x):
 k=np.exp(-np.arange(-6,7)**2/(2*1.5**2)); k/=sum(k);return np.convolve(np.pad(x,(6,6),mode='edge'),k,mode='valid')
for side in [0,1]:
 values=[]; wr=[]
 for r in rows:
  targets=[];models=[]
  for v,cx,sole,h,sgn in [('bald_front',353,654,593,1),('bald_back',915.75,651,589,-1)]:
   py=round(sole-(654-r)/593*h);t=np.array(Image.open(S/(v+'_target.png')).convert('L'))[py]>127;m=np.array(Image.open(W/'earvolume'/(v+'.png')).getchannel('A'))[py]>127
   if not np.any(t) or not np.any(m):continue
   tx=sgn*(np.where(t)[0]-cx)*593/h;mx=sgn*(np.where(m)[0]-cx)*593/h
   targets.append([min(tx),max(tx)][side]);models.append([min(mx),max(mx)][side])
  values.append(np.mean(targets)-np.mean(models));wr.append(abs(np.mean(models)))
 delta.append(smooth(np.nan_to_num(values)));widths.append(smooth(wr))
for sign,side in [(-1,0),(1,1)]:
 d=np.interp(row,rows,delta[side]);w=np.interp(row,rows,widths[side]);rad=np.clip(abs(xx)/np.maximum(w,1),0,1)**1.4
 t=np.clip((162-row)/8,0,1);fade=t*t*(3-2*t);c[:,0]+=d*s*.85*rad*fade*(np.sign(xx)==sign)
np.save(W/'final.npy',c)
print('Correction extrema canonical pixels',[(float(x.min()),float(x.max())) for x in delta])

from pathlib import Path
from PIL import Image,ImageFilter
import numpy as np,sys
sys.path.insert(0,'Tools/HeroBase');from plate_profiles import MALE,FEMALE
out=Path('work/hero-base/face-relief-trials')
def blur(a,r):return np.asarray(Image.fromarray(a.astype('float32'),mode='F').filter(ImageFilter.GaussianBlur(r)),dtype=float)
# Pillow GaussianBlur does not support F; normalized 16-bit precision is retained
# through a separable NumPy kernel on the small measurement crop.
def blur(a,r):
 rad=max(1,int(r*3));x=np.arange(-rad,rad+1);k=np.exp(-x*x/(2*r*r));k/=k.sum()
 b=np.apply_along_axis(lambda row:np.convolve(np.pad(row,rad,mode='edge'),k,'valid'),0,a)
 return np.apply_along_axis(lambda row:np.convolve(np.pad(row,rad,mode='edge'),k,'valid'),1,b)
for sex,suf,p in [('male','M',MALE),('female','F',FEMALE)]:
 rgb=np.asarray(Image.open('ArtDir/hero/base_lock/'+sex+'_body_plain.jpg').crop((p['cx']-65,0,p['cx']+65,185)),dtype=float)/255
 luma=rgb@[.2126,.7152,.0722];yy,xx=np.indices(luma.shape);X=xx-65;Y=yy
 rows=sorted(p['head']);width=np.interp(Y[:,0],[a[0] for a in rows],[a[1] for a in rows])[:,None]
 valid=(np.abs(X)<.94*width)&(Y>=rows[0][0])&(Y<=rows[-1][0])
 for sign in [-1,1]:
  valid&=~((abs(X-sign*p['eye_x'])<p['eye_r']+2)&(abs(Y-p['eye_y'])<p['eye_ry']+2))
  valid&=~((abs(X-sign*p['eye_x'])<14)&(abs(Y-p['brow_y'])<5))
 valid&=~((abs(X)<p['mouth_w']+2)&(abs(Y-p['mouth_y'])<4))
 valid&=~((abs(X)<8)&(abs(Y-(p['nose_y']+2))<2))
 clean=blur(luma*valid,3)/np.maximum(blur(valid.astype(float),3),1e-5)
 clean=np.where(valid,luma,clean);detail=blur(clean,1.1)-blur(clean,9)
 fade=np.clip((Y-(p['eye_y']-15))/12,0,1)*np.clip((rows[-1][0]-Y)/12,0,1)*np.clip((.96*width-abs(X))/8,0,1)
 relief=np.clip(detail*32,-3.0,3.0)*fade
 np.save(out/(suf+'_relief.npy'),relief)
 print(sex,'relief min/max',relief.min(),relief.max())

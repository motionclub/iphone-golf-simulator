"""python3 legtargets.py : plate profile edges vs model silhouette (baseline) per z -> data/leg_targets.json (y targets in metres, model frame)."""
import numpy as np, json
from PIL import Image
S=0.005916/3
m=Image.open('../../ArtDir/hero/base_lock/female_multiangle_body.jpg').convert('RGB')
c=np.array(m.crop((700,45,830,345)).resize((390,900),Image.LANCZOS)).astype(float)
lum=c.mean(2); bg=np.median(np.concatenate([lum[:,:20],lum[:,-20:]],1),1,keepdims=True)
fgp=((bg-lum)>9)|((c[:,:,0]-c[:,:,2])>14)
mod=np.array(Image.open('proof/psil_base.png'))[:,:,3]>127
yc=json.load(open('data/headcentre.json'))['yc']
def ext(mask,r):
    xs=np.where(mask[r])[0]
    return (xs.min(),xs.max()+1) if len(xs) else (np.nan,np.nan)
zs=np.arange(0.17,0.80,0.01)
rows=[int((1.7335-z)/S) for z in zs]
P=np.array([ext(fgp,r) for r in rows],float); M=np.array([ext(mod,r) for r in rows],float)
# registration: shift plate so edges agree over z in [0.60,0.75]
sel=(zs>=0.60)&(zs<=0.75)
off=np.nanmedian(np.concatenate([(M[sel,0]-P[sel,0]),(M[sel,1]-P[sel,1])]))
print('registration offset px',off,'= mm',off*S*1000)
P=P+off
def smooth(a,n=5):
    pad=np.pad(a,(n//2,n//2),mode='edge'); return np.convolve(pad,np.ones(n)/n,mode='valid')
Pf=smooth(P[:,0]); Pb=smooth(P[:,1]); Mf=smooth(M[:,0]); Mb=smooth(M[:,1])
toy=lambda px: yc+(px-270)*S
out={'z':zs.tolist(),'plate_front_y':toy(Pf).tolist(),'plate_back_y':toy(Pb).tolist(),'model_front_y':toy(Mf).tolist(),'model_back_y':toy(Mb).tolist(),'offset_px':float(off)}
json.dump(out,open('data/leg_targets.json','w'))
for z,a,b,cc,d in zip(zs[::4],Pf[::4],Pb[::4],Mf[::4],Mb[::4]):
    print(f'z={z:.2f} plate [{a:.0f},{b:.0f}] depth {(b-a)*S*1000:4.0f}mm  model [{cc:.0f},{d:.0f}] depth {(d-cc)*S*1000:4.0f}mm  d_front {(a-cc)*S*1000:+4.0f}mm d_back {(b-d)*S*1000:+4.0f}mm')
